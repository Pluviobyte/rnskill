# Observed style specification

## `niulai-film-3d` (default)

This mode is derived from currently available public film-frame captures rather than an official production guide.

### Reference files

Pick two or three from `assets/style-reference/`. Cover face, body, and environment when possible.

| File | Use for |
|---|---|
| `niulai-calf-closeup.jpg` | muzzle, flat grass, cylinder trees, screen-capture softness |
| `niulai-herd-dark.jpg` | pale rubber muzzles, half-lidded eyes, uneven horns, cloned-but-not-identical faces |
| `niulai-two-cows.jpg` | two-shot staging, balloon torsos, lollipop trees, painted-on brows |
| `niulai-wide-trio.jpg` | full-body inflatable-suit silhouette, white sock-hooves, painted sunset backdrop |
| `niulai-crowd-field.jpg` | group scale mismatch, tube limbs, floating contact with the ground |
| `niulai-leopard-forest.jpg` | pasted repeating print, mask-like snout, stock cave/rock assets |

### Characters

- Bodies read as cheap inflatable costumes or stuffed balloons standing upright, not as sculpted animals. Torsos are cylindrical sausages with almost no waist, neck, or muscle.
- Heads are oversized and slightly separate from the body, like a mask glued onto a suit. Limbs are short tubes. Hands are mittens. Feet are white sock-hooves.
- Bovine faces use a wide pale plastic muzzle, small nostrils, half-lidded or empty dark eyes, blunt or uneven horns, and stiff painted brows. Expression stays awkward and restrained.
- Multiple characters differ by body color, horn shape, scale, clothing, and position. Do not clone one model perfectly, but they may share the same primitive topology.
- Favor construction mistakes over a clean design language: narrow uneven slit eyes with almost no sclera, a swollen lavender-gray rubber muzzle placed slightly wrong, a floating eyebrow, mismatched horn and ear sizes, a long sagging potato torso, tiny tube arms, peg legs, and clothing painted onto or fused into the body.
- In group scenes, each character should fail differently. Let caps intersect horns, muzzles sit at different heights, arms terminate inconsistently, and costume seams drift. A coherent cast sheet is a failure.

### Geometry and materials

- Prefer blobby inflatable geometry over crisp fashionable faceting.
- Fur is a blurry low-resolution noise or color bitmap pasted onto a balloon, not a groomed or embossed fur system. UVs stretch at joints. Broad smears, seams, and scale mismatch are visible; fine tactile surface detail is a failure.
- Clothing is a low-resolution fabric decal on simple geometry.
- Metal, fire, trees, rocks, and furniture may use unrelated material quality, creating a mild asset-pack mismatch.

### Scene and light

- Environments resemble early 3D tutorials: painted sunset skies, purple cardboard hills, lollipop trees, flat grass planes, stock caves.
- Lighting is frontal or flat with weak contact shadows. Characters often look slightly detached from the ground.
- Isolated colors may be oversaturated while blacks remain muddy.
- Add mild off-screen cinema capture softness and compression only after the model/material look is correct. Do not substitute VHS noise for actual style.

### What misses the style

- Clean modern low-poly, Pixar/Disney faces, large sparkling eyes, appealing mascot design, or any “good 3D character” look.
- Detailed fur, photoreal skin, cinematic fire, volumetric light, strong depth of field, or physically coherent materials.
- Deliberate retro PS1 pixelation without the rounded inflatable suits and coarse pasted textures.
- A polished animal-headed human with correct anatomy. That is the most common failure.
- A live-action room with a mascot head pasted on.
- Shiny vinyl clothing, groomed fluffy fur, button eyes, ragdoll stitches, or letter prints.
- Professionally art-directed "ugly cute" or tasteful indie low-poly. The reference is not intentional design roughness; it must look accidentally inconsistent and technically under-resolved.

## `niulai-poster-ink` (explicit only)

Use white paper, large negative space, black/gray mountain ink washes, deep green water strokes, a tiny red-cloaked bovine figure, vertical calligraphic composition, and restrained mineral pigments. Do not introduce the film's 3D characters or asset-pack environments.
