# Evaluation rubric

Score each dimension from 0 to 5. Pass only when the total is at least 27/30 and no dimension is below 4.

| Dimension | 0-2 | 3 | 4-5 |
|---|---|---|---|
| Character mass | human, cute mascot, or clean game model | bovine and low-detail but proportionally safe | round heavy torso, oversized head, short stiff limbs, awkward readable silhouette |
| Face | polished or expressive cartoon face | wide muzzle and reduced eye detail | rubbery oversized muzzle, half-lidded eyes, uneven features, stiff expression |
| Material | realistic fur or coherent clean shaders | coarse texture present | obvious repetition, stretching, scale mismatch, seams, pasted-on fabric |
| Scene | cinematic or photoreal environment | simplified background | stock/programmatic assets, uneven scale, mild material mismatch |
| Lighting/capture | cinematic lighting, sharp commercial render | flatter light and some softness | weak shadows, muddy depth, isolated saturation, mild screen-capture compression |
| Overall + invariants | source scene lost or generic low-poly | recognizable scene and partial match | clearly reads as observed 《牛来》 film-frame grammar while preserving count, action, props, and crop |

Record scores in this order: `mass / face / material / scene / light / overall = total`.

Do not inflate scores because the result is intentionally ugly. The target is a specific combination of awkward geometry, coarse materials, primitive staging, and preserved source semantics.

Automatic fail if the result still reads as tasteful, coherent, professionally art-directed low-poly illustration. Also fail if faces, bodies, costumes, lighting, and environment share one clean design system instead of looking inconsistently assembled by a beginner.
