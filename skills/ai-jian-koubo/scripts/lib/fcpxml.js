'use strict';
/*
 * FCPXML 1.8 生成（从 review_server.js 抽出，便于单测）。
 *
 * 一句话职责：拿到「删除段 + 静音段 + 视频文件」，算出真正保留的片段（复用
 * compute_keeps.js 这一份切割算法），再渲染成可被剪映 / Final Cut Pro 导入的 FCPXML。
 *
 * 设计约束（改动前必读）：
 *   - FCPXML 1.8 DTD 不支持 fade 元素，淡入淡出留给剪辑软件自己加
 *   - 媒体引用用绝对路径的 file:// URI（百分号编码），剪映和 FCP 都靠它定位源视频
 *   - 时间一律用 FCP ticks（帧号 × fpsDen），不要改成秒——浮点累积会导致 ±1 帧漂移
 */

const path = require('path');
const { execSync } = require('child_process');
const { computeFinalKeeps } = require('./compute_keeps');

// 把绝对路径编码成 file:// URI（保留路径分隔符与安全字符，其余百分号编码）
function fileUri(absPath) {
  return 'file://' + absPath.split('').map(c => (
    /[a-zA-Z0-9\-_.~/]/.test(c) ? c : encodeURIComponent(c)
  )).join('');
}

// FCP 要求的 UUID 格式
function uuid() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

// 用 ffprobe 探测视频元数据：时长、帧率（有理数）、宽高
function probeVideo(videoFile) {
  const duration = parseFloat(
    execSync(`ffprobe -v error -show_entries format=duration -of csv=p=0 "file:${videoFile}"`).toString().trim()
  );

  // 帧率为有理数，如 "30000/1001" = 29.97fps
  const fpsRaw = execSync(
    `ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of csv=p=0 "file:${videoFile}"`
  ).toString().trim().replace(/,+$/, '');
  const fpsParts = fpsRaw.split('/').map(Number);
  const [fpsNum, fpsDen] = fpsParts.length === 2 ? fpsParts : [fpsParts[0], 1];

  const sizeRaw = execSync(
    `ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 "file:${videoFile}"`
  ).toString().trim().split(',');
  const width = parseInt(sizeRaw[0]) || 1920;
  const height = parseInt(sizeRaw[1]) || 1080;

  return { duration, fpsNum, fpsDen, width, height };
}

/**
 * 生成 FCPXML。
 * @param {object} o
 * @param {string} o.videoFile        源视频路径
 * @param {number[]} o.deleteList      删除段（秒区间，见 compute_keeps）
 * @param {Array} o.silencePeriods     预计算静音段
 * @param {object} [o.cutOpts]         切割参数（padStart/padEnd 等）
 * @returns {{ xml:string, outputPath:string, finalKeeps:Array, baseName:string }}
 */
function buildFcpxml({ videoFile, deleteList, silencePeriods, cutOpts }) {
  const { duration, fpsNum, fpsDen, width, height } = probeVideo(videoFile);

  // ticks = 帧号 × fpsDen，分母为 fpsNum：对 29.97/30/24 等所有帧率都成立
  const toFCPTicks = (sec) => Math.round(sec * fpsNum / fpsDen) * fpsDen;
  const frameDuration = `${fpsDen}/${fpsNum}s`;

  // 切割算法单一来源：合并删除段 → 取反 → 边界吸附静音 → 内部长静音二次切
  const finalKeeps = computeFinalKeeps(deleteList, silencePeriods, duration, cutOpts);

  const baseName = path.basename(videoFile, path.extname(videoFile));
  const outputPath = path.resolve(`${baseName}_cut.fcpxml`);

  const videoSrc = fileUri(path.resolve(videoFile));
  const fcpxmlSrc = fileUri(outputPath);

  // asset 时长用音频采样率（48000）做分母
  const audioRate = 48000;
  const assetDurationNum = Math.round(duration * audioRate);

  // 每个保留片段一个 asset-clip，引用同一个 asset r1；
  // offset 在 tick 空间累加，避免浮点秒累积误差导致 ±1 帧偏移
  let timelineOffsetTicks = 0;
  const clips = finalKeeps.map((seg) => {
    const startTicks = toFCPTicks(seg.start);
    const durTicks = toFCPTicks(seg.end - seg.start);
    const offsetTicks = timelineOffsetTicks;
    timelineOffsetTicks += durTicks;
    return `            <asset-clip name="${baseName}" offset="${offsetTicks}/${fpsNum}s" ref="r1" start="${startTicks}/${fpsNum}s" duration="${durTicks}/${fpsNum}s" audioRole="dialogue" format="r2" tcFormat="NDF" />`;
  }).join('\n');

  const totalTicks = timelineOffsetTicks;

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<fcpxml version="1.8">
  <resources>
    <format id="r2" frameDuration="${frameDuration}" width="${width}" height="${height}" colorSpace="1-1-1 (Rec. 709)" />
    <asset id="r1" name="${baseName}" src="${videoSrc}" start="0/1s" duration="${assetDurationNum}/${audioRate}s" format="r2" hasAudio="1" hasVideo="1" audioSources="1" audioChannels="2" audioRate="48k" />
  </resources>
  <library location="${fcpxmlSrc}">
    <event name="${baseName}_剪辑" uid="${uuid()}">
      <project name="${baseName}_cut" uid="${uuid()}">
        <sequence duration="${totalTicks}/${fpsNum}s" format="r2" tcStart="0/1s" tcFormat="NDF" audioLayout="stereo" audioRate="48k">
          <spine>
${clips}
          </spine>
        </sequence>
      </project>
    </event>
  </library>
</fcpxml>`;

  return { xml, outputPath, finalKeeps, baseName };
}

module.exports = { buildFcpxml };
