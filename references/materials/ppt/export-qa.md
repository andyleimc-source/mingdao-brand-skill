# PPTX 导出与图片预览 QA

在 `references/materials/ppt/workflow.md` 生成 PPTX 后、交给用户确认前，必须逐项执行本文件。PPT 不生成 HTML 预览，也不执行 `references/common/pre-preview-self-check.md`。

只要有一项不通过，回到生成脚本修改坐标或参数，重新生成 PPTX，再从头检查全部项目。整个循环由 AI 内部完成，用户只能看到最后一轮结果。

本文件承担 Geometry QA、File QA 和 Visual QA。Content QA 必须在生成 PPTX 前按 `references/materials/ppt/workflow.md` 完成，不能由导出检查替代。

## 0. 内部布局数据与几何 QA

渲染前先验证生成过程产生的内部布局数据：

```bash
node scripts/ppt/layout_qa.mjs validate "$TMP_DIR/layout-audit.json"
```

- 内部布局数据必须覆盖 PPTX 的全部页码，并分别记录 `structureLayout` 与 `backgroundStyle`。
- `contentArea` 必须由已注册的结构布局返回，不能由页面临时声明，不能复用其他结构布局的内容区。
- 根内容组的 `usedBounds` 必须由其内容元素边界联合计算；页面标题、Logo、页码、页脚和纯背景视觉不进入根内容组。
- `center`、`top`、`bottom` 的实际偏差不得超过 `8 LU`；`custom` 必须记录功能理由。
- 缺少内部布局数据、页码记录不全、结构布局名称混入背景颜色、主内容组缺失或命令退出码非 0，均直接判定失败，不得用图片目测覆盖。

内部布局数据默认只保存在临时工作目录，供 AI 与验收脚本使用；不作为用户交付物。用户要求查看验收依据时，只输出必要摘要。

## 1. 把 PPTX 渲染成图片

不能只读生成脚本推断排版。多页演示文稿先生成整份缩略图网格：

```bash
python scripts/ppt/thumbnail.py output.pptx
```

需要检查单页细节时，再生成高清逐页图片：

```bash
python scripts/ppt/office/soffice.py --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 200 output.pdf slide
```

**渲染分辨率不得低于 200dpi。** 低于这个值时，注释级小字（10pt）和数字在 JPEG 里会糊成一团：既可能把真实的排版问题看漏，也可能把正常字形误判成「被压扁 / 字体不对」而去改本来没问题的东西。判断字形是否失真，不要靠放大糊图目测，应把 PDF 渲染图与该字体文件的直接渲染结果并排比对（`PIL.ImageFont.truetype` 同字号画一份基准即可），并核对 PDF 页面尺寸是否为 959.98×540pt（精确 16:9，确认全局没有被拉伸）。

LibreOffice 与 PowerPoint 的字体渲染可能不同。这里的结果用于发现大多数排版问题，不代表收件人的 PowerPoint 环境一定完全一致。

## 2. 文字溢出与截断

逐页检查卡片和文本框中的文字是否：

- 超出容器边界；
- 被截断；
- 挤出安全区；
- 因容器高度不足导致卡片变形；
- 残留占位文字。

任一情况出现即不通过。优先调整文本框或卡片高度；需要调整字号时仍须遵守 `references/common/design-foundation.md` 1.2 节「字号下限」（0.7 × 该物料正文基准字号）。

## 3. 元素重叠与间距

- 检查文字压形状、线穿字、卡片互相压线。
- 在生成源码中检查相邻元素的逻辑间距是否至少为 8 LU，并保持为 8 LU 的整数倍；写入 PPTX 后等价于 1/18 英寸的整数倍。
- 渲染图片只用于检查对齐、疏密和间距节奏，不按导出图片上的实际像素数判断是否满足 8 LU 模数，因为不同渲染 DPI 会产生不同像素结果。
- 检查同组并排元素间距是否一致。
- 检查是否存在一处过空、一处过挤的失衡。

任意元素重叠、源码逻辑间距小于 8 LU、未遵守 8 LU 模数且无功能性例外，或同组间距不一致，即不通过。

## 4. 图标

页面使用通用图标时，校验生成源码、图标目录和最终 PPTX：

```bash
python scripts/common/material_symbols.py validate generate-deck.js generated-icons --require-icons
python scripts/common/material_symbols.py validate output.pptx --require-icons
```

同时检查：

