# PPT 组件适配层

本文件把 `references/common/component-system.md` 的共享组件映射到 16:9 PPT。先按 `references/materials/ppt/masters.md` 取得内容安全区，按 `references/materials/ppt/layouts.md` 分配一级区域，再使用本文件选择组件几何配方，最后按 `references/materials/ppt/styles.md` 应用 PPT 视觉样式。公共颜色与对比度仍以 `references/common/design-foundation.md` 为准。

本文件中的组件均为 `Specified`，表示语义、几何和验收规则已经定义，但尚未通过完整的真实 PPTX 组件样稿矩阵验证；不得假定 `scripts/ppt/components/` 已有可直接调用的实现。

## 目录

1. LU 单位与实现边界
2. 组件适配契约
3. 有效内容框与测量流程
4. 几何基线
5. 内容组件配方
6. 容器与集合配方
7. 空间骨架兼容矩阵
8. 选择与溢出
9. 组件验收

## 1. LU 单位与实现边界

PPT 使用 `1920 × 1080 LU` 的整数逻辑画布：

```text
1 LU = 1 / 144 英寸 = 6350 EMU = 0.5pt
8 LU = 1 / 18 英寸 = 50800 EMU
```

PptxGenJS 的 `LAYOUT_WIDE` 为 `12192000 × 6858000 EMU`，正好对应 `1920 × 1080 LU`。整数 LU 可以精确换算为整数 EMU，不产生累计坐标误差。

所有 `x / y / w / h` 等布局坐标和空间尺寸都先以整数 LU 计算，再通过唯一换算函数传给 PptxGenJS：

```js
function lu(value) {
  if (!Number.isInteger(value)) {
    throw new Error(`PPT layout value must be an integer LU: ${value}`);
  }
  return value / 144;
}
```

所有向下吸附 8 LU 模数的计算统一使用：

```js
function floorTo8(value) {
  return Math.floor(value / 8) * 8;
}
```

```js
slide.addText(text, {
  x: lu(box.x),
  y: lu(box.y),
  w: lu(box.w),
  h: lu(box.h),
  fontSize: 14,
  margin: 0,
});
```

实现约束：

- 禁止对 `x / y / w / h` 裸写英寸或未转换的 LU。
- 不预先把 `value / 144` 截成有限小数；直接把换算结果交给 PptxGenJS。
- PptxGenJS 内部会把大于等于 `100` 的坐标数字视为已经转换的 EMU；统一调用 `lu()`，避免 `x: 148` 被误解释为 148 EMU。
- `fontSize`、`lineSpacing`、描边等属性继续使用 PptxGenJS 对该属性规定的单位，不调用 `lu()`。
- 所有文本框显式设置 `margin: 0`；组件内边距由几何配方计算。
- 坐标准确不代表文字一定准确。字体替换、字体度量和渲染器差异仍需通过实际渲染 QA 检查。

## 2. 组件适配契约

每个正式配方至少记录：

```text
组件名称
共享信息职责与内容槽位
配方名称
参考栏数
minWidthLU
minHeightLU（需要时）
内部几何公式
高度计算方式
兼容空间骨架
切换条件
Status
```

参考栏数帮助初步选择；`minWidthLU / minHeightLU` 是最终硬条件。不得只因为外部区域跨了足够栏数，就忽略 Surface 内边距和 Group / Collection 间距造成的有效区域缩小。

## 3. 有效内容框与测量流程

### 3.1 有效内容框

按顺序扣除空间：

```text
页面骨架分配的外部区域
− Surface / Card 内边距
− Group 内部留白
− Collection 行列间距
= 组件有效内容框
```

例如 4 栏外部区域宽度为：

```text
4 × 128 + 3 × 8 = 536 LU
```

若 Surface 左右内边距各为当前基线 `24 LU`：

```text
有效宽度 = 536 − 48 = 488 LU
```

配方是否可用以 `488 LU` 判断，而不是以“4 栏”判断。

### 3.2 先测量、后渲染

实现必须执行：

```text
measure → layout → render → QA
```

组件先用当前品牌与语言的真实字体计算理想高度。Collection 汇总子组件测量结果、确定行高和最终 box 后，才把元素写入 PPTX。不能边添加元素边猜测后续坐标。

单个组件至少返回：

```text
recipe
preferredHeightLU
usedBounds
overflow
warnings
```

## 4. 几何基线

本节是首版几何与排版计算基线。填充、线宽、圆角、内边距档位与视觉状态见 `references/materials/ppt/styles.md`；后续组件样稿修改字号、图标尺寸、内边距或行距时，必须重新计算相关配方的最小尺寸。

