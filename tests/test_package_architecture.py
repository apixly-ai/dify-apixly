import unittest
from pathlib import Path

import yaml
from dify_plugin import DifyPluginEnv
from dify_plugin.core.plugin_registration import PluginRegistration


class SingleProviderArchitectureTests(unittest.TestCase):
    def test_media_package_preserves_its_single_credentialed_provider(self):
        manifest = yaml.safe_load(Path("manifest.yaml").read_text())
        self.assertEqual(manifest["plugins"]["tools"], ["provider/apixly.yaml"])
        registration = PluginRegistration(DifyPluginEnv())
        self.assertEqual(set(registration.tools_mapping), {"apixly_media"})
        provider, _, tools = registration.tools_mapping["apixly_media"]
        self.assertTrue(
            next(x for x in provider.credentials_schema if x.name == "api_key").required
        )
        self.assertEqual(set(tools), {"generate_image", "edit_image", "create_video", "query_task"})

    def test_unused_creative_runtime_is_not_present_in_media_package(self):
        for path in [
            "provider/creative.yaml",
            "provider/creative.py",
            "tools/compose_creative_prompt.py",
            "tools/compose_creative_prompt.yaml",
            "apixly_media/creative.py",
        ]:
            with self.subTest(path=path):
                self.assertFalse(Path(path).exists())
