---
name: heygen-digital-avatar
description: Create and composite HeyGen digital-human videos in the content workspace. Use whenever the user asks for a 数字人, 数字人5, HeyGen, AI 口播人物, 数字人小窗, 圆形头像口播, full-screen digital human, or asks to make a video that uses the existing avatar. Enforce Creator-plan CLI OAuth, the configured Digital Twin, local IndexTTS2 narration, Avatar III for an unspecified digital human but Avatar V whenever the named preset 数字人5 is requested, adaptive face measurement plus the approved human-reviewed visual-centering offset in the headroom_08 circular bottom-left layout unless full-screen is explicitly requested, subtitle-safe placement, credit-aware master reuse, final QC/archive routing, and mandatory pairing with `heygen-avatar-motion` before any motion prompt or paid generation.
---

# HeyGen 数字人口播

Create the avatar layer for a video. Let `ra-video-production-director` own the
whole production, captions, QC, and archive; let this skill own HeyGen auth,
avatar selection, generation, and the approved avatar layout.

Before writing or approving any HeyGen `motion_prompt`, load and apply
`heygen-avatar-motion`. Its motion classes and validation gate are mandatory
unless the user explicitly requests a different action. Never submit a paid
generation while that validation gate fails.

## Fixed profile

Read `references/pluviobyte-profile.json` before building. Treat it as the
machine-readable default. Do not substitute another look from the same avatar
group.

- Authenticate with HeyGen CLI OAuth and Creator subscription credits. Run
  HeyGen commands with `HEYGEN_API_KEY` removed from the child environment so
  a shell variable cannot silently switch billing lanes.
- Use the landscape Digital Twin look the look specified in `references/pluviobyte-profile.json`
  For an unspecified digital human,
  use Avatar III. The exact named preset `数字人5` always means Avatar V and
  counts as an explicit premium-engine request; never resolve it to Avatar III.
  Do not silently
  substitute a legacy portrait look or a generated suit/scene
  look from the same avatar group.
- Use local IndexTTS2 through `tts-skill`, voice
  `pluvio-indextts2-calm-v1`. Never ask HeyGen to synthesize the voice and
  never use MiniMax or another fallback for local production.
- Treat narration approval as a hard paid-generation gate. Generate the full
  IndexTTS2 audition first, give the exact audio file to the user, and wait for
  explicit approval of that version before uploading audio to HeyGen. If the
  user asks for a digital human without mentioning audio approval, remind them
  and stop at the audition stage. Any audio edit invalidates prior approval.
- Default to the approved `headroom_08` circular avatar at the lower-left.
  Only use a full-screen/main-canvas avatar when the user explicitly says
  `全屏数字人` or an equivalent unambiguous instruction.
- Use the compact neutral circle from the profile: 240px portrait content with
  one plain white border and no colored accent ring. Keep its bottom alignment
  stable when changing canvas ratio. Do not restore the older 300px portrait
  or dark-red outer ring unless the user explicitly requests a larger or
  emphasized avatar.
- Do not trust one fixed crop for every generated master. The standard
  compositor must sample five frames, measure the face center with macOS Vision,
  then apply the profile's human-reviewed visual offset. For the approved black-T
  circle, candidate 06 places the portrait 20px below mathematical face center
  and keeps the horizontal offset at 0px. Remeasure the finished circle and
  require the average face center to land within 2px of this offset target. The
  profile crop is a reviewed fallback, not evidence that a new master is centered.
- Keep captions and important content outside the avatar exclusion zone.
- Use Avatar IV/V only after the user requests higher quality, invokes the
  named preset `数字人5`, or Avatar III fails review. State the expected
  credit/cost increase before generation. Because `数字人5` is itself an
  explicit Avatar V instruction, do not ask the user to reconfirm the engine
  after giving the cost notice.

## Workflow

1. Run `env -u HEYGEN_API_KEY heygen auth status`. Require credential type
   `oauth`, billing type `subscription`, and plan `creator`. Stop before a
   paid generation if any condition differs.
2. Generate the complete narration audition with `tts-skill`; require the
   canonical WAV and a `voice_manifest.json` with `used_fallback=false` and
   `minimax_used=false`. Check mixed-language names and technical terms before
   presenting the audition.
3. Give the user the exact audition WAV (and optionally a portable MP3) and
   wait for an explicit confirmation such as “音频确认，可以生成数字人”. Record
   the approved WAV SHA-256 in `media/audio-approval.json`. Do not upload audio,
   build a HeyGen request, or consume credits before this record exists.
