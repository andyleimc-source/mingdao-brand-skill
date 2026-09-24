// deck-lib.js — 用 pptxgenjs 生成合规 PPT 的最小工具层
//
// 这不是 SKILL-STATUS.md 里规划的 scripts/ppt/ 框架，是一份可直接跑的参考实现，
// 把散在各规范文件里的常量和规则集中成代码，避免每次做 PPT 重新推导、重新踩坑。
//
// 对应规范：
//   references/common/design-foundation.md    颜色 / 字号比例 / 对比度
//   references/brands/mingdao.md              本示例的明道云降级字体
//   references/common/grid-system.md          边距 / 列宽 / 8px 模数
//   references/common/logo.md                 Logo 尺寸
//   references/materials/ppt/workflow.md      pptxgenjs 实现约束
//   references/materials/ppt/components.md    Icon Token / Text Pair / Group Card
//   references/materials/ppt/layouts.md       页面版式

// ── 画布与单位 ────────────────────────────────────────────────────
// 空间布局使用 1920×1080 逻辑像素，写入 x/y/w/h 时统一换算为英寸。
// 字号和绝对行距直接使用 pt，不复用空间坐标的换算函数。
const CANVAS = { w: 1920, h: 1080, in: { w: 13.333, h: 7.5 } };
const IN = (px) => px / 144;

// ── 网格（grid-system.md 公式对 1920 画布的解，与 layouts.md 一致）──
const MARGIN = 148, COL = 128, GUT = 8, MODULE = 8;
const USABLE = CANVAS.w - 2 * MARGIN;              // 1624
const span = (n) => n * COL + (n - 1) * GUT;       // 跨 n 列的宽度
const colX = (n) => MARGIN + n * (COL + GUT);      // 第 n 列左边界

// ── 色板（design-foundation.md 1.1 / 1.1.1）─────────────────────────
const C = {
  blue: "1677FF", grey: "E0E5EC", navy: "082C5E", white: "FFFFFF",
  ink: "151A21", ink2: "4E535C", ink3: "767A80", disabled: "C1C7CF",
  ruleStrong: "D6DBE2", ruleSoft: "E0E5EC", surface: "EBF0F6",
};

// ── 字号（components.md；全部直接使用 pt）─────────────────────────
const FS = { page: 28, card: 20, body: 14, note: 10 };
const FS_MIN_RATIO = 0.7;   // design-foundation 1.2「字号下限」= 0.7 × 正文基准

// 字体：显式指定思源黑体真实字面，不让渲染器用 bold:true 猜替代字体
const FONT = {
  zh: "思源黑体 CN",
  zhBold: "思源黑体 CN Bold",
  mono: "Menlo",
};

// ── 对比度（把 design-foundation 1.1 的表变成可执行断言）───────────
const srgb = (c) => { c /= 255; return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; };
function luminance(hex) {
  const h = hex.replace("#", "");
  const [r, g, b] = [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16));
  return 0.2126 * srgb(r) + 0.7152 * srgb(g) + 0.0722 * srgb(b);
}
function contrast(a, b) {
  const [x, y] = [luminance(a), luminance(b)].sort((m, n) => n - m);
  return (x + 0.05) / (y + 0.05);
}

/**
 * 文字放上背景前先过这一关，不合规直接抛错——不要等渲染出来靠肉眼看。
 * WCAG：大字（≥18pt，或 ≥14pt 且加粗）门槛 3.0，其余 4.5。
 * 典型后果：白字压品牌蓝 #1677FF 只有 4.10，做正文不合规、只能做大字。
 */
function assertReadable(fg, bg, sizePt, bold = false) {
  const isLarge = sizePt >= 18 || (sizePt >= 14 && bold);
  const need = isLarge ? 3.0 : 4.5;
  const got = contrast(fg, bg);
  if (got < need) {
    throw new Error(
      `对比度不足：#${fg} on #${bg} = ${got.toFixed(2)}，` +
      `${sizePt}pt${bold ? " 粗体" : ""} 需要 ≥ ${need}。` +
      `改用更大字号、换文字色，或把这段文字挪到浅色底上。`
    );
  }
  return got;
}

// ── Logo（logo.md 公式对 1920 画布的解）───────────────────────────
// 基准宽度 1624 → 占比 0.1127 → 宽 184px；高按各文件 viewBox 实测比例换算
const LOGO_RATIO = { full: 2.043, simple: 3.228 };
const LOGO_W = 184;
const logoH = (variant = "full") => LOGO_W / LOGO_RATIO[variant];

