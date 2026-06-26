# Add WAV ingestion path

> We are creating branch dev-python-ingest-file from dev-python.
>
> Goal:
> Add a minimal dependency-free audio file ingestion path for a simple WAV file of one person speaking.
>
> Important constraints:
>
> - Do not add Whisper, librosa, numpy, scipy, torch, pydub, ffmpeg, or any external audio dependencies.
> - Use only the Python standard library for this milestone.
> - Support WAV files only.
> - Assume the transcript is provided by the caller.
> - Do not attempt automatic speech recognition.
> - Do not infer emotion.
> - Do not identify speakers.
> - Do not persist voiceprints or biometric profiles.
>
> Desired behavior:
> Given:
>
> - path to a WAV file
> - transcript string
>
> Produce:
>
> - RawTurn
> - TurnTiming
> - basic TurnFeatures
> - TurnMetadata JSON through ProsodyPipeline
>
> Implementation tasks:
>
> 1. Add a module such as:
>    src/conversation_prosody_pipeline/audio_file.py
>
> 2. Implement a small WAV reader using the standard library `wave` module.
>
> 3. Add a function or class that reads:
>    - sample rate
>    - number of frames
>    - duration_ms
>    - sample width
>    - channel count
>
> 4. Compute only basic safe features:
>    - duration_ms
>    - energy_rms from PCM samples if feasible with stdlib
>    - speech_rate_wpm from provided transcript word count divided by duration
>
> 5. Create a helper such as:
>    ingest_wav_file(path: str | Path, transcript: str) -> tuple[RawTurn, TurnFeatures]
>
>    or a small adapter class if that fits the current extractor architecture better.
>
> 6. Add an example:
>    examples/ingest_wav_file.py
>
>    It should accept or clearly show:
>    - a WAV path
>    - a transcript
>    - use ProsodyPipeline
>    - print JSON metadata
>
> 7. Add tests using a generated tiny WAV file created during the test with the standard library.
>    Do not commit binary audio files.
>
> 8. Update docs/architecture.md or add docs/audio-file-ingest.md explaining:
>    - this is a minimal local WAV ingestion path
>    - transcript is caller-provided
>    - no STT is performed
>    - this exists to validate the pipeline shape before adding real speech adapters
>
> 9. Keep the existing tests passing.
>
> Definition of done:
>
> - `scripts/venv run python -m unittest discover -s tests` passes.
> - The new example runs against a generated or documented WAV file.
> - No new runtime dependencies are added.

<details><summary>18 previous messages</summary>