| Token | 当前基线 |
|---|---:|
| 布局模数 | 8 LU |
| 组件内部紧密间距 | 8 LU |
| 图文或相邻内容间距 | 16 LU |
| Group / Collection 常规间距 | 24 LU |
| 大区段间距 | 32 LU |
| Surface / Card 默认内边距 | 24 LU（`Padding.Standard`） |
| Icon Token Small | 56 × 56 LU = 28 × 28 pt |
| Icon Token Standard | 72 × 72 LU = 36 × 36 pt |
| Icon Token Focus | 96 × 96 LU = 48 × 48 pt |
| 正文 / Description | 14pt |
| 组件标题 | 20pt |
| 注释 / 辅助 | 10pt |
| 页面标题 | 28pt |

- 中文 14pt 正文当前使用 `lineSpacing: 20`；其他字号按实际字体测量并设置绝对行距。
- Surface / Card 的填充、圆角、内边距与反白状态执行 `styles.md`；PPT 首版不启用 Outline，矩形圆角上限为 `8 LU`，真正圆形几何除外。
- Feature、Stat、Quote 等组件不自行添加 Surface。需要 Card 时由外层统一扣除内边距。
- 同一 Collection 中的图标尺寸、字号角色和视觉角色保持一致。

### 4.1 Tag.Text

Tag 的共享语义与识别条件见 `references/common/component-system.md`。PPT 首版只定义纯文字 `Tag.Text`，不定义带背景的 Filled / Badge 配方。

- Tag 默认锚定 Card 或所属内容组件的顶部首行右侧。首行左侧可以是 Icon Token、标题、其他文本或为空；左侧内容类型不改变 Tag 的右侧锚点。
- Tag 的右边缘与所属内容框的右内边界对齐。先用当前品牌真实字体测量 Tag，再从首行左侧内容的可用宽度中扣除 `tagWidth + 16 LU`；不得让 Tag 与左侧内容重叠。
- Tag 与首行左侧内容按垂直中心对齐：

```text
tagX = contentBox.x + contentBox.w − tagWidth
tagY = topRow.y + (topRow.h − tagHeight) / 2
leftTopWidth = tagX − 16 LU − leftTopX
```

- Tag 只影响顶部首行的可用宽度，不缩窄后续标题、正文或其他内容行。
- 同一 Collection 中没有 Tag 的单元不生成占位、不保留空标签区，也不因此增加顶部留白。
- Tag 默认保持单行。真实文案无法与左侧内容共同容纳时，切换为独立一行并重新测量当前 Card；不得缩小到字号下限以下、裁切或让同组无 Tag 的 Card 保留空行。
- Tag 不是页面级组件，不能脱离 Card 或所属内容组件独立摆放。

## 5. 内容组件配方

### 5.1 Narrative

#### Narrative.Standard

| 字段 | 规则 |
|---|---|
| 参考栏数 | 3–10 栏 |
| `minWidthLU` | 400 |
| `minHeightLU` | 按实测文字 |
| 对齐 | 默认起始侧对齐 |
| 最大正文行宽 | 1080 LU；区域更宽时保留主动留白 |
| 高度 | 所有已提供槽位的实测高度 + 槽位间距 |
| Status | Specified |

支持共享组件系统允许的 Heading、Body、List 组合。不得因获得 12 栏就让长正文横跨整页。

#### Narrative.Focus

| 字段 | 规则 |
|---|---|
| 参考栏数 | 6–10 栏 |
| `minWidthLU` | 808 |
| `minHeightLU` | 160 |
| 对齐 | 起始侧或居中，由整个页面关系决定 |
| 最大文字行宽 | 1352 LU |
| 数量 | 同一页面默认一个 |
| Status | Specified |

只承载短结论、品牌声明、章节语句或页面核心观点。长正文和复杂列表切换 Standard 或拆页。

### 5.2 Feature

#### Feature.Horizontal

| 字段 | 规则 |
|---|---|
| 参考栏数 | 5–8 栏 |
| `minWidthLU` | 560 |
| `minHeightLU` | 72 |
| Icon | 72 × 72 LU |
| 图文间距 | 16 LU |
| 文字宽度 | `box.w − 88` |
| 高度 | `max(72, textHeight)` |
| Status | Specified |

图标与文字顶部对齐；Title 与 Description 使用 `8 LU` 间距。Supporting Info 存在时继续计入文字实测高度。

#### Feature.Vertical

