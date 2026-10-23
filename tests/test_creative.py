import copy
import hashlib
import importlib
import json
import math
import unittest
from pathlib import Path


class CreativeCompilerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = Path("tests/fixtures/creative-golden-v1.json").read_bytes()
        assert (
            hashlib.sha256(source).hexdigest()
            == "a2fdd732a225d99cc24bbab8e53f8c043726acb45280200377031be8bd4e508e"
        )
        cls.fixtures = json.loads(source)

    def module(self):
        try:
            return importlib.import_module("apixly_media.creative")
        except ModuleNotFoundError:
            self.fail("The canonical creative prompt compiler has not been implemented.")

    def test_all_valid_shared_fixtures_match_exactly_without_mutating_input(self):
        compose = self.module().compose_creative_prompt
        for case in self.fixtures["valid"]:
            with self.subTest(case=case["id"]):
                original = copy.deepcopy(case["input"])
                self.assertEqual(compose(case["input"]), case["expected"])
                self.assertEqual(case["input"], original)

    def test_all_invalid_shared_fixtures_fail_with_exact_field_paths(self):
        module = self.module()
        for case in self.fixtures["invalid"]:
            with self.subTest(case=case["id"]):
                with self.assertRaises(module.CreativePromptError) as caught:
                    module.compose_creative_prompt(case["input"])
                self.assertEqual(caught.exception.path, case["error_path"])
                self.assertEqual(caught.exception.field_path, case["error_path"])
                self.assertIn(case["error_path"], str(caught.exception))

    def test_nonfinite_and_boolean_numbers_are_rejected_without_value_echo(self):
        module = self.module()
        for field, value in [
            ("yaw", math.nan),
            ("pitch", math.inf),
            ("yaw", -math.inf),
            ("pitch", True),
        ]:
            with self.subTest(field=field, value_type=type(value).__name__):
                with self.assertRaises(module.CreativePromptError) as caught:
                    module.compose_creative_prompt(
                        {"prompt": "base", "tools": {"angle": {field: value}}}
                    )
                self.assertEqual(caught.exception.path, "tools.angle." + field)
        with self.assertRaises(module.CreativePromptError) as caught:
            module.compose_creative_prompt(
                {"prompt": "base", "tools": {"camera": {"body": "PRIVATE_INVALID_VALUE_731"}}}
            )
        self.assertNotIn("PRIVATE_INVALID_VALUE_731", str(caught.exception))

    def test_utf16_limits_accept_exact_emoji_boundary_and_reject_one_more(self):
        module = self.module()
        exact = "\U0001f600" * 10_000
        self.assertEqual(module.compose_creative_prompt({"prompt": exact})["final_prompt"], exact)
        with self.assertRaises(module.CreativePromptError) as caught:
            module.compose_creative_prompt({"prompt": exact + "\U0001f600"})
        self.assertEqual(caught.exception.path, "prompt")
        with self.assertRaises(module.CreativePromptError) as caught:
            module.compose_creative_prompt(
                {"prompt": "", "tools": {"lighting": {"smartText": "\U0001f600" * 501}}}
            )
        self.assertEqual(caught.exception.path, "tools.lighting.smartText")

    def test_smart_text_uses_javascript_trim_whitespace(self):
        compose = self.module().compose_creative_prompt
        base = {
            "prompt": "",
            "tools": {"lighting": {"enabled": True, "smartText": "\ufeff soft light \ufeff"}},
        }
        self.assertEqual(compose(base)["final_prompt"], "Lighting: lighting style: soft light")
        base["tools"]["lighting"]["smartText"] = "\u0085soft light\u0085"
        self.assertEqual(
            compose(base)["final_prompt"], "Lighting: lighting style: \u0085soft light\u0085"
        )
        base["tools"]["lighting"]["smartText"] = "\u001csoft light\u001c"
        self.assertEqual(
            compose(base)["final_prompt"], "Lighting: lighting style: \u001csoft light\u001c"
        )

    def test_yaw_wrap_matches_the_source_javascript_normalization_order(self):
        result = self.module().compose_creative_prompt(
            {"prompt": "", "tools": {"angle": {"enabled": True, "yaw": 22.49999999999997}}}
        )
        self.assertEqual(
            result["final_prompt"],
            "Camera: three-quarter front view, from the right, (22° azimuth)",
        )

    def test_javascript_round_avoids_half_addition_precision_loss(self):
        compose = self.module().compose_creative_prompt
        self.assertEqual(
            compose(
                {"prompt": "", "tools": {"angle": {"enabled": True, "yaw": 0.49999999999999994}}}
            )["final_prompt"],
            "",
        )
        self.assertEqual(
            compose(
                {"prompt": "", "tools": {"angle": {"enabled": True, "yaw": 337.49999999999994}}}
            )["final_prompt"],
            "Camera: (337° azimuth)",
        )
        self.assertEqual(
            compose(
                {"prompt": "", "tools": {"angle": {"enabled": True, "yaw": 22.49999999999999}}}
            )["final_prompt"],
            "Camera: three-quarter front view, from the right, (22° azimuth)",
        )

    def test_ui_only_fields_do_not_change_compiled_output(self):
        compose = self.module().compose_creative_prompt
        original = {
            "prompt": "base",
            "tools": {
                "angle": {"enabled": True, "yaw": 90},
                "lighting": {"enabled": True, "preset": "goldenHour"},
            },
        }
        decorated = copy.deepcopy(original)
        decorated["tools"]["angle"]["showPrompt"] = False
        decorated["tools"]["lighting"]["view"] = "front"
        self.assertEqual(compose(original), compose(decorated))


if __name__ == "__main__":
    unittest.main()