- Icon Token 中必须显示由本地 Material Symbols Outlined TTF 渲染的实际 PNG，不能只有纯色背景。
- 文件名保留 `ms-outlined__*.png`。
- PNG 和 PPTX 内嵌图片保留 `Material-Symbol-*` 来源元数据。
- Icon Token 的语义和资源符合 `references/common/component-system.md`，几何尺寸符合 `references/materials/ppt/components.md`，容器形状与视觉配方符合 `references/materials/ppt/styles.md`。
- 同一组图标保持相同档位，除非存在明确层级理由。
- 有圆形容器的 Icon Token 是否使用 `Padding.Icon = 8 LU`，且 PNG 可见图形包围框的最大边不小于容器直径的 50%；不能只检查透明图片外框。
- 图标颜色是否在解析容器背景后确定；浅色背景的深色 PNG 是否未被直接复用到 Accent / Inverse 状态。
- `#1677FF`、`#082C5E` 背景上的 Icon Token 是否使用 `#FFFFFF` 100% 反白；同一反白 Card 的图标、标题和正文是否分别通过公共对比度检查。

任一校验命令退出码非 0，或图标来自其他图标库、Emoji、手绘 SVG、网页截图、纯色占位，即不通过。

页面完全没有通用图标时记录“不适用”，并去掉 `--require-icons`；不得为了通过检查添加无意义图标。

## 5. 字体

- 检查标题和正文是否保持明确的字重与字号层级。
- 封面主标题与封底主要结束语承担同一 `BrandFocus.Primary` 语义时，是否使用同一字号 Token；是否因页面类型不同而临时缩小封底字号。
- `12 pt` 及以下的 Tag 是否使用当前品牌真实 Regular 字体，未使用 Medium、Semibold 或 Bold。
- 检查是否因字体替换导致异常换行或文本溢出。
- 明道云：检查是否按 `references/brands/mingdao.md` 完成苹方预检；苹方缺失时应有提示并实际使用 Source Han Sans CN。LibreOffice 未正确显示苹方时，不直接判定交付文件失败；但静默换成未授权字体，或替换后标题与正文无法区分，均不通过。
- Nocoly：英文块使用 Inter；CJK 文本框按内容语言使用正确的 Noto Sans CJK SC / TC / HK / JP / KR 实例；地区字形错误、两套字体基线明显跳变或发生未记录的字体替换，均不通过。
- 交付时说明本次实际使用的字体，并提醒接收方安装相同字体；固定视觉效果的交付同时提供 PDF 或图片。

## 6. 母版、颜色、网格与对齐

