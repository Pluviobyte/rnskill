#!/usr/bin/env node
/*
 * 首次使用环境自检（跨平台 Win / macOS / Linux）
 *
 * 用法:
 *   node doctor.js            正常自检；全绿则写 .setup_done，下次自动跳过
 *   node doctor.js --force    忽略 .setup_done，强制重新检测
 *   node doctor.js --json     额外在末尾输出一行 JSON（给上层程序解析）
 *
 * 退出码: 0 = 全部通过；1 = 有未通过项（需引导用户修复）
 *
 * 设计要点:
 *   - 三层检查：系统依赖 → 凭证文件 → 联网实测 key+两个资源
 *   - 第三层用极小假音频 ping，只看鉴权层状态码，几乎不耗免费额度
 *   - 全绿后写 SKILL_DIR/.setup_done，SKILL.md 步骤 -1 见此文件即跳过引导
 */

'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const https = require('https');
const crypto = require('crypto');
const { spawnSync } = require('child_process');

const isWin = process.platform === 'win32';
const isMac = process.platform === 'darwin';
const HOME = os.homedir();
const SKILL_DIR = path.resolve(__dirname, '..');
const SENTINEL = path.join(SKILL_DIR, '.setup_done');
// .env 候选位置（与 agent / 安装位置无关）：显式指定 → skill 内 → skill 上一级（兼容 Claude Code 旧约定）
const ENV_CANDIDATES = [
  process.env.VOLCENGINE_ENV_FILE,
  path.join(SKILL_DIR, '.env'),
  path.join(path.dirname(SKILL_DIR), '.env'),
].filter(Boolean);
const RECOMMEND_ENV = path.join(SKILL_DIR, '.env');

const args = process.argv.slice(2);
const FORCE = args.includes('--force');
const JSON_OUT = args.includes('--json');

// ── 终端着色（Windows 新终端也支持 ANSI）─────────────────
const useColor = process.stdout.isTTY;
const paint = (code, s) => (useColor ? `\x1b[${code}m${s}\x1b[0m` : s);
const C = {
  green: s => paint('32', s), red: s => paint('31', s),
  yellow: s => paint('33', s), dim: s => paint('2', s),
  bold: s => paint('1', s), cyan: s => paint('36', s),
};
const OK = C.green('✅'), BAD = C.red('❌'), WARN = C.yellow('⚠️ ');

// ── 已配置则快速跳过（除非 --force）──────────────────────
if (!FORCE && fs.existsSync(SENTINEL)) {
  console.log(`${OK} 环境已配置完成（${C.dim('如需重新检测：node doctor.js --force')}）`);
  process.exit(0);
}

// ── 自愈：补回 .sh 执行位 ────────────────────────────────
// git clone / 解压后 shell 脚本常丢失可执行位，导致 "permission denied"。
// 主流程已统一用 `bash <script>` 调用（不依赖此位），这里再兜底，方便直接 ./xxx.sh 调用。
function fixShebangs() {
  if (isWin) return; // Windows 无执行位概念
  const dir = path.join(SKILL_DIR, 'scripts');
  try {
    for (const f of fs.readdirSync(dir)) {
      if (!f.endsWith('.sh')) continue;
      try { fs.chmodSync(path.join(dir, f), 0o755); } catch (_) {}
    }
  } catch (_) {}
}

// ── 第一层：系统依赖 ─────────────────────────────────────
function probe(cmd, arg) {
  try {
    const r = spawnSync(cmd, [arg], { stdio: 'ignore', timeout: 5000, windowsHide: true });
    return !r.error; // r.error 在找不到命令(ENOENT)时被设置
  } catch (_) { return false; }
}

const winHint = (mac, win) => (isWin ? win : mac);