| 字段 | 规则 |
|---|---|
| 参考栏数 | 3–4 栏 |
| `minWidthLU` | 320 |
| `minHeightLU` | 128 |
| Icon | 56 × 56 LU |
| 图文间距 | 16 LU |
| 文字宽度 | `box.w` |
| 高度 | `56 + 16 + textHeight` |
| Status | Specified |

默认起始侧对齐。只有整个 Collection 明确采用居中表达时，同组 Feature 才能统一居中。

#### Feature.TextOnly

| 字段 | 规则 |
|---|---|
| 参考栏数 | 3–12 栏 |
| `minWidthLU` | 320 |
| `minHeightLU` | 按实测文字 |
| 文字宽度 | `box.w`，宽区域继续遵守可读行宽 |
| 高度 | `textHeight` |
| Status | Specified |

图标不增加理解、没有准确图标或内容本身足够明确时优先使用。不得为了形式完整临时添加图标。

### 5.3 Stat

#### Stat.Hero

| 字段 | 规则 |
|---|---|
| 参考栏数 | 6–12 栏 |
| `minWidthLU` | 808 |
| `minHeightLU` | 200 |
| 排列 | Value、Label、Context 纵向排列 |
| 数量 | 同一页面默认一个 |
| 高度 | 各槽位实测高度 + 合法间距 |
| Status | Specified |

Value 使用当前 PPT 排版体系中最高的合法数据层级，但不在本文件新增未经视觉验证的字号。没有核心数据语义时改用 Narrative.Focus。

#### Stat.Stacked

| 字段 | 规则 |
|---|---|
| 参考栏数 | 3–4 栏 |
| `minWidthLU` | 280 |
| `minHeightLU` | 144 |
| 排列 | Value 在上，Label、Context 在下 |
| 高度 | 各槽位实测高度 + 合法间距 |
| Status | Specified |

多个 Stat 由 Collection 统一数值基线、文字起点和最终高度。

#### Stat.Inline

| 字段 | 规则 |
|---|---|
| 参考栏数 | 5–8 栏 |
| `minWidthLU` | 536 |
| `minHeightLU` | 96 |
| 间距 | Value 与说明区相隔 24 LU |
| 高度 | `max(valueHeight, labelContextHeight)` |
| Status | Specified |

有效宽度不足时切换 Stacked，不压缩 Value 或说明字号。

### 5.4 Quote

#### Quote.Block

| 字段 | 规则 |
|---|---|
| 参考栏数 | 3–8 栏 |
| `minWidthLU` | 400 |
| `minHeightLU` | 144 |
| 排列 | Quote、Attribution、Role / Source 纵向排列 |
| 高度 | 所有已提供槽位实测高度 + 合法间距 |
| Status | Specified |

引号优先使用字体字符，不绘制装饰性 SVG；引号不能比引用内容更抢眼。

#### Quote.Focus

| 字段 | 规则 |
|---|---|
| 参考栏数 | 6–10 栏 |
| `minWidthLU` | 808 |
| `minHeightLU` | 200 |
| 数量 | 同一页面一个 |
| 最大文字行宽 | 1352 LU |
| Status | Specified |

引用过长时切换 Block 或拆页。没有真实引用语义时改用 Narrative.Focus。

### 5.5 Media

#### Media.Contain

| 字段 | 规则 |
|---|---|
| 参考栏数 | 3–12 栏 |
| `minWidthLU` | 400；复杂界面按可读性提高 |
| `minHeightLU` | 由素材比例和标签决定 |
| 适配 | 在 `box` 内分别计算贴宽与贴高，选择不溢出的结果 |
| Status | Specified |

完整保留信息型视觉。素材比例与区域严重不匹配时切换布局，不裁掉界面、表格或示意信息。

#### Media.Cover

| 字段 | 规则 |
|---|---|
| 参考栏数 | 3–12 栏 |
| `minWidthLU` | 320 |
| `minHeightLU` | 160 |
| 适配 | 按目标 box 比例裁切，保护主体和关键内容 |
| Status | Specified |

边缘出血由页面骨架扩展 Media 的外部 box，组件本身仍按最终 box 计算裁切。Caption 存在时从媒体区域中单独预留高度。

### 5.6 Stepper

Stepper 内部包含 Step Node 与 Connector；不单独暴露 Step。

#### Stepper.Horizontal

| 字段 | 规则 |
|---|---|
| 参考栏数 | 6–12 栏 |
| `minWidthLU` | 808 |
| `minHeightLU` | 200 |
| 步骤数量 | 首版建议 2–5 |
| 节点最小宽度 | 240 LU |
| Marker | 按下方响应式档位选择 |
| Status | Specified |

