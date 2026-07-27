# Video Production Routing

Use the narrowest skill that fits. Do not stack multiple creation workflows
unless the task truly crosses boundaries.

| User intent | Primary route | Notes |
| --- | --- | --- |
| Final narration/merged video -> SRT/VTT/timeline | `ra-audio-to-subtitles` | Canonical production timing from Volcengine word timestamps. |
| Existing talking-head footage + designed captions | `embedded-captions` | For caption styling, matting, and burn-in after timing. |
| Existing footage + graphic cards/callouts | `graphic-overlays` | For designed overlays, not plain subtitles. |
| Product / SaaS launch / feature reveal | `product-launch-video` | Use product visuals and marketing structure. |
| General website showcase | `website-to-video` | Use when it is not a launch/promo. |
| Topic explainer with generated narration | `faceless-explainer` | For arbitrary text/topic to narrated video. |
| Longer custom multi-scene piece | `general-video` | Fallback when no specialized lane fits. |
| Short kinetic type/logo/stat/overlay | `motion-graphics` | Usually under 10s, no narration arc. |
| HyperFrames implementation details | `hyperframes`, `hyperframes-cli` | Use after route is chosen. |
| Remotion mentioned as target tool | `remotion:remotion-best-practices` | Use only if building in Remotion. |
| Remotion project -> HyperFrames | `remotion-to-hyperframes` | Only explicit port/migration requests. |
| Download source video/audio | `ra-video-download` | Use before analysis or transcription. |
| Extract source-video spoken content | `ra-逐字稿提取skill` | Transcript-only; not the production subtitle clock. |
| TTS / voice clone | `tts-skill` or `hyperframes-media` | Pick based on the selected workflow. |

If two routes seem plausible, pick the one closest to the user's artifact:
existing footage beats generated video; reference-video replication beats style
inspiration; captions beat overlays when the user only asked for subtitles.

For every narrated final, `ra-audio-to-subtitles` owns the timing layer even
when another skill owns caption styling or burn-in.
