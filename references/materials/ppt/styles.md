# PPT 组件视觉样式

本文件把 `references/common/component-system.md` 的视觉角色映射为 PPT 可执行样式。先按 `references/materials/ppt/components.md` 确定组件语义、配方和几何，再用本文件确定填充、线条、圆角、内边距与组件视觉状态。

文字颜色、背景—文字对比度、品牌色使用和透明度规则只以 `references/common/design-foundation.md` 为准；本文件不复制公共 Token。字号、字重、行距、`x / y / w / h`、最小尺寸、内容槽位、分页与溢出处理仍由品牌配置、`components.md` 和其他 PPT 适配文件管理。

## 目录

1. 样式 Token 与实现单位
2. 色彩与透明度
3. Surface / Card
4. Divider
5. Connector
6. Icon Token
7. Tag
8. 组内一致性与选择顺序
9. PptxGenJS 映射

## 1. 样式 Token 与实现单位

### 1.1 线宽

描边与线条使用 PptxGenJS 原生 pt，不调用 `lu()`：

| Token | 值 | 用途 |
|---|---:|---|
| `Stroke.Subtle` | 0.75 pt | 轻分割 |
| `Stroke.Standard` | 1 pt | 普通线条基线 |
| `Stroke.Strong` | 1.5 pt | 重大结构分割或真实重点 |

Connector 是流程轨道，使用本文件第 5 节的组件专用 `4 pt`，不套用普通 Stroke 档位。

### 1.2 圆角

| Token | 值 | 用途 |
|---|---:|---|
| `Radius.None` | 0 LU | 默认矩形 |
| `Radius.Small` | 4 LU | Surface 等需要轻微柔化的矩形 |
| `Radius.Medium` | 8 LU | 较大容器的圆角上限 |

- 矩形组件默认使用 `Radius.None`；只有配方明确规定时才启用圆角。
- 矩形圆角不得超过 `8 LU`，不得把普通组件自动做成胶囊或圆形。
- 真正的圆形属于独立几何类型，必须等宽等高，不使用 Radius Token，也不受 `8 LU` 上限约束；PptxGenJS 实现见第 9 节。

### 1.3 内边距

| Token | 值 | 用途 |
|---|---:|---|
| `Padding.Icon` | 8 LU | 有圆形容器的 Icon Token |
| `Padding.Compact` | 16 LU | 小型信息块 |
| `Padding.Standard` | 24 LU | 普通 Surface / Card |
| `Padding.Spacious` | 32 LU | 大型重点区域 |

- 同组同类组件使用同一内边距档位。
- 内容空间不足时，可以按 `Spacious → Standard → Compact` 降一档；不得临时生成零散值。
- 降低内边距后仍须满足组件最小尺寸和内容安全区，不得以压缩内边距代替拆页或配方切换。

## 2. 色彩与透明度

### 2.1 当前页面强调色

`Accent.Primary` 是动态角色，映射为当前页面的主导品牌色，不固定等于品牌蓝。只有语义明确要求品牌蓝时才显式调用公共品牌蓝 Token。

- 页面先确定主导色，再由组确定视觉角色，子元素继承组的配色。
- `Accent.Primary` 与所在背景缺少可见对比时，改用 Bare、Subtle、Inverse 或非颜色层级手段；不得为了可见而自动切换到另一种品牌色。
- 禁止按组件、单元或元素序号轮换品牌蓝、云灰和墨蓝。

### 2.2 公共颜色与透明度

- 文字、图标、背景—文字组合及对比度执行 `references/common/design-foundation.md`，本文件只引用角色，不重复色值。
- 普通组件填充、线条和图标默认使用实色。
- 不用透明度临时制造浅色卡片或新的色阶；需要浅色底时使用公共规范已有的实色 Token。
- 深色或品牌色背景上的弱化白字、弱化图标，以及 Logo 水印，分别执行 `design-foundation.md`、`masters.md` 与 `references/common/logo.md` 的已验证规则。
- 需要公共规范以外的透明度时，先完成对比度验证并回写公共规范，不得只在单份 PPT 中临时取值。

## 3. Surface / Card

Bare 是默认角色。只有位置和间距不足以表达分组，或存在真实重点、反白背景时，才启用其他角色。

| 角色 | 填充 | 描边 | 圆角 | 内边距 | 文字与图标 |
|---|---|---|---|---|---|
| `Surface.Bare` | 无 | 无 | `Radius.None` | 0 | 公共默认角色 |
| `Surface.Subtle` | `#EBF0F6` | 无 | `Radius.Small` | `Padding.Standard` | 公共默认角色 |
| `Surface.Accent` | `Accent.Primary` | 无 | `Radius.Small` | `Padding.Standard` | 按公共对比度规则自动选择 |
| `Surface.Inverse` | 无，继承所在深色或图片背景 | 无 | `Radius.None` | `Padding.Standard` | 执行公共反白规则 |

- PPT 首版不启用 `Outline`，不得用透明底加四边描边的方式模拟 Outline。
- 需要明确边界时依次考虑位置与间距、`Surface.Subtle`、局部 Divider；只有重大结构边界才使用 `Divider.Strong`。
- 一个内容分支只应用一次 Surface，默认禁止 Surface / Card 嵌套。
- 所有 Surface 默认无投影。

## 4. Divider

| 配方 | 色值 | 粗细 | 用途 |
|---|---|---:|---|
| `Divider.Light` | `#E0E5EC` | `Stroke.Subtle` | 间距仍不足以区分的普通局部分隔 |
| `Divider.Strong` | `#082C5E` | `Stroke.Strong` | 章节、主要区域或真实对比的重大结构边界 |

