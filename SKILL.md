---
name: video-transcriber
description: Use when user provides a Bilibili URL (BV number, bilibili.com link, b23.tv short link), a Douyin URL (v.douyin.com, douyin.com), or a local media file path (mp4, mkv, flv, avi, mov, webm, m4v, mp3, wav, m4a, flac, aac) and asks to transcribe, convert, extract, or summarize the spoken content. Triggers on "转写这个视频", "提取这段录音的文字", "看看这个 B 站/抖音讲了什么", or any paste of a BV/URL with transcription intent. Also fires when mixed text contains a video link plus a verb like "转写 / 总结 / 提取文字".
license: MIT
compatibility: python>=3.10,<3.13; windows/linux/macos; ffmpeg required for local media
metadata:
  models:
    - iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch (Paraformer-Large, ~848MB)
    - iic/speech_fsmn_vad_zh-cn-16k-common-pytorch (FSMN-VAD, ~4MB)
    - iic/punc_ct-transformer_zh-cn-common-vocab272727-pytorch (CT-PUNC, ~283MB)
---

# video-transcriber

把 B 站视频或本地音视频转成带时间戳的文字。基石模型：**FunASR Paraformer-Large + FSMN-VAD + CT-PUNC**（中文 ASR + 标点恢复）。

## When to Use

- 用户给一个 B 站链接（BV 号 / `bilibili.com/video/...` / `b23.tv/...`），要转写或总结
- 用户给一个抖音链接（`v.douyin.com` 短链 / `douyin.com/video/<id>`），要转写或总结
- 用户给本地视频/音频路径（mp4, mkv, mp3, wav, m4a 等），要文字稿
- 混合文本里塞了个视频链接 + 转写/总结意图

**NOT for**：纯图片 OCR、PDF 文字、纯字幕文件翻译、YouTube（暂未适配）

## Setup（新用户一条命令完成，三种路径按需选择）

```bash
run.bat --setup          # Windows：检查环境 + 配置 ASR + 写配置
./run.sh --setup         # Linux/macOS
```

**三种运行路径（环境负担递减）：**

| 路径 | 适合谁 | 要什么 | 耗时 |
|------|--------|--------|------|
| **A. 本地 FunASR** | avtt/GPU 用户 | 已有模型或下载 ~1.1GB | 0 或 2–10 分钟 |
| **B. 云端 SiliconFlow** | 无 GPU 新用户 | 免费 API key，零模型零依赖 | ~1 分钟 |
| **C. 自动（默认）** | 大多数用户 | 本地模型优先，没模型且有 key 走云端 | 自动 |

- 路径 B：设 `SILICONFLOW_API_KEY=<你的 key>`（siliconflow.cn 免费注册），即可免下 1.1GB 模型直接用
- run.bat / run.sh 连 Python 都没有时会**自动安装 uv**，uv 自动下载 Python + 依赖——全程无感
- 已有 avtt / 任意 conda 环境（装了 funasr + torch）的用户：直接跑，0 安装

```bash
python setup.py --model-root D:\path\to\existing\model   # 复用已有模型，跳过下载
```

## How to Invoke（推荐）

**始终用 `run.bat`（Windows）或 `run.sh`（Linux/macOS）**——自动选 avtt conda env → 任意 conda env → uv → system python 四层通道。不要直接 `python video_transcriber.py`（PATH 里的 python 可能没装 funasr/torch）。

```bash
run.bat "BV1xx411c7mD"
run.bat "https://www.bilibili.com/video/BV1xx411c7mD"
run.bat "帮我看看这个 https://b23.tv/abc123 讲什么"
run.bat "C:\Videos\lecture.mp4"
run.bat "D:\audios\interview.wav"
run.bat --status
run.bat --clear-cache
```

作为 Python 模块调用（智能体集成）：`import video_transcriber`，调用 `run() / info() / check_status() / initialize() / setup() / clear_cache()`。

## ASR 后端（config.json 的 asr_backend）

| 后端 | 说明 | 依赖 |
|------|------|------|
| `auto`（默认） | 本地模型就绪→FunASR；否则有 key→云端 | — |
| `local` | FunASR Paraformer-Large + FSMN-VAD + CT-PUNC（带句级时间戳） | funasr/torch/modelscope + ~1.1GB 模型 |
| `cloud` | 云端转写 API，**供应商可插拔**（纯标准库，零模型下载） | 仅 `asr_api_key`（或环境变量 `ASR_API_KEY`） |

**云端供应商（`asr_provider`）**：

| 供应商 | 配置 | 说明 |
|--------|------|------|
| `siliconflow`（默认） | `asr_model` 任选官方支持模型（2025-08：SenseVoiceSmall / TeleAI/TeleSpeechASR，以官方列表为准） | 无句级时间戳 |
| `openai`（通用） | `asr_base_url` + `asr_api_key` + `asr_model` | 任意 OpenAI 兼容端点；`asr_verbose_json: true` 时支持句级时间戳的供应商返回 segments |

**用火山方舟做供应商**（OpenAI 兼容）：

```json
{
  "asr_backend": "cloud",
  "asr_provider": "openai",
  "asr_base_url": "https://ark.cn-beijing.volces.com/api/v3",
  "asr_api_key": "<火山方舟 API Key>",
  "asr_model": "<豆包语音模型，如 doubao-seed-asr-1>",
  "asr_verbose_json": true
}
```

