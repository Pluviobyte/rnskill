#!/usr/bin/env node
/**
 * 生成审核网页（视频版本）
 *
 * 用法: node generate_review.js <subtitles_words.json> [auto_selected.json] [video_file]
 * 输出: review.html, video.mp4（符号链接到当前目录）
 */

const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const subtitlesFile = process.argv[2] || 'subtitles_words.json';
const autoSelectedFile = process.argv[3] || 'auto_selected.json';
const videoFile = process.argv[4] || 'video.mp4';

// 创建视频文件的符号链接到当前目录（避免复制大文件）
const videoBaseName = 'video.mp4';
if (videoFile !== videoBaseName && fs.existsSync(videoFile)) {
  const absVideoPath = path.resolve(videoFile);
  if (fs.existsSync(videoBaseName)) fs.unlinkSync(videoBaseName);
  fs.symlinkSync(absVideoPath, videoBaseName);
  console.log('📁 已链接视频到当前目录:', videoBaseName, '→', absVideoPath);
}

if (!fs.existsSync(subtitlesFile)) {
  console.error('❌ 找不到字幕文件:', subtitlesFile);
  process.exit(1);
}

const words = JSON.parse(fs.readFileSync(subtitlesFile, 'utf8'));
let autoSelected = [];

if (fs.existsSync(autoSelectedFile)) {
  autoSelected = JSON.parse(fs.readFileSync(autoSelectedFile, 'utf8'));
  console.log('AI 预选:', autoSelected.length, '个元素');
}

function readVideoAspectRatio(file) {
  const target = fs.existsSync(file) ? file : videoBaseName;
  try {
    const output = execFileSync('ffprobe', [
      '-v', 'error',
      '-select_streams', 'v:0',
      '-show_entries', 'stream=width,height',
      '-of', 'csv=p=0',
      target,
    ], { encoding: 'utf8' }).trim();
    const [width, height] = output.split(',').map(Number);
    if (width > 0 && height > 0) return `${width} / ${height}`;
  } catch (e) {
    console.warn('⚠️ 未能读取视频比例，使用默认竖屏比例 9:16');
  }
  return '9 / 16';
}

const videoAspectRatio = readVideoAspectRatio(videoFile);