const DEPS = [
  {
    name: 'ffmpeg', ok: () => probe('ffmpeg', '-version'),
    why: '从视频里抽音频',
    hint: winHint('brew install ffmpeg',
      'winget install Gyan.FFmpeg   或   scoop install ffmpeg'),
  },
  {
    name: 'node', ok: () => probe('node', '-v'),
    why: '跑本 Skill 的所有脚本',
    hint: winHint('brew install node', 'winget install OpenJS.NodeJS'),
  },
  {
    name: 'python3', ok: () => probe('python3', '--version') || probe('python', '--version'),
    why: '音频 base64 编码 / 结果解析',
    hint: winHint('brew install python',
      'winget install Python.Python.3.12   （装完确保 python 在 PATH）'),
  },
  {
    name: 'curl', ok: () => probe('curl', '--version'),
    why: '调用火山引擎转录接口',
    hint: winHint('macOS 自带，通常无需安装',
      'Windows 10+ 自带；若缺失：winget install cURL.cURL'),
  },
];

function checkDeps() {
  console.log(C.bold('\n[1/3] 系统依赖'));
  const missing = [];
  for (const d of DEPS) {
    const ok = d.ok();
    console.log(`  ${ok ? OK : BAD} ${d.name.padEnd(8)} ${C.dim(d.why)}`);
    if (!ok) { console.log(`        ${C.yellow('安装：')}${d.hint}`); missing.push(d.name); }
  }
  return missing;
}

// ── 第二层：凭证文件 ─────────────────────────────────────
const PLACEHOLDERS = ['your_api_key_here', 'your-api-key', 'xxx', '<your_api_key>', ''];