> I’ll take this through end to end: first I’m going to inspect the existing pipeline/types shape and tests so the new ingest path plugs in with the least ceremony. Then I’ll add the module, example, docs, and a generated-WAV unit test.
>
> <details><summary>Explored 2 files, a list, ran a command</summary>
>
> - Ran `git status --short --branch`
>
> <details><summary>Explored 2 files, a list</summary>
>
> - Read `./src/conversation_prosody_pipeline/pipeline.py`
> - Read `./src/conversation_prosody_pipeline/types.py`
> - Listed files
>
> </details>
>
> </details>
>
> The branch is already `dev-python-ingest-file`, so I’m staying on it. The core model is pleasantly small: `ProsodyPipeline.process_turn()` takes transcript/features/timing, so the ingest helper can return exactly those native objects without bending the architecture.
>
> <details><summary>Explored 6 files</summary>
>
> - Read `./src/conversation_prosody_pipeline/__init__.py`
> - Read `./src/conversation_prosody_pipeline/extractors.py`
> - Read `./src/conversation_prosody_pipeline/baseline.py`
> - Read `./tests/test_pipeline.py`
> - Read `./docs/architecture.md`
> - Read `./examples/minimal_turn.py`
>
> </details>
>
> I found the extractor protocols, but for this milestone a direct adapter module is cleaner than a new protocol implementation: read WAV metadata, compute safe basics, build `RawTurn` plus `TurnFeatures`, and let the caller feed those through `ProsodyPipeline`. I’m going to wire it into the public package exports too, since the example should feel first-class.
>
> <details><summary>Explored 3 files</summary>
>
> - Read `./pyproject.toml`
> - Read `./README.md`
> - Read `./DEVELOPMENT.md`
>
> </details>
>
> I’m making one small schema extension here: adding optional `duration_ms` to `TurnFeatures`. Timing already carries the same duration structurally, but including it in features matches the requested metadata JSON and allows baseline comparisons just like speech rate and energy.
>
> <details><summary>Created a file, edited 2 files</summary>
>
> - Wrote `./src/conversation_prosody_pipeline/__init__.py` (+4 -0)
> - Wrote `./src/conversation_prosody_pipeline/audio_file.py` (+140 -0)
> - Wrote `./src/conversation_prosody_pipeline/types.py` (+1 -0)
>
> </details>
>
> The WAV reader now does the narrow job: uncompressed PCM metadata plus normalized RMS over raw samples, including 8/16/24/32-bit PCM handling. Next I’m adding the example and tests with a generated temporary WAV, so the repo stays dependency-free and binary-free.
>
> <details><summary>Created 3 files, edited a file</summary>
>
> - Wrote `./docs/architecture.md` (+7 -2)
> - Wrote `./docs/audio-file-ingest.md` (+50 -0)
> - Wrote `./examples/ingest_wav_file.py` (+61 -0)
> - Wrote `./tests/test_audio_file.py` (+66 -0)
>
> </details>
>
> The new example can run two ways: with a real WAV and transcript, or with no args, where it creates a temporary one-second WAV and prints pipeline JSON. I’ve also added a focused doc page and linked it from architecture.
>
> <details><summary>Ran 2 commands</summary>
>
> - Ran `scripts/venv run python examples/ingest_wav_file.py`
> - Ran `scripts/venv run python -m unittest discover -s tests`
>
> </details>
>
> Tests and the no-argument example both pass. I’m doing a quick diff pass now to catch small API/doc nits before I call it done.
>
> <details><summary>Ran 2 commands</summary>
>
> - Ran `git diff -- src/conversation_prosody_pipeline/audio_file.py src/conversation_prosody_pipeline/types.py src/conversation_prosody_pipeline/__init__.py tests/test_audio_file.py examples/ingest_wav_file.py docs/architecture.md docs/audio-file-ingest.md`
> - Ran `git status --short`
>
> </details>
>
> One thing I noticed on the pass: since `duration_ms` is now serialized inside `features`, I’m going to update the metadata schema doc too. It’s a small extra touch, but it keeps the documentation honest with the new JSON surface.
>
> <details><summary>Edited a file, explored 4 files</summary>
>
> <details><summary>Explored a file</summary>
>
> - Read `./docs/metadata-schema.md`
>
> </details>
>
> - Wrote `./docs/metadata-schema.md` (+3 -1)
>
> <details><summary>Explored 3 files</summary>
>
> - Read `./src/conversation_prosody_pipeline/audio_file.py`
> - Read `./examples/ingest_wav_file.py`
> - Read `./tests/test_audio_file.py`
>
> </details>
>
> </details>
>
> Everything still looks within the requested boundaries: no dependency changes, no committed audio files, and the example-generated WAV lives only in a temp directory. I’m doing one final test run after the doc/schema touch so the reported result is current.
>
> <details><summary>Ran 3 commands</summary>
>
> - Ran `git diff --stat`
> - Ran `scripts/venv run python -m unittest discover -s tests`
> - Ran `git status --short --branch`
>
> </details>
</details>

Implemented the minimal WAV ingestion path on `dev-python-ingest-file`.

What changed:

- Added [audio_file.py](./src/conversation_prosody_pipeline/audio_file.py) with:
  - `WavInfo`
  - `read_wav_info(...)`
  - `ingest_wav_file(...)`
  - stdlib-only PCM RMS energy calculation
- Added `duration_ms` to `TurnFeatures` so it appears in metadata JSON.
- Exported the new ingest helpers from package `__init__`.
- Added [examples/ingest_wav_file.py](./examples/ingest_wav_file.py), which works with a provided WAV/transcript or generates a temporary WAV when run with no args.
- Added generated-WAV tests in [test_audio_file.py](./tests/test_audio_file.py).
- Added [docs/audio-file-ingest.md](./docs/audio-file-ingest.md) and updated architecture/schema docs.

