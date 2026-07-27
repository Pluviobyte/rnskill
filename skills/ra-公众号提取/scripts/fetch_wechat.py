#!/usr/bin/env python3
"""
Fetch and extract WeChat public account articles by spoofing MicroMessenger UA.

Usage:
    python3 fetch_wechat.py <url> [--output-dir <dir>] [--raw]

Output:
    Writes a clean Markdown file to the output directory.
    Prints the file path and article metadata to stdout.

Exit codes:
    0  success
    1  fetch failed (network, CAPTCHA, or non-article page)
    2  parse failed (content extraction returned empty)
"""

import argparse
import json
import os
import re
import sys
import urllib.request
from html import unescape
from datetime import datetime

WECHAT_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Mobile/15E148 MicroMessenger/8.0.49(0x18003137) "
    "NetType/WIFI Language/zh_CN"
)

WECHAT_REFERER = "https://mp.weixin.qq.com/"


def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers={
        "User-Agent": WECHAT_UA,
        "Referer": WECHAT_REFERER,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def extract_meta(html: str) -> dict:
    meta = {}

    title_patterns = [
        r"var msg_title = '([^']*)'",
        r'var msg_title = "([^"]*)"',
        r'og:title"\s+content="([^"]*)"',
        r'class="rich_media_title[^"]*"[^>]*>([^<]+)<',
    ]
    for p in title_patterns:
        m = re.search(p, html)
        if m and m.group(1).strip():
            meta["title"] = unescape(m.group(1).strip())
            break

    author_patterns = [
        r'<meta\s+name="author"\s+content="([^"]*)"',
        r'author:\s*[\'"]([^\'"]+)[\'"]',
        r'class="profile_nickname"[^>]*>([^<]+)<',
        r'class="rich_media_meta_nickname"[^>]*>([^<]+)<',
    ]
    for p in author_patterns:
        m = re.search(p, html)
        if m and m.group(1).strip():
            meta["author"] = unescape(m.group(1).strip())
            break

    for key, pattern in [
        ("publish_time", r"var ct = ['\"](\d+)['\"]"),
        ("biz", r"var biz = ['\"]([^'\"]*)['\"]"),
    ]:
        m = re.search(pattern, html)
        if m:
            val = unescape(m.group(1))
            if key == "publish_time" and val.isdigit():
                try:
                    val = datetime.fromtimestamp(int(val)).strftime("%Y-%m-%d %H:%M")
                except (ValueError, OSError):
                    pass
            meta[key] = val
    return meta


def extract_body(html: str) -> str:
    m = re.search(
        r'id="js_content"[^>]*>(.*?)</div>\s*(?:<script|<div\s+class="ct_mpda_wrp")',
        html,
        re.DOTALL,
    )
    if not m:
        return ""

    body = m.group(1)

    body = re.sub(r'<br\s*/?>', '\n', body)
    body = re.sub(r'</p>', '\n', body)
    body = re.sub(r'</section>', '\n', body)
    body = re.sub(r'<h([1-6])[^>]*>(.*?)</h\1>', lambda g: '\n' + '#' * int(g.group(1)) + ' ' + g.group(2) + '\n', body, flags=re.DOTALL)
    body = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', body, flags=re.DOTALL)
    body = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', body, flags=re.DOTALL)
    body = re.sub(r'<blockquote[^>]*>(.*?)</blockquote>', lambda g: '\n> ' + g.group(1).strip() + '\n', body, flags=re.DOTALL)

    imgs = []
    for img in re.finditer(r'<img[^>]*(?:data-src|src)="([^"]+)"[^>]*/?\s*>', body):
        src = img.group(1)
        if "mmbiz.qpic.cn" in src:
            imgs.append(src)
    body = re.sub(r'<img[^>]*/?\s*>', '', body)

    body = re.sub(r'<[^>]+>', '', body)
    body = unescape(body)
    body = re.sub(r'\n{3,}', '\n\n', body)
    body = re.sub(r'[ \t]+', ' ', body)
    body = body.strip()

    return body


def is_captcha_page(html: str) -> bool:
    return "环境异常" in html[:3000] and "去验证" in html[:3000]


def slugify(title: str) -> str:
    slug = re.sub(r'[^\w一-鿿]+', '-', title)
    return slug.strip('-')[:60] or "wechat-article"


def main():
    parser = argparse.ArgumentParser(description="Fetch WeChat article")
    parser.add_argument("url", help="mp.weixin.qq.com article URL")
    parser.add_argument("--output-dir", default=None, help="Output directory (default: cwd)")
    parser.add_argument("--raw", action="store_true", help="Also save raw HTML")
    parser.add_argument("--doctor", action="store_true", help="Check dependencies")
    args = parser.parse_args()

    if args.doctor:
        print("fetch_wechat.py: OK (stdlib only, no external dependencies)")
        sys.exit(0)

    if "mp.weixin.qq.com" not in args.url:
        print(f"ERROR: not a WeChat article URL: {args.url}", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching: {args.url}")
    try:
        html = fetch_html(args.url)
    except Exception as e:
        print(f"ERROR: fetch failed: {e}", file=sys.stderr)
        sys.exit(1)

    if is_captcha_page(html):
        print("ERROR: hit CAPTCHA page — UA spoofing did not bypass this time", file=sys.stderr)
        print("TIP: try again in a few minutes, or fetch from a different IP", file=sys.stderr)
        sys.exit(1)

    meta = extract_meta(html)
    body = extract_body(html)

    if not body or len(body) < 50:
        print("ERROR: body extraction returned < 50 chars, likely a non-article page", file=sys.stderr)
        sys.exit(2)

    title = meta.get("title", "未知标题")
    author = meta.get("author", "未知作者")
    pub_time = meta.get("publish_time", "")

    md_lines = [
        f"# {title}",
        "",
        f"作者：{author}",
    ]
    if pub_time:
        md_lines.append(f"发布时间：{pub_time}")
    md_lines += ["", body]
    md_content = "\n".join(md_lines)

    out_dir = args.output_dir or os.getcwd()
    os.makedirs(out_dir, exist_ok=True)

    date_prefix = datetime.now().strftime("%Y-%m-%d")
    slug = slugify(title)
    filename = f"{date_prefix}-{slug}.md"
    out_path = os.path.join(out_dir, filename)

    counter = 1
    while os.path.exists(out_path):
        out_path = os.path.join(out_dir, f"{date_prefix}-{slug}-{counter}.md")
        counter += 1

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    if args.raw:
        raw_path = out_path.replace(".md", ".raw.html")
        with open(raw_path, "w", encoding="utf-8") as f:
            f.write(html)

    result = {
        "status": "ok",
        "title": title,
        "author": author,
        "publish_time": pub_time,
        "char_count": len(body),
        "output_path": out_path,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
