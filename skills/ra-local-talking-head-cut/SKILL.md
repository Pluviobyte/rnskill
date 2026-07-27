---
name: ra-local-talking-head-cut
description: Produce a polished local talking-head or narrated screen-recording rough cut without a cloud editor. Use when Codex must clean Chinese or mixed Chinese-English speech, correct product terminology before semantic editing, compress pauses without making speech breathless, preserve source resolution and frame rate, normalize dialogue loudness, generate final-audio subtitle artifacts, or benchmark local output against ChatCut/video-use/chengfeng/AI剪口播.
---

# 本地口播精剪

Deliver a reproducible local workflow, not an editing product. Keep upstream
skills untouched and write every job under the source project's engineering
directory.

## Required workflow

1. Probe the source. Preserve width, height, and frame rate unless the user
   explicitly requests a delivery conversion.
2. Transcribe with the installed `video-use/helpers/transcribe.py` using
   `volc.seedasr.auc` and word timestamps. Reuse its cached normalized JSON.
3. Run `scripts/prepare_transcript.py` with
   `references/default-glossary.json`. It must create `review.md`,
   `precut-review.srt`, `corrected-script.md`, `uncertain-terms.md`, and
   `subtitle-approval.json`.
4. Give the user the source video plus `precut-review.srt` and the readable
   review. Correct only well-supported terminology. Never guess an uncertain
   model or product name. **Stop here and wait for explicit user approval.**
   Do not build an EDL or render a cut while approval is pending.
5. Resolve uncertain terms by adding confirmed mappings to a job-local copy of
   the glossary, then rerun preparation so both the script and pre-cut SRT are
   regenerated together. Preparation always resets approval. After the user
   confirms the regenerated SRT, set `subtitle-approval.json` to
   `approved: true`, record the confirmation time, and leave
   `unresolved_terms` empty. Never keep approval across regeneration.
6. Write optional `decisions.json` for semantic deletions. Delete repeated
   starts and failed takes before their later complete version; preserve unique
   meaning. Use normalized word indexes only inside artifacts, never in the
   user-facing report.
7. Run `scripts/build_edl.py` with the approval file. The script must refuse to
   continue unless subtitles are approved and all uncertainty is resolved. Its
   default pacing keeps pauses up to 550 ms,
   compresses longer pauses to 380-450 ms, removes only unambiguous `呃/额`, and
   pads source head/tail. Do not replace this with blanket deletion of every
   pause above 200 ms.
8. Run `scripts/render_cut.py` without transitions to create a hard-cut preview.
   It preserves source dimensions/fps, applies 15 ms audio fades at every cut,
   uses light dialogue cleanup, and performs two-pass loudness normalization to
   -16 LUFS / -1.5 dBTP. Stronger denoise or gates are candidates, not defaults:
   reject a candidate when the same ASR alignment test drops by more than 0.01
   or falls below 0.90.
9. Run `scripts/analyze_visual_cuts.py` on the hard-cut preview. Inspect its
   contact sheet and use only its recommended 80-120 ms transitions, capped at
   three per video. Rerender with `--transitions` only when a valid semantic cut
   also has a large visual discontinuity. Do not add blanket transitions.
10. Run `scripts/qc.py` against the chosen clean final MP4 and pass it the same
    transition JSON when transitions were used. Require matching dimensions/fps,
    valid audio/video, expected duration, and loudness within the gate. Inspect
    both the general and transition contact sheets.
11. Run `scripts/generate_final_subtitles.py` against the exact final MP4 and
    approved `corrected-script.md`. It delegates timing/alignment to
    `ra-audio-to-subtitles` and refuses delivery unless `caption-qc.json` is
    PASS. ASR is the timing source; approved script text is the display source.
    Never reuse `precut-review.srt` after timeline edits.
12. When the deliverable needs visible subtitles, run `skill-captions` with
    the final `captions.json` and PASS `caption-qc.json`. Use `anchor-dark`
    unless the contract selects another style. Preview a representative frame,
    burn the derivative, and require `caption-render-qc.json` to pass. Keep the
    clean rough cut and portable SRT.

## Commands

```bash
SKILL_DIR="<this skill directory>"
JOB="<engineering job directory>"
WORDS="$JOB/transcripts/<source-name>.json"

python3 "$SKILL_DIR/scripts/prepare_transcript.py" \
  "$WORDS" --out-dir "$JOB/transcript-review" \
  --glossary "$SKILL_DIR/references/default-glossary.json"

python3 "$SKILL_DIR/scripts/build_edl.py" \
  <source.mp4> "$WORDS" --out "$JOB/edl.json" \
  --approval "$JOB/transcript-review/subtitle-approval.json" \
  --decisions "$JOB/decisions.json"

python3 "$SKILL_DIR/scripts/render_cut.py" \
  "$JOB/edl.json" --out "$JOB/local-hard-cut-preview.mp4"

CODEX_PY="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
"$CODEX_PY" "$SKILL_DIR/scripts/analyze_visual_cuts.py" \
  "$JOB/local-hard-cut-preview.mp4" --edl "$JOB/edl.json" \
  --out-dir "$JOB/visual-cut-qc"

python3 "$SKILL_DIR/scripts/render_cut.py" \
  "$JOB/edl.json" --out "$JOB/local-benchmark.mp4" \
  --transitions "$JOB/visual-cut-qc/visual-cut-qc.json"

python3 "$SKILL_DIR/scripts/qc.py" \
  <source.mp4> "$JOB/local-benchmark.mp4" \
  --edl "$JOB/edl.json" \
  --transitions "$JOB/visual-cut-qc/visual-cut-qc.json" \
  --out-dir "$JOB/qc"

python3 "$SKILL_DIR/scripts/generate_final_subtitles.py" \
  "$JOB/local-benchmark.mp4" \
  --script "$JOB/transcript-review/corrected-script.md" \
  --approval "$JOB/transcript-review/subtitle-approval.json" \
  --out-dir "$JOB/captions"

"$CODEX_PY" ".claude/skills/skill-captions/scripts/render_captions.py" \
  "$JOB/local-benchmark.mp4" "$JOB/captions/captions.json" \
  --qc "$JOB/captions/caption-qc.json" --style anchor-dark \
  --out "$JOB/local-benchmark-captioned.mp4" \
  --preview "$JOB/qc/caption-preview.png" --preview-at 15

```

Omit `--decisions` when no semantic repeats or failed takes exist.

## Decision gates

- Prefer missed filler over lost meaning.
- Treat transcript correction and playback deletion as separate operations.
- Do not create an EDL while subtitle approval is false or unresolved terms
  remain.
- Treat `precut-review.srt` as source-timeline review material only.
- Do not burn captions while `caption-qc.json` is absent or not PASS.
- Do not accept audio cleanup whose same-input ASR coverage regresses by more
  than one percentage point, even when it sounds superficially quieter.
- Do not add transitions to every cut; a transition requires both a valid
  semantic boundary and measured visual discontinuity.
- Do not call a rough-cut subtitle timeline production-ready.
- Do not deliver when `cut-qc.json` reports `fail`.
- Keep intermediates in `01-内容生产/视频工作台/制作中/<日期-主题>/`; archive only the user-approved
  final under `视频工作台/已制作/月上旬或月下旬/日期-主题/`.

Read [references/artifact-contract.md](references/artifact-contract.md) when
integrating another renderer or modifying artifact schemas.
