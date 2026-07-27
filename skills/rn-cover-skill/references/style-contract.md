# Style contract and reference-free construction

## Fixed identity

Keep only these invariants:

- Canvas: `5:2`, normally `3000 × 1200`.
- Background: exact flat warm white `#FAF9F5`.
- Foreground: near-black typography and restrained charcoal linework.
- Accent: one small muted-coral focal signal.
- Structure: strong left typography, an original conceptual visual on the right, and generous negative space.
- Spatial texture: a faint square drafting grid across the right visual field.
- Decoration: no underline, divider, rule, or decorative line beneath the text.

Never accept a model-generated background as final. Generate only isolated right-side artwork; let `compose_cover.py` draw the fixed background, controlled grid, placement, and real text.

## Aesthetic relationships

Use relationships rather than fixed coordinates:

- Start with a clear asymmetry: typography anchors the left; the diagram creates counterweight on the right.
- Let the headline determine the split. Short copy permits a larger visual closer to the center; long Chinese copy earns more horizontal room and pushes the visual right.
- Keep at least one comfortable headline-sized gap between text and actual diagram marks.
- Align the two sides by optical center, not merely by bounding-box center.
- Let the diagram feel substantial enough to be a second subject, but never let it overpower the headline.
- Let the grid begin in the transition zone or farther right according to the text width. It should remain faintly legible at thumbnail size, then recede behind the diagram at full size.
- Use negative space as active rhythm. Avoid both a cramped center seam and an empty gulf between the two sides.

The reference image suggests a useful family resemblance—editorial serif, large type, faint geometry, delicate paths—but its exact node count, loop, labels, line breaks, grid origin, and distances are not a template.

## Flexible geometry ranges

Use these only as starting ranges:

- Left text origin: roughly `5–8%` of canvas width.
- Grid transition: roughly `35–58%`, moving right as the headline grows.
- Right artwork start: roughly `48–72%`, depending on text length.
- Right artwork height: roughly `55–88%`, depending on the visual family.
- Outer breathing room: visually consistent on all sides, without forcing equal numeric margins.

Move outside these ranges when the title or concept benefits and the hierarchy remains intact.

The grid is part of the visual identity, but its geometry is not locked: vary its starting edge, cell size, and contrast to suit the composition. Omit it only when the user explicitly requests a clean background.

## Typography

- Latin headline: bold editorial serif with tight tracking and deliberate line breaks.
- Optional Latin emphasis: italicize one coherent phrase or line.
- Chinese or mixed headline: heavy sans with strong stroke mass and clean Latin glyphs.
- Optional label: smaller and quieter than the headline.
- Optional subtitle: bold italic editorial serif with relaxed leading.
- Vertically center the complete left text group after calculating its real height.
- Prefer an expressive silhouette—one broad line, a strong two-line block, or a smaller label over a large Chinese line—rather than mechanical wrapping.

Font sizes are outcomes of hierarchy and available width, not identity constants. At thumbnail scale, the headline must remain the first thing read.

## Original visual families

Choose freely from the topic:

- Workflow, orchestration, routed systems
- Tool integration or modular stacks
- Growth, distribution, convergence
- Comparison, choice, verification
- Charts, curves, thresholds, progress
- Architecture, layers, orbits, dependencies
- Content production or transformation
- Research, evidence, notes, learning
- A new abstract metaphor invented for the specific title

Vary the visual family, silhouette, topology, object count, route, central object, and coral signal placement. A new cover should not look like a previous diagram with the title swapped.

## ImageGen construction

Generate an isolated diagram on a removable chroma background. Keep the prompt descriptive rather than numerically prescriptive:

```text
Use case: productivity-visual
Asset type: isolated editorial diagram asset for the right side of a 5:2 cover
Primary request: Generate a completely original conceptual diagram for "{theme}". Create only the diagram object; background, grid, and typography will be composed separately.
Scene/backdrop: perfectly flat solid #00FF00 chroma-key background; no gradient, texture, grid, floor, shadow, or lighting variation
Subject: {fresh_visual_concept}. Use delicate charcoal geometry, restrained dashed routes where useful, minimal interface or diagram objects, and one small muted-coral focal signal. Express the idea without labels.
Style/medium: sophisticated editorial infographic, modern AI research publication, understated vector-like line art
Composition/framing: coherent self-contained silhouette; fully visible; tight but comfortable crop; balanced optical center; no unnecessary empty padding
Color palette: charcoal, near-black, muted coral, optional #FAF9F5 card surfaces
Text: none
Constraints: create from scratch with no reference image; no words, letters, numbers, logos, watermark, people, photography, canvas background, or grid; keep subject colors distinct from #00FF00
Avoid: copied-looking topology, chunky generic flowchart icons, pseudo-text, neon, glossy 3D, heavy shadows, dense UI, clutter
```

Never include `Input images:`. Never pass `referenced_image_paths` or `num_last_images_to_include`.

After generation:

1. Remove the chroma key.
2. Reject green fringe, pseudo-text, clipped geometry, excessive padding, or a generic copied-looking layout.
3. Let the compositor trim transparent margins and place the effective visual bounds.
4. Adjust grid, artwork start, and artwork height by optical judgment.