```text
nodeWidth = floorTo8((box.w − (count − 1) × 32) / count)
```

无法整除的余量进入 Stepper 两侧留白。标题和说明位于 Marker 下方；Connector 连接相邻 Marker 的中心，不穿过文字。任一节点不足 `240 LU` 时切换 Vertical。

Marker 档位按页面角色与节点数量选择，而不是固定使用 Small：

| 场景 | Marker 档位 |
|---|---|
| Stepper 是页面唯一或绝对主导的内容，只有 2–3 个节点 | Focus：96 LU / 48 pt |
| Stepper 是页面主体，有 3–4 个节点 | Standard：72 LU / 36 pt |
| 有 4–5 个节点，或页面还有其他主要内容 | Small：56 LU / 28 pt |

- 同一 Stepper 的所有 Marker 使用相同档位，除非存在真实状态或单元异化语义。
- Focus 不能仅用于填补空白；放大后仍须满足节点最小宽度、标题与说明的正常字号和间距。
- Marker、标题、说明和必要总结句先按相对位置组成完整内容组，再执行 `layouts.md` 的纵向定位；不得跨页面照抄旧坐标。

#### Stepper.Vertical

| 字段 | 规则 |
|---|---|
| 参考栏数 | 3–8 栏 |
| `minWidthLU` | 400 |
| `minHeightLU` | 由节点总高度决定 |
| Marker | 56 × 56 LU |
| Marker 与文字间距 | 16 LU |
| 节点间距 | 24 LU |
| Status | Specified |

```text
nodeHeight = max(56, textHeight)
textX = box.x + 72
textWidth = box.w − 72
```

Connector 连接相邻 Marker，最后一个节点之后不显示。总高度超出内容区时按真实步骤边界拆页。

## 6. 容器与集合配方

### 6.1 Group

- 默认纵向组织子组件。
- 子组件常规间距使用当前基线 `24 LU`；同一紧密语义组可以使用 `16 LU`。
- Group 高度为所有子组件实测高度、内部间距与已启用 Divider 的总和。
- 最多两级语义分组；第二级不自动增加 Surface。

### 6.2 Collection.Stack

- 子组件统一宽度，使用各自理想高度。
- 默认间距 `24 LU`。
- 需要 Divider 时由 Collection 统一插入，最后一项之后关闭。

### 6.3 Collection.Row

- 只排列 2–4 个同级组件。
- 默认间距 `16 LU`；当 Row 对应页面 12 栏的正式列分区时，保持布局骨架的 `8 LU` gutter。
- 先测量全部子组件，再统一为本行最大高度。
- 任一子组件低于其 `minWidthLU` 时切换 Grid、Stack 或其他页面骨架。

### 6.4 Collection.Grid

- 只使用 2、3、4 列。
- 默认间距 `16 LU`；对应正式页面列边界时保持 `8 LU` gutter。
- 同一行等宽、统一高度；严格横向扫描时整组统一为最大高度。
- 行数和行高按当前内容重新计算，不复用旧页面坐标。
- 最后一行不足列数时保持原列宽，从阅读起始侧排列；不拉宽剩余项填满。

Row / Grid 的列宽计算：

```text
rawItemWidth = (box.w − (columns − 1) × gap) / columns
itemWidth = floorTo8(rawItemWidth)
remainder = box.w − (columns × itemWidth + (columns − 1) × gap)
```

`remainder` 平分为集合两侧留白。若平分后出现非整数 LU，前后两侧使用相差不超过 `1 LU` 的整数，并保持所有组件宽度一致。

### 6.5 Surface / Card

- Bare 为默认，不扣除 Surface 内边距。
- Subtle、Accent、Inverse 的视觉配方执行 `references/materials/ppt/styles.md`；PPT 首版不启用 Outline。
- Subtle、Accent、Inverse 默认使用 `Padding.Standard = 24 LU`；只有 `styles.md` 允许的档位切换才能改变内边距。
- Card 调用 Tag 时执行 `4.1 Tag.Text`；Tag 不改变 Card 的内容组件语义，也不能作为增加 Card 高度或统一空占位的理由。
- 先扣除 Surface 内边距，再判断内部组件配方。
- 默认禁止 Surface / Card 嵌套。
- 矩形圆角上限为 `8 LU`；真正圆形几何按 `styles.md` 处理；不得使用投影。

## 7. 空间骨架兼容矩阵