function parseKeyFromFile(f) {
  let key = '';
  for (const line of fs.readFileSync(f, 'utf8').split(/\r?\n/)) {
    const m = line.match(/^\s*VOLCENGINE_API_KEY\s*=\s*(.*)$/);
    if (m) key = m[1].trim().replace(/^["']|["']$/g, '');
  }
  return key;
}

function readKey() {
  // 1) 环境变量优先（最通用，任何 agent / CI 都能用）
  const envKey = (process.env.VOLCENGINE_API_KEY || '').trim();
  if (envKey && !PLACEHOLDERS.includes(envKey.toLowerCase())) {
    return { state: 'ok', key: envKey, source: '环境变量' };
  }
  // 2) 依次查候选 .env 文件
  let sawFile = false;
  for (const f of ENV_CANDIDATES) {
    if (!fs.existsSync(f)) continue;
    sawFile = true;
    const key = parseKeyFromFile(f);
    if (!key) continue;
    if (PLACEHOLDERS.includes(key.toLowerCase())) return { state: 'placeholder', source: f };
    return { state: 'ok', key, source: f };
  }
  return { state: sawFile ? 'missing_key' : 'missing_file' };
}

function checkEnv() {
  console.log(C.bold('\n[2/3] API Key 凭证'));
  const r = readKey();
  if (r.state === 'ok') {
    console.log(`  ${OK} 找到 VOLCENGINE_API_KEY（${C.dim(r.key.slice(0, 8) + '…')}，来自 ${r.source}）`);
    return r;
  }
  const msg = {
    missing_file: `${BAD} 没找到 API Key（环境变量和 .env 都没有）`,
    missing_key: `${BAD} .env 里缺 VOLCENGINE_API_KEY`,
    placeholder: `${WARN} VOLCENGINE_API_KEY 还是占位符，没换成真 key`,
  }[r.state];
  console.log(`  ${msg}`);
  console.log(C.yellow(`   方式一(推荐)：在 ${RECOMMEND_ENV} 写一行  VOLCENGINE_API_KEY=你的key`));
  console.log(C.yellow('   方式二：export VOLCENGINE_API_KEY=你的key'));
  console.log(C.yellow('   key 申请：https://console.volcengine.com/speech/new/overview'));
  return r;
}

// ── 第三层：联网实测 key + 两个资源 ──────────────────────
// 只发极小假音频，看鉴权层状态码：
//   45000010 → key 无效；45000151 → 该资源未开通；其它 → 鉴权通过
function ping(apiKey, resourceId, urlPath) {
  return new Promise(resolve => {
    const body = JSON.stringify({
      user: { uid: 'doctor' },
      audio: { data: Buffer.from('ping').toString('base64') },
      request: { model_name: 'bigmodel' },
    });
    const req = https.request({
      hostname: 'openspeech.bytedance.com',
      path: urlPath, method: 'POST',
      headers: {
        'X-Api-Key': apiKey,
        'X-Api-Resource-Id': resourceId,
        'X-Api-Request-Id': crypto.randomUUID(),
        'X-Api-Sequence': '-1',
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
      },
    }, res => {
      const status = res.headers['x-api-status-code'] || '';
      const message = res.headers['x-api-message'] || '';
      res.on('data', () => {});
      res.on('end', () => resolve({ status, message }));
    });
    req.on('error', e => resolve({ status: '', message: '', netErr: e.message }));
    req.setTimeout(12000, () => { req.destroy(); resolve({ status: '', message: '', netErr: '超时' }); });
    req.write(body);
    req.end();
  });
}

function interpret(name, openHint, r) {
  if (r.netErr) {
    console.log(`  ${WARN} ${name}：无法连接火山引擎（${r.netErr}）— 检查网络后重试`);
    return 'unknown';
  }
  if (r.status === '45000010') {
    console.log(`  ${BAD} ${name}：API Key 无效（确认来自「新版」控制台）`);
    return 'badkey';
  }
  if (r.status === '45000151') {
    console.log(`  ${BAD} ${name}：资源未开通`);
    console.log(`        ${C.yellow('去控制台开通：')}${openHint}`);
    return 'noresource';
  }
  console.log(`  ${OK} ${name}：可用`);
  return 'ok';
}

async function checkResources(apiKey) {
  console.log(C.bold('\n[3/3] 联网实测（key + 两个资源）'));
  const [flash, std] = await Promise.all([
    ping(apiKey, 'volc.bigasr.auc_turbo', '/api/v3/auc/bigmodel/recognize/flash'),
    ping(apiKey, 'volc.bigasr.auc', '/api/v3/auc/bigmodel/submit'),
  ]);
  const rf = interpret('极速版 auc_turbo', '「录音文件识别-极速版」', flash);
  const rs = interpret('标准版 auc', '「录音文件识别-标准版」', std);
  if (rf === 'badkey' || rs === 'badkey') {
    console.log(C.dim('   两个引擎共用同一个 key；key 无效会一起失败。'));
  }
  if ((rf === 'ok') !== (rs === 'ok')) {
    console.log(C.dim('   提示：默认 auto 轮流需两个资源都开通才能吃满 ≈40h；'));
    console.log(C.dim('   只想用一个，转录时加 --flash 或 --v3-standard 即可。'));
  }
  return { flash: rf, std: rs };
}

// ── 主流程 ───────────────────────────────────────────────
(async () => {
  console.log(C.cyan(C.bold('🩺 AI剪口播 · 环境自检')) + C.dim(`  (${process.platform})`));

  fixShebangs();
  const missingDeps = checkDeps();
  const env = checkEnv();

  let res = null;
  const canPing = env.state === 'ok';
  if (canPing) {
    res = await checkResources(env.key);
  } else {
    console.log(C.bold('\n[3/3] 联网实测'));
    console.log(`  ${C.dim('跳过 — 先把上面的 API Key 配好再测')}`);
  }

  const depsOk = missingDeps.length === 0;
  const envOk = env.state === 'ok';
  const resOk = !!res && res.flash === 'ok' && res.std === 'ok';
  const allGreen = depsOk && envOk && resOk;

  console.log(C.bold('\n── 结论 ' + '─'.repeat(28)));
  if (allGreen) {
    fs.writeFileSync(SENTINEL, new Date().toISOString() + '\n');
    console.log(`${OK} ${C.green('全部通过！')}已记录，下次使用不再打扰。`);
    console.log(C.dim(`   标记文件：${SENTINEL}`));
  } else {
    const todo = [];
    if (!depsOk) todo.push(`装依赖：${missingDeps.join(' / ')}`);
    if (!envOk) todo.push('配置 API Key 到 .env');
    if (envOk && !resOk) todo.push('开通缺失的火山引擎资源');
    console.log(`${BAD} ${C.red('还差几步：')}`);
    todo.forEach((t, i) => console.log(`   ${i + 1}. ${t}`));
    console.log(C.dim('   修好后重跑：node doctor.js'));
  }

  if (JSON_OUT) {
    console.log('__DOCTOR_JSON__ ' + JSON.stringify({
      allGreen, depsOk, missingDeps, envState: env.state,
      flash: res && res.flash, std: res && res.std, platform: process.platform,
    }));
  }
  process.exit(allGreen ? 0 : 1);
})();
