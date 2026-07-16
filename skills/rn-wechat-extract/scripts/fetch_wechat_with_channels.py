#!/usr/bin/env python3
"""
Fetch WeChat public account article with video channel (视频号) video download support.

Download pipeline for 视频号-embedded videos (the article HTML itself has no
directly playable URL for these, only opaque identifiers):

    1. Extract export_id + object_nonce_id from the <mp-common-video> embed tag
       (or use a direct weixin.qq.com/sph/... share link if the article has one).
    2. [TikHub, paid] fetch_video_detail(export_id, object_nonce_id) -> resolve the
       real numeric object_id (the export_id/nonce pair alone is not a stable identifier).
    3. [TikHub, paid] fetch_video_share_url(object_id) -> weixin.qq.com/sph/xxx share link.
    4. [Third-party community worker, free] sph.litao.workers.dev fetch_video_profile
       (share_url) -> h264/h265 CDN url. This CDN url carries an X-snsvideoflag query
       param that makes WeChat's CDN return the plaintext, pre-transcoded stream
       (X-encflag: 0) instead of the ISAAC64-encrypted original — so no decrypt
       step is needed afterwards.
    5. Download that CDN url with WeChat headers (hits WeChat's own CDN directly).

Steps 2-4 depend on two external services that are NOT part of this project:
- TikHub (https://tikhub.io): a paid commercial API. Requires your own API key,
  passed via --tikhub-key or the TIKHUB_API_KEY environment variable. Steps 2+3
  are billed at $0.01 each ($0.02/video total). We are not affiliated with TikHub.
- sph.litao.workers.dev: a free, already-deployed Cloudflare Worker run by a third
  party, not by this project. It's a public instance of the open-source project
  ltaoo/wx_channels_download (https://github.com/ltaoo/wx_channels_download) — we
  did not write or deploy it, and its uptime is outside our control. To self-host,
  deploy that project yourself and point SPH_WORKER_URL below at your own instance.

Without a TikHub key, video channel videos are still detected and reported but
not downloaded; everything else (text, images, native videos) still works.

Based on:
- Original: Pluviobyte/rnskill
- Video channel resolution: TikHub WeChat-Channels-V2-API (https://docs.tikhub.io)
- Share-link-to-CDN-url resolution: ltaoo/wx_channels_download
  (https://github.com/ltaoo/wx_channels_download), used via its already-deployed
  public instance at sph.litao.workers.dev
"""

import sys
import os
import re
import json
import urllib.request
import urllib.error
import html as html_module
from datetime import datetime
from pathlib import Path

# WeChat iOS WebView User-Agent
WECHAT_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.49"
WECHAT_REFERER = "https://mp.weixin.qq.com/"

# TikHub WeChat Channels V2 API
TIKHUB_BASE = "https://api.tikhub.io/api/v1/wechat_channels/v2"

# Community worker: share_url -> playable (unencrypted) video url
SPH_WORKER_URL = "https://sph.litao.workers.dev/api/fetch_video_profile"


def fetch_html(url: str) -> str:
    """Fetch HTML with WeChat User-Agent."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": WECHAT_UA,
            "Referer": WECHAT_REFERER,
        }
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def download_file(url: str, output_path: str, file_type: str = "file") -> bool:
    """Download file with WeChat headers."""
    try:
        # Clean URL (fix escaped characters)
        clean_url = url.replace('\\x26amp;', '&').replace('\\x26', '&')

        req = urllib.request.Request(
            clean_url,
            headers={
                "User-Agent": WECHAT_UA,
                "Referer": WECHAT_REFERER,
            }
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
            with open(output_path, "wb") as f:
                f.write(data)
        return True
    except Exception as e:
        print(f"  ⚠ Failed to download {file_type}: {e}", file=sys.stderr)
        return False


def tikhub_post(api_key: str, endpoint: str, payload: dict, timeout: int = 30) -> dict:
    """POST to a TikHub WeChat Channels V2 endpoint. Raises on transport/HTTP error."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{TIKHUB_BASE}/{endpoint}",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            # Cloudflare in front of api.tikhub.io blocks the default
            # "Python-urllib/x.y" User-Agent; a normal browser UA passes.
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def tikhub_resolve_object_id(api_key: str, embed: dict) -> str:
    """export_id/object_nonce_id -> real numeric object_id, via fetch_video_detail. Returns '' on failure."""
    payload = {"raw": False}
    if embed.get("export_id"):
        payload["export_id"] = embed["export_id"]
    if embed.get("object_nonce_id"):
        payload["object_nonce_id"] = embed["object_nonce_id"]
    try:
        result = tikhub_post(api_key, "fetch_video_detail", payload)
    except Exception as e:
        print(f"    ⚠ TikHub fetch_video_detail failed: {e}", file=sys.stderr)
        return ""
    return (result.get("data") or {}).get("id") or ""


