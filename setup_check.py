#!/usr/bin/env python3
"""
向后兼容入口（等价于 `python setup.py`）。

对 avtt 用户：默认复用 AI-VedioToText 项目已下好的模型目录，
不重复下载 1.1GB；对没有该目录的新用户，回退到 skill/model 正常下载。

用法：
  python setup_check.py                     # 一键安装（复用 AI-VedioToText 模型）
  python setup_check.py --model-root <path> # 指定模型目录
"""
import subprocess
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

SKILL_DIR = Path(__file__).parent.resolve()
# avtt 用户已有的模型目录（AI-VedioToText 项目）
AI_VEDIO_MODEL = Path(r"D:\Desktop_Archive\AI-VedioToText\model")
SKILL_MODEL = SKILL_DIR / "model"


def main() -> int:
    extra = list(sys.argv[1:])
    # 未显式指定 --model-root 时：优先复用 AI-VedioToText 的模型，否则默认下载到 skill/model
    if "--model-root" not in extra and not any(a in ("-h", "--help") for a in extra):
        if AI_VEDIO_MODEL.exists():
            extra = ["--model-root", str(AI_VEDIO_MODEL)] + extra
            print(f"[setup_check] 检测到已有模型目录，将复用：{AI_VEDIO_MODEL}")
        else:
            extra = ["--model-root", str(SKILL_MODEL)] + extra
    return subprocess.call([sys.executable, str(SKILL_DIR / "setup.py")] + extra)


if __name__ == "__main__":
    sys.exit(main())