`优先` 表示常用匹配，`适合` 表示可直接使用，`条件` 表示仍需检查内容和有效区域，`—` 表示首版不使用。

| 组件配方 | 单一区域 | 左右分区 | 上下分区 | 多栏并列 | 网格 / 矩阵 | 全幅视觉 |
|---|---:|---:|---:|---:|---:|---:|
| Narrative.Standard | 适合 | 适合 | 适合 | 条件 | 条件 | — |
| Narrative.Focus | 优先 | 条件 | 条件 | — | — | 适合 |
| Feature.Horizontal | 适合 | 优先 | 适合 | 条件 | 条件 | — |
| Feature.Vertical | 条件 | 条件 | 条件 | 优先 | 优先 | — |
| Feature.TextOnly | 适合 | 适合 | 适合 | 适合 | 适合 | — |
| Stat.Hero | 优先 | 条件 | 条件 | — | — | 条件 |
| Stat.Stacked | 条件 | 适合 | 适合 | 优先 | 优先 | — |
| Stat.Inline | 适合 | 优先 | 适合 | 条件 | — | — |
| Quote.Block | 适合 | 适合 | 适合 | 条件 | 条件 | — |
| Quote.Focus | 优先 | 条件 | 条件 | — | — | 条件 |
| Media.Contain | 适合 | 优先 | 适合 | 条件 | 条件 | — |
| Media.Cover | 适合 | 优先 | 适合 | 条件 | 适合 | 优先 |
| Stepper.Horizontal | 优先 | 条件 | 适合 | — | — | — |
| Stepper.Vertical | 适合 | 适合 | 优先 | 条件 | — | — |

兼容矩阵只完成第一层筛选；最终必须通过有效内容框的最小尺寸和实际内容测量。

## 8. 选择与溢出

### 8.1 选择顺序

1. 按 `references/common/component-system.md` 判断信息职责。
2. 按 `references/materials/ppt/layouts.md` 选择空间骨架。
3. 计算外部区域和有效内容框。
4. 从兼容矩阵中筛选配方。
5. 用 `minWidthLU / minHeightLU` 和真实内容测量确认。
6. 按 `references/materials/ppt/styles.md` 选择视觉配方并重新确认扣除内边距后的有效内容框。
7. 由 Collection 协调最终尺寸，再渲染。

### 8.2 内容溢出

继续执行共享组件系统的内容保留顺序：

1. 用当前品牌真实字体重新测量。
2. 合并重复信息或无损精简。
3. 切换当前组件已有配方。
4. 调整 Collection 的列数或排列。
5. 切换页面空间骨架。
6. 按语义拆页。
7. 仍无法处理时再请用户决定删减。

禁止把 PowerPoint 自动缩字作为适配手段，禁止因槽位“可选”就删除用户已提供的非重复信息。

## 9. 组件验收

### 9.1 规范检查

- 是否先选择共享组件语义，再选择 PPT 几何配方。
- 是否按 `references/materials/ppt/styles.md` 应用已定义的 PPT 视觉配方，未临时创造样式值。
- 是否只使用公开组件，未独立摆放 Icon Token、Divider 或 Connector。
- Tag 是否只附着于 Card 或具体内容组件；是否按真实元信息识别、锚定顶部首行右侧，并且没有给同组无 Tag 单元保留空位。
- 是否以有效内容框而不是外部栏数通过最小尺寸判断。
- 所有 `x / y / w / h` 是否为整数 LU 并统一调用 `lu()`。
- 是否先测量全部相关组件，再确定 Collection 行高和后续坐标。
- 同一 Collection 是否等宽、同高并使用一致视觉角色。
- 是否默认 Bare，未启用或模拟 Outline，并避免 Surface / Card 嵌套。
- Media 是否按信息功能选择 Contain / Cover。
- Stepper 是否只有真实线性顺序，最后节点之后没有 Connector。
- 溢出时是否保留必要内容并执行规定切换顺序。

### 9.2 状态检查

当前所有配方均为 `Specified`。后续真实 PPTX 组件样稿至少覆盖：

- 明道云与 Nocoly；
- 中文、英文及较长内容；
- 最小宽度、推荐宽度和宽区域；
- Bare 与 `styles.md` 中需要验证的 Surface / Card、Divider、Connector、Icon Token 和 Tag 视觉配方；
- 单独使用、Stack、Row 和 Grid；
- 实际 PPTX 渲染后的文字、边界、对齐和字体替换。

通过样稿矩阵后才能把对应配方标为 `Validated`。最终交付仍执行 `references/materials/ppt/export-qa.md`。
