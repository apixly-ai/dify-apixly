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
                            [submit[0]["id"], "task_id"],
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
            ["video_reference", "output"],
        )
        defaults = {v["variable"]: v["default"] for v in nodes["image_start"]["data"]["variables"]}
        self.assertEqual(defaults["video_model"], "grok-imagine-video-1.5-preview")
        self.assertEqual(defaults["video_seconds"], 3)
        self.assertEqual(len([n for n in nodes.values() if n["data"]["type"] == "loop"]), 2)


if __name__ == "__main__":
    unittest.main()
