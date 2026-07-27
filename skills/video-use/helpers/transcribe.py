"""Transcribe video with Volcengine Doubao ASR word timestamps.

Extracts mono 16kHz audio with ffmpeg, submits it to Volcengine Recording File
Recognition 2.0, and normalizes the response into video-use's transcript schema:
``words`` entries with text, start, end, and type fields.

Cached: if the output file already exists, the API call is skipped.

Usage:
    python helpers/transcribe.py <video_path>
    python helpers/transcribe.py <video_path> --edit-dir /custom/edit
    python helpers/transcribe.py --doctor
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


SUBMIT_URL = "https://openspeech.bytedance.com/api/v3/auc/bigmodel/submit"
QUERY_URL = "https://openspeech.bytedance.com/api/v3/auc/bigmodel/query"
DEFAULT_RESOURCE_ID = "volc.seedasr.auc"


def _parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            values[key] = value.strip().strip('"').strip("'")
    return values


def _env_candidates() -> list[Path]:
    candidates: list[Path] = []
    for origin in (Path.cwd(), Path(__file__).resolve()):
        current = origin if origin.is_dir() else origin.parent
        for parent in (current, *current.parents):
            candidate = parent / ".env"
            if candidate not in candidates:
                candidates.append(candidate)
    return candidates


def load_config() -> tuple[dict[str, str], Path | None]:
    config = dict(os.environ)
    used: Path | None = None
    for candidate in _env_candidates():
        values = _parse_env(candidate)
        for key, value in values.items():
            config.setdefault(key, value)
        if used is None and values.get("VOLCENGINE_API_KEY"):
            used = candidate
    return config, used


def load_api_key() -> str:
    config, _ = load_config()
    value = config.get("VOLCENGINE_API_KEY", "")
    if not value:
        sys.exit("VOLCENGINE_API_KEY not found in workspace .env or environment")
    return value


def extract_audio(video_path: Path, dest: Path) -> None:
    cmd = [
        "ffmpeg", "-y", "-v", "error", "-i", str(video_path),
        "-vn", "-ac", "1", "-ar", "16000", "-b:a", "64k", str(dest),
    ]
    subprocess.run(cmd, check=True)


def _api_request(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
) -> tuple[dict[str, Any], dict[str, str]]:
    request = Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=180) as response:
            body = response.read().decode("utf-8", errors="replace")
            normalized_headers = {key.lower(): value for key, value in response.headers.items()}
            return (json.loads(body) if body else {}), normalized_headers
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Volcengine HTTP {exc.code}: {body[:500]}") from exc
    except URLError as exc:
        raise RuntimeError(f"Volcengine request failed: {exc.reason}") from exc


def call_volcengine(
    audio_path: Path,
    api_key: str,
    resource_id: str,
    num_speakers: int | None = None,
    poll_interval: int = 3,
    timeout: int = 900,
) -> dict[str, Any]:
    audio_bytes = audio_path.read_bytes()
    if len(audio_bytes) > 48 * 1024 * 1024:
        raise RuntimeError("Audio is larger than 48 MB; split or compress it before ASR")

    request_id = str(uuid.uuid4())
    payload = {
        "user": {"uid": "video-use"},
        "audio": {
            "data": base64.b64encode(audio_bytes).decode("ascii"),
            "format": audio_path.suffix.lower().lstrip(".") or "mp3",
        },
        "request": {
            "model_name": "bigmodel",
            "enable_itn": True,
            "enable_punc": True,
            "enable_ddc": False,
            "show_utterances": True,
            "enable_speaker_info": bool(num_speakers and num_speakers > 1),
        },
    }
    common_headers = {
        "X-Api-Key": api_key,
        "X-Api-Resource-Id": resource_id,
        "X-Api-Request-Id": request_id,
        "Content-Type": "application/json",
    }
    _, submit_headers = _api_request(
        SUBMIT_URL,
        payload,
        {**common_headers, "X-Api-Sequence": "-1"},
    )
    submit_status = submit_headers.get("x-api-status-code", "")
    if submit_status != "20000000":
        message = submit_headers.get("x-api-message", "")
        raise RuntimeError(f"Volcengine submit failed: status={submit_status or 'missing'} message={message}")

    query_headers = dict(common_headers)
    if submit_headers.get("x-tt-logid"):
        query_headers["X-Tt-Logid"] = submit_headers["x-tt-logid"]

    deadline = time.monotonic() + timeout
    while time.monotonic() <= deadline:
        time.sleep(poll_interval)
        result, response_headers = _api_request(QUERY_URL, {}, query_headers)
        query_status = response_headers.get("x-api-status-code", "")
        if query_status == "20000000":
            return result
        if query_status in {"", "20000001", "20000002"}:
            continue
        if query_status == "20000003":
            raise RuntimeError("Volcengine treated the audio as silent")
        message = response_headers.get("x-api-message", "")
        raise RuntimeError(f"Volcengine query failed: status={query_status} message={message}")
    raise RuntimeError(f"Volcengine ASR timed out after {timeout}s")


def normalize_volcengine_result(
    result: dict[str, Any],
    resource_id: str = DEFAULT_RESOURCE_ID,
    language: str | None = None,
) -> dict[str, Any]:
    root = result.get("result", result)
    utterances = root.get("utterances") if isinstance(root, dict) else None
    if not isinstance(utterances, list):
        raise RuntimeError("Volcengine response has no result.utterances")

    words: list[dict[str, Any]] = []
    previous_end: float | None = None
    for utterance in utterances:
        if not isinstance(utterance, dict):
            continue
        utterance_speaker = utterance.get("speaker_id", utterance.get("speaker"))
        for word in utterance.get("words") or []:
            if not isinstance(word, dict):
                continue
            text = str(word.get("text", "")).strip()
            start_raw = word.get("start_time")
            end_raw = word.get("end_time")
            if not text or start_raw is None or end_raw is None:
                continue
            start = float(start_raw) / 1000.0
            end = float(end_raw) / 1000.0
            if start < 0 or end < start:
                continue
            if previous_end is not None and start - previous_end >= 0.2:
                words.append({
                    "text": "",
                    "start": round(previous_end, 3),
                    "end": round(start, 3),
                    "type": "spacing",
                })
            normalized_word: dict[str, Any] = {
                "text": text,
                "start": round(start, 3),
                "end": round(end, 3),
                "type": "word",
            }
            speaker = word.get("speaker_id", word.get("speaker", utterance_speaker))
            if speaker is not None:
                normalized_word["speaker_id"] = str(speaker)
            words.append(normalized_word)
            previous_end = max(previous_end or 0.0, end)

    if not any(word.get("type") == "word" for word in words):
        raise RuntimeError("Volcengine response has no usable word timestamps")

    transcript_text = str(root.get("text", "")).strip() if isinstance(root, dict) else ""
    return {
        "provider": "volcengine",
        "resource_id": resource_id,
        "language_code": language,
        "text": transcript_text,
        "words": words,
        "raw_result": result,
    }


def transcribe_one(
    video: Path,
    edit_dir: Path,
    api_key: str,
    language: str | None = None,
    num_speakers: int | None = None,
    verbose: bool = True,
    poll_interval: int = 3,
    timeout: int = 900,
) -> Path:
    transcripts_dir = edit_dir / "transcripts"
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    out_path = transcripts_dir / f"{video.stem}.json"
    if out_path.exists():
        if verbose:
            print(f"cached: {out_path.name}")
        return out_path

    config, _ = load_config()
    resource_id = config.get("VOLCENGINE_RESOURCE_ID", DEFAULT_RESOURCE_ID)
    if verbose:
        print(f"  extracting audio from {video.name}", flush=True)

    started = time.time()
    with tempfile.TemporaryDirectory(prefix="video-use-volc-") as temp_name:
        audio = Path(temp_name) / f"{video.stem}.mp3"
        extract_audio(video, audio)
        if verbose:
            print(f"  submitting {audio.name} to Volcengine ASR", flush=True)
        raw_result = call_volcengine(
            audio,
            api_key,
            resource_id,
            num_speakers=num_speakers,
            poll_interval=poll_interval,
            timeout=timeout,
        )
    payload = normalize_volcengine_result(raw_result, resource_id, language)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if verbose:
        elapsed = time.time() - started
        word_count = sum(1 for word in payload["words"] if word.get("type") == "word")
        print(f"  saved: {out_path.name} ({word_count} words) in {elapsed:.1f}s")
    return out_path


def doctor() -> int:
    config, env_file = load_config()
    checks = {
        "ffmpeg": shutil.which("ffmpeg") is not None,
        "ffprobe": shutil.which("ffprobe") is not None,
        "volcengine_api_key": bool(config.get("VOLCENGINE_API_KEY")),
        "resource_id": config.get("VOLCENGINE_RESOURCE_ID", DEFAULT_RESOURCE_ID),
        "env_file": str(env_file) if env_file else None,
    }
    checks["ready"] = bool(checks["ffmpeg"] and checks["ffprobe"] and checks["volcengine_api_key"])
    print(json.dumps(checks, ensure_ascii=False, indent=2))
    return 0 if checks["ready"] else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Transcribe video with Volcengine word timestamps")
    parser.add_argument("video", type=Path, nargs="?", help="Path to video file")
    parser.add_argument("--edit-dir", type=Path, default=None)
    parser.add_argument("--language", type=str, default=None)
    parser.add_argument("--num-speakers", type=int, default=None)
    parser.add_argument("--poll-interval", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--doctor", action="store_true")
    args = parser.parse_args()

    if args.doctor:
        raise SystemExit(doctor())
    if not args.video:
        parser.error("video is required unless --doctor is used")
    video = args.video.expanduser().resolve()
    if not video.is_file():
        sys.exit(f"video not found: {video}")
    edit_dir = (args.edit_dir or (video.parent / "edit")).expanduser().resolve()
    transcribe_one(
        video=video,
        edit_dir=edit_dir,
        api_key=load_api_key(),
        language=args.language,
        num_speakers=args.num_speakers,
        poll_interval=args.poll_interval,
        timeout=args.timeout,
    )


if __name__ == "__main__":
    main()
