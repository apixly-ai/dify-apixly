import base64
import json
import unittest

import httpx

from apixly_media.client import MediaClient, MediaError, UnknownOutcome


class MediaContractTests(unittest.TestCase):
    def client(self, handler):
        self.calls = []

        def capture(request):
            self.calls.append(request)
            return handler(request)

        return MediaClient("test-secret", transport=httpx.MockTransport(capture))

    def test_generate_exact_model_and_async_json(self):
        client = self.client(lambda _: httpx.Response(200, json={"id": "12", "status": "queued"}))
        task = client.generate_image(
            "gemini-3-pro-image-preview", "Make blue", {"size": "1024x1024", "seed": 0}
        )
        self.assertEqual(task["id"], "12")
        self.assertFalse(task["terminal"])
        request = self.calls[0]
        self.assertEqual(str(request.url), "https://apixly.ai/v1/images/generations")
        self.assertEqual(
            json.loads(request.content),
            {
                "model": "gemini-3-pro-image-preview",
                "prompt": "Make blue",
                "async": True,
                "size": "1024x1024",
                "seed": 0,
            },
        )
        self.assertEqual(request.headers["authorization"], "Bearer test-secret")

    def test_edit_forwards_url_and_data_url_in_gateway_json_contract(self):
        client = self.client(lambda _: httpx.Response(200, json={"id": "13"}))
        data_url = "data:image/png;base64," + base64.b64encode(b"png-content").decode()
        client.edit_image(
            "gpt-image-2",
            "Blue background",
            ["https://cdn.example/photo.png", data_url],
            {"quality": "high"},
            data_url,
        )
        request = self.calls[0]
        self.assertEqual(request.url.path, "/v1/images/edits")
        body = json.loads(request.content)
        self.assertEqual(
            body["images"],
            [{"image_url": "https://cdn.example/photo.png"}, {"image_url": data_url}],
        )
        self.assertEqual(body["mask"], {"image_url": data_url})
        self.assertEqual(len(self.calls), 1)

    def test_video_uses_flat_params_and_exact_id(self):
        client = self.client(
            lambda _: httpx.Response(
                200, json={"id": "video-9", "status": "queued", "model": "seedance-2.0-mini"}
            )
        )
        client.create_video(
            "seedance-2.0-mini",
            "Slow pan",
            {
                "seconds": 4,
                "resolution": "480p",
                "aspect_ratio": "16:9",
                "images": ["https://cdn.example/p.png"],
            },
        )
        self.assertEqual(self.calls[0].url.path, "/v1/videos")
        body = json.loads(self.calls[0].content)
        self.assertEqual(body["model"], "seedance-2.0-mini")
        self.assertEqual(body["seconds"], 4)
        self.assertNotIn("async", body)

    def test_submit_timeout_never_repeats_post_or_exposes_secret(self):
        def timeout(request):
            raise httpx.ReadTimeout("Bearer test-secret", request=request)

        client = self.client(timeout)
        with self.assertRaises(UnknownOutcome) as raised:
            client.generate_image("EXACT-model", "Draw")
        self.assertNotIn("test-secret", str(raised.exception))
        self.assertEqual(len(self.calls), 1)

    def test_missing_id_is_unknown_and_not_retried(self):
        client = self.client(lambda _: httpx.Response(200, json={"data": []}))
        with self.assertRaises(UnknownOutcome):
            client.create_video("EXACT-video", "Move")
        self.assertEqual(len(self.calls), 1)

    def test_submit_503_is_unknown_and_not_retried(self):
        client = self.client(lambda _: httpx.Response(503, text="test-secret"))
        with self.assertRaises(UnknownOutcome):
            client.create_video("EXACT-video", "Move")
        self.assertEqual(len(self.calls), 1)

    def test_parameters_cannot_override_model_prompt_async_or_inject_key(self):
        client = self.client(lambda _: httpx.Response(200, json={"id": "14"}))
        for field in [
            "model",
            "prompt",
            "async",
            "api_key",
            "authorization",
            "base_url",
            "callback_url",
        ]:
            with self.subTest(field=field), self.assertRaises(MediaError):
                client.generate_image("exact", "Draw", {field: "override"})
        self.assertEqual(len(self.calls), 0)

    def test_input_validation_happens_before_generation(self):
        client = self.client(lambda _: httpx.Response(200, json={"id": "15"}))
        for reference in [
            "file:///etc/passwd",
            "https://u:p@host.example/img.png",
            "data:text/html;base64,QQ==",
            "data:image/png;base64,not-base64",
        ]:
            with self.subTest(reference=reference), self.assertRaises(MediaError):
                client.edit_image("exact", "Edit", [reference])
        with self.assertRaises(MediaError):
            client.edit_image("exact", "Edit", [])
        self.assertEqual(len(self.calls), 0)

    def test_query_image_terminal_outputs_and_usage(self):
        client = self.client(
            lambda _: httpx.Response(
                200,
                json={
                    "id": "14",
                    "model": "gpt-image-2",
                    "status": "succeeded",
                    "data": [{"url": "https://apixly.ai/v1/images/content?ref=signed"}],
                    "usage": {"output_tokens": 4},
                },
            )
        )
        task = client.query_task("image", "14")
        self.assertEqual(self.calls[0].url.path, "/v1/images/generations/14")
        self.assertTrue(task["terminal"])
        self.assertTrue(task["success"])
        self.assertEqual(len(task["urls"]), 1)
        self.assertEqual(task["usage"], {"output_tokens": 4})

    def test_failure_and_expiry_are_explicit_terminal_results(self):
        for status in ["failed", "expired", "cancelled", "mystery"]:
            with self.subTest(status=status):
                client = self.client(
                    lambda _: httpx.Response(
                        200,
                        json={
                            "id": "video-3",
                            "status": status,
                            "error": {"message": "test-secret rejected"},
                        },
                    )
                )
                task = client.query_task("video", "video-3")
                self.assertTrue(task["terminal"])
                self.assertFalse(task["success"])
                self.assertNotIn("test-secret", json.dumps(task))

    def test_success_without_media_does_not_claim_delivered(self):
        client = self.client(lambda _: httpx.Response(200, json={"id": "2", "status": "succeeded"}))
        task = client.query_task("image", "2")
        self.assertFalse(task["success"])
        self.assertEqual(task["result_state"], "result_unavailable")

    def test_poll_http_failure_preserves_id_and_never_generates(self):
        client = self.client(lambda _: httpx.Response(503, text="upstream"))
        task = client.query_task("video", "video-6")
        self.assertEqual(task["result_state"], "query_error")
        self.assertFalse(task["terminal"])
        self.assertEqual(task["id"], "video-6")
        self.assertEqual([r.method for r in self.calls], ["GET"])

    def test_task_id_cannot_change_api_path(self):
        client = self.client(lambda _: httpx.Response(200))
        for task_id in ["../models", "1?token=x", "", "a/b"]:
            with self.subTest(task_id=task_id), self.assertRaises(MediaError):
                client.query_task("video", task_id)
        self.assertEqual(len(self.calls), 0)

    def test_gateway_redirect_is_not_followed(self):
        client = self.client(
            lambda _: httpx.Response(307, headers={"Location": "https://attacker.example/api"})
        )
        with self.assertRaises(UnknownOutcome):
            client.create_video("exact", "Move")
        self.assertEqual(len(self.calls), 1)

    def test_result_download_has_no_authorization_and_rejects_external_urls(self):
        client = self.client(
            lambda _: httpx.Response(200, content=b"media", headers={"content-type": "image/png"})
        )
        content, mime = client.download_result("https://apixly.ai/v1/images/content?ref=signed")
        self.assertEqual((content, mime), (b"media", "image/png"))
        self.assertNotIn("authorization", self.calls[0].headers)
        for url in [
            "https://evil.example/x",
            "https://apixly.ai.evil.example/x",
            "https://apixly.ai:443/v1/images/content?ref=x",
            "https://apixly.ai/v1/models",
        ]:
            with self.subTest(url=url), self.assertRaises(MediaError):
                client.download_result(url)
        self.assertEqual(len(self.calls), 1)

    def test_read_only_credential_check_does_not_generate(self):
        client = self.client(lambda _: httpx.Response(200, json={"data": [{"id": "gpt-image-2"}]}))
        client.validate_credentials()
        self.assertEqual([(r.method, r.url.path) for r in self.calls], [("GET", "/v1/models")])

    def test_submission_preserves_request_id_for_billing_reconciliation(self):
        client = self.client(
            lambda _: httpx.Response(
                200,
                json={"id": "20", "status": "queued"},
                headers={"x-request-id": "customer-request-20"},
            )
        )
        task = client.generate_image("exact", "Draw")
        self.assertEqual(task["request_id"], "customer-request-20")

    def test_production_platform_signed_results_download_without_key(self):
        client = self.client(
            lambda _: httpx.Response(200, content=b"image", headers={"content-type": "image/png"})
        )
        content, _ = client.download_result(
            "https://platform.apixly.ai/v1/images/content?ref=production"
        )
        self.assertEqual(content, b"image")
        self.assertNotIn("authorization", self.calls[0].headers)

    def test_video_preserves_public_effective_parameters_and_adjustments(self):
        client = self.client(
            lambda _: httpx.Response(
                200,
                json={
                    "id": "21",
                    "status": "completed",
                    "url": "https://apixly.ai/v1/videos/content?ref=x",
                    "effective_parameters": {"resolution": "720p"},
                    "parameter_adjustments": [
                        {"field": "resolution", "requested": "480p", "effective": "720p"}
                    ],
                },
            )
        )
        task = client.query_task("video", "21")
        self.assertEqual(task["effective_parameters"], {"resolution": "720p"})
        self.assertEqual(task["parameter_adjustments"][0]["requested"], "480p")

    def test_query_response_id_mismatch_preserves_original_and_reports_error(self):
        client = self.client(
            lambda _: httpx.Response(
                200,
                json={
                    "id": "different",
                    "status": "completed",
                    "url": "https://apixly.ai/v1/videos/content?ref=x",
                },
            )
        )
        task = client.query_task("video", "original")
        self.assertEqual(task["id"], "original")
        self.assertEqual(task["result_state"], "query_error")
        self.assertFalse(task["success"])

    def test_nonfinite_parameters_fail_before_submission(self):
        client = self.client(lambda _: httpx.Response(200, json={"id": "22"}))
        for value in [float("nan"), float("inf"), float("-inf")]:
            with self.subTest(value=str(value)), self.assertRaises(MediaError):
                client.create_video("exact", "Move", {"nested": {"value": value}})
        self.assertEqual(len(self.calls), 0)

    def test_unsupported_media_mime_is_explicitly_rejected(self):
        client = self.client(
            lambda _: httpx.Response(
                200, content=b"data", headers={"content-type": "image/svg+xml"}
            )
        )
        with self.assertRaisesRegex(MediaError, "supported"):
            client.download_result("https://apixly.ai/v1/images/content?ref=x")


if __name__ == "__main__":
    unittest.main()
