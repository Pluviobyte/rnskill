"""MiniMax TTS helper retained for relay-station article/demo integrations.

The public function intentionally matches the older local helper API used by
existing demo scripts: ``text_to_audio(...)`` returns a dict with ``success``
and writes the generated audio file to ``output_path``. Local video production
must use IndexTTS2 instead of this helper.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


API_URL = os.environ.get("MINIMAX_TTS_API_URL", "https://api.minimax.io/v1/t2a_v2")


def _clean_format(fmt: str) -> str:
    value = (fmt or "mp3").lower().lstrip(".")
    if value == "mpeg":
        return "mp3"
    return value


def _request(payload: dict[str, Any], api_key: str) -> dict[str, Any]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {"success": False, "error": f"HTTP {exc.code}: {body}"}
    except Exception as exc:  # noqa: BLE001 - return errors to the caller.
        return {"success": False, "error": str(exc)}

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"success": False, "error": f"Invalid JSON response: {raw[:500]}"}


def text_to_audio(
    *,
    text: str,
    voice_id: str,
    output_path: str,
    model: str = "speech-02-hd",
    speed: float = 1.0,
    vol: float = 1.0,
    pitch: int = 0,
    emotion: str | None = None,
    format: str = "mp3",
    sample_rate: int = 32000,
    bitrate: int = 128000,
    **_: Any,
) -> dict[str, Any]:
    api_key = os.environ.get("MINIMAX_API_KEY")
    if not api_key:
        return {"success": False, "error": "Missing MINIMAX_API_KEY"}
    if not text.strip():
        return {"success": False, "error": "Empty text"}
    if not voice_id.strip():
        return {"success": False, "error": "Empty voice_id"}

    audio_format = _clean_format(format)
    payload: dict[str, Any] = {
        "model": model,
        "text": text,
        "stream": False,
        "output_format": "hex",
        "voice_setting": {
            "voice_id": voice_id,
            "speed": speed,
            "vol": vol,
            "pitch": pitch,
        },
        "audio_setting": {
            "sample_rate": sample_rate,
            "bitrate": bitrate,
            "format": audio_format,
            "channel": 1,
        },
    }
    if emotion:
        payload["emotion"] = emotion

    response = _request(payload, api_key)
    if response.get("success") is False and "error" in response:
        return response

    base_resp = response.get("base_resp") or {}
    status_code = base_resp.get("status_code", 0)
    if status_code not in (0, "0", None):
        return {
            "success": False,
            "error": base_resp.get("status_msg") or json.dumps(base_resp, ensure_ascii=False),
            "response": response,
        }

    data = response.get("data") or {}
    audio_hex = data.get("audio")
    if not audio_hex:
        return {"success": False, "error": "Response did not contain data.audio", "response": response}

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        out.write_bytes(bytes.fromhex(audio_hex))
    except ValueError as exc:
        return {"success": False, "error": f"Invalid audio hex: {exc}", "response": response}

    return {
        "success": True,
        "path": str(out),
        "voice_id": voice_id,
        "model": model,
        "format": audio_format,
        "trace_id": response.get("trace_id"),
        "extra_info": response.get("extra_info"),
    }
