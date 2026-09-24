#!/usr/bin/env python3
"""把一份 pptx 的所有页面拼成一张带页码的缩略图网格。

用途：给自检 subagent 一次看完整份 deck，不用一页页单独看图，省 token 也省轮次
（对应 references/materials/ppt/export-qa.md 的视觉检查环节）。

用法：
    python scripts/ppt/thumbnail.py output.pptx
    python scripts/ppt/thumbnail.py output.pptx my-prefix

不传第二个参数时，前缀默认取输入文件名（不是写死的固定值）——同一目录下测试多份不同的
deck 不会互相覆盖缩略图，这是刻意跟 Anthropic 官方 pptx skill 的 thumbnail.py 反着来的：
它默认前缀是固定的 "thumbnails"，官方文档自己也承认这个默认值容易导致"同一目录跑两份
deck，后一份的缩略图覆盖前一份，第一份的缩略图就这样丢了"，我们没有理由重复这个已知坑。

单份网格图最多放 12 页，超过 12 页自动拆成多张（-2、-3...），避免一张图缩得太小看不清。
"""

import argparse
import math
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SLIDES_PER_GRID = 12
GRID_COLUMNS = 4
CELL_WIDTH = 480
LABEL_HEIGHT = 28
CELL_PADDING = 12
PDFTOPPM_DPI = 100  # 缩略图不需要高分辨率，100dpi 够看清版式/文字是否溢出


def find_pdftoppm() -> str:
    import shutil
    path = shutil.which("pdftoppm")
    if not path:
        sys.exit(
            "找不到 pdftoppm。请先安装 Poppler"
            "（macOS: brew install poppler；Linux: apt-get install poppler-utils）。"
        )
    return path


def pptx_to_pdf(pptx_path: Path, workdir: Path) -> Path:
    soffice_wrapper = Path(__file__).resolve().parent / "office" / "soffice.py"
    result = subprocess.run(
        [sys.executable, str(soffice_wrapper), "--headless", "--convert-to", "pdf",
         str(pptx_path), "--outdir", str(workdir)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        sys.exit(f"pptx 转 pdf 失败：\n{result.stdout}\n{result.stderr}")
    pdf_path = workdir / f"{pptx_path.stem}.pdf"
    if not pdf_path.exists():
        sys.exit(f"soffice 报告成功但没找到输出的 pdf：{pdf_path}")
    return pdf_path


def pdf_to_slide_images(pdf_path: Path, workdir: Path) -> list[Path]:
    pdftoppm = find_pdftoppm()
    out_prefix = workdir / "slide"
    result = subprocess.run(
        [pdftoppm, "-jpeg", "-r", str(PDFTOPPM_DPI), str(pdf_path), str(out_prefix)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        sys.exit(f"pdf 转图片失败：\n{result.stdout}\n{result.stderr}")
    images = sorted(workdir.glob("slide-*.jpg")) or sorted(workdir.glob("slide*.jpg"))
    if not images:
        sys.exit(f"pdftoppm 报告成功但没找到输出图片，检查 {workdir} 下的文件")
    return images


# PIL 的 ImageFont.load_default() 是纯 ASCII 位图字体，画中文会变成方框（"囗"）。
# 按常见系统路径找一个能显示中文的字体；一个都找不到就退回英文标签，不能让标签开天窗。
CJK_FONT_CANDIDATES = [
    "/System/Library/Fonts/PingFang.ttc",              # macOS，跟品牌字体栈一致，优先
    "/System/Library/Fonts/Hiragino Sans GB.ttc",       # macOS 备选
    "/System/Library/Fonts/STHeiti Medium.ttc",         # macOS 备选
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",  # 常见 Linux 路径
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",  # 常见 Linux 路径（Debian/Ubuntu）
]


def load_label_font(size: int):
    for path in CJK_FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size), True  # (font, 支持中文)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size), False
    except TypeError:
        return ImageFont.load_default(), False  # 旧版 Pillow 不支持 size 参数


def build_grid(slide_images: list[Path], output_path: Path, start_index: int = 0) -> None:
    sample = Image.open(slide_images[0])
    cell_h = round(CELL_WIDTH * sample.height / sample.width)

    n = len(slide_images)
    cols = min(GRID_COLUMNS, n)
    rows = math.ceil(n / cols)

    grid_w = cols * (CELL_WIDTH + CELL_PADDING) + CELL_PADDING
    grid_h = rows * (cell_h + LABEL_HEIGHT + CELL_PADDING) + CELL_PADDING

    grid = Image.new("RGB", (grid_w, grid_h), "white")
    draw = ImageDraw.Draw(grid)
    font, supports_cjk = load_label_font(18)

    for idx, img_path in enumerate(slide_images):
        col, row = idx % cols, idx // cols
        x = CELL_PADDING + col * (CELL_WIDTH + CELL_PADDING)
        y = CELL_PADDING + row * (cell_h + LABEL_HEIGHT + CELL_PADDING)

        thumb = Image.open(img_path).convert("RGB").resize((CELL_WIDTH, cell_h))
        grid.paste(thumb, (x, y))
        draw.rectangle([x, y, x + CELL_WIDTH - 1, y + cell_h - 1], outline="#D6DBE2", width=1)
        page_no = start_index + idx + 1
        label = f"第 {page_no} 页" if supports_cjk else f"Slide {page_no}"
        draw.text((x, y + cell_h + 4), label, fill="#151A21", font=font)

    grid.save(output_path, quality=90)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pptx", help="输入的 .pptx 文件")
    parser.add_argument("prefix", nargs="?", default=None, help="输出文件名前缀，默认取 pptx 文件名")
    args = parser.parse_args()

    pptx_path = Path(args.pptx).resolve()
    if not pptx_path.exists():
        sys.exit(f"文件不存在：{pptx_path}")
    if pptx_path.suffix.lower() != ".pptx":
        sys.exit("只支持 .pptx 文件")

    prefix = args.prefix or pptx_path.stem

    with tempfile.TemporaryDirectory(prefix="thumbnail-") as workdir_str:
        workdir = Path(workdir_str)
        pdf_path = pptx_to_pdf(pptx_path, workdir)
        slide_images = pdf_to_slide_images(pdf_path, workdir)

        batches = [slide_images[i:i + SLIDES_PER_GRID] for i in range(0, len(slide_images), SLIDES_PER_GRID)]
        output_paths = []
        for batch_idx, batch in enumerate(batches):
            if len(batches) == 1:
                out_name = f"{prefix}-thumbs.jpg"
            else:
                out_name = f"{prefix}-thumbs-{batch_idx + 1}.jpg"
            out_path = pptx_path.parent / out_name
            build_grid(batch, out_path, start_index=batch_idx * SLIDES_PER_GRID)
            output_paths.append(out_path)

        for p in output_paths:
            print(str(p))


if __name__ == "__main__":
    main()
