"""Confidential OAuth adapter; stores only the revocable scoped connection."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import time
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlencode, urlsplit

import httpx
from dify_plugin.entities.oauth import ToolOAuthCredentials
from dify_plugin.errors.tool import ToolProviderOAuthError
from werkzeug import Request

from apixly_media.client import MediaError

AUTHORIZE_URL = "https://apixly.ai/api/integrations/authorize"
TOKEN_URL = "https://apixly.ai/api/integrations/token"


def media_credentials(credentials: Mapping[str, Any]) -> tuple[str, bool]:
    """Choose one explicit credential type without falling back to another Key."""
    token, key = credentials.get("connection_token"), credentials.get("api_key")
    if token and key:
        raise MediaError("Choose one Apixly OAuth connection or manual API key credential.")
    if token:
        if not isinstance(token, str) or not re.fullmatch(r"apc_[A-Za-z0-9_-]{43}", token):
            raise MediaError("The Apixly connection token is invalid. Authorize again.")
        return token, True
    if not isinstance(key, str) or not key.strip():
        raise MediaError("Authorize an Apixly account or configure an Apixly API key.")
    return key, False


def _callback_uri(value: str) -> str:
    try:
        parsed = urlsplit(value)
        parsed.port
    except (ValueError, TypeError):
        raise ToolProviderOAuthError("The Dify callback URI is invalid.") from None
    host = parsed.hostname or ""
    loopback = host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".localhost")
    if (
        not isinstance(value, str)
        or len(value) > 2048
        or not host
        or parsed.username
        or parsed.password
        or parsed.fragment
        or any(ord(c) < 32 for c in value)
        or not (parsed.scheme == "https" or (parsed.scheme == "http" and loopback))
    ):
        raise ToolProviderOAuthError(
            "Use the exact HTTPS Dify callback URI; local loopback HTTP is allowed for testing."
        )
    return value


class OAuthConnection:
    def __init__(
        self,
        system_credentials: Mapping[str, Any],
        *,
        transport: httpx.BaseTransport | None = None,
    ):
        self.client_id = system_credentials.get("client_id")
        self.client_secret = system_credentials.get("client_secret")
        if any(
            not isinstance(v, str) or not v.strip() or len(v) > 1024
            for v in (self.client_id, self.client_secret)
        ):
            raise ToolProviderOAuthError(
                "A workspace administrator must configure a registered Apixly OAuth client ID and secret first."
            )
        self.transport = transport

    def _signature(self, redirect_uri: str, timestamp: str, nonce: str) -> str:
        message = json.dumps(
            [self.client_id, redirect_uri, timestamp, nonce], separators=(",", ":")
        ).encode()
        return hmac.new(self.client_secret.encode(), message, hashlib.sha256).hexdigest()

    def authorization_url(self, redirect_uri: str) -> str:
        redirect_uri = _callback_uri(redirect_uri)
        timestamp, nonce = str(int(time.time())), secrets.token_urlsafe(24)
        # Opaque signed state carries no verifier, identity, credential or secret.
        # Dify separately owns its HttpOnly OAuth context cookie and tenant scope.
        state = ".".join(("v1", timestamp, nonce, self._signature(redirect_uri, timestamp, nonce)))
        return (
            AUTHORIZE_URL
            + "?"
            + urlencode(
                {
                    "response_type": "code",
                    "client_id": self.client_id,
                    "redirect_uri": redirect_uri,
                    "state": state,
                }
            )
        )

    def credentials(self, redirect_uri: str, request: Request) -> ToolOAuthCredentials:
        redirect_uri = _callback_uri(redirect_uri)
        if request.args.get("error"):
            raise ToolProviderOAuthError(
                "Apixly authorization was declined or expired. Start authorization again."
            )
        codes, states = request.args.getlist("code"), request.args.getlist("state")
        if len(codes) != 1 or not codes[0] or len(codes[0]) > 4096 or len(states) != 1:
            raise ToolProviderOAuthError(
                "The OAuth callback is incomplete. Start authorization again."
            )
        match = re.fullmatch(r"v1\.(\d{1,12})\.([A-Za-z0-9_-]{32})\.([a-f0-9]{64})", states[0])
        if not match:
            raise ToolProviderOAuthError(
                "OAuth state validation failed. Start authorization again."
            )
        timestamp, nonce, signature = match.groups()
        age = time.time() - int(timestamp)
        if (
            age < -60
            or age > 600
            or not hmac.compare_digest(signature, self._signature(redirect_uri, timestamp, nonce))
        ):
            raise ToolProviderOAuthError(
                "OAuth state is invalid or expired. Start authorization again."
            )
        try:
            with httpx.Client(
                transport=self.transport, timeout=15, follow_redirects=False, trust_env=False
            ) as client:
                response = client.post(
                    TOKEN_URL,
                    json={
                        "grant_type": "authorization_code",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "code": codes[0],
                        "redirect_uri": redirect_uri,
                    },
                    headers={"Accept": "application/json", "Cache-Control": "no-store"},
                )
        except httpx.HTTPError:
            raise ToolProviderOAuthError(
                "The connection exchange could not be confirmed. It was not retried; start authorization again."
            ) from None
        if response.status_code != 200:
            raise ToolProviderOAuthError(
                f"Apixly authorization exchange returned HTTP {response.status_code}. It was not retried; start authorization again."
            )
        try:
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError
            token = data["access_token"]
            media_credentials({"connection_token": token})
            expires = data["expires_in"]
            revision = data["selection_revision"]
            if (
                data.get("token_type") != "Bearer"
                or type(expires) is not int
                or not 0 < expires <= 7776000
                or type(revision) is not int
                or revision < 0
            ):
                raise ValueError
            account, key = data["account"], data["selected_key"]
            connection_id, account_id, key_id = (data["connection_id"], account["id"], key["id"])
            if any(
                type(v) not in (str, int) or not str(v) or len(str(v)) > 128
                for v in (connection_id, account_id, key_id)
            ):
                raise ValueError
            account_name, key_name, masked = account.get("name", ""), key["name"], key["masked"]
            if any(
                not isinstance(v, str) or len(v) > 256 for v in (account_name, key_name, masked)
            ):
                raise ValueError
        except (ValueError, KeyError, TypeError, MediaError):
            raise ToolProviderOAuthError(
                "Apixly returned an invalid scoped connection response. No API key or website login token was stored."
            ) from None
        return ToolOAuthCredentials(
            credentials={
                "connection_token": token,
                "connection_id": str(connection_id),
                "account_id": str(account_id),
                "account_name": account_name,
                "selected_key_id": str(key_id),
                "key_name": key_name,
                "key_masked": masked,
                "selection_revision": revision,
            },
            expires_at=int(time.time()) + expires,
        )