云端通用限制：音频通常 ≤1 小时、文件 ≤50MB（超出自动报错）。

B 站下载已纯标准库化（urllib），直连失败自动降级 **yt-dlp** 兜底（若已安装）。

## Input Recognition

| 类型 | 示例 |
|------|------|
| BV 号 | `BV1xx411c7mD` |
| 标准 URL | `https://www.bilibili.com/video/BV1xx411c7mD` |
| 短链 | `https://b23.tv/abc123`（自动展开） |
| 抖音短链 | `https://v.douyin.com/xxx/` |
| 抖音视频页 | `https://www.douyin.com/video/<id>` |
| 通用平台链接 | `https://www.youtube.com/watch?v=...` / AcFun / 微博 等（需 yt-dlp，YouTube 需代理） |
| 混合文本 | `帮我看看 https://bilibili.com/video/BV1xx... 讲什么` |
| 本地视频 | `C:\Videos\lecture.mp4` |
| 本地音频 | `D:\audios\interview.wav` |

**抖音下载方案（多级 fallback）**：L1 H5 分享页 SSR 直连（快、零依赖）→ L2 Selenium 浏览器拿 cookie 调 web detail API 拿 CDN 地址（稳定，绕开风控，需装 selenium）→ L3 手动 cookie（浏览器复制，最快最稳）。抖音风控是动态的，失败时稍后重试或填 cookie 即可。

**通用平台**（非 B 站/抖音链接）：走 yt-dlp 主路由下载音频（`pip install yt-dlp`）。分享链接支持**整段粘贴**（自动提取 URL）。

## Output

```json
{
  "status": "success",
  "type": "bilibili",
  "title": "视频标题",
  "transcription": "全文（带标点）",
  "transcription_path": "<cache>/text/视频标题.txt",
  "segments": [{"start": 0.0, "end": 4.2, "text": "第一句..."}, ...],
  "duration": 930.5,
  "bv_id": "BV1xx411c7mD",
  "url": "https://...",
  "_skill": {"name": "video-transcriber", "version": "3.0.0"}
}
```

## Configuration

默认 `config.json`（首次运行自动生成，`model_root` 可指向任意已有模型目录复用）：

```json
{
  "max_duration_minutes": 70,
  "use_punc": true,
  "device": "auto",
  "auto_download": true,
  "asr_backend": "auto",
  "siliconflow_api_key": "",
  "siliconflow_model": "FunAudioLLM/SenseVoiceSmall",
  "model_root": "<skill>/model",
  "cache_dir": "<skill>/cache",
  "cookie": ""
}
```

**复用已有模型**：把 `model_root` 改成已有 Paraformer 三件套的根目录即可，跳过 1.1GB 下载：

```json
{ "model_root": "D:\\Desktop_Archive\\AI-VedioToText\\model" }
```

## Requirements

- Python 3.10–3.12（3.13+ 可能跟 funasr 不兼容）
- ffmpeg（本地音视频必需；Windows: `winget install ffmpeg`）
- ~1.1 GB 磁盘（模型）；可选 NVIDIA GPU（CUDA 加速 5–10x）

## Troubleshooting

| 现象 | 解决 |
|------|------|
| `无法获取视频信息` | B 站地区限制/大会员/登录态失效。填 `cookie` 字段，或装 yt-dlp 自动兜底 |
| `ffmpeg 提取失败` | 装 ffmpeg 并加到 PATH（`winget install ffmpeg`） |
| `asr_unavailable` | 两条路：`python setup.py` 下本地模型，或设 `ASR_API_KEY` 走云端 |
| 模型下载慢/失败 | 重试（已内置 3 次）；或 `--model-root` 指定已有模型目录；或设 `MODELSCOPE_CACHE` |
| 云端 HTTP 4xx | 检查 `asr_api_key` / `asr_model` / `asr_base_url` 是否正确、供应商模型是否支持 |
| B 站返回 FLV 格式 | 暂不支持 DASH 之外格式，可装 yt-dlp 兜底 |
| 时长超限 | 调大 `max_duration_minutes`（0 = 不限） |

## Module Layout

| 文件 | 职责 |
|------|------|
| `run.bat` / `run.sh` | **推荐入口**：自动选 avtt / conda / uv / system python |
| `setup.py` | **一键安装**：环境检查 + 下载模型 + 写配置 |
| `video_transcriber.py` | 主入口：`run / setup / info / check_status / initialize / clear_cache` |
| `asr_backend.py` | ASR 后端抽象：local (FunASR) / siliconflow (云端) / auto，纯标准库 |
| `bilibili.py` | B 站爬虫（urllib 纯标准库 + 自动 cookie 重抓 + yt-dlp 兜底） |
| `douyin.py` | 抖音下载（H5 SSR → Selenium cookie → API CDN 多级 fallback，纯标准库 + 可选 selenium） |
| `local_media.py` | 本地音视频识别 + ffmpeg 提取/转 WAV |
| `recognizer.py` | FunASR Paraformer-Large 识别（单例缓存） |
| `download.py` | 模型下载/检查（CLI：`--check` / `--force` / `--model-root`） |
| `cache.py` | 音频 + 文本缓存管理 |
| `config.py` | 配置加载/保存 |
| `pyproject.toml` | `uv run` / `pip install .` 自动装依赖 |
