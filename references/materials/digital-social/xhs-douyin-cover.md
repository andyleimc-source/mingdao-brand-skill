# 小红书 / 视频号 / 抖音封面

- **尺寸**：1080×1440px（3:4）竖版 / 1440×1080px（4:3）横版
- **平台特点**：小红书偏生活美学，视频号/抖音偏动感吸睛
- **横向网格**（图文/多元素左右分区时，两种画布各自独立计算，无强制安全边距）：
  - 3:4 竖版（1080×1440）：固定用 **6 列**（物料专属选择，不套用 `references/common/grid-system.md` 默认规则）
  - 4:3 横版（1440×1080）：固定用 **10 列**（物料专属选择）
  两者都按 `references/common/grid-system.md` 公式计算：gutter 固定 8px，列宽向下取整到 8px 模数，零头吸收进边距，具体像素值每次按当次画布重新算。
  抖音/视频号版式需为上下各留出文字预留区（纵向留白，跟这里的横向分区是两回事）：顶部约 20%、底部约 30%，左右分区仍按上面的列宽取整数列跨度，不能直接套用纵向的百分比。

> 若制作 9:16 竖版素材，需遵循 `references/materials/digital-social/mobile-poster-vertical-video.md` 安全构图框。
> 通用原则见 `references/materials/digital-social/digital-social-common.md`（社媒 & 数字图片通用原则）。
