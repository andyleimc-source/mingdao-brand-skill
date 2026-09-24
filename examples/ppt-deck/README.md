# PPT 生成参考实现（examples/ppt-deck）

`workflow.md` 规定 PPT 用 pptxgenjs 生成，但仓库里此前没有可运行代码，每次做 PPT 都要从零推导画布换算、网格常量、对比度门槛，同一批坑反复踩。这里放一份**可直接跑通的最小实现**，把规范里的常量和规则集中成代码。

## 这不是什么

**这不是 `SKILL-STATUS.md` 里规划的 `scripts/ppt/{core,components,layouts,render.ts,qa}` 框架。** 那套结构由作者规划、用 TypeScript，本目录是单文件 JS 的参考实现，放在 `examples/` 下刻意不占用 `scripts/ppt/` 的命名空间。正式框架落地后，本目录可以退化成使用示例，或直接删除。

## 文件

| 文件 | 作用 |
|---|---|
| `deck-lib.js` | 工具层：单位换算、网格常量、色板、字号表、**对比度断言**、Icon Token / Group Card / Divider 绘制件 |
| `example-deck.js` | 4 页可运行示例：封面 / 章节页 / 多特性页(3×2) / 左右对照页 |

## 跑起来

```bash
npm i
# 渲染示例用的图标（默认色即品牌蓝，此处要白色版）
for i in check_circle schedule hub; do
  python3 ../../scripts/common/material_symbols.py render $i \
    --output-dir icons --size 256 --color "#FFFFFF"
done
node example-deck.js
```

产出 `example-deck.pptx`。按 `references/materials/ppt/export-qa.md` 渲染成图自检：

```bash
python3 ../../scripts/ppt/office/soffice.py --headless --convert-to pdf example-deck.pptx --outdir .
pdftoppm -jpeg -r 200 example-deck.pdf slide
```

## 最值得复用的一件事：把对比度规则变成断言

`design-foundation.md` 1.1 节用文字规定了哪些配色能做正文、哪些只能做大字。靠人记会漏，靠肉眼看渲染图更会漏——白字压品牌蓝（4.10）和白字压墨蓝（13.71）在缩略图上看着都"挺清楚"。

`assertReadable(前景色, 背景色, 字号pt, 是否加粗)` 把这条规则变成生成期的硬失败：

```js
L.assertReadable("FFFFFF", "1677FF", 14);        // 抛错：4.10 < 4.5，正文级不合规
L.assertReadable("FFFFFF", "1677FF", 18);        // 通过：18pt 属大字，门槛 3.0
```

`txt()` 传了 `bg` 参数就会自动校验，**违规的页面根本生成不出来**，不用等渲染完再回头返工。

> 实测副产品：用它复核 `design-foundation.md` 1.1 节表格里声称的 9 个对比度值，7 个精确吻合，2 个对不上（「辅助色 #E0E5EC 配点缀色/近黑」原写 14.92，实为 10.83 / 13.81）。数值已更正，结论不变——两者都远高于 4.5，原推荐仍然成立。不透明度表的 3 个值全部吻合。

## 其余几个避坑点（都已固化进 `deck-lib.js`）

- **`txt()` 强制 `margin: 0`**：pptxgenjs 文本框默认 inset 会把按像素算好的坐标整体顶偏。
- **`txt()` 强制绝对行距**：中文字体自带约 1.4em 行高，再叠 `lineSpacingMultiple` 会让实际行距接近字号 2 倍，容器高度全部算小、分隔线划穿文字。用 `blockH(字号, 行数)` 反推容器高度，别拍脑袋。
- **显式使用 `思源黑体 CN` / `思源黑体 CN Bold` 字面**：本示例演示明道云缺失苹方后的 Source Han Sans CN 路径；苹方没有 Bold 字面，不能依赖 `bold: true` 让渲染引擎猜替代字体；LibreOffice 对英文家族名可能错误替换为思源宋体，因此示例使用字体内部的中文家族名。Nocoly PPT 不复用这组字体，须按 `references/brands/nocoly.md` 使用 Inter 与对应地区的 Noto Sans CJK。
- **`iconToken()` 直接把 PNG 摆进圆心**：`material_symbols.py render` 已按实际墨迹居中。若你手上的 PNG 是旧版脚本产出的（按基线定位，每个图标偏移量不同，key 偏上 10.2%），**重新渲染**，不要在排版侧做偏移补偿。
- **`assertModule()`**：布局尺寸必须是 8px 模数整数倍（字号例外，用 2px 原子尺寸）。

## 边界

- 只覆盖静态内容。转场、形状级动效 pptxgenjs 没有 API，仍需在 PowerPoint 里手工加。
- 示例文案是**结构占位**。真实物料必须先完成 `workflow.md` 的生成前内容关卡与 Content QA，禁止直接交付本目录的示例文字。
