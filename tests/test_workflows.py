import json
import unittest

from scripts.build_workflows import build_image_to_video, build_workflow


class WorkflowSafetyTests(unittest.TestCase):
    checksum = "a" * 64

    def nodes(self, workflow):
        return {node["id"]: node for node in workflow["workflow"]["graph"]["nodes"]}

    def test_real_package_and_tool_identifiers_are_used(self):
        workflow = build_workflow("image", self.checksum)
        dependency = workflow["dependencies"][0]
        self.assertEqual(dependency["type"], "package")
        self.assertEqual(
            dependency["value"]["plugin_unique_identifier"],
            f"apixly-ai/apixly_media:0.1.0@{self.checksum}",
        )
        for node in self.nodes(workflow).values():
            if node["data"]["type"] == "tool":
                self.assertEqual(node["data"]["provider_id"], "apixly-ai/apixly_media/apixly_media")

    def test_end_output_names_are_unique_across_all_branches_for_native_publish(self):
        workflows = [build_workflow(kind, self.checksum) for kind in ("image", "edit", "video")]
        workflows.append(build_image_to_video(self.checksum))
        for workflow in workflows:
            with self.subTest(app=workflow["app"]["name"]):
                names = [
                    output["variable"]
                    for node in self.nodes(workflow).values()
                    if node["data"]["type"] == "end"
                    for output in node["data"]["outputs"]
                ]
                self.assertEqual(len(names), len(set(names)))

    def test_all_string_bindings_use_native_v2_mixed_inputs_to_survive_ui_mount(self):
        names = {
            "model",
            "prompt",
            "parameters_json",
            "reference_image",
            "reference_images",
            "resolution",
            "aspect_ratio",
            "task_id",
        }
        workflows = [build_workflow(kind, self.checksum) for kind in ("image", "edit", "video")]
        workflows.append(build_image_to_video(self.checksum))
        for workflow in workflows:
            for node in self.nodes(workflow).values():
                for name, value in node["data"].get("tool_parameters", {}).items():
                    if name in names and value["type"] != "constant":
                        with self.subTest(app=workflow["app"]["name"], node=node["id"], field=name):
                            self.assertEqual(value["type"], "mixed")
                            self.assertIsInstance(value["value"], str)
                            self.assertTrue(value["value"].startswith("{{#"))

    def test_each_workflow_submits_once_outside_bounded_loop(self):
        for kind, submit_name in [
            ("image", "generate_image"),
            ("edit", "edit_image"),
            ("video", "create_video"),
        ]:
            with self.subTest(kind=kind):
                workflow = build_workflow(kind, self.checksum)
                nodes = self.nodes(workflow)
                submit = [n for n in nodes.values() if n["data"].get("tool_name") == submit_name]
                self.assertEqual(len(submit), 1)
                self.assertNotIn("parentId", submit[0])
                self.assertFalse(submit[0]["data"]["retry_config"]["retry_enabled"])
                loops = [n for n in nodes.values() if n["data"]["type"] == "loop"]
                self.assertEqual(len(loops), 1)
                self.assertEqual(loops[0]["data"]["loop_count"], 60)
                self.assertIs(loops[0]["data"]["break_conditions"][0]["value"], True)
                for n in nodes.values():
                    if n.get("parentId") == loops[0]["id"] and n["data"]["type"] == "tool":
                        self.assertEqual(n["data"]["tool_name"], "query_task")
                        self.assertEqual(
                            n["data"]["tool_parameters"]["task_id"]["value"],
                            "{{#" + submit[0]["id"] + ".task_id#}}",
                        )

    def test_final_query_returns_dify_files_and_preserves_task_id(self):
        workflow = build_workflow("video", self.checksum)
        nodes = self.nodes(workflow)
        final = nodes["final_query"]
        self.assertNotIn("parentId", final)
        self.assertTrue(final["data"]["tool_parameters"]["download"]["value"])
        end = nodes["result"]["data"]
        files = next(x for x in end["outputs"] if x["variable"] == "files")
        self.assertEqual(files["value_selector"], ["final_query", "files"])
        self.assertEqual(files["value_type"], "array[file]")

    def test_submission_failure_has_separate_stop_branch(self):
        workflow = build_workflow("image", self.checksum)
        edges = workflow["workflow"]["graph"]["edges"]
        self.assertTrue(
            any(
                e["source"] == "has_task"
                and e["sourceHandle"] == "false"
                and e["target"] == "submit_error"
                for e in edges
            )
        )
        self.assertFalse(
            any(e["source"] == "submit_error" and e["target"] == "submit" for e in edges)
        )
        self.assertNotIn("api_key", json.dumps(workflow))

    def test_edit_starter_accepts_a_normal_encoded_reference_image(self):
        workflow = build_workflow("edit", self.checksum)
        inputs = {v["variable"]: v for v in self.nodes(workflow)["start"]["data"]["variables"]}
        self.assertGreaterEqual(inputs["reference_image"]["max_length"], 200_000)
        self.assertGreaterEqual(inputs["additional_images"]["max_length"], 200_000)

    def test_released_edit_workflow_has_no_unqualified_mask_input(self):
        workflow = build_workflow("edit", self.checksum)
        nodes = self.nodes(workflow)
        self.assertFalse(
            any(v["variable"] in {"mask", "mask_url"} for v in nodes["start"]["data"]["variables"])
        )
        self.assertNotIn("mask", nodes["submit"]["data"]["tool_parameters"])

    def test_image_to_video_connects_generated_urls_and_submits_each_stage_once(self):
        workflow = build_image_to_video(self.checksum)
        nodes = self.nodes(workflow)
        submits = [
            n
            for n in nodes.values()
            if n["data"].get("tool_name") in {"generate_image", "create_video"}
        ]
        self.assertEqual(len(submits), 2)
        self.assertTrue(all("parentId" not in n for n in submits))
        self.assertTrue(all(not n["data"]["retry_config"]["retry_enabled"] for n in submits))
        self.assertEqual(
            nodes["video_reference"]["data"]["variables"][0]["value_selector"],
            ["image_final_query", "urls"],
        )
        self.assertIn("tojson", nodes["video_reference"]["data"]["template"])
        self.assertEqual(
            nodes["video_submit"]["data"]["tool_parameters"]["parameters_json"]["value"],
            "{{#video_reference.output#}}",
        )
        self.assertEqual(
            nodes["video_submit"]["data"]["tool_parameters"]["parameters_json"]["type"],
            "mixed",
        )
        defaults = {v["variable"]: v["default"] for v in nodes["image_start"]["data"]["variables"]}
        self.assertEqual(defaults["video_model"], "grok-imagine-video-1.5-preview")
        self.assertEqual(defaults["video_seconds"], 3)
        self.assertNotIn("video_resolution", defaults)
        self.assertNotIn("video_aspect_ratio", defaults)
        self.assertNotIn("resolution", nodes["video_submit"]["data"]["tool_parameters"])
        self.assertNotIn("aspect_ratio", nodes["video_submit"]["data"]["tool_parameters"])
        self.assertEqual(len([n for n in nodes.values() if n["data"]["type"] == "loop"]), 2)


if __name__ == "__main__":
    unittest.main()