def tikhub_fetch_share_url(api_key: str, object_id: str) -> str:
    """object_id -> weixin.qq.com/sph/xxx share link, via fetch_video_share_url. Returns '' on failure."""
    try:
        result = tikhub_post(api_key, "fetch_video_share_url", {"object_id": object_id, "raw": False})
    except Exception as e:
        print(f"    ⚠ TikHub fetch_video_share_url failed: {e}", file=sys.stderr)
        return ""
    return (result.get("data") or {}).get("share_url") or ""


def worker_resolve_video_url(share_url: str) -> dict:
    """share_url -> {'video_url', 'description', 'author'} with an unencrypted CDN url, or None."""
    try:
        data = json.dumps({"url": share_url}).encode("utf-8")
        req = urllib.request.Request(
            SPH_WORKER_URL,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"    ⚠ sph worker fetch_video_profile failed: {e}", file=sys.stderr)
        return None

    feed_info = (result.get("data") or {}).get("feedInfo") or {}
    video_url = (
        (feed_info.get("h264VideoInfo") or {}).get("videoUrl")
        or (feed_info.get("h265VideoInfo") or {}).get("videoUrl")
        or feed_info.get("videoUrl")
    )
    if not video_url:
        return None
    return {
        "video_url": video_url,
        "description": feed_info.get("description", ""),
        "author": ((result.get("data") or {}).get("authorInfo") or {}).get("nickname", ""),
    }


def download_channel_video(api_key: str, source, out_path: str) -> str:
    """
    Resolve and download one video channel video.
    `source` is either a share_url string, or an embed dict {export_id, object_nonce_id}
    requiring TikHub resolution first.
    Returns the share_url used on success, or "" on failure.
    """
    if isinstance(source, str):
        share_url = source
    else:
        object_id = tikhub_resolve_object_id(api_key, source)
        if not object_id:
            print("    ⚠ Could not resolve object_id (export_id/nonce may have expired, re-scrape the article)", file=sys.stderr)
            return ""
        share_url = tikhub_fetch_share_url(api_key, object_id)
        if not share_url:
            print("    ⚠ TikHub returned an empty share_url", file=sys.stderr)
            return ""

    profile = worker_resolve_video_url(share_url)
    if not profile:
        print(f"    ⚠ Could not resolve a playable video from {share_url}", file=sys.stderr)
        return ""

    return share_url if download_file(profile["video_url"], out_path, "channel video") else ""


def extract_images_from_html(html: str) -> list:
    """Extract image URLs from HTML (data-src attribute)."""
    pattern = r'data-src="(https://mmbiz\.qpic\.cn[^"]*)"'
    urls = re.findall(pattern, html)

    content_urls = []
    for url in urls:
        if any(skip in url.lower() for skip in ["avatar", "qr_code", "weapp_code", "qrcode", "follow"]):
            continue
        content_urls.append(url)

    return list(dict.fromkeys(content_urls))


def extract_videos_from_html(html: str) -> list:
    """Extract direct (already-playable) video URLs embedded in the article HTML."""
    videos = []

    # Pattern 1: mpvideo.qpic.cn URLs in JavaScript
    script_pattern = r"'(https?://mpvideo\.qpic\.cn/[^']+\.mp4[^']*)'"
    script_urls = re.findall(script_pattern, html)
    for url in script_urls:
        clean_url = url.replace('\\x26amp;', '&').replace('\\x26', '&')
        if clean_url not in videos:
            videos.append(clean_url)

    # Pattern 2: Unescaped URLs
    mp4_pattern = r'(https?://mpvideo\.qpic\.cn/[^\s"\'<>]+\.mp4)'
    mp4_urls = re.findall(mp4_pattern, html)
    for url in mp4_urls:
        clean_url = url.replace('\\x26amp;', '&').replace('\\x26', '&')
        if clean_url not in videos:
            videos.append(clean_url)

    return videos


