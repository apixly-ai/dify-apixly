from dify_plugin import ToolProvider


class ApixlyCreativeProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, str]) -> None:
        # This provider only compiles text locally and requires no credentials.
        return None
