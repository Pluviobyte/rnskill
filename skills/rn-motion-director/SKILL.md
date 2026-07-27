---
name: rn-motion-director
description: >
  Motion-first AI video director for topic-to-video creation. Use when the user
  gives a theme, idea, article, script, or brief and wants AI to freely create a
  real animated video instead of a PPT/slideshow-style explainer; when deciding
  visual metaphors, motion grammar, scene beats, component choices, generated
  image needs, HyperFrames/Remotion implementation strategy, and anti-PPT QC.
---

# AI 动效导演元 Skill

## Role

Act as the director layer that turns a topic into a motion-first video concept
and controls execution until the result behaves like video, not a deck.

This skill does not replace `ra-video-production-director`, `hyperframes`,
`remotion`, image generation, or QC tools. It runs before and above them:
define the motion language, choose the visual system, reject PPT-like plans,
then hand off to the right production lane and keep the anti-PPT gate active.

## Core Doctrine

Do not start from pages, slides, or cards. Start from movement.

For every topic, first find a visual metaphor that can move: a river, network,
branching tree, orbit, factory line, swarm, collapse, compression, scanner,
handoff, growth loop, map route, stack, wave, clock, lens, or machine.

Text is an anchor, not the main carrier. If a beat depends on reading a long
paragraph, convert the idea into motion, structure, symbols, or images.

## Workflow

### 1. Intake

Capture only decisions that change the creative path:

- topic or source material
- audience and platform if known
- desired ratio and length; default to 16:9 and 30-60 seconds if unspecified
- narration, silent motion graphic, or captioned explainer
- factual accuracy level: casual, source-backed, or reference-replica
- required style, reference video, component library, or image-generation skill

If the user simply gives a topic and asks for a video, proceed with best
judgment. Do not ask for a full brief unless the missing answer changes the
production route.

### 2. Source and Truth Gate

For factual, historical, scientific, legal, medical, financial, current, or
named-entity topics, verify the core claims before writing the motion plan.
Prefer primary or authoritative sources. Use absolute dates when dates matter.

Keep facts short. The video should not become an encyclopedia; facts exist to
support the motion narrative.

### 3. Motion Thesis

Write one sentence:

`This video moves by showing <visual metaphor> transforming from <start state>
to <end state>, proving <core claim>.`

Examples:

- Human evolution: a time river branches, lights up tools, then becomes a
  migration network.
- AI agents: one cursor splits into autonomous task nodes that route through
  tools and return as completed work.
- Economic inflation: a stable price grid stretches, leaks, and rebalances.

If no moving metaphor is found, stop and invent one before planning scenes.

### 4. Beat Graph

Plan a continuous timeline, not pages. Each beat must include:

- `time`: start-end seconds
- `narrative job`: hook, reveal, contrast, mechanism, consequence, proof, close
- `main moving object`: the element carrying motion
- `state change`: what physically changes on screen
- `camera/layer motion`: push, pan, parallax, orbit, crop, or stable base
- `text role`: title, label, caption, counter, or none
- `asset need`: code/SVG, generated image, screenshot, icon, footage, or none
- `PPT risk`: what would make this beat feel like a slide

At least 80% of beats must have a visible state change beyond fade/slide-in.

### 5. Motion Grammar

Read `references/motion-grammar.md` before choosing primitives. Combine 2-4
motion primitives per video and reuse them with variation. Do not stack every
effect everywhere.

### 6. Image and Asset Direction

Use generated images only when they carry narrative work: a character, scene,
object, historical visual, metaphor, or visual texture that code cannot express
well enough. Avoid decorative stock-like images.

If image generation is used, specify:

- what the image must explain
- where it appears in the timeline
- how it moves after generation
- whether it must match an existing visual system

Static images must be animated with crop, mask, parallax, reveal, light sweep,
depth layers, or transformation. A still image plus text is not enough.

### 7. Implementation Route

Default to HyperFrames for authored motion videos in this workspace. Read and
follow the relevant HyperFrames skills before writing composition code.

Use Remotion when the project is already React/Remotion-based or when React
component reuse is the main advantage. Use Lottie/Rive/Three.js only for the
specific visual layer that benefits from them.

If the user asks for a complete production, continue into production instead
of stopping at a plan:

- create source project under
  `<WORKSPACE>/01-内容生产/视频工作台/动效项目/`
- render final MP4
- archive to `<WORKSPACE>/legacy-archive/`
- put contact sheets and QC artifacts under the same project `质检/` folder

### 8. Anti-PPT Gate

Read `references/anti-ppt-gate.md` before implementation and again before
final delivery. If the plan fails, rewrite the motion plan before coding.

Hard fail conditions:

- the plan is a list of pages/slides
- most beats are title + bullets + fade
- objects appear but do not transform or travel
- there is no continuous visual system across beats
- the same card layout repeats without meaningful motion changes
- the user asked for a video but the output is only a storyboard

### 9. QC and Completion

Before calling a video done:

- run the toolchain checks required by the selected renderer
- extract keyframes at meaningful beat midpoints
- inspect whether motion continuity is visible across the contact sheet
- check text fit, resolution, duration, and archive paths
- state remaining limitations honestly, especially if no audio or no generated
  images were used

## Output Contract

For planning-only requests, output:

1. Motion thesis
2. Beat graph
3. Component and asset plan
4. Anti-PPT risks
5. Production route

For production requests, use the same structure internally, then produce the
actual video and final QC artifacts.

## References

- `references/motion-grammar.md`: visual metaphors and motion primitives.
- `references/anti-ppt-gate.md`: checklist for rejecting slide-like videos.
