#!/usr/bin/env python3
"""
Fetch WeChat public account article with image and video download support.

Enhanced version of fetch_wechat.py that downloads images and videos.
Based on original by Pluviobyte (https://github.com/Pluviobyte/rnskill)

Usage:
    python fetch_wechat_with_media.py <url> [--output-dir DIR] [--no-images] [--no-videos] [--raw]
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

def extract_images_from_html(html: str) -> list:
    """Extract image URLs from HTML (data-src attribute)."""
    # Match data-src for lazy-loaded images
    pattern = r'data-src="(https://mmbiz\.qpic\.cn[^"]*)"'
    urls = re.findall(pattern, html)
    
    # Filter out non-content images (avatars, QR codes, etc.)
    content_urls = []
    for url in urls:
        if any(skip in url.lower() for skip in ["avatar", "qr_code", "weapp_code", "qrcode", "follow"]):
            continue
        content_urls.append(url)
    
    return list(dict.fromkeys(content_urls))  # Remove duplicates while preserving order

def extract_videos_from_html(html: str) -> list:
    """Extract video URLs from HTML."""
    videos = []
    
    # Pattern 1: mpvideo.qpic.cn URLs in JavaScript (with escaped quotes)
    # Look for URLs wrapped in single quotes with escaped characters
    script_pattern = r"'(https?://mpvideo\.qpic\.cn/[^']+\.mp4[^']*)'"
    script_urls = re.findall(script_pattern, html)
    
    for url in script_urls:
        # Clean escaped characters
        clean_url = url.replace('\\x26amp;', '&').replace('\\x26', '&')
        if clean_url not in videos:
            videos.append(clean_url)
    
    # Pattern 2: Also look for unescaped URLs
    mp4_pattern = r'(https?://mpvideo\.qpic\.cn/[^\s"\'<>]+\.mp4)'
    mp4_urls = re.findall(mp4_pattern, html)
    
    for url in mp4_urls:
        clean_url = url.replace('\\x26amp;', '&').replace('\\x26', '&')
        if clean_url not in videos:
            videos.append(clean_url)
    
    # Pattern 3: Video channel (视频号) IDs - wxv_ format
    wxv_pattern = r"video_id:\s*['\"](wxv_[^['\"]+)['\"]"
    wxv_ids = re.findall(wxv_pattern, html)
    
    # Pattern 4: Video snap card format (video_snap_card)
    # This is another way to embed video channels
    snap_card_pattern = r"video_snap_card:\s*['\"]([^['\"]+)['\"]"
    snap_cards = re.findall(snap_card_pattern, html)
    
    # Pattern 5: Finder username format
    finder_pattern = r"username\\x22:\\x22([^@]+@finder)\\x22"
    finder_usernames = re.findall(finder_pattern, html)
    
    # Pattern 6: Export ID format
    export_pattern = r"export_id\\x22:\\x22([^\\x22]+)\\x22"
    export_ids = re.findall(export_pattern, html)
    
    # Pattern 7: Finder video URL (findermp.video.qq.com)
    finder_video_pattern = r"findermp\.video\.qq\.com[^\"]*"
    finder_video_urls = re.findall(finder_video_pattern, html)
    
    if wxv_ids:
        print(f"  Found {len(wxv_ids)} video channel IDs (wxv_): {', '.join(wxv_ids)}", file=sys.stderr)
    if finder_usernames:
        print(f"  Found {len(finder_usernames)} video channel usernames (finder)", file=sys.stderr)
    if export_ids:
        print(f"  Found {len(export_ids)} video channel export IDs", file=sys.stderr)
    if finder_video_urls:
        print(f"  Found {len(finder_video_urls)} finder video URLs (may be expired)", file=sys.stderr)
    
    return videos

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
    
    # Replace img tags with markdown image syntax (using data-src)
    def replace_img(match):
        tag = match.group(0)
        m = re.search(r'data-src="([^"]*)"', tag)
        if m:
            url = m.group(1)
            return f'\n![image]({url})\n'
        return ''
    
    body = re.sub(r'<img[^>]*>', replace_img, body)
    
    # Replace video iframes with placeholder
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
    
    parser = argparse.ArgumentParser(description="Fetch WeChat article with image and video support")
    parser.add_argument("url", nargs="?", help="mp.weixin.qq.com article URL")
    parser.add_argument("--output-dir", default=None, help="Output directory (default: cwd)")
    parser.add_argument("--no-images", action="store_true", help="Skip image download")
    parser.add_argument("--no-videos", action="store_true", help="Skip video download")
    parser.add_argument("--raw", action="store_true", help="Also save raw HTML")
    parser.add_argument("--doctor", action="store_true", help="Check dependencies")
    args = parser.parse_args()

    if args.doctor:
        print("fetch_wechat_with_media.py: OK (stdlib only, no external dependencies)")
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
        if args.raw:
            raw_path = Path(args.output_dir or ".") / "debug_raw.html"
            raw_path.write_text(html, encoding="utf-8")
            print(f"Raw HTML saved to: {raw_path}", file=sys.stderr)
        sys.exit(2)

    # Prepare output directory
    out_dir = Path(args.output_dir or ".")
    out_dir.mkdir(parents=True, exist_ok=True)

    slug = slugify(title)
    date_str = datetime.now().strftime("%Y-%m-%d")
    base_name = f"{date_str}-{slug}"

    # Download images if enabled
    image_count = 0
    image_map = {}
    
    if not args.no_images:
        print("Extracting images...", file=sys.stderr)
        image_urls = extract_images_from_html(html)
        
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
                    # Map URL to local path for markdown
                    image_map[url] = f"{base_name}_images/{img_filename}"
            
            print(f"Downloaded {image_count}/{len(image_urls)} images", file=sys.stderr)

    # Download videos if enabled
    video_count = 0
    video_map = {}
    video_channel_ids = []
    
    if not args.no_videos:
        print("Extracting videos...", file=sys.stderr)
        video_urls = extract_videos_from_html(html)
        
        # Also extract video channel IDs
        wxv_pattern = r"video_id:\s*['\"](wxv_[^['\"]+)['\"]"
        video_channel_ids = re.findall(wxv_pattern, html)
        
        if video_urls:
            videos_dir = out_dir / f"{base_name}_videos"
            videos_dir.mkdir(exist_ok=True)
            
            print(f"Found {len(video_urls)} videos", file=sys.stderr)
            if video_channel_ids:
                print(f"Found {len(video_channel_ids)} video channel (视频号) IDs", file=sys.stderr)
            
            for i, url in enumerate(video_urls, 1):
                vid_filename = f"video_{i:02d}.mp4"
                vid_path = videos_dir / vid_filename
                
                print(f"  Downloading video {i}/{len(video_urls)}...", file=sys.stderr)
                if download_file(url, str(vid_path), "video"):
                    video_count += 1
                    video_map[url] = f"{base_name}_videos/{vid_filename}"
            
            print(f"Downloaded {video_count}/{len(video_urls)} videos", file=sys.stderr)

    # Update markdown with local image paths
    if image_map:
        for url, local_path in image_map.items():
            body = body.replace(url, local_path)

    # Update markdown with video placeholder
    if video_map:
        for i, (url, local_path) in enumerate(video_map.items(), 1):
            body = body.replace('[VIDEO]', f'\n[Video {i}: {local_path}]\n', 1)

    # Write markdown
    md_path = out_dir / f"{base_name}.md"
    md_content = f"# {title}\n\n"
    md_content += f"作者：{author}\n"
    md_content += f"发布时间：{publish_time}\n"
    if image_count > 0:
        md_content += f"图片数量：{image_count}\n"
    if video_count > 0:
        md_content += f"视频数量：{video_count}\n"
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
        "output_path": str(md_path),
    }
    if image_count > 0:
        result["images_dir"] = str(out_dir / f"{base_name}_images")
    if video_count > 0:
        result["videos_dir"] = str(out_dir / f"{base_name}_videos")
    if video_channel_ids:
        result["video_channel_ids"] = video_channel_ids
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
