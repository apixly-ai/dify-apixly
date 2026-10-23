from collections.abc import Mapping
from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.entities.oauth import ToolOAuthCredentials
from dify_plugin.errors.tool import ToolProviderCredentialValidationError, ToolProviderOAuthError
from werkzeug import Request

from apixly_media.client import MediaClient, MediaError
from apixly_media.connection import OAuthConnection, media_credentials


class ApixlyProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, str]) -> None:
        client = None
        try:
            token, account_mode = media_credentials(credentials)
            client = MediaClient(token, account_mode=account_mode)
            client.validate_credentials()
        except MediaError as exc:
            raise ToolProviderCredentialValidationError(str(exc)) from exc
        finally:
            if client is not None:
                client.close()

    def _oauth_get_authorization_url(
        self, redirect_uri: str, system_credentials: Mapping[str, Any]
    ) -> str:
        return OAuthConnection(system_credentials).authorization_url(redirect_uri)

    def _oauth_get_credentials(
        self, redirect_uri: str, system_credentials: Mapping[str, Any], request: Request
    ) -> ToolOAuthCredentials:
        return OAuthConnection(system_credentials).credentials(redirect_uri, request)

    def _oauth_refresh_credentials(
        self,
        redirect_uri: str,
        system_credentials: Mapping[str, Any],
        credentials: Mapping[str, Any],
    ) -> ToolOAuthCredentials:
        raise ToolProviderOAuthError(
            "The Apixly connection has expired. Authorize again to reconnect your selected Key."
        )