def extract_video_channel_embeds(html: str) -> list:
    """
    Extract structured video channel (视频号) embeds from <mp-common-videosnap> tags:
    export_id (data-id="export/...") + object_nonce_id (data-nonceid) + username.

    This pair is what TikHub's fetch_video_detail needs to resolve the real
    object_id (data-nonceid alone is object_nonce_id, NOT object_id).
    """
    # The tag appears both HTML-escaped (\x22 for ") in inline JS and literally
    # in the rendered markup; normalize before matching.
    html_norm = html.replace('\\x22', '"').replace('\\x27', "'")

    embeds = []
    seen = set()
    for tag in re.findall(r'<mp-common-videosnap\b[^>]*>', html_norm, re.I):
        m_id = re.search(r'data-id="(export/[^"]*)"', tag)
        m_nonce = re.search(r'data-nonceid="(\d+)"', tag)
        m_user = re.search(r'data-username="([^"]*@finder)"', tag)
        m_desc = re.search(r'data-desc="([^"]*)"', tag)

        export_id = m_id.group(1) if m_id else None
        object_nonce_id = m_nonce.group(1) if m_nonce else None
        if not export_id and not object_nonce_id:
            continue

        key = export_id or object_nonce_id
        if key in seen:
            continue
        seen.add(key)

        embeds.append({
            "export_id": export_id,
            "object_nonce_id": object_nonce_id,
            "username": m_user.group(1) if m_user else None,
            "desc": html_module.unescape(m_desc.group(1)).strip() if m_desc else "",
        })

    return embeds


def extract_direct_sph_links(html: str) -> list:
    """Extract already-complete video channel share links (weixin.qq.com/sph/xxx)."""
    sph_pattern = r'https?://weixin\.qq\.com/sph/([A-Za-z0-9]+)'
    ids = list(dict.fromkeys(re.findall(sph_pattern, html)))
    return [f"https://weixin.qq.com/sph/{sph_id}" for sph_id in ids]


def parse_article(html: str):
    """Parse article title, author, time, and body."""
    # Title
    m = re.search(r'var\s+msg_title\s*=\s*["\'](.+?)["\']', html)
    title = html_module.unescape(m.group(1)) if m else "Untitled"

    # Author
    m = re.search(r'<meta[^>]*name="author"[^>]*content="([^"]*)"', html)
    if not m:
        m = re.search(r'<span[^>]*class="profile_meta_value"[^>]*>([^<]*)</span>', html)
    author = html_module.unescape(m.group(1)) if m else "Unknown"

    # Publish time
    m = re.search(r'var\s+ct\s*=\s*"?(\d+)"?', html)
    if m:
        try:
            publish_time = datetime.fromtimestamp(int(m.group(1))).strftime("%Y-%m-%d %H:%M")
        except:
            publish_time = ""
    else:
        m = re.search(r'<em[^>]*id="publish_time"[^>]*>([^<]*)</em>', html)
        publish_time = m.group(1).strip() if m else ""

    # Body
    m = re.search(r'id="js_content"[^>]*>(.*?)</div>\s*(?:<div|<script)', html, re.DOTALL)
    if not m:
        m = re.search(r'id="js_content"[^>]*>(.*)', html, re.DOTALL)
    body = m.group(1) if m else ""

    # Convert to markdown
    body = re.sub(r'<br\s*/?>', '\n', body)
    body = re.sub(r'</p>', '\n', body)
    body = re.sub(r'</section>', '\n', body)
    body = re.sub(r'<h([1-6])[^>]*>(.*?)</h\1>', lambda g: '\n' + '#' * int(g.group(1)) + ' ' + g.group(2) + '\n', body, flags=re.DOTALL)
    body = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', body, flags=re.DOTALL)
    body = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', body, flags=re.DOTALL)
    body = re.sub(r'<blockquote[^>]*>(.*?)</blockquote>', lambda g: '\n> ' + g.group(1).strip() + '\n', body, flags=re.DOTALL)

    def replace_img(match):
        tag = match.group(0)
        m = re.search(r'data-src="([^"]*)"', tag)
        if m:
            url = m.group(1)
            return f'\n![image]({url})\n'
        return ''

    body = re.sub(r'<img[^>]*>', replace_img, body)
    body = re.sub(r'<iframe[^>]*class="video_iframe[^>]*>.*?</iframe>', '\n[VIDEO]\n', body, flags=re.DOTALL)

    body = re.sub(r'<[^>]+>', '', body)
    body = html_module.unescape(body)
    body = re.sub(r'\n{3,}', '\n\n', body)
    body = re.sub(r'[ \t]+', ' ', body)
    body = body.strip()

    return title, author, publish_time, body