const html = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>剪口播 · 审核稿</title>
  <style>
    :root {
      --bg-canvas: #f7f6f3;
      --bg-surface: #ffffff;
      --bg-muted: #f4f3f0;
      --bg-subtle: #fafaf8;
      --border: rgba(15, 15, 15, 0.08);
      --divider: rgba(15, 15, 15, 0.055);
      --text: #191918;
      --text-muted: #6b6b67;
      --text-faint: #9a9a95;
      --accent: #0f7b6c;
      --accent-soft: #e6f2ef;
      --accent-text: #0a5d50;
      --deleted-bg: #fbe9e7;
      --deleted-fg: #b43c2a;
      --highlight-bg: #fef0c7;
      --highlight-fg: #7c5a10;
      --font-body: "PingFang SC", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      --font-mono: "SF Mono", "JetBrains Mono", "Menlo", monospace;
      --sidebar-w: clamp(460px, 42vw, 600px);
      --header-h: 44px;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: var(--font-body);
      background: var(--bg-canvas);
      color: var(--text);
      height: 100vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      -webkit-font-smoothing: antialiased;
    }

    /* ─── Header ─── */
    .header {
      height: var(--header-h);
      background: var(--bg-surface);
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 16px;
      flex-shrink: 0;
      z-index: 10;
    }
    .header-left {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 14px;
      font-weight: 500;
      color: var(--text);
      min-width: 0;
    }
    .header-left .logo {
      font-size: 15px;
      display: flex;
      align-items: center;
      gap: 6px;
      white-space: nowrap;
    }
    .header-left .logo .icon { font-size: 16px; }
    .header-left .badge {
      font-size: 11px;
      font-weight: 500;
      background: var(--accent-soft);
      color: var(--accent-text);
      padding: 2px 8px;
      border-radius: 10px;
    }
    .header-right {
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .header-btn {
      height: 28px;
      padding: 0 10px;
      border: none;
      border-radius: 6px;
      font-size: 13px;
      font-family: var(--font-body);
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      background: transparent;
      color: var(--text-muted);
      transition: background 0.12s;
    }
    .header-btn:hover { background: var(--bg-muted); color: var(--text); }
    .header-btn.primary {
      background: var(--accent);
      color: #fff;
      font-weight: 500;
    }
    .header-btn.primary:hover { background: #0d6b5e; }
    select.speed-select {
      height: 28px;
      padding: 0 6px;
      border: 1px solid var(--border);
      border-radius: 6px;
      font-size: 12px;
      font-family: var(--font-mono);
      background: var(--bg-surface);
      color: var(--text-muted);
      cursor: pointer;
      outline: none;
    }
    select.speed-select:hover { border-color: rgba(15,15,15,0.15); }
    .transport-speed {
      margin-left: 2px;
      flex-shrink: 0;
    }

    /* ─── Main layout ─── */
    .main {
      display: flex;
      flex: 1;
      overflow: hidden;
    }

    /* ─── Left Sidebar ─── */
    .sidebar {
      width: var(--sidebar-w);
      flex-shrink: 0;
      background: var(--bg-surface);
      border-right: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      overflow-y: auto;
    }
    .sidebar-section {
      padding: 12px 14px;
    }
    .sidebar-section + .sidebar-section {
      border-top: 1px solid var(--divider);
    }

    /* Video */
    .video-wrap {
      padding: 10px 10px 0;
    }
    #player {
      width: 100%;
      aspect-ratio: ${videoAspectRatio};
      object-fit: contain;
      border-radius: 8px;
      background: #000;
      display: block;
    }

    /* Transport row */
    .transport {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 10px 14px;
    }
    .transport-btn {
      width: 30px;
      height: 30px;
      border: none;
      border-radius: 6px;
      background: var(--bg-muted);
      color: var(--text-muted);
      font-size: 14px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: background 0.12s;
    }
    .transport-btn:hover { background: #eae9e5; color: var(--text); }
    .transport-btn.playing { background: var(--accent-soft); color: var(--accent); }
    #time {
      font-family: var(--font-mono);
      font-size: 13px;
      color: var(--text-muted);
      margin-left: auto;
    }

    /* Cards */
    .card {
      background: var(--bg-subtle);
      border-radius: 8px;
      padding: 12px;
    }
    .card-title {
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-faint);
      margin-bottom: 10px;
    }

    /* Clip preview card */
    .clip-row {
      display: flex;
      align-items: baseline;
      gap: 6px;
      margin-bottom: 8px;
    }
    .clip-time-big {
      font-size: 22px;
      font-weight: 600;
      font-family: var(--font-mono);
      color: var(--accent);
    }
    .clip-arrow {
      font-size: 14px;
      color: var(--text-faint);
    }
    .clip-time-old {
      font-size: 15px;
      font-family: var(--font-mono);
      color: var(--text-muted);
      text-decoration: line-through;
      text-decoration-color: var(--text-faint);
    }
    .clip-bar-wrap {
      height: 6px;
      border-radius: 3px;
      background: var(--deleted-bg);
      overflow: hidden;
      margin-bottom: 6px;
    }
    .clip-bar-keep {
      height: 100%;
      background: var(--accent);
      border-radius: 3px;
      transition: width 0.3s;
    }
    .clip-saved {
      font-size: 12px;
      color: var(--text-muted);
    }
    .clip-saved b { color: var(--accent-text); font-weight: 600; }

    /* Keyboard hints */
    kbd {
      display: inline-block;
      font-family: var(--font-mono);
      font-size: 11px;
      background: var(--bg-muted);
      border: 1px solid var(--border);
      border-radius: 4px;
      padding: 1px 5px;
      color: var(--text);
      white-space: nowrap;
    }

    .shortcut-strip {
      min-height: 42px;
      background: var(--bg-surface);
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      gap: 14px;
      padding: 7px 16px;
      flex-shrink: 0;
      overflow-x: auto;
    }
    .shortcut-title {
      font-size: 12px;
      font-weight: 600;
      color: var(--text);
      white-space: nowrap;
    }
    .shortcut-list {
      display: flex;
      align-items: center;
      gap: 12px;
      min-width: 0;
    }
    .shortcut-item {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      font-size: 12px;
      color: var(--text-muted);
      white-space: nowrap;
    }
    .shortcut-item.primary {
      color: var(--accent-text);
      font-weight: 500;
    }
    .shortcut-item.primary kbd {
      background: var(--accent-soft);
      border-color: transparent;
      color: var(--accent-text);
    }

    /* ─── Right panel ─── */
    .right-panel {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    /* Filter bar */
    .filter-bar {
      height: 40px;
      background: var(--bg-surface);
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      padding: 0 16px;
      gap: 6px;
      flex-shrink: 0;
      overflow-x: auto;
    }
    .filter-bar::-webkit-scrollbar,
    .shortcut-strip::-webkit-scrollbar { display: none; }
    .search-box {
      display: flex;
      align-items: center;
      gap: 6px;
      background: var(--bg-muted);
      border-radius: 6px;
      padding: 0 10px;
      height: 28px;
      font-size: 13px;
      color: var(--text-faint);
      cursor: text;
      min-width: 140px;
    }
    .search-box input {
      border: none;
      background: transparent;
      outline: none;
      font-size: 13px;
      font-family: var(--font-body);
      color: var(--text);
      width: 100%;
    }
    .search-box input::placeholder { color: var(--text-faint); }
    .search-box .hint {
      font-family: var(--font-mono);
      font-size: 10px;
      color: var(--text-faint);
      background: var(--bg-surface);
      border: 1px solid var(--border);
      border-radius: 3px;
      padding: 0 4px;
      line-height: 16px;
    }
    .filter-divider {
      width: 1px;
      height: 16px;
      background: var(--border);
      margin: 0 4px;
    }
    .filter-btn {
      height: 26px;
      padding: 0 10px;
      border: 1px solid var(--border);
      border-radius: 14px;
      background: var(--bg-surface);
      font-size: 12px;
      font-family: var(--font-body);
      color: var(--text-muted);
      cursor: pointer;
      transition: all 0.12s;
      white-space: nowrap;
    }
    .filter-btn:hover { background: var(--bg-muted); border-color: rgba(15,15,15,0.12); }
    .filter-btn.active { background: var(--accent-soft); color: var(--accent-text); border-color: transparent; }
    .filter-summary {
      margin-left: auto;
      font-size: 12px;
      color: var(--text-faint);
      font-family: var(--font-mono);
      white-space: nowrap;
    }

    /* Transcript body */
    .transcript-body {
      flex: 1;
      overflow-y: auto;
      padding: 16px 24px 60px;
    }
    .content {
      line-height: 2.4;
      max-width: 720px;
    }

    /* Chapter header */
    .chapter-header {
      display: flex;
      align-items: center;
      gap: 10px;
      margin: 24px 0 8px;
      user-select: none;
    }
    .chapter-header:first-child { margin-top: 0; }
    .chapter-num {
      font-family: var(--font-mono);
      font-size: 12px;
      font-weight: 600;
      color: var(--text-faint);
      background: var(--bg-muted);
      width: 24px;
      height: 24px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 6px;
      flex-shrink: 0;
    }
    .chapter-range {
      font-family: var(--font-mono);
      font-size: 12px;
      color: var(--text-faint);
      flex-shrink: 0;
    }
    .chapter-line {
      flex: 1;
      height: 1px;
      background: var(--divider);
    }
    .chapter-count {
      font-size: 11px;
      color: var(--text-faint);
      flex-shrink: 0;
    }

    /* Words — two states */
    .word {
      display: inline;
      padding: 2px 1px;
      border-radius: 3px;
      cursor: pointer;
      transition: all 0.1s;
      font-size: 15px;
      color: var(--text);
    }
    .word:hover { background: var(--bg-muted); }
    .word.selected {
      color: var(--text-faint);
      text-decoration: line-through;
      text-decoration-color: var(--text-muted);
    }
    .word.selected:hover { background: var(--deleted-bg); }
    .word.current {
      background: var(--highlight-bg);
      color: var(--highlight-fg);
      border-radius: 3px;
      text-decoration: none;
    }
    /* Gap pills */
    .gap {
      display: inline-block;
      background: var(--bg-muted);
      border: 1px solid #d9d7d0;
      color: var(--text-muted);
      padding: 1px 8px;
      margin: 1px 2px;
      border-radius: 10px;
      font-size: 11px;
      font-family: var(--font-mono);
      cursor: pointer;
      transition: all 0.1s;
      vertical-align: middle;
      line-height: 18px;
    }
    .gap:hover { background: #eae9e5; border-color: #cccac3; }
    .gap.selected {
      background: #e8e8e6;
      color: var(--text-faint);
      text-decoration: line-through;
      border-color: #d4d3ce;
    }
    .gap.current {
      background: var(--highlight-bg);
      color: var(--highlight-fg);
      border-color: #e8d89c;
      text-decoration: none;
    }
    /* Bottom legend */
    .bottom-legend {
      height: 32px;
      background: var(--bg-surface);
      border-top: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 16px;
      font-size: 12px;
      color: var(--text-faint);
      flex-shrink: 0;
    }
    .legend-item {
      display: flex;
      align-items: center;
      gap: 5px;
    }
    .legend-swatch {
      display: inline-block;
      width: 28px;
      font-size: 12px;
      text-align: center;
    }
    .legend-swatch.del {
      color: var(--text-faint);
      text-decoration: line-through;
      text-decoration-color: var(--text-muted);
    }
    .legend-swatch.normal { color: var(--text); }
    .legend-swatch.playing {
      background: var(--highlight-bg);
      color: var(--highlight-fg);
      border-radius: 3px;
      padding: 0 2px;
    }

    /* ─── Loading overlay ─── */
    .loading-overlay {
      display: none;
      position: fixed;
      top: 0; left: 0;
      width: 100%; height: 100%;
      background: rgba(255,255,255,0.92);
      backdrop-filter: blur(4px);
      z-index: 9999;
      justify-content: center;
      align-items: center;
      flex-direction: column;
    }
    .loading-overlay.show { display: flex; }
    .loading-spinner {
      width: 48px;
      height: 48px;
      border: 3px solid var(--bg-muted);
      border-top-color: var(--accent);
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    .loading-text {
      margin-top: 20px;
      font-size: 16px;
      font-weight: 500;
      color: var(--text);
    }
    .loading-progress-container {
      margin-top: 16px;
      width: 260px;
      height: 4px;
      background: var(--bg-muted);
      border-radius: 2px;
      overflow: hidden;
    }
    .loading-progress-bar {
      height: 100%;
      background: var(--accent);
      width: 0%;
      transition: width 0.3s ease;
      border-radius: 2px;
    }
    .loading-time {
      margin-top: 12px;
      font-size: 13px;
      color: var(--text-muted);
    }
    .loading-estimate {
      margin-top: 6px;
      font-size: 12px;
      color: var(--text-faint);
    }

    /* Scrollbar */
    .transcript-body::-webkit-scrollbar,
    .sidebar::-webkit-scrollbar { width: 6px; }
    .transcript-body::-webkit-scrollbar-track,
    .sidebar::-webkit-scrollbar-track { background: transparent; }
    .transcript-body::-webkit-scrollbar-thumb,
    .sidebar::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.12); border-radius: 3px; }
    .transcript-body::-webkit-scrollbar-thumb:hover,
    .sidebar::-webkit-scrollbar-thumb:hover { background: rgba(0,0,0,0.2); }

    @media (max-width: 820px), (max-aspect-ratio: 3 / 4) {
      .header {
        padding: 0 10px;
        gap: 8px;
      }
      .header-left {
        min-width: 0;
      }
      .header-left .logo {
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .header-left .badge {
        display: none;
      }
      .header-right {
        flex-shrink: 0;
      }
      .main {
        flex-direction: column;
      }
      .sidebar {
        width: 100%;
        max-height: 58vh;
        border-right: 0;
        border-bottom: 1px solid var(--border);
      }
      .video-wrap {
        display: flex;
        justify-content: center;
        padding: 8px 10px 0;
      }
      #player {
        width: auto;
        height: min(42vh, 520px);
        max-width: calc(100vw - 20px);
      }
      .transport {
        padding: 8px 12px;
        gap: 6px;
      }
      .sidebar-section {
        padding: 8px 12px 10px;
      }
      .card {
        padding: 10px;
      }
      .card-title {
        margin-bottom: 6px;
      }
      .clip-row {
        margin-bottom: 6px;
      }
      .clip-time-big {
        font-size: 18px;
      }
      .right-panel {
        width: 100%;
        min-height: 0;
      }
      .filter-bar {
        height: 38px;
        padding: 0 12px;
      }
      .shortcut-strip {
        min-height: 38px;
        padding: 6px 12px;
        gap: 10px;
      }
      .shortcut-list {
        gap: 10px;
      }
      .transcript-body {
        padding: 12px 14px 56px;
      }
      .content {
        max-width: none;
        line-height: 2.25;
      }
      .bottom-legend {
        justify-content: flex-start;
        overflow-x: auto;
        padding: 0 12px;
      }
      .bottom-legend::-webkit-scrollbar {
        display: none;
      }
    }

    @media (max-width: 520px) {
      .header-btn {
        padding: 0 8px;
      }
      .header-btn:not(.primary) .header-btn-label {
        display: none;
      }
      .search-box {
        min-width: 120px;
      }
      #time {
        font-size: 12px;
      }
      select.speed-select {
        width: 64px;
      }
      .shortcut-title {
        display: none;
      }
    }
  </style>
