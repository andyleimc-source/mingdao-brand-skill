# 社媒模板资源

存放从 Figma 模板 1:1 转出的可复用 HTML 模板，图片、品牌徽章和装饰图形均直接嵌入，素材本身来自 Figma 原始文件导出，不是 AI 生成。它们是模板结构的一部分，不是可复用的通用图标。

## 文件列表

| 文件名 | 说明 | Figma 来源 |
|---|---|---|
| `wechat-post-签约新客户.html` | 公众号贴图模板，1080×1438，蓝底白卡 + 标题 + 客户 Logo 位 + 认证徽章 | [公众号贴图](https://www.figma.com/design/kN2cStxCCnb53bIRc9bGiQ/%E5%B8%82%E5%9C%BA?node-id=2118-37) |

## 使用规则

- 换客户场景：替换 `#logo` 里的 `<img>` 为对应客户官方 Logo 文件，标题文字按需修改，其余结构/坐标/颜色不要改动。
- 新增通用图标时必须读取 [material-symbols.md](../../references/common/material-symbols.md)，只使用本地 Material Symbols Outlined；不得从模板现有 SVG 装饰图形中拆路径充当图标。
- 背景色 `#1677FF` 为品牌蓝（见 [design-foundation.md](../../references/common/design-foundation.md) 1.1 节），禁止替换成 AI 生成的随机配色。
- 若 Figma 源文件有更新，需重新读取并同步这里的 HTML，避免两边不一致。
