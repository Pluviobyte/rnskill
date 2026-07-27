#!/usr/bin/env node
/* ============================================================
   _gen-fem.cjs — 把 cards-fem.jsx 的三主题设计稿 1:1 移植成静态 HTML
   说明：本脚本仅用于一次性生成 template.html 里的「女性向三主题」卡片段，
        把 JSX 里的 SVG 装饰组件（含计算型坐标）忠实渲染成静态标记。
        生成结果会打印到 stdout，由调用方写进模板。
   ============================================================ */

// 把内联样式对象转成 CSS 字符串：数值默认补 px，opacity/transform 等保持原样
function sty(o) {
  const unitless = new Set(["opacity", "zIndex", "fontWeight", "lineHeight", "flex"]);
  return Object.entries(o)
    .map(([k, v]) => {
      const prop = k.replace(/[A-Z]/g, (m) => "-" + m.toLowerCase());
      const val = typeof v === "number" && !unitless.has(k) ? `${v}px` : v;
      return `${prop}:${val}`;
    })
    .join(";");
}

/* ===================== SVG 图案库（移植自 cards-fem.jsx） ===================== */
// 通用
const Sparkle = (s = 40, cn = "", style = {}) =>
  `<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="currentColor" class="${cn}" style="${sty(style)}"><path d="M12 0c1.2 8.4 3.4 10.8 12 12-8.6 1.2-10.8 3.6-12 12-1.2-8.4-3.4-10.8-12-12C8.6 10.8 10.8 8.4 12 0z"/></svg>`;
const Star = (s = 20, cn = "", style = {}) =>
  `<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="currentColor" class="${cn}" style="${sty(style)}"><path d="M12 2l2.6 6.6L21 11l-6.4 2.4L12 20l-2.6-6.6L3 11l6.4-2.4z"/></svg>`;
// 粉色王国
const Rainbow = (w = 520, cn = "", style = {}) => {
  const arcs = ["#FF9EC4", "#FFC18E", "#FFE59E", "#A8E6A1", "#9ED6F0", "#C9A8F0"]
    .map(
      (c, i) =>
        `<path d="M${30 + i * 22} 270 A ${230 - i * 22} ${230 - i * 22} 0 0 1 ${490 - i * 22} 270" stroke="${c}" stroke-width="20" stroke-linecap="round"/>`
    )
    .join("");
  return `<svg width="${w}" height="${w / 2 + 10}" viewBox="0 0 520 270" fill="none" class="${cn}" style="${sty(style)}">${arcs}</svg>`;
};
const Cloud = (w = 200, cn = "", style = {}) =>
  `<svg width="${w}" height="${w * 0.62}" viewBox="0 0 200 124" fill="currentColor" class="${cn}" style="${sty(style)}"><path d="M48 110c-24 0-40-16-40-36s17-35 38-34c5-22 24-34 44-34 24 0 42 16 46 38 18 1 32 14 32 32 0 19-15 34-37 34z"/></svg>`;
const Castle = (w = 300, cn = "", style = {}) =>
  `<svg width="${w}" height="${w * 0.7}" viewBox="0 0 300 210" fill="none" stroke="currentColor" stroke-width="2.2" class="${cn}" style="${sty(style)}"><path d="M40 205V90l24-18 24 18v115M150 205V70l30-24 30 24v135M252 205V96l20-15 20 15v109"/><path d="M64 72l-10-26 20 8 20-8-10 26M180 46l-12-30 24 10 24-10-12 30M272 81l-8-22 16 7 16-7-8 22"/><path d="M20 205h270"/></svg>`;
// 乙游：花纹角、蝴蝶、月、罗马环
const Filigree = (cn = "", style = {}) =>
  `<svg width="180" height="180" viewBox="0 0 180 180" fill="none" stroke="currentColor" stroke-width="1.3" class="${cn}" style="${sty(style)}"><path d="M10 10c40 0 70 6 70 40 0 18-12 30-28 30-12 0-20-8-20-18 0-8 6-14 14-14"/><path d="M10 10c0 40 6 70 40 70 18 0 30-12 30-28 0-12-8-20-18-20"/><circle cx="32" cy="32" r="4" fill="currentColor" stroke="none"/><path d="M10 50c14 2 24 8 30 18M50 10c2 14 8 24 18 30"/></svg>`;
