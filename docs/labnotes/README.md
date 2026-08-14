# Experiment labnotes

Labnotes form the chronological experimental record for Conversation Prosody
Pipeline. Each note has a stable sequential identifier and a descriptive slug:

```text
labnote-NNN-short-description.md
```

Assign the next unused number when adding a note. Numbers describe publication order,
not success or importance, and are never reused. Keep negative, inconclusive,
aborted, and design-only work in the record when it informs later experiments; state
the outcome clearly inside the note.

## Index

| ID | Run date | Question | Status | Relationship |
|---|---|---|---|---|
| [001](labnote-001-selected-poems-real-media.md) | 2026-06-27 | Do file and simulated-stream ingestion produce consistent metadata from real spoken audio? | Successful | Initial real-media ingest check |
| [002](labnote-002-shakespeare-monologue-downstream-response.md) | 2026-07-01 | Do delivery cues improve or meaningfully change an LLM's conversational response? | Failed to demonstrate improvement | Follows 001; moves from ingest consistency to downstream usefulness |
| [003](labnote-003-amy-lm-synthetic-prosody-downstream-response.md) | 2026-07-01 | Do matched cues improve responses to flattened conversational text over text-only and shuffled controls? | Negative/inconclusive | Follows 002; uses short synthetic conversational utterances and stronger controls |
| [004](labnote-004-context-conditioned-prosody-ir.md) | 2026-08-13 | Can local models infer intended prosody from discourse context, and can Kokoro render the inferred structure? | Inference and oracle synthesis complete; listener evaluation pending | Holds target wording fixed; evaluates inference and synthesis separately |
