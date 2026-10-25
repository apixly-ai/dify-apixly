"""Checked-in DSLs must resolve to the independently verified distribution.

The fixture captures a real public Marketplace lookup/download and official-key
signature verification. Tests stay offline; they do not treat a builder-generated
checksum or an unsigned GitHub package as a Marketplace publication receipt.
"""

import json
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CREATIVE = "apixly-ai/apixly_creative"
MEDIA = "apixly-ai/apixly_media"


class MarketplaceWorkflowPinTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt = json.loads(
            (ROOT / "tests/fixtures/creative-marketplace-0.1.0.json").read_text()
        )
        cls.version = cls.receipt["version_response"]["data"]["version"]
        cls.creative_uid = cls.version["unique_identifier"]
        cls.documents = {
            path.name: yaml.safe_load(path.read_text())
            for path in sorted((ROOT / "examples").glob("*.yml"))
        }

    def test_identity_is_an_active_signed_and_publicly_downloadable_version(self):
        download = self.receipt["marketplace_download"]
        self.assertEqual(self.receipt["version_response"]["code"], 0)
        self.assertEqual(self.version["status"], "active")
        self.assertEqual(self.version["plugin_org"], "apixly-ai")
        self.assertEqual(self.version["plugin_name"], "apixly_creative")
        self.assertEqual(self.version["version"], "0.1.0")
        self.assertEqual(self.creative_uid, f"{CREATIVE}:0.1.0@{download['content_checksum']}")
        self.assertEqual(download["plugin_unique_identifier"], self.creative_uid)
        self.assertEqual(download["http_status"], 200)
        self.assertIs(download["official_signature_verified"], True)
        unavailable = self.receipt["unavailable_original_marketplace_uid"]
        self.assertEqual(unavailable["http_status"], 404)
        self.assertNotEqual(unavailable["plugin_unique_identifier"], self.creative_uid)

    def test_checked_in_creative_dependencies_resolve_to_the_verified_marketplace(self):
        affected = 0
        for filename, document in self.documents.items():
            dependencies = [
                item["value"]["plugin_unique_identifier"]
                for item in document["dependencies"]
                if item["value"]["plugin_unique_identifier"].startswith(CREATIVE + ":")
            ]
            if dependencies:
                affected += 1
                with self.subTest(workflow=filename):
                    self.assertEqual(dependencies, [self.creative_uid])
        self.assertEqual(affected, 8)

    def test_every_creative_node_uses_the_resolvable_declared_dependency(self):
        count = 0
        for filename, document in self.documents.items():
            dependencies = {
                item["value"]["plugin_unique_identifier"] for item in document["dependencies"]
            }
            for node in document["workflow"]["graph"]["nodes"]:
                data = node["data"]
                if data.get("plugin_id") == CREATIVE:
                    count += 1
                    with self.subTest(workflow=filename, node=node["id"]):
                        self.assertEqual(data["plugin_unique_identifier"], self.creative_uid)
                        self.assertIn(data["plugin_unique_identifier"], dependencies)
        self.assertEqual(count, 20)

    def test_media_pins_keep_the_qualified_manual_package_identity(self):
        expected = self.receipt["manual_media_package"]["plugin_unique_identifier"]
        identifiers = []
        self.assertEqual(len(self.documents), 12)
        for filename, document in self.documents.items():
            identifiers.extend(
                (filename, item["value"]["plugin_unique_identifier"])
                for item in document["dependencies"]
                if item["value"]["plugin_unique_identifier"].startswith(MEDIA + ":")
            )
            identifiers.extend(
                (filename, node["data"]["plugin_unique_identifier"])
                for node in document["workflow"]["graph"]["nodes"]
                if node["data"].get("plugin_id") == MEDIA
            )
        self.assertEqual(len(identifiers), 43)
        for filename, identifier in identifiers:
            with self.subTest(workflow=filename):
                self.assertEqual(identifier, expected)
