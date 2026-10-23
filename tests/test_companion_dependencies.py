import unittest

from scripts.build_workflows import build_creative_workflow


class CompanionDependencyTests(unittest.TestCase):
    def test_free_preview_depends_only_on_independent_credential_free_package(self):
        doc = build_creative_workflow("preview", "a" * 64, creative_checksum="b" * 64)
        ids = {d["value"]["plugin_unique_identifier"] for d in doc["dependencies"]}
        self.assertEqual(ids, {"apixly-ai/apixly_creative:0.1.0@" + "b" * 64})
        tool = next(n for n in doc["workflow"]["graph"]["nodes"] if n["data"]["type"] == "tool")[
            "data"
        ]
        self.assertEqual(tool["plugin_id"], "apixly-ai/apixly_creative")
        self.assertEqual(tool["provider_id"], "apixly-ai/apixly_creative/apixly_creative")
        self.assertEqual(tool["plugin_unique_identifier"], next(iter(ids)))

    def test_paid_creative_flows_pin_both_independent_packages(self):
        for kind in ["image", "edit", "video"]:
            with self.subTest(kind=kind):
                doc = build_creative_workflow(kind, "a" * 64, creative_checksum="b" * 64)
                ids = {d["value"]["plugin_unique_identifier"] for d in doc["dependencies"]}
                self.assertEqual(
                    ids,
                    {
                        "apixly-ai/apixly_media:0.2.0@" + "a" * 64,
                        "apixly-ai/apixly_creative:0.1.0@" + "b" * 64,
                    },
                )
                tools = {
                    n["id"]: n["data"]
                    for n in doc["workflow"]["graph"]["nodes"]
                    if n["data"]["type"] == "tool"
                }
                self.assertEqual(
                    tools["creative_compose"]["plugin_unique_identifier"],
                    "apixly-ai/apixly_creative:0.1.0@" + "b" * 64,
                )
                self.assertEqual(
                    tools["submit"]["plugin_unique_identifier"],
                    "apixly-ai/apixly_media:0.2.0@" + "a" * 64,
                )