Verified:

- `scripts/venv run python -m unittest discover -s tests` passes: 11 tests.
- `scripts/venv run python examples/ingest_wav_file.py` runs and prints metadata JSON.
- No new runtime dependencies added.

> Sweet. Can you also setup a small little import/ workspace thats in the ignorelist for now?

<details><summary>8 previous messages</summary>

> Yep, I’ll add a tiny local import workspace that’s ignored so you can drop WAVs/transcripts there without polluting git. I’ll check the repo ignore pattern first, then make the smallest matching addition.
>
> <details><summary>Explored 2 lists, ran a command</summary>
>
> <details><summary>Explored a list</summary>
>
> - Listed files
>
> </details>
>
> - Ran `git status --short --branch`
>
> <details><summary>Explored a list</summary>
>
> - Listed files
>
> </details>
>
> </details>
>
> The branch is clean now, so I’ll keep this as a separate tiny workspace change. I’m going with `import/` at the repo root, plus a tracked `.gitkeep` so the folder exists while its contents stay ignored.
>
> <details><summary>Explored a file</summary>
>
> - Read `./.gitignore`
>
> </details>
>
> I found the ignore file is mostly generic Node/Python plus a couple local helper entries. I’m adding a clearly named local import section so future-you knows it’s intentional, not random clutter.
>
> <details><summary>Created a file, edited a file</summary>
>
> - Wrote `./.gitignore` (+4 -0)
> - Wrote `./import/.gitkeep` (+1 -0)
>
> </details>
>
> The ignored workspace is in place. I’m checking git’s view of it now, including a quick ignored-file probe, so we know dropped files will stay out of status.
>
> <details><summary>Ran 3 commands</summary>
>
> - Ran `git status --short`
> - Ran `git check-ignore -v import/example.wav`
> - Ran `git check-ignore -v import/.gitkeep`
>
> </details>
</details>

Set up a tiny ignored import workspace:

- Added `import/.gitkeep` so the folder exists in git.
- Updated `.gitignore` so `import/*` is ignored, except `import/.gitkeep`.

Verified with `git check-ignore`: files like `import/example.wav` will be ignored, while the placeholder stays tracked.

> Please take a look at the import data I extracted there and try finding actual transcripts for the audio

<details><summary>10 previous messages</summary>

