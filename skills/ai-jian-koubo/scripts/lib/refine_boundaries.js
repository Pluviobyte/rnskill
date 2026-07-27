#!/usr/bin/env node
/**
 * 能量回收（boundary reclaim）
 *
 * 问题：ASR 给每个字标的 start/end 常常「越界」——把字说完之后的静音/换气也圈进字里。
 *       于是「字与字的间隙」被压缩到 0.2s 阈值以下，句尾换气既不成 gap 元素、
 *       全局 dB silencedetect 又嫌它不够安静，两头漏掉，留在成片里。
 *
 * 思路：不信 ASR 时间戳，直接看真实音频能量。
 *   1. 解码 PCM → 每 10ms 算一次 RMS(dB) 得能量包络
 *   2. 局部人声参考线 ref = 附近 ±winSec 内最响 − offsetDb（自适应音量起伏）
 *   3. 每个字：从 ASR end 往回缩到「最后一帧高于 ref」= 真实字尾；
 *              从 ASR start 往后缩到「第一帧高于 ref」= 真实起声
 *   4. 相邻两字的 realEnd→realStart 即真实非语音区（含越界静音 + 句尾换气）
 *   5. 与传入的 dB 静音段取并集输出
 *
 * compute_keeps.js 完全不用改：它照常吃 silence_periods，按 minInternalSilence / pad 切。
 *
 * 用法: node refine_boundaries.js <audio> <subtitles_words.json> [in_silence.json] [out_silence.json]
 * 作为库: require('./lib/refine_boundaries').reclaim({audioFile, words, baseSilence, opts})
 */
'use strict';
const fs = require('fs');
const { execSync } = require('child_process');

const DEFAULTS = {
  sampleRate: 8000,
  frameMs: 10,        // 能量包络帧长
  smoothFrames: 2,    // 能量包络 max-pool ±此帧数(≈±20ms)，填掉字内部短瞬停，避免误当静音
  expandSec: 0.30,    // 每个字边界向内扩多少去找越界静音（被 ASR 时间戳吞掉的部分）
  offsetDb: 12,       // 人声线 = 窗口内最响 − 此值；越大越保守（只切更安静的）
  minReclaim: 0.12,   // 回收出的非语音区 ≥ 此长度才输出（秒）
  mergeGap: 0.02,     // 并集合并间距
};

function decodeEnvelope(audioFile, SR, frameMs) {
  const pcm = execSync(`ffmpeg -i "${audioFile}" -ac 1 -ar ${SR} -f s16le -`, { maxBuffer: 1 << 29 });
  const N = Math.floor(pcm.length / 2);
  const win = Math.round(SR * frameMs / 1000);
  const env = [];
  for (let i = 0; i < N; i += win) {
    let sum = 0, cnt = 0;
    const end = Math.min(N, i + win);
    for (let j = i; j < end; j++) { const v = pcm.readInt16LE(j * 2) / 32768; sum += v * v; cnt++; }
    const rms = Math.sqrt(sum / cnt);
    env.push(rms > 0 ? 20 * Math.log10(rms) : -90);
  }
  return env; // env[k] 对应时间 k*frameMs/1000
}

// max-pool 平滑：env[i] → 取 ±halfW 内最大值。
// 作用：字内部音素间的短瞬停（<20ms）旁边一定有响帧，会被填平 → 不会被误判成静音；
//       句尾真静音/换气是持续的低能量区，填不平 → 保留。
function maxPool(env, halfW) {
  const n = env.length, out = new Array(n);
  for (let i = 0; i < n; i++) {
    let m = -90;
    const a = Math.max(0, i - halfW), b = Math.min(n - 1, i + halfW);
    for (let j = a; j <= b; j++) if (env[j] > m) m = env[j];
    out[i] = m;
  }
  return out;
}

function reclaim({ audioFile, words, baseSilence = [], opts = {} }) {
  const o = Object.assign({}, DEFAULTS, opts);
  const frameSec = o.frameMs / 1000;
  const raw = decodeEnvelope(audioFile, o.sampleRate, o.frameMs);
  const env = maxPool(raw, o.smoothFrames);
  const last = env.length - 1;
  const k = t => Math.max(0, Math.min(last, Math.round(t / frameSec)));

  const spoken = words.filter(w => !w.isGap);

  // 在 [loK, hiK] 窗口内：以「窗口最响 − offsetDb」为局部人声线，
  // 找最长的「连续低于人声线」run，即被字时间戳吞掉的真实静音/换气。窗口本地化 → 不会跨多字连成大段。
  const reclaimed = [];
  for (let i = 0; i < spoken.length - 1; i++) {
    const w1 = spoken[i], w2 = spoken[i + 1];
    // 向两侧的字内部扩，去够 ASR 越界圈进字里的静音；但不越过各自字的另一端
    const loK = k(Math.max(w1.start, w1.end - o.expandSec));
    const hiK = k(Math.min(w2.end, w2.start + o.expandSec));
    if (hiK - loK < 2) continue;
    let localMax = -90;
    for (let j = loK; j <= hiK; j++) if (env[j] > localMax) localMax = env[j];
    const thr = localMax - o.offsetDb;
    // 扫最长 sub-threshold run
    let bestA = -1, bestB = -1, curA = -1;
    for (let j = loK; j <= hiK; j++) {
      if (env[j] < thr) { if (curA < 0) curA = j; if (j - curA > bestB - bestA) { bestA = curA; bestB = j; } }
      else curA = -1;
    }
    if (bestA >= 0 && (bestB - bestA) * frameSec >= o.minReclaim) {
      reclaimed.push({ start: +(bestA * frameSec).toFixed(3), end: +(bestB * frameSec).toFixed(3) });
    }
  }

  // 与 dB 静音并集 + 合并
  const all = [...baseSilence, ...reclaimed].sort((a, b) => a.start - b.start);
  const merged = [];
  for (const p of all) {
    const lastSeg = merged[merged.length - 1];
    if (lastSeg && p.start <= lastSeg.end + o.mergeGap) lastSeg.end = Math.max(lastSeg.end, p.end);
    else merged.push({ start: p.start, end: p.end });
  }
  return { merged, reclaimedCount: reclaimed.length };
}

module.exports = { reclaim, DEFAULTS };

if (require.main === module) {
  const [audioFile, wordsFile, inSil, outSil] = process.argv.slice(2);
  if (!audioFile || !wordsFile) { console.error('用法: node refine_boundaries.js <audio> <subtitles_words.json> [in_silence.json] [out_silence.json]'); process.exit(1); }
  const words = JSON.parse(fs.readFileSync(wordsFile, 'utf8'));
  const baseSilence = inSil && fs.existsSync(inSil) ? JSON.parse(fs.readFileSync(inSil, 'utf8')) : [];
  const { merged, reclaimedCount } = reclaim({ audioFile, words, baseSilence });
  const out = outSil || 'silence_periods.json';
  fs.writeFileSync(out, JSON.stringify(merged));
  console.log(`能量回收: 新挖出 ${reclaimedCount} 段越界静音/换气`);
  console.log(`并集后静音段: ${baseSilence.length}(dB) → ${merged.length}(合并后) → ${out}`);
}
