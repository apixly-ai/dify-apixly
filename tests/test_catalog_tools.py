import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from apixly_media.client import MediaError
from tools import base
from tools.refresh_model_catalog import RefreshModelCatalogTool


class CatalogToolTests(unittest.TestCase):
    def test_manual_exact_model_overrides_picker_without_modifying_id(self):
        self.assertEqual(
            base.selected_model({"model": "EXACT-manual-model", "catalog_model": "picked-model"}),
            "EXACT-manual-model",
        )
        self.assertEqual(
            base.selected_model({"model": "", "catalog_model": "picked-model"}), "picked-model"
        )
        self.assertEqual(base.selected_model({"catalog_model": "future@MODEL/2"}), "future@MODEL/2")
        for parameters in [
            {},
            {"model": False, "catalog_model": "picked-model"},
            {"model": "   ", "catalog_model": "picked-model"},
        ]:
            with self.assertRaises(MediaError):
                base.selected_model(parameters)

    def test_three_media_schemas_offer_dynamic_picker_and_no_default_manual_override(self):
        for name in ["generate_image", "edit_image", "create_video"]:
            with self.subTest(tool=name):
                data = yaml.safe_load(Path(f"tools/{name}.yaml").read_text())
                fields = {field["name"]: field for field in data["parameters"]}
                self.assertEqual(fields["catalog_model"]["type"], "dynamic-select")
                self.assertFalse(fields["catalog_model"]["required"])
                self.assertFalse(fields["model"]["required"])
                self.assertNotIn("default", fields["model"])
                self.assertIn("overrides picker", fields["model"]["label"]["en_US"])

    def test_refresh_catalog_is_read_only_and_exposes_stale_or_failure_status(self):
        snapshot = {
            "available": True,
            "models": [{"id": "image", "type": "image"}],
            "videos": [],
            "stale": True,
            "refreshing": False,
            "error": "Saved options",
            "updatedAt": 100,
            "capabilitiesError": None,
        }
        with patch("tools.refresh_model_catalog.ModelCatalogService") as service:
            service.return_value.read.return_value = snapshot
            messages = list(
                RefreshModelCatalogTool.from_credentials({"api_key": "fixture"})._invoke({})
            )
            service.return_value.read.assert_called_once_with(force=True)
        variables = {
            message.message.variable_name: message.message.variable_value
            for message in messages
            if hasattr(message.message, "variable_name")
        }
        self.assertTrue(variables["success"])
        self.assertTrue(variables["stale"])
        self.assertEqual(variables["image_models"][0]["id"], "image")
        self.assertEqual(variables["video_models"], [])
        with patch(
            "tools.refresh_model_catalog.ModelCatalogService",
            side_effect=MediaError("Authorize first."),
        ):
            failed = list(RefreshModelCatalogTool.from_credentials({})._invoke({}))
        outputs = {
            message.message.variable_name: message.message.variable_value
            for message in failed
            if hasattr(message.message, "variable_name")
        }
        self.assertFalse(outputs["success"])
        self.assertEqual(outputs["error"], "Authorize first.")


if __name__ == "__main__":
    unittest.main()
