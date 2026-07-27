#!/usr/bin/env python3
"""Generate subtitle artifacts from final media using Volcengine word timestamps."""

from __future__ import annotations

import argparse
import base64
import difflib
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
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus"}
CAPTION_CONNECTORS = (
    "比如说", "第一个", "第二个", "第三个", "首先", "其次", "然后",
    "而且", "但是", "只是", "所以", "如果", "其实", "就是", "这个", "某个",
)


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            values[key] = value
    return values


def env_candidates(explicit: str | None) -> list[Path]:
    found: list[Path] = []
    if explicit:
        found.append(Path(explicit).expanduser())
    for origin in (Path.cwd(), Path(__file__).resolve()):
        current = origin if origin.is_dir() else origin.parent
        for parent in (current, *current.parents):
            candidate = parent / ".env"
            if candidate not in found:
                found.append(candidate)
    return found


def load_config(explicit_env: str | None) -> tuple[dict[str, str], Path | None]:
    config = dict(os.environ)
    used: Path | None = None
    for candidate in env_candidates(explicit_env):
        values = parse_env_file(candidate)
        if values:
            for key, value in values.items():
                config.setdefault(key, value)
            if "VOLCENGINE_API_KEY" in values and used is None:
                used = candidate
    return config, used


def normalize_chars(text: str) -> list[str]:
    return [char.casefold() for char in text if char.isalnum()]


def extract_markdown_narration(text: str) -> str | None:
    lines = []
    for raw in text.splitlines():
        match = re.match(r"^\s*-\s*口播[：:]\s*(.+?)\s*$", raw)
        if match:
            lines.append(match.group(1))
    return "\n".join(lines) if lines else None


def collect_narration(value: Any) -> list[str]:
    output: list[str] = []
    if isinstance(value, list):
        for item in value:
            output.extend(collect_narration(item))
    elif isinstance(value, dict):
        direct = value.get("narration")
        if isinstance(direct, str) and direct.strip():
            output.append(direct.strip())
        else:
            for key in ("segments", "scenes", "items"):
                if key in value:
                    output.extend(collect_narration(value[key]))
    return output


def load_script(path: str | None, inline: str | None) -> str | None:
    if inline:
        return inline.strip()
    if not path:
        return None
    script_path = Path(path).expanduser().resolve()
    raw = script_path.read_text(encoding="utf-8")
    if script_path.suffix.lower() == ".json":
        segments = collect_narration(json.loads(raw))
        if not segments:
            raise RuntimeError(f"No narration fields found in {script_path}")
        return "\n".join(segments)
    if script_path.suffix.lower() in {".md", ".markdown"}:
        extracted = extract_markdown_narration(raw)
        if extracted:
            return extracted
    return raw.strip()