> I’ll look through the ignored `import/` workspace and see what came with the audio: filenames, sidecar metadata, text files, archives, or anything transcript-shaped. If there’s only raw audio, I’ll tell you plainly what’s available and what would require ASR or an external source.
>
> <details><summary>Explored 2 lists, ran a command</summary>
>
> <details><summary>Explored 2 lists</summary>
>
> - Listed files in `import`
> - Listed files in `import`
>
> </details>
>
> - Ran `git status --short --ignored import`
>
> </details>
>
> This is LibriSpeech `dev-clean`, which is good news: it normally ships exact transcript sidecars named like `*-trans.txt` beside the audio. My first file scan was too shallow for the utterances, so I’m going one level deeper and matching the transcript IDs to audio files.
>
> <details><summary>Explored 2 searches, a list</summary>
>
> - Searched for `*.flac` in `dev-clean`
> - Searched for `*trans.txt` in `dev-clean`
> - Listed files in `dev-clean`
>
> </details>
>
> Yep, the exact transcripts are present locally. Each `*.trans.txt` file maps utterance IDs to the matching `.flac` files, so no ASR is needed here; this is lookup work, not transcription. I’m going to build a small ignored manifest so you have an easy audio-path to transcript map to use next.
>
> <details><summary>Explored a file, a search, ran a command</summary>
>
> - Ran `wc -l import/LibriSpeech/dev-clean/*/*/*trans.txt`
>
> <details><summary>Explored a file, a search</summary>
>
> - Read `./import/LibriSpeech/dev-clean/5694/64038/5694-64038.trans.txt`
> - Searched for `*trans.txt` in `dev-clean`
>
> </details>
>
> </details>
>
> I found 2,703 `.flac` files and 2,703 transcript lines across 97 LibriSpeech sidecar files. I’m writing an ignored TSV manifest now with `audio_path`, `utterance_id`, and `transcript`, and I’ll verify there are no missing audio matches.
>
> <details><summary>Ran a command</summary>
>
> - Ran `scripts/venv run python -c "from pathlib import Path
> root = Path('import/LibriSpeech/dev-clean')
> out = Path('import/librispeech-dev-clean-transcripts.tsv')
> rows = []
> missing = []
> for transcript_file in sorted(root.glob('*/*/*.trans.txt')):
>     for line in transcript_file.read_text(encoding='utf-8').splitlines():
>         if not line.strip():
>             continue
>         utterance_id, transcript = line.split(' ', 1)
>         audio_path = transcript_file.with_name(f'{utterance_id}.flac')
>         if not audio_path.exists():
>             missing.append(str(audio_path))
>         rows.append((audio_path.as_posix(), utterance_id, transcript))
> out.write_text('audio_path\tutterance_id\ttranscript\n' + ''.join(f'{audio}\t{uid}\t{text}\n' for audio, uid, text in rows), encoding='utf-8')
> print(f'wrote {len(rows)} rows to {out}')
> print(f'missing audio files: {len(missing)}')"`
>
> </details>
>
> The transcript manifest is built and every transcript ID resolved to a local audio file. I’ll spot-check the manifest and confirm it stays ignored by git.
>
> <details><summary>Explored a file, ran 2 commands</summary>
>
> <details><summary>Explored a file</summary>
>
> - Read `./import/librispeech-dev-clean-transcripts.tsv`
>
> </details>
>
> - Ran `git status --short --ignored import/librispeech-dev-clean-transcripts.tsv import/LibriSpeech/dev-clean/5694/64038/5694-64038-0000.flac`
>
> - Ran `wc -l import/librispeech-dev-clean-transcripts.tsv`
>
> </details>
</details>

Found them. The import data is LibriSpeech `dev-clean`, and it already includes exact transcript sidecars, so no ASR was needed.

I created an ignored manifest here:

`import/librispeech-dev-clean-transcripts.tsv`

It has:

```text
audio_path    utterance_id    transcript
```

Summary:

- 2,703 `.flac` audio files
- 97 `*.trans.txt` transcript files
- 2,703 transcript rows found
- 0 missing audio matches

One important wrinkle: the audio is `.flac`, not `.wav`, so the current WAV-only ingestion helper won’t ingest these files directly yet. But the transcript lookup itself is done and ready to use for a later FLAC conversion/import step.

> Sweet. Can you make a new scripts/ bash that handles converting everything into a import/converted/ workspace? what dependencies do you need for that?

<details><summary>12 previous messages</summary>

