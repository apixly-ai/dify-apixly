import json
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from apixly_media.catalog import (
    CatalogCache,
    CatalogError,
    build_catalog_snapshot,
    build_model_options,
    catalog_identity,
    parse_model_catalog,
    parse_model_list,
    parse_video_config,
)

MODELS = {
    "data": [
        {
            "id": "plain-photo",
            "type": "image",
            "name": "Photo",
            "pricing": {"unit": "image", "price": 0.02},
        },
        {"id": "image-in-name-is-chat", "type": "chat", "extra": [1, False, None]},
        {"id": "future-clip", "type": "video", "pricing": None},
        {"id": "configured-clip", "type": "future-type"},
    ],
    "snapshot": {"public": True, "revision": 4},
}
CONFIG = {
    "data": [
        {
            "model": "configured-clip",
            "modes": ["text2video"],
            "resolutions": ["720p"],
            "extra": {"duration": 3},
        },
        {"model": "not-authorized", "modes": []},
    ]
}


class CatalogParserTests(unittest.TestCase):
    def test_sanitized_public_catalog_sample_has_observed_model_counts(self):
        sample = json.loads(Path("tests/fixtures/public-catalog-2026-10-23.json").read_text())
        models = parse_model_list(sample["models"])
        videos = parse_video_config(sample["videos"])
        self.assertEqual(len(models), 29)
        self.assertEqual(len(build_model_options(models, videos, "image")), 14)
        self.assertEqual(len(build_model_options(models, videos, "video")), 11)

    def test_preserves_full_envelope_metadata_without_mutating_input(self):
        parsed = parse_model_catalog(MODELS)
        self.assertEqual(parsed, MODELS)
        parsed["snapshot"]["revision"] = 9
        parsed["data"][0]["pricing"]["price"] = 100
        self.assertEqual(MODELS["snapshot"]["revision"], 4)
        self.assertEqual(MODELS["data"][0]["pricing"]["price"], 0.02)
        self.assertEqual(parse_model_list(MODELS), MODELS["data"])
        self.assertEqual(parse_video_config(CONFIG), CONFIG["data"])

    def test_strict_image_type_and_listed_video_or_config_rule(self):
        images = build_model_options(MODELS["data"], CONFIG["data"], "image")
        self.assertEqual([item["id"] for item in images], ["plain-photo"])
        self.assertEqual(images[0]["pricing"], {"unit": "image", "price": 0.02})
        videos = build_model_options(MODELS["data"], CONFIG["data"], "video")
        self.assertEqual([item["id"] for item in videos], ["future-clip", "configured-clip"])
        self.assertIsNone(videos[0]["videoCapability"])
        self.assertEqual(videos[1]["videoCapability"], CONFIG["data"][0])
        self.assertNotIn("not-authorized", str(videos))

    def test_invalid_catalog_and_capability_shapes_raise_safe_error(self):
        for payload in [
            None,
            [],
            {},
            {"data": {}},
            {"data": [{"id": "SECRET", "type": ""}]},
            {"data": [{"id": "same", "type": "image"}, {"id": "same", "type": "image"}]},
            {"data": [{"id": "😀" * 251, "type": "image"}]},
        ]:
            with (
                self.subTest(payload_type=type(payload).__name__),
                self.assertRaises(CatalogError) as error,
            ):
                parse_model_catalog(payload)
            self.assertNotIn("SECRET", str(error.exception))
        for payload in [
            {"data": [{"model": "SECRET", "modes": "text2video"}]},
            {"data": [{"model": "x", "resolutions": [1]}]},
            {"data": [{"model": "x"}, {"model": "x"}]},
        ]:
            with self.assertRaises(CatalogError):
                parse_video_config(payload)

    def test_capability_failure_preserves_images_and_same_identity_saved_caps_only(self):
        snapshot = build_catalog_snapshot(MODELS, CONFIG)
        self.assertEqual(
            snapshot["metadata"], MODELS["snapshot"] and {"snapshot": MODELS["snapshot"]}
        )
        self.assertEqual([item["model"] for item in snapshot["videos"]], ["configured-clip"])
        partial = build_catalog_snapshot(MODELS, None, previous_videos=CONFIG["data"])
        self.assertEqual(partial["models"], MODELS["data"])
        self.assertEqual([item["model"] for item in partial["videos"]], ["configured-clip"])
        self.assertTrue(partial["capabilitiesError"])
        empty = build_catalog_snapshot(MODELS, None)
        self.assertEqual(empty["videos"], [])
        with self.assertRaises(CatalogError):
            build_catalog_snapshot(None, CONFIG)

    def test_identity_uses_only_digests_and_key_revision_isolates_account_cache(self):
        manual = catalog_identity({"mode": "manual", "key": "private-fixture"})
        self.assertRegex(manual, r"^manual:[a-f0-9]{64}$")
        self.assertNotIn("private-fixture", manual)
        account = {
            "mode": "account",
            "connectionId": "c1",
            "accountId": "a1",
            "keyId": "19",
            "revision": 1,
        }
        self.assertNotEqual(catalog_identity(account), catalog_identity({**account, "revision": 2}))
        self.assertNotEqual(catalog_identity(account), catalog_identity({**account, "keyId": "20"}))
        for value in [{}, {"mode": "manual", "key": ""}, {"mode": "account"}]:
            with self.assertRaises(CatalogError):
                catalog_identity(value)


