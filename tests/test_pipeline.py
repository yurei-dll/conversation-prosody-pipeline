import unittest

from conversation_prosody_pipeline import ProsodyPipeline, TurnFeatures, TurnTiming


class ProsodyPipelineTests(unittest.TestCase):
    def test_first_turn_has_no_deltas_before_baseline_exists(self) -> None:
        pipeline = ProsodyPipeline()

        metadata = pipeline.process_turn("Hello.", TurnFeatures(speech_rate_wpm=120))

        self.assertEqual(metadata.baseline_sample_count, 0)
        self.assertEqual(metadata.deltas.absolute, {})
        self.assertEqual(metadata.deltas.relative, {})

    def test_second_turn_reports_observational_deltas(self) -> None:
        pipeline = ProsodyPipeline()
        pipeline.process_turn(
            "First turn.",
            TurnFeatures(speech_rate_wpm=100, pause_before_ms=200),
        )

        metadata = pipeline.process_turn(
            "Second turn.",
            TurnFeatures(speech_rate_wpm=75, pause_before_ms=500),
        )

        self.assertEqual(metadata.baseline_sample_count, 1)
        self.assertEqual(metadata.deltas.absolute["speech_rate_wpm"], -25)
        self.assertEqual(metadata.deltas.relative["speech_rate_wpm"], -0.25)
        self.assertEqual(metadata.deltas.absolute["pause_before_ms"], 300)
        self.assertEqual(metadata.to_dict()["transcript"], "Second turn.")

    def test_metadata_serializes_schema_version(self) -> None:
        pipeline = ProsodyPipeline()

        metadata = pipeline.process_turn("Versioned turn.", TurnFeatures(speech_rate_wpm=120))

        serialized = metadata.to_dict()
        self.assertEqual(serialized["schema_version"], "1.0")
        self.assertNotIn("timing", serialized)

    def test_metadata_serializes_timing_when_provided(self) -> None:
        pipeline = ProsodyPipeline()

        metadata = pipeline.process_turn(
            "Timed turn.",
            TurnFeatures(speech_rate_wpm=90),
            timing=TurnTiming(start_ms=125.0, end_ms=2125.0, duration_ms=2000.0),
        )

        self.assertEqual(
            metadata.to_dict()["timing"],
            {
                "start_ms": 125.0,
                "end_ms": 2125.0,
                "duration_ms": 2000.0,
            },
        )


if __name__ == "__main__":
    unittest.main()
