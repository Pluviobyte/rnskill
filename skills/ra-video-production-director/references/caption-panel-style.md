# Local Translucent Caption Panel (optional legacy preset)

The workspace default now lives in `skill-captions` as `anchor-dark`. Use this
older `local-translucent` treatment only when a handoff contract or the user
explicitly selects it. It remains useful for narrated explainers that need a
light panel over source footage, screenshots, or the V5 grid.

## Visual Contract

- Center the caption in the lower safe zone, normally `bottom: 96px` to
  `120px` on a 1920 x 1080 canvas.
- Shrink-wrap the panel to the rendered text. Cap its width at `1240px`.
- Use 44px mobile-readable type, 1.22 line height, weight 900, and dark ink.
- Use a warm-white translucent fill, 20px radius, a subtle 1px border, and a
  soft shadow.
- Do not use a full-width bar, black outline, colored offset frame, or opaque
  lower-third block.
- Do not use `backdrop-filter`, CSS `filter: blur()`, or per-caption live blur.
  A long video creates one timed element per caption; repeated heavy filters
  can force slow screenshot capture or trigger black-frame failures.

Use this HyperFrames/CSS baseline:

```css
.caption {
  position: absolute;
  left: 50%;
  bottom: 96px;
  z-index: 30;
  width: max-content;
  max-width: 1240px;
  padding: 14px 28px 16px;
  box-sizing: border-box;
  transform: translateX(-50%);
  border: 1px solid rgba(21, 32, 42, 0.10);
  border-radius: 20px;
  background: linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.92),
    rgba(247, 250, 251, 0.84)
  );
  box-shadow: 0 12px 34px rgba(64, 93, 112, 0.14);
  color: #15202a;
  font-size: 44px;
  line-height: 1.22;
  font-weight: 900;
  text-align: center;
  white-space: normal;
}
```

For Xiaohei pages, use `bottom: 120px` when the layout contract has enough
clearance. For full-screen source footage, `bottom: 96px` is the preferred
baseline. Keep the same padding and visual treatment in Remotion or another
renderer.

## Exceptions

Use frameless captions only when the entire caption zone is a controlled,
uniform light field and the project note records why a panel is unnecessary,
or when the user explicitly requests frameless captions. A user-specified
caption style overrides this baseline.

## QC

Before full render, inspect source-footage and light-grid frames plus the
longest caption. Reject the result when the panel:

- spans the frame instead of wrapping the text;
- covers body content, a note card, or the main illustration;
- falls outside the lower safe zone;
- becomes visually heavier than the page title;
- loses readable contrast on either the lightest or darkest sampled frame;
- introduces a heavy-overlay/filter warning in the render checker.
