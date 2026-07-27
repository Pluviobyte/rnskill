# 解析 VOLCENGINE_API_KEY —— 与具体 agent / 安装位置无关。
#
# 查找顺序：
#   1) 环境变量 $VOLCENGINE_API_KEY
#   2) $VOLCENGINE_ENV_FILE 指定的 .env
#   3) <skill 目录>/.env          （推荐：跟着 skill 走，换 agent 也不丢）
#   4) <skill 目录的上一级>/.env   （兼容 Claude Code 旧约定 ~/.claude/skills/.env）
#
# 调用方需先设置 SCRIPT_DIR=脚本所在目录；source 本文件后 $API_KEY 可用，找不到则退出 1。

_skill_dir="$(dirname "$SCRIPT_DIR")"
API_KEY="${VOLCENGINE_API_KEY:-}"

if [ -z "$API_KEY" ]; then
  for _ef in "${VOLCENGINE_ENV_FILE:-}" "$_skill_dir/.env" "$(dirname "$_skill_dir")/.env"; do
    [ -n "$_ef" ] && [ -f "$_ef" ] || continue
    API_KEY=$(grep '^VOLCENGINE_API_KEY=' "$_ef" | head -1 | cut -d'=' -f2- | tr -d '\r\n ')
    [ -n "$API_KEY" ] && break
  done
fi

if [ -z "$API_KEY" ]; then
  echo "❌ 没找到 VOLCENGINE_API_KEY" >&2
  echo "   方式一(推荐)：在 $_skill_dir/.env 写一行  VOLCENGINE_API_KEY=你的key" >&2
  echo "   方式二：运行前  export VOLCENGINE_API_KEY=你的key" >&2
  echo "   key 申请：https://console.volcengine.com/speech/new/overview" >&2
  exit 1
fi
