# Artifact contract

## Inputs

- Source media: MP4/MOV with one audible dialogue stream.
- Normalized ASR JSON: top-level `words`; each entry has `text`, `start`, `end`
  and `type=word|spacing`. The equivalent `isGap` schema is also accepted.
- Optional `decisions.json`:

```json
{
  "delete_word_indices": [12, 13],
  "notes": ["Delete failed first start; later complete version remains"]
}
```

## Outputs

- `transcript-review/review.md`: raw and glossary-corrected phrase view.
- `transcript-review/precut-review.srt`: source-timeline caption preview for
  user confirmation before any cut.
- `transcript-review/corrected-script.md`: display-text source for final subtitle
  alignment.
- `transcript-review/uncertain-terms.md`: unresolved proper-name gate.
- `transcript-review/subtitle-approval.json`: mandatory approval state. EDL
  generation is forbidden until `approved=true` and `unresolved_terms=[]`.
- `edl.json`: source keep ranges and pacing policy.
- `local-hard-cut-preview.mp4`: source-size/source-fps diagnostic render used to
  inspect hard-cut visual discontinuities before the final render.
- `visual-cut-qc/visual-cut-qc.json`: every cut boundary's measured pixel
  discontinuity plus at most three recommended 80-120 ms transitions.
- `visual-cut-qc/visual-cut-contact-sheet.png`: before/after evidence for cut
  review.
- `local-benchmark.mp4`: chosen clean rough cut with normalized dialogue and
  only the approved selective transitions.
- `qc/cut-qc.json`: hard checks and measured media properties.
- `qc/contact-sheet.png`: representative visual proof.
- `captions/`: final-media `captions_words.json`, `captions.json`, SRT, VTT and
  PASS `caption-qc.json` generated after the cut.
- `*-captioned.mp4`: optional burned-caption derivative generated only from
  the QC-passed final SRT. Preserve the clean rough cut and portable captions.

## Pass criteria

- Video dimensions and rational frame rate equal the source.
- Output has video and audio streams.
- Output duration is within one second of EDL duration.
- When transitions are used, expected duration subtracts their total overlap;
  `cut-qc.json` records transition count and overlap.
- Integrated loudness is between -17.5 and -14.5 LUFS.
- True peak does not exceed -0.5 dBFS.
- Selective transitions are allowed only at measured visual discontinuities,
  last 80-120 ms, and total no more than three per video.
- Stronger denoise/gate candidates must keep ASR coverage at least 0.90 and may
  not regress more than 0.01 against the light-cleanup baseline on the same
  timeline and script.
- Production subtitles additionally require `ra-audio-to-subtitles` coverage
  at least 0.90, no isolated fragments or split discourse connectors, maximum
  reading speed at most 12 units/s, and `caption-qc.json` status `pass`.
- Pre-cut subtitle approval never substitutes for post-cut caption QC.
