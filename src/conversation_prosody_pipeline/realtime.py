"""Transport-neutral real-time turn ingestion."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable

from conversation_prosody_pipeline.audio_file import _sample_squares, _speech_rate_wpm
from conversation_prosody_pipeline.pipeline import ProsodyPipeline
from conversation_prosody_pipeline.types import TurnFeatures, TurnMetadata, TurnTiming


_SAMPLE_WIDTHS = {
    "pcm_u8": 1,
    "pcm_s16le": 2,
    "pcm_s24le": 3,
    "pcm_s32le": 4,
}


@dataclass(frozen=True)
class PCMFormat:
    """The fixed encoding and layout of one turn's interleaved PCM audio."""

    encoding: str
    sample_rate: int
    channel_count: int

    def __post_init__(self) -> None:
        if self.encoding not in _SAMPLE_WIDTHS:
            supported = ", ".join(sorted(_SAMPLE_WIDTHS))
            raise ValueError(
                f"unsupported PCM encoding {self.encoding!r}; expected one of {supported}"
            )
        if not isinstance(self.sample_rate, int) or isinstance(self.sample_rate, bool):
            raise TypeError("sample_rate must be an integer")
        if self.sample_rate <= 0:
            raise ValueError("sample_rate must be greater than zero")
        if not isinstance(self.channel_count, int) or isinstance(self.channel_count, bool):
            raise TypeError("channel_count must be an integer")
        if self.channel_count <= 0:
            raise ValueError("channel_count must be greater than zero")

    @property
    def sample_width(self) -> int:
        """Return the number of bytes in one sample for one channel."""

        return _SAMPLE_WIDTHS[self.encoding]

    @property
    def frame_size(self) -> int:
        """Return the number of bytes in one interleaved audio frame."""

        return self.sample_width * self.channel_count

    @classmethod
    def from_wav_format(
        cls,
        *,
        sample_rate: int,
        sample_width: int,
        channel_count: int,
    ) -> PCMFormat:
        """Create a format for the integer PCM encodings supported by WAV ingest."""

        encodings = {
            1: "pcm_u8",
            2: "pcm_s16le",
            3: "pcm_s24le",
            4: "pcm_s32le",
        }
        try:
            encoding = encodings[sample_width]
        except KeyError as error:
            raise ValueError(f"unsupported PCM sample width: {sample_width}") from error
        return cls(
            encoding=encoding,
            sample_rate=sample_rate,
            channel_count=channel_count,
        )


