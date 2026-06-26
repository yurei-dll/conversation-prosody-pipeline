# Simulated Audio Stream Ingest

The experimental streaming path in `audio_stream.py` uses WAV files as
deterministic simulated audio streams. It exists to validate the stream-processing
architecture before any live capture adapter is introduced.

This is not live microphone support. The module does not open devices, capture
audio, call speech-to-text services, infer emotion, identify speakers, or store
voiceprints. It uses only the Python standard library and reads local PCM WAV
data with `wave`.

## Shape

- `AudioChunk` carries raw PCM bytes, audio format fields, chunk timing, and an
  `is_final` marker.
- `iter_wav_chunks()` reads a WAV file incrementally and yields ordered chunks
  without loading the full file at once.
- `StreamingFeatureAccumulator` accepts chunks one at a time and accumulates
  minimal measurable features: duration and RMS energy.
- `ingest_wav_stream()` runs the simulated stream and returns the same
  pipeline-native `RawTurn` and `TurnFeatures` shape used elsewhere.

Transcripts remain caller-provided. Passing a transcript at finalization time
allows the accumulator to compute `speech_rate_wpm`; no STT is performed.

Future live microphone or transport adapters can reuse the same chunk and
accumulator shape by producing `AudioChunk` objects from their own source.
