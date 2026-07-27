---
name: ra-audio-to-subtitles
description: Generate production subtitle artifacts from the final narration audio or final merged video using Volcengine Doubao ASR word timestamps. Use for local IndexTTS2 videos, Xiaohei page videos, talking-head delivery subtitles, SRT/VTT export, or whenever subtitle timing must match the final audio. Do not use script-length interpolation for final deliverables.
---

# 真实时间戳字幕

Use the final audio stream as the only timing source. Never estimate final
subtitle timing from character count, scene duration, TTS segment duration, or
fixed delays.

## Required workflow

1. Finish and concatenate narration first. If the user recorded or merged a
   video, use that final merged media instead.
2. Run `scripts/generate_subtitles.py` against the final media and the exact
   narration script.
3. Inspect phrase segmentation. Keep English product/model tokens intact,
   merge isolated one-word fragments, and place connectors such as `比如说`,
   `但是`, and `只是` with the phrase they introduce.
4. Render captions from `captions.json`; export `captions.srt` for Bilibili,
   YouTube, editing software, and archive.
5. Require `caption-qc.json` to report `status: pass` before final render or
   delivery. The gate includes alignment, overlap, fragments, connector splits,
   caption duration, and reading speed.
6. If ASR fails or alignment coverage is below the gate, stop. A character-
   count estimate may be used only for an explicitly labeled scratch preview.

## Commands

Project with `narration_segments.json`:

```bash
python3 .claude/skills/ra-audio-to-subtitles/scripts/generate_subtitles.py \
  <project>/media/final-voiceover.mp3 \
  --script <project>/narration_segments.json \
  --out-dir <project>/media/captions
```

Recorded or merged video with a Markdown handoff containing `- 口播：` lines:

```bash
python3 .claude/skills/ra-audio-to-subtitles/scripts/generate_subtitles.py \
  <project>/merged.mp4 \
  --script <project>/handoff.md \
  --out-dir <project>/media/captions
```

Health check:

```bash
python3 .claude/skills/ra-audio-to-subtitles/scripts/generate_subtitles.py --doctor
```

Offline regression test with an existing Volcengine response:

```bash
python3 .claude/skills/ra-audio-to-subtitles/scripts/generate_subtitles.py \
  <audio> --script <script> --asr-result <volcengine-result.json> \
  --out-dir <output>
```

## Output contract

The output directory must contain:

- `asr-result.json`: raw Volcengine response
- `captions_words.json`: word/character timestamps and detected gaps
- `captions.json`: phrase captions consumed by HyperFrames or Remotion
- `captions.srt` and `captions.vtt`: portable subtitle files
- `caption-qc.json`: alignment coverage and timing validation

Read [references/artifact-contract.md](references/artifact-contract.md) before
integrating another renderer or delivery checker.

## Hard rules

- Transcribe the exact final audio used by the MP4. Do not transcribe an earlier
  segment, draft voice, or a differently trimmed file.
- Use the original narration text for display and ASR only for timing. This
  preserves names, English terms, punctuation, and intentional wording.
- Align the original script to ASR tokens before grouping phrases. Do not scale
  boundaries by total character count.
- Phrase captions remain the default. Word timestamps are the timing substrate,
  not a requirement to show karaoke-style one-character captions.
- Preserve meaningful spaces inside English names such as `Claude Max`; never
  split an ASCII product/model token across captions.
- Reject captions shorter than 0.5 seconds, isolated fragments, split discourse
  connectors, and reading speeds above 12 units/s. Treat speeds above 9 units/s
  as a review warning.
- Keep one canonical caption timeline. Scene changes, keyword reveals, and
  component cues should look up caption text or timestamps from that timeline.
- `VOLCENGINE_API_KEY` comes from the workspace root `.env` or the environment.
  Never print or copy it into an artifact.
- Default resource ID is `volc.seedasr.auc`; override only with
  `VOLCENGINE_RESOURCE_ID` when the account uses a different enabled resource.
- Final delivery requires alignment coverage at least 0.90 unless a stricter
  project contract is set. Lower coverage is a failure, not a warning.
