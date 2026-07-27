#!/usr/bin/env node
/**
 * 生成审核数据文件 + 复制前端模板
 *
 * 用法: node generate_review.js <subtitles_words.json> <auto_selected.json> <audio_file> [输出目录]
 * 输出: data.json + review.html (from templates/) + audio.mp3
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const subtitlesFile = process.argv[2];
const autoSelectedFile = process.argv[3];
const audioFile = process.argv[4];
const outDir = process.argv[5] || '.';

if (!subtitlesFile || !autoSelectedFile || !audioFile) {
  console.error('用法: node generate_review.js <subtitles_words.json> <auto_selected.json> <audio_file> [输出目录]');
  process.exit(1);
}

// 确保输出目录存在（recursive: true 本身幂等，无需 existsSync）
fs.mkdirSync(outDir, { recursive: true });

if (!fs.existsSync(subtitlesFile)) {
  console.error('❌ 找不到字幕文件:', subtitlesFile);
  process.exit(1);
}

// ── 读取字幕数据 ─────────────────────────────────────────
const words = JSON.parse(fs.readFileSync(subtitlesFile, 'utf8'));
const wordCount = words.filter(w => !w.isGap).length;
const gapCount = words.filter(w => w.isGap).length;
console.log('字幕: ' + words.length + ' 个元素（' + wordCount + ' 字 + ' + gapCount + ' 静音段）');

// ── 读取 AI 预选 ─────────────────────────────────────────
let autoSelected = [];
if (fs.existsSync(autoSelectedFile)) {
  try {
    autoSelected = JSON.parse(fs.readFileSync(autoSelectedFile, 'utf8'));
    console.log('AI 预选: ' + autoSelected.length + ' 个');
  } catch (e) {
    console.warn('⚠️  auto_selected.json 格式错误，跳过: ' + e.message);
    console.warn('   请检查 AI 输出的 JSON 是否符合格式，例如 [72, 85, 120]');
  }
}

// ── 写入 data.json ───────────────────────────────────────
const data = {
  words,
  autoSelected,
  generatedAt: new Date().toISOString()
};
fs.writeFileSync(path.join(outDir, 'data.json'), JSON.stringify(data, null, 2));
console.log('已生成 data.json');

// ── 复制音频文件 ──────────────────────────────────────────
const audioDst = path.join(outDir, 'audio.mp3');
if (audioFile !== audioDst && fs.existsSync(audioFile)) {
  fs.copyFileSync(audioFile, audioDst);
  console.log('已复制音频: audio.mp3');
} else if (audioFile === audioDst && fs.existsSync(audioFile)) {
  console.log('音频已是 audio.mp3');
} else {
  console.warn('⚠️  音频文件不存在: ' + audioFile);
}

// ── 复制前端模板 ──────────────────────────────────────────
const templateSrc = path.join(__dirname, 'templates', 'review.html');
const templateDst = path.join(outDir, 'review.html');
if (fs.existsSync(templateSrc)) {
  fs.copyFileSync(templateSrc, templateDst);
  console.log('已生成 review.html（来自模板）');
} else {
  console.error('❌ 找不到模板: ' + templateSrc);
  process.exit(1);
}

// ── 静音检测（供 FCPXML 导出使用）──────────────────────────
const SILENCE_MIN_DUR = 0.2;
const SILENCE_PEAK_OFFSET_DB = 35; // 峰值音量 - 此偏移 = 静音阈值
const SILENCE_DB_MIN = -55;        // 阈值下限（录音太轻时兜底）
const SILENCE_DB_MAX = -20;        // 阈值上限（录音太响时兜底）
const silenceOut = path.join(outDir, 'silence_periods.json');

// 音频时长：末尾静音段兜底 + peaks 目标点数都要用，只探一次
let audioDuration = 0;
try {
  audioDuration = parseFloat(
    execSync(`ffprobe -v error -show_entries format=duration -of csv=p=0 "file:${audioDst}"`).toString().trim()
  ) || 0;
} catch (e) {
  console.warn('⚠️  ffprobe 读取音频时长失败: ' + e.message);
}

try {
  // 取峰值音量，自适应计算静音阈值（峰值不受停顿多少影响，比均值更稳定）
  const volRaw = execSync(
    `ffmpeg -i "${audioDst}" -af volumedetect -f null - 2>&1`
  ).toString();
  const maxMatch = volRaw.match(/max_volume:\s*([-\d.]+)\s*dB/);
  let SILENCE_DB = -35; // 默认兜底
  if (maxMatch) {
    const maxVol = parseFloat(maxMatch[1]);
    SILENCE_DB = Math.max(SILENCE_DB_MIN, Math.min(SILENCE_DB_MAX, maxVol - SILENCE_PEAK_OFFSET_DB));
    console.log(`🔊 峰值音量: ${maxVol.toFixed(1)}dB → 静音阈值: ${SILENCE_DB.toFixed(1)}dB`);
  } else {
    console.warn('⚠️  无法读取峰值音量，使用默认阈值 -35dB');
  }

  const raw = execSync(
    `ffmpeg -i "${audioDst}" -af silencedetect=noise=${SILENCE_DB.toFixed(1)}dB:d=${SILENCE_MIN_DUR} -f null - 2>&1`
  ).toString();
  const ss = [...raw.matchAll(/silence_start: ([\d.]+)/g)];
  const se = [...raw.matchAll(/silence_end: ([\d.]+)/g)];
  const periods = ss.map((m, i) => ({
    start: parseFloat(m[1]),
    end:   se[i] ? parseFloat(se[i][1]) : audioDuration  // 末尾静音用音频时长兜底
  }));

  // ── 能量回收：补全 ASR 越界时间戳吞掉的句尾换气/静音 ──
  // 全局 dB silencedetect 漏掉的：ASR 把字说完后的静音圈进了字里，间隙 < 0.2s 不成 gap，
  // 换气声又比阈值响。refine_boundaries 用真实音频能量把字边界缩回真声处，挖出这些段，与 dB 取并集。
  let finalSilence = periods;
  try {
    const { reclaim } = require('./lib/refine_boundaries');
    const r = reclaim({ audioFile: audioDst, words, baseSilence: periods });
    finalSilence = r.merged;
    console.log('🎯 能量回收: 新挖出 ' + r.reclaimedCount + ' 段句尾换气/静音');
  } catch (e) {
    console.warn('⚠️  能量回收跳过(回退纯 dB): ' + e.message);
  }

  fs.writeFileSync(silenceOut, JSON.stringify(finalSilence));
  console.log('🔕 静音检测完成，dB ' + periods.length + ' 段 → 并集 ' + finalSilence.length + ' 段 → silence_periods.json');
} catch (e) {
  console.warn('⚠️  silencedetect 失败，跳过: ' + e.message);
  fs.writeFileSync(silenceOut, '[]');
}

// ── 预生成波形包络 peaks.json ───────────────────────────
// 前端审核页直接用预算好的包络渲染波形，跳过浏览器端解码 mp3 + 主线程算 peaks，
// 长视频也能秒开、滚动顺滑。8000Hz 单声道足够画包络。
const peaksOut = path.join(outDir, 'peaks.json');
try {
  const SR = 8000;
  // 目标采样点：约 150 点/秒，封顶 60000。点更密 → 放大时波形有真实细节、不阶梯，
  // 渲染端再做插值+平滑画成填充包络（贴近剪映/FCP）。60000 浮点 ≈ 300KB，长视频内存仍可控。
  const pointsTarget = Math.min(60000, Math.max(2000, Math.round(audioDuration * 150)));
  const pcm = execSync(`ffmpeg -i "${audioDst}" -ac 1 -ar ${SR} -f s16le -`, { maxBuffer: 1 << 28 });
  const sampleCount = Math.floor(pcm.length / 2);
  const bucket = Math.max(1, Math.ceil(sampleCount / pointsTarget));
  const peaks = [];
  for (let i = 0; i < sampleCount; i += bucket) {
    let max = 0;
    const end = Math.min(sampleCount, i + bucket);
    for (let j = i; j < end; j++) {
      const v = Math.abs(pcm.readInt16LE(j * 2));
      if (v > max) max = v;
    }
    peaks.push(+(max / 32768).toFixed(4)); // 归一化到 0..1
  }
  fs.writeFileSync(peaksOut, JSON.stringify({ duration: audioDuration, sampleRate: SR, peaks }));
  console.log('📈 波形包络完成，' + peaks.length + ' 点 → peaks.json');
} catch (e) {
  console.warn('⚠️  peaks 生成失败，前端将退回实时解码: ' + e.message);
  fs.writeFileSync(peaksOut, '[]');
}

console.log('');
console.log('✅ 审核数据准备完成');
console.log('   启动服务器: node review_server.js');
console.log('   打开: http://localhost:8899');
