#!/usr/bin/env node
// ============================================================
// render.cjs — 小红书长文转图片 · 渲染脚本
// 用 Playwright 打开任务目录下的 index.html，
// 把页面里所有 .card / .dcard / .ecard / .femcard 卡片节点逐张截图导出为 PNG。
//
// 用法：
//   node render.cjs <任务目录> [--scale 1|2] [--html 文件名]
//   · 任务目录：包含 index.html 的文件夹，PNG 输出到其 output/ 子目录
//   · --scale：清晰度倍率，默认 1（即 1080×1440 原始尺寸），2 = 2160×2880
//   · --html：自定义 HTML 文件名，默认 index.html
// ============================================================
const path = require('path');
const fs = require('fs');
const { pathToFileURL } = require('url');

function resolvePlaywright(taskDir) {
  const candidates = [
    path.join(process.cwd(), 'node_modules', 'playwright'),
    path.join(taskDir, 'node_modules', 'playwright'),
    path.join(__dirname, '..', 'node_modules', 'playwright'),
    'playwright',
  ];
  for (const c of candidates) {
    try { return require(c); } catch (_) { /* 尝试下一个候选路径 */ }
  }
  throw new Error('找不到 playwright，请先执行 npm install && npx playwright install chromium');
}

(async () => {
  // ---------- 解析命令行参数 ----------
  const args = process.argv.slice(2);
  if (args.includes('--help') || args.includes('-h')) {
    console.log(`Usage:
  xhs-render <task-dir> [--scale 1|2] [--html index.html]

Examples:
  xhs-render ./preview
  xhs-render ./work/my-article --scale 2`);
    process.exit(0);
  }
  const taskDir = path.resolve(args[0] || '.');
  const scaleIdx = args.indexOf('--scale');
  const scale = scaleIdx > -1 ? Number(args[scaleIdx + 1]) || 1 : 1;
  const htmlIdx = args.indexOf('--html');
  const htmlName = htmlIdx > -1 ? args[htmlIdx + 1] : 'index.html';

  const htmlPath = path.join(taskDir, htmlName);
  if (!fs.existsSync(htmlPath)) {
    console.error('找不到 HTML 文件:', htmlPath);
    process.exit(1);
  }
  const outDir = path.join(taskDir, 'output');
  fs.mkdirSync(outDir, { recursive: true });

  const { chromium } = resolvePlaywright(taskDir);
  const browser = await chromium.launch();
  // deviceScaleFactor 控制截图清晰度；卡片本身已是 1080×1440 实际像素
  const page = await browser.newPage({ deviceScaleFactor: scale });
  await page.goto(pathToFileURL(htmlPath).href, { waitUntil: 'networkidle' });

  // 等 Google Fonts 等网络字体全部就绪，避免截到回退字体
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(800);

  // ---------- 逐张截图 ----------
  // 选所有卡片节点（A/B/C 用 .card、D 用 .dcard、E 用 .ecard、女性向三主题用 .femcard），按 DOM 顺序导出；
  // 文件名优先用节点 id，否则用序号
  const handles = await page.$$('.card, .dcard, .ecard, .femcard');
  if (handles.length === 0) {
    console.error('页面里没有 .card / .dcard / .ecard / .femcard 节点，请检查 HTML');
    await browser.close();
    process.exit(1);
  }
  let i = 0;
  for (const el of handles) {
    i += 1;
    const id = await el.getAttribute('id');
    const name = (id || `card-${String(i).padStart(2, '0')}`) + '.png';
    await el.screenshot({ path: path.join(outDir, name) });
    // 输出实际尺寸方便核对（应为 1080×1440 × scale）
    const box = await el.boundingBox();
    console.log(`已导出 ${name}  (${Math.round(box.width * scale)}×${Math.round(box.height * scale)})`);
  }

  await browser.close();
  console.log(`完成：共 ${i} 张 → ${outDir}`);
})();
