# Style contract and no-reference prompt

## Fixed visual DNA

- Canvas: `5:2`, normally `3000 × 1200`.
- Background: warm ivory `#F4F1EA`, subtle paper softness.
- Layout: typography on the left; compact diagram on the far right.
- Grid: thin, low-contrast neutral grid only behind artwork.
- Lines: charcoal `#44433F`, thin dashed strokes with rounded corners.
- Accent: muted coral `#D97A57`, limited to one outline/signal.
- Objects: empty rounded nodes, routed connectors, one floating interface/card object.
- Hierarchy: Chinese headline first, Latin label second, illustration third.

## Adaptive layout

Estimate the width of the final text before generating:

- Short Chinese title (`≤12` full-width glyphs): reserve `60%` for text; require the generated base to stay blank through `68%`; artwork begins at `70%`.
- Medium title (`13–17` glyphs): reserve `64%`; keep the base blank through `70%`; artwork begins at `72%`.
- Long title: use one intentional break, reserve `66%`; keep the base blank through `72%`; artwork begins at `74%`.

Treat the extra blank band as a safety buffer against ImageGen drift. The artwork must stay between `artwork_start` and `96%` of canvas width. Reject any base with a node or connector left of the blank boundary.

## Choose a new topology

Select one per cover from semantics:

- Automation/workflow: compact loop with 3–4 nodes.
- Tool stack/integration: offset chain feeding one center card.
- Growth/distribution: one input branching into 2–3 routes, then reconverging.
- Comparison/decision: split path, decision diamond, chosen output.
- Content production: capture → transform → compose → publish, expressed without text.
- Learning/research: orbiting note cards around one evidence card.

Change the topology, node geometry, path routing, card angle, and accent position for each new cover.

## Built-in ImageGen prompt template

Replace braces, then call ImageGen without any image inputs:

```text
Use case: productivity-visual
Asset type: ultra-wide 5:2 editorial technology cover background
Primary request: Generate a completely original warm-ivory editorial cover background for the theme "{theme}". Keep every pixel in the entire left {blank_boundary_percent}% visually empty except for the warm-ivory paper background: no grid, no line, no node, no connector, no card, no decoration. Create a fresh compact abstract workflow illustration only on the far right.
Subject: {topology_description}. Use thin charcoal dashed connectors, empty rounded nodes, one floating minimal interface/card object, and one restrained muted-coral outline or signal. Express the idea visually without labels.
Style/medium: premium editorial infographic, vector-like line art, modern AI research publication, understated and elegant
Composition/framing: exact 5:2 ultra-wide banner; a hard empty-zone boundary at {blank_boundary_percent}% canvas width; artwork contained from {artwork_start_percent}% to 96%; centered vertically; fully visible; generous margins; the illustration must be small and yield space to the title
Color palette: warm ivory #F4F1EA, charcoal #44433F, faint grid #D9D6CF, muted coral #D97A57
Text: none
Constraints: no reference image; newly invent this diagram; no words, letters, numbers, logos, watermark, people, or photography; grid only behind the right-side artwork; absolutely no visible mark may cross left of the hard empty-zone boundary; no clipped nodes
Avoid: pseudo-text, reused-looking composition, oversized diagram, neon, glossy 3D, heavy shadows, dense UI, clutter
```

Never include `Input images:` in this prompt. Never pass `referenced_image_paths` or `num_last_images_to_include`.