def safe_caption_cut(text: str, max_chars: int) -> int:
    """Choose a balanced cut without breaking terms or discourse connectors."""
    if len(normalize_chars(text)) <= max_chars:
        return len(text)
    protected = [match.span() for match in re.finditer(r"[A-Za-z0-9.+/\-]+(?: [A-Za-z0-9.+/\-]+)*", text)]
    for phrase in CAPTION_CONNECTORS:
        protected.extend((match.start(), min(len(text), match.end() + 1)) for match in re.finditer(re.escape(phrase), text))

    total = len(normalize_chars(text))
    target = total / max(2, (total + max_chars - 1) // max_chars)
    candidates: list[tuple[float, int]] = []
    for cut in range(1, len(text)):
        if any(start < cut < end for start, end in protected):
            continue
        left = len(normalize_chars(text[:cut]))
        right = len(normalize_chars(text[cut:]))
        if left < 4 or right < 4 or left > max_chars + 2:
            continue
        priority = 3.0
        if text[cut - 1] in "，、；：,;:。？！!?":
            priority = 0.0
        elif any(text.startswith(phrase, cut) for phrase in CAPTION_CONNECTORS):
            priority = 0.5
        elif bool(re.match(r"[A-Za-z0-9]", text[cut:cut + 1])) != bool(re.match(r"[A-Za-z0-9]", text[cut - 1:cut])):
            priority = 1.5
        candidates.append((abs(left - target) + priority * 1.5, cut))
    if candidates:
        return min(candidates)[1]
    return min(max_chars, len(text))


def join_caption_chunks(left: str, right: str) -> str:
    separator = " " if re.search(r"[A-Za-z0-9]$", left) and re.match(r"^[A-Za-z0-9]", right) else ""
    return left.rstrip() + separator + right.lstrip()


def merge_short_chunks(chunks: list[str], max_chars: int) -> list[str]:
    merged = list(chunks)
    index = 0
    while index < len(merged):
        chunk = merged[index]
        length = reading_units(chunk)
        starts_forward = chunk.startswith(CAPTION_CONNECTORS)
        starts_ascii = bool(re.match(r"^[A-Za-z0-9]", chunk))
        needs_merge = length <= 4 or (starts_forward and length <= 6) or (starts_ascii and length <= 6)
        if not needs_merge or len(merged) == 1:
            index += 1
            continue
        options: list[tuple[int, int, str]] = []
        if index > 0:
            combined = join_caption_chunks(merged[index - 1], chunk)
            if len(normalize_chars(combined)) <= max_chars + 4:
                options.append((len(normalize_chars(combined)), index - 1, combined))
        if index + 1 < len(merged):
            combined = join_caption_chunks(chunk, merged[index + 1])
            if len(normalize_chars(combined)) <= max_chars + 4:
                preference = -100 if starts_forward or chunk in {"它和", "它做调研"} else 0
                options.append((len(normalize_chars(combined)) + preference, index, combined))
        if not options:
            index += 1
            continue
        _, target, combined = min(options)
        if target == index - 1:
            merged[index - 1:index + 1] = [combined]
            index = max(0, index - 1)
        else:
            merged[index:index + 2] = [combined]
    return merged


def split_connector_segments(text: str) -> list[str]:
    cuts = {0, len(text)}
    for phrase in CAPTION_CONNECTORS:
        for match in re.finditer(re.escape(phrase), text):
            if match.start() > 0 and len(normalize_chars(text[:match.start()])) >= 4:
                cuts.add(match.start())
    points = sorted(cuts)
    return [text[points[index]:points[index + 1]] for index in range(len(points) - 1) if text[points[index]:points[index + 1]]]


def split_caption_text(text: str, max_chars: int) -> list[str]:
    # Treat approved narration lines as soft caption boundaries and retain
    # meaningful spaces inside English product names such as "Claude Max".
    segments = []
    for item in re.split(r"[\r\n]+", text.strip()):
        cleaned = re.sub(r" {2,}", " ", item.strip())
        if cleaned:
            segments.extend(split_connector_segments(cleaned))
    if not segments:
        return []
    chunks: list[str] = []
    for segment in segments:
        sentences = [part for part in re.split(r"(?<=[。？！!?])", segment) if part]
        for sentence in sentences:
            pieces = [part for part in re.split(r"(?<=[，、；：,;:])", sentence) if part]
            buffer = ""
            for piece in pieces:
                while len(piece) > max_chars:
                    if buffer:
                        chunks.append(buffer.rstrip())
                        buffer = ""
                    cut = safe_caption_cut(piece, max_chars)
                    chunks.append(piece[:cut].strip())
                    piece = piece[cut:].lstrip()
                if not piece:
                    continue
                if buffer and len(buffer) + len(piece) > max_chars:
                    chunks.append(buffer.rstrip())
                    buffer = piece.lstrip()
                else:
                    buffer += piece
            if buffer:
                chunks.append(buffer.rstrip())

    return merge_short_chunks(chunks, max_chars)


def reading_units(text: str) -> float:
    units = 0.0
    for token in re.findall(r"[A-Za-z0-9.+/\-]+(?: [A-Za-z0-9.+/\-]+)*|[\u3400-\u9fff]|[^\s]", text):
        if re.fullmatch(r"[A-Za-z0-9.+/\-]+(?: [A-Za-z0-9.+/\-]+)*", token):
            units += 1.5
        elif re.fullmatch(r"[\u3400-\u9fff]", token):
            units += 1.0
        elif token not in "，、；：,;:。？！!?":
            units += 0.5
    return units


def media_duration(path: Path) -> float | None:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nk=1:nw=1", str(path)],
            capture_output=True,
            text=True,
            check=True,
        )
        return float(result.stdout.strip())
    except (FileNotFoundError, subprocess.CalledProcessError, ValueError):
        return None


