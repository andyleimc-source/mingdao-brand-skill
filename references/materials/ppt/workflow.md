# PPT 生成工作流

## 必读关系

- 始终先读取 `references/common/design-foundation.md`，再按 `SKILL.md` 的品牌路由只读取 `references/brands/mingdao.md` 或 `references/brands/nocoly.md`；用户明确要求联名时才同时读取。
- 生成前读取 `references/common/generation-checklist-common.md`，形成内容方案并完成本文件的 Content QA。
- 设计和生成页面时先读取 `references/materials/ppt/masters.md` 选择固定框架，再读取 `references/materials/ppt/layouts.md` 分配一级区域，并依次读取 `references/common/component-system.md`、`references/materials/ppt/components.md` 与 `references/materials/ppt/styles.md`：先确定组件语义与几何，再应用 PPT 视觉样式。
- PPTX 生成后、向用户展示图片前读取并执行 `references/materials/ppt/export-qa.md`。

## 生成前内容关卡

开始设计前执行 `references/common/generation-checklist-common.md` 的软确认流程。

- **PPT 专属必要事实**：受众与演示目标。优先根据标题、内容、会议背景和项目资料推断；只有不同受众会实质改变叙事结构且无法判断时，才命中“受众或行动不明确”并暂停提问。
- **封面颜色确认**：用户没有指定封面颜色时，AI 先按 `references/common/design-foundation.md` 1.1 节推荐一种颜色并说明理由，再提供品牌蓝 `#1677FF`、云灰 `#E0E5EC`、墨蓝 `#082C5E`、纯白 `#FFFFFF` 四个选项，等待用户确认后再生成 PPTX。只确认封面一次；普通内容页默认白色，不逐页询问背景色。
- Logo 版本、内容去重和信息层级按通用内容关卡自动判断。

## Content QA（生成内部草稿 PPTX 前必做）

拿到用户提供的内容后，先完成纯文本内容自检：

- **完整性**：每页是否都有实际数据或文案，是否残留“待补充”等占位内容。
- **一致性**：同一概念、术语、数字和结论是否前后一致。
- **顺序与结构**：内容顺序是否符合叙事逻辑，必要背景是否出现在结论之前。

发现问题时先自行修正可判断的一致性与结构问题；只有命中通用内容关卡第 5 节的暂停或确认条件时才逐一询问或请用户补充。

## 生成工作流

PPT 不生成 HTML 预览。用户确认的对象必须来自待交付 PPTX 的实际渲染结果：

1. 完成生成前内容关卡、封面颜色确认和 Content QA。
2. 先按 `references/materials/ppt/masters.md` 选择结构布局，再独立确定背景样式；随后按 `references/materials/ppt/layouts.md` 选择内容骨架，按 `references/common/component-system.md` 判断组件语义，按 `references/materials/ppt/components.md` 选择 PPT 几何配方，最后按 `references/materials/ppt/styles.md` 应用 PPT 视觉样式。
3. 用 **pptxgenjs** 生成原生内部草稿 PPTX，包括版式、文字、图片、图表和演讲者备注等静态内容；同时生成覆盖全部页面的内部布局数据，记录每页的 `structureLayout`、`backgroundStyle`、`contentArea`、根内容组元素边界和对齐策略。
4. 运行 `node scripts/ppt/layout_qa.mjs validate <layout-audit.json>`。缺少页面记录、结构内容区不匹配、主内容组缺失或对齐偏差超过 `8 LU` 时，停止并修改生成脚本；不得进入图片预览。
5. 几何验收通过后，按 `references/materials/ppt/export-qa.md` 把 PPTX 渲染成图片并完成内部自检循环；不通过时修改生成脚本、重新生成，并从第 4 步重新检查。
6. 只把收敛后的最后一轮逐页图片交给用户确认。可以附缩略图网格作为结构总览，但不能只提供无法检查文字的小尺寸网格图。
7. 用户确认后交付生成这些图片的**同一份 PPTX**。用户要求修改时，从第 2 步重新生成、验收、渲染和确认。

