#!/usr/bin/env python3
# 构建火山引擎新版控制台（极速版 / 标准版）转录请求体，打印 JSON 到 stdout。
#
# 用法: python3 build_request.py <audio_file_or_url>
#   · 以 http(s):// 开头 → URL 模式（audio.url）
#   · 否则当本地文件 → base64 直传（audio.data）
#   · format 由扩展名推断，默认 mp3
#
# 极速版 / 标准版 请求体结构完全一致，差异只在 endpoint / resource-id / 同步还是轮询，
# 所以这里只有一份，避免两个脚本各抄一遍（历史上抄了导致字数统计三种写法、路径插值脆弱）。

import base64
import json
import os
import re
import sys

audio = sys.argv[1]

if re.match(r'^https?://', audio):
    ext = os.path.splitext(audio.split('?')[0])[1].lstrip('.').lower() or 'mp3'
    audio_field = {"url": audio, "format": ext}
else:
    ext = os.path.splitext(audio)[1].lstrip('.').lower() or 'mp3'
    with open(audio, "rb") as f:
        audio_field = {"data": base64.b64encode(f.read()).decode(), "format": ext}

req = {
    "user": {"uid": "ai_jiankoubo"},
    "audio": audio_field,
    "request": {
        "model_name": "bigmodel",
        "enable_itn": True,
        "enable_punc": False,
        "enable_ddc": False,
        "show_utterances": True,
        "enable_speaker_info": False,
    },
}

json.dump(req, sys.stdout)
