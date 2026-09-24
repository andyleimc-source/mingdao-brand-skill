# 明道云品牌配置

仅在用户明确要求明道云物料，或已从 Logo、品牌名称和上下文确定品牌归属为明道云时读取本文件。读取本文件前先读取 `references/common/design-foundation.md`；Logo 的通用使用和尺寸规则见 `references/common/logo.md`。

## 1. 品牌身份

- 明道云是中文品牌，没有对应英文名或音译名。
- Nocoly 是独立品牌，不得把 Nocoly 当作明道云英文名，也不得把两者拼成一个品牌名称。
- 任何物料、提示词和示例文案中都不得编造 “MingDao Cloud” 等英文名称。
- 使用 `assets/common/logos/` 下的官方文件，不用 AI 重新生成、临摹或重组 Logo。

### 公司全称

- 明道云的公司全称是“上海万企明道软件有限公司”。禁止在物料中修改、杜撰完整的公司全称。
- 仅在涉及“谁承担责任、谁拥有权利、谁是正式合作主体”时使用公司全称，例如法律与交易文件、官方证明材料（营业执照、资质证书、投标文件、备案）、招聘与雇佣材料等。
- 其他日常品牌物料（海报、PPT、社媒、官网等）使用“明道云”品牌名，不需要带出公司全称。

### Logo 选择

| 场景 | 文件 |
|---|---|
| 浅色背景、完整品牌露出 | `mingdao-logo-light.svg` |
| 深色背景、完整品牌露出 | `mingdao-logo-dark.svg` |
| 浅色背景、扁横幅或竖向空间紧张 | `mingdao.svg` |
| 深色背景、扁横幅或竖向空间紧张 | `mingdao-dark.svg` |

HAP、HDP 等组合标志只使用 `assets/common/logos/子产品 logo/` 下以“明道云&”开头的官方版本。

## 2. 色彩

直接使用 `references/common/design-foundation.md` 1.1 节的共享色彩 Token，不建立第二套明道云专属色值。

## 3. 字体

### 3.1 默认与降级

中文、英文和数字默认使用苹方 `PingFang SC`，保持中英混排的统一节奏。生成前检测实际渲染环境是否能取得苹方字面：

1. 检测到苹方：继续使用苹方。
2. 未检测到苹方：提示用户，但不暂停生成；改用 `Source Han Sans CN`。
3. 禁止静默替换为宋体、微软雅黑、Arial 或其他未写入本文件的字体。

缺失苹方时使用以下提示：

> 当前环境未安装“苹方 PingFang SC”，生成效果可能与品牌首选规范存在差异。本次将自动使用品牌认可的备用字体“Source Han Sans CN”，以保证字重、换行和版式稳定。

苹方属于 Apple 授权系统字体，设备上可使用不代表允许复制或再分发；不得将苹方字体文件提交到本 Skill 仓库。Source Han Sans 采用 SIL OFL，可在保留原始许可证和版权声明的前提下作为 Skill 资源分发。

### 3.2 字重

| 用途 | 苹方 | Source Han Sans CN |
|---|---|---|
| 正文 | Regular 400 | Regular 400 |
| 标签、数据强调 | Medium 500 | Medium 500 |
| 标题 | Semibold 600 | Bold 700 |
| 注释 | Light 300 | Light 300 |

苹方没有 Bold 字面。不得用 `bold: true` 请求合成 Bold；需要标题时显式使用 Semibold。使用 Source Han Sans 时显式指定真实的 Regular、Medium、Bold 或 Light 字面。

### 3.3 CSS Token

```css
--font-sans-cjk: "PingFang SC", "Source Han Sans CN", sans-serif;
--font-sans-latin: "PingFang SC", "Source Han Sans CN", sans-serif;
--font-mono: "SF Mono", "Menlo", "Consolas", monospace;
```

等宽字体只用于图表数值、编号、版本号等确需等宽对齐的技术信息。使用前检测真实字面并渲染确认；不得假设字体栈首项一定可用。

### 3.4 字体资源与安装

- HTML、图片和 PDF 优先直接读取 Skill 内合法收录的 Source Han Sans 字体文件，不依赖远程 CDN。
- PPT、PowerPoint 和 LibreOffice 需要系统字体时，先检测当前用户字体库；缺失 Source Han Sans 且 Skill 已收录字体文件时，征得用户一次同意后安装到当前用户字体库。
- 安装脚本必须幂等，不覆盖用户已安装的更新版本，安装后刷新字体缓存并重新检测。
- 如果仓库尚未收录对应字体文件，不得声称已经内置或自动安装；应明确报告缺少的资源。