转场和形状级动效不在自动生成范围内。pptxgenjs 不提供相应 API，需要时由市场部同事在 PowerPoint 中手动添加。

## pptxgenjs 实现约束

- 默认使用 16:9。布局设计以 `1920 × 1080 LU` 为整数逻辑画布，PPTX 实际页面尺寸为 13.333×7.5 英寸（33.87×19.05cm）。
- 写入 pptxgenjs 时，布局坐标和空间尺寸统一按 `英寸 = LU ÷ 144` 换算。因此 `1 LU = 6350 EMU`，`8 LU = 1/18 英寸 = 50800 EMU`；整数 LU 可以精确落到整数 EMU。
- 上述换算只适用于 `x`、`y`、`w`、`h` 等布局坐标和空间尺寸。字号、描边、文本边距等属性须遵守 pptxgenjs 对该属性规定的单位，不得统一套用 `÷ 144`。
- 组件填充、线宽、圆角、内边距与视觉状态执行 `references/materials/ppt/styles.md`；文字颜色、背景—文字对比度和透明度仍以 `references/common/design-foundation.md` 为唯一来源。
- PPT 专属规范使用 `LU`，不使用 `px` 指代坐标。`references/common/grid-system.md` 中跨物料的 px 数值映射到 PPT 时保持数值不变并改记为 LU，再通过 `lu()` 写入 PPTX；不得把 LU 当作导出图片像素。
- 所有 `x`、`y`、`w`、`h` 必须以整数 LU 计算，并通过 `references/materials/ppt/components.md` 定义的唯一 `lu()` 函数转换；禁止裸写 LU 或预先截断换算后的小数英寸。
- 十六进制颜色不带 `#`，例如 `"1677FF"`。
- 在调用 `addSlide()` 前设置 `pres.layout`。
- **每个文本框都要显式写 `margin: 0`**。pptxgenjs 的文本框默认带 inset（在 1920 LU 画布中，上下约 7.2 LU、左右约 14.4 LU），不关掉会让按 LU 计算的坐标整体偏移，且偏移量随字号变化。
- **中文排版禁用 `lineSpacingMultiple`，改用绝对行距 `lineSpacing`（磅）**。中文字体自带的行高本身就接近 1.4em，再乘一个 1.4 的倍数，实际行距会逼近字号的 2 倍（14pt 正文实测接近 55 LU 而非预期的 39 LU）。后果是按「字号 × 1.4 × 行数」预留的文本框高度偏小。正文 14pt 用 `lineSpacing: 20`，其余按实际字体测量后写入绝对磅值。
- **字体家族和字重必须来自当前品牌配置，不依赖 `bold: true` 合成不存在的字面**。明道云先按 `references/brands/mingdao.md` 检测苹方：可用时标题显式使用 Semibold，缺失时提示并改用 Source Han Sans CN 的真实 Bold；现有示例在 LibreOffice 中显式使用内部家族名 `思源黑体 CN` / `思源黑体 CN Bold`，避免英文家族名被错误替换。Nocoly 按 `references/brands/nocoly.md` 使用 Inter 与 Noto Sans CJK 的地区实例，只用真实的 400 / 500 / 700；英文块用 Inter，CJK 文本框按 `zh-CN` / `zh-TW` / `zh-HK` / `ja` / `ko` 显式指定 SC / TC / HK / JP / KR，不能依赖 PowerPoint 猜地区字形。
- 坐标超出页面边缘不会自动报错，必须检查渲染图。
- 每页从 `scripts/ppt/layout_qa.mjs` 的结构布局注册表取得 `contentArea`，用 `placeContentGroup()` 计算根内容组纵向偏移；不得把整张画布中心或其他结构布局的内容区当作当前页面基准。
- `structureLayout` 与 `backgroundStyle` 分别保存。背景色、图片或视频变化不能改变结构布局 ID、固定对象或内容区。
- 组件不会像网页 CSS 一样按内容自动回流。按 `references/materials/ppt/components.md` 先测量、再布局和渲染，并通过导出 QA 检查溢出；不得突破 `references/common/design-foundation.md` 1.2 节「字号下限」（0.7 × 该物料正文基准字号）。
- 通用图标先按 `references/common/material-symbols.md` 搜索和渲染，再以带来源元数据的透明 PNG 加入 PPTX。图标不是可在 PowerPoint 中改色的矢量图形；只有背景色块、看不出图标形状时不合格。
- LibreOffice 预览字体不等于收件人在 PowerPoint 中看到的最终字体，按 `references/materials/ppt/export-qa.md` 处理字体差异。

