"""Read-only fixed-origin catalog adapter for manual keys or scoped connections."""

from __future__ import annotations

import copy
import hashlib
import threading
import weakref
from typing import Any

import httpx

from apixly_media.catalog import CatalogCache, build_catalog_snapshot, catalog_identity
from apixly_media.client import ACCOUNT_API_BASE, API_BASE, MediaError, connection_error_message
from apixly_media.connection import media_credentials

_CACHE = CatalogCache()
_BINDINGS: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()
_BINDING_LOCK = threading.RLock()


class _FetchError(MediaError):
    def __init__(self, status: int | None = None, code: str | None = None):
        self.status = status
        self.code = code if connection_error_message(code) else None
        super().__init__(
            "Could not read the Apixly catalog. No generation was submitted."
            if status is None
            else f"Apixly catalog returned HTTP {status}. No generation was submitted."
        )


class ModelCatalogService:
    def __init__(
        self,
        credentials: dict[str, Any],
        *,
        cache: CatalogCache | None = None,
        transport: httpx.BaseTransport | None = None,
    ):
        self.token, self.account_mode = media_credentials(credentials)
        self.cache = cache if cache is not None else _CACHE
        self.transport = transport
        self.base = ACCOUNT_API_BASE if self.account_mode else API_BASE
        self.digest = hashlib.sha256(self.token.encode()).hexdigest()

    def _get(self, path: str, *, account: bool = False) -> dict:
        url = "https://apixly.ai/api/integrations/account" if account else self.base + path
        try:
            with httpx.Client(
                transport=self.transport,
                timeout=15,
                follow_redirects=False,
                trust_env=False,
            ) as client:
                response = client.get(
                    url,
                    headers={
                        "Authorization": "Bearer " + self.token,
                        "Accept": "application/json",
                        "Cache-Control": "no-store",
                        "User-Agent": "apixly-dify-media/0.2.0",
                    },
                )
        except httpx.HTTPError:
            raise _FetchError() from None
        if response.status_code != 200:
            try:
                body = response.json()
                error = body.get("error") if isinstance(body, dict) else None
                code = error.get("code") or error.get("type") if isinstance(error, dict) else None
            except ValueError:
                code = None
            raise _FetchError(response.status_code, code)
        try:
            data = response.json()
        except ValueError:
            raise _FetchError() from None
        if not isinstance(data, dict):
            raise _FetchError()
        return data

    def _binding(self) -> dict | None:
        with _BINDING_LOCK:
            return copy.deepcopy(_BINDINGS.get(self.cache, {}).get(self.digest))

    def _account_identity(self) -> tuple[str, dict]:
        data = self._get("", account=True)
        try:
            fields = {
                "mode": "account",
                "connectionId": data["connection_id"],
                "accountId": data["account"]["id"],
                "keyId": data["selected_key"]["id"],
                "revision": data["selection_revision"],
            }
            if (
                any(
                    type(fields[name]) not in (str, int) or not str(fields[name])
                    for name in ("connectionId", "accountId", "keyId")
                )
                or type(fields["revision"]) is not int
                or fields["revision"] < 0
            ):
                raise ValueError
            selected = {
                "id": str(fields["keyId"]),
                "name": data["selected_key"].get("name", ""),
                "masked": data["selected_key"].get("masked", ""),
            }
            if any(not isinstance(value, str) for value in selected.values()):
                raise ValueError
            identity = catalog_identity(fields)
        except (KeyError, TypeError, ValueError):
            raise _FetchError() from None
        with _BINDING_LOCK:
            bindings = _BINDINGS.setdefault(self.cache, {})
            previous = bindings.get(self.digest)
            if previous and previous["identity"] != identity:
                self.cache.invalidate(previous["identity"])
            bindings[self.digest] = {"identity": identity, "selected_key": selected}
        return identity, selected

    def _load(self, identity: str) -> dict:
        models = self._get("/models/list")
        # A model-list failure never authorizes config-only IDs.
        previous = self.cache.peek(identity).get("videos", [])
        try:
            capabilities = self._get("/video/config")
        except MediaError:
            capabilities = None
        return build_catalog_snapshot(models, capabilities, previous_videos=previous)

    def read(self, *, force: bool = False) -> dict:
        selected = None
        if self.account_mode:
            try:
                identity, selected = self._account_identity()
            except _FetchError as error:
                previous = self._binding()
                if previous and error.status not in (401, 403):

                    def fail() -> dict:
                        raise _FetchError()

                    status = self.cache.read(previous["identity"], fail, force=True)
                    return {**status, **previous, "selection_confirmed": False}
                if previous:
                    self.cache.invalidate(previous["identity"])
                    with _BINDING_LOCK:
                        _BINDINGS.get(self.cache, {}).pop(self.digest, None)
                return {
                    "available": False,
                    "models": [],
                    "videos": [],
                    "stale": True,
                    "refreshing": False,
                    "updatedAt": None,
                    "error": connection_error_message(error.code)
                    or "Could not read the account or selected Key. Check Apixly connection settings.",
                    "error_code": error.code,
                    "selection_confirmed": False,
                }
        else:
            identity = catalog_identity({"mode": "manual", "key": self.token})
        status = self.cache.read(identity, lambda: self._load(identity), force=force)
        return {
            **status,
            "identity": identity,
            "selected_key": selected,
            "selection_confirmed": True,
        }
