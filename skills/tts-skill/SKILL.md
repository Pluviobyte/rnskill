---
name: tts-skill
description: Generate cloned narration for the content workspace. Use local IndexTTS2 with the canonical lossless Pluviobyte reference for every local video, voice audition, digital-human narration, and subtitle-ready audio render. Preserve MiniMax only for public-facing articles or tutorials that teach users to connect through the relay service; never use MiniMax for local video production.
---

# TTS Skill

Route every request into exactly one lane.

## Hard Routing Rules

1. For local video production, use local IndexTTS2 only. Do not call MiniMax,
   even when MiniMax credentials exist in `.env`.
2. Use voice id `pluvio-indextts2-calm-v1` and the canonical lossless WAV in
   `automation/config/tts-routing.json`. Never use an MP3 as the speaker
   reference and never replace the canonical reference with the latest output;
   that would accumulate cloning drift.
3. Generate the locked narration as lossless WAV. MP3 may be emitted only as a
   portable audition copy, never as the source for another clone or for final
   subtitle timing.
4. Apply the `default_delivery.playback_speed` declared in
   `automation/config/tts-routing.json` to every audition and final WAV. The
   production default is `1.12x`, implemented with FFmpeg `atempo` so pitch is
   preserved. Record the effective multiplier in `voice_manifest.json`.
5. Do not silently fall back to macOS `say`, browser speech, MiniMax, or another
   generic/cloud voice. If IndexTTS2, its model weights, Apple MPS/CPU, or the
   canonical reference is unavailable, repair the local lane or stop.
6. Every final narration render must leave `voice_manifest.json` with provider,
   voice id, model, canonical reference path and SHA-256, segment contract,
   output path, and `used_fallback=false`.
7. TTS segment durations are planning metadata only. Run
   `ra-audio-to-subtitles` against the exact concatenated lossless narration and
   use its word timestamps for final captions.
8. For digital-human production, treat the full narration as an audition until
   the user explicitly approves that exact audio version. Do not describe an
   unapproved audition as locked or forward it to HeyGen.
9. Before every local audition or final render, enforce
   `references/pronunciation-lexicon.json`. A user-approved pronunciation in
   that file overrides generic phonetic heuristics. Keep the display spelling
   separate from TTS text when needed, and stop rather than render a forbidden
   spelling.

## Local Video Lane: IndexTTS2

Read the machine-readable route from:

`automation/config/tts-routing.json`

Generate a narration from a JSONL segment contract with:

```bash
python3 .claude/skills/tts-skill/scripts/generate_indextts2_narration.py \
  --batch-file <segments.jsonl> \
  --output <final-narration.wav> \
  --manifest <voice_manifest.json>
```

Each non-empty JSONL line must follow the official IndexTTS2 batch contract and
contain `text`; it may also contain `emotion_vector`, `emotion_weight`, and
`silence_after_ms`. Default to a calm delivery. Add stronger emotion only when
the user explicitly asks for it.

Run `--dry-run` before a new contract or after changing the local model setup.
The helper verifies that the canonical speaker reference is a lossless PCM WAV,
invokes the official local IndexTTS2 CLI, normalizes the result, and writes the
manifest. Keep the raw WAV beside the normalized WAV for auditability.

For mixed Chinese/English scripts, inspect model names, brands, abbreviations,
and numbers before the full render. Load
`references/pronunciation-lexicon.json` first. Entries there are approved
production contracts: use their `tts` value exactly and reject every
`forbidden_tts` form. In particular, keep `Codex` as the raw English token;
never transliterate it as “扣代克斯”, “扣戴克斯”, or “扣德克斯”. For a term
that is not yet in the lexicon, audition alternatives while keeping canonical
spelling in the display script and final captions. After the user chooses,
record that decision in the lexicon before the full render.

## Public Article Lane: MiniMax Relay

MiniMax is retained only as the public solution used in articles, tutorials,
course examples, and relay-station onboarding. It is not a local production
provider. When this lane is requested, read
`references/minimax-relay-article.md` and use `assets/minimax_tts.py` only for
the article/demo example.

## QC

Before using narration in a final video:

- confirm `provider` is `IndexTTS2`/`indextts2-local`
- confirm `voice_id` is `pluvio-indextts2-calm-v1`
- confirm the reference SHA-256 matches the routing config
- confirm the recommended output is PCM WAV and decodes successfully
- confirm `playback_speed` is `1.12` unless the production contract explicitly
  overrides the workspace default
- confirm `used_fallback=false` and no segment provider is MiniMax
- confirm the pronunciation contract is present in `voice_manifest.json` and
  the approved mixed-language terms were used
- generate captions from that exact WAV and require `caption-qc.json` PASS
- for a digital human, require explicit user approval of the exact audition WAV
  before any paid avatar generation; changing the audio invalidates approval
