// example-deck.js — deck-lib.js 的可运行示例，演示四种最常用的页面类型
//
// 跑之前先渲染图标（默认色即品牌蓝，文件名不带颜色后缀）：
//   python3 ../../scripts/common/material_symbols.py render check_circle --output-dir icons --size 256 --color "#FFFFFF"
//   python3 ../../scripts/common/material_symbols.py render schedule     --output-dir icons --size 256 --color "#FFFFFF"
//   python3 ../../scripts/common/material_symbols.py render hub          --output-dir icons --size 256 --color "#FFFFFF"
// 然后：node example-deck.js
//
// ⚠ 本文件是**结构示例**，文案是示例文案。真实物料必须先完成
//   workflow.md 的生成前内容关卡与 Content QA，禁止把这里的占位文字直接交付。

const path = require("path");
const L = require("./deck-lib");
const { C, FS, MARGIN, USABLE, span, IN } = L;

const ICONS = path.join(__dirname, "icons");
const ic = (n) => `ms-outlined__${n}__f0-w400-g0-o24-s256-cFFFFFF.png`;

const pres = L.newDeck("deck-lib 示例");

// ── 1. 封面：满版品牌蓝 ────────────────────────────────────────────
// 蓝底白字对比度仅 4.10，正文级不合规 → 副标题必须 ≥18pt。
// assertReadable 会在这里挡住违规组合，而不是等渲染出来靠眼睛看。
{
  const s = pres.addSlide();
  s.background = { color: C.blue };
  L.txt(s, "示例标题", {
    x: IN(MARGIN), y: IN(452), w: IN(USABLE), h: IN(212),
    sizePt: 84, bold: true, color: C.white, bg: C.blue,
    valign: "middle", lineSpacingPt: 97,
  });
  L.txt(s, "副标题：蓝底上的文字不能小于 18pt，否则对比度不达标。", {
    x: IN(MARGIN), y: IN(704), w: IN(span(10)), h: IN(112),
    sizePt: 18, color: C.white, bg: C.blue,
  });
}

// ── 2. 章节分隔页：编号用等宽字体，多个章节号竖排才能对齐 ──────────
{
  const s = pres.addSlide();
  s.background = { color: C.navy };
  L.txt(s, "01", {
    x: IN(MARGIN), y: IN(MARGIN), w: IN(span(3)), h: IN(60),
    sizePt: FS.card, bold: true, color: C.white, bg: C.navy, fontFace: L.FONT.mono,
  });
  L.txt(s, "章节标题", {
    x: IN(MARGIN), y: IN(420), w: IN(USABLE), h: IN(248),
    sizePt: 101, bold: true, color: C.white, bg: C.navy,
    valign: "middle", lineSpacingPt: 111,
  });
}

// ── 3. 多特性页：3 列 × 2 行 Feature Item（layouts.md「多特性页」）──
// 子项不带 Card Wrapper；卡片跨 4 列 = 536px，相邻间距 = 1 个 gutter。
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  L.txt(s, "多特性页", {
    x: IN(MARGIN), y: IN(MARGIN), w: IN(USABLE), h: IN(76),
    sizePt: FS.page, bold: true, color: C.ink, bg: C.white,
  });

  const W = span(4), ROW_H = 184, ROW_GAP = 40, TOP = 312;
  L.assertModule(W, ROW_H, ROW_GAP, TOP);

  ["check_circle", "schedule", "hub", "check_circle", "schedule", "hub"].forEach((icon, i) => {
    const x = MARGIN + (i % 3) * (W + L.GUT);
    const y = TOP + Math.floor(i / 3) * (ROW_H + ROW_GAP);
    const size = L.iconToken(s, pres, { x, y, icon: ic(icon), iconDir: ICONS, tier: "medium" });
    const tx = x + size + 16, tw = W - size - 16;   // Icon Token 与文字固定 16px
    L.txt(s, `特性 ${i + 1}`, {
      x: IN(tx), y: IN(y), w: IN(tw), h: IN(52),
      sizePt: FS.card, bold: true, color: C.ink, bg: C.white,
    });
    L.txt(s, "描述文字，两行以内；容器高度用 blockH() 反推，不要拍脑袋给。", {
      x: IN(tx), y: IN(y + 56), w: IN(tw), h: IN(L.blockH(FS.body, 2)),
      sizePt: FS.body, color: C.ink2, bg: C.white,
    });
  });
}

// ── 4. 对照表：两个等高面板 ────────────────────────────────────────
// 强调样式（蓝底）不能装正文，这里左描边右浅灰，两侧都能安全放正文。
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  L.txt(s, "左右对照", {
    x: IN(MARGIN), y: IN(MARGIN), w: IN(USABLE), h: IN(76),
    sizePt: FS.page, bold: true, color: C.ink, bg: C.white,
  });

  const W = span(6), TOP = 300, H = 560, PAD = 40;
  [["左栏", "outlined", C.white], ["右栏", "secondary", C.grey]].forEach(([title, style, bg], i) => {
    const x = MARGIN + i * (W + L.GUT);
    L.card(s, pres, { x, y: TOP, w: W, h: H, style });
    L.txt(s, title, {
      x: IN(x + PAD), y: IN(TOP + PAD), w: IN(W - 2 * PAD), h: IN(56),
      sizePt: FS.card, bold: true, color: C.ink, bg,
    });
    let iy = TOP + PAD + 76;
    ["条目一", "条目二", "条目三"].forEach((item, k) => {
      if (k > 0) L.divider(s, pres, { x: x + PAD, y: iy - 16, w: W - 2 * PAD });
      L.txt(s, `· ${item}`, {
        x: IN(x + PAD), y: IN(iy), w: IN(W - 2 * PAD), h: IN(L.blockH(FS.body, 2)),
        sizePt: FS.body, color: C.ink2, bg,
      });
      iy += 104;   // 条目步进要大于文字实高，否则分隔线会压到字上
    });
  });
}

pres.writeFile({ fileName: path.join(__dirname, "example-deck.pptx") })
  .then((f) => console.log("✓", f));
