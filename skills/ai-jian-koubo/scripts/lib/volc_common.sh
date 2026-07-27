# 火山引擎新版控制台（极速版 flash / 标准版 auc）共用函数。
# 极速版与标准版只在 endpoint / resource-id / 同步直出还是 submit-query 轮询上不同，
# 其余（请求体构建、状态头解析、字数统计、request-id）完全一致，统一收敛到这里。
#
# 调用前需先 source load_api_key.sh，并设置 SCRIPT_DIR=本脚本所在目录（scripts/）。

# 小写 UUID 作为 X-Api-Request-Id（提交/查询复用同一个）
volc_gen_request_id() {
  local id
  id=$(uuidgen 2>/dev/null || python3 -c "import uuid; print(uuid.uuid4())")
  printf '%s' "$id" | tr '[:upper:]' '[:lower:]'
}

# volc_build_request <audio_file_or_url> <out_file>：写请求体 JSON 到 out_file
volc_build_request() {
  python3 "$SCRIPT_DIR/lib/build_request.py" "$1" > "$2"
}

# volc_header <headers_file> <header-name>：取响应头的值（大小写不敏感，取首个空格后全部）
volc_header() {
  grep -i "^$2:" "$1" | tail -1 | tr -d '\r' | cut -d' ' -f2-
}

# volc_status <headers_file>：取 X-Api-Status-Code（数字）。标准版/极速版状态都在响应头，不在 body。
volc_status() {
  grep -i '^x-api-status-code:' "$1" | tail -1 | tr -d '\r' | awk '{print $2}'
}

# volc_word_count <result_json>：打印 "N utterances / M 字"，解析失败回退 "?"
volc_word_count() {
  python3 - "$1" <<'PY' 2>/dev/null || echo "?"
import json, sys
d = json.load(open(sys.argv[1]))
r = d.get("result", {})
print("%d utterances / %d 字" % (len(r.get("utterances", []) or []), len(r.get("text", "") or "")))
PY
}
