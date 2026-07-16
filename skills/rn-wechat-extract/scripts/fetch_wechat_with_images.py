#!/usr/bin/env python3
"""
Fetch WeChat public account article with image download support.

Enhanced version of fetch_wechat.py that also downloads images.
Based on original by Pluviobyte (https://github.com/Pluviobyte/rnskill)

Usage:
    python fetch_wechat_with_images.py <url> [--output-dir DIR] [--no-images] [--raw]
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

def download_image(url: str, output_path: str) -> bool:
    """Download image with WeChat headers."""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": WECHAT_UA,
                "Referer": WECHAT_REFERER,
            }
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            with open(output_path, "wb") as f:
                f.write(data)
        return True
    except Exception as e:
        print(f"  ⚠ Failed to download {url}: {e}", file=sys.stderr)
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
    
    parser = argparse.ArgumentParser(description="Fetch WeChat article with image support")
    parser.add_argument("url", nargs="?", help="mp.weixin.qq.com article URL")
    parser.add_argument("--output-dir", default=None, help="Output directory (default: cwd)")
    parser.add_argument("--no-images", action="store_true", help="Skip image download")
    parser.add_argument("--raw", action="store_true", help="Also save raw HTML")
    parser.add_argument("--doctor", action="store_true", help="Check dependencies")
    args = parser.parse_args()

    if args.doctor:
        print("fetch_wechat_with_images.py: OK (stdlib only, no external dependencies)")
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
                if download_image(url, str(img_path)):
                    image_count += 1
                    # Map URL to local path for markdown
                    image_map[url] = f"{base_name}_images/{img_filename}"
            
            print(f"Downloaded {image_count}/{len(image_urls)} images", file=sys.stderr)

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
        "output_path": str(md_path),
    }
    if image_count > 0:
        result["images_dir"] = str(out_dir / f"{base_name}_images")
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
