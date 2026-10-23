import json
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
from dify_plugin import DifyPluginEnv
from dify_plugin.core.plugin_registration import PluginRegistration
from dify_plugin.entities.tool import ToolConfiguration, ToolProviderConfiguration

from apixly_media.client import MediaError
from tools.create_video import CreateVideoTool
from tools.edit_image import EditImageTool
from tools.generate_image import GenerateImageTool
from tools.query_task import QueryTaskTool


class ToolRuntimeTests(unittest.TestCase):
    def invoke(self, cls, parameters, result=None):
        tool = cls.from_credentials({"api_key": "fixture-key"})
        with patch("tools.base.MediaClient") as mocked:
            client = mocked.return_value
            if result is not None:
                client.query_task.return_value = result
            messages = list(tool._invoke(parameters))
        return client, messages

    def test_sdk_parses_all_yaml_declarations(self):
        provider = ToolProviderConfiguration.model_validate(
            yaml.safe_load(Path("provider/apixly.yaml").read_text())
        )
        self.assertEqual(provider.identity.name, "apixly_media")
        for name in ["generate_image", "edit_image", "create_video", "query_task"]:
            with self.subTest(name=name):
                entity = ToolConfiguration.model_validate(
                    yaml.safe_load(Path(f"tools/{name}.yaml").read_text())
                )
                self.assertEqual(entity.identity.name, name)

    def test_sdk_full_registration_resolves_exactly_one_class_per_entrypoint(self):
        plugin = PluginRegistration(DifyPluginEnv())
        self.assertEqual(set(plugin.tools_mapping), {"apixly_media"})
        _, _, tools = plugin.tools_mapping["apixly_media"]
        self.assertEqual(set(tools), {"generate_image", "edit_image", "create_video", "query_task"})

    def test_invalid_json_stops_before_api_calls(self):
        client, messages = self.invoke(
            GenerateImageTool, {"model": "exact", "prompt": "Draw", "parameters_json": "{broken"}
        )
        client.generate_image.assert_not_called()
        self.assertTrue(
            any(
                getattr(m.message, "json_object", {}).get("result_state") == "validation_error"
                for m in messages
            )
        )

    def test_validation_error_emits_stable_workflow_variables(self):
        _, messages = self.invoke(
            GenerateImageTool, {"model": "exact", "prompt": "Draw", "parameters_json": "{broken"}
        )
        variables = {
            m.message.variable_name: m.message.variable_value
            for m in messages
            if hasattr(m.message, "variable_name")
        }
        self.assertEqual(variables["result_state"], "validation_error")
        self.assertFalse(variables["success"])
        self.assertEqual(variables["task_id"], "")

    def test_generate_preserves_exact_model_id(self):
        client, _ = self.invoke(
            GenerateImageTool,
            {
                "model": "gemini-3-pro-image-preview",
                "prompt": "Draw",
                "parameters_json": '{"seed":0}',
            },
        )
        client.generate_image.assert_called_once_with(
            "gemini-3-pro-image-preview", "Draw", {"seed": 0}
        )

    def test_edit_preserves_all_references(self):
        client, _ = self.invoke(
            EditImageTool,
            {
                "model": "exact",
                "prompt": "Edit",
                "reference_images": '["https://cdn.example/1.png","https://cdn.example/2.png"]',
            },
        )
        client.edit_image.assert_called_once_with(
            "exact",
            "Edit",
            ["https://cdn.example/1.png", "https://cdn.example/2.png"],
            {},
            None,
        )

    def test_video_preserves_json_parameter_types(self):
        client, _ = self.invoke(
            CreateVideoTool,
            {
                "model": "exact",
                "prompt": "Move",
                "parameters_json": '{"seconds":4,"images":["https://cdn.example/1.png"]}',
            },
        )
        client.create_video.assert_called_once_with(
            "exact", "Move", {"seconds": 4, "images": ["https://cdn.example/1.png"]}
        )

    def test_named_image_parameters_are_easy_to_use_and_keep_types(self):
        client, _ = self.invoke(
            GenerateImageTool,
            {
                "model": "exact",
                "prompt": "Draw",
                "aspect_ratio": "1:1",
                "n": 1,
                "size": "1024x1024",
                "parameters_json": '{"seed":0}',
            },
        )
        client.generate_image.assert_called_once_with(
            "exact", "Draw", {"seed": 0, "aspect_ratio": "1:1", "n": 1, "size": "1024x1024"}
        )

    def test_conflicting_named_and_advanced_parameters_do_not_submit(self):
        client, messages = self.invoke(
            CreateVideoTool,
            {"model": "exact", "prompt": "Move", "seconds": 4, "parameters_json": '{"seconds":8}'},
        )
        client.create_video.assert_not_called()
        self.assertTrue(
            any(
                getattr(m.message, "json_object", {}).get("result_state") == "validation_error"
                for m in messages
            )
        )

    def test_single_reference_field_appends_explicit_additional_references(self):
        client, _ = self.invoke(
            EditImageTool,
            {
                "model": "exact",
                "prompt": "Edit",
                "reference_image": "https://cdn.example/first.png",
                "reference_images": '["https://cdn.example/second.png"]',
            },
        )
        client.edit_image.assert_called_once_with(
            "exact",
            "Edit",
            ["https://cdn.example/first.png", "https://cdn.example/second.png"],
            {},
            None,
        )

    def test_delayed_query_is_one_read_and_never_resubmits(self):
        task = {
            "id": "21",
            "status": "pending",
            "terminal": False,
            "success": False,
            "result_state": "pending",
            "urls": [],
        }
        with patch("tools.query_task.time.sleep") as sleep:
            client, _ = self.invoke(
                QueryTaskTool, {"kind": "image", "task_id": "21", "wait_seconds": 5}, task
            )
        sleep.assert_called_once_with(5)
        client.query_task.assert_called_once_with("image", "21")
        client.generate_image.assert_not_called()

    def test_all_tool_parameter_labels_have_english_and_chinese(self):
        for path in Path("tools").glob("*.yaml"):
            data = yaml.safe_load(path.read_text())
            self.assertIn("zh_Hans", data["identity"]["label"])
            for parameter in data["parameters"]:
                self.assertIn("en_US", parameter["label"])
                self.assertIn("zh_Hans", parameter["label"])

    def test_query_never_submits_and_download_is_optional(self):
        task = {
            "id": "video-4",
            "status": "completed",
            "terminal": True,
            "success": True,
            "result_state": "completed",
            "urls": ["https://apixly.ai/v1/videos/content?ref=x"],
            "kind": "video",
        }
        client, _ = self.invoke(
            QueryTaskTool, {"kind": "video", "task_id": "video-4", "download": False}, task
        )
        client.query_task.assert_called_once_with("video", "video-4")
        client.download_result.assert_not_called()
        client.create_video.assert_not_called()
        client.generate_image.assert_not_called()

    def test_download_failure_does_not_claim_file_delivery_success(self):
        tool = QueryTaskTool.from_credentials({"api_key": "fixture-key"})
        task = {
            "id": "video-4",
            "status": "completed",
            "terminal": True,
            "success": True,
            "result_state": "completed",
            "urls": ["https://apixly.ai/v1/videos/content?ref=x"],
            "kind": "video",
        }
        with patch("tools.base.MediaClient") as mocked:
            client = mocked.return_value
            client.query_task.return_value = task
            client.download_result.side_effect = MediaError("Result download timed out")
            messages = list(tool._invoke({"kind": "video", "task_id": "video-4", "download": True}))
        variables = {
            m.message.variable_name: m.message.variable_value
            for m in messages
            if hasattr(m.message, "variable_name")
        }
        self.assertFalse(variables["success"])
        self.assertTrue(variables["generation_success"])
        self.assertEqual(variables["result_state"], "download_error")
        self.assertEqual(variables["task_id"], "video-4")
        client.create_video.assert_not_called()
        client.generate_image.assert_not_called()

    def test_unqualified_mask_fields_are_rejected_at_public_entrypoint(self):
        for name in ("mask", "mask_url"):
            with self.subTest(name=name):
                client, messages = self.invoke(
                    EditImageTool,
                    {
                        "model": "exact",
                        "prompt": "Edit",
                        "reference_image": "https://cdn.example/input.png",
                        name: "https://cdn.example/mask.png",
                    },
                )
                client.edit_image.assert_not_called()
                errors = [
                    m.message.json_object for m in messages if hasattr(m.message, "json_object")
                ]
                self.assertEqual(errors[0]["result_state"], "validation_error")
                self.assertIn("not enabled", errors[0]["error"])

    def test_advanced_json_cannot_bypass_mask_qualification_gate(self):
        for name in ("mask", "mask_url", "MASK_URL"):
            with self.subTest(name=name):
                client, messages = self.invoke(
                    EditImageTool,
                    {
                        "model": "exact",
                        "prompt": "Edit",
                        "reference_image": "https://cdn.example/input.png",
                        "parameters_json": json.dumps({name: "https://cdn.example/mask.png"}),
                    },
                )
                client.edit_image.assert_not_called()
                self.assertTrue(
                    any(
                        getattr(m.message, "json_object", {}).get("result_state")
                        == "validation_error"
                        for m in messages
                    )
                )

    def test_released_tool_schema_does_not_advertise_mask(self):
        declaration = yaml.safe_load(Path("tools/edit_image.yaml").read_text())
        self.assertFalse(any(p["name"] in {"mask", "mask_url"} for p in declaration["parameters"]))

    def test_video_geometry_has_no_implicit_global_default(self):
        declaration = yaml.safe_load(Path("tools/create_video.yaml").read_text())
        parameters = {p["name"]: p for p in declaration["parameters"]}
        self.assertFalse(parameters["resolution"].get("default"))
        self.assertFalse(parameters["aspect_ratio"].get("default"))


if __name__ == "__main__":
    unittest.main()