根内容组必须让渲染和验收复用同一份元素边界，不能另外手写一套“看起来会通过”的报告数字：

```js
const measuredBounds = unionBounds(relativeElements);
const placement = placeContentGroup({
  structureLayout,
  measuredBounds,
  alignment: "center",
});
const placedElements = relativeElements.map((element) => ({
  ...element,
  bounds: translateBounds(element.bounds, 0, placement.offsetY),
}));

// 页面渲染只读取 placedElements；内部布局数据也记录同一 placedElements。
```

## Scripts

| 脚本 | 作用 |
|---|---|
| `scripts/common/material_symbols.py` | 验证 Material Symbols 资产、搜索和渲染图标、校验生成源码与 PPTX |
| `scripts/ppt/layout_qa.mjs` | 提供结构布局内容区、根内容组定位函数，并验证内部布局数据 |
| `scripts/ppt/office/soffice.py` | 将 PPTX 转换为 PDF |
| `scripts/ppt/thumbnail.py deck.pptx [prefix]` | 将整份 PPTX 渲染并拼成带页码的缩略图网格；超过 12 页自动拆图 |

组件生成代码尚未落地，不能假设 `components.md` 与 `styles.md` 中的组件配方已经可以直接调用。当前只有 `layout_qa.mjs` 的结构内容区、根内容组定位与几何验收属于可执行实现；后续有实际组件实现时再扩展：

```text
scripts/ppt/
├── core/          # PPT 专属单位、坐标和文档模型
├── components/    # 可复用页内组件
├── layouts/       # 页面级版式组合
├── layout_qa.mjs  # 已实现：结构内容区、根内容组定位与内部布局验收
├── render.ts      # 由内容模型生成 PPTX 的入口
└── qa/            # PPTX 文件检查和渲染后检查
```

当前不创建空目录。只有相应代码真正落地时才建立；某段代码被两类以上物料复用后，再评估是否上移到 `scripts/common/`。

## 禁止事项

- 不要跳过生成前内容关卡或 Content QA。
- 不要生成 HTML 作为 PPT 预览。
- 不要把内部自检的中间轮次图片交给用户。
- 不要使用其他图标库、Emoji、手绘 SVG、网页截图或纯色块替代 Material Symbols 图标。
- 不要在内容变化后沿用未经重新计算的列数、卡片高度或页面坐标。
- 不要另外制作一张与 PPTX 无关的图片作为预览。
- 不要在用户确认图片后重新生成一份未经检查的 PPTX。

## 交付规格

- **尺寸**：16:9（1920×1080 LU / 33.87×19.05cm）
- **格式**：PPTX
- **页面类型**：封面页、目录页、章节页、内容页、数据页、总结页和结束页；按实际内容选择，不要求每份演示文稿机械包含全部类型
- **母版**：按 `references/materials/ppt/masters.md` 使用真实 Slide Master 锁定背景、Logo、标题区、内容安全区、页码和页脚；普通内容页默认白底

是否为动效自动化引入 Aspose.Slides 等付费方案仍待确认，见 `SKILL-STATUS.md`。
