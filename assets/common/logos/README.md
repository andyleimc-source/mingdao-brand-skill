# Logo 资源

存放明道云 / Nocoly 官方 Logo 源文件，以及按 `references/common/logo.md` 生成并审核通过的反白派生文件，供本 skill 生成物料时直接调用/嵌入。除补齐缺失的反白版外，禁止用 AI 重新生成或修改 Logo。

**本表的长宽比取自各文件 `viewBox` 实测值**，`logo.md` 第 4 步换算 Logo 高度时直接用这一列，不要凭目测估。

## 明道云

| 文件名 | 长宽比 | 说明 |
|---|---|---|
| `mingdao-logo-light.svg` | **2.043:1** | 完整版·标准色（图形标+标准字+网址，浅色背景用） |
| `mingdao-logo-dark.svg` | **2.044:1** | 完整版·反白（图形标+标准字+网址，深色背景用） |
| `mingdao.svg` | **3.228:1** | 简版·标准色（仅标准字，无图形标、无网址，浅色背景用）——画布高度紧张（如公众号头条封面这类扁横幅）优先用这版控制 logo 占用的竖向空间 |
| `mingdao-dark.svg` | **3.228:1** | 简版·反白（仅标准字，无图形标、无网址，深色背景用） |
| `mingdao-logo_watermark.svg` | **2.043:1** | 水印灰 `#C1C7CF`（由完整版改色），仅文档/PPT 弱化场景 |

## 图形标（只用于浏览器图标、网站小图标等极小位置，不用于头像）

| 文件名 | 长宽比 | 说明 |
|---|---|---|
| `mingdao-ming-icon.svg` | **1:1** | 「明」App 图标：品牌蓝连续圆角方块（超椭圆）+ 白色「明」，字形取自设计组 `正方形明.ai` |
| `mingdao-ming.svg` | **1:1** | 「明」字形·品牌蓝，透明底 |
| `mingdao-ming_dark.svg` | **1:1** | 「明」字形·反白 |
| `nocoly-n.svg` | **1:1** | Nocoly「n」·黑，路径原样取自 `nocoly.svg` 的字母 n（与官网 favicon 同形） |
| `nocoly-n_dark.svg` | **1:1** | Nocoly「n」·反白 |

## Nocoly 与联名

| 文件名 | 长宽比 | 说明 |
|---|---|---|
| `nocoly.svg` | **2.957:1** | Nocoly 标准版，显式纯黑 `#000000` |
| `nocoly_dark.svg` | **2.957:1** | Nocoly 反白版，按 `logo.md` 第 3 节由标准版派生（只改 fill 为白） |
| `nocoly_watermark.svg` | **2.957:1** | Nocoly 水印灰 `#C1C7CF`，仅文档/PPT 弱化场景 |
| `mingdao&nocoly-light.svg` | **6.341:1** | 明道云 + Nocoly 联名（浅色背景用），已是品牌蓝 `#1677FF`。⚠ 旧蓝 `#2196F3` 已退役，任何 logo 都不得再使用 |
| `mingdao&nocoly-dark.svg` | **6.376:1** | 明道云 + Nocoly 联名反白版；深色、品牌蓝或高饱和背景使用。文件内含官方自带的白色透明度层级，必须原样使用 |

## 子产品（`子产品 logo/` 目录）

| 文件名 | 长宽比 | 说明 |
|---|---|---|
| `子产品 logo/HAP-横版.svg` | **2.966:1** | HAP 横版，图形为品牌蓝 `#1677FF`、文字为显式纯黑 `#000000` |
| `子产品 logo/HAP-竖版.svg` | **0.651:1** | HAP 竖版（高大于宽），图形为品牌蓝 `#1677FF`、文字为显式纯黑 `#000000` |
| `子产品 logo/HAP-横版_dark.svg` / `HAP-竖版_dark.svg` / `HDP-横版_dark.svg` / `HDP-竖版_dark.svg` | 同标准版 | 独立产品标反白版，按 `logo.md` 第 3 节派生 |
| `子产品 logo/HDP-横版.svg` | **3.044:1** | HDP 横版，图形为品牌蓝 `#1677FF`、文字为显式纯黑 `#000000` |
| `子产品 logo/HDP-竖版.svg` | **0.683:1** | HDP 竖版（高大于宽），图形为品牌蓝 `#1677FF`、文字为显式纯黑 `#000000` |
| `子产品 logo/明道云&HAP.svg` | **5.985:1** | 明道云 + HAP 组合，品牌蓝 `#1677FF` + 白 |
| `子产品 logo/明道云&HAP_dark.svg` | **5.814:1** | 明道云 + HAP 组合反白版，深色背景用 |
| `子产品 logo/明道云&HDP.svg` | **5.930:1** | 明道云 + HDP 组合 |
| `子产品 logo/明道云&HDP_dark.svg` | **5.760:1** | 明道云 + HDP 组合反白版，深色背景用 |
| `子产品 logo/nocoly&HAP.svg` | **5.302:1** | Nocoly + HAP 组合，浅色背景用 |
| `子产品 logo/nocoly&HAP_dark.svg` | **5.312:1** | Nocoly + HAP 组合反白版，深色背景用 |
| `子产品 logo/nocoly&HDP.svg` | **5.257:1** | Nocoly + HDP 组合，浅色背景用 |
| `子产品 logo/nocoly&HDP_dark.svg` | **5.267:1** | Nocoly + HDP 组合反白版，深色背景用 |

> 目录名含中文和空格，脚本里引用时记得加引号或转义。

## PNG（`png/` 目录）

每个 SVG 都有同名透明底 PNG，长边 2000px，目录结构与 SVG 一致。由 SVG 直接渲染（`magick -background none -density 1200 <src>.svg -resize 2000x2000 <out>.png`），SVG 更新后须重出对应 PNG。

## 通用约定

- 优先放 SVG（矢量、可无损缩放）；如有印刷用途，另存 AI/EPS 源文件，命名加 `.ai` / `.eps` 后缀。
- 品牌选择见 [mingdao.md](../../../references/brands/mingdao.md) 与 [nocoly.md](../../../references/brands/nocoly.md)，通用使用和尺寸计算见 [logo.md](../../../references/common/logo.md)。
- **位图物料（PPT、封面图等）嵌入 SVG 前需转 PNG**：`magick -background none -density 600 <src>.svg -resize <目标宽>x <out>.png`。必须带 `-background none` 保留透明，`-density` 要足够高否则边缘发毛；只指定宽度、让高度按原始比例自动换算，禁止同时写死宽高（会形变）。