</head>
<body>
  <!-- Loading overlay -->
  <div class="loading-overlay" id="loadingOverlay">
    <div class="loading-spinner"></div>
    <div class="loading-text">正在剪辑...</div>
    <div class="loading-progress-container">
      <div class="loading-progress-bar" id="loadingProgress"></div>
    </div>
    <div class="loading-time" id="loadingTime">已等待 0 秒</div>
    <div class="loading-estimate" id="loadingEstimate">预估剩余: 计算中...</div>
  </div>

  <!-- Header -->
  <div class="header">
    <div class="header-left">
      <span class="logo"><span class="icon">&#9986;</span> 剪口播 · ${path.basename(videoFile)}</span>
      <span class="badge">已分析</span>
    </div>
    <div class="header-right">
      <button class="header-btn" onclick="copyDeleteList()" title="复制删除列表">
        <span>&#128203;</span><span class="header-btn-label">字幕</span>
      </button>
      <button class="header-btn primary" onclick="executeCut()">执行剪辑</button>
    </div>
  </div>

  <!-- Main -->
  <div class="main">
    <!-- Left Sidebar -->
    <div class="sidebar">
      <div class="video-wrap">
        <video id="player" src="${videoBaseName}" preload="auto"></video>
      </div>

      <!-- Transport -->
      <div class="transport">
        <button class="transport-btn" onclick="player.currentTime=Math.max(0,player.currentTime-5)" title="-5s">&#9198;</button>
        <button class="transport-btn" id="playBtn" onclick="togglePlay()" title="播放/暂停">&#9654;</button>
        <button class="transport-btn" onclick="player.currentTime+=5" title="+5s">&#9197;</button>
        <select class="speed-select transport-speed" id="speed" onchange="player.playbackRate=parseFloat(this.value)" title="播放速度">
          <option value="0.5">0.5x</option>
          <option value="0.75">0.75x</option>
          <option value="1" selected>1.0x</option>
          <option value="1.25">1.25x</option>
          <option value="1.5">1.5x</option>
          <option value="2">2.0x</option>
        </select>
        <span id="time">00:00 / 00:00</span>
      </div>

      <!-- Clip preview -->
      <div class="sidebar-section">
        <div class="card" id="clipCard">
          <div class="card-title">剪辑预览</div>
          <div class="clip-row">
            <span class="clip-time-old" id="clipOld">--:--</span>
            <span class="clip-arrow">&rarr;</span>
            <span class="clip-time-big" id="clipNew">--:--</span>
          </div>
          <div class="clip-bar-wrap">
            <div class="clip-bar-keep" id="clipBar" style="width:100%"></div>
          </div>
          <div class="clip-saved" id="clipSaved">选中后实时预览</div>
        </div>
      </div>

    </div>

    <!-- Right panel -->
    <div class="right-panel">
      <!-- Filter bar -->
      <div class="filter-bar">
        <div class="search-box">
          <span style="font-size:14px;color:var(--text-faint)">&#128269;</span>
          <input type="text" id="searchInput" placeholder="搜索..." oninput="filterSearch(this.value)">
          <span class="hint">&#8984;K</span>
        </div>
        <div class="filter-divider"></div>
        <button class="filter-btn active" data-filter="all" onclick="setFilter('all',this)">全部 <span id="fAll">0</span></button>
        <button class="filter-btn" data-filter="silence" onclick="setFilter('silence',this)">静音 <span id="fSilence">0</span></button>
        <button class="filter-btn" data-filter="filler" onclick="setFilter('filler',this)">语气词 <span id="fFiller">0</span></button>
        <button class="filter-btn" data-filter="stutter" onclick="setFilter('stutter',this)">卡顿 <span id="fStutter">0</span></button>
        <button class="filter-btn" data-filter="repeat" onclick="setFilter('repeat',this)">重说 <span id="fRepeat">0</span></button>
        <span class="filter-summary">已选 <span id="selCount">0</span> / <span id="totalCount">0</span></span>
      </div>

      <!-- Shortcut strip -->
      <div class="shortcut-strip">
        <span class="shortcut-title">快捷键</span>
        <div class="shortcut-list">
          <span class="shortcut-item primary"><kbd>左键拖动</kbd><span>批量选择 / 取消</span></span>
          <span class="shortcut-item"><kbd>双击</kbd><span>切换选中</span></span>
          <span class="shortcut-item"><kbd>Space</kbd><span>播放 / 暂停</span></span>
          <span class="shortcut-item"><kbd>&larr; &rarr;</kbd><span>跳 1 秒</span></span>
          <span class="shortcut-item"><kbd>Shift + &larr;&rarr;</kbd><span>跳 5 秒</span></span>
          <span class="shortcut-item"><kbd>&#8984;K</kbd><span>搜索</span></span>
        </div>
      </div>

      <!-- Transcript body -->
      <div class="transcript-body" id="transcriptBody">
        <div class="content" id="content"></div>
      </div>

      <!-- Bottom legend -->
      <div class="bottom-legend">
        <div class="legend-item"><span class="legend-swatch del">删除</span><span>已选中</span></div>
        <div class="legend-item"><span class="legend-swatch normal">保留</span><span>未选中</span></div>
        <div class="legend-item"><span class="legend-swatch playing">播放</span><span>当前词</span></div>
        <span style="color:var(--divider)">|</span>
        <span>单击跳转 · 双击切换 · 左键拖动批量</span>
      </div>
    </div>
  </div>

  <script>
    const words = ${JSON.stringify(words)};
    const autoSelected = new Set(${JSON.stringify(autoSelected)});
    const selected = new Set(autoSelected);

    // 自动保存状态（必须在 rebuildSkipIntervals 之前声明，否则 TDZ）
    let saveTimer = null;
    let autosaveEnabled = false;

    const player = document.getElementById('player');
    const timeDisplay = document.getElementById('time');
    const playBtn = document.getElementById('playBtn');

    function togglePlay() {
      if (player.paused) player.play();
      else player.pause();
    }
    player.addEventListener('play', () => { playBtn.classList.add('playing'); playBtn.innerHTML = '&#9646;&#9646;'; });
    player.addEventListener('pause', () => { playBtn.classList.remove('playing'); playBtn.innerHTML = '&#9654;'; });

    const content = document.getElementById('content');
    let elements = [];
    let isSelecting = false;
    const dragSelect = {
      pending: false,
      startIndex: -1,
      lastIndex: -1,
      mode: 'add',
      startX: 0,
      startY: 0,
      snapshot: null
    };

    // 当前激活的 filter
    let activeFilter = 'all';
    let searchQuery = '';

    function formatTime(sec) {
      if (!sec || isNaN(sec)) return '00:00';
      const m = Math.floor(sec / 60);
      const s = Math.floor(sec % 60);
      return \`\${m.toString().padStart(2, '0')}:\${s.toString().padStart(2, '0')}\`;
    }

    function formatDuration(sec) {
      const totalSec = parseFloat(sec);
      const m = Math.floor(totalSec / 60);
      const s = (totalSec % 60).toFixed(1);
      if (m > 0) return \`\${m}分\${s}秒 (\${totalSec}s)\`;
      return \`\${s}秒\`;
    }

    function setSelected(i, shouldSelect) {
      if (!words[i]) return;
      if (shouldSelect) {
        selected.add(i);
        if (elements[i]) elements[i].classList.add('selected');
      } else {
        selected.delete(i);
        if (elements[i]) elements[i].classList.remove('selected');
      }
    }

    function applySelectionRange(from, to, mode) {
      const min = Math.min(from, to);
      const max = Math.max(from, to);
      const shouldSelect = mode === 'add';
      for (let j = min; j <= max; j++) {
        setSelected(j, shouldSelect);
      }
      updateStats();
    }

    function restoreSelectionSnapshot(snapshot) {
      selected.clear();
      snapshot.forEach(i => selected.add(i));
      elements.forEach((el, i) => {
        if (el) el.classList.toggle('selected', selected.has(i));
      });
    }

    function applyLiveSelectionRange(to) {
      if (!dragSelect.snapshot) return;
      restoreSelectionSnapshot(dragSelect.snapshot);
      applySelectionRange(dragSelect.startIndex, to, dragSelect.mode);
    }

    function getIndexedTarget(e) {
      const direct = e.target && e.target.closest ? e.target.closest('[data-index]') : null;
      if (direct) return direct;
      const atPoint = document.elementFromPoint(e.clientX, e.clientY);
      return atPoint && atPoint.closest ? atPoint.closest('[data-index]') : null;
    }

    // ─── 章节分割（gap >= 1.5s） ───
    function buildChapters() {
      const chapters = [];
      let current = { startIdx: 0, startTime: words.length ? words[0].start : 0, endTime: 0, suggestions: 0 };

      for (let i = 0; i < words.length; i++) {
        const w = words[i];
        current.endTime = w.end;
        if (autoSelected.has(i)) current.suggestions++;

        // gap >= 1.5s → 新章节
        if (w.isGap && (w.end - w.start) >= 1.5 && i < words.length - 1) {
          current.endIdx = i;
          chapters.push(current);
          current = { startIdx: i + 1, startTime: words[i + 1].start, endTime: 0, suggestions: 0 };
        }
      }
      current.endIdx = words.length - 1;
      chapters.push(current);
      return chapters;
    }

    // ─── 预选分类统计 ───
    function categorize(i) {
      const w = words[i];
      if (w.isGap) return 'silence';
      const t = (w.text || '').trim().toLowerCase();
      if (/^(嗯|啊|呃|额|哦|噢|唔|emm|em|uhm|uh|hmm|嘶)$/.test(t)) return 'filler';
      if (w.reason && /重说|repeat/i.test(w.reason)) return 'repeat';
      if (w.reason && /卡顿|stutter/i.test(w.reason)) return 'stutter';
      if (w.reason && /残句/i.test(w.reason)) return 'incomplete';
      return 'other';
    }

    function countByCategory() {
      const counts = { silence: 0, filler: 0, stutter: 0, repeat: 0, incomplete: 0, other: 0 };
      autoSelected.forEach(i => {
        const cat = categorize(i);
        if (counts[cat] !== undefined) counts[cat]++;
      });
      return counts;
    }

    // ─── 渲染 ───
    function render() {
      content.innerHTML = '';
      elements = new Array(words.length);

      const chapters = buildChapters();

      chapters.forEach((ch, ci) => {
        // Chapter header
        const header = document.createElement('div');
        header.className = 'chapter-header';
        const num = String(ci + 1).padStart(2, '0');
        header.innerHTML = \`
          <span class="chapter-num">\${num}</span>
          <span class="chapter-range">\${formatTime(ch.startTime)} — \${formatTime(ch.endTime)}</span>
          <div class="chapter-line"></div>
          <span class="chapter-count">\${ch.suggestions ? ch.suggestions + ' 建议' : ''}</span>
        \`;
        content.appendChild(header);

        // Words in this chapter
        for (let i = ch.startIdx; i <= ch.endIdx; i++) {
          const word = words[i];
          const el = document.createElement(word.isGap ? 'span' : 'span');
          el.className = word.isGap ? 'gap' : 'word';

          if (selected.has(i)) el.classList.add('selected');

          if (word.isGap) {
            const duration = (word.end - word.start).toFixed(1);
            el.textContent = duration + 's';
          } else {
            el.textContent = word.text;
          }

          el.dataset.index = i;

          // 双击选中/取消
          el.ondblclick = () => toggle(i);

          // 左键拖动批量选择；单击仍跳转
          el.onmousedown = (e) => {
            if (e.button !== 0) return;
            isSelecting = false;
            const mode = selected.has(i) ? 'remove' : 'add';
            dragSelect.pending = true;
            dragSelect.startIndex = i;
            dragSelect.lastIndex = i;
            dragSelect.mode = mode;
            dragSelect.startX = e.clientX;
            dragSelect.startY = e.clientY;
            dragSelect.snapshot = new Set(selected);
            e.preventDefault();
          };

          content.appendChild(el);
          elements[i] = el;

          // 非 gap 之间加空格
          if (!word.isGap) {
            const next = words[i + 1];
            if (next && !next.isGap && i < ch.endIdx) {
              content.appendChild(document.createTextNode(' '));
            }
          }
        }
      });

      updateStats();
      updateFilterCounts();
    }

    // 左键拖动多选
    document.getElementById('content').addEventListener('mousemove', e => {
      if (!dragSelect.pending && !isSelecting) return;
      if (e.buttons !== 1) {
        finishDragSelect(false);
        return;
      }

      const target = getIndexedTarget(e);
      if (!target) return;

      const i = parseInt(target.dataset.index);
      const movedEnough = Math.abs(e.clientX - dragSelect.startX) > 3 || Math.abs(e.clientY - dragSelect.startY) > 3 || i !== dragSelect.startIndex;

      if (!isSelecting) {
        if (!movedEnough) return;
        isSelecting = true;
        applyLiveSelectionRange(dragSelect.startIndex);
      }

      if (Number.isInteger(i) && i !== dragSelect.lastIndex) {
        applyLiveSelectionRange(i);
        dragSelect.lastIndex = i;
      }
    });

    document.addEventListener('mouseup', () => {
      finishDragSelect(true);
    });

    function finishDragSelect(allowSingleClick) {
      if (!dragSelect.pending && !isSelecting) return;
      const wasSelecting = isSelecting;
      const clickIndex = dragSelect.startIndex;

      dragSelect.pending = false;
      isSelecting = false;
      dragSelect.startIndex = -1;
      dragSelect.lastIndex = -1;
      dragSelect.snapshot = null;

      if (wasSelecting) {
        rebuildSkipIntervals();
      } else if (allowSingleClick && words[clickIndex]) {
        player.currentTime = words[clickIndex].start;
      }
    }

    function toggle(i) {
      finishDragSelect(false);
      if (selected.has(i)) {
        setSelected(i, false);
      } else {
        setSelected(i, true);
      }
      rebuildSkipIntervals();
      updateStats();
    }

    function updateStats() {
      // Clip preview card
      const totalDur = words.length ? words[words.length - 1].end - words[0].start : 0;
      let deletedDur = 0;
      selected.forEach(i => { deletedDur += words[i].end - words[i].start; });
      const newDur = Math.max(0, totalDur - deletedDur);
      const pct = totalDur > 0 ? ((deletedDur / totalDur) * 100).toFixed(0) : 0;
      const keepPct = totalDur > 0 ? ((newDur / totalDur) * 100).toFixed(0) : 100;

      document.getElementById('clipOld').textContent = formatTime(totalDur);
      document.getElementById('clipNew').textContent = formatTime(newDur);
      document.getElementById('clipBar').style.width = keepPct + '%';
      document.getElementById('clipSaved').innerHTML = deletedDur > 0
        ? \`删减 \${deletedDur.toFixed(1)}s · 节省 <b>\${pct}%</b>\`
        : '尚未选择删除片段';

      // Filter summary
      document.getElementById('selCount').textContent = selected.size;
      document.getElementById('totalCount').textContent = words.length;
    }

    function updateFilterCounts() {
      const counts = countByCategory();
      document.getElementById('fAll').textContent = words.length;
      document.getElementById('fSilence').textContent = counts.silence;
      document.getElementById('fFiller').textContent = counts.filler;
      document.getElementById('fStutter').textContent = counts.stutter;
      document.getElementById('fRepeat').textContent = counts.repeat;
    }

    // ─── Filter ───
    function setFilter(type, btn) {
      activeFilter = type;
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      if (type === 'all') {
        // 显示所有
        elements.forEach(el => { if (el) el.style.display = ''; });
        document.querySelectorAll('.chapter-header').forEach(h => h.style.display = '');
        return;
      }

      // 高亮该类型，滚到第一个
      let first = null;
      elements.forEach((el, i) => {
        if (!el) return;
        if (autoSelected.has(i) && categorize(i) === type) {
          el.style.display = '';
          el.style.outline = '2px solid var(--accent)';
          el.style.outlineOffset = '1px';
          el.style.borderRadius = '3px';
          if (!first) first = el;
        } else {
          el.style.display = '';
          el.style.outline = '';
          el.style.outlineOffset = '';
        }
      });
      if (first) first.scrollIntoView({ behavior: 'smooth', block: 'center' });

      // 3 秒后去掉 outline
      setTimeout(() => {
        elements.forEach(el => { if (el) { el.style.outline = ''; el.style.outlineOffset = ''; } });
      }, 3000);
    }

    // ─── Search ───
    function filterSearch(query) {
      searchQuery = query.trim().toLowerCase();
      if (!searchQuery) {
        elements.forEach(el => { if (el) el.style.display = ''; });
        document.querySelectorAll('.chapter-header').forEach(h => h.style.display = '');
        return;
      }
      let first = null;
      elements.forEach((el, i) => {
        if (!el) return;
        const w = words[i];
        const text = (w.text || '').toLowerCase();
        if (text.includes(searchQuery)) {
          el.style.outline = '2px solid var(--accent)';
          el.style.outlineOffset = '1px';
          if (!first) first = el;
        } else {
          el.style.outline = '';
          el.style.outlineOffset = '';
        }
      });
      if (first) first.scrollIntoView({ behavior: 'smooth', block: 'center' });

      // 清除 outline 延迟
      clearTimeout(filterSearch._timer);
      filterSearch._timer = setTimeout(() => {
        elements.forEach(el => { if (el) { el.style.outline = ''; el.style.outlineOffset = ''; } });
      }, 4000);
    }

    // ─── Web Audio API ───
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const source = audioCtx.createMediaElementSource(player);
    const gainNode = audioCtx.createGain();
    source.connect(gainNode);
    gainNode.connect(audioCtx.destination);
    player.addEventListener('play', () => { if (audioCtx.state === 'suspended') audioCtx.resume(); });

    // 预计算跳过区间
    let skipIntervals = [];
    function rebuildSkipIntervals() {
      const sorted = Array.from(selected).sort((a, b) => a - b);
      skipIntervals = [];
      let i = 0;
      while (i < sorted.length) {
        let start = words[sorted[i]].start;
        let end = words[sorted[i]].end;
        let j = i + 1;
        while (j < sorted.length && words[sorted[j]].start - end < 0.1) {
          end = words[sorted[j]].end;
          j++;
        }
        skipIntervals.push({ start: start - 0.05, end });
        i = j;
      }
      autosave();
    }
    rebuildSkipIntervals();

    // ─── 自动保存选中状态 ───
    function autosave() {
      if (!autosaveEnabled) return;
      clearTimeout(saveTimer);
      saveTimer = setTimeout(() => {
        const data = Array.from(selected).sort((a, b) => a - b);
        fetch('/api/save-selection', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data),
        }).catch(e => console.warn('autosave failed', e));
      }, 400);
    }

    async function loadSavedSelection() {
      try {
        const r = await fetch('/api/load-selection');
        if (r.ok) {
          const data = await r.json();
          if (Array.isArray(data)) {
            selected.clear();
            data.forEach(i => selected.add(i));
            document.querySelectorAll('.word.selected, .gap.selected').forEach(el => el.classList.remove('selected'));
            selected.forEach(i => { if (elements[i]) elements[i].classList.add('selected'); });
            console.log('已加载保存的选中:', data.length);
          }
        }
      } catch (e) {
        console.warn('load failed', e);
      }
      autosaveEnabled = true;
      rebuildSkipIntervals();
      updateStats();
    }

    // rAF tick
    let lastHighlight = -1;
    let skipLock = false;
    function tick() {
      requestAnimationFrame(tick);
      const t = player.currentTime;

      if (!player.paused) {
        for (const iv of skipIntervals) {
          if (t >= iv.start && t < iv.end) {
            if (!skipLock) {
              skipLock = true;
              gainNode.gain.setValueAtTime(0, audioCtx.currentTime);
              player.currentTime = iv.end;
            }
            return;
          }
        }
        if (skipLock) {
          skipLock = false;
          gainNode.gain.setValueAtTime(1, audioCtx.currentTime);
        }
      }

      timeDisplay.textContent = \`\${formatTime(t)} / \${formatTime(player.duration || 0)}\`;

      // 高亮当前词
      let curr = -1;
      for (let i = 0; i < words.length; i++) {
        if (t >= words[i].start && t < words[i].end) { curr = i; break; }
      }
      if (curr !== lastHighlight) {
        if (lastHighlight >= 0 && elements[lastHighlight]) elements[lastHighlight].classList.remove('current');
        if (curr >= 0 && elements[curr]) {
          elements[curr].classList.add('current');
          elements[curr].scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        lastHighlight = curr;
      }
    }
    requestAnimationFrame(tick);

    // ─── Actions ───
    function copyDeleteList() {
      const segments = [];
      const sortedSelected = Array.from(selected).sort((a, b) => a - b);
      sortedSelected.forEach(i => {
        const word = words[i];
        segments.push({ start: word.start, end: word.end });
      });

      const merged = [];
      for (const seg of segments) {
        if (merged.length === 0) {
          merged.push({ ...seg });
        } else {
          const last = merged[merged.length - 1];
          if (Math.abs(seg.start - last.end) < 0.05) {
            last.end = seg.end;
          } else {
            merged.push({ ...seg });
          }
        }
      }

      const json = JSON.stringify(merged, null, 2);
      navigator.clipboard.writeText(json).then(() => {
        alert('已复制 ' + merged.length + ' 个删除片段到剪贴板');
      });
    }

    function clearAll() {
      selected.clear();
      elements.forEach((el, i) => {
        if (el) el.classList.remove('selected');
      });
      rebuildSkipIntervals();
      updateStats();
    }

    async function executeCut() {
      const videoDuration = player.duration;
      const videoMinutes = (videoDuration / 60).toFixed(1);
      const estimatedTime = Math.max(5, Math.ceil(videoDuration / 4));
      const estMin = Math.floor(estimatedTime / 60);
      const estSec = estimatedTime % 60;
      const estText = estMin > 0 ? \`\${estMin}分\${estSec}秒\` : \`\${estSec}秒\`;

      if (!confirm(\`确认执行剪辑？\\n\\n视频时长: \${videoMinutes} 分钟\\n预计耗时: \${estText} 起\\n\\n点击确定开始\`)) return;

      const segments = [];
      const sortedSelected = Array.from(selected).sort((a, b) => a - b);
      sortedSelected.forEach(i => {
        const word = words[i];
        segments.push({ start: word.start, end: word.end });
      });

      const overlay = document.getElementById('loadingOverlay');
      const loadingTimeEl = document.getElementById('loadingTime');
      const loadingProgress = document.getElementById('loadingProgress');
      const loadingEstimate = document.getElementById('loadingEstimate');
      overlay.classList.add('show');
      loadingEstimate.textContent = \`预估剩余: \${estText}\`;

      const startTime = Date.now();
      const timer = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        loadingTimeEl.textContent = \`已等待 \${elapsed} 秒\`;
        const progress = Math.min(95, (elapsed / estimatedTime) * 100);
        loadingProgress.style.width = progress + '%';
        const remaining = Math.max(0, estimatedTime - elapsed);
        if (remaining > 0) {
          loadingEstimate.textContent = \`预估剩余: \${remaining} 秒\`;
        } else {
          loadingEstimate.textContent = '即将完成...';
        }
      }, 500);

      try {
        const res = await fetch('/api/cut', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(segments)
        });
        const data = await res.json();

        clearInterval(timer);
        loadingProgress.style.width = '100%';
        await new Promise(r => setTimeout(r, 300));
        overlay.classList.remove('show');
        loadingProgress.style.width = '0%';
        const totalTime = ((Date.now() - startTime) / 1000).toFixed(1);

        if (data.success) {
          const msg = \`剪辑完成！(耗时 \${totalTime}s)\\n\\n输出文件: \${data.output}\\n\\n下一步：让 Agent 基于剪后视频重新转写，并 AI 校对字幕。\\n\\n时间统计:\\n  原时长: \${formatDuration(data.originalDuration)}\\n  新时长: \${formatDuration(data.newDuration)}\\n  删减: \${formatDuration(data.deletedDuration)} (\${data.savedPercent}%)\`;
          alert(msg);
        } else {
          alert('剪辑失败: ' + data.error);
        }
      } catch (err) {
        clearInterval(timer);
        overlay.classList.remove('show');
        loadingProgress.style.width = '0%';
        alert('请求失败: ' + err.message + '\\n\\n请确保使用 review_server.js 启动服务');
      }
    }

    // ─── Keyboard shortcuts ───
    document.addEventListener('keydown', e => {
      // 忽略搜索框输入
      if (e.target.tagName === 'INPUT') return;

      if (e.code === 'Space') {
        e.preventDefault();
        togglePlay();
      } else if (e.code === 'ArrowLeft') {
        e.preventDefault();
        player.currentTime = Math.max(0, player.currentTime - (e.shiftKey ? 5 : 1));
      } else if (e.code === 'ArrowRight') {
        e.preventDefault();
        player.currentTime = player.currentTime + (e.shiftKey ? 5 : 1);
      } else if (e.code === 'KeyK' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        document.getElementById('searchInput').focus();
      }
    });

    render();
    loadSavedSelection();
  </script>
</body>
</html>`;

fs.writeFileSync('review.html', html);
console.log('✅ 已生成 review.html');
console.log('📌 启动服务器: node "$SKILL_DIR/scripts/review_server.js" 8899 "$VIDEO_PATH"');
console.log('📌 打开: http://localhost:8899/review.html');