def prepare_audio(media: Path, temp_dir: Path) -> Path:
    if media.suffix.lower() in AUDIO_EXTS and media.suffix.lower() in {".mp3", ".wav"}:
        return media
    output = temp_dir / "final-audio.mp3"
    try:
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", str(media), "-vn", "-ac", "1", "-ar", "16000", "-b:a", "64k", str(output)],
            check=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("ffmpeg is required to extract final audio") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"ffmpeg could not extract audio from {media}") from exc
    return output


def api_request(url: str, payload: dict[str, Any], headers: dict[str, str]) -> tuple[dict[str, Any], dict[str, str]]:
    request = Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=180) as response:
            body = response.read().decode("utf-8", errors="replace")
            return (json.loads(body) if body else {}), {key.lower(): value for key, value in response.headers.items()}
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Volcengine HTTP {exc.code}: {body[:500]}") from exc
    except URLError as exc:
        raise RuntimeError(f"Volcengine request failed: {exc.reason}") from exc


def transcribe(audio: Path, api_key: str, resource_id: str, poll_interval: int, timeout: int) -> dict[str, Any]:
    audio_bytes = audio.read_bytes()
    if len(audio_bytes) > 48 * 1024 * 1024:
        raise RuntimeError("Final audio is larger than 48 MB; compress it before direct ASR upload")
    request_id = str(uuid.uuid4())
    audio_format = audio.suffix.lower().lstrip(".") or "mp3"
    payload = {
        "user": {"uid": "ra-audio-to-subtitles"},
        "audio": {"data": base64.b64encode(audio_bytes).decode("ascii"), "format": audio_format},
        "request": {
            "model_name": "bigmodel",
            "enable_itn": True,
            "enable_punc": True,
            "enable_ddc": False,
            "show_utterances": True,
            "enable_speaker_info": False,
        },
    }
    common = {
        "X-Api-Key": api_key,
        "X-Api-Resource-Id": resource_id,
        "X-Api-Request-Id": request_id,
        "Content-Type": "application/json",
    }
    _, submit_headers = api_request(SUBMIT_URL, payload, {**common, "X-Api-Sequence": "-1"})
    status = submit_headers.get("x-api-status-code", "")
    if status != "20000000":
        raise RuntimeError(f"Volcengine submit failed: status={status or 'missing'} message={submit_headers.get('x-api-message', '')}")
    log_id = submit_headers.get("x-tt-logid")
    query_headers = dict(common)
    if log_id:
        query_headers["X-Tt-Logid"] = log_id

    deadline = time.monotonic() + timeout
    while time.monotonic() <= deadline:
        time.sleep(poll_interval)
        result, response_headers = api_request(QUERY_URL, {}, query_headers)
        status = response_headers.get("x-api-status-code", "")
        if status == "20000000":
            return result
        if status in {"20000001", "20000002", ""}:
            continue
        if status == "20000003":
            raise RuntimeError("Volcengine treated the final audio as silent")
        raise RuntimeError(f"Volcengine query failed: status={status} message={response_headers.get('x-api-message', '')}")
    raise RuntimeError(f"Volcengine ASR timed out after {timeout}s")


def milliseconds(value: Any) -> float:
    number = float(value)
    return number / 1000.0


