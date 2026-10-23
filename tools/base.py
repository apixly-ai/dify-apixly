import json
from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from apixly_media.client import MediaClient, MediaError, UnknownOutcome


def json_value(value: Any, expected: type, name: str) -> Any:
    if value in (None, ""):
        return expected()
    try:
        parsed = json.loads(value) if isinstance(value, str) else value
    except (ValueError, TypeError) as exc:
        raise MediaError(f"{name} must contain valid JSON.") from exc
    if not isinstance(parsed, expected):
        raise MediaError(f"{name} must be a JSON {'object' if expected is dict else 'array'}.")
    return parsed


def model_parameters(parameters: dict[str, Any], names: tuple[str, ...]) -> dict[str, Any]:
    result = dict(json_value(parameters.get("parameters_json"), dict, "Advanced parameters"))
    for name in names:
        value = parameters.get(name)
        if value in (None, ""):
            continue
        if name in result and result[name] != value:
            raise MediaError(
                f"{name} conflicts with advanced parameters. Set it in one place or use matching values."
            )
        result[name] = value
    return result


class MediaTool(Tool):
    def execute(self, client: MediaClient, parameters: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def emit_result(self, result: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        yield self.create_json_message(result)
        for field, value in {
            "task_id": result.get("id", ""),
            "status": result.get("status", "unknown"),
            "terminal": result.get("terminal", False),
            "success": result.get("success", False),
            "generation_success": result.get("generation_success", result.get("success", False)),
            "result_state": result.get("result_state", "unknown"),
            "urls": result.get("urls", []),
        }.items():
            yield self.create_variable_message(field, value)

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        client = None
        try:
            advanced = json_value(
                tool_parameters.get("parameters_json"), dict, "Advanced parameters"
            )
            if any(
                isinstance(name, str) and name.lower() in {"mask", "mask_url"}
                for name in (*tool_parameters.keys(), *advanced.keys())
            ):
                raise MediaError(
                    "Masked inpainting is not enabled in this release because no model passed "
                    "its quality checks. Use ordinary reference-image editing without mask fields."
                )
            client = MediaClient(self.runtime.credentials.get("api_key", ""))
            result = dict(self.execute(client, tool_parameters))
            result["generation_success"] = result.get("success", False)
            if result.get("success"):
                download_errors = []
                downloaded = 0
                for index, url in enumerate(result.get("urls", [])):
                    if tool_parameters.get("download") is True:
                        try:
                            blob, mime = client.download_result(url)
                            extension = {
                                "image/png": "png",
                                "image/jpeg": "jpg",
                                "image/webp": "webp",
                                "video/mp4": "mp4",
                                "video/webm": "webm",
                            }[mime]
                            yield self.create_blob_message(
                                blob,
                                {
                                    "mime_type": mime,
                                    "filename": f"apixly-{result['id']}-{index + 1}.{extension}",
                                },
                            )
                            downloaded += 1
                        except MediaError as exc:
                            download_errors.append(str(exc))
                    else:
                        # Links avoid extra platform fetches; JSON keeps every URL
                        # available for downstream file/storage nodes.
                        yield self.create_link_message(url)
                if tool_parameters.get("download") is True:
                    result["downloaded_files"] = downloaded
                    if download_errors:
                        result.update(
                            success=False,
                            result_state="download_error",
                            error="; ".join(download_errors),
                            next_action="Query the same task ID for fresh URLs or recover the download. Do not submit a new generation.",
                        )
            # Publish final workflow variables only after requested downloads.
            # A generated asset and a delivered Dify file are distinct outcomes.
            yield from self.emit_result(result)
        except UnknownOutcome as exc:
            result = {
                "result_state": "unknown_submission",
                "success": False,
                "terminal": False,
                "error": str(exc),
                "automatic_retry": False,
            }
            yield from self.emit_result(result)
            yield self.create_text_message(str(exc))
        except MediaError as exc:
            result = {
                "result_state": "validation_error",
                "success": False,
                "terminal": False,
                "error": str(exc),
                "automatic_retry": False,
            }
            yield from self.emit_result(result)
            yield self.create_text_message(str(exc))
        finally:
            if client is not None:
                client.close()