- Divider 默认关闭；已有 Surface 边界或充分留白时不添加。
- 同一列表或卡片组不得为每个单元重复添加 `Divider.Strong`。
- 最后一项之后不添加 Divider。
- Divider 线条本身不携带固定的相邻间距；首版由页面布局根据内容关系决定。

## 5. Connector

| 配方 | 色值 | 粗细 | 用途 |
|---|---|---:|---|
| `Connector.Neutral` | `#E0E5EC` | 4 pt | 普通步骤或节点之间的流程轨道 |
| `Connector.Emphasis` | `Accent.Primary` | 4 pt | 当前路径、关键方向或重点关系 |

- 两种 Connector 只通过颜色区分，不改变粗细，避免同一轨道产生视觉断层。
- 同一流程默认使用同一种 Connector；只有真实的当前路径或关键关系才局部切换为 Emphasis。
- 只有方向无法通过排列顺序明确判断时才添加箭头；普通横向或纵向 Stepper 不强制每段都带箭头。
- Connector 只表达真实流程关系，不作为填补空白的装饰线；最后节点之后不再延伸。

## 6. Icon Token

Icon Token 的外部尺寸仍使用 `components.md` 的 Small、Standard、Focus 几何档位。

| 配方 | 容器 | 图标 | 内边距 |
|---|---|---|---|
| `IconToken.Bare` | 无 | 公共默认图标角色 | 0 |
| `IconToken.Subtle` | `#EBF0F6` 实色圆形，无描边 | 公共默认图标角色 | `Padding.Icon` |
| `IconToken.Accent` | `Accent.Primary` 实色圆形，无描边 | 先解析容器背景，再选择公共对比色角色 | `Padding.Icon` |

- Subtle 与 Accent 必须使用等宽等高的真正圆形容器，不用圆角矩形模拟。
- 图标图片框扣除 `Padding.Icon` 后，还须检查 PNG 内部透明留白；最终可见图形包围框的最大边不得小于容器直径的 50%。同组图标按可见图形做光学校准，不以透明 PNG 的外框机械判断大小。
- 不能把为浅色背景生成的深色 PNG 直接复用到 Accent / Inverse 状态。生成 Icon Token 前先解析容器配方，再选择或生成对应颜色的 Material Symbols PNG。
- `#1677FF` 品牌蓝和 `#082C5E` 墨蓝背景上的 Icon Token 使用 `#FFFFFF` 100% 反白；其他背景继续按公共对比度规则解析，不临时发明颜色。
- 同一 Surface / Card 反白时，图标、标题和正文分别解析各自的对比度角色，不能只反白文字。
- 深色或图片背景上的普通反白图标直接执行公共反白规则，不额外套色块容器。
- 同组 Icon Token 使用同一配方与尺寸档位，除非存在明确层级或单元异化理由。
- 所有 Icon Token 默认无投影。

## 7. Tag

PPT 首版只启用 `Tag.Text`：

| 配方 | 字号 | 字重 | 背景与边界 | 文字色 |
|---|---:|---:|---|---|
| `Tag.Text` | 10–12 pt | Regular（400） | 无填充、无描边、无图标 | 按所在 Surface 的背景与公共对比度规则解析 |

- `12 pt` 及以下的 Tag 不使用 Medium、Semibold 或 Bold。需要提高辨识度时优先调整前景—背景对比度、位置和留白，不能靠加粗补救。
- Accent / Inverse Card 上使用满足小字号对比度的反白文字；白色或 Subtle Card 上从当前页面强调文字角色与次要文字角色中选择满足对比度的一种。
- Tag 默认单行、无投影，不自动添加胶囊背景、描边或图标。
- 首版不定义 `Tag.Filled` 或 Badge 样式；不得为了“像标签”临时创造底色、圆角或边框。
- 位置、首行避让和无 Tag 时不占位执行 `components.md` 的 `Tag.Text` 几何规则。

## 8. 组内一致性与选择顺序

1. 先按 `component-system.md` 判断信息职责。
2. 再按 `components.md` 选择几何配方并计算有效内容框。
3. 默认使用 Bare；分组不足时使用 Subtle；真实重点使用 Accent；深色或图片背景使用 Inverse。
4. 同一 Collection 的同级组件继承同一 Surface、Icon Token、Divider 与 Connector 配方。
5. 颜色分组、单元异化和两列强对比继续执行 `design-foundation.md` 的语义、面积与记录要求。
6. Icon Token、Tag、Divider 和 Connector 不能脱离公开组件独立充当装饰。

## 9. PptxGenJS 映射

- `x / y / w / h`、矩形圆角和组件内边距先以整数 LU 计算；需要写入英寸属性时统一调用 `components.md` 的 `lu()`。
- 圆角矩形使用 `ShapeType.roundRect`，以 `rectRadius: lu(4)` 或 `rectRadius: lu(8)` 写入明确半径；普通矩形使用 `ShapeType.rect`。
- 圆形容器使用 `ShapeType.ellipse`，并确保 `w === h`；不要依赖超大 `rectRadius`。
- `line.width` 直接写 pt 数值，不调用 `lu()`；Connector 的 `4 pt` 同样直接写入。
- PptxGenJS 十六进制颜色不带 `#`；规范中的 `#E0E5EC` 在代码中写作 `"E0E5EC"`。
- Surface 和 Icon Token 的内边距通过扣减有效内容框实现；文本框仍显式使用 `margin: 0`，不得把 PptxGenJS 默认文本 inset 当作组件内边距。
- Tag 文本框使用当前品牌配置的真实 Regular 字体文件或字体家族，显式关闭 `bold`，并按 `components.md` 计算后的首行右侧坐标写入。
- 实现完成后必须渲染 PPTX，并按 `export-qa.md` 检查圆角、线宽、颜色、组内一致性与不同渲染器下的结果。
