# rnskill

[中文](README.zh.md) | English

AI Agent Skills maintained by 雪踏乌云 for Codex, Claude Code, and other Agent workflows that support `SKILL.md`.

The collection covers Chinese writing, content extraction, motion direction, original reference-motion studies, halftone collage motion, style-specific video production, openers, and evidence-based replica QA.

## Requirements

- Codex, Claude Code, or another Agent that supports project-level skills.
- A target project that can load `.agents/skills/<skill-name>/SKILL.md`.

## Installation

### Claude Code Plugin Marketplace

```bash
claude plugin marketplace add Pluviobyte/rnskill
claude plugin install rn-renhua@rnskill
```

### Universal (Codex / Claude Code)

```bash
npx -y skills add Pluviobyte/rnskill -g --all
```

Or install a single skill:

```bash
npx -y skills add Pluviobyte/rnskill --skill rn-editorial-collage-motion
```

### Manual Install

Copy only the skill you need into your project:

```bash
# Codex
mkdir -p <project>/.agents/skills
cp -R skills/rn-renhua <project>/.agents/skills/rn-renhua
cp -R skills/rn-motion-replica <project>/.agents/skills/rn-motion-replica
cp -R skills/rn-editorial-collage-motion <project>/.agents/skills/rn-editorial-collage-motion

# Claude Code
mkdir -p <project>/.claude/skills
cp -R skills/rn-renhua <project>/.claude/skills/rn-renhua
cp -R skills/rn-motion-replica <project>/.claude/skills/rn-motion-replica
cp -R skills/rn-editorial-collage-motion <project>/.claude/skills/rn-editorial-collage-motion
```

## Available Skills

### Writing

| Skill | Description |
|-------|-------------|
| [`rn-renhua`](skills/rn-renhua/) | Chinese AI/tech writing de-AI editor. Removes AI-flavored patterns while preserving author voice, facts, and judgment. |

### Content Extraction

| Skill | Description |
|-------|-------------|
| [`rn-wechat-extract`](skills/rn-wechat-extract/) | Extract full text from WeChat public account articles via MicroMessenger UA spoofing. Stdlib only, no API key. |

### Video Production

| Skill | Description |
|-------|-------------|
| [`rn-motion-director`](skills/rn-motion-director/) | Motion-first AI video director. Turns topics into motion video concepts with visual metaphors, beat graphs, and anti-PPT QC. |
| [`rn-motion-replica`](skills/rn-motion-replica/) | Builds an original, editable HyperFrames motion study from an authorized reference range, with analysis evidence and final-MP4 QC. |
| [`rn-editorial-collage-motion`](skills/rn-editorial-collage-motion/) | Turns a reference or short brief into an editable halftone paper-collage spec, approved Codex-generated stills, and deterministic assemble-from-empty motion rendered locally with FFmpeg or HyperFrames. |
| [`rn-dark-saas-video`](skills/rn-dark-saas-video/) | Dark cinematic SaaS product video in "magic UI" style. 8 scene blueprints, 3 timing presets, hard style rules. |
| [`rn-bw-text-opener`](skills/rn-bw-text-opener/) | Black-white typed text opener animation with synced typing SFX. 3 timing presets. Includes a Python timing plan generator. |

### Quality Control

| Skill | Description |
|-------|-------------|
| [`rn-replica-qc`](skills/rn-replica-qc/) | SOP v2 replica QA. Five fidelity levels plus asset, runtime, and delivery full-frame gates; exact replay and parametric motion are registered separately. |

## Directory Structure

```text
rnskill/
├── skills/
│   ├── rn-renhua/              # Writing: de-AI editor
│   ├── rn-wechat-extract/      # Extraction: WeChat article reader
│   ├── rn-motion-director/     # Video: motion director
│   ├── rn-motion-replica/      # Video: original editable motion study
│   ├── rn-editorial-collage-motion/ # Video: halftone collage assembly
│   ├── rn-dark-saas-video/     # Video: dark SaaS style
│   ├── rn-bw-text-opener/      # Video: typed text opener
│   └── rn-replica-qc/          # QC: reference video replica
├── docs/                       # Per-skill overview pages
├── assets/                     # Showcase images and videos
├── tools/                      # Build and packaging scripts
├── .claude-plugin/             # Claude Code marketplace manifest
└── .github/workflows/          # Release automation
```

## Maintainer Sync

The four mirrored video skills are developed in `Pluviobyte/video-production-skills`. Refresh them without touching repository-native skills such as `rn-renhua` and `rn-motion-replica`:

```bash
python3 tools/sync-video-skills.py --source /path/to/video-production-skills
python3 tools/sync-video-skills.py --source /path/to/video-production-skills --check
```

## Credits and Local Adaptation

`rn-editorial-collage-motion` is an independent adaptation inspired by Vikash Kumar's original [Arcads Collage Motion Skill](https://buldrr.com/arcads-collage-motion-skill/). Credit goes to Vikash Kumar for the original two-stage idea: decode a reference into an editable visual specification, then animate approved collage stills as an assemble-from-empty sequence.

The original workflow requires the Arcads MCP connector and Arcads credits, and uses Nano Banana 2 for stills plus Seedance 2.0 for motion. This repository edition replaces that service chain with Codex's built-in image generation and local FFmpeg or HyperFrames rendering. It therefore needs no Arcads MCP connection and consumes no Arcads credits, making it a free local-compatible edition for users who already have access to Codex; existing Codex access and local compute requirements still apply. This adaptation is not an official Arcads or original-author release.

## License

CC BY-NC 4.0. See [LICENSE](LICENSE).

## Author

雪踏乌云 · [@Pluvio9yte](https://x.com/Pluvio9yte)
