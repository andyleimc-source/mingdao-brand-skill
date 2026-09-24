#!/usr/bin/env python3
"""LibreOffice headless 转换包装脚本。

裸调用 `soffice --headless --convert-to pdf x.pptx` 在沙箱/容器环境里容易卡死，
常见原因是多个实例抢同一个默认用户配置目录的锁，或者转换过程中弹出对话框
（比如字体缺失提示）等不到响应、进程又没有超时保护。这个脚本用两个手段规避：

1. 每次运行都用一个全新的临时用户配置目录（-env:UserInstallation），
   不会跟其他正在跑的 soffice 实例抢锁
2. subprocess 加硬超时，超时直接判定失败并给出明确报错，不会无限挂起

用法（跟 references/materials/ppt/export-qa.md 里写的一致）：
    python scripts/ppt/office/soffice.py --headless --convert-to pdf output.pptx
    python scripts/ppt/office/soffice.py --headless --convert-to pdf output.pptx --outdir ./out --timeout 180
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_TIMEOUT_SECONDS = 120

# 常见的 soffice/libreoffice 安装位置，PATH 里找不到时按顺序兜底
FALLBACK_BINARY_PATHS = [
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",  # macOS
    "/usr/bin/soffice",                                        # 大多数 Linux 发行版
    "/usr/lib/libreoffice/program/soffice",                    # Linux 备选路径
    "/opt/libreoffice/program/soffice",                        # 部分容器镜像
]


def find_soffice_binary() -> str:
    for name in ("soffice", "libreoffice"):
        found = shutil.which(name)
        if found:
            return found
    for path in FALLBACK_BINARY_PATHS:
        if Path(path).exists():
            return path
    sys.exit(
        "找不到 soffice / libreoffice 可执行文件。请先安装 LibreOffice"
        "（macOS: brew install --cask libreoffice；Linux: apt-get install libreoffice）。"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--headless", action="store_true", help="兼容参数，本脚本总是无头运行")
    parser.add_argument("--convert-to", required=True, help="目标格式，例如 pdf")
    parser.add_argument("input", help="输入文件路径，例如 output.pptx")
    parser.add_argument("--outdir", default=None, help="输出目录，默认跟输入文件同目录")
    parser.add_argument(
        "--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS,
        help=f"超时秒数，默认 {DEFAULT_TIMEOUT_SECONDS}s，超时判定失败而不是无限等待",
    )
    args = parser.parse_args()

    soffice_binary = find_soffice_binary()

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        sys.exit(f"输入文件不存在：{input_path}")

    outdir = Path(args.outdir).resolve() if args.outdir else input_path.parent
    outdir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="soffice-profile-") as profile_dir:
        cmd = [
            soffice_binary,
            "--headless",
            "--norestore",
            "--nolockcheck",
            "--nodefault",
            "--nofirststartwizard",
            f"-env:UserInstallation=file://{profile_dir}",
            "--convert-to", args.convert_to,
            "--outdir", str(outdir),
            str(input_path),
        ]

        try:
            result = subprocess.run(cmd, timeout=args.timeout, capture_output=True, text=True)
        except subprocess.TimeoutExpired:
            sys.exit(
                f"soffice 转换 {input_path.name} 超过 {args.timeout} 秒仍未完成，判定为卡死并终止——"
                f"这正是这个包装脚本要拦住的问题。先确认输入文件没有损坏，"
                f"排除后可以用 --timeout 调大再试。"
            )

        if result.returncode != 0:
            sys.exit(
                f"soffice 转换失败（退出码 {result.returncode}）\n"
                f"stdout: {result.stdout}\nstderr: {result.stderr}"
            )

        expected_output = outdir / f"{input_path.stem}.{args.convert_to}"
        if not expected_output.exists():
            sys.exit(
                f"soffice 报告成功，但没有在预期位置找到输出文件：{expected_output}\n"
                f"stdout: {result.stdout}"
            )

        print(str(expected_output))


if __name__ == "__main__":
    main()
