---
name: video-use-install
description: Install the content-system video-use variant with Volcengine word timestamps.
---

# video-use install

This workspace uses a local variant of `browser-use/video-use`. Editing logic,
EDL rendering, cut-boundary checks, and timeline views remain upstream-compatible;
the transcription provider is Volcengine Doubao ASR.

## Requirements

1. The complete skill directory, including `helpers/`, is discoverable by the agent.
2. `ffmpeg` and `ffprobe` are on `PATH`.
3. Python dependencies from `pyproject.toml` are installed.
4. `VOLCENGINE_API_KEY` resolves from the workspace root `.env` or environment.
5. The default ASR resource is `volc.seedasr.auc`; use
   `VOLCENGINE_RESOURCE_ID` only when the account requires another resource.

## Install and registration

The project copy under `.claude/skills/video-use/` is the source of truth.
Run the workspace sync script after updating it:

```bash
bash automation/scripts/sync_skills.sh
```

For global discovery, link the project source of truth into each agent's skill
directory. Do not link an unmodified upstream checkout because it still uses a
different transcription provider.

## Dependency setup

```bash
cd <WORKSPACE>/.claude/skills/video-use
UV_PROJECT_ENVIRONMENT=<HOME>/.venvs/video-use uv sync
ln -sfn <HOME>/.venvs/video-use .venv
command -v ffmpeg >/dev/null
command -v ffprobe >/dev/null
```

`yt-dlp` remains optional and is only needed for URL downloads. Animation
engines are installed lazily inside the individual animation slot.

## Readiness check

```bash
.venv/bin/python helpers/transcribe.py --doctor
.venv/bin/python helpers/timeline_view.py --help >/dev/null
ffprobe -version | head -1
```

The doctor must report `ready: true`, `volcengine_api_key: true`, and resource
ID `volc.seedasr.auc`. A real transcription test should use a short genuine
speech clip; synthetic silence is not a valid ASR check.

## Daily use

Read `SKILL.md` and all helper descriptions. Put raw footage in its project
folder; all outputs stay under `<videos_dir>/edit/`. Transcripts are cached per
source and must not be regenerated unless the source changes.
