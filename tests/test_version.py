import inspect
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from scripts import build_workflows


class CandidateVersionTests(unittest.TestCase):
    def test_manifest_uses_minor_candidate_without_changing_manifest_schema(self):
        manifest = yaml.safe_load(Path("manifest.yaml").read_text())
        self.assertEqual(manifest["version"], "0.2.0")
        self.assertEqual(manifest["meta"]["version"], "0.0.1")

    def test_every_workflow_builder_defaults_to_the_candidate_version(self):
        for builder in [
            build_workflows.build_workflow,
            build_workflows.build_image_to_video,
            build_workflows.build_creative_workflow,
            build_workflows.build_studio_workflow,
        ]:
            with self.subTest(builder=builder.__name__):
                self.assertEqual(inspect.signature(builder).parameters["version"].default, "0.2.0")

    def test_cli_emits_twelve_dsl_dependencies_for_the_same_candidate_version(self):
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
            files = list(Path(directory).glob("*.yml"))
            self.assertEqual(len(files), 12)
            for file in files:
                with self.subTest(file=file.name):
                    document = yaml.safe_load(file.read_text())
                    identifier = document["dependencies"][0]["value"]["plugin_unique_identifier"]
                    expected = (
                        "apixly-ai/apixly_creative:0.1.0@" + "b" * 64
                        if any(
                            marker in file.name for marker in ["creative-preview", "studio-preview"]
                        )
                        else "apixly-ai/apixly_media:0.2.0@" + "a" * 64
                    )
                    self.assertEqual(identifier, expected)


if __name__ == "__main__":
    unittest.main()
