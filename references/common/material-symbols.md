# Material Symbols 图标规范

所有明道云 / Nocoly 品牌物料统一使用本地 Google Material Symbols Outlined。Logo、二维码、照片、品牌插画、数据图表不属于“通用图标”，不受本规则替代，但也不能伪装成图标库资源。

`prototypes/` 下的历史实验稿不是可复用素材，其中可能仍有占位色块或手绘 SVG；不得从该目录复制图标或生成逻辑。

## 唯一来源与固定风格

- 只从 `assets/common/icons/material-symbols/` 读取资源；禁止使用 Google Fonts CDN。
- 只使用 **Outlined** 风格；禁止混入 Material Icons、Rounded、Sharp、Emoji、Lucide、Font Awesome、Heroicons、Iconify 或手绘 SVG 图标。
- 默认参数：`FILL=0`、`wght=400`、`GRAD=0`、`opsz=24`。仅在表达选中/开启状态时使用 `FILL=1`；同一组图标保持相同参数。
- 图标名必须存在于 `codepoints.txt`。没有完全匹配项时选语义最接近的合法图标，仍不合适就取消图标，不得切换图标库。
- 图标颜色和容器背景继续遵守 `design-foundation.md`；不得沿用图标库示例颜色。

## 强制工作流

先验证官方资产，再搜索图标名：

```bash
python scripts/common/material_symbols.py verify-assets
python scripts/common/material_symbols.py search "account workflow"
```

### HTML / 网页预览

将 `MaterialSymbolsOutlined.woff2` 随 HTML 一起本地加载；单文件交付时将 WOFF2 转成 data URI 嵌入，不得改用远程 CDN。图标必须保留标准类名和合法 ligature 名，便于校验：

```css
@font-face {
  font-family: "Material Symbols Outlined";
  src: url("./MaterialSymbolsOutlined.woff2") format("woff2");
  font-style: normal;
  font-weight: 100 700;
}

.material-symbols-outlined {
  font-family: "Material Symbols Outlined";
  font-style: normal;
  font-weight: 400;
  line-height: 1;
  letter-spacing: normal;
  text-transform: none;
  white-space: nowrap;
  word-wrap: normal;
  direction: ltr;
  font-feature-settings: "liga";
  -webkit-font-feature-settings: "liga";
  -webkit-font-smoothing: antialiased;
  font-variation-settings: "FILL" 0, "wght" 400, "GRAD" 0, "opsz" 24;
}
```

```html
<span class="material-symbols-outlined" data-material-symbol="account_tree"
      aria-hidden="true">account_tree</span>
```

展示预览前验证 HTML；有图标时必须带 `--require-icons`：

```bash
python scripts/common/material_symbols.py validate output.html --require-icons
```

### PPT / 位图物料

不得自行画图标或截取网页。用本地 TTF 渲染带来源元数据的透明 PNG：

```bash
python scripts/common/material_symbols.py render account_tree \
  --output-dir generated-icons --size 256 --color "#1677FF"
```

将命令输出的 `ms-outlined__*.png` 原样交给生成脚本使用，不要重命名或二次栅格化。PPT 同时校验生成源码、图标目录和最终 PPTX；页面确实用了图标时加 `--require-icons`：

```bash
python scripts/common/material_symbols.py validate generate-deck.js generated-icons --require-icons
python scripts/common/material_symbols.py validate output.pptx --require-icons
```

如果物料完全没有通用图标，去掉 `--require-icons`；不得为了让校验通过而添加无意义图标。
