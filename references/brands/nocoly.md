# Nocoly 品牌配置

仅在用户明确要求 Nocoly 物料，或已从 Logo、品牌名称和上下文确定品牌归属为 Nocoly 时读取本文件。读取本文件前先读取 `references/common/design-foundation.md`；Logo 的通用使用和尺寸规则见 `references/common/logo.md`。

## 1. 品牌身份

- Nocoly 是独立英文品牌，不是明道云的英文名或替代名称。
- 非联名物料不得出现明道云 Logo、明道云中文品牌名或明道云子产品组合标志。
- 浅色背景使用 `assets/common/logos/nocoly.svg`；深色、品牌蓝或高饱和背景优先使用已有的 `nocoly_dark.svg`，文件不存在时按 `references/common/logo.md` 生成并保存独立反白派生文件后使用。禁止在物料中临时覆盖标准版颜色，也禁止把黑色标准版直接压在此类背景上。
- HAP、HDP 等组合标志只使用 `assets/common/logos/子产品 logo/` 下以 `nocoly&` 开头的官方版本。
- 联名物料只有在用户明确要求明道云与 Nocoly 联名时才可同时使用两个品牌资产。

## 2. 色彩

直接使用 `references/common/design-foundation.md` 1.1 节的共享色彩 Token，不建立第二套 Nocoly 专属色值。共享色值不代表两个品牌可以在同一物料中互换 Logo 或品牌名称。

## 3. 字体

Nocoly 面向多语言市场，正式生成字体采用 **Noto Sans CJK + Inter**。Helvetica Neue 和 San Francisco 仅可作为视觉调研参照，不进入正式字体栈，也不得随 Skill 分发。

### 3.1 语言映射

| 内容语言 | 字体 |
|---|---|
| 英文及拉丁文字为主 | Inter |
| 简体中文 `zh-CN` | Noto Sans CJK SC |
| 台湾繁体 `zh-TW` | Noto Sans CJK TC |
| 香港繁体 `zh-HK` | Noto Sans CJK HK |
| 日文 `ja` | Noto Sans CJK JP |
| 韩文 `ko` | Noto Sans CJK KR |

不能只写笼统的 `Noto Sans CJK` 后依赖渲染环境猜地区字形。HTML 根据 `lang` 属性加载对应字体；PPT、图片和 PDF 按文本块的实际语言显式指定地区字体。

### 3.2 英文与 CJK 混排

- 英文标题、英文正文、独立标签、数据和数字优先使用 Inter。
- CJK 段落中偶尔出现的英文单词、产品名或数字默认跟随对应 Noto Sans CJK 字体，避免逐词切换造成基线、字宽和字重跳变。
- 英文成为主要信息时，整块文字使用 Inter，不逐字符切换。
- 同一文本块中确需混用两套字体时，校正字号、基线和字间距，并用实际渲染结果验收。

### 3.3 字重

只使用两套字体都具有真实字面的三档：

| 用途 | 字重 |
|---|---|
| 正文、标签 | Regular 400 |
| 数据强调 | Medium 500 |
| 标题 | Bold 700 |

不使用合成粗体，不用 600 模拟介于 Medium 与 Bold 之间的层级。层级不足时优先调整字号、颜色和留白。

### 3.4 CSS Token

```css
--font-sans-latin: "Inter", sans-serif;
--font-sans-zh-cn: "Noto Sans CJK SC", sans-serif;
--font-sans-zh-tw: "Noto Sans CJK TC", sans-serif;
--font-sans-zh-hk: "Noto Sans CJK HK", sans-serif;
--font-sans-ja: "Noto Sans CJK JP", sans-serif;
--font-sans-ko: "Noto Sans CJK KR", sans-serif;
```

不要把 SC、TC、HK、JP、KR 五个实例按顺序写成一个通用回退栈；地区字形由内容语言决定，不由字体是否安装决定。

### 3.5 字体资源与安装

Noto Sans CJK 与 Inter 均采用 SIL OFL。官方字体资源位于 `assets/common/fonts/nocoly/`：Inter 4.1 使用 Variable WOFF2；Noto Sans CJK 2.004 使用 SC / TC / HK / JP / KR 五个地区的 Variable TTF。`SOURCE.json` 记录固定版本、上游链接、语言映射和 SHA-256，两个许可证文件与字体一起分发。

每次生成或修改 Nocoly HTML 后，必须立即运行字体后处理；脚本根据根 `<html lang>` 与嵌套 `lang` 只嵌入 Inter 和实际使用的 CJK 地区实例，重复执行不会重复插入：

```bash
python3 scripts/common/font_assets.py verify-assets
python3 scripts/common/font_assets.py embed-html output.html
python3 scripts/common/font_assets.py validate-html output.html
```

HTML 必须声明 `en`、`zh-CN`、`zh-TW`、`zh-HK`、`ja` 或 `ko`；多语言局部内容用嵌套 `lang` 标记。单文件交付使用 data URI，不保留 Google Fonts、gstatic 或 Inter CDN 引用。不得手工复制 Base64、跳过 `validate-html`，或把五套 CJK 字体无差别全部嵌入每个文件。

随 Skill 分发时必须：

- 使用官方发布文件，记录版本、下载来源和校验值；
- 在字体目录保留对应的 OFL 许可证与版权声明；
- 不修改后继续沿用原始字体名；
- 不从 Google Fonts CDN 或其他远程 CDN 临时加载。

HTML 使用上述脚本自动嵌入；由 HTML 渲染的图片与 PDF 必须从同一已校验文件生成。PPT、PowerPoint 和 LibreOffice 需要系统字体时，先检测当前用户字体库；缺失且 Skill 已收录可安装字体文件时，征得用户一次同意后安装到当前用户字体库。安装脚本必须幂等，不覆盖更新版本，安装后刷新字体缓存并重新检测。

当前 Inter 资产是 Web 用 WOFF2，不作为系统字体安装源；PPT 需要 Inter 系统字体时仍须先检测并报告。任何清单内资源缺失或校验失败时，不得声称字体已内置、自动嵌入或自动安装。
