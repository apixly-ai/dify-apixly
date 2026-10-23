import unittest

from scripts import build_workflows


class CreativeWorkflowTests(unittest.TestCase):
    checksum = "a" * 64

    def workflow(self, kind):
        builder = getattr(build_workflows, "build_creative_workflow", None)
        self.assertTrue(callable(builder), "Creative workflow builder is not implemented.")
        return builder(kind, self.checksum, creative_checksum="b" * 64)

    def nodes(self, workflow):
        return {n["id"]: n for n in workflow["workflow"]["graph"]["nodes"]}

    def test_free_preview_has_no_api_provider_or_generation_node(self):
        workflow = self.workflow("preview")
        nodes = self.nodes(workflow)
        tool_nodes = [n for n in nodes.values() if n["data"]["type"] == "tool"]
        self.assertEqual(len(tool_nodes), 1)
        self.assertEqual(
            tool_nodes[0]["data"]["provider_id"], "apixly-ai/apixly_creative/apixly_creative"
        )
        self.assertEqual(tool_nodes[0]["data"]["tool_name"], "compose_creative_prompt")
        self.assertNotIn("api_key", str(workflow))
        self.assertFalse(any(n["data"]["type"] == "loop" for n in nodes.values()))

    def test_all_formal_examples_default_off_and_preserve_original_prompt(self):
        for kind in ["preview", "image", "edit", "video"]:
            with self.subTest(kind=kind):
                nodes = self.nodes(self.workflow(kind))
                compose = nodes["creative_compose"]["data"]["tool_parameters"]
                for name in ["angle_enabled", "lighting_enabled", "camera_enabled"]:
                    self.assertIs(compose[name]["value"], False)
                self.assertNotIn("lighting_yaw", compose)
                self.assertNotIn("lighting_pitch", compose)
                self.assertNotIn("camera_focal", compose)
                self.assertEqual(
                    compose["prompt"], {"type": "mixed", "value": "{{#start.prompt#}}"}
                )

    def test_compose_failure_stops_before_any_paid_submission(self):
        for kind, media_tool in [
            ("image", "generate_image"),
            ("edit", "edit_image"),
            ("video", "create_video"),
        ]:
            with self.subTest(kind=kind):
                workflow = self.workflow(kind)
                nodes = self.nodes(workflow)
                submits = [n for n in nodes.values() if n["data"].get("tool_name") == media_tool]
                self.assertEqual(len(submits), 1)
                self.assertNotIn("parentId", submits[0])
                self.assertFalse(submits[0]["data"]["retry_config"]["retry_enabled"])
                self.assertEqual(
                    submits[0]["data"]["tool_parameters"]["prompt"],
                    {"type": "mixed", "value": "{{#creative_compose.final_prompt#}}"},
                )
                conditions = nodes["creative_ready"]["data"]["cases"][0]["conditions"]
                self.assertTrue(
                    any(
                        c["variable_selector"] == ["creative_compose", "success"]
                        and c["value"] is True
                        for c in conditions
                    )
                )
                edges = workflow["workflow"]["graph"]["edges"]
                false_edge = next(
                    e
                    for e in edges
                    if e["source"] == "creative_ready" and e["sourceHandle"] == "false"
                )
                self.assertEqual(nodes[false_edge["target"]]["data"]["type"], "end")
                self.assertFalse(any(e["source"] == false_edge["target"] for e in edges))
                self.assertTrue(
                    any(
                        e["source"] == "creative_ready"
                        and e["sourceHandle"] == "true"
                        and e["target"] == "submit"
                        for e in edges
                    )
                )

    def test_outputs_keep_final_prompt_and_error_variables_unique(self):
        for kind in ["preview", "image", "edit", "video"]:
            with self.subTest(kind=kind):
                nodes = self.nodes(self.workflow(kind))
                ends = [n["data"]["outputs"] for n in nodes.values() if n["data"]["type"] == "end"]
                variables = [v["variable"] for end in ends for v in end]
                self.assertEqual(len(variables), len(set(variables)))
                self.assertTrue(
                    any(
                        v["value_selector"] == ["creative_compose", "final_prompt"]
                        for end in ends
                        for v in end
                    )
                )
                self.assertTrue(
                    any(
                        v["value_selector"] == ["creative_compose", "error"]
                        for end in ends
                        for v in end
                    )
                )
                for node in nodes.values():
                    for name, value in node["data"].get("tool_parameters", {}).items():
                        if value["type"] == "variable":
                            self.assertNotIn(
                                name,
                                {
                                    "prompt",
                                    "model",
                                    "reference_image",
                                    "reference_images",
                                    "parameters_json",
                                    "task_id",
                                },
                            )

    def test_customer_results_show_prompt_or_safe_error_without_debug_dump(self):
        for kind in ["preview", "image", "edit", "video"]:
            with self.subTest(kind=kind):
                workflow = self.workflow(kind)
                nodes = self.nodes(workflow)
                result = nodes["creative_result" if kind == "preview" else "result"]
                outputs = result["data"]["outputs"]
                self.assertFalse(
                    any(
                        output["value_selector"]
                        in [
                            ["creative_compose", "sections"],
                            ["creative_compose", "applied_tools"],
                            ["creative_compose", "changed"],
                        ]
                        for output in outputs
                    )
                )
                if kind == "preview":
                    self.assertEqual([item["variable"] for item in outputs], ["final_prompt"])
                    ready = nodes["creative_ready"]["data"]["cases"][0]["conditions"][0]
                    self.assertEqual(ready["variable_selector"], ["creative_compose", "success"])
                    self.assertIs(ready["value"], True)
                    error = nodes["creative_error"]["data"]["outputs"]
                    self.assertEqual(
                        [item["value_selector"] for item in error],
                        [["creative_compose", "error"]],
                    )


if __name__ == "__main__":
    unittest.main()
