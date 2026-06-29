from __future__ import annotations

from dataclasses import dataclass
import json
import math
import struct
from typing import Iterator

from conversation_prosody_pipeline import PCMFormat, ProsodySession, TurnTiming


SAMPLE_RATE = 8_000
CHUNK_FRAMES = 800
AUDIO_FORMAT = PCMFormat(
    encoding="pcm_s16le",
    sample_rate=SAMPLE_RATE,
    channel_count=1,
)


@dataclass(frozen=True)
class FinalTranscript:
    text: str
    timing: TurnTiming


class FakeSpeechToText:
    """Stand in for an external STT client that receives the same PCM stream."""

    def __init__(self, transcript: str, start_ms: float) -> None:
        self.transcript = transcript
        self.start_ms = start_ms
        self.frame_count = 0

    def push_audio(self, raw_pcm: bytes) -> None:
        self.frame_count += len(raw_pcm) // AUDIO_FORMAT.frame_size

    def finalize(self) -> FinalTranscript:
        duration_ms = self.frame_count / SAMPLE_RATE * 1000.0
        return FinalTranscript(
            text=self.transcript,
            timing=TurnTiming(
                start_ms=self.start_ms,
                end_ms=self.start_ms + duration_ms,
                duration_ms=duration_ms,
            ),
        )


def main() -> None:
    session = ProsodySession()
    results = [
        process_turn(
            session,
            turn_id="turn-1",
            transcript="Yeah, that's fine.",
            start_ms=0.0,
            amplitude=12_000,
        ),
        process_turn(
            session,
            turn_id="turn-2",
            transcript="Yeah... I'm fine.",
            start_ms=1_500.0,
            amplitude=4_000,
        ),
    ]
    print(json.dumps(results, indent=2))


def process_turn(
    session: ProsodySession,
    *,
    turn_id: str,
    transcript: str,
    start_ms: float,
    amplitude: int,
) -> dict[str, object]:
    """Imitate a microphone tee feeding external STT and CPP together."""

    stt = FakeSpeechToText(transcript, start_ms)
    turn = session.start_turn(
        turn_id=turn_id,
        audio_format=AUDIO_FORMAT,
        start_ms=start_ms,
    )

    for sequence, raw_pcm in enumerate(iter_audio_chunks(amplitude=amplitude)):
        stt.push_audio(raw_pcm)
        turn.push_audio(raw_pcm, sequence=sequence)

    turn.end_audio()
    final_transcript = stt.finalize()
    metadata = turn.finish(
        transcript=final_transcript.text,
        timing=final_transcript.timing,
    )
    return metadata.to_dict()


def iter_audio_chunks(*, amplitude: int) -> Iterator[bytes]:
    for chunk_index in range(10):
        samples = bytearray()
        for frame_offset in range(CHUNK_FRAMES):
            frame_index = chunk_index * CHUNK_FRAMES + frame_offset
            sample = int(amplitude * math.sin(2 * math.pi * 220 * frame_index / SAMPLE_RATE))
            samples.extend(struct.pack("<h", sample))
        yield bytes(samples)


if __name__ == "__main__":
    main()
