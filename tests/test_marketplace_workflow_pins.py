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
        cls.media_receipt = json.loads(
            (ROOT / "tests/fixtures/media-marketplace-0.2.0.json").read_text()
        )
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

    def test_media_identity_is_active_signed_and_publicly_downloadable(self):
        version = self.media_receipt["version_response"]["data"]["version"]
        download = self.media_receipt["marketplace_download"]
        self.assertEqual(self.media_receipt["version_response"]["code"], 0)
        self.assertEqual(version["status"], "active")
        self.assertEqual(version["plugin_org"], "apixly-ai")
        self.assertEqual(version["plugin_name"], "apixly_media")
        self.assertEqual(version["version"], "0.2.0")
        self.assertEqual(
            version["unique_identifier"], f"{MEDIA}:0.2.0@{download['content_checksum']}"
        )
        self.assertEqual(download["plugin_unique_identifier"], version["unique_identifier"])
        self.assertEqual(download["http_status"], 200)
        self.assertIs(download["official_signature_verified"], True)
        unavailable = self.media_receipt["unavailable_original_marketplace_uid"]
        self.assertEqual(unavailable["http_status"], 404)
        self.assertNotEqual(unavailable["plugin_unique_identifier"], version["unique_identifier"])

    def test_media_dependencies_and_nodes_use_verified_marketplace_identity(self):
        expected = self.media_receipt["marketplace_download"]["plugin_unique_identifier"]
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
            dependencies = {
                item["value"]["plugin_unique_identifier"] for item in document["dependencies"]
            }
            for node in document["workflow"]["graph"]["nodes"]:
                if node["data"].get("plugin_id") == MEDIA:
                    with self.subTest(workflow=filename, node=node["id"]):
                        self.assertIn(node["data"]["plugin_unique_identifier"], dependencies)
        self.assertEqual(len(identifiers), 43)
        for filename, identifier in identifiers:
            with self.subTest(workflow=filename):
                self.assertEqual(identifier, expected)
