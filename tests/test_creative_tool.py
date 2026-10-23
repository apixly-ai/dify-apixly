import importlib
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
from dify_plugin import DifyPluginEnv
from dify_plugin.core.plugin_registration import PluginRegistration

from apixly_media.creative import compose_creative_prompt


class CreativeToolTests(unittest.TestCase):
    def tool_class(self):
        try:
            return importlib.import_module(
                "tools.compose_creative_prompt"
            ).ComposeCreativePromptTool
        except ModuleNotFoundError:
            self.fail("The credential-free creative tool has not been implemented.")

    def invoke(self, parameters):
        with patch("tools.base.MediaClient") as client:
            messages = list(self.tool_class().from_credentials({})._invoke(parameters))
            client.assert_not_called()
        variables = {
            m.message.variable_name: m.message.variable_value
            for m in messages
            if hasattr(m.message, "variable_name")
        }
        objects = [m.message.json_object for m in messages if hasattr(m.message, "json_object")]
        return variables, objects

    def test_sdk_registers_a_credential_free_provider_without_weakening_api_provider(self):
        registration = PluginRegistration(DifyPluginEnv())
        self.assertEqual(set(registration.tools_mapping), {"apixly_media", "apixly_creative"})
        provider, _, tools = registration.tools_mapping["apixly_creative"]
        self.assertEqual(provider.credentials_schema, [])
        self.assertEqual(set(tools), {"compose_creative_prompt"})
        original, _, original_tools = registration.tools_mapping["apixly_media"]
        self.assertTrue(
            next(x for x in original.credentials_schema if x.name == "api_key").required
        )
        self.assertEqual(
            set(original_tools), {"generate_image", "edit_image", "create_video", "query_task"}
        )

    def test_disabled_controls_keep_exact_prompt_and_never_construct_an_api_client(self):
        variables, _ = self.invoke(
            {
                "prompt": "  keep\n spacing  ",
                "mode": "edit",
                "angle_enabled": False,
                "angle_preset": "back",
            }
        )
        self.assertTrue(variables["success"])
        self.assertEqual(variables["final_prompt"], "  keep\n spacing  ")
        self.assertFalse(variables["changed"])

    def test_named_inputs_compile_exact_canonical_edit_prompt_and_types(self):
        parameters = {
            "prompt": "Keep the toy car.",
            "mode": "edit",
            "angle_enabled": True,
            "angle_yaw": 90,
            "angle_pitch": 55,
            "angle_shot": "close_up",
            "lighting_enabled": True,
            "lighting_preset": "goldenHour",
            "lighting_key_light": "left",
            "camera_enabled": True,
            "camera_focal": 85,
            "camera_aperture": "f/1.4",
        }
        payload = {
            "prompt": parameters["prompt"],
            "mode": "edit",
            "tools": {
                "angle": {"enabled": True, "yaw": 90, "pitch": 55, "shot": "close_up"},
                "lighting": {"enabled": True, "preset": "goldenHour", "keyLight": "left"},
                "camera": {"enabled": True, "focal": 85, "aperture": "f/1.4"},
            },
        }
        expected = compose_creative_prompt(payload)
        variables, objects = self.invoke(parameters)
        for field, value in expected.items():
            self.assertEqual(variables[field], value)
        self.assertTrue(objects[-1]["success"])
        self.assertEqual(variables["result_state"], "composed")

    def test_missing_continuous_light_fields_do_not_override_legacy_direction(self):
        variables, _ = self.invoke(
            {
                "prompt": "",
                "lighting_enabled": True,
                "lighting_key_light": "left",
                "lighting_yaw": "",
                "lighting_pitch": "",
            }
        )
        self.assertEqual(
            variables["final_prompt"],
            "Lighting: key light from camera left, dramatic side lighting",
        )
        variables, _ = self.invoke(
            {
                "prompt": "",
                "lighting_enabled": True,
                "lighting_key_light": "left",
                "lighting_yaw": 0,
                "lighting_pitch": 0,
            }
        )
        self.assertEqual(variables["final_prompt"], "")

    def test_client_forged_prompt_and_invalid_values_fail_with_safe_field_paths(self):
        for parameters, path in [
            ({"prompt": "base", "final_prompt": "FORGED_PRIVATE_VALUE"}, "final_prompt"),
            ({"prompt": "base", "angle_enabled": "true"}, "tools.angle.enabled"),
            ({"prompt": "base", "camera_body": "PRIVATE_UNSUPPORTED_CAMERA"}, "tools.camera.body"),
        ]:
            with self.subTest(path=path):
                variables, objects = self.invoke(parameters)
                self.assertFalse(variables["success"])
                self.assertEqual(variables["error_path"], path)
                self.assertEqual(variables["final_prompt"], "")
                self.assertNotIn("PRIVATE", str(objects))
                self.assertIn(path, variables["error"])

    def test_invalid_tool_input_container_returns_a_safe_error(self):
        for parameters in [None, [], "PRIVATE_INVALID_CONTAINER"]:
            with self.subTest(input_type=type(parameters).__name__):
                variables, objects = self.invoke(parameters)
                self.assertFalse(variables["success"])
                self.assertEqual(variables["error_path"], "payload")
                self.assertNotIn("PRIVATE", str(objects))

    def test_tool_declaration_is_bilingual_and_controls_default_off(self):
        path = Path("tools/compose_creative_prompt.yaml")
        self.assertTrue(path.exists(), "The new tool declaration is missing.")
        entity = yaml.safe_load(path.read_text())
        fields = {p["name"]: p for p in entity["parameters"]}
        for name in ["angle_enabled", "lighting_enabled", "camera_enabled"]:
            self.assertIs(fields[name]["default"], False)
            self.assertEqual(fields[name]["type"], "boolean")
        self.assertNotIn("default", fields["lighting_yaw"])
        self.assertNotIn("default", fields["lighting_pitch"])
        self.assertNotIn("api_key", fields)
        for field in fields.values():
            self.assertTrue(field["label"]["en_US"])
            self.assertTrue(field["label"]["zh_Hans"])


if __name__ == "__main__":
    unittest.main()