class CatalogCacheTests(unittest.TestCase):
    def setUp(self):
        self.clock = [0]
        self.cache = CatalogCache(now=lambda: self.clock[0])
        self.identity = catalog_identity({"mode": "manual", "key": "key-one"})
        self.snapshot = build_catalog_snapshot(MODELS, CONFIG)

    def tearDown(self):
        self.cache.close()

    def test_fresh_cache_is_lazy_and_force_refresh_is_explicit(self):
        calls = []

        def load():
            calls.append(1)
            return self.snapshot

        first = self.cache.read(self.identity, load)
        self.assertTrue(first["available"])
        self.assertFalse(first["stale"])
        self.cache.read(self.identity, load)
        self.assertEqual(len(calls), 1)
        self.cache.read(self.identity, load, force=True)
        self.assertEqual(len(calls), 2)

    def test_stale_while_revalidate_is_nonblocking_and_singleflight(self):
        self.cache.read(self.identity, lambda: self.snapshot)
        self.clock[0] = 600
        entered, release = threading.Event(), threading.Event()
        calls = []

        def load():
            calls.append(1)
            entered.set()
            if not release.wait(2):
                raise RuntimeError("Test release missing")
            return {**self.snapshot, "metadata": {"fresh": True}}

        stale = self.cache.read(self.identity, load)
        self.assertTrue(entered.wait(1))
        self.assertTrue(stale["stale"])
        self.assertTrue(stale["refreshing"])
        self.cache.read(self.identity, load)
        release.set()
        latest = self.cache.settled(self.identity, timeout=2)
        self.assertEqual(calls, [1])
        self.assertEqual(latest["metadata"], {"fresh": True})
        self.assertFalse(latest["refreshing"])

    def test_failure_retains_same_identity_and_empty_success_is_distinct(self):
        self.cache.read(self.identity, lambda: self.snapshot)

        def fail():
            raise RuntimeError("Bearer private-fixture")

        failure = self.cache.read(self.identity, fail, force=True)
        self.assertTrue(failure["available"])
        self.assertTrue(failure["stale"])
        self.assertNotIn("private-fixture", failure["error"])
        other = catalog_identity({"mode": "manual", "key": "key-two"})
        failed_empty = self.cache.read(other, fail)
        self.assertFalse(failed_empty["available"])
        empty = self.cache.read(other, lambda: {"models": [], "videos": []}, force=True)
        self.assertTrue(empty["available"])
        self.assertFalse(empty["stale"])
        self.assertIsNone(empty["error"])

    def test_partial_capability_failure_marks_snapshot_stale(self):
        status = self.cache.read(self.identity, lambda: build_catalog_snapshot(MODELS, None))
        self.assertTrue(status["available"])
        self.assertTrue(status["stale"])
        self.assertTrue(status["capabilitiesError"])
        self.assertEqual(status["models"], MODELS["data"])

    def test_invalidated_inflight_response_cannot_restore_or_cross_identity(self):
        entered, release = threading.Event(), threading.Event()

        def old_loader():
            entered.set()
            if not release.wait(2):
                raise RuntimeError("Test release missing")
            return self.snapshot

        with ThreadPoolExecutor(max_workers=1) as callers:
            pending = callers.submit(self.cache.read, self.identity, old_loader)
            self.assertTrue(entered.wait(1))
            self.cache.invalidate(self.identity)
            fresh = self.cache.read(self.identity, lambda: {"models": [], "videos": []})
            release.set()
            self.assertFalse(pending.result(timeout=2)["available"])
        self.assertTrue(fresh["available"])
        self.assertEqual(self.cache.peek(self.identity)["models"], [])

    def test_fresh_reader_subscribes_to_inflight_force_refresh(self):
        self.cache.read(self.identity, lambda: self.snapshot)
        entered, release, notified = threading.Event(), threading.Event(), threading.Event()
        updates = []

        def load():
            entered.set()
            if not release.wait(2):
                raise RuntimeError("Test release missing")
            return {"models": [], "videos": [], "metadata": {"new": True}}

        def updated(snapshot):
            updates.append(snapshot)
            notified.set()

        with ThreadPoolExecutor(max_workers=1) as callers:
            force = callers.submit(self.cache.read, self.identity, load, force=True)
            self.assertTrue(entered.wait(1))
            cached = self.cache.read(self.identity, lambda: self.snapshot, on_update=updated)
            self.assertFalse(cached["stale"])
            self.assertTrue(cached["refreshing"])
            release.set()
            force.result(timeout=2)
            self.assertTrue(notified.wait(1))
        self.assertEqual(len(updates), 1)
        self.assertEqual(updates[0]["metadata"], {"new": True})

    def test_updated_at_is_epoch_milliseconds_while_ttl_uses_monotonic_seconds(self):
        wall = [1792750000.125]
        monotonic = [8]
        cache = CatalogCache(now=lambda: monotonic[0], wall_now=lambda: wall[0])
        try:
            first = cache.read(self.identity, lambda: self.snapshot)
            self.assertEqual(first["updatedAt"], 1792750000125)
            wall[0] += 10000
            self.assertFalse(cache.peek(self.identity)["stale"])
            monotonic[0] += 600
            self.assertTrue(cache.peek(self.identity)["stale"])
        finally:
            cache.close()


if __name__ == "__main__":
    unittest.main()
