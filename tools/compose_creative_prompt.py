"""Credential-free Dify adapter for the canonical offline compiler."""

from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from apixly_media.creative import CreativePromptError, compose_creative_prompt

FIELD_PATHS = {
    "angle_enabled": ("angle", "enabled"),
    "angle_preset": ("angle", "preset"),
    "angle_yaw": ("angle", "yaw"),
    "angle_pitch": ("angle", "pitch"),
    "angle_shot": ("angle", "shot"),
    "angle_show_prompt": ("angle", "showPrompt"),
    "lighting_enabled": ("lighting", "enabled"),
    "lighting_preset": ("lighting", "preset"),
    "lighting_brightness": ("lighting", "brightness"),
    "lighting_color": ("lighting", "color"),
    "lighting_key_light": ("lighting", "keyLight"),
    "lighting_yaw": ("lighting", "lightYaw"),
    "lighting_pitch": ("lighting", "lightPitch"),
    "lighting_rim_light": ("lighting", "rimLight"),
    "lighting_smart_text": ("lighting", "smartText"),
    "lighting_view": ("lighting", "view"),
    "camera_enabled": ("camera", "enabled"),
    "camera_body": ("camera", "body"),
    "camera_lens": ("camera", "lens"),
    "camera_focal": ("camera", "focal"),
    "camera_aperture": ("camera", "aperture"),
}


def creative_payload(parameters: dict[str, Any]) -> dict[str, Any]:
    if type(parameters) is not dict:
        raise CreativePromptError("payload", "must be an object")
    for name in parameters:
        if name not in {"prompt", "mode", *FIELD_PATHS}:
            path = name if isinstance(name, str) and name.isidentifier() else "unknown_field"
            raise CreativePromptError(path, "unknown tool input")
    tools = {}
    for name, (group, field) in FIELD_PATHS.items():
        if name not in parameters:
            continue
        value = parameters[name]
        # Empty optional native numeric inputs are unset, not synthetic zeroes.
        # In particular, omitted lighting coordinates must not replace keyLight.
        if name in {"lighting_yaw", "lighting_pitch", "camera_focal"} and value in ("", None):
            continue
        tools.setdefault(group, {})[field] = value
    return {
        "prompt": parameters.get("prompt", ""),
        "mode": parameters.get("mode", "generate"),
        "tools": tools,
    }


class ComposeCreativePromptTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            result = compose_creative_prompt(creative_payload(tool_parameters))
            output = {
                "success": True,
                "result_state": "composed",
                "error_path": "",
                "error": "",
                **result,
            }
            yield self.create_text_message(result["final_prompt"])
        except CreativePromptError as exc:
            output = {
                "success": False,
                "result_state": "validation_error",
                "error_path": exc.path,
                "error": str(exc),
                "final_prompt": "",
                "sections": [],
                "applied_tools": [],
                "changed": False,
            }
            yield self.create_text_message(str(exc))
        yield self.create_json_message(output)
        for name in [
            "success",
            "result_state",
            "error_path",
            "error",
            "final_prompt",
            "sections",
            "applied_tools",
            "changed",
        ]:
            yield self.create_variable_message(name, output[name])
