---
name: rn-niulai-style-image
description: Transform photos, film stills, or new scene descriptions into the observed visual grammar of the 2026 animated film 《牛来》. Use when the user asks for 牛来风格、牛来正片风格、粗粝低模动物 3D、把真人画面改成牛来式动画，or requests iterative comparison against 《牛来》 references. Default to the rough film-3D mode; use the separate ink-poster mode only when the user explicitly asks for the movie poster look.
---

# 牛来风格图片生成

Use the runtime's image-edit tool for an existing still and its image-generation tool only for a new scene. Treat the task as `style-transfer` when an edit target exists and as `stylized-concept` for a new scene.

## Choose the mode

- Default to `niulai-film-3d`: rough low-budget 3D observed in public film frames.
- Use `niulai-poster-ink` only when the user explicitly asks for the water-ink poster. Never mix the poster with the film-frame references.
- Describe the result as matching the *observed public-frame visual grammar*, not as an official art specification.

Read [style-spec.md](references/style-spec.md) before authoring the prompt. Read [evaluation-rubric.md](references/evaluation-rubric.md) before judging any output.

## Prepare inputs

1. Label the edit target as Image 1.
2. Select two style references from `assets/style-reference/` that cover face and body. The image tool accepts at most three inputs total.
3. If a source still is wider than about 1600 px, resize a working copy first. Oversized stills fail.
4. Preserve the target's character count, positions, action, clothing-color roles, key props, and camera crop unless the user asks to change them.
5. Remove source logos, titles, dates, subtitles, and watermarks from the output.
6. If a still is blocked by moderation, stop that still and switch to another adult scene. Do not paraphrase to retry. Prefer stills of adults; skip group shots of children.

## Build the first prompt

Use this structure:

```text
Use case: style-transfer
Asset type: <intended use and aspect>
Input images: Image 1 is the edit target; Images 2-N are style references. Match the look of Images 2-N, not a polished 3D reinterpretation.
Primary request: Rebuild Image 1 as cheap inflatable-costume 3D from an early-2000s amateur animation, while preserving <scene invariants>.
Character translation: Replace people with distinct upright bovine characters whose bodies are sausage-like inflatable suits; preserve identity through role, clothing color, pose, and left-right position rather than human facial likeness.
Style/medium: balloon torsos with almost no waist; oversized mask heads; pale plastic muzzles; small half-lidded eyes; uneven blunt horns; short tube limbs; mitten hands; white sock-hooves; blurry low-resolution fur-color bitmaps stretched across smooth blobby meshes; broad smears, visible seams and scale mismatch; weak contact shadows; primitive flat lighting; stock tutorial trees and painted backdrops; mild cinema-screen capture softness.
Constraints: <invariants>; no text, logo, watermark, subtitle, or date.
Avoid: professional 3D, clean low-poly, cinematic game art, realistic fur, appealing mascot design, Pixar/Disney, global illumination, correct human anatomy under an animal head.
```

Do not ask merely for "low poly." That usually produces clean modern game art and misses the target. The dominant miss is a well-made animal-headed human. If the body has a waist, articulated fingers, groomed fur, or cinematic light, the result is wrong.

## Iterate deliberately

1. Generate one first-pass image.
2. Compare target, style reference, and output with `scripts/.venv/bin/python scripts/make_comparison.py` when local paths are available. Create `scripts/.venv` and install Pillow if that interpreter is missing.
3. Score all six rubric dimensions. Continue if total score is below 27/30, any dimension is below 4, or an automatic-fail condition applies.
4. Change one dominant failure per iteration:
   - live-action leftover -> rebuild the whole frame as 3D, including walls, props, and fire;
   - too polished -> degrade texture scale, seams, lighting coherence, and capture sharpness;
   - too cute -> flatten expressions, shrink eyes, widen muzzle, stiffen pose;
   - mascot-in-a-photo or vinyl suit -> replace with balloon geometry and blurry stretched low-resolution color bitmaps;
   - ragdoll overshoot -> remove button eyes, Frankenstein stitches, and letter prints;
   - reference bleed -> do not use a leopard/print ref unless the target character is spotted;
   - generic low-poly -> replace crisp facets with blobby forms and mismatched pasted textures;
   - material still looks skilled -> remove embossed/procedural detail, flatten to blurry low-resolution bitmaps, broad UV smears, and simple smooth meshes;
   - scene drift -> repeat character count, positions, props, and action invariants;
   - character merging -> name every character by position and action.
5. Re-state all invariants on every edit. Stop only after the threshold passes.

Keep iteration history under `assets/showcases/iterations/` when building or validating this Skill. Save selected finals under `assets/showcases/final/`.

## Deliver

Report:

- final image paths;
- final prompt or prompt template;
- per-image rubric score;
- which iteration changed the result materially;
- built-in image generation as the execution mode.
