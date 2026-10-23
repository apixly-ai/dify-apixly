from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from apixly_media.client import MediaClient, MediaError


class ApixlyProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, str]) -> None:
        client = None
        try:
            client = MediaClient(credentials.get("api_key", ""))
            client.validate_credentials()
        except MediaError as exc:
            raise ToolProviderCredentialValidationError(str(exc)) from exc
        finally:
            if client is not None:
                client.close()