def is_captcha_page(html: str) -> bool:
    """Check if page is a CAPTCHA page."""
    return "环境异常" in html[:3000] and "去验证" in html[:3000]


def slugify(title: str) -> str:
    """Create URL-safe slug from title."""
    slug = re.sub(r'[^\w一-鿿]+', '-', title)
    return slug.strip('-')[:60] or "wechat-article"


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Fetch WeChat article with video channel support")
    parser.add_argument("url", nargs="?", help="mp.weixin.qq.com article URL")
    parser.add_argument("--output-dir", default=None, help="Output directory (default: cwd)")
    parser.add_argument("--raw", action="store_true", help="Also save raw HTML")
    parser.add_argument("--tikhub-key", default=os.environ.get("TIKHUB_API_KEY"),
                         help="TikHub API key for resolving 视频号 videos. Falls back to TIKHUB_API_KEY env var.")
    parser.add_argument("--no-channel-videos", action="store_true",
                         help="Skip downloading video channel (视频号) videos even if a TikHub key is available")
    parser.add_argument("--doctor", action="store_true", help="Check dependencies")
    args = parser.parse_args()

    if args.doctor:
        print("fetch_wechat_with_channels.py: OK (stdlib only, no external dependencies)")
        print("  Video channel (视频号) downloads additionally require a TikHub API key")
        print("  (--tikhub-key or TIKHUB_API_KEY env var); https://tikhub.io")
        sys.exit(0)

    if not args.url:
        parser.error("url is required (unless --doctor)")

    if "mp.weixin.qq.com" not in args.url:
        print(f"ERROR: not a WeChat article URL: {args.url}", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching: {args.url}", file=sys.stderr)

    try:
        html = fetch_html(args.url)
    except Exception as e:
        print(f"ERROR: fetch failed: {e}", file=sys.stderr)
        sys.exit(1)

    if is_captcha_page(html):
        print("ERROR: CAPTCHA page detected. Wait a few minutes and retry.", file=sys.stderr)
        sys.exit(1)

    title, author, publish_time, body = parse_article(html)
    if not body:
        print("ERROR: failed to parse article body", file=sys.stderr)
        sys.exit(2)

    # Prepare output directory
    out_dir = Path(args.output_dir or ".")
    out_dir.mkdir(parents=True, exist_ok=True)

    slug = slugify(title)
    date_str = datetime.now().strftime("%Y-%m-%d")
    base_name = f"{date_str}-{slug}"

    # Extract images
    print("Extracting images...", file=sys.stderr)
    image_urls = extract_images_from_html(html)
    image_count = 0
    image_map = {}

    if image_urls:
        images_dir = out_dir / f"{base_name}_images"
        images_dir.mkdir(exist_ok=True)

        print(f"Found {len(image_urls)} images", file=sys.stderr)

        for i, url in enumerate(image_urls, 1):
            ext = ".jpg" if "jpeg" in url or "jpg" in url else ".png"
            img_filename = f"image_{i:02d}{ext}"
            img_path = images_dir / img_filename

            print(f"  Downloading image {i}/{len(image_urls)}...", file=sys.stderr)
            if download_file(url, str(img_path), "image"):
                image_count += 1
                image_map[url] = f"{base_name}_images/{img_filename}"

        print(f"Downloaded {image_count}/{len(image_urls)} images", file=sys.stderr)

    # Extract direct (already-playable) videos
    print("Extracting videos...", file=sys.stderr)
    video_urls = extract_videos_from_html(html)
    video_count = 0
    videos_dir = None

    if video_urls:
        videos_dir = out_dir / f"{base_name}_videos"
        videos_dir.mkdir(exist_ok=True)

        print(f"Found {len(video_urls)} direct video URLs", file=sys.stderr)

        for i, url in enumerate(video_urls, 1):
            vid_path = videos_dir / f"video_{i:02d}.mp4"
            print(f"  Downloading video {i}/{len(video_urls)}...", file=sys.stderr)
            if download_file(url, str(vid_path), "video"):
                video_count += 1

        print(f"Downloaded {video_count}/{len(video_urls)} direct videos", file=sys.stderr)

    # Extract video channel (视频号) sources: structured embeds + direct share links
    channel_embeds = extract_video_channel_embeds(html)
    direct_sph_links = extract_direct_sph_links(html)
    channel_sources = list(channel_embeds) + list(direct_sph_links)

    channel_count = 0
    channel_share_urls = []

    if channel_sources:
        print(f"\nFound {len(channel_sources)} video channel (视频号) video(s):", file=sys.stderr)
        for src in channel_sources:
            if isinstance(src, str):
                print(f"  - share link: {src}", file=sys.stderr)
            else:
                print(f"  - export_id={src['export_id']}, object_nonce_id={src['object_nonce_id']}", file=sys.stderr)

        if args.no_channel_videos:
            print("  (--no-channel-videos set, skipping download)", file=sys.stderr)
        elif not args.tikhub_key:
            print("  ⚠ No TikHub API key: pass --tikhub-key or set TIKHUB_API_KEY to download these", file=sys.stderr)
        else:
            if videos_dir is None:
                videos_dir = out_dir / f"{base_name}_videos"
                videos_dir.mkdir(exist_ok=True)

            for i, src in enumerate(channel_sources, 1):
                print(f"  Resolving channel video {i}/{len(channel_sources)}...", file=sys.stderr)
                vid_path = videos_dir / f"channel_{i:02d}.mp4"
                share_url = download_channel_video(args.tikhub_key, src, str(vid_path))
                if share_url:
                    channel_count += 1
                    channel_share_urls.append(share_url)

            print(f"Downloaded {channel_count}/{len(channel_sources)} video channel videos", file=sys.stderr)

    # Update markdown with local image paths
    if image_map:
        for url, local_path in image_map.items():
            body = body.replace(url, local_path)

    # Write markdown
    md_path = out_dir / f"{base_name}.md"
    md_content = f"# {title}\n\n"
    md_content += f"作者：{author}\n"
    md_content += f"发布时间：{publish_time}\n"
    if image_count > 0:
        md_content += f"图片数量：{image_count}\n"
    if video_count > 0:
        md_content += f"视频数量：{video_count}\n"
    if channel_sources:
        md_content += f"视频号内容：{len(channel_sources)} 个（成功下载 {channel_count} 个）\n"
    md_content += f"\n---\n\n{body}\n"

    md_path.write_text(md_content, encoding="utf-8")

    # Save raw HTML if requested
    if args.raw:
        raw_path = out_dir / f"{base_name}.raw.html"
        raw_path.write_text(html, encoding="utf-8")

    # Output result
    result = {
        "status": "ok",
        "title": title,
        "author": author,
        "publish_time": publish_time,
        "char_count": len(body),
        "image_count": image_count,
        "video_count": video_count,
        "channel_video_found": len(channel_sources),
        "channel_video_downloaded": channel_count,
        "output_path": str(md_path),
    }
    if image_count > 0:
        result["images_dir"] = str(out_dir / f"{base_name}_images")
    if video_count > 0 or channel_count > 0:
        result["videos_dir"] = str(out_dir / f"{base_name}_videos")
    if channel_share_urls:
        result["channel_share_urls"] = channel_share_urls
    if channel_sources and not args.tikhub_key and not args.no_channel_videos:
        result["note"] = "Video channel videos detected but not downloaded: pass --tikhub-key or set TIKHUB_API_KEY"

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
