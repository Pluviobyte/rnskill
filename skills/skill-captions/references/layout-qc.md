# Layout QC

Inspect at least the first cue, the longest cue, a middle cue, and a late cue.

Require:

- identical bottom anchor across all samples;
- one- and two-line panels grow upward from the same baseline;
- panel wraps the text instead of becoming a full-width bar;
- no text stroke, text shadow, or large panel shadow in `anchor-dark`;
- dark ink, a warm-white translucent surface, a fine border, and only a subtle
  soft shadow in `anchor-light`;
- legible contrast on both the lightest and darkest sampled backgrounds;
- no overlap with titles, UI, faces, illustrations, or lower-left avatar/PiP;
- no clipped glyphs, English token splits, or more than two lines;
- native-resolution drawing at 4K;
- portable SRT/VTT retained beside the project;
- `caption-render-qc.json` reports `pass`.

If a lower-left avatar occupies the caption zone, keep the subtitle horizontally
centered only when there is adequate clearance. Otherwise shorten the line,
raise the shared bottom anchor for the entire affected section, or change the
page layout. Do not move individual cues independently.
