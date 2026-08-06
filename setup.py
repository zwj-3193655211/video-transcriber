#!/usr/bin/env python3
"""
video-transcriber one-shot installer / first-run setup

For NEW users: one command does everything.
    1. verify Python + key deps (funasr / modelscope / ffmpeg)
    2. download the 3 ASR models (Paraformer-Large + FSMN-VAD + CT-PUNC, ~1.1GB)
       -> or reuse an existing model dir via --model-root (skip download)
    3. write config.json with the resolved settings

Usage:
  python setup.py                    # full setup: deps check + models + config
  python setup.py --model-root D:\\path\\to\\existing\\model
                                     # reuse models already downloaded elsewhere
  python setup.py --no-download      # skip model download, only check + write config
  python setup.py --check            # verify environment only, write nothing

Notes:
  - Model download goes through ModelScope (fast in CN). If it fails, set
    the MODELSCOPE_CACHE env var to a writable cache dir and retry.
  - torch is pulled in automatically by funasr; if you want GPU, install a
    CUDA build of torch first (see README).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

SKILL_DIR = Path(__file__).parent.resolve()
DEFAULT_MODEL_DIR = SKILL_DIR / "model"
CONFIG_FILE = SKILL_DIR / "config.json"


def step(title: str) -> None:
    print(f"\n[{title}]")


def check_deps() -> bool:
    step("1/3 环境依赖")
    ok = True
    # 云端模式只需纯标准库；本地模式需要 funasr/torch/modelscope
    try:
        import funasr
        print(f"  OK  funasr {funasr.__version__}（本地 ASR）")
    except ImportError:
        print("  --  funasr 未装（仅本地 ASR 需要；云端模式可跳过）")
    try:
        import modelscope
        print(f"  OK  modelscope {modelscope.__version__}（模型下载）")
    except ImportError:
        print("  --  modelscope 未装（仅本地模型下载需要）")
    try:
        import torch
        print(f"  OK  torch {torch.__version__} (cuda: {torch.cuda.is_available()})")
    except ImportError:
        print("  --  torch 未装（仅本地 ASR 需要；云端模式可跳过）")
    try:
        import requests
        print(f"  OK  requests {requests.__version__}")
    except ImportError:
        print("  --  requests 未装（纯标准库已可运行，非必需）")

    key = os.environ.get("ASR_API_KEY", "").strip() or os.environ.get("SILICONFLOW_API_KEY", "").strip()
    if key:
        print(f"  OK  ASR_API_KEY 已设置（云端 ASR 可用，零模型下载）")
    else:
        print("  --  ASR_API_KEY 未设置（可选：填了走云端转写，免下 1.1GB 模型）")

    ff = shutil.which("ffmpeg")
    if ff:
        print(f"  OK  ffmpeg {ff}")
    else:
        print("  !!  ffmpeg 未找到（本地视频/音频必需；Windows: winget install ffmpeg）")
        ok = False

    if not ok:
        print("\n  依赖缺失的解决办法：")
        print("    A) 有 uv（推荐）: uv run --project <skill-dir> python setup.py")
        print("    B) 手动:        pip install -r requirements.txt")
    return ok


def check_models(model_root: Path) -> bool:
    step("2/3 ASR 模型")
    need = [
        ("VAD",       model_root / "vad" / "speech_fsmn_vad_zh-cn-16k-common-pytorch" / "model.pt"),
        ("PUNC",      model_root / "punc" / "punc_ct-transformer_zh-cn-common-vocab272727-pytorch" / "model.pt"),
        ("Paraformer", model_root / "paraformer" / "paraformer-offline" / "iic"
                      / "speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch" / "model.pt"),
    ]
    ok = True
    for name, f in need:
        if f.exists():
            mb = sum(p.stat().st_size for p in f.parent.rglob("*") if p.is_file()) / 1024 / 1024
            print(f"  OK  {name} ({mb:.0f} MB)  {f.parent}")
        else:
            print(f"  !!  {name} 缺失: {f}")
            ok = False
    return ok


def write_config(model_root: Path) -> Path:
    cfg = {
        "max_duration_minutes": 70,
        "use_punc": True,
        "device": "auto",
        "auto_download": True,
        "asr_backend": "auto",
        "asr_provider": "siliconflow",
        "asr_base_url": "",
        "asr_api_key": os.environ.get("ASR_API_KEY", "")
        or os.environ.get("SILICONFLOW_API_KEY", ""),
        "asr_model": "FunAudioLLM/SenseVoiceSmall",
        "asr_verbose_json": False,
        "model_root": str(model_root),
        "cache_dir": str(SKILL_DIR / "cache"),
        "cookie": "",
    }
    CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  OK  写入配置 {CONFIG_FILE}")
    print(f"       model_root = {model_root}")
    print(f"       asr_backend = auto（本地模型优先，否则云端）")
    return CONFIG_FILE


def main() -> int:
    p = argparse.ArgumentParser(description="video-transcriber 一键安装/配置")
    p.add_argument("--model-root", default=str(DEFAULT_MODEL_DIR),
                   help=f"模型根目录（默认下载到 {DEFAULT_MODEL_DIR}；可指向已有模型目录跳过下载）")
    p.add_argument("--no-download", action="store_true", help="跳过模型下载")
    p.add_argument("--check", action="store_true", help="仅检查环境，不写配置")
    args = p.parse_args()

    print("=" * 60)
    print("video-transcriber 安装向导")
    print(f"  skill 目录: {SKILL_DIR}")
    print(f"  Python:     {sys.executable} ({sys.version.split()[0]})")
    print("=" * 60)

    deps_ok = check_deps()

    model_root = Path(args.model_root).resolve()
    models_ok = check_models(model_root)

    # 3/3: 下载缺失模型（云端模式可跳过）
    if args.check:
        print("\n" + "=" * 60)
        print("检查完成（未写配置）。")
        print("=" * 60)
        return 0 if (deps_ok and models_ok) else 1

    key = os.environ.get("ASR_API_KEY", "").strip() or os.environ.get("SILICONFLOW_API_KEY", "").strip()
    if not models_ok and not args.no_download:
        if key:
            print("\nℹ️  检测到 ASR_API_KEY：可选择免下载模型，直接走云端 ASR。")
            print("   仍想下载本地模型（GPU 用户推荐）请继续，5 秒后开始...")
            print("   跳过下载：python setup.py --no-download")
            time.sleep(5)
        step("3/3 下载缺失模型 (~1.1GB, ModelScope 国内源)")
        model_root.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(
            [sys.executable, str(SKILL_DIR / "download.py"),
             "--model-root", str(model_root)],
        )
        if r.returncode != 0:
            print("\n!! 模型下载未完成。可用选项：")
            print(f"   - 重试: python {SKILL_DIR / 'download.py'} --model-root {model_root}")
            print("   - 复用已有模型: python setup.py --model-root <已有目录>")
            return 1
        models_ok = check_models(model_root)

    if not models_ok:
        print("\n!! 模型未下载。可继续使用云端 ASR：")
        print("   1) 设置环境变量 ASR_API_KEY=<你的 key>（SiliconFlow / 火山方舟等，见 README）")
        print("   2) 重新运行 setup.py 写入配置（或手动填 config.json 的 asr_api_key）")
        return 1

    write_config(model_root)

    print("\n" + "=" * 60)
    print("安装完成！接下来可以：")
    print(f'  run.bat "BV1xx411c7mD"            (Windows)')
    print(f'  ./run.sh "BV1xx411c7mD"           (Linux/macOS)')
    print('  或在任意智能体里说："转写这个 B 站视频 / 本地视频"')
    print("=" * 60)
    return 0 if deps_ok else 0  # config written even if deps incomplete


if __name__ == "__main__":
    sys.exit(main())