> For FLAC-to-WAV conversion, Python’s standard library can’t decode FLAC, so the clean dependency is an external CLI converter. I’ll check what’s already available locally, then I’ll add a bash script that uses the smallest suitable tool and writes into ignored `import/converted/`.
>
> <details><summary>Explored a list, ran 4 commands</summary>
>
> <details><summary>Explored a list</summary>
>
> - Listed files in `scripts`
>
> </details>
>
> - Ran `command -v flac`
>
> - Ran `git status --short --branch`
>
> - Ran `command -v sox`
>
> - Ran `command -v ffmpeg`
>
> </details>
>
> Only `ffmpeg` is installed here; `flac` and `sox` are not. To keep the project dependency-free, I’m going to make this a bash-only helper that shells out to an external converter if present, preferring the lighter `flac` CLI and falling back to `ffmpeg` because this machine already has it.
>
> <details><summary>Created a file</summary>
>
> - Wrote `./scripts/convert_import_flac_to_wav` (+122 -0)
>
> </details>
>
> I added the converter script with resumable behavior: if an output WAV is newer than the source FLAC, it skips it, and it writes a per-utterance `.txt` transcript next to each converted WAV when the LibriSpeech sidecar has a match. Next I’m making it executable and checking the bash syntax/help output.
>
> <details><summary>Ran 3 commands</summary>
>
> - Ran `chmod +x scripts/convert_import_flac_to_wav`
> - Ran `bash -n scripts/convert_import_flac_to_wav`
> - Ran `scripts/convert_import_flac_to_wav --help`
>
> </details>
>
> I caught a little LibriSpeech naming gotcha before running a smoke test: transcript sidecars are named from the first two ID parts, like `1272-128104.trans.txt`, not just the directory name. I’m patching that now so the copied transcript files actually appear beside the WAVs.
>
> <details><summary>Edited a file</summary>
>
> - Wrote `./scripts/convert_import_flac_to_wav` (+3 -2)
>
> </details>
>
> The transcript lookup is corrected. I’ll do a smoke conversion on a small LibriSpeech folder into `/tmp` so we verify the converter and transcript sidecars without filling `import/converted/` during setup.
>
> <details><summary>Ran 2 commands</summary>
>
> - Ran `bash -n scripts/convert_import_flac_to_wav`
> - Ran `scripts/convert_import_flac_to_wav import/LibriSpeech/dev-clean/1272/128104 /tmp/conversation-prosody-convert-smoke`
>
> </details>
>
> The smoke conversion succeeded using local `ffmpeg`: 15 FLACs became WAVs and all 15 transcripts were copied beside them. I’m checking the output shape and git status now.
>
> <details><summary>Explored a file, a list, ran 2 commands</summary>
>
> <details><summary>Explored a list</summary>
>
> - Listed files in `conversation-prosody-convert-smoke`
>
> </details>
>
> - Ran `git status --short --ignored scripts/convert_import_flac_to_wav import/converted`
>
> <details><summary>Explored a file</summary>
>
> - Read `/tmp/conversation-prosody-convert-smoke/1272-128104-0000.txt`
>
> </details>
>
> - Ran `file /tmp/conversation-prosody-convert-smoke/1272-128104-0000.wav`
>
> </details>
</details>

Added [scripts/convert_import_flac_to_wav](./scripts/convert_import_flac_to_wav). It converts all `.flac` files under `import/LibriSpeech/dev-clean` into matching `.wav` files under ignored `import/converted/`, and writes a sibling `.txt` transcript for each utterance.

Dependencies:

- Required shell tools: `bash`, `awk`, `basename`, `dirname`, `find`, `mkdir`, `sort`
- Audio converter CLI: prefers `flac`, falls back to `ffmpeg`
- On this machine: `ffmpeg` is installed; `flac` is not

Usage:

```bash
scripts/convert_import_flac_to_wav
```

Or with custom paths:

```bash
scripts/convert_import_flac_to_wav import/LibriSpeech/dev-clean import/converted
```

I smoke-tested it on one small folder: 15 WAVs converted, 15 transcripts copied, output was valid 16-bit mono 16 kHz WAV.

> SO I installled flac but when I listen to the audio files they almost sound... corrupted. is something broken or are they just designed like that?

<details><summary>8 previous messages</summary>

