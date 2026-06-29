from __future__ import annotations

import math
import struct
import unittest

from conversation_prosody_pipeline import PCMFormat, ProsodySession, TurnTiming


class PCMFormatTests(unittest.TestCase):
    def test_reports_sample_and_frame_sizes(self) -> None:
        audio_format = PCMFormat(
            encoding="pcm_s24le",
            sample_rate=48_000,
            channel_count=2,
        )

        self.assertEqual(audio_format.sample_width, 3)
        self.assertEqual(audio_format.frame_size, 6)

    def test_rejects_unknown_encoding_and_invalid_dimensions(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported PCM encoding"):
            PCMFormat(encoding="float32", sample_rate=16_000, channel_count=1)
        with self.assertRaisesRegex(ValueError, "sample_rate"):
            PCMFormat(encoding="pcm_s16le", sample_rate=0, channel_count=1)
        with self.assertRaisesRegex(TypeError, "sample_rate must be an integer"):
            PCMFormat(
                encoding="pcm_s16le",
                sample_rate=16_000.5,  # type: ignore[arg-type]
                channel_count=1,
            )
        with self.assertRaisesRegex(ValueError, "channel_count"):
            PCMFormat(encoding="pcm_s16le", sample_rate=16_000, channel_count=0)
        with self.assertRaisesRegex(TypeError, "channel_count must be an integer"):
            PCMFormat(
                encoding="pcm_s16le",
                sample_rate=16_000,
                channel_count=1.5,  # type: ignore[arg-type]
            )

    def test_maps_supported_wav_sample_widths(self) -> None:
        audio_format = PCMFormat.from_wav_format(
            sample_rate=8_000,
            sample_width=1,
            channel_count=1,
        )

        self.assertEqual(audio_format.encoding, "pcm_u8")

        with self.assertRaisesRegex(ValueError, "unsupported PCM sample width"):
            PCMFormat.from_wav_format(
                sample_rate=8_000,
                sample_width=8,
                channel_count=1,
            )


class StreamingTurnTests(unittest.TestCase):
    def setUp(self) -> None:
        self.audio_format = PCMFormat(
            encoding="pcm_s16le",
            sample_rate=1_000,
            channel_count=1,
        )
        self.session = ProsodySession()

    def test_derives_duration_energy_timing_and_turn_id_from_pcm(self) -> None:
        turn = self.session.start_turn(
            turn_id="turn-1",
            audio_format=self.audio_format,
            start_ms=250.0,
        )
        turn.push_audio(self._samples(0, 16_384), sequence=0)
        turn.push_audio(self._samples(-16_384, 0), sequence=1)
        turn.end_audio()

        metadata = turn.finish(transcript="one two")

        self.assertEqual(turn.frame_count, 4)
        self.assertEqual(turn.chunk_count, 2)
        self.assertEqual(metadata.turn_id, "turn-1")
        self.assertEqual(metadata.features.duration_ms, 4.0)
        self.assertEqual(metadata.features.speech_rate_wpm, 30_000.0)
        self.assertTrue(
            math.isclose(metadata.features.energy_rms, math.sqrt(0.125), rel_tol=1e-12)
        )
        self.assertEqual(
            metadata.timing,
            TurnTiming(start_ms=250.0, end_ms=254.0, duration_ms=4.0),
        )
        self.assertEqual(metadata.to_dict()["turn_id"], "turn-1")
        self.assertTrue(turn.is_finalized)
        self.assertIsNone(self.session.active_turn)

    def test_feature_aggregation_is_independent_of_chunk_boundaries(self) -> None:
        samples = [0, 1_000, -2_000, 3_000, -4_000]
        raw_pcm = self._samples(*samples)

        single_chunk = self.session.start_turn(
            turn_id="single-chunk",
            audio_format=self.audio_format,
        )
        single_chunk.push_audio(raw_pcm, sequence=0)
        single_chunk.end_audio()
        single_metadata = single_chunk.finish(transcript="same")

        split_chunks = self.session.start_turn(
            turn_id="split-chunks",
            audio_format=self.audio_format,
        )
        split_chunks.push_audio(raw_pcm[:4], sequence=0)
        split_chunks.push_audio(raw_pcm[4:6], sequence=1)
        split_chunks.push_audio(raw_pcm[6:], sequence=2)
        split_chunks.end_audio()
        split_metadata = split_chunks.finish(transcript="same")

        self.assertEqual(
            split_metadata.features.duration_ms,
            single_metadata.features.duration_ms,
        )
        self.assertTrue(
            math.isclose(
                split_metadata.features.energy_rms,
                single_metadata.features.energy_rms,
                rel_tol=1e-12,
            )
        )

    def test_accepts_caller_provided_turn_timing(self) -> None:
        timing = TurnTiming(start_ms=1_200.0, end_ms=1_700.0, duration_ms=500.0)
        turn = self.session.start_turn(turn_id="timed", audio_format=self.audio_format)
        turn.push_audio(self._samples(1, 2), sequence=0)
        turn.end_audio()

        metadata = turn.finish(transcript="timed", timing=timing)

        self.assertEqual(metadata.timing, timing)
        self.assertEqual(metadata.features.duration_ms, 2.0)

    def test_rejects_invalid_timing_without_finalizing(self) -> None:
        turn = self.session.start_turn(turn_id="timing-type", audio_format=self.audio_format)
        turn.push_audio(self._samples(1), sequence=0)
        turn.end_audio()

        with self.assertRaisesRegex(TypeError, "timing must be a TurnTiming or None"):
            turn.finish(transcript="timed", timing={})  # type: ignore[arg-type]

        self.assertTrue(turn.is_audio_complete)
        self.assertEqual(self.session.pipeline.baseline.sample_count, 0)

    def test_rejects_missing_duplicate_and_reordered_sequences(self) -> None:
        turn = self.session.start_turn(turn_id="ordered", audio_format=self.audio_format)

        with self.assertRaisesRegex(ValueError, "expected audio sequence 0, received 1"):
            turn.push_audio(self._samples(1), sequence=1)
        with self.assertRaisesRegex(TypeError, "sequence must be an integer"):
            turn.push_audio(self._samples(1), sequence=0.0)  # type: ignore[arg-type]

        turn.push_audio(self._samples(1), sequence=0)

        with self.assertRaisesRegex(ValueError, "expected audio sequence 1, received 0"):
            turn.push_audio(self._samples(1), sequence=0)
        with self.assertRaisesRegex(ValueError, "expected audio sequence 1, received 2"):
            turn.push_audio(self._samples(1), sequence=2)

    def test_rejects_empty_partial_and_non_bytes_chunks_without_advancing(self) -> None:
        stereo = PCMFormat(encoding="pcm_s16le", sample_rate=1_000, channel_count=2)
        turn = self.session.start_turn(turn_id="framing", audio_format=stereo)

        with self.assertRaisesRegex(ValueError, "at least one complete frame"):
            turn.push_audio(b"", sequence=0)
        with self.assertRaisesRegex(ValueError, "not divisible by frame size 4"):
            turn.push_audio(b"\x00\x00", sequence=0)
        with self.assertRaisesRegex(TypeError, "raw_pcm must be bytes"):
            turn.push_audio(bytearray(b"\x00\x00\x00\x00"), sequence=0)  # type: ignore[arg-type]

        self.assertEqual(turn.chunk_count, 0)
        self.assertEqual(turn.frame_count, 0)

    def test_separates_audio_completion_from_transcript_finalization(self) -> None:
        turn = self.session.start_turn(turn_id="empty", audio_format=self.audio_format)

        with self.assertRaisesRegex(ValueError, "before audio is complete"):
            turn.finish(transcript="")
        with self.assertRaisesRegex(ValueError, "before audio has been received"):
            turn.end_audio()

        self.assertTrue(turn.is_open)
        self.assertIs(self.session.active_turn, turn)

        turn.push_audio(self._samples(1), sequence=0)
        turn.end_audio()

        self.assertTrue(turn.is_audio_complete)
        self.assertIs(self.session.active_turn, turn)
        with self.assertRaisesRegex(ValueError, "audio_complete turn"):
            turn.push_audio(self._samples(1), sequence=1)

        turn.finish(transcript="arrived later")

    def test_finalization_and_abort_are_one_time_operations(self) -> None:
        finalized = self.session.start_turn(
            turn_id="finalized",
            audio_format=self.audio_format,
        )
        finalized.push_audio(self._samples(1), sequence=0)
        finalized.end_audio()
        finalized.finish(transcript="done")

        with self.assertRaisesRegex(ValueError, "finalized turn"):
            finalized.push_audio(self._samples(1), sequence=1)
        with self.assertRaisesRegex(ValueError, "finalized turn"):
            finalized.finish(transcript="again")
        with self.assertRaisesRegex(ValueError, "finalized turn"):
            finalized.abort()

        aborted = self.session.start_turn(turn_id="aborted", audio_format=self.audio_format)
        aborted.push_audio(self._samples(1), sequence=0)
        aborted.abort()

        self.assertTrue(aborted.is_aborted)
        self.assertIsNone(self.session.active_turn)
        with self.assertRaisesRegex(ValueError, "aborted turn"):
            aborted.finish(transcript="too late")

    def test_rejects_invalid_turn_identity_and_start_time(self) -> None:
        with self.assertRaisesRegex(ValueError, "turn_id must not be empty"):
            self.session.start_turn(turn_id="", audio_format=self.audio_format)
        with self.assertRaisesRegex(TypeError, "turn_id must be a string"):
            self.session.start_turn(
                turn_id=1,  # type: ignore[arg-type]
                audio_format=self.audio_format,
            )
        with self.assertRaisesRegex(TypeError, "audio_format must be a PCMFormat"):
            self.session.start_turn(
                turn_id="bad-format",
                audio_format="pcm_s16le",  # type: ignore[arg-type]
            )
        with self.assertRaisesRegex(ValueError, "start_ms must be finite and not negative"):
            self.session.start_turn(
                turn_id="negative-time",
                audio_format=self.audio_format,
                start_ms=-1.0,
            )
        with self.assertRaisesRegex(ValueError, "start_ms must be finite and not negative"):
            self.session.start_turn(
                turn_id="infinite-time",
                audio_format=self.audio_format,
                start_ms=math.inf,
            )

    @staticmethod
    def _samples(*values: int) -> bytes:
        return b"".join(struct.pack("<h", value) for value in values)


class ProsodySessionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.audio_format = PCMFormat(
            encoding="pcm_s16le",
            sample_rate=1_000,
            channel_count=1,
        )

    def test_updates_baseline_only_for_finalized_turns(self) -> None:
        session = ProsodySession()
        aborted = session.start_turn(turn_id="aborted", audio_format=self.audio_format)
        aborted.push_audio(struct.pack("<h", 1_000), sequence=0)
        aborted.abort()

        first = self._finish_turn(session, "first", [1_000, -1_000])
        second = self._finish_turn(session, "second", [2_000, -2_000])

        self.assertEqual(first.baseline_sample_count, 0)
        self.assertEqual(second.baseline_sample_count, 1)
        self.assertEqual(session.pipeline.baseline.sample_count, 2)
        self.assertGreater(second.deltas.absolute["energy_rms"], 0)

    def test_allows_only_one_active_turn_and_unique_ids(self) -> None:
        session = ProsodySession()
        turn = session.start_turn(turn_id="one", audio_format=self.audio_format)

        with self.assertRaisesRegex(ValueError, "is still active"):
            session.start_turn(turn_id="two", audio_format=self.audio_format)

        turn.abort()

        with self.assertRaisesRegex(ValueError, "has already been used"):
            session.start_turn(turn_id="one", audio_format=self.audio_format)

    def test_sessions_keep_independent_conversation_baselines(self) -> None:
        first_session = ProsodySession()
        second_session = ProsodySession()

        self._finish_turn(first_session, "first-a", [1_000])
        first_b = self._finish_turn(first_session, "first-b", [2_000])
        second_a = self._finish_turn(second_session, "second-a", [2_000])

        self.assertEqual(first_b.baseline_sample_count, 1)
        self.assertEqual(second_a.baseline_sample_count, 0)

    def test_reset_clears_baseline_and_turn_ids(self) -> None:
        session = ProsodySession()
        self._finish_turn(session, "reusable", [1_000])

        session.reset()
        after_reset = self._finish_turn(session, "reusable", [2_000])

        self.assertEqual(after_reset.baseline_sample_count, 0)

    def test_reset_rejects_an_active_turn(self) -> None:
        session = ProsodySession()
        turn = session.start_turn(turn_id="active", audio_format=self.audio_format)

        with self.assertRaisesRegex(ValueError, "while a turn is active"):
            session.reset()

        turn.abort()

    def _finish_turn(
        self,
        session: ProsodySession,
        turn_id: str,
        samples: list[int],
    ):
        turn = session.start_turn(turn_id=turn_id, audio_format=self.audio_format)
        raw_pcm = b"".join(struct.pack("<h", value) for value in samples)
        turn.push_audio(raw_pcm, sequence=0)
        turn.end_audio()
        return turn.finish(transcript="one word")


if __name__ == "__main__":
    unittest.main()
