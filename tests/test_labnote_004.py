import sys
import unittest
from pathlib import Path


EXPERIMENT_DIR = Path(__file__).parents[1] / "experiments" / "labnote_004"
sys.path.insert(0, str(EXPERIMENT_DIR))

from corpus import build_cases  # noqa: E402
from run_inference import semantic_ir_error, validate_ir  # noqa: E402


class Labnote004CorpusTests(unittest.TestCase):
    def test_corpus_has_balanced_pairs(self):
        cases = build_cases()
        self.assertEqual(len(cases), 132)
        pairs = {}
        for case in cases:
            pairs.setdefault(case["pair_id"], []).append(case)
        self.assertEqual(len(pairs), 66)
        self.assertTrue(all(len(readings) == 2 for readings in pairs.values()))
        self.assertTrue(all(readings[0]["target"] == readings[1]["target"] for readings in pairs.values()))

    def test_every_phenomenon_has_six_pairs(self):
        pair_phenomena = {}
        for case in build_cases():
            pair_phenomena[case["pair_id"]] = case["phenomenon"]
        counts = {}
        for phenomenon in pair_phenomena.values():
            counts[phenomenon] = counts.get(phenomenon, 0) + 1
        self.assertEqual(set(counts.values()), {6})
        self.assertEqual(len(counts), 11)

    def test_ir_validation_accepts_gold(self):
        for case in build_cases():
            self.assertEqual(validate_ir(case["gold_ir"], case["target"]), case["gold_ir"])

    def test_ir_validation_records_non_target_focus_as_an_outcome(self):
        value = validate_ir({
            "focus_span": "missing",
            "focus_strength": 2,
            "boundary": "final",
            "delivery": "corrective",
            "pace": "normal",
        }, "The target sentence.")
        self.assertIn("exact substring", semantic_ir_error(value, "The target sentence."))


if __name__ == "__main__":
    unittest.main()
