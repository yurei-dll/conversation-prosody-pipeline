# Labnote 004 experiment runner

**Status:** Inference and oracle synthesis complete; blinded listener evaluation pending.

This directory contains the tracked, reproducible inputs and runners for the
same-text/different-context prosody experiment. Generated outputs belong under the
ignored `artifacts/` directory and are not source-distribution files.

The experiment is split into independently resumable phases:

1. `inference` asks local language models to infer a bounded prosody IR from discourse
   context while the literal target utterance stays fixed.
2. `calibration` tests which IR-to-Kokoro compilation operations produce measurable
   acoustic changes.
3. `oracle-synthesis` renders gold IR independently of model inference.
4. `end-to-end` renders selected model predictions after the oracle compiler passes
   calibration.

Run the inference phase:

```bash
python experiments/labnote_004/run_inference.py \
  --run-dir artifacts/labnote-004/inference
```

The runner uses only the Python standard library and a loopback Ollama endpoint. It
stores every attempt and accepted result in SQLite, writes immutable corpus and run
manifests, and safely resumes completed work. `export_results.py` creates JSONL and
CSV summaries from the ledger without modifying it.

The default matrix is deliberately large enough to estimate variance:

- 132 context-target cases (66 fixed utterances, two readings each);
- `qwen3:8b`, `gemma3:12b`, and `llama3.2`;
- three prompt formulations; and
- five generation seeds.

This yields 5,940 inference trials. Models are processed in groups to avoid repeated
GPU model swaps.

The oracle synthesis matrix contains 132 cases × three conditions × two voices = 792
clips. The conditions are neutral text, gold IR compilation, and the sibling reading's
swapped IR. The initial compiler uses Kokoro token timestamps for localized focus gain,
global relative speed for pace, and punctuation for continuation boundaries. Immutable
base waveforms are cached by text, voice, and speed and reused across conditions. It
records but deliberately does not translate categorical delivery labels into
unsupported emotion controls.

## Prosody IR

The first experiment uses a small, closed schema:

```json
{
  "focus_span": "she",
  "focus_strength": 2,
  "boundary": "final",
  "delivery": "corrective",
  "pace": "normal"
}
```

Allowed values are enforced by the runner. The schema intentionally avoids emotion
diagnosis and other claims that cannot be read directly from the authored discourse
condition.

## Service execution

On the experiment host, run this through a native systemd user service rather than an
interactive SSH process. The service may be restarted safely with the same `--run-dir`.
The experiment itself requires no network access after models and dependencies are
installed.

Prepare and fingerprint Kokoro once before starting synthesis:

```bash
.venv-kokoro/bin/python experiments/labnote_004/prepare_kokoro.py
```

This downloads the official `hexgrad/Kokoro-82M` assets as needed, generates a short
sample with each selected voice, and records resolved package versions plus hashes of
the cached model files.