4. Recompute the WAV SHA-256 immediately before upload. If it differs from the
   approved hash, invalidate the approval, remind the user, and return to step
   3. A request to “continue”, “directly produce”, or “make the avatar” is not
   audio approval unless the user explicitly confirms the audition itself.
5. Generate production captions from the approved locked audio with
   `ra-audio-to-subtitles`. Require `caption-qc.json` to pass before final
   composition.
6. Upload the approved locked WAV with
   `env -u HEYGEN_API_KEY heygen asset create --file <narration.wav>` and save
   the JSON response in the project. Extract its asset ID without copying
   credentials into files or logs.
7. Use `heygen-avatar-motion` to classify each semantic section, save the exact
   executable motion prompt, and pass its validation gate. Explanatory body
   sections default to hands fully outside the image; visible hand motion is
   reserved for meaningful result or conclusion zones.
8. Resolve the engine from the named preset before building the request. For
   an unspecified digital human, generate one 16:9, 1080p avatar master with
   `fit=contain` and `engine.type=avatar_iii`. For `数字人5`, generate the same
   single master with `engine.type=avatar_v` and pass the premium-engine guard:

   ```bash
   python3 scripts/build_request.py \
     --audio-asset-id '<asset-id>' \
     --title '<project title>' \
     --engine avatar_v \
     --allow-premium-engine \
     --output media/heygen-create-request.json
   env -u HEYGEN_API_KEY heygen video create \
     -d media/heygen-create-request.json --wait \
     > media/heygen-create-response.json
   ```

9. Download the completed master with `heygen video download`. Reuse that
   single master for every requested aspect ratio. Do not spend a second
   generation merely to change crop, circle placement, background, or canvas
   ratio.
10. For the default layout, overlay the master with
   `scripts/compose_circle_avatar.py`. Its default `--center-mode auto` samples
   the current master, applies the measured crop plus the reviewed visual offset,
   then verifies the rendered circle against that target. Archive the generated
   centering report. A Remotion/HyperFrames implementation must reproduce the
   same measurement, visual offset, and 2px gate rather than copying the fallback
   coordinates blindly.
11. For explicit full-screen mode, use the HeyGen master as the main visual and
   skip the circular compositor. Record `layout=fullscreen_explicit` in the
   production note.
12. Verify media streams, duration, representative frames, subtitle clearance,
   hair completeness, reduced headroom, voice provenance, and caption QC.
   Then follow `ra-video-production-director` for final archive delivery.

## Standard compositor

Use this when the base edit is already at the requested output size:

```bash
python3 scripts/compose_circle_avatar.py \
  --base <base-video.mp4> \
  --avatar <heygen-master.mp4> \
  --output <final.mp4> \
  --layout auto \
  --audio-source avatar \
  --centering-report <centering-report.json>
```

`auto` supports the approved 1920x1080 and 1080x1920 layouts. The avatar audio
is authoritative for a narration-only composition. Use `--audio-source base`
only when the locked narration is already present in the base edit. Do not mix
two copies of the narration.

The adaptive face-measurement pass is mandatory for a newly generated master.
`--center-mode profile` uses the reviewed black-T fallback crop only for
diagnosis and still must pass the post-render 2px check against the reviewed
visual-offset target. Use `--crop-x` and `--crop-y` together only for an
explicitly reviewed manual correction. Never regenerate or spend another
HeyGen credit merely to correct local framing.

## Credit guard

Before generation, state how many HeyGen masters will be created. The default
count is one. Layout experiments must use local recomposition and consume zero
additional HeyGen credits. Save request/response JSON and the downloaded master
under the project so retries can detect and reuse completed work.

## Output contract

Keep these artifacts in the engineering project:

- `media/narration.wav` and `media/voice_manifest.json`
- `media/audio-approval.json` containing the explicitly approved audio SHA-256
- `media/heygen-asset-response.json`
- `media/heygen-create-request.json`
- `media/heygen-create-response.json`
- `media/pluviobyte-avatar-master.mp4`
- production caption artifacts and `caption-qc.json`
- final MP4, media probe, contact sheet, and SHA-256 record
- centering report with the sampled frames' measurements, reviewed visual-offset
  target, applied source crop, final average center, per-axis target deviation,
  tolerance, and `status: pass`

Never store OAuth tokens or API keys in project artifacts.
