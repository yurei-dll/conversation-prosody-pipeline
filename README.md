# Conversation Prosody Pipeline

> A modular middleware pipeline that enriches spoken conversations with conversational metadata before they reach a language model.

## Why?

Modern voice assistants typically reduce speech to plain text before sending it to a language model.

Unfortunately, conversations are much richer than text alone.

Consider these two utterances:

> "Yeah... I'm fine."

The transcript is identical.

The conversation is not.

One speaker may answer instantly with a laugh.

Another may pause for several seconds, speak quietly, and trail off at the end of the sentence.

Humans naturally use these vocal cues to understand one another. Most current LLM pipelines discard them entirely.

This project exists to preserve that information.

---

## Philosophy

Conversation Prosody Pipeline **does not attempt to determine emotions.**

Instead, it extracts measurable conversational features and exposes them as structured metadata.

Examples include:

* Speech rate
* Pause duration
* Speaking energy
* Pitch variability
* Turn-taking statistics
* Response latency
* Hesitation frequency
* Conversation pacing

Rather than outputting:

```json
{
  "emotion": "sad"
}
```

the pipeline prefers outputs like:

```json
{
  "speech_rate_delta": -18.3,
  "pause_delta": 0.42,
  "energy_delta": -0.27,
  "pitch_variability_delta": -0.38
}
```

These are observations, not conclusions.

The downstream language model remains responsible for reasoning about what those observations might mean.

---

## Goals

* Preserve conversational information that transcripts lose.
* Remain model-agnostic.
* Avoid identity recognition or biometric tracking.
* Operate as middleware rather than a replacement for existing LLMs.
* Keep outputs interpretable and measurable.

---

## Architecture

```text
Microphone
      │
      ▼
Speech Recognition
      │
      ▼
Prosody Extraction
      │
      ▼
Conversation State
      │
      ▼
Structured Metadata (JSON)
      │
      ▼
Language Model
      │
      ▼
Response
```

The language model receives both the transcript and conversational metadata.

Example:

```yaml
Transcript:
  "Yeah, that's fine."

Conversation:
  speech_rate_delta: -21%
  pause_duration_delta: +310 ms
  energy_delta: -15%
  interruption_count: 0
```

The pipeline intentionally avoids prescribing an interpretation.

---

## Groundwork

This repository now includes a small Python core for experimenting with the metadata
shape described above:

```text
src/conversation_prosody_pipeline/
  baseline.py   Conversation-local running baselines
  pipeline.py   Turn-by-turn metadata builder
  types.py      Typed feature and metadata objects
```

Run the minimal example:

```bash
scripts/venv run python examples/minimal_turn.py
```

Run tests:

```bash
scripts/venv run python -m unittest discover -s tests
```

Manage a local virtualenv:

```bash
scripts/venv install
source .venv/bin/activate
```

VS Code users can run the same workflow through `Tasks: Run Task`:

```text
venv: create
venv: install
venv: recreate
venv: remove
example: minimal turn
test: unittest
```

See also:

* [Metadata schema](docs/metadata-schema.md)
* [Roadmap](docs/roadmap.md)

---

## Privacy

This project intentionally avoids persistent speaker identification.

Conversation Prosody Pipeline analyzes **how speech changes during the current conversation**, not **who is speaking**.

No voiceprints, biometric databases, or long-term speaker profiles are required.

The goal is to improve conversational context while minimizing privacy concerns.

---

## Design Principles

* Modular over monolithic.
* Observations over assumptions.
* Middleware over end-to-end replacement.
* Privacy by design.
* Model agnostic.

---

## Potential Applications

* Voice assistants
* Accessibility software
* Educational tutors
* Companion AIs
* Customer support
* Research
* Robotics
* Interactive storytelling

Any system that benefits from understanding conversational dynamics without relying solely on transcripts.

---

## Status

🚧 Early concept.

This repository currently focuses on architecture, experimentation, and validating whether structured conversational metadata can improve downstream language model interactions.

Contributions, experiments, and alternative approaches are welcome.
