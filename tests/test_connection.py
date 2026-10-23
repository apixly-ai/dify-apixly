import json
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import httpx
import yaml
from dify_plugin.errors.tool import ToolProviderOAuthError
from werkzeug import Request
from werkzeug.test import EnvironBuilder

from apixly_media.client import MediaClient, MediaError
from apixly_media.connection import OAuthConnection, media_credentials
from provider.apixly import ApixlyProvider


class ConnectionTests(unittest.TestCase):
    client = {"client_id": "dify-test-app", "client_secret": "private-test-client-secret"}
    redirect = "https://dify.example/console/api/oauth/plugin/apixly/tool/callback"
    token = "apc_" + "f" * 43

    def callback(self, **query):
        return Request(EnvironBuilder(path="/callback", query_string=query).get_environ())

    def response(self):
        return {
            "access_token": self.token,
            "token_type": "Bearer",
            "expires_in": 7776000,
            "connection_id": "connection-1",
            "account": {"id": 9, "name": "Studio user", "email": "test@example.test"},
            "selected_key": {
                "id": "19",
                "name": "studixly-key",
                "masked": "sk-…1234",
                "is_default": True,
            },
            "selection_revision": 2,
        }

    def test_authorization_url_keeps_secret_private_and_binds_signed_state(self):
        auth = OAuthConnection(self.client)
        url = auth.authorization_url(self.redirect)
        parsed = urlsplit(url)
        self.assertEqual(
            parsed.scheme + "://" + parsed.netloc + parsed.path,
            "https://apixly.ai/api/integrations/authorize",
        )
        query = parse_qs(parsed.query)
        self.assertEqual(query["client_id"], [self.client["client_id"]])
        self.assertEqual(query["redirect_uri"], [self.redirect])
        self.assertEqual(query["response_type"], ["code"])
        self.assertNotIn(self.client["client_secret"], url)
        self.assertNotIn("code_verifier", query)
        self.assertNotEqual(
            query["state"], parse_qs(urlsplit(auth.authorization_url(self.redirect)).query)["state"]
        )

    def test_invalid_or_missing_client_and_unsafe_callback_fail_without_network(self):
        with patch("httpx.Client") as network:
            for credentials in [{}, {"client_id": "x"}, {"client_secret": "x"}]:
                with (
                    self.subTest(credentials=list(credentials)),
                    self.assertRaises(ToolProviderOAuthError),
                ):
                    OAuthConnection(credentials).authorization_url(self.redirect)
            for redirect in [
                None,
                [],
                "http://public.example/callback",
                "https://user:pass@example.test/callback",
                "https://example.test/callback#secret",
                "javascript:alert(1)",
            ]:
                with self.subTest(redirect=redirect), self.assertRaises(ToolProviderOAuthError):
                    OAuthConnection(self.client).authorization_url(redirect)
            network.assert_not_called()
        self.assertTrue(
            OAuthConnection(self.client).authorization_url(
                "http://dify-plugin-e2e.localhost:17880/callback"
            )
        )

    def test_token_exchange_once_with_confidential_proof_and_only_scoped_credentials(self):
        calls = []

        def handler(request):
            calls.append(request)
            return httpx.Response(200, json=self.response())

        auth = OAuthConnection(self.client, transport=httpx.MockTransport(handler))
        state = parse_qs(urlsplit(auth.authorization_url(self.redirect)).query)["state"][0]
        credentials = auth.credentials(
            self.redirect, self.callback(code="one-time-code", state=state)
        )
        self.assertEqual(len(calls), 1)
        self.assertEqual(str(calls[0].url), "https://apixly.ai/api/integrations/token")
        self.assertEqual(
            json.loads(calls[0].content),
            {
                "grant_type": "authorization_code",
                **self.client,
                "code": "one-time-code",
                "redirect_uri": self.redirect,
            },
        )
        self.assertNotIn("authorization", calls[0].headers)
        self.assertEqual(credentials.credentials["connection_token"], self.token)
        self.assertEqual(credentials.credentials["key_name"], "studixly-key")
        self.assertEqual(credentials.credentials["key_masked"], "sk-…1234")
        self.assertEqual(credentials.credentials["selection_revision"], 2)
        self.assertNotIn("api_key", credentials.credentials)
        self.assertNotIn("client_secret", credentials.credentials)
        self.assertNotIn("email", credentials.credentials)
        self.assertGreater(credentials.expires_at, 0)

    def test_tampered_expired_wrong_redirect_or_error_callback_stops_before_exchange(self):
        calls = []
        auth = OAuthConnection(
            self.client, transport=httpx.MockTransport(lambda r: calls.append(r))
        )
        with patch("apixly_media.connection.time.time", return_value=1000):
            state = parse_qs(urlsplit(auth.authorization_url(self.redirect)).query)["state"][0]
        for callback, redirect, now in [
            (self.callback(code="code", state=state + "x"), self.redirect, 1001),
            (self.callback(code="code", state=state), self.redirect, 1601),
            (self.callback(code="code", state=state), self.redirect + "?changed=1", 1001),
            (self.callback(code="code"), self.redirect, 1001),
            (self.callback(error="denied-secret", state=state), self.redirect, 1001),
        ]:
            with (
                patch("apixly_media.connection.time.time", return_value=now),
                self.assertRaises(ToolProviderOAuthError) as error,
            ):
                auth.credentials(redirect, callback)
            self.assertNotIn("denied-secret", str(error.exception))
        self.assertEqual(calls, [])

    def test_failed_exchange_never_retries_or_echoes_server_or_client_secrets(self):
        for behavior in ["timeout", "500", "redirect", "bad-json", "wrong-token"]:
            with self.subTest(behavior=behavior):
                calls = []

                def handler(request):
                    calls.append(request)
                    if behavior == "timeout":
                        raise httpx.ReadTimeout(self.client["client_secret"], request=request)
                    if behavior == "500":
                        return httpx.Response(500, text=self.token + self.client["client_secret"])
                    if behavior == "redirect":
                        return httpx.Response(
                            302, headers={"Location": "https://third-party.test/"}
                        )
                    if behavior == "bad-json":
                        return httpx.Response(200, text="not-json")
                    return httpx.Response(
                        200, json={**self.response(), "access_token": "raw-api-key"}
                    )

                auth = OAuthConnection(self.client, transport=httpx.MockTransport(handler))
                state = parse_qs(urlsplit(auth.authorization_url(self.redirect)).query)["state"][0]
                with self.assertRaises(ToolProviderOAuthError) as raised:
                    auth.credentials(self.redirect, self.callback(code="code", state=state))
                self.assertEqual(len(calls), 1)
                for secret in [self.token, self.client["client_secret"], "raw-api-key"]:
                    self.assertNotIn(secret, str(raised.exception))

    def test_single_provider_exposes_manual_key_and_private_oauth_client_modes(self):
        config = yaml.safe_load(Path("provider/apixly.yaml").read_text())
        self.assertTrue(config["credentials_for_provider"]["api_key"]["required"])
        schema = config["oauth_schema"]
        self.assertEqual(
            {item["name"] for item in schema["client_schema"]}, {"client_id", "client_secret"}
        )
        for field in schema["client_schema"]:
            self.assertTrue(field["required"])
            self.assertNotIn("default", field)
        connection = next(
            item for item in schema["credentials_schema"] if item["name"] == "connection_token"
        )
        self.assertEqual(connection["type"], "secret-input")
        self.assertTrue(connection["required"])
        with patch("provider.apixly.OAuthConnection") as mocked:
            mocked.return_value.authorization_url.return_value = "https://apixly.ai/authorize"
            self.assertEqual(
                ApixlyProvider()._oauth_get_authorization_url(self.redirect, self.client),
                "https://apixly.ai/authorize",
            )
            mocked.assert_called_once_with(self.client)

    def test_credential_modes_are_explicit_and_never_silently_fallback(self):
        self.assertEqual(
            media_credentials({"api_key": "manual-fixture"}), ("manual-fixture", False)
        )
        self.assertEqual(media_credentials({"connection_token": self.token}), (self.token, True))
        for credentials in [
            {},
            {"connection_token": "bad-token"},
            {"connection_token": self.token, "api_key": "manual-fixture"},
        ]:
            with self.assertRaises(MediaError):
                media_credentials(credentials)
        for length in [16, 42, 44, 500]:
            with self.subTest(token_length=length), self.assertRaises(MediaError):
                media_credentials({"connection_token": "apc_" + "f" * length})

    def test_account_client_uses_fixed_relay_and_exact_payload_once(self):
        calls = []

        def handler(request):
            calls.append(request)
            return httpx.Response(200, json={"id": "123", "status": "queued"})

        client = MediaClient(self.token, account_mode=True, transport=httpx.MockTransport(handler))
        client.generate_image("EXACT-image-model", "  exact prompt\n", {"n": 1})
        self.assertEqual(len(calls), 1)
        self.assertEqual(
            str(calls[0].url), "https://apixly.ai/api/integrations/v1/images/generations"
        )
        self.assertEqual(
            json.loads(calls[0].content),
            {"model": "EXACT-image-model", "prompt": "  exact prompt\n", "async": True, "n": 1},
        )
        self.assertEqual(calls[0].headers["authorization"], "Bearer " + self.token)
        self.assertEqual(
            calls[0].headers["user-agent"],
            "apixly-dify-media/"
            + str(yaml.safe_load(Path("manifest.yaml").read_text())["version"]),
        )
        self.assertNotIn(self.token, client._safe(self.token))

    def test_account_queries_and_validation_use_relay_without_post_retries(self):
        calls = []

        def handler(request):
            calls.append(request)
            if request.url.path.endswith("/models"):
                return httpx.Response(200, json={"data": []})
            return httpx.Response(200, json={"id": "123", "status": "queued"})

        client = MediaClient(self.token, account_mode=True, transport=httpx.MockTransport(handler))
        client.validate_credentials()
        client.query_task("image", "123")
        client.query_task("video", "123")
        self.assertEqual(
            [request.url.path for request in calls],
            [
                "/api/integrations/v1/models",
                "/api/integrations/v1/images/generations/123",
                "/api/integrations/v1/videos/123",
            ],
        )

    def test_malformed_connection_metadata_returns_safe_oauth_error(self):
        for changed in [
            {"account": []},
            {"selected_key": None},
            {"expires_in": True},
            {"selection_revision": -1},
            {"connection_id": False},
        ]:
            with self.subTest(fields=list(changed)):
                auth = OAuthConnection(
                    self.client,
                    transport=httpx.MockTransport(
                        lambda _: httpx.Response(200, json={**self.response(), **changed})
                    ),
                )
                state = parse_qs(urlsplit(auth.authorization_url(self.redirect)).query)["state"][0]
                with self.assertRaises(ToolProviderOAuthError):
                    auth.credentials(self.redirect, self.callback(code="code", state=state))

    def test_expired_connection_requires_reauthorization_without_fake_refresh(self):
        with patch("httpx.Client") as network:
            with self.assertRaisesRegex(ToolProviderOAuthError, "[Aa]uthorize again"):
                ApixlyProvider()._oauth_refresh_credentials(
                    self.redirect, self.client, {"connection_token": self.token}
                )
            network.assert_not_called()

    def test_relay_key_rejection_and_invalid_connection_have_distinct_safe_guidance(self):
        for code, expected, forbidden in [
            ("selected_key_rejected", "selected Key", "Authorize again"),
            ("invalid_connection", "Authorize again", "switches to"),
        ]:
            with self.subTest(code=code):
                calls = []

                def handler(request):
                    calls.append(request)
                    return httpx.Response(
                        401, json={"error": {"code": code, "message": self.token}}
                    )

                client = MediaClient(
                    self.token, account_mode=True, transport=httpx.MockTransport(handler)
                )
                with self.assertRaises(MediaError) as raised:
                    client.generate_image("EXACT-model", "Draw")
                self.assertIn(expected, str(raised.exception))
                self.assertNotIn(forbidden, str(raised.exception))
                self.assertNotIn(self.token, str(raised.exception))
                self.assertEqual([request.method for request in calls], ["POST"])


if __name__ == "__main__":
    unittest.main()
