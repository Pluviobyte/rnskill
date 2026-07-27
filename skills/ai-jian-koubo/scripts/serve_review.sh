#!/bin/bash
#
# 启动审核服务器 —— 关键点：让它跑在一个【独立、由操作系统拥有的终端】里，
# 而不是调用方 agent 的后台进程里。
#
# 为什么这么做：
#   审核网页需要这个本地 Node 服务一直监听端口。不同 agent 对后台进程的处理不同：
#     · Claude Code 有常驻进程管理器，会在整个会话期间替你保活后台进程 → 从不出问题；
#     · 某些 agent（如 Codex）把每条命令放在临时子进程/沙箱里，命令一返回就回收整棵
#       进程树（连 nohup / disown 的子进程也一起杀）→ 端口失联，浏览器报「拒绝连接」。
#   所以这里不再依赖 agent 保活，而是在 OS 层另起一个终端窗口前台运行服务器：
#     · macOS  ：写一个可双击的 .command 文件并用 open 打开（Terminal.app 拥有它）
#     · Linux  ：调用已安装的终端模拟器 + setsid 脱离
#     · Windows：Git Bash 下用 start 起一个新 cmd 窗口
#   无论哪种，最后都会【再打印一条手动命令兜底】——万一环境禁止开新窗口，用户照着在
#   自己的终端里跑一次即可（这条路任何环境都成立）。
#
# 用法: serve_review.sh <review_dir> <video_path> <server_js> [port|auto]
#   环境变量 SERVE_REVIEW_NO_SPAWN=1 → 跳过自动开窗，只写启动脚本并打印手动命令（测试/受限环境用）
#

set -e

REVIEW_DIR="$1"
VIDEO="$2"
SERVER_JS="$3"
WANT_PORT="${4:-auto}"

[ -d "$REVIEW_DIR" ] || { echo "❌ 审核目录不存在: $REVIEW_DIR"; exit 1; }
[ -f "$VIDEO" ]      || { echo "❌ 视频文件不存在: $VIDEO"; exit 1; }
[ -f "$SERVER_JS" ]  || { echo "❌ 找不到 review_server.js: $SERVER_JS"; exit 1; }

NODE_BIN="$(command -v node || true)"
[ -n "$NODE_BIN" ] || { echo "❌ 找不到 node，请先安装"; exit 1; }

port_busy() { lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1; }

if [ "$WANT_PORT" = "auto" ]; then
  PORT=""
  for p in 8899 8900 8901 8902; do port_busy "$p" || { PORT="$p"; break; }; done
  [ -n "$PORT" ] || { echo "❌ 端口 8899-8902 都被占用"; exit 1; }
else
  PORT="$WANT_PORT"
fi
URL="http://localhost:$PORT"

# ── 单一来源：把「前台启动服务器」写成一个可直接运行 / 双击的脚本 ──────────
# 所有启动方式（自动开窗、手动兜底）都指向这一个文件，避免到处拼引号、漂移。
case "$(uname -s)" in
  Darwin) LAUNCHER="$REVIEW_DIR/启动审核服务.command" ;;  # macOS 双击默认用 Terminal 打开
  *)      LAUNCHER="$REVIEW_DIR/启动审核服务.sh" ;;
esac
{
  printf '%s\n' '#!/bin/bash'
  printf '%s\n' '# 双击 / 运行本文件即可（重新）启动审核服务器；审核完直接关掉这个终端窗口即停止。'
  printf 'cd "%s" || exit 1\n' "$REVIEW_DIR"
  printf 'exec "%s" "%s" %s "%s"\n' "$NODE_BIN" "$SERVER_JS" "$PORT" "$VIDEO"
} > "$LAUNCHER"
chmod +x "$LAUNCHER"

# ── 尝试在 OS 层另起一个终端窗口前台运行 ────────────────────────────────
SPAWNED=0
if [ -z "$SERVE_REVIEW_NO_SPAWN" ]; then
  case "$(uname -s)" in
    Darwin)
      open "$LAUNCHER" && SPAWNED=1
      ;;
    Linux)
      for t in x-terminal-emulator gnome-terminal konsole xfce4-terminal xterm; do
        command -v "$t" >/dev/null 2>&1 || continue
        setsid "$t" -e bash "$LAUNCHER" >/dev/null 2>&1 && { SPAWNED=1; break; }
      done
      ;;
    MINGW*|MSYS*|CYGWIN*)
      cmd.exe /c start "审核服务器" bash "$LAUNCHER" >/dev/null 2>&1 && SPAWNED=1
      ;;
  esac
fi

# ── 健康检查（只在确实尝试开窗后才轮询）──────────────────────────────────
# 不带 -f：连得上就算就绪，不纠结 HTTP 状态码
READY=0
if [ "$SPAWNED" = 1 ]; then
  for _ in $(seq 1 16); do
    sleep 0.5
    if curl -sS "$URL/" -o /dev/null 2>&1; then READY=1; break; fi
  done
fi

echo
if [ "$READY" = 1 ]; then
  echo "✅ 审核服务器已在【独立终端窗口】运行: $URL"
  open "$URL" 2>/dev/null || xdg-open "$URL" 2>/dev/null || start "" "$URL" 2>/dev/null || true
  echo "   · 审核完成后，关掉那个终端窗口即可停止服务"
  echo "   · 下次重启：双击或运行  $LAUNCHER"
else
  echo "⚠️ 没能自动开启独立终端（环境可能禁止开新窗口）。"
  echo "   请手动打开一个终端，运行下面这条并【保持窗口开着】，然后访问 $URL ："
  echo
  echo "      bash \"$LAUNCHER\""
fi
