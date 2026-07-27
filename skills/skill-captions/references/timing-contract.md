# Timing contract

Read the canonical artifacts from `ra-audio-to-subtitles`:

- `captions_words.json`
- `captions.json`
- `captions.srt`
- `captions.vtt`
- `caption-qc.json`

Consume each `captions.json` cue as:

```json
{"start": 1.24, "end": 3.68, "text": "这是一句字幕。"}
```

Use `start` and `end` unchanged. A final burn requires:

- `caption-qc.json.status` equal to `pass`;
- `timing_source` equal to `volcengine-word-timestamps`;
- alignment coverage at least 0.90;
- no overlaps or failed readability gates.

An excluded range removes cues that overlap an interval which already contains
burned captions. Do not shift later cues after exclusion.