> Let’s sanity-check the actual files instead of guessing. LibriSpeech clips can sound a bit old-bookish and tightly cropped, but they should not sound digitally garbled; I’ll verify the FLAC integrity, WAV format, and a sample waveform range.
>
> <details><summary>Explored 2 searches, ran 2 commands</summary>
>
> - Ran `command -v flac`
>
> <details><summary>Explored a search</summary>
>
> - Searched for `*.wav` in `converted`
>
> </details>
>
> - Ran `git status --short --branch`
>
> <details><summary>Explored a search</summary>
>
> - Searched for `*.flac` in `dev-clean`
>
> </details>
>
> </details>
>
> Interesting: `flac` is installed now, but there isn’t an `import/converted/` directory in this checkout yet, so I’ll test one source FLAC and make a temporary WAV from it. If the source validates and the decoded WAV has normal PCM stats, the weirdness is probably the dataset/clip style or playback path, not corruption.
>
> <details><summary>Ran 3 commands</summary>
>
> - Ran `flac -t import/LibriSpeech/dev-clean/1272/128104/1272-128104-0000.flac`
> - Ran `file import/LibriSpeech/dev-clean/1272/128104/1272-128104-0000.flac`
> - Ran `flac -a import/LibriSpeech/dev-clean/1272/128104/1272-128104-0000.flac`
>
> </details>
>
> That sample FLAC passes `flac -t`, and `file` reports normal LibriSpeech-ish parameters: 16-bit, mono, 16 kHz. I’m checking decoded PCM levels next; actual corruption usually shows up as full-scale clipping, absurd sample widths, or broken decode errors.
>
> <details><summary>Explored a search, a list, ran 3 commands</summary>
>
> - Ran `flac -d -f -o /tmp/librispeech-sanity.wav import/LibriSpeech/dev-clean/1272/128104/1272-128104-0000.flac`
>
> <details><summary>Explored a search</summary>
>
> - Searched for `*.ana` in `.`
>
> </details>
>
> - Ran `scripts/venv run python -c "import wave, audioop
> p='/tmp/librispeech-sanity.wav'
> with wave.open(p,'rb') as w:
>     frames=w.readframes(w.getnframes())
>     print('channels', w.getnchannels())
>     print('sample_width', w.getsampwidth())
>     print('sample_rate', w.getframerate())
>     print('frames', w.getnframes())
>     print('duration_s', w.getnframes()/w.getframerate())
>     print('rms', audioop.rms(frames, w.getsampwidth()))
>     print('max_abs', audioop.max(frames, w.getsampwidth()))
>     print('avg_abs', audioop.avgpp(frames, w.getsampwidth()))"`
>
> - Ran `file /tmp/librispeech-sanity.wav`
>
> <details><summary>Explored a list</summary>
>
> - Listed files in `1272-128104-0000.flac`
>
> </details>
>
> </details>
>
> Small Python-version footnote: `audioop` is gone in this environment, so I’ll use plain `wave` plus `struct`/`array` style stdlib math instead. The decoded WAV itself is normal RIFF PCM: 16-bit mono at 16 kHz.
>
> <details><summary>Ran a command</summary>
>
> - Ran `scripts/venv run python -c "import math, struct, wave
> p='/tmp/librispeech-sanity.wav'
> with wave.open(p,'rb') as w:
>     width=w.getsampwidth()
>     frames=w.readframes(w.getnframes())
>     samples=struct.unpack('<' + 'h'*(len(frames)//2), frames)
>     max_abs=max(abs(s) for s in samples)
>     rms=math.sqrt(sum(s*s for s in samples)/len(samples))
>     clipped=sum(1 for s in samples if abs(s) >= 32760)
>     near_silent=sum(1 for s in samples if abs(s) < 100)
>     print('channels', w.getnchannels())
>     print('sample_width', width)
>     print('sample_rate', w.getframerate())
>     print('frames', w.getnframes())
>     print('duration_s', round(w.getnframes()/w.getframerate(), 4))
>     print('rms', round(rms, 2))
>     print('normalized_rms', round(rms/32768, 4))
>     print('max_abs', max_abs)
>     print('clipped_samples', clipped)
>     print('near_silent_fraction', round(near_silent/len(samples), 4))"`
>
> </details>
</details>

Looks like nothing is broken.

I checked a sample source file:

`import/LibriSpeech/dev-clean/1272/128104/1272-128104-0000.flac`

Findings:

- `flac -t` says: `ok`
- Source format: FLAC, 16-bit, mono, 16 kHz
- Decoded WAV: valid RIFF PCM, 16-bit mono, 16 kHz
- Duration: ~5.855s
- No clipping: `clipped_samples = 0`
- Normal-ish RMS: `normalized_rms = 0.0619`

So the files are probably just like that. LibriSpeech is audiobook speech, often public-domain readings, chopped into short utterance clips. It can sound:

- mono and narrow-band compared to modern recordings
- a little muffled because it is 16 kHz speech audio
- abruptly cut at starts/ends
- “old book narrator” rather than natural conversation

One extra note: I don’t see `import/converted/` in this checkout yet, so I tested by converting one file into `/tmp`. If your local converted files sound worse than the original `.flac`, rerun with:

```bash
scripts/convert_import_flac_to_wav
```

Now that `flac` is installed, the script will prefer `flac` over `ffmpeg`.
