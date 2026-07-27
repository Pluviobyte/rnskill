#!/usr/bin/env python3
"""
Lightweight transcript path for Douyin/Xiaohongshu URLs:
URL -> Qushuiyin media resolver -> DashScope Paraformer -> Markdown.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
ENV_FILE = SKILL_DIR / ".env"
LOADED_ENV_FILES: list[str] = []


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    real_path = str(path.resolve())
    if real_path in LOADED_ENV_FILES:
        return
    LOADED_ENV_FILES.append(real_path)
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key.strip(), value)


_load_dotenv(ENV_FILE)
for parent in SKILL_DIR.parents:
    _load_dotenv(parent / ".env")


def default_output_dir() -> str:
    configured = os.getenv("TRANSCRIPT_OUTPUT_DIR")
    if configured:
        return configured
    for parent in SKILL_DIR.parents:
        candidate = parent / "01-内容生产" / "视频工作台" / ".internal" / "洗稿"
        if candidate.exists():
            return str(candidate)
    return str(SKILL_DIR / "outputs")


QUSHUIYIN_API_BASE = os.getenv("QUSHUIYIN_API_BASE", "https://api.guijianpan.com").rstrip("/")
QUSHUIYIN_API_KEY = os.getenv("QUSHUIYIN_API_KEY", "")
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY") or os.getenv("PARAFORMER_API_KEY", "")
PARAFORMER_MODEL = os.getenv("PARAFORMER_MODEL", "paraformer-v2")
PARAFORMER_POLL_INTERVAL_SECONDS = int(os.getenv("PARAFORMER_POLL_INTERVAL_SECONDS", "3"))
PARAFORMER_TIMEOUT_SECONDS = int(os.getenv("PARAFORMER_TIMEOUT_SECONDS", "240"))

DASHSCOPE_TRANSCRIPTION_URL = (
    "https://dashscope.aliyuncs.com/api/v1/services/audio/asr/transcription"
)
DASHSCOPE_TASK_URL = "https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"


def is_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def detect_platform(url: str) -> str:
    host = urllib.parse.urlparse(url).hostname or ""
    host = host.lower()
    if "xiaohongshu" in host or "xhslink" in host:
        return "xiaohongshu"
    if "douyin" in host:
        return "douyin"
    return "unknown"


def safe_filename(name: str, max_len: int = 60) -> str:
    name = re.sub(r"https?://\S+", "", name or "")
    name = re.sub(r"#\S+", "", name)
    name = re.sub(r'[\\/:*?"<>|]', "_", name)
    name = re.sub(r"\s+", "_", name.strip())
    return (name[:max_len].strip("_") or "transcript")


def http_json(method: str, url: str, *, headers: dict[str, str] | None = None,
              payload: dict[str, Any] | None = None, timeout: int = 30) -> Any:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method.upper())
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    if data is not None and not req.has_header("Content-Type"):
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {body[:400]}") from exc


def split_title_and_text(value: str) -> tuple[str, str]:
    if "||" not in value:
        return value.strip(), ""
    title, text = value.split("||", 1)
    return title.strip(), text.strip()


def first_string_field(items: list[Any], field_names: tuple[str, ...]) -> str:
    for item in items:
        if isinstance(item, str) and item.startswith("http"):
            return item
        if isinstance(item, dict):
            for name in field_names:
                value = item.get(name)
                if isinstance(value, str) and value.startswith("http"):
                    return value
    return ""


def resolve_qushuiyin(source_url: str, platform: str) -> dict[str, Any]:
    if not QUSHUIYIN_API_KEY:
        raise RuntimeError("QUSHUIYIN_API_KEY not configured")

    endpoint = f"{QUSHUIYIN_API_BASE}/waterRemoveDetail/xxmQsyByAk"
    query = urllib.parse.urlencode({"ak": QUSHUIYIN_API_KEY, "link": source_url})
    data = http_json("GET", f"{endpoint}?{query}", timeout=30)
    content = data.get("content") if isinstance(data, dict) else None
    if data.get("code") != "10000" or not isinstance(content, dict):
        raise RuntimeError(data.get("msg") or "Qushuiyin resolve failed")

    title, embedded_text = split_title_and_text(content.get("title", "") or "")
    full_text = content.get("originText", "") or content.get("msg", "") or ""
    if full_text.startswith(("http://", "https://")) and embedded_text:
        full_text = embedded_text

    video_url = content.get("url", "") or first_string_field(
        content.get("videoList") or content.get("video_list") or [],
        ("url", "playUrl", "play_url", "downloadUrl", "download_url"),
    )
    if not video_url:
        raise RuntimeError("Qushuiyin did not return a video URL")

    return {
        "platform": platform,
        "title": title,
        "author": content.get("author", "") or "",
        "full_text": full_text,
        "video_url": video_url,
        "cover_url": content.get("cover", "") or content.get("headUrl", "") or "",
        "raw": data,
    }


def dashscope_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def collect_text(result_json: Any) -> str:
    if not isinstance(result_json, dict):
        return ""
    if isinstance(result_json.get("text"), str):
        return result_json["text"].strip()
    parts: list[str] = []
    for key in ("transcripts", "sentences"):
        items = result_json.get(key)
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict) and isinstance(item.get("text"), str):
                    parts.append(item["text"].strip())
    return "\n".join(p for p in parts if p)


def collect_sentences(result_json: Any) -> list[dict[str, Any]]:
    if not isinstance(result_json, dict):
        return []
    candidates: list[Any] = []
    if isinstance(result_json.get("sentences"), list):
        candidates.extend(result_json["sentences"])
    for transcript in result_json.get("transcripts") or []:
        if isinstance(transcript, dict) and isinstance(transcript.get("sentences"), list):
            candidates.extend(transcript["sentences"])

    sentences = []
    for item in candidates:
        if isinstance(item, dict) and isinstance(item.get("text"), str) and item["text"].strip():
            sentences.append(item)
    return sentences


def transcribe_paraformer(media_url: str) -> tuple[str, str, dict[str, Any]]:
    if not DASHSCOPE_API_KEY:
        raise RuntimeError("DASHSCOPE_API_KEY/PARAFORMER_API_KEY not configured")

    submit = http_json(
        "POST",
        DASHSCOPE_TRANSCRIPTION_URL,
        headers={**dashscope_headers(DASHSCOPE_API_KEY), "X-DashScope-Async": "enable"},
        payload={"model": PARAFORMER_MODEL, "input": {"file_urls": [media_url]}},
        timeout=30,
    )
    task_id = submit.get("output", {}).get("task_id") if isinstance(submit, dict) else ""
    if not task_id:
        raise RuntimeError(f"Paraformer task_id not found: {submit}")

    print(f"[INFO] Paraformer task: {task_id}", file=sys.stderr)
    deadline = time.time() + PARAFORMER_TIMEOUT_SECONDS
    last_data: dict[str, Any] = {}
    while time.time() < deadline:
        query = http_json(
            "POST",
            DASHSCOPE_TASK_URL.format(task_id=task_id),
            headers=dashscope_headers(DASHSCOPE_API_KEY),
            payload={},
            timeout=30,
        )
        last_data = query if isinstance(query, dict) else {}
        output = last_data.get("output", {})
        status = output.get("task_status") or last_data.get("task_status")
        if status in {"SUCCEEDED", "FAILED", "CANCELED"}:
            if status != "SUCCEEDED":
                raise RuntimeError(f"Paraformer task {status}: {last_data}")
            results = output.get("results") or output.get("task_results") or []
            transcription_url = ""
            if results and isinstance(results[0], dict):
                transcription_url = results[0].get("transcription_url", "") or ""
            if not transcription_url:
                raise RuntimeError(f"transcription_url not found: {last_data}")
            result_json = http_json("GET", transcription_url, timeout=60)
            text = collect_text(result_json)
            if not text:
                raise RuntimeError("No text found in Paraformer result")
            return task_id, text, result_json

        print(".", end="", file=sys.stderr, flush=True)
        time.sleep(PARAFORMER_POLL_INTERVAL_SECONDS)

    raise RuntimeError(f"Paraformer transcription timed out: {last_data}")


def value_to_seconds(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number / 1000 if number > 1000 else number


def sentence_times(item: dict[str, Any]) -> tuple[float | None, float | None]:
    start = None
    end = None
    for key in ("begin_time", "start_time", "start"):
        start = value_to_seconds(item.get(key))
        if start is not None:
            break
    for key in ("end_time", "end"):
        end = value_to_seconds(item.get(key))
        if end is not None:
            break
    return start, end


def mmss(seconds: float | int | None) -> str:
    seconds = int(seconds or 0)
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def text_chunks(text: str, max_chars: int = 180) -> list[str]:
    pieces = re.split(r"(?<=[。！？!?])", text.strip())
    chunks: list[str] = []
    buf = ""
    for piece in pieces:
        piece = piece.strip()
        if not piece:
            continue
        if buf and len(buf) + len(piece) > max_chars:
            chunks.append(buf)
            buf = piece
        else:
            buf = (buf + piece).strip()
    if buf:
        chunks.append(buf)
    return chunks or ([text.strip()] if text.strip() else [])


def build_body(text: str, result_json: dict[str, Any]) -> str:
    sentences = collect_sentences(result_json)
    if not sentences:
        return "\n\n".join(f"## {i}. 逐字稿\n\n{chunk}" for i, chunk in enumerate(text_chunks(text), 1))

    sections: list[tuple[float | None, float | None, list[str]]] = []
    cur_texts: list[str] = []
    cur_start: float | None = None
    cur_end: float | None = None
    for item in sentences:
        start, end = sentence_times(item)
        if cur_start is None:
            cur_start = start
        cur_end = end if end is not None else cur_end
        cur_texts.append(item["text"].strip())
        duration = (cur_end - cur_start) if cur_start is not None and cur_end is not None else 0
        if len(cur_texts) >= 4 or duration >= 35:
            sections.append((cur_start, cur_end, cur_texts))
            cur_texts = []
            cur_start = None
            cur_end = None
    if cur_texts:
        sections.append((cur_start, cur_end, cur_texts))

    parts = []
    for idx, (start, end, lines) in enumerate(sections, 1):
        stamp = f"\n\n[{mmss(start)} - {mmss(end)}]" if start is not None or end is not None else ""
        parts.append(f"## {idx}. 逐字稿{stamp}\n\n" + "\n\n".join(lines))
    return "\n\n".join(parts)


def build_markdown(source_url: str, resolved: dict[str, Any], task_id: str,
                   text: str, result_json: dict[str, Any], override_title: str | None = None) -> str:
    title = override_title or resolved.get("title") or "视频逐字稿"
    platform_zh = {"douyin": "抖音", "xiaohongshu": "小红书"}.get(resolved["platform"], resolved["platform"])
    header = [
        f"# {title}",
        "",
        f"> 来源: {source_url}",
        f"> 平台: {platform_zh}",
        f"> 转写: qushuiyin 解析 + 阿里云百炼 Paraformer ({PARAFORMER_MODEL})",
        f"> 任务: {task_id}",
    ]
    if resolved.get("author"):
        header.append(f"> 作者: {resolved['author']}")
    return "\n".join(header) + "\n\n" + build_body(text, result_json).strip() + "\n"


def run(input_path: str, *, title: str | None = None, output_dir: str | None = None,
        save_md: bool = True) -> bool:
    if not is_url(input_path):
        return False
    platform = detect_platform(input_path)
    if platform not in {"douyin", "xiaohongshu"}:
        return False
    if not QUSHUIYIN_API_KEY or not DASHSCOPE_API_KEY:
        return False

    print("[Fast 1/3] qushuiyin 解析媒体直链...", file=sys.stderr)
    resolved = resolve_qushuiyin(input_path, platform)
    picked_title = title or resolved.get("title") or "视频逐字稿"
    print(f"[INFO] 平台: {platform} | 标题: {picked_title}", file=sys.stderr)

    print("[Fast 2/3] Paraformer 转写...", file=sys.stderr)
    task_id, text, result_json = transcribe_paraformer(resolved["video_url"])
    print("", file=sys.stderr)

    print("[Fast 3/3] 生成 Markdown...", file=sys.stderr)
    final_md = build_markdown(input_path, resolved, task_id, text, result_json, title)

    if save_md:
        out_dir = Path(output_dir or default_output_dir())
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{safe_filename(picked_title)}_transcript.md"
        out_file.write_text(final_md, encoding="utf-8")
        print(f"[OK] 逐字稿已保存: {out_file}", file=sys.stderr)

    print("=" * 55, file=sys.stderr)
    print("[OK] 转录完成,完整逐字稿见 stdout", file=sys.stderr)
    print(final_md)
    return True


def mask(value: str) -> str:
    return value[:6] + "…" + value[-4:] if len(value) > 12 else "***"


def doctor() -> int:
    print("=" * 55)
    print("  ra-逐字稿提取skill 体检")
    print("=" * 55)
    issues = []
    if QUSHUIYIN_API_KEY:
        print(f"  ✓ QUSHUIYIN_API_KEY: {mask(QUSHUIYIN_API_KEY)}")
    else:
        print("  ✗ QUSHUIYIN_API_KEY 未配置")
        issues.append("在项目根目录 .env 写 QUSHUIYIN_API_KEY")

    if DASHSCOPE_API_KEY:
        print(f"  ✓ DASHSCOPE_API_KEY/PARAFORMER_API_KEY: {mask(DASHSCOPE_API_KEY)}")
    else:
        print("  ✗ DASHSCOPE_API_KEY 或 PARAFORMER_API_KEY 未配置")
        issues.append("在项目根目录 .env 写 DASHSCOPE_API_KEY")

    print(f"  ✓ QUSHUIYIN_API_BASE: {QUSHUIYIN_API_BASE}")
    print(f"  ✓ PARAFORMER_MODEL: {PARAFORMER_MODEL}")
    for loaded_env in LOADED_ENV_FILES:
        if loaded_env != str(ENV_FILE.resolve()):
            print(f"  ✓ 已读取项目配置: {loaded_env}")

    print("=" * 55)
    if issues:
        print(f"  发现 {len(issues)} 个问题:")
        for issue in issues:
            print(f"     - {issue}")
        return 1
    print("  全部就绪")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="ra-逐字稿提取skill: qushuiyin + Paraformer")
    parser.add_argument("input", nargs="?", help="抖音/小红书视频 URL")
    parser.add_argument("--title", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--no-save", dest="save_md", action="store_false")
    parser.add_argument("--doctor", action="store_true", help="检查 qushuiyin + Paraformer 配置")
    parser.set_defaults(save_md=True)
    args = parser.parse_args()

    if args.doctor:
        raise SystemExit(doctor())
    if not args.input:
        parser.error("缺少 input 参数。当前 skill 只接收抖音/小红书视频 URL。")
    if not run(args.input, title=args.title, output_dir=args.output_dir, save_md=args.save_md):
        raise SystemExit("当前 skill 只支持抖音/小红书视频 URL，且必须配置 QUSHUIYIN_API_KEY 和 DASHSCOPE_API_KEY。")


if __name__ == "__main__":
    main()
