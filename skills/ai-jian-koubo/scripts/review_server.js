#!/usr/bin/env node
/**
 * 审核服务器
 *
 * 功能：
 * 1. 提供静态文件服务（review.html, audio.mp3）
 * 2. POST /api/fcpxml - 接收删除列表，导出 FCPXML 工程文件（可导入剪映 / Final Cut Pro）
 *
 * 用法: node review_server.js [port] [video_file]
 * 必须: video_file（无默认值，会检查文件是否存在）
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const { buildFcpxml } = require('./lib/fcpxml');

const PORT = process.argv[2] || 8899;
const VIDEO_FILE = process.argv[3];

if (!VIDEO_FILE) {
  console.error('❌ 错误: 必须指定视频文件路径');
  console.error('用法: node review_server.js [port] [video_file]');
  process.exit(1);
}

if (!fs.existsSync(VIDEO_FILE)) {
  console.error(`❌ 错误: 视频文件不存在: ${VIDEO_FILE}`);
  process.exit(1);
}

// 静音边界，由 generate_review.js 预计算（对 audio.mp3 跑 silencedetect，自适应阈值 = 峰值 - 35dB）
// 切割算法本身在 lib/compute_keeps.js（前后端共用，单一来源）
let silencePeriods = [];
try {
  silencePeriods = JSON.parse(fs.readFileSync('silence_periods.json', 'utf8'));
  silencePeriods.sort((a, b) => a.start - b.start); // 确保按时间升序
  console.log('🔕 读取到 ' + silencePeriods.length + ' 个静音段');
} catch (e) {
  console.warn('⚠️ 读取 silence_periods.json 失败，末尾裁剪已跳过');
}

// 自进化学习需要的原料：词级文本（重建上下文）+ AI 初选 idx（diff 基线）。
// 都在 data.json（generate_review.js 生成，与本进程同在 3_审核/）里，启动时读一次。
let reviewWords = [];
let aiSelectedIdx = [];
try {
  const d = JSON.parse(fs.readFileSync('data.json', 'utf8'));
  reviewWords = Array.isArray(d.words) ? d.words : [];
  aiSelectedIdx = Array.isArray(d.autoSelected) ? d.autoSelected : [];
} catch (e) {
  console.warn('⚠️ 读取 data.json 失败，导出时将无法生成 review_log.json（自进化学习日志）');
}

const MIME_TYPES = {
  '.html': 'text/html',
  '.js': 'application/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.mp3': 'audio/mpeg',
  '.mp4': 'video/mp4',
};

const server = http.createServer((req, res) => {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  // 共享切割算法模块：从 scripts/lib 单一来源直供前端，避免拷贝漂移
  if (req.method === 'GET' && req.url.split('?')[0] === '/lib/compute_keeps.js') {
    const libPath = path.join(__dirname, 'lib', 'compute_keeps.js');
    if (fs.existsSync(libPath)) {
      res.writeHead(200, { 'Content-Type': 'application/javascript' });
      fs.createReadStream(libPath).pipe(res);
    } else {
      res.writeHead(404);
      res.end('Not Found');
    }
    return;
  }

  // 视频文件代理（原始视频不在当前目录时使用）
  if (req.method === 'GET' && req.url.startsWith('/video')) {
    if (!VIDEO_FILE || !fs.existsSync(VIDEO_FILE)) {
      res.writeHead(404);
      res.end('Video not found');
      return;
    }
    const stat = fs.statSync(VIDEO_FILE);
    const ext = path.extname(VIDEO_FILE).toLowerCase();
    const contentType = ext === '.mp4' ? 'video/mp4' : ext === '.mov' ? 'video/quicktime' : 'video/mp4';

    if (req.headers.range) {
      const range = req.headers.range.replace('bytes=', '').split('-');
      const start = parseInt(range[0], 10);
      const end = range[1] ? parseInt(range[1], 10) : stat.size - 1;
      res.writeHead(206, {
        'Content-Type': contentType,
        'Content-Range': `bytes ${start}-${end}/${stat.size}`,
        'Accept-Ranges': 'bytes',
        'Content-Length': end - start + 1,
      });
      fs.createReadStream(VIDEO_FILE, { start, end }).pipe(res);
    } else {
      res.writeHead(200, {
        'Content-Type': contentType,
        'Content-Length': stat.size,
        'Accept-Ranges': 'bytes',
      });
      fs.createReadStream(VIDEO_FILE).pipe(res);
    }
    return;
  }

  // API: 导出 FCPXML
  if (req.method === 'POST' && req.url === '/api/fcpxml') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        // 兼容两种请求体：旧版直接传删除段数组；新版传 { deleteList, opts }
        const parsed = JSON.parse(body);
        const deleteList = Array.isArray(parsed) ? parsed : (parsed.deleteList || []);
        const cutOpts = (parsed && !Array.isArray(parsed) && parsed.opts) ? parsed.opts : undefined;
        const finalSelected = (parsed && !Array.isArray(parsed) && Array.isArray(parsed.finalSelected)) ? parsed.finalSelected : null;

        // FCPXML 生成（含 ffprobe 探测 + 切割算法）抽到 lib/fcpxml.js，便于单测
        const { xml, outputPath: outputFcpxml, finalKeeps, baseName } = buildFcpxml({
          videoFile: VIDEO_FILE,
          deleteList,
          silencePeriods,
          cutOpts,
        });

        fs.writeFileSync(outputFcpxml, xml);
        console.log(`✅ 导出 FCPXML: ${outputFcpxml} (${finalKeeps.length} 片段)`);

        // ── 自进化学习日志 review_log.json ──────────────────────────
        // 与导出 FCPXML 同一次点击产出。AI 初选(aiSelectedIdx) vs 你最终(finalSelected)
        // 的词级 diff，带文字+句子上下文，供「学习」步抽象成 经验规则.md。
        // 只比对词，不比对静音段(isGap)——静音去留由切割参数 opts 管，不进规则学习。
        // 整段包 try/catch：日志失败绝不能影响导出本身。
        try {
          if (finalSelected) {
            const isWord = (i) => reviewWords[i] && !reviewWords[i].isGap;
            // 把某个 idx 还原成「所在句中标出该词」的可读上下文（两侧扩到静音边界或最多 12 词）
            const contextFor = (idx) => {
              let l = idx, r = idx;
              for (let k = 0; k < 12 && l - 1 >= 0 && reviewWords[l - 1] && !reviewWords[l - 1].isGap; k++) l--;
              for (let k = 0; k < 12 && r + 1 < reviewWords.length && reviewWords[r + 1] && !reviewWords[r + 1].isGap; k++) r++;
              let s = '';
              for (let i = l; i <= r; i++) {
                if (reviewWords[i].isGap) continue;
                s += (i === idx) ? '【' + reviewWords[i].text + '】' : reviewWords[i].text;
              }
              return s;
            };
            const entry = (i) => ({
              idx: i,
              text: reviewWords[i] ? reviewWords[i].text : '',
              start: reviewWords[i] ? reviewWords[i].start : null,
              end: reviewWords[i] ? reviewWords[i].end : null,
              context: contextFor(i),
            });
            const aiSet = new Set(aiSelectedIdx);
            const finalSet = new Set(finalSelected);
            const aiOnly = aiSelectedIdx.filter(i => !finalSet.has(i) && isWord(i)).sort((a, b) => a - b);
            const userOnly = finalSelected.filter(i => !aiSet.has(i) && isWord(i)).sort((a, b) => a - b);
            const log = {
              video: baseName,
              exportedAt: new Date().toISOString(),
              opts: cutOpts || null,
              aiSelected: aiSelectedIdx,
              finalSelected,
              segments: finalKeeps.length,
              diff: {
                说明: 'aiOnly=AI想删但你保留了(可能AI过删，该收敛规则)；userOnly=你删了但AI没想到(可能AI漏删，该补规则)',
                aiOnly: aiOnly.map(entry),
                userOnly: userOnly.map(entry),
              },
            };
            const logPath = path.resolve('review_log.json');
            fs.writeFileSync(logPath, JSON.stringify(log, null, 2));
            console.log(`🧠 学习日志: ${logPath} (AI过删 ${aiOnly.length} / 漏删 ${userOnly.length})`);
          } else {
            console.warn('⚠️ 请求未带 finalSelected（旧版前端？），跳过 review_log.json');
          }
        } catch (logErr) {
          console.warn('⚠️ 生成 review_log.json 失败（不影响导出）: ' + logErr.message);
        }

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: true, output: outputFcpxml, segments: finalKeeps.length }));
      } catch (err) {
        console.error('❌ FCPXML 导出失败:', err.message);
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: false, error: err.message }));
      }
    });
    return;
  }

  // API: 下载文件
  if (req.method === 'GET' && req.url.startsWith('/api/download/')) {
    const encodedFileName = req.url.replace('/api/download/', '');
    const fileName = decodeURIComponent(encodedFileName);
    const filePath = path.resolve(fileName);
    if (!fs.existsSync(filePath)) {
      res.writeHead(404);
      res.end('Not Found');
      return;
    }
    const stat = fs.statSync(filePath);
    // RFC 5987 编码（非 ASCII 字符必须编码）
    const rawName = path.basename(filePath);
    const encodedName = encodeURIComponent(rawName);
    const displayName = /[^\x00-\x7F]/.test(rawName)
      ? `UTF-8''${encodedName}`  // RFC 5987 格式
      : `"${rawName}"`;

    res.writeHead(200, {
      'Content-Type': 'application/octet-stream',
      'Content-Disposition': `attachment; filename*=UTF-8''${encodedName}`,
      'Content-Length': stat.size,
    });
    fs.createReadStream(filePath).pipe(res);
    return;
  }

  // 静态文件服务（从当前目录读取）
  let filePath = req.url === '/' ? '/review.html' : req.url;
  filePath = '.' + filePath;

  const ext = path.extname(filePath);
  const contentType = MIME_TYPES[ext] || 'application/octet-stream';

  // 检查文件是否存在
  if (!fs.existsSync(filePath)) {
    res.writeHead(404);
    res.end('Not Found');
    return;
  }

  const stat = fs.statSync(filePath);

  // 支持 Range 请求（音频/视频拖动）
  if (req.headers.range && (ext === '.mp3' || ext === '.mp4')) {
    const range = req.headers.range.replace('bytes=', '').split('-');
    const start = parseInt(range[0], 10);
    const end = range[1] ? parseInt(range[1], 10) : stat.size - 1;

    res.writeHead(206, {
      'Content-Type': contentType,
      'Content-Range': `bytes ${start}-${end}/${stat.size}`,
      'Accept-Ranges': 'bytes',
      'Content-Length': end - start + 1,
    });

    fs.createReadStream(filePath, { start, end }).pipe(res);
    return;
  }

  // 普通请求
  res.writeHead(200, {
    'Content-Type': contentType,
    'Content-Length': stat.size,
    'Accept-Ranges': 'bytes'
  });
  fs.createReadStream(filePath).pipe(res);
});

server.listen(PORT, () => {
  // 落地两个文件到当前目录（3_审核/），让 agent / 用户随时能找到地址并重启：
  //   server_url.txt      — 浏览器要打开的地址
  //   .review_server.pid  — 进程号，用于停止/排障（kill $(cat .review_server.pid)）
  const url = `http://localhost:${PORT}`;
  try {
    fs.writeFileSync('server_url.txt', url + '\n');
    fs.writeFileSync('.review_server.pid', String(process.pid) + '\n');
  } catch (e) { /* 写不进不致命，地址下面也会打印 */ }

  // 输出机器可读的端口号，供 shell 捕获
  console.log('READY_PORT=' + PORT);
  console.log(`
🎬 审核服务器已启动
📍 地址: http://localhost:${PORT}
📹 视频: ${VIDEO_FILE}

操作说明:
1. 在网页中审核 AI 预选的删除片段
2. 点击「导出 FCPXML」按钮
3. 把生成的 .fcpxml 文件拖入剪映 / Final Cut Pro
  `);
});
