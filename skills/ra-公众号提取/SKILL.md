---
name: ra-公众号提取
description: "提取微信公众号文章全文。Use when the user provides a mp.weixin.qq.com URL and asks for 提取文章, 抓取公众号, 读一下这篇, or when another skill (ra-洗稿, ra-选题, ra-video-wash-pipeline) needs to read a WeChat article before processing. Uses MicroMessenger UA spoofing to bypass WeChat's first-layer access control. Stdlib only, no API key required."
---

# ra-公众号提取

## Goal

Extract the full text of a WeChat public account article into clean Markdown, ready for downstream skills.

This skill is intentionally narrow:

- fetch the article HTML with a spoofed WeChat UA
- parse title, author, publish time, and body text
- write a Markdown file to `01-内容生产/视频工作台/.internal/公众号/`
- print the complete text in the conversation

Do not summarize, rewrite, translate, title, or start production. Hand the extracted text to the calling skill or user.

## Locate The Skill

```bash
WX_HOME="$(
  for d in "$(pwd)/.codex/skills/ra-公众号提取" \
           "$(pwd)/.agents/skills/ra-公众号提取" \
           "$(pwd)/.claude/skills/ra-公众号提取" \
           "$HOME/.codex/skills/ra-公众号提取" \
           "$HOME/.agents/skills/ra-公众号提取" \
           "$HOME/.claude/skills/ra-公众号提取"; do
    [ -f "$d/SKILL.md" ] && echo "$d" && break
  done
)"
export WX_HOME
```

Use `"$WX_HOME/scripts/fetch_wechat.py"` for every operation.

## How It Works

WeChat blocks external access to public account articles through several layers:

1. **User-Agent detection** — checks for `MicroMessenger` keyword; rejects normal browser UAs
2. **Referer check** — expects requests from `mp.weixin.qq.com`
3. **JS lazy-loading** — images use `data-src` instead of `src`
4. **Rate limiting** — frequent requests trigger CAPTCHA

This skill bypasses layer 1 and 2 by sending a request with a genuine WeChat iOS WebView User-Agent and the correct Referer header. This is sufficient to receive the full article HTML for text extraction. No login, cookie, or API key is needed.

Limitations:
- Images are extracted as URLs only (from `data-src`), not downloaded
- Some articles with heavy JS rendering may return partial content
- Rapid successive calls from the same IP may trigger CAPTCHA (wait and retry)
- Does not work on articles that require WeChat login or payment

## Workflow

1. Health check (optional):

   ```bash
   python3 "$WX_HOME/scripts/fetch_wechat.py" --doctor
   ```

2. Extract article:

   ```bash
   python3 "$WX_HOME/scripts/fetch_wechat.py" "<mp.weixin.qq.com URL>" \
     --output-dir "01-内容生产/视频工作台/.internal/公众号"
   ```

3. The script outputs a JSON result with `title`, `author`, `publish_time`, `char_count`, and `output_path`. Read the output file and present the full text to the user or pass it to the next skill.

4. If the script exits with code 1 (fetch/CAPTCHA failure), report the error and suggest:
   - Wait a few minutes and retry
   - Ask the user to paste the article text directly

5. If the script exits with code 2 (parse failure), save the raw HTML with `--raw` for debugging.

## Storage Rules

- Extracted articles land in `01-内容生产/视频工作台/.internal/公众号/` by default (source privacy zone).
- Source URLs and source titles must not appear in any handoff file, finished script, or public document.
- When called by ra-洗稿 or ra-选题, the source link is recorded only in the topic card's `来源:` field.

## Integration With Other Skills

This skill is a **source reader**, not a content processor. Typical call chains:

| User says | Call chain |
|---|---|
| 这篇公众号洗稿 / 基于这篇公众号制作视频 | ra-公众号提取 → ra-洗稿 |
| 这篇文章存个选题 | ra-公众号提取 → ra-选题 |
| 读一下这篇公众号 | ra-公众号提取 (standalone) |
| 这篇公众号做成图文 | ra-公众号提取 → ra-洗稿 (图文形态) |

When another skill needs to read a `mp.weixin.qq.com` URL, call this skill first to obtain the text, then pass the extracted Markdown to the downstream skill.

## Script Reference

```
fetch_wechat.py <url> [options]

Arguments:
  url                    mp.weixin.qq.com article URL

Options:
  --output-dir <dir>     Output directory (default: current directory)
  --raw                  Also save the raw HTML alongside the Markdown
  --doctor               Check dependencies and exit
```

Exit codes: 0 = success, 1 = fetch failed, 2 = parse failed.

No external dependencies — uses Python stdlib only (`urllib`, `re`, `html`, `json`).
