---
name: rn-wechat-extract
description: "Extract full text from WeChat public account articles (mp.weixin.qq.com). Use when the user provides a WeChat article URL and asks for 提取文章, 抓取公众号, 读一下这篇, or when another skill needs to read a WeChat article before processing. Bypasses WeChat's access control via MicroMessenger UA spoofing. Stdlib only, no API key required."
---

# RN WeChat Extract

Extract the full text of a WeChat public account article into clean Markdown.

This skill is a **source reader** — it extracts and returns text. It does not summarize, rewrite, translate, or produce video.

## How It Works

WeChat blocks external access to public account articles through User-Agent detection: the server checks for the `MicroMessenger` keyword and rejects normal browser requests.

This skill sends HTTP requests with a genuine WeChat iOS WebView User-Agent and the correct Referer header, which is sufficient to receive the full article HTML. No login, cookie, or API key is needed.

**Extracts:** title, author, publish time, and body text as Markdown.

**Limitations:**
- Some heavily JS-rendered articles may return partial content
- Rapid successive calls from the same IP may trigger CAPTCHA (wait and retry)
- Does not work on login-gated or paid articles

**Enhanced Versions:**
- `fetch_wechat_with_images.py` - Downloads images only
- `fetch_wechat_with_media.py` - Downloads both images and directly-embedded videos
- `fetch_wechat_with_channels.py` - Also downloads WeChat Channels (视频号) videos embedded in the article, via an optional [TikHub](https://tikhub.io) API key
- Images saved to `{title}_images/` directory
- Videos saved to `{title}_videos/` directory
- Markdown references updated to local paths

## Locate The Skill

```bash
WX_HOME="$(
  for d in "$(pwd)/.codex/skills/rn-wechat-extract" \
           "$(pwd)/.agents/skills/rn-wechat-extract" \
           "$(pwd)/.claude/skills/rn-wechat-extract" \
           "$(pwd)/rnskill/skills/rn-wechat-extract" \
           "$HOME/.codex/skills/rn-wechat-extract" \
           "$HOME/.agents/skills/rn-wechat-extract" \
           "$HOME/.claude/skills/rn-wechat-extract"; do
    [ -f "$d/SKILL.md" ] && echo "$d" && break
  done
)"
export WX_HOME
```

## Workflow

1. Health check (optional):

   ```bash
   python3 "$WX_HOME/scripts/fetch_wechat.py" --doctor
   ```

2. Extract article:

   ```bash
   python3 "$WX_HOME/scripts/fetch_wechat.py" "<mp.weixin.qq.com URL>" \
     --output-dir "<desired output directory>"
   ```

3. The script prints a JSON result to stdout:

   ```json
   {
     "status": "ok",
     "title": "文章标题",
     "author": "公众号名称",
     "publish_time": "2026-07-14 00:18",
     "char_count": 7025,
     "output_path": "path/to/extracted.md"
   }
   ```

4. Read the output file and present the full text or pass it to the next skill.

5. On failure:
   - Exit 1 (fetch/CAPTCHA): suggest retry after a few minutes or ask the user to paste text
   - Exit 2 (parse failure): rerun with `--raw` to save HTML for debugging

## Command Reference

### Basic Version (text only)

```
fetch_wechat.py <url> [options]

Arguments:
  url                    mp.weixin.qq.com article URL

Options:
  --output-dir <dir>     Output directory (default: current directory)
  --raw                  Also save the raw HTML alongside the Markdown
  --doctor               Check dependencies and exit
```

### Enhanced Version (images only)

```
fetch_wechat_with_images.py <url> [options]

Arguments:
  url                    mp.weixin.qq.com article URL

Options:
  --output-dir <dir>     Output directory (default: current directory)
  --no-images            Skip image download
  --raw                  Also save the raw HTML alongside the Markdown
  --doctor               Check dependencies and exit
```

### Enhanced Version (images + videos)

```
fetch_wechat_with_media.py <url> [options]

Arguments:
  url                    mp.weixin.qq.com article URL

Options:
  --output-dir <dir>     Output directory (default: current directory)
  --no-images            Skip image download
  --no-videos            Skip video download
  --raw                  Also save the raw HTML alongside the Markdown
  --doctor               Check dependencies and exit
```

**Output structure (with media):**
```
output/
├── 2026-07-15-article-title.md
├── 2026-07-15-article-title.raw.html  (if --raw)
├── 2026-07-15-article-title_images/
│   ├── image_01.jpg
│   ├── image_02.jpg
│   └── ...
└── 2026-07-15-article-title_videos/
    ├── video_01.mp4
    ├── video_02.mp4
    └── ...
```

### Enhanced Version (images + videos + video channels / 视频号)

```
fetch_wechat_with_channels.py <url> [options]

Arguments:
  url                     mp.weixin.qq.com article URL

Options:
  --output-dir <dir>      Output directory (default: current directory)
  --tikhub-key <key>      TikHub API key for resolving 视频号 videos. Falls back to TIKHUB_API_KEY env var.
  --no-channel-videos     Detect but skip downloading 视频号 videos
  --raw                   Also save the raw HTML alongside the Markdown
  --doctor                Check dependencies and exit
```

Without `--tikhub-key` / `TIKHUB_API_KEY`, video channel videos are still detected and reported (their `export_id` / `object_nonce_id`) but not downloaded — everything else (text, images, direct videos) still works.

**Output structure (with channels):**
```
output/
├── 2026-07-15-article-title.md
├── 2026-07-15-article-title.raw.html  (if --raw)
├── 2026-07-15-article-title_images/
│   ├── image_01.jpg
│   └── ...
└── 2026-07-15-article-title_videos/
    ├── video_01.mp4       # direct mpvideo.qpic.cn videos
    └── channel_01.mp4     # 视频号 videos resolved via TikHub + worker
```

No external dependencies — Python stdlib only (`urllib`, `re`, `html`, `json`).

## Integration Examples

This skill provides text for any downstream content workflow:

| Scenario | Call chain |
|---|---|
| Rewrite article into video script | rn-wechat-extract → rewrite skill |
| Save article as topic idea | rn-wechat-extract → topic management |
| Read and discuss an article | rn-wechat-extract (standalone) |
| Turn article into image cards | rn-wechat-extract → content adaptation |
| Extract article with images | rn-wechat-extract (with_images) |
| Extract article with full media | rn-wechat-extract (with_media) |
| Extract article including 视频号 videos | rn-wechat-extract (with_channels) |

## Enhanced Versions

| Version | Images | Direct Videos | 视频号 Videos | Use Case |
|---------|--------|----------------|----------------|----------|
| Original | ❌ | ❌ | ❌ | Text-only extraction |
| with_images | ✅ | ❌ | ❌ | Articles with important images |
| with_media | ✅ | ✅ | ❌ | Articles with native videos |
| with_channels | ✅ | ✅ | ✅ (requires TikHub key) | Articles embedding WeChat Channels videos |

### Usage Examples

```bash
# Text only (original)
python3 "$WX_HOME/scripts/fetch_wechat.py" "<url>" --output-dir "./output"

# With images
python3 "$WX_HOME/scripts/fetch_wechat_with_images.py" "<url>" --output-dir "./output"

# With images and videos
python3 "$WX_HOME/scripts/fetch_wechat_with_media.py" "<url>" --output-dir "./output"

# With images, videos, and video channel (视频号) videos
python3 "$WX_HOME/scripts/fetch_wechat_with_channels.py" "<url>" \
  --output-dir "./output" --tikhub-key "$TIKHUB_API_KEY"
```

### Technical Details

**Images:**
- WeChat uses lazy-loaded `data-src` attributes
- Script extracts URLs and downloads with WeChat headers
- Images saved to `{title}_images/` directory

**Videos:**
- Videos hosted on `mpvideo.qpic.cn`
- Script extracts MP4 URLs from JavaScript
- Videos saved to `{title}_videos/` directory
- Some videos may require authentication (403 errors) — the article's video URLs carry a short-lived token, so download can fail if the HTML is stale; re-scrape close to download time

**Video Channel (视频号) Videos:**

The article HTML has no directly playable URL for a 视频号-embedded video, only opaque identifiers. Resolving one to a downloadable file takes 3 network hops, **two of which call third-party services not built or operated by this project** — see [Third-Party Services](#third-party-services-视频号-downloads-only) below before relying on this in production.

1. Extract `export_id` (`data-id="export/..."`) and `object_nonce_id` (`data-nonceid`) from the article's `<mp-common-videosnap>` embed tag — or use a direct `weixin.qq.com/sph/...` share link if the article already has one.
2. **[TikHub]** `fetch_video_detail` (export_id + object_nonce_id) → resolve the real numeric `object_id`. Note `object_nonce_id` alone is *not* the object_id — a common mix-up since both are numeric strings.
3. **[TikHub]** `fetch_video_share_url` (object_id) → a `weixin.qq.com/sph/xxx` share link.
4. **[Third-party community worker]** `sph.litao.workers.dev/api/fetch_video_profile` (share_url) → an h264/h265 CDN video URL carrying an `X-snsvideoflag` query param. This param makes WeChat's CDN return the **plaintext, pre-transcoded** stream (`X-encflag: 0` in the response headers) instead of the ISAAC64-encrypted original that TikHub's own media URL points to — so no separate decrypt step is needed.
5. Download that CDN URL with WeChat headers (no third party involved — this hits WeChat's own CDN directly).

## Third-Party Services (视频号 downloads only)

Everything else in this skill (text/image/native-video extraction) is self-contained and needs no third-party service or API key. Only the 视频号 video pipeline in `fetch_wechat_with_channels.py` (steps 2–4 above) depends on two external services **neither built nor operated by this project**:

1. **[TikHub](https://tikhub.io)** — a paid, commercial third-party API. You need your own TikHub account and API key (`--tikhub-key` / `TIKHUB_API_KEY`). This project has no affiliation with TikHub; it just calls two of their public endpoints (`fetch_video_detail`, `fetch_video_share_url`), each billed at $0.01/call ($0.02/video total). See their [WeChat Channels V2 API docs](https://docs.tikhub.io).

2. **[sph.litao.workers.dev](https://sph.litao.workers.dev/)** — a free, already-deployed Cloudflare Worker run by a third party (not by this project or by TikHub). It is a public instance of the open-source project **[ltaoo/wx_channels_download](https://github.com/ltaoo/wx_channels_download)**, and we simply call its already-running `/api/fetch_video_profile` endpoint. We did not write or deploy this service, and its uptime is outside this project's control. If it ever goes down, the fallback is to self-host that same open-source project yourself and point `SPH_WORKER_URL` in `fetch_wechat_with_channels.py` at your own deployment.