class StreamingTurn:
    """Accumulate one ordered PCM turn and finalize it through a pipeline."""

    def __init__(
        self,
        *,
        turn_id: str,
        audio_format: PCMFormat,
        pipeline: ProsodyPipeline,
        start_ms: float = 0.0,
        on_close: Callable[[StreamingTurn], None] | None = None,
    ) -> None:
        if not isinstance(turn_id, str):
            raise TypeError("turn_id must be a string")
        if not turn_id:
            raise ValueError("turn_id must not be empty")
        if not isinstance(start_ms, (int, float)) or isinstance(start_ms, bool):
            raise TypeError("start_ms must be numeric")
        if not math.isfinite(start_ms) or start_ms < 0:
            raise ValueError("start_ms must be finite and not negative")
        if not isinstance(audio_format, PCMFormat):
            raise TypeError("audio_format must be a PCMFormat")

        self.turn_id = turn_id
        self.audio_format = audio_format
        self.start_ms = start_ms
        self._pipeline = pipeline
        self._on_close = on_close
        self._expected_sequence = 0
        self._frame_count = 0
        self._sample_count = 0
        self._total_squares = 0.0
        self._state = "open"

    @property
    def is_open(self) -> bool:
        return self._state == "open"

    @property
    def is_finalized(self) -> bool:
        return self._state == "finalized"

    @property
    def is_audio_complete(self) -> bool:
        return self._state == "audio_complete"

    @property
    def is_aborted(self) -> bool:
        return self._state == "aborted"

    @property
    def chunk_count(self) -> int:
        return self._expected_sequence

    @property
    def frame_count(self) -> int:
        return self._frame_count

    @property
    def duration_ms(self) -> float:
        return self._frame_count / self.audio_format.sample_rate * 1000.0

    def push_audio(self, raw_pcm: bytes, *, sequence: int) -> None:
        """Add the next complete PCM chunk in sequence order."""

        self._require_open("push audio")
        if not isinstance(sequence, int) or isinstance(sequence, bool):
            raise TypeError("sequence must be an integer")
        if sequence < 0:
            raise ValueError("sequence must not be negative")
        if sequence != self._expected_sequence:
            raise ValueError(
                f"expected audio sequence {self._expected_sequence}, received {sequence}"
            )
        if not isinstance(raw_pcm, bytes):
            raise TypeError("raw_pcm must be bytes")
        if not raw_pcm:
            raise ValueError("raw_pcm must contain at least one complete frame")
        if len(raw_pcm) % self.audio_format.frame_size != 0:
            raise ValueError(
                f"PCM chunk length {len(raw_pcm)} is not divisible by frame size "
                f"{self.audio_format.frame_size}"
            )

        total_squares, sample_count = _sample_squares(
            raw_pcm,
            self.audio_format.sample_width,
        )
        self._total_squares += total_squares
        self._sample_count += sample_count
        self._frame_count += len(raw_pcm) // self.audio_format.frame_size
        self._expected_sequence += 1

    def end_audio(self) -> None:
        """Close PCM ingestion while allowing the final transcript to arrive later."""

        self._require_open("end audio for")
        if self._frame_count == 0:
            raise ValueError("cannot end audio before audio has been received")
        self._state = "audio_complete"

    def finish(
        self,
        *,
        transcript: str,
        timing: TurnTiming | None = None,
    ) -> TurnMetadata:
        """Finalize the turn once and update its conversation-local baseline."""

        if self._state != "audio_complete":
            if self._state == "open":
                raise ValueError("cannot finalize before audio is complete")
            raise ValueError(f"cannot finalize a {self._state} turn")
        if not isinstance(transcript, str):
            raise TypeError("transcript must be a string")
        if timing is not None and not isinstance(timing, TurnTiming):
            raise TypeError("timing must be a TurnTiming or None")

        duration_ms = self.duration_ms
        energy_rms = None
        if self._sample_count > 0:
            energy_rms = (self._total_squares / self._sample_count) ** 0.5

        features = TurnFeatures(
            duration_ms=duration_ms,
            energy_rms=energy_rms,
            speech_rate_wpm=_speech_rate_wpm(transcript, duration_ms),
        )
        resolved_timing = timing or TurnTiming(
            start_ms=self.start_ms,
            end_ms=self.start_ms + duration_ms,
            duration_ms=duration_ms,
        )
        metadata = self._pipeline.process_turn(
            transcript=transcript,
            features=features,
            timing=resolved_timing,
            turn_id=self.turn_id,
        )
        self._state = "finalized"
        self._notify_closed()
        return metadata

    def abort(self) -> None:
        """Discard an unfinished turn without updating the baseline."""

        if self._state in {"finalized", "aborted"}:
            raise ValueError(f"cannot abort a {self._state} turn")
        self._state = "aborted"
        self._notify_closed()

    def _require_open(self, operation: str) -> None:
        if self._state != "open":
            raise ValueError(f"cannot {operation} a {self._state} turn")

    def _notify_closed(self) -> None:
        if self._on_close is not None:
            self._on_close(self)


class ProsodySession:
    """Own one conversation baseline and its currently active streaming turn."""

    def __init__(self, pipeline: ProsodyPipeline | None = None) -> None:
        self.pipeline = pipeline or ProsodyPipeline()
        self._active_turn: StreamingTurn | None = None
        self._used_turn_ids: set[str] = set()

    @property
    def active_turn(self) -> StreamingTurn | None:
        return self._active_turn

    def start_turn(
        self,
        *,
        turn_id: str,
        audio_format: PCMFormat,
        start_ms: float = 0.0,
    ) -> StreamingTurn:
        """Start the sole active turn in this conversation session."""

        if self._active_turn is not None:
            raise ValueError(f"turn {self._active_turn.turn_id!r} is still active")
        if not isinstance(turn_id, str):
            raise TypeError("turn_id must be a string")
        if turn_id in self._used_turn_ids:
            raise ValueError(f"turn_id {turn_id!r} has already been used in this session")

        turn = StreamingTurn(
            turn_id=turn_id,
            audio_format=audio_format,
            pipeline=self.pipeline,
            start_ms=start_ms,
            on_close=self._close_turn,
        )
        self._active_turn = turn
        self._used_turn_ids.add(turn_id)
        return turn

    def reset(self) -> None:
        """Clear conversation-local state when no turn is active."""

        if self._active_turn is not None:
            raise ValueError("cannot reset a session while a turn is active")
        self.pipeline = ProsodyPipeline()
        self._used_turn_ids.clear()

    def _close_turn(self, turn: StreamingTurn) -> None:
        if self._active_turn is turn:
            self._active_turn = None