// ── 基础绘制件 ────────────────────────────────────────────────────
/** 所有文本都走这里：强制 margin:0，强制绝对行距，杜绝两个最常见的排版事故 */
function txt(slide, text, o) {
  const { sizePt, bold = false, color, bg, lineSpacingPt, fontFace, ...rest } = o;
  if (bg) assertReadable(color, bg, sizePt, bold);
  const resolvedFontFace = fontFace ?? (bold ? FONT.zhBold : FONT.zh);
  const resolvedBold = fontFace ? bold : false;
  return slide.addText(text, {
    margin: 0,                                   // pptxgenjs 默认 inset 会顶偏全部坐标
    fontFace: resolvedFontFace,
    align: "left",
    valign: "top",
    fontSize: sizePt,
    bold: resolvedBold,
    color,
    // 绝对行距（磅）。中文字体自带约 1.4em 行高，再用 lineSpacingMultiple 相乘
    // 会让实际行距接近字号 2 倍，文本框高度全部算小
    lineSpacing: lineSpacingPt ?? Math.round(sizePt * 1.4),
    ...rest,
  });
}

/** 一行文字占多高（逻辑 px）——绝对行距使用 pt，1pt 对应 2 个逻辑 px */
const lineH = (sizePt, lineSpacingPt) => (lineSpacingPt ?? Math.round(sizePt * 1.4)) * 2;
const blockH = (sizePt, lines, lineSpacingPt) => lineH(sizePt, lineSpacingPt) * lines;

/**
 * Icon Token：圆形容器 + Material Symbols PNG（components.md 尺寸档位）
 * 图标 PNG 必须由 scripts/common/material_symbols.py render 生成。
 * 该脚本已按实际墨迹居中，这里直接把 PNG 摆进圆心即可；
 * 若你的 PNG 是旧版本脚本产出的（墨迹按基线定位、每个图标偏移量不同），
 * 请重新渲染，不要在这里做偏移补偿。
 */
const TOKEN = { large: { size: 88, pad: 16 }, medium: { size: 64, pad: 12 }, small: { size: 56, pad: 10 } };
function iconToken(slide, pres, { x, y, icon, iconDir, bg = C.blue, tier = "medium" }) {
  const { size, pad } = TOKEN[tier];
  slide.addShape(pres.ShapeType.ellipse, {
    x: IN(x), y: IN(y), w: IN(size), h: IN(size), fill: { color: bg }, line: { type: "none" },
  });
  slide.addImage({
    path: `${iconDir}/${icon}`,
    x: IN(x + pad), y: IN(y + pad), w: IN(size - 2 * pad), h: IN(size - 2 * pad),
  });
  return size;
}

/** Group Card / Card Wrapper（components.md 三种样式，圆角固定 4px）*/
const CARD_STYLE = {
  emphasis: { fill: C.blue, line: null },        // 注意：蓝底只能放大字，正文放上去不合规
  secondary: { fill: C.grey, line: null },
  outlined: { fill: C.white, line: C.blue },
};
function card(slide, pres, { x, y, w, h, style = "secondary" }) {
  const s = CARD_STYLE[style];
  slide.addShape(pres.ShapeType.roundRect, {
    x: IN(x), y: IN(y), w: IN(w), h: IN(h), rectRadius: IN(4),
    fill: { color: s.fill },
    ...(s.line ? { line: { color: s.line, width: 1 } } : { line: { type: "none" } }),
  });
}

/** Divider（同类元素纵向堆叠时用；与上下文字至少留 8px）*/
function divider(slide, pres, { x, y, w, color = C.ruleStrong }) {
  slide.addShape(pres.ShapeType.rect, {
    x: IN(x), y: IN(y), w: IN(w), h: IN(1), fill: { color }, line: { type: "none" },
  });
}

/** 8px 模数校验：布局尺寸必须是模数整数倍（字号不受此限，用 2px 原子尺寸）*/
function assertModule(...values) {
  const bad = values.filter((v) => v % MODULE !== 0);
  if (bad.length) throw new Error(`不是 ${MODULE}px 模数的整数倍：${bad.join(", ")}`);
}

function newDeck(title, author = "明道云市场部") {
  const PptxGenJS = require("pptxgenjs");
  const pres = new PptxGenJS();
  pres.defineLayout({ name: "HD16x9", width: CANVAS.in.w, height: CANVAS.in.h });
  pres.layout = "HD16x9";                        // 必须在 addSlide() 之前
  pres.title = title;
  pres.author = author;
  return pres;
}

module.exports = {
  CANVAS, IN, MARGIN, COL, GUT, MODULE, USABLE, span, colX,
  C, FS, FS_MIN_RATIO, FONT, LOGO_W, logoH, LOGO_RATIO, TOKEN, CARD_STYLE,
  contrast, assertReadable, assertModule,
  txt, lineH, blockH, iconToken, card, divider, newDeck,
};
