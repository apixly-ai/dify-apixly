"""Fixed-origin API client. Every paid submission is attempted exactly once."""

from __future__ import annotations

import base64
import binascii
import ipaddress
import json
import re
from typing import Any
from urllib.parse import urlsplit

import httpx

API_BASE = "https://apixly.ai/v1"
MAX_ASSET_BYTES = 32 * 1024 * 1024
MAX_REFERENCE_BYTES = 20 * 1024 * 1024
SUPPORTED_MIMES = {"image/png", "image/jpeg", "image/webp", "video/mp4", "video/webm"}
PENDING = {"queued", "pending", "processing", "running", "in_progress", "submitted"}
SUCCEEDED = {"succeeded", "completed", "success"}
FAILED = {"failed", "expired", "cancelled", "canceled", "rejected"}
RESERVED = {
    "model",
    "prompt",
    "async",
    "api_key",
    "authorization",
    "base_url",
    "callback_url",
    "images",
    "mask",
}


class MediaError(ValueError):
    """The request could not be validated or was explicitly rejected."""


class UnknownOutcome(MediaError):
    """A submit may have reached the server. Never replay it automatically."""


def required_text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MediaError(f"{name} is required.")
    return value


def validate_reference(value: Any, *, image: bool = True) -> str:
    value = required_text(value, "Reference")
    if value.startswith("data:"):
        match = re.fullmatch(r"data:(image/(?:png|jpeg|webp));base64,([A-Za-z0-9+/=\r\n]+)", value)
        if not match or not image:
            raise MediaError(
                "Use an image/png, image/jpeg or image/webp base64 data URL for image references; video/audio references require HTTPS URLs."
            )
        if len(match[2]) > ((MAX_REFERENCE_BYTES + 2) // 3) * 4:
            raise MediaError("Reference image exceeds 20 MiB.")
        try:
            decoded = base64.b64decode(match[2].replace("\r", "").replace("\n", ""), validate=True)
        except (ValueError, binascii.Error) as exc:
            raise MediaError("Reference image has invalid base64.") from exc
        if not decoded or len(decoded) > MAX_REFERENCE_BYTES:
            raise MediaError("Reference image must contain between 1 byte and 20 MiB.")
        return value
    try:
        url = urlsplit(value)
        port = url.port
    except ValueError as exc:
        raise MediaError("Reference URL is invalid.") from exc
    if (
        url.scheme != "https"
        or not url.hostname
        or url.username
        or url.password
        or port not in (None, 443)
    ):
        raise MediaError("Reference URL must be public HTTPS without embedded credentials.")
    host = url.hostname.lower()
    if host in {"localhost", "localhost.localdomain"} or host.endswith(
        (".localhost", ".local", ".internal")
    ):
        raise MediaError("Private reference hosts are not supported.")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address and not address.is_global:
        raise MediaError("Private reference addresses are not supported.")
    # References are forwarded, never fetched by this plugin. The gateway owns
    # DNS resolution, SSRF checks, size limits, and provider-specific transport.
    return value


class MediaClient:
    def __init__(self, api_key: str, *, transport: httpx.BaseTransport | None = None):
        self.api_key = required_text(api_key, "Apixly API key")
        self.http = httpx.Client(
            transport=transport,
            follow_redirects=False,
            timeout=httpx.Timeout(60, connect=10),
            trust_env=False,
        )

    def close(self) -> None:
        self.http.close()

    def _safe(self, value: Any) -> str:
        text = str(value).replace(self.api_key, "[REDACTED]")
        text = re.sub(r"(?i)bearer\s+\S+", "Bearer [REDACTED]", text)
        return text[:500]

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "User-Agent": "apixly-dify-media/0.1.0",
        }

    def validate_credentials(self) -> None:
        try:
            response = self.http.get(f"{API_BASE}/models", headers=self._headers())
        except httpx.HTTPError as exc:
            raise MediaError(
                "Could not connect to Apixly. Check connectivity and try credential validation again."
            ) from exc
        if response.status_code != 200:
            raise MediaError(
                f"Apixly credential validation returned HTTP {response.status_code}. Check the key, key group and account balance. No generation was submitted."
            )
        try:
            data = response.json()
        except ValueError as exc:
            raise MediaError("Apixly credential validation returned invalid JSON.") from exc
        if not isinstance(data, dict) or not isinstance(data.get("data"), list):
            raise MediaError("Apixly model discovery returned an unexpected response.")

    def _parameters(
        self, parameters: dict[str, Any] | None, *, video: bool = False
    ) -> dict[str, Any]:
        if parameters is None:
            return {}
        if not isinstance(parameters, dict):
            raise MediaError("Parameters must be a JSON object.")
        try:
            json.dumps(parameters, allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise MediaError(
                "Parameters must contain only finite, JSON-compatible values; NaN and Infinity are not supported."
            ) from exc
        reserved = RESERVED - ({"images"} if video else set())
        if any(not isinstance(key, str) or key.lower() in reserved for key in parameters):
            raise MediaError(
                "Parameters contain a reserved field. Use the dedicated model, prompt and reference inputs."
            )
        result = dict(parameters)
        if video:
            for name in ("images", "videos", "audios"):
                if name in result:
                    if not isinstance(result[name], list) or len(result[name]) > 16:
                        raise MediaError(f"{name} must be an array of up to 16 references.")
                    result[name] = [
                        validate_reference(item, image=name == "images") for item in result[name]
                    ]
        return result

    def _submit(self, path: str, payload: dict[str, Any], kind: str) -> dict[str, Any]:
        try:
            response = self.http.post(f"{API_BASE}{path}", json=payload, headers=self._headers())
        except httpx.HTTPError as exc:
            raise UnknownOutcome(
                "Submission outcome is unknown after a connection error or timeout. No automatic retry was made. Check Apixly task history before submitting again."
            ) from exc
        if (
            response.status_code >= 500
            or response.status_code == 408
            or 300 <= response.status_code < 400
        ):
            raise UnknownOutcome(
                f"Submission outcome is unknown (HTTP {response.status_code}). No automatic retry was made. Check Apixly task history before submitting again."
            )
        if not 200 <= response.status_code < 300:
            raise MediaError(
                f"Apixly rejected submission (HTTP {response.status_code}). Check key access, balance and model parameters. No automatic retry was made."
            )
        try:
            data = response.json()
        except ValueError as exc:
            raise UnknownOutcome(
                "Submission returned invalid JSON. No automatic retry was made. Check Apixly task history before submitting again."
            ) from exc
        if not isinstance(data, dict) or not data.get("id"):
            raise UnknownOutcome(
                "Submission returned no task ID. No automatic retry was made. Check Apixly task history before submitting again."
            )
        data.setdefault("status", "queued")
        data.setdefault("model", payload["model"])
        data["request_id"] = response.headers.get("x-request-id", "")
        return self._normalize(data, kind)

    def generate_image(
        self, model: str, prompt: str, parameters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        payload = self._parameters(parameters)
        payload.update(
            model=required_text(model, "Exact model ID"),
            prompt=required_text(prompt, "Prompt"),
            async_=True,
        )
        payload["async"] = payload.pop("async_")
        return self._submit("/images/generations", payload, "image")

    def edit_image(
        self,
        model: str,
        prompt: str,
        references: list[str],
        parameters: dict[str, Any] | None = None,
        mask: str | None = None,
    ) -> dict[str, Any]:
        if not isinstance(references, list) or not 1 <= len(references) <= 16:
            raise MediaError(
                "Image editing requires between 1 and 16 reference images; model limits may be lower."
            )
        payload = self._parameters(parameters)
        payload.update(
            model=required_text(model, "Exact model ID"), prompt=required_text(prompt, "Prompt")
        )
        payload["async"] = True
        payload["images"] = [{"image_url": validate_reference(item)} for item in references]
        if mask:
            payload["mask"] = {"image_url": validate_reference(mask)}
        return self._submit("/images/edits", payload, "image")

    def create_video(
        self, model: str, prompt: str, parameters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        payload = self._parameters(parameters, video=True)
        payload.update(
            model=required_text(model, "Exact model ID"), prompt=required_text(prompt, "Prompt")
        )
        if model == "grok-imagine-video" and any(
            payload.get(name) for name in ("images", "videos", "audios")
        ):
            raise MediaError(
                "grok-imagine-video supports text-to-video only. Select an exact model with "
                "reference support; the plugin will not replace the model automatically."
            )
        if model == "grok-imagine-video-1.5-preview" and any(
            not reference.startswith("https://") for reference in payload.get("images", [])
        ):
            raise MediaError(
                "grok-imagine-video-1.5-preview requires public HTTPS reference image URLs. "
                "Inline base64 data URLs are not supported on this route."
            )
        return self._submit("/videos", payload, "video")

    def query_task(self, kind: str, task_id: str) -> dict[str, Any]:
        if kind not in {"image", "video"}:
            raise MediaError("Task kind must be image or video.")
        if not isinstance(task_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", task_id):
            raise MediaError("Task ID must contain only letters, digits, underscores and hyphens.")
        path = "/images/generations/" if kind == "image" else "/videos/"
        base = {
            "kind": kind,
            "id": task_id,
            "status": "unknown",
            "terminal": False,
            "success": False,
            "result_state": "query_error",
            "urls": [],
        }
        try:
            response = self.http.get(f"{API_BASE}{path}{task_id}", headers=self._headers())
        except httpx.HTTPError:
            return {
                **base,
                "error": "Status query timed out or failed to connect. Query this same task ID again; do not create another generation.",
            }
        if not 200 <= response.status_code < 300:
            return {
                **base,
                "http_status": response.status_code,
                "error": f"Status query returned HTTP {response.status_code}. The task outcome was not established. Check key ownership/access or query the same ID later.",
            }
        try:
            data = response.json()
        except ValueError:
            return {
                **base,
                "error": "Status query returned invalid JSON. Query this same task ID again.",
            }
        if not isinstance(data, dict):
            return {
                **base,
                "error": "Status query returned an unexpected response. Query this same task ID again.",
            }
        if data.get("id") is not None and str(data["id"]) != task_id:
            return {
                **base,
                "error": "Status response task ID did not match the requested ID. No result was accepted. Query the original ID again or contact support.",
            }
        data.setdefault("id", task_id)
        data["request_id"] = response.headers.get("x-request-id", "")
        return self._normalize(data, kind)

    def _normalize(self, data: dict[str, Any], kind: str) -> dict[str, Any]:
        status = str(data.get("status", "unknown"))
        urls = []
        if isinstance(data.get("url"), str) and data["url"]:
            urls.append(data["url"])
        for item in data.get("data", []) if isinstance(data.get("data"), list) else []:
            if isinstance(item, dict) and isinstance(item.get("url"), str) and item["url"]:
                urls.append(item["url"])
        urls = list(dict.fromkeys(urls))
        success = status in SUCCEEDED and bool(urls)
        result = {
            "kind": kind,
            "id": str(data.get("id", "")),
            "model": str(data.get("model", "")),
            "status": status,
            "terminal": status not in PENDING,
            "success": success,
            "urls": urls,
        }
        if data.get("request_id"):
            result["request_id"] = self._safe(data["request_id"])
        if status in PENDING:
            result["result_state"] = "pending"
            result["next_action"] = (
                "Query the same task ID. Do not submit a new generation to wait for this task."
            )
        elif status in SUCCEEDED:
            result["result_state"] = "completed" if success else "result_unavailable"
            if not success:
                result["error"] = (
                    "Provider reports success but no downloadable result is available. Query this same task ID again or contact support; do not regenerate automatically."
                )
        elif status in FAILED:
            result["result_state"] = "failed"
            error = data.get("error", {})
            message = error.get("message", status) if isinstance(error, dict) else error
            result["error"] = self._safe(message)
        else:
            result["result_state"] = "unknown_status"
            result["error"] = (
                "Unknown task status. Stop automatic polling and inspect this task with support."
            )
        if isinstance(data.get("usage"), dict):
            # Only usage meters are returned; arbitrary gateway response fields,
            # upstream bodies, credentials and private supplier fields are omitted.
            result["usage"] = {
                key: value
                for key, value in data["usage"].items()
                if isinstance(value, (int, float)) and not isinstance(value, bool)
            }
        if isinstance(data.get("progress"), (int, float)):
            result["progress"] = data["progress"]
        for field in ("effective_parameters", "parameter_adjustments"):
            if isinstance(data.get(field), (dict, list)):
                result[field] = data[field]
        return result

    def download_result(self, url: str) -> tuple[bytes, str]:
        parsed = urlsplit(url)
        if (
            parsed.scheme != "https"
            or parsed.netloc not in {"apixly.ai", "platform.apixly.ai"}
            or parsed.path not in {"/v1/images/content", "/v1/videos/content"}
            or not parsed.query
            or parsed.fragment
        ):
            raise MediaError(
                "Result downloads must use an Apixly signed image/video content URL. No third-party download was attempted."
            )
        # This public signed URL is sufficient. Never send the API key, including
        # to same-origin content endpoints. Redirects are deliberately rejected.
        try:
            with self.http.stream("GET", url, headers={"Accept": "image/*,video/*"}) as response:
                if response.status_code != 200:
                    raise MediaError(
                        f"Result download returned HTTP {response.status_code}. Query the existing task for a fresh URL; do not regenerate."
                    )
                mime = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
                if mime not in SUPPORTED_MIMES:
                    raise MediaError(
                        "Result MIME type is not supported for file output. Supported formats are PNG, JPEG, WebP, MP4 and WebM; use the signed URL if appropriate."
                    )
                chunks = []
                total = 0
                for chunk in response.iter_bytes():
                    total += len(chunk)
                    if total > MAX_ASSET_BYTES:
                        raise MediaError(
                            "Result exceeds the 32 MiB plugin download limit. Use the signed URL output instead."
                        )
                    chunks.append(chunk)
        except httpx.HTTPError as exc:
            raise MediaError(
                "Result download failed. Query the existing task for a fresh URL; do not regenerate."
            ) from exc
        if not total:
            raise MediaError("Result download was empty. Query the existing task again.")
        return b"".join(chunks), mime
