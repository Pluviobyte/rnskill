/**
 * 切割算法单一来源（前后端共用）
 *
 * 输入「用户选中的删除段」，输出「实际保留片段 finalKeeps」。
 * 中间会做：合并相邻删除段 → 取反得保留段 → 边界向静音吸附 →
 * 保留段内部的长静音二次切割。这套逻辑过去内联在 review_server.js，
 * 现在抽出来让审核页前端也能实时预览到「真正会切到哪一帧」。
 *
 * UMD：Node 用 require('./lib/compute_keeps')，浏览器用 <script> 后读 window.ComputeKeeps。
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.ComputeKeeps = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  // 默认阈值（与历史 review_server.js 行为完全一致）
  const DEFAULTS = {
    mergeGap: 0.15,          // 相邻删除段间距 < 此值则合并，吸收词级时间戳天然间隙
    minKeepDur: 0.1,         // 短于此的保留段无意义，丢弃
    lookBack: 0.6,           // 删除点前后多大窗口内寻找静音作为吸附切点
    padFrames: 2 / 30,       // 吸附后给说话者留的喘气余量（秒）
    edgeMargin: 0.05,        // 保留段边缘此范围内的静音不算「内部静音」
    minInternalSilence: 0.2, // 保留段内部 ≥ 此长度的静音会被二次切掉（换气/未识别停顿）
  };

  // 在 (rawStart, windowEnd] 内找最近的静音终点（最小 end），用于裁保留段开头
  function findNextSilenceEnd(periods, rawStart, windowEnd) {
    let best = null;
    for (const sp of periods) {
      if (sp.end > rawStart && sp.end <= windowEnd) {
        if (best === null || sp.end < best) best = sp.end;
      }
    }
    return best;
  }

  // 在 [windowStart, rawEnd) 内找最后一个静音起点，用于裁保留段末尾
  function findLastSilenceStart(periods, rawEnd, windowStart) {
    let best = null;
    for (const sp of periods) {
      if (sp.start >= windowStart && sp.start < rawEnd) best = sp.start;
    }
    return best;
  }

  /**
   * @param {{start:number,end:number}[]} deleteList 用户选中的删除段（无需排序）
   * @param {{start:number,end:number}[]} silencePeriods ffmpeg 检测的静音段
   * @param {number} duration 媒体总时长（秒）
   * @param {object} [opts] 覆盖默认阈值
   * @returns {{start:number,end:number}[]} 实际保留片段（已吸附 + 内部二次切）
   */
  function computeFinalKeeps(deleteList, silencePeriods, duration, opts) {
    const o = Object.assign({}, DEFAULTS, opts || {});
    // 非对称喘气余量：起始(lead-in)与结尾(trail)可分别设置。
    // 未显式给 padStart/padEnd 时退回对称 padFrames，保持旧行为。
    const padStart = (opts && opts.padStart != null) ? opts.padStart : o.padFrames;
    const padEnd = (opts && opts.padEnd != null) ? opts.padEnd : o.padFrames;
    const periods = (silencePeriods || []).slice().sort((a, b) => a.start - b.start);

    // 1) 合并删除段
    const sorted = (deleteList || []).slice().sort((a, b) => a.start - b.start);
    const merged = [];
    for (const seg of sorted) {
      const last = merged[merged.length - 1];
      if (!last || seg.start > last.end + o.mergeGap) merged.push({ start: seg.start, end: seg.end });
      else last.end = Math.max(last.end, seg.end);
    }

    // 2) 取反得保留段，并把边界吸附到最近静音
    const keepSegments = [];
    let cursor = 0;
    for (const del of merged) {
      if (del.start > cursor + o.minKeepDur) {
        const silEnd = findNextSilenceEnd(periods, cursor, cursor + o.lookBack);
        const trimmedStart = silEnd !== null ? silEnd - padStart : cursor;

        const silStart = findLastSilenceStart(periods, del.start, del.start - o.lookBack);
        const trimmedEnd = silStart !== null ? silStart + padEnd : del.start;

        if (trimmedEnd > trimmedStart + o.minKeepDur) {
          keepSegments.push({ start: trimmedStart, end: trimmedEnd });
        }
      }
      cursor = del.end;
    }
    if (cursor < duration - o.minKeepDur) {
      const silEnd = findNextSilenceEnd(periods, cursor, cursor + o.lookBack);
      const trimmedStart = silEnd !== null ? silEnd - padStart : cursor;
      keepSegments.push({ start: trimmedStart, end: duration });
    }

    // 3) 保留段内部长静音二次切割
    const finalKeeps = [];
    for (const keep of keepSegments) {
      const internal = periods.filter(sp =>
        sp.start > keep.start + o.edgeMargin &&
        sp.end < keep.end - o.edgeMargin &&
        (sp.end - sp.start) >= o.minInternalSilence
      );
      let cur = keep.start;
      for (const sp of internal) {
        if (sp.start + padEnd > cur + o.minKeepDur) finalKeeps.push({ start: cur, end: sp.start + padEnd });
        cur = sp.end;
      }
      if (keep.end > cur + o.minKeepDur) finalKeeps.push({ start: cur, end: keep.end });
    }

    return finalKeeps;
  }

  // 区间相减：a 减去 b（两侧都已按 start 升序、内部不重叠），丢弃短于 minDur 的碎片。
  // 审核页用它算「算法切了、但用户没选」的误伤段（cuts − deleteSegs）。
  function intervalSubtract(a, b, minDur) {
    const min = minDur == null ? 0.02 : minDur;
    const out = [];
    for (const c of a) {
      let segs = [{ start: c.start, end: c.end }];
      for (const d of b) {
        const next = [];
        for (const s of segs) {
          if (d.end <= s.start || d.start >= s.end) { next.push(s); continue; }
          if (d.start > s.start) next.push({ start: s.start, end: d.start });
          if (d.end < s.end) next.push({ start: d.end, end: s.end });
        }
        segs = next;
      }
      for (const s of segs) if (s.end - s.start > min) out.push(s);
    }
    return out;
  }

  // 保留段取反 → 实际被切掉的区间（含吸附/二次切的「误伤」）
  function keepsToCuts(finalKeeps, duration) {
    const cuts = [];
    let cursor = 0;
    for (const k of finalKeeps) {
      if (k.start > cursor + 1e-6) cuts.push({ start: cursor, end: k.start });
      cursor = Math.max(cursor, k.end);
    }
    if (cursor < duration - 1e-6) cuts.push({ start: cursor, end: duration });
    return cuts;
  }

  return { computeFinalKeeps, keepsToCuts, intervalSubtract, DEFAULTS };
});
