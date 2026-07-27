#!/usr/bin/env python3
"""Download source media into the private content-creation workspace."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Iterable


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)


def workspace_root() -> Path:
    configured = os.environ.get("CONTENT_CREATION_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    for parent in (Path.cwd(), *Path.cwd().parents):
        if (parent / "CLAUDE.md").exists() and (parent / "01-内容生产").exists():
            return parent
    return Path.cwd().resolve()


def load_env_value(root: Path, name: str) -> str:
    value = os.environ.get(name, "").strip()
    if value:
        return value
    env_file = root / ".env"
    if not env_file.exists():
        return ""
    pattern = re.compile(rf"\s*{re.escape(name)}\s*=\s*(.+)\s*$")
    for line in env_file.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match:
            return match.group(1).strip().strip('"').strip("'")
    return ""


def resolve_url(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.geturl()


def douyin_aweme_id(url: str) -> tuple[str, str]:
    final_url = resolve_url(url)
    match = re.search(r"/(?:video|note)/(\d+)", final_url)
    if not match:
        match = re.search(r"(?:aweme_id=|modal_id=)(\d+)", final_url)
    return (match.group(1) if match else "", final_url)


def nested_url_lists(value: Any, path: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], str]]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield from nested_url_lists(child, (*path, str(key)))
    elif isinstance(value, list):
        if path and path[-1] == "url_list":
            for item in value:
                if isinstance(item, str) and item.startswith(("http://", "https://")):
                    yield path, item
        else:
            for index, child in enumerate(value):
                yield from nested_url_lists(child, (*path, str(index)))


def pick_douyin_media_url(video: dict[str, Any]) -> str:
    preferred = ("play_addr_h264", "play_addr_265", "play_addr", "download_addr")
    found = list(nested_url_lists(video))
    for key in preferred:
        for path, url in found:
            if key in path:
                return url.replace("playwm", "play")
    return found[0][1] if found else ""


def tikhub_douyin(url: str, output_dir: Path, stem: str, root: Path) -> tuple[Path, dict[str, Any]]:
    try:
        from tikhub import TikHub
    except ImportError as exc:
        raise RuntimeError("Python package 'tikhub' is unavailable") from exc

    api_key = load_env_value(root, "TIKHUB_API_KEY")
    if not api_key:
        raise RuntimeError("TIKHUB_API_KEY is missing")

    aweme_id, final_url = douyin_aweme_id(url)
    if not aweme_id:
        raise RuntimeError("Could not resolve the Douyin aweme_id")

    client = TikHub(
        base_url="https://api.tikhub.dev", api_key=api_key, timeout=25.0, max_retries=1
    )
    response = client.douyin_web.fetch_one_video(aweme_id=aweme_id)
    detail = (response.get("data") or {}).get("aweme_detail") or {}
    media_url = pick_douyin_media_url(detail.get("video") or {})
    if not media_url:
        raise RuntimeError("TikHub returned metadata without a downloadable media URL")

    destination = unique_path(output_dir / f"{stem}.mp4")
    request = urllib.request.Request(
        media_url,
        headers={"User-Agent": USER_AGENT, "Referer": "https://www.douyin.com/"},
    )
    with urllib.request.urlopen(request, timeout=60) as response, destination.open("wb") as handle:
        shutil.copyfileobj(response, handle, length=1024 * 1024)

    if destination.stat().st_size == 0:
        destination.unlink(missing_ok=True)
        raise RuntimeError("TikHub media download produced an empty file")

    metadata = {
        "platform": "douyin",
        "aweme_id": aweme_id,
        "resolved_url": final_url,
        "title": detail.get("desc") or "",
        "author": (detail.get("author") or {}).get("nickname") or "",
    }
    return destination, metadata


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    for number in range(2, 1000):
        candidate = path.with_name(f"{path.stem}-{number}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Too many existing files for {path.name}")


def run_ytdlp(
    url: str,
    output_dir: Path,
    stem: str,
    audio_only: bool,
    browser: str | None,
) -> tuple[Path, dict[str, Any]]:
    executable = shutil.which("yt-dlp")
    if not executable:
        raise RuntimeError("yt-dlp is not installed")

    before = {path.resolve() for path in output_dir.iterdir() if path.is_file()}
    template = str(output_dir / f"{stem}.%(ext)s")
    command = [executable, "--no-playlist", "--no-overwrites", "--write-info-json"]
    if browser:
        command.extend(["--cookies-from-browser", browser])
    if audio_only:
        command.extend(["--extract-audio", "--audio-format", "mp3"])
    else:
        command.extend(["--format", "bv*+ba/b"])
    command.extend(["--output", template, url])

    completed = subprocess.run(command, text=True, capture_output=True)
    if completed.returncode != 0:
        message = completed.stderr.strip().splitlines()[-1] if completed.stderr.strip() else "unknown error"
        raise RuntimeError(message)

    new_files = [
        path
        for path in output_dir.iterdir()
        if path.is_file()
        and path.resolve() not in before
        and path.suffix.lower() not in {".json", ".part", ".ytdl"}
    ]
    if not new_files:
        candidates = [
            path
            for path in output_dir.glob(f"{stem}.*")
            if path.suffix.lower() not in {".json", ".part", ".ytdl"}
        ]
        new_files = candidates
    if not new_files:
        raise RuntimeError("yt-dlp finished without a media file")

    media = max(new_files, key=lambda path: path.stat().st_mtime)
    info_file = output_dir / f"{stem}.info.json"
    metadata: dict[str, Any] = {}
    if info_file.exists():
        raw = json.loads(info_file.read_text(encoding="utf-8"))
        metadata = {
            "platform": raw.get("extractor_key") or raw.get("extractor") or "",
            "id": raw.get("id") or "",
            "title": raw.get("title") or raw.get("description") or "",
            "author": raw.get("uploader") or raw.get("creator") or "",
            "resolved_url": raw.get("webpage_url") or url,
        }
    return media, metadata


def probe_media(path: Path) -> dict[str, Any]:
    executable = shutil.which("ffprobe")
    if not executable:
        raise RuntimeError("ffprobe is not installed")
    command = [
        executable,
        "-v",
        "error",
        "-show_entries",
        "format=duration,format_name:stream=index,codec_type,codec_name,width,height",
        "-of",
        "json",
        str(path),
    ]
    completed = subprocess.run(command, text=True, capture_output=True)
    if completed.returncode != 0:
        raise RuntimeError(f"ffprobe rejected the file: {completed.stderr.strip()}")
    result = json.loads(completed.stdout)
    duration = float((result.get("format") or {}).get("duration") or 0)
    if duration <= 0:
        raise RuntimeError("Downloaded media has zero or unknown duration")
    if not result.get("streams"):
        raise RuntimeError("Downloaded media contains no audio or video stream")
    return result


def extract_audio(video: Path) -> Path:
    executable = shutil.which("ffmpeg")
    if not executable:
        raise RuntimeError("ffmpeg is not installed")
    output = unique_path(video.with_suffix(".mp3"))
    completed = subprocess.run(
        [executable, "-v", "error", "-i", str(video), "-vn", "-c:a", "libmp3lame", "-q:a", "2", str(output)],
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"Audio extraction failed: {completed.stderr.strip()}")
    return output


def safe_stem(url: str, platform: str, identifier: str = "") -> str:
    raw = f"source-{platform}-{identifier}" if identifier else f"source-{platform}"
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", raw).strip("-")[:80]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--audio-only", action="store_true")
    parser.add_argument("--cookies-from-browser", metavar="BROWSER")
    args = parser.parse_args()

    root = workspace_root()
    is_douyin = "douyin.com" in urllib.parse.urlparse(args.url).netloc.lower()
    platform = "douyin" if is_douyin else "media"
    output_dir = args.output_dir
    if output_dir is None:
        date = dt.date.today().isoformat()
        output_dir = root / "01-内容生产/视频工作台/.internal" / f"{date}-{platform}-download"
    elif not output_dir.is_absolute():
        output_dir = root / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    errors: list[str] = []
    media: Path | None = None
    metadata: dict[str, Any] = {}
    method = ""
    aweme_id = ""
    if is_douyin:
        try:
            aweme_id, _ = douyin_aweme_id(args.url)
        except Exception as exc:  # keep fallback routes available
            errors.append(f"resolve: {exc}")
    stem = safe_stem(args.url, platform, aweme_id)

    if is_douyin:
        try:
            media, metadata = tikhub_douyin(args.url, output_dir, stem, root)
            method = "tikhub"
            if args.audio_only:
                audio = extract_audio(media)
                media = audio
        except Exception as exc:
            errors.append(f"tikhub: {exc}")

    if media is None and args.cookies_from_browser:
        try:
            media, metadata = run_ytdlp(
                args.url, output_dir, stem, args.audio_only, args.cookies_from_browser
            )
            method = "yt-dlp-cookie"
        except Exception as exc:
            errors.append(f"yt-dlp-cookie: {exc}")

    if media is None:
        try:
            media, metadata = run_ytdlp(args.url, output_dir, stem, args.audio_only, None)
            method = "yt-dlp"
        except Exception as exc:
            errors.append(f"yt-dlp: {exc}")

    if media is None:
        print(json.dumps({"ok": False, "errors": errors}, ensure_ascii=False, indent=2))
        return 2

    probe = probe_media(media)
    source_record = {
        "source_url": args.url,
        "downloaded_at": dt.datetime.now().astimezone().isoformat(),
        "method": method,
        "media_path": str(media.resolve()),
        "metadata": metadata,
        "probe": probe,
        "fallback_errors": errors,
    }
    record_path = unique_path(output_dir / f"{media.stem}.source.json")
    record_path.write_text(json.dumps(source_record, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "ok": True,
                "method": method,
                "media_path": str(media.resolve()),
                "source_metadata_path": str(record_path.resolve()),
                "probe": probe,
                "fallback_errors": errors,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