const Butterfly = (s = 60, cn = "", style = {}) =>
  `<svg width="${s}" height="${s}" viewBox="0 0 60 60" fill="currentColor" class="${cn}" style="${sty(style)}"><path d="M30 30c-4-14-14-22-24-20-6 1-7 9-3 16 4 8 16 10 27 8zM30 30c4-14 14-22 24-20 6 1 7 9 3 16-4 8-16 10-27 8zM30 28c-3 12-12 20-21 22 7 4 16 1 21-8zM30 28c3 12 12 20 21 22-7 4-16 1-21-8z" opacity="0.9"/><path d="M30 22v20" stroke="currentColor" stroke-width="1.4"/></svg>`;
const Moon = (s = 120, cn = "", style = {}) =>
  `<svg width="${s}" height="${s}" viewBox="0 0 120 120" fill="none" class="${cn}" style="${sty(style)}"><path d="M78 12a48 48 0 1 0 30 86A40 40 0 0 1 78 12z" fill="currentColor" opacity="0.16"/><path d="M78 12a48 48 0 1 0 30 86A40 40 0 0 1 78 12z" stroke="currentColor" stroke-width="1.2"/></svg>`;
const RomanRing = (s = 300, cn = "", style = {}) => {
  const nums = ["XII", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"]
    .map((r, i) => {
      const a = ((i * 30 - 90) * Math.PI) / 180;
      const x = 150 + 130 * Math.cos(a);
      const y = 150 + 130 * Math.sin(a);
      return `<text x="${x}" y="${y}" font-size="14" fill="currentColor" stroke="none" text-anchor="middle" dominant-baseline="middle" font-family="Cormorant Garamond, serif">${r}</text>`;
    })
    .join("");
  return `<svg width="${s}" height="${s}" viewBox="0 0 300 300" fill="none" stroke="currentColor" stroke-width="1" class="${cn}" style="${sty(style)}"><circle cx="150" cy="150" r="140"/><circle cx="150" cy="150" r="120"/>${nums}</svg>`;
};
// 吉卜力：胖云、山丘、叶、鸟、太阳
const PuffCloud = (w = 240, cn = "", style = {}) =>
  `<svg width="${w}" height="${w * 0.5}" viewBox="0 0 240 120" fill="currentColor" class="${cn}" style="${sty(style)}"><path d="M40 110c-20 0-34-13-34-30 0-15 12-27 28-28 3-16 17-28 34-28 14 0 26 8 31 20 4-3 9-4 14-4 14 0 24 10 24 23 0 2 0 4-1 6 14 2 24 13 24 27 0 16-13 28-30 28z"/></svg>`;
const Hills = (h = 260, cn = "", style = {}) =>
  `<svg width="1080" height="${h}" viewBox="0 0 1080 ${h}" fill="none" class="${cn}" style="${sty(style)}" preserveAspectRatio="none"><path d="M0 ${h} L0 120 Q 270 30 540 110 T 1080 90 L1080 ${h} Z" fill="var(--accent)" opacity="0.16"/><path d="M0 ${h} L0 175 Q 320 100 620 165 T 1080 150 L1080 ${h} Z" fill="var(--accent)" opacity="0.26"/></svg>`;
const Leaf = (s = 80, cn = "", style = {}) =>
  `<svg width="${s}" height="${s}" viewBox="0 0 80 80" fill="none" stroke="currentColor" stroke-width="1.8" class="${cn}" style="${sty(style)}"><path d="M12 68C12 36 36 12 68 12 68 44 44 68 12 68z"/><path d="M20 60 56 24"/></svg>`;
const Bird = (s = 44, cn = "", style = {}) =>
  `<svg width="${s}" height="${s * 0.5}" viewBox="0 0 44 22" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" class="${cn}" style="${sty(style)}"><path d="M3 18C9 6 16 6 22 14 28 6 35 6 41 18"/></svg>`;
const Sun = (s = 130, cn = "", style = {}) => {
  let rays = "";
  for (let i = 0; i < 12; i++) {
    const a = (i * 30 * Math.PI) / 180;
    rays += `<line x1="${65 + 42 * Math.cos(a)}" y1="${65 + 42 * Math.sin(a)}" x2="${65 + 56 * Math.cos(a)}" y2="${65 + 56 * Math.sin(a)}" stroke-linecap="round"/>`;
  }
  return `<svg width="${s}" height="${s}" viewBox="0 0 130 130" fill="none" stroke="currentColor" stroke-width="2" class="${cn}" style="${sty(style)}"><circle cx="65" cy="65" r="30"/>${rays}</svg>`;
};

/* ===================== 装饰散点 / 边框（按主题） ===================== */
function Deco(theme) {
  let inner = "";
  if (theme === "t-pink") {
    inner =
      Rainbow(560, "", { right: -130, top: -40, opacity: 0.85 }) +
      Cloud(230, "dc-white", { left: -50, top: 150, opacity: 0.9 }) +
      Cloud(160, "dc-white", { right: 60, top: 430, opacity: 0.8 }) +
      Castle(300, "dc-soft", { left: 30, bottom: 150, opacity: 0.4 }) +
      Sparkle(42, "dc-white", { left: 120, top: 360 }) +
      Star(26, "dc-white", { right: 180, top: 330 }) +
      Star(20, "dc-white", { left: 70, bottom: 360 }) +
      Sparkle(28, "dc-accent2", { right: 120, bottom: 320 });
  } else if (theme === "t-otome") {
    inner =
      RomanRing(360, "dc-soft", { right: -90, top: -70, opacity: 0.28 }) +
      Moon(140, "dc-accent", { left: 60, top: 200, opacity: 0.5 }) +
      Filigree("dc-accent", { left: 26, top: 26, opacity: 0.7 }) +
      Filigree("dc-accent", { right: 26, bottom: 26, opacity: 0.7, transform: "rotate(180deg)" }) +
      Butterfly(66, "dc-accent2", { right: 150, top: 330, opacity: 0.8, transform: "rotate(-12deg)" }) +
      Butterfly(40, "dc-accent", { left: 120, bottom: 320, opacity: 0.7, transform: "rotate(18deg)" }) +
      Star(16, "dc-white", { right: 260, top: 250, opacity: 0.8 }) +
      Star(12, "dc-white", { left: 200, top: 420, opacity: 0.7 }) +
      Star(14, "dc-white", { right: 120, bottom: 420, opacity: 0.8 });
  } else {
    // t-ghibli
    inner =
      Sun(150, "dc-accent2", { right: 70, top: 70, opacity: 0.5 }) +
      PuffCloud(280, "dc-white", { left: -40, top: 180, opacity: 0.85 }) +
      PuffCloud(180, "dc-white", { right: 130, top: 380, opacity: 0.7 }) +
      Bird(46, "dc-soft", { left: 160, top: 300, opacity: 0.8 }) +
      Bird(32, "dc-soft", { left: 230, top: 330, opacity: 0.7 }) +
      Hills(280, "", { left: 0, bottom: 0 }) +
      Leaf(64, "dc-accent", { right: 60, bottom: 250, opacity: 0.5, transform: "rotate(20deg)" });
  }
  return `<div class="fem-deco">${inner}</div>`;
}
function Frame(theme) {
  return theme === "t-otome" ? `<div class="fem-frame"></div>` : "";
}

/* ===================== 公共结构 ===================== */
const pad = (n) => String(n).padStart(2, "0");
const ICON = {
  "t-pink": Sparkle(22, "dc-accent"),
  "t-otome": Butterfly(24, "dc-accent"),
  "t-ghibli": Leaf(22, "dc-accent"),
};
function FTop(idx) {
  return `<div class="fem-top">
    <div class="fem-brand"><div class="fem-mono"><span>泊</span></div><div class="fem-word">泊舟的AI思考</div></div>
    <div class="fem-idx">${idx}</div>
  </div>`;
}
function FFoot() {
  return `<div class="fem-foot"><div>泊舟的AI思考</div><div>AI<span class="dot"></span>记忆<span class="dot"></span>Agent</div></div>`;
}
function FKick(text, ic) {
  return `<div class="fem-kick">${ic ? `<span class="ic">${ic}</span>` : ""}${text}</div>`;
}
// 普通卡片外壳
function Shell(theme, type, idx, body) {
  return `<section class="femcard ${type} ${theme}" id="">
  ${Deco(theme)}${Frame(theme)}
  ${FTop(idx)}
  <div class="fem-body">${body}</div>
  ${FFoot()}
</section>`;
}

/* ===================== 页型（移植自 cards-fem.jsx） ===================== */
function FCover(theme) {
  return `<section class="femcard fem-cover ${theme}" id="">
  ${Deco(theme)}${Frame(theme)}
  ${FTop("AI MEMORY · 01")}
  <div class="fem-body">
    <h1 class="fem-title cv-title">聊久了 AI<br>为什么会<em>断片</em></h1>
    <div class="cv-kick">${FKick("AI 记忆 · 工程师手记", ICON[theme])}</div>
    <p class="fem-lead cv-lead">前面刚说好的需求，聊到后面它自己改回去了。这篇用大白话讲清：AI 到底怎么记忆。</p>
    <div class="fem-img cv-img"><img class="slot-img" src="assets/cover-hero.jpg" alt=""></div>
  </div>
</section>`;
}
function FStatement(theme, page, total) {
  const body = `${FKick("写在前面")}
    <div style="margin-top:34px">
      <div class="st-big">你以为它<em>记住了</em>，<br>其实它早忘了。</div>
      <p class="st-sub">这不是 AI 笨——是它跟人记事的方式，根本就不一样。</p>
    </div>`;
  return Shell(theme, "fem-statement", `${pad(page)} / ${pad(total)}`, body);
}
function FBody(theme, page, total) {
  const body = `<div class="bp-head">
      ${FKick("CHAPTER 01 · 基础认知")}
      <h2 class="bp-title">AI 的脑子不是硬盘<br>是<em>一张书桌</em></h2>
    </div>
    <div class="bp-flow">
      <p>你说的每句话、它回的每句话，都是摊在桌上的纸。<span class="hl">桌面一满，新的纸就放不下了。</span></p>
      <div class="fem-note"><span class="lab">术语</span><p>这张书桌，技术上叫<em>「上下文窗口」</em>。</p></div>
      <p>更要命的是，AI 没有抽屉——不在桌上的东西，对它就等于不存在。</p>
    </div>`;
  return Shell(theme, "fem-body-pg", `${pad(page)} / ${pad(total)}`, body);
}
function FList(theme, page, total) {
  const rows = [
    ["揉成纸团", "思路一 · 用「扔」", true],
    ["分层档案馆", "思路二 · 用「存」", false],
    ["按需检索", "思路三 · 用「取」", false],
  ];
  const lis = rows
    .map(
      (r, i) =>
        `<div class="fem-li${r[2] ? " on" : ""}"><div class="li-no">${pad(i + 1)}</div><div class="li-cell"><div class="li-name">${r[0]}</div><div class="li-by">${r[1]}</div></div>${r[2] ? `<div class="li-tail">→</div>` : ""}</div>`
    )
    .join("\n    ");
  const body = `<div class="lp-head"><div class="lp-cat">桌面满了，怎么办？</div><div class="lp-arrow">→</div></div>
    ${lis}`;
  return Shell(theme, "fem-list", `${pad(page)} / ${pad(total)}`, body);
}
function FIdea(theme, page, total) {
  const body = `<div class="bp-head" style="margin:40px 0 30px">
      ${FKick("IDEA 01 · 思路一")}
      <h2 class="bp-title">把旧笔记<em>揉成纸团</em></h2>
    </div>
    <div class="bp-flow" style="gap:22px">
      <p>对话快满时，系统自动把前面打包成摘要贴回去，原文永久删除。</p>
      <div class="fem-points">
        <div class="pt"><span class="m">01</span><span class="t">摘要会<b>丢细节</b></span></div>
        <div class="pt"><span class="m">02</span><span class="t">原件不可逆，<b>找不回</b></span></div>
        <div class="pt"><span class="m">03</span><span class="t">越压越糊，成了「摘要的摘要」</span></div>
      </div>
      <div class="fem-conc">能用，但聊得越久，丢得越多。</div>
    </div>`;
  return Shell(theme, "fem-body-pg", `${pad(page)} / ${pad(total)}`, body);
}
function FViews(theme, page, total) {
  const body = `${FKick("小结")}
    <div style="margin-top:14px">
      <h2 class="bp-title" style="margin-top:0">三种思路<br>三种<em>记忆观</em></h2>
      <div class="vw-rows">
        <div class="vw-row"><div class="vw-k">负担</div><div><div class="vw-lab">思路一</div><div class="vw-d">太多了，得压缩掉</div></div></div>
        <div class="vw-row"><div class="vw-k">资产</div><div><div class="vw-lab">思路二</div><div class="vw-d">不能丢，得存好</div></div></div>
        <div class="vw-row"><div class="vw-k"><em>能力</em></div><div><div class="vw-lab">思路三</div><div class="vw-d">会存、会用，还能进化</div></div></div>
      </div>
    </div>`;
  return Shell(theme, "fem-views", `${pad(page)} / ${pad(total)}`, body);
}
function FMedia(theme, page, total) {
  const body = `<div class="mp-head">
      ${FKick("CHAPTER 02 · 为什么重要")}
      <h2 class="bp-title" style="margin-top:16px;font-size:58px">记忆，决定了<br>AI 能<em>走多远</em></h2>
    </div>
    <div class="mp-img"><img class="slot-img" src="assets/media-1.jpg" alt=""></div>
    <div class="mp-cap">没有记忆的 AI，只是永远停在入职第一天的实习生</div>
    <div class="mp-flow"><p>第三种思路给了它一套<span class="hl">能存、能学、能进化</span>的知识系统。</p></div>`;
  return Shell(theme, "fem-media", `${pad(page)} / ${pad(total)}`, body);
}
function FEnding(theme) {
  return `<section class="femcard fem-ending ${theme}" id="">
  ${Deco(theme)}${Frame(theme)}
  ${FTop("AI MEMORY · 终")}
  <div class="fem-body">
    ${FKick("写在最后", ICON[theme])}
    <div style="margin-top:22px">
      <h2 class="ed-title">一个<em>记事</em>的 AI<br>才值得长期合作</h2>
      <p class="ed-sub">Agent 记忆还很早期，但方向已经清晰——未来的 AI 不只更聪明，还会更记事。</p>
      <div><div class="ed-cta">点赞 · 收藏 · 关注我 <span class="arr">→</span></div></div>
    </div>
  </div>
  ${FFoot()}
</section>`;
}

/* ===================== 组装：三主题各一套完整 deck ===================== */
const THEMES = [
  ["t-pink", "F 粉色王国（童话甜粉）"],
  ["t-otome", "G 乙游夜境（暗黑浪漫，深色）"],
  ["t-ghibli", "H 吉卜力（治愈自然）"],
];
const SHORT = { "t-pink": "pink", "t-otome": "otome", "t-ghibli": "ghibli" };

let out = "";
for (const [theme, label] of THEMES) {
  const T = 8;
  const cards = [
    FCover(theme),
    FStatement(theme, 2, T),
    FBody(theme, 3, T),
    FList(theme, 4, T),
    FIdea(theme, 5, T),
    FViews(theme, 6, T),
    FMedia(theme, 7, T),
    FEnding(theme),
  ];
  // 给每张卡片补上有意义的 id：demo-{short}-{页型}
  const ids = ["cover", "statement", "body", "list", "idea", "views", "media", "ending"];
  const withIds = cards.map((c, i) => c.replace('id=""', `id="demo-${SHORT[theme]}-${ids[i]}"`));
  out += `\n<!-- ────────── 女性向 · ${label} · 主题类名 ${theme} ────────── -->\n`;
  out += withIds.join("\n\n") + "\n";
}

process.stdout.write(out);