- 页面是否通过 `references/materials/ppt/masters.md` 定义的真实 Slide Master 绑定固定框架，普通内容页之间的 Logo、标题区、页码和页脚不得因逐页复制而漂移。
- `structureLayout` 与 `backgroundStyle` 是否分开记录；背景色、图片或视频变化是否未新增结构母版、改变固定对象或改变 `contentArea`。
- 封面 `backgroundStyle` 是否与生成前用户确认的颜色一致；缺少确认记录或静默换色均不通过。
- 整份 PPT 是否指定统一的默认内容页母版；普通内容页默认使用 `#FFFFFF`，切换特殊背景必须有图片、视频、数据可读性或重点表达等功能理由。
- 普通内容页 Logo 是否固定在右上角并保持相同基础尺寸；Weak 必须使用 `#C1C7CF` 重着色版本，不能以标准 Logo 降透明度冒充。
- 章节过渡母版默认不显示 Logo；Cover 默认显示顶部 Standard Logo；End 的 Logo 默认关闭，只有用户明确需要时才显示。
- End 用户要求显示 Logo 且页面仍有结束语、联系方式等主要内容时，是否与 Cover 使用相同 Standard 尺寸和顶部锚点；只有 Logo-only 页面可以使用水平、垂直居中的 Focus Logo。
- `BrandFocus.End.NoLogo` 是否使用 `y = 112–968 LU` 的完整纵向安全区；是否仍保留不存在的顶部 Logo 排除区。
- Title / No Title 状态是否使用各自固定锚点；无标题内容不得覆盖右上角 Logo 排除区。
- 页码和页脚是否按整份 PPT 统一开关；页脚只能使用用户提供的内容，封面、章节过渡和结束页不得显示。
- 色值必须来自 `references/common/design-foundation.md`；功能色只有在存在真实语义需求并得到用户确认后才能使用。
- 每页明确一个主导色；整份 PPT 默认沿用同一主导色，只有用户明确要求按章节区分颜色时才允许切换，并保持章节内部稳定。
- 每页最多使用一种非主导品牌色，其明显面积原则上不超过页面视觉面积的约 20%，且不得形成第二视觉中心；两列强对比突破限额时须符合 `references/common/design-foundation.md` 的例外条件并记录理由。
- 网格、卡片组、列表组和图标组中的同级单元须继承同一组配色；背景、标题、边框、图标容器等同类元素保持一致，禁止按单元或元素序号轮换品牌三色。
- 颜色分组按整行、整列或完整子组保持组内一致；单个单元异色须有明确的信息语义，同一网格组默认最多一个异色单元，并在检查记录中说明理由。
- 两列真实对比可以使用不同颜色，默认只给列头、关键数字或标识条建立颜色对应，列体保持中性。
- 数据图表可以按真实数据系列使用多色，但映射须稳定并优先使用品牌蓝色阶；图表配色不得扩散到标题、卡片和网格组件。
- 间距、边距和列宽遵循 `references/common/grid-system.md` 与 `references/materials/ppt/layouts.md`。
- 页面是否明确使用 `layouts.md` 的六类骨架之一及其规定变体；横向跨度不得使用任意百分比或临时列宽。
- 相同信息关系是否复用稳定骨架；新增布局是否记录现有骨架不适用的理由和真实语义。
- 信息型视觉是否完整显示；表现型视觉裁切是否保护主体；同一多图组是否使用一致的适配方式。
- 同一文字块内多行保持统一的左对齐、居中或右对齐。
- Logo 和图片不得拉伸变形。
- Logo 满足 `references/common/logo.md` 的尺寸和安全区要求。
- 页面先按 `references/common/component-system.md` 选择正确组件语义，再符合 `references/materials/ppt/components.md` 的有效内容框、几何配方和兼容矩阵，并按 `references/materials/ppt/styles.md` 应用 PPT 视觉配方。
- 所有 `x / y / w / h` 是否以整数 LU 计算并统一通过 `lu()` 转换；是否存在裸写 LU、裸写小数英寸或提前截断换算结果。
- 组件是否执行先测量、再由 Group / Collection 协调尺寸、最后渲染的顺序；同一行是否等宽同高。
- 页面标题、Logo、页码和页脚是否排除在主内容组测量之外；单一主要内容组是否按 `layouts.md` 在内容区内重新计算纵向位置，中心偏差是否不超过 `8 LU`。
- 生成代码是否先计算组内相对位置和实测高度，再整体定位；不得给 Marker、标题、正文和总结句分别写页面级固定 `y` 坐标。
- 是否只独立使用公开组件，未把 Icon Token、Divider 或 Connector 当作页面装饰组件。
- Tag 是否来自真实状态、类别、优先级或选择建议，是否附着于具体组件而非独立摆放；Card 顶部首行右侧是否正确避让左侧内容，无 Tag 的同组 Card 是否未保留空位。
- Surface / Card 是否默认不嵌套；是否未启用或用四边描边模拟 Outline；Divider 是否默认关闭并只在间距仍不足时启用。
- Divider、Connector 的色值与粗细是否符合 `styles.md`；Connector 是否只表达真实流程关系，最后节点之后是否停止。
- IconToken.Subtle 与 IconToken.Accent 是否使用等宽等高的真正圆形容器；同组 Icon Token 是否保持相同配方与尺寸档位。
- Horizontal Stepper 是否按页面角色与节点数量选择 Marker 档位；页面唯一主体为 2–3 节点时是否使用 Focus，4–5 节点或仍有其他主要内容时是否回落到 Standard / Small。
- 普通组件是否使用实色，是否存在未经公共规范验证的临时透明度；同组组件是否按单元序号轮换 Surface、Icon Token 或品牌色。
- 当前配方状态是否仍为 Specified；未经过组件样稿验证时不得声称已具备 Validated 的正式组件实现。

## 7. 输出检查记录

先记录内部布局数据的结构、内容区和偏差结论，再逐项记录“图片依据 → 结论”；不能只写“通过/不通过”。

循环上限为 3 轮：

- 全部通过：只把最后一轮逐页图片交给用户确认。
- 第 3 轮仍不通过：停止自动重试，报告具体页码、元素和失败项目，转人工处理。
- 用户确认后：交付生成这些图片的同一份 PPTX，不得重新生成未经检查的文件。
