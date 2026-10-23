import json
import unittest
from unittest.mock import patch

import httpx

from apixly_media.catalog import CatalogCache
from apixly_media.catalog_service import ModelCatalogService


class CatalogServiceTests(unittest.TestCase):
    token = "apc_" + "f" * 43

    def setUp(self):
        self.cache = CatalogCache()
        self.calls = []
        self.revision = 1
        self.key_id = "19"
        self.cap_fail = False
        self.account_status = 200
        self.account_error_code = "invalid_connection"
        self.models_fail = False

    def tearDown(self):
        self.cache.close()

    def handler(self, request):
        self.calls.append(request)
        self.assertEqual(request.method, "GET")
        if request.url.path.endswith("/account"):
            if self.account_status != 200:
                return httpx.Response(
                    self.account_status,
                    json={
                        "error": self.account_error_code
                        if getattr(self, "flat_account_error", False)
                        else {"code": self.account_error_code}
                    },
                )
            return httpx.Response(
                self.account_status,
                json={
                    "connection_id": "c1",
                    "account": {"id": 9},
                    "selected_key": {"id": self.key_id, "name": "studio-key", "masked": "sk-…1234"},
                    "selection_revision": self.revision,
                },
            )
        if request.url.path.endswith("/models/list"):
            return httpx.Response(
                500 if self.models_fail else 200,
                json={
                    "data": [
                        {"id": "exact-image", "type": "image", "pricing": {"retail": 0.02}},
                        {"id": "exact-video", "type": "video"},
                    ],
                    "currency": "USD",
                },
            )
        if request.url.path.endswith("/video/config"):
            return httpx.Response(
                500 if self.cap_fail else 200,
                json={"data": [{"model": "exact-video", "modes": ["text2video"]}]},
            )
        self.fail("Unexpected endpoint")

    def service(self, credentials):
        return ModelCatalogService(
            credentials, cache=self.cache, transport=httpx.MockTransport(self.handler)
        )

    def test_manual_mode_uses_catalog_not_legacy_models_and_fetches_lazily(self):
        service = self.service({"api_key": "manual-fixture"})
        self.assertEqual(self.calls, [])
        first = service.read()
        self.assertTrue(first["available"])
        self.assertEqual(
            [call.url.path for call in self.calls], ["/v1/models/list", "/v1/video/config"]
        )
        self.assertTrue(
            all(call.headers["authorization"] == "Bearer manual-fixture" for call in self.calls)
        )
        service.read()
        self.assertEqual(len(self.calls), 2)
        service.read(force=True)
        self.assertEqual(len(self.calls), 4)
        self.assertEqual(first["metadata"], {"currency": "USD"})

    def test_oauth_uses_current_selected_key_metadata_and_relay_catalog(self):
        service = self.service(
            {
                "connection_token": self.token,
                "selected_key_id": "old-untrusted-node-value",
                "selection_revision": 0,
            }
        )
        first = service.read()
        self.assertEqual(
            [call.url.path for call in self.calls],
            [
                "/api/integrations/account",
                "/api/integrations/v1/models/list",
                "/api/integrations/v1/video/config",
            ],
        )
        self.assertEqual(first["selected_key"]["id"], "19")
        self.revision, self.key_id = 2, "20"
        second = service.read()
        self.assertNotEqual(first["identity"], second["identity"])
        self.assertFalse(self.cache.peek(first["identity"])["available"])
        self.assertEqual(second["selected_key"]["id"], "20")
        self.assertNotIn(self.token, json.dumps(second))

    def test_revoked_connection_invalidates_saved_options(self):
        service = self.service({"connection_token": self.token})
        first = service.read()
        self.account_status = 401
        failed = service.read()
        self.assertFalse(failed["available"])
        self.assertFalse(self.cache.peek(first["identity"])["available"])
        self.assertIn("Authorize again", failed["error"])
        self.assertNotIn(self.token, json.dumps(failed))

    def test_live_flat_revocation_code_clears_catalog_and_requires_authorization(self):
        service = self.service({"connection_token": self.token})
        first = service.read()
        self.account_status = 401
        self.flat_account_error = True
        failed = service.read()
        self.assertFalse(failed["available"])
        self.assertEqual(failed["error_code"], "invalid_connection")
        self.assertEqual(failed["http_status"], 401)
        self.assertIn("Authorize again", failed["error"])
        self.assertFalse(self.cache.peek(first["identity"])["available"])
        self.assertTrue(all(request.method == "GET" for request in self.calls))

    def test_flat_unavailable_key_is_not_treated_as_transient_saved_catalog(self):
        service = self.service({"connection_token": self.token})
        first = service.read()
        self.account_status = 409
        self.account_error_code = "selected_key_unavailable"
        self.flat_account_error = True
        failed = service.read()
        self.assertFalse(failed["available"])
        self.assertEqual(failed["error_code"], "selected_key_unavailable")
        self.assertIn("selected Key is unavailable", failed["error"])
        self.assertNotIn("Authorize again", failed["error"])
        self.assertFalse(self.cache.peek(first["identity"])["available"])

    def test_selected_key_rejection_keeps_saved_connection_and_does_not_request_reauthorization(
        self,
    ):
        service = self.service({"connection_token": self.token})
        first = service.read()
        self.account_status, self.account_error_code = 401, "selected_key_rejected"
        failed = service.read()
        self.assertFalse(failed["available"])
        self.assertFalse(self.cache.peek(first["identity"])["available"])
        self.assertIn("selected Key", failed["error"])
        self.assertNotIn("Authorize again", failed["error"])
        self.assertTrue(all(request.method == "GET" for request in self.calls))

    def test_cap_failure_keeps_images_and_same_key_capabilities_with_warning(self):
        service = self.service({"api_key": "manual-fixture"})
        service.read()
        self.cap_fail = True
        partial = service.read(force=True)
        self.assertTrue(partial["available"])
        self.assertTrue(partial["stale"])
        self.assertEqual(partial["videos"][0]["model"], "exact-video")
        self.assertTrue(partial["capabilitiesError"])
        self.assertEqual(partial["models"][0]["id"], "exact-image")
        self.models_fail = True
        failed = service.read(force=True)
        self.assertTrue(failed["available"])
        self.assertTrue(failed["stale"])

    def test_cold_failure_has_no_fabricated_models_or_generation_requests(self):
        self.models_fail = True
        failed = self.service({"api_key": "manual-fixture"}).read()
        self.assertFalse(failed["available"])
        self.assertEqual(failed["models"], [])
        self.assertEqual(len(self.calls), 1)

    def test_generation_tool_options_use_credential_scoped_read_only_catalog(self):
        from tools.create_video import CreateVideoTool
        from tools.generate_image import GenerateImageTool

        snapshot = {
            "available": True,
            "models": [{"id": "image", "type": "image"}, {"id": "video", "type": "video"}],
            "videos": [],
            "stale": False,
        }
        for tool_class, expected in [(GenerateImageTool, "image"), (CreateVideoTool, "video")]:
            with patch("tools.base.ModelCatalogService") as mocked:
                mocked.return_value.read.return_value = snapshot
                tool = tool_class.from_credentials({"connection_token": self.token})
                options = tool._fetch_parameter_options("catalog_model")
                mocked.assert_called_once_with({"connection_token": self.token})
                self.assertEqual([option.value for option in options], [expected])


if __name__ == "__main__":
    unittest.main()
