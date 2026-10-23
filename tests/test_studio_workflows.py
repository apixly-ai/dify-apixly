import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import build_workflows


class StudioWorkflowTests(unittest.TestCase):
    def workflow(self, kind):
        builder = getattr(build_workflows, "build_studio_workflow", None)
        self.assertTrue(callable(builder), "Studio workflow builder is missing")
        return builder(kind, "a" * 64, creative_checksum="b" * 64)

    def nodes(self, document):
        return {node["id"]: node for node in document["workflow"]["graph"]["nodes"]}

    def test_preview_uses_three_small_panels_and_one_small_compose_without_media(self):
        doc = self.workflow("preview")
        tools = [
            node["data"]["tool_name"]
            for node in self.nodes(doc).values()
            if node["data"]["type"] == "tool"
        ]
        self.assertCountEqual(tools, ["viewpoint", "lighting", "camera_lens", "compose_prompt"])
        self.assertEqual(len(doc["dependencies"]), 1)
        self.assertIn(
            "apixly_creative:0.1.0@" + "b" * 64,
            doc["dependencies"][0]["value"]["plugin_unique_identifier"],
        )
        self.assertNotIn("api_key", str(doc))

    def test_every_panel_defaults_off_and_lighting_does_not_invent_coordinates(self):
        for kind in ["preview", "image", "edit", "video"]:
            with self.subTest(kind=kind):
                nodes = self.nodes(self.workflow(kind))
                for panel in ["studio_viewpoint", "studio_lighting", "studio_camera"]:
                    self.assertEqual(
                        nodes[panel]["data"]["tool_parameters"]["enabled"],
                        {"type": "constant", "value": False},
                    )
                light = nodes["studio_lighting"]["data"]["tool_parameters"]
                self.assertEqual(light["direction_mode"], {"type": "constant", "value": "named"})
                self.assertNotIn("yaw", light)
                self.assertNotIn("pitch", light)

    def test_settings_use_native_string_mixed_bindings_and_edit_mode_is_applied_once(self):
        for kind in ["preview", "image", "edit", "video"]:
            nodes = self.nodes(self.workflow(kind))
            compose = nodes["creative_compose"]["data"]
            self.assertEqual(compose["tool_name"], "compose_prompt")
            params = compose["tool_parameters"]
            self.assertEqual(
                set(params),
                {"prompt", "mode", "viewpoint_settings", "lighting_settings", "camera_settings"},
            )
            self.assertEqual(params["prompt"], {"type": "mixed", "value": "{{#start.prompt#}}"})
            for field, node in [
                ("viewpoint_settings", "studio_viewpoint"),
                ("lighting_settings", "studio_lighting"),
                ("camera_settings", "studio_camera"),
            ]:
                self.assertEqual(
                    params[field], {"type": "mixed", "value": "{{#" + node + ".settings#}}"}
                )
            self.assertEqual(params["mode"]["value"], "edit" if kind == "edit" else "generate")

    def test_control_sequence_joins_once_and_composition_failure_stops_before_submit(self):
        for kind in ["preview", "image", "edit", "video"]:
            doc = self.workflow(kind)
            edges = doc["workflow"]["graph"]["edges"]
            route = [
                "start",
                "studio_viewpoint",
                "studio_lighting",
                "studio_camera",
                "creative_compose",
                "creative_ready",
            ]
            for source, target in zip(route, route[1:]):
                self.assertTrue(
                    any(edge["source"] == source and edge["target"] == target for edge in edges)
                )
            self.assertEqual(sum(edge["target"] == "creative_compose" for edge in edges), 1)
            self.assertTrue(
                any(
                    edge["source"] == "creative_ready"
                    and edge["sourceHandle"] == "false"
                    and edge["target"] == "creative_error"
                    for edge in edges
                )
            )
            nodes = self.nodes(doc)
            if kind != "preview":
                self.assertFalse(nodes["submit"]["data"]["retry_config"]["retry_enabled"])
                self.assertNotIn("parentId", nodes["submit"])
                self.assertEqual(
                    nodes["submit"]["data"]["tool_parameters"]["prompt"],
                    {"type": "mixed", "value": "{{#creative_compose.final_prompt#}}"},
                )

    def test_legacy_eight_builders_remain_unchanged_by_recommended_studio_builds(self):
        before = build_workflows.build_creative_workflow(
            "edit", "a" * 64, creative_checksum="b" * 64
        )
        self.workflow("edit")
        after = build_workflows.build_creative_workflow(
            "edit", "a" * 64, creative_checksum="b" * 64
        )
        self.assertEqual(before, after)
        old = self.nodes(after)["creative_compose"]["data"]
        self.assertEqual(old["tool_name"], "compose_creative_prompt")
        self.assertIn("angle_enabled", old["tool_parameters"])

    def test_cli_adds_four_studio_files_without_replacing_existing_eight(self):
        with tempfile.TemporaryDirectory(dir="validation") as directory:
            subprocess.run(
                [
                    sys.executable,
                    "scripts/build_workflows.py",
                    "--checksum",
                    "a" * 64,
                    "--creative-checksum",
                    "b" * 64,
                    "--output",
                    directory,
                ],
                check=True,
            )
            files = {path.name for path in Path(directory).glob("*.yml")}
            self.assertEqual(len(files), 12)
            self.assertTrue(
                {
                    f"apixly-studio-{kind}-workflow.yml"
                    for kind in ["preview", "image", "edit", "video"]
                }
                <= files
            )
            self.assertIn("apixly-creative-preview-workflow.yml", files)
            self.assertIn("apixly-image-to-video-workflow.yml", files)


if __name__ == "__main__":
    unittest.main()
