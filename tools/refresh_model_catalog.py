from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from apixly_media.catalog import build_model_options
from apixly_media.catalog_service import ModelCatalogService
from apixly_media.client import MediaError


class RefreshModelCatalogTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            snapshot = ModelCatalogService(self.runtime.credentials).read(force=True)
        except MediaError as error:
            snapshot = {
                "available": False,
                "models": [],
                "videos": [],
                "stale": True,
                "error": str(error),
            }
        result = {
            "success": bool(snapshot.get("available")),
            "stale": bool(snapshot.get("stale", True)),
            "error": snapshot.get("error") or snapshot.get("capabilitiesError") or "",
            "image_models": build_model_options(
                snapshot.get("models", []), snapshot.get("videos", []), "image"
            ),
            "video_models": build_model_options(
                snapshot.get("models", []), snapshot.get("videos", []), "video"
            ),
            "catalog": snapshot,
        }
        yield self.create_json_message(result)
        for name, value in result.items():
            yield self.create_variable_message(name, value)
        text = "Catalog refreshed. No generation was submitted."
        if not result["success"]:
            text = "Catalog unavailable. " + result["error"]
        elif result["stale"]:
            text = "Showing saved or partially available catalog options. " + result["error"]
        yield self.create_text_message(text)