def extract_word_units(result: dict[str, Any]) -> list[dict[str, Any]]:
    root = result.get("result", result)
    utterances = root.get("utterances") if isinstance(root, dict) else None
    if not isinstance(utterances, list):
        raise RuntimeError("Volcengine response has no result.utterances")
    words: list[dict[str, Any]] = []
    for utterance in utterances:
        if not isinstance(utterance, dict):
            continue
        for word in utterance.get("words") or []:
            if not isinstance(word, dict):
                continue
            text = str(word.get("text", "")).strip()
            start_raw = word.get("start_time")
            end_raw = word.get("end_time")
            if not text or start_raw is None or end_raw is None:
                continue
            if float(start_raw) < 0 or float(end_raw) < 0:
                continue
            start, end = milliseconds(start_raw), milliseconds(end_raw)
            if end < start:
                continue
            words.append({"text": text, "start": round(start, 3), "end": round(end, 3), "isGap": False})
    words.sort(key=lambda item: (item["start"], item["end"]))
    if not words:
        raise RuntimeError("Volcengine response has no usable word timestamps")
    return words


def words_with_gaps(words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    last_end = 0.0
    for word in words:
        if word["start"] - last_end >= 0.2:
            output.append({"text": "", "start": round(last_end, 3), "end": word["start"], "isGap": True})
        output.append(word)
        last_end = max(last_end, word["end"])
    return output


def expand_asr_characters(words: list[dict[str, Any]]) -> tuple[list[str], list[dict[str, float]]]:
    characters: list[str] = []
    timings: list[dict[str, float]] = []
    for word in words:
        normalized = normalize_chars(word["text"])
        if not normalized:
            continue
        duration = max(0.001, word["end"] - word["start"])
        for index, char in enumerate(normalized):
            start = word["start"] + duration * index / len(normalized)
            end = word["start"] + duration * (index + 1) / len(normalized)
            characters.append(char)
            timings.append({"start": start, "end": end})
    if not characters:
        raise RuntimeError("ASR words could not be normalized into timing characters")
    return characters, timings


def align_script(script_chars: list[str], asr_chars: list[str]) -> tuple[list[int], int]:
    matcher = difflib.SequenceMatcher(a=script_chars, b=asr_chars, autojunk=False)
    mapping: list[int | None] = [None] * len(script_chars)
    matched = 0
    for block in matcher.get_matching_blocks():
        if block.size == 0:
            continue
        matched += block.size
        for offset in range(block.size):
            mapping[block.a + offset] = block.b + offset

    anchors = [index for index, value in enumerate(mapping) if value is not None]
    if not anchors:
        raise RuntimeError("Original script and ASR text have no alignable characters")
    for index, value in enumerate(mapping):
        if value is not None:
            continue
        left = next((pos for pos in reversed(anchors) if pos < index), None)
        right = next((pos for pos in anchors if pos > index), None)
        if left is None:
            right_value = mapping[right] if right is not None else 0
            predicted = max(0, int(right_value) - (right - index if right is not None else 0))
        elif right is None:
            predicted = min(len(asr_chars) - 1, int(mapping[left]) + index - left)
        else:
            left_value, right_value = int(mapping[left]), int(mapping[right])
            fraction = (index - left) / (right - left)
            predicted = round(left_value + (right_value - left_value) * fraction)
        mapping[index] = max(0, min(len(asr_chars) - 1, predicted))

    resolved = [int(value) for value in mapping]
    for index in range(1, len(resolved)):
        if resolved[index] < resolved[index - 1]:
            resolved[index] = resolved[index - 1]
    return resolved, matched


def build_captions(script: str, mapping: list[int], asr_timings: list[dict[str, float]], max_chars: int) -> list[dict[str, Any]]:
    chunks = split_caption_text(script, max_chars)
    script_count = len(normalize_chars(script))
    chunk_count = sum(len(normalize_chars(chunk)) for chunk in chunks)
    if chunk_count != script_count:
        raise RuntimeError(f"Caption splitting lost script characters: script={script_count}, chunks={chunk_count}")

    captions: list[dict[str, Any]] = []
    cursor = 0
    for chunk in chunks:
        length = len(normalize_chars(chunk))
        if length == 0:
            continue
        start_index = mapping[cursor]
        end_index = mapping[cursor + length - 1]
        start = asr_timings[start_index]["start"]
        end = asr_timings[end_index]["end"]
        captions.append({
            "start": round(start, 3),
            "end": round(max(start + 0.05, end), 3),
            "text": chunk,
            "source": "volcengine-word-timestamps",
        })
        cursor += length

    for index, caption in enumerate(captions):
        next_start = captions[index + 1]["start"] if index + 1 < len(captions) else None
        desired = max(caption["end"] + 0.12, caption["start"] + 0.6)
        if next_start is not None:
            caption["end"] = round(max(caption["end"], min(desired, next_start - 0.03)), 3)
            if caption["end"] > next_start:
                caption["end"] = round(next_start, 3)
        else:
            caption["end"] = round(desired, 3)
    return captions


def timestamp(seconds: float, separator: str) -> str:
    total_ms = max(0, round(seconds * 1000))
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{separator}{millis:03d}"


def subtitle_text(captions: list[dict[str, Any]], vtt: bool) -> str:
    blocks = []
    for index, caption in enumerate(captions, 1):
        line = f"{timestamp(caption['start'], '.' if vtt else ',')} --> {timestamp(caption['end'], '.' if vtt else ',')}\n{caption['text']}"
        blocks.append(line if vtt else f"{index}\n{line}")
    prefix = "WEBVTT\n\n" if vtt else ""
    return prefix + "\n\n".join(blocks) + "\n"


def split_connector_boundaries(captions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings = []
    for index in range(len(captions) - 1):
        left, right = captions[index]["text"], captions[index + 1]["text"]
        for phrase in CAPTION_CONNECTORS:
            if any(left.endswith(phrase[:cut]) and right.startswith(phrase[cut:]) for cut in range(1, len(phrase))):
                findings.append({"after_caption": index + 1, "phrase": phrase})
    return findings


def build_qc(
    script_chars: list[str],
    asr_chars: list[str],
    matched: int,
    words: list[dict[str, Any]],
    captions: list[dict[str, Any]],
    media: Path,
    resource_id: str,
    min_coverage: float,
    duration: float | None,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    coverage = matched / len(script_chars) if script_chars else 0.0
    overlap_count = 0
    reading_speeds = []
    short_fragments = []
    for index, caption in enumerate(captions):
        caption_duration = caption["end"] - caption["start"]
        if caption["end"] <= caption["start"]:
            errors.append(f"caption {index + 1} has non-positive duration")
        if 0 < caption_duration < 0.5:
            errors.append(f"caption {index + 1} is shorter than 0.5s")
        units = reading_units(caption["text"])
        speed = units / max(caption_duration, 0.001)
        reading_speeds.append(speed)
        if units <= 1.5 and caption_duration < 0.8:
            short_fragments.append({"caption": index + 1, "text": caption["text"], "duration": round(caption_duration, 3)})
        if index and caption["start"] < captions[index - 1]["end"] - 0.001:
            overlap_count += 1
    connector_splits = split_connector_boundaries(captions)
    if coverage < min_coverage:
        errors.append(f"alignment coverage {coverage:.4f} is below {min_coverage:.4f}")
    if overlap_count:
        errors.append(f"{overlap_count} caption overlaps detected")
    if short_fragments:
        errors.append(f"{len(short_fragments)} isolated short caption fragments detected")
    if connector_splits:
        errors.append(f"{len(connector_splits)} discourse connectors split across captions")
    if reading_speeds and max(reading_speeds) > 12.0:
        errors.append(f"maximum reading speed {max(reading_speeds):.2f} units/s exceeds 12.0")
    elif reading_speeds and max(reading_speeds) > 9.0:
        warnings.append(f"maximum reading speed {max(reading_speeds):.2f} units/s exceeds preferred 9.0")
    if duration is not None and captions and captions[-1]["end"] > duration + 0.5:
        errors.append(f"last caption ends after media duration: {captions[-1]['end']:.3f}s > {duration:.3f}s")
    if not captions:
        errors.append("no captions generated")
    return {
        "status": "fail" if errors else "pass",
        "timing_source": "volcengine-word-timestamps",
        "alignment_coverage": round(coverage, 6),
        "minimum_coverage": min_coverage,
        "script_characters": len(script_chars),
        "matched_characters": matched,
        "asr_characters": len(asr_chars),
        "word_units": len(words),
        "caption_count": len(captions),
        "overlap_count": overlap_count,
        "max_reading_units_per_second": round(max(reading_speeds), 3) if reading_speeds else 0.0,
        "short_fragments": short_fragments,
        "split_connectors": connector_splits,
        "media_duration": duration,
        "source_media": str(media),
        "asr_resource_id": resource_id,
        "warnings": warnings,
        "errors": errors,
    }


def doctor(args: argparse.Namespace) -> int:
    config, env_file = load_config(args.env_file)
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("media", nargs="?", help="final audio or final merged video")
    parser.add_argument("--script", help="narration JSON, Markdown handoff, or plain text file")
    parser.add_argument("--script-text", help="inline narration text")
    parser.add_argument("--out-dir", default="media/captions")
    parser.add_argument("--asr-result", help="reuse an existing Volcengine result instead of calling the API")
    parser.add_argument("--env-file")
    parser.add_argument("--resource-id")
    parser.add_argument("--poll-interval", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--max-chars", type=int, default=22)
    parser.add_argument("--min-coverage", type=float, default=0.90)
    parser.add_argument("--doctor", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.doctor:
        return doctor(args)
    if not args.media:
        raise RuntimeError("media is required unless --doctor is used")
    media = Path(args.media).expanduser().resolve()
    if not media.is_file():
        raise RuntimeError(f"Final media does not exist: {media}")
    if not 0 < args.min_coverage <= 1:
        raise RuntimeError("--min-coverage must be between 0 and 1")

    config, _ = load_config(args.env_file)
    resource_id = args.resource_id or config.get("VOLCENGINE_RESOURCE_ID", DEFAULT_RESOURCE_ID)
    script = load_script(args.script, args.script_text)
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="ra-captions-") as temp_name:
        audio = prepare_audio(media, Path(temp_name))
        if args.asr_result:
            result_path = Path(args.asr_result).expanduser().resolve()
            result = json.loads(result_path.read_text(encoding="utf-8"))
        else:
            api_key = config.get("VOLCENGINE_API_KEY")
            if not api_key:
                raise RuntimeError("VOLCENGINE_API_KEY is missing from the environment or workspace .env")
            result = transcribe(audio, api_key, resource_id, args.poll_interval, args.timeout)

    raw_words = extract_word_units(result)
    asr_chars, asr_timings = expand_asr_characters(raw_words)
    if not script:
        root = result.get("result", result)
        script = str(root.get("text", "")).strip() if isinstance(root, dict) else ""
    script_chars = normalize_chars(script or "")
    if not script_chars:
        raise RuntimeError("No usable narration script was provided or returned by ASR")
    mapping, matched = align_script(script_chars, asr_chars)
    captions = build_captions(script or "", mapping, asr_timings, args.max_chars)
    duration = media_duration(media)
    qc = build_qc(script_chars, asr_chars, matched, raw_words, captions, media, resource_id, args.min_coverage, duration)

    (out_dir / "asr-result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "captions_words.json").write_text(json.dumps(words_with_gaps(raw_words), ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "captions.json").write_text(json.dumps(captions, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "captions.srt").write_text(subtitle_text(captions, vtt=False), encoding="utf-8")
    (out_dir / "captions.vtt").write_text(subtitle_text(captions, vtt=True), encoding="utf-8")
    (out_dir / "caption-qc.json").write_text(json.dumps(qc, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "status": qc["status"],
        "out_dir": str(out_dir),
        "alignment_coverage": qc["alignment_coverage"],
        "caption_count": qc["caption_count"],
        "word_units": qc["word_units"],
        "errors": qc["errors"],
    }, ensure_ascii=False, indent=2))
    return 0 if qc["status"] == "pass" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
