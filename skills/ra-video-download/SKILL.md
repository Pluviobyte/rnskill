---
name: ra-video-download
description: "Download source video or audio from Douyin, YouTube, Bilibili, Twitter/X, Xiaohongshu, and other yt-dlp-supported URLs into the content-creation workspace. Use when the user says 下载视频, 下载音频, 保存这个链接, 把源视频拉下来, or when another video workflow needs a local source file before transcription, frame analysis, editing, reference replication, or archiving."
---

# 视频下载

Download source media only. Do not transcribe, rewrite, edit, or publish it.

## Storage rules

- Keep source URLs, source titles, source metadata, and downloaded reference media inside `01-内容生产/视频工作台/.internal/` by default.
- Use `01-内容生产/视频工作台/制作中/<日期-主题>/原始素材/` only when the caller explicitly names a production project and the media is an approved production input.
- Never place source information in a handoff, finished script, final archive, or public document.
- Never overwrite an existing file. Let the downloader add a stable suffix or stop.

## Workflow

1. Confirm that the URL is source media and that downloading it is within the user's request.
2. Run the bundled downloader. It uses this order:
   - Douyin: TikHub media URL, then `yt-dlp` with browser cookies, then plain `yt-dlp`.
   - Other supported sites: plain `yt-dlp`, optionally with browser cookies when required.
3. Inspect the returned local path and media probe. A successful HTTP response alone is not delivery.
4. Require a playable audio or video stream and a non-zero duration. Report the local path, duration, dimensions, and selected download method.
5. If every route fails, preserve the concise failure log and state the missing prerequisite. Do not claim that the video was downloaded.

## Command

Use the Python interpreter that can import `tikhub` for the best Douyin path. In this workspace, prefer `/opt/homebrew/bin/python3` when available.

```bash
/opt/homebrew/bin/python3 scripts/download_media.py '<url>'
```

Useful options:

```bash
# Explicit production input directory
/opt/homebrew/bin/python3 scripts/download_media.py '<url>' --output-dir '01-内容生产/视频工作台/制作中/<日期-主题>/原始素材/<项目>'

# Extract audio only
/opt/homebrew/bin/python3 scripts/download_media.py '<url>' --audio-only

# Use an authenticated browser profile for a protected public page
/opt/homebrew/bin/python3 scripts/download_media.py '<url>' --cookies-from-browser chrome
```

Resolve `scripts/download_media.py` relative to this `SKILL.md`; do not assume the current directory is the skill directory.

## Safety and failure handling

- Use browser cookies only for the requested public media. Do not print, copy, or persist raw cookies.
- Read `TIKHUB_API_KEY` from the environment or the workspace-root `.env`; never print it.
- Do not bypass private-account access controls, paywalls, DRM, or deleted/private media.
- Treat TikHub and browser cookies as acquisition fallbacks, not as proof that reuse rights exist.
- Keep the original source file untouched after download.
- If `ffprobe` fails, reject the file even if it has an `.mp4` extension.

## Handoff

Return a compact result containing:

- local media path
- source metadata path
- method used (`tikhub`, `yt-dlp-cookie`, or `yt-dlp`)
- duration, resolution, and codecs
- any limitation such as watermark, missing audio, or authentication failure

Then route onward only when requested: `ra-逐字稿提取skill` for source speech extraction, `video-use` for editing, or `ra-video-production-director` for production.
