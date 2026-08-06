# video-transcriber

把 **B 站视频**、**抖音视频** 或 **本地音视频** 转成带时间戳的文字（中文 ASR + 标点恢复）。

基石模型：**FunASR Paraformer-Large + FSMN-VAD + CT-PUNC**（与 AI-VedioToText 项目同一套模型，下载后可互相复用）。

> Agent Skills 标准 skill：`SKILL.md` 为加载入口，适配 pi / Claude Code / Codex / Mavis 等任意支持该标准的智能体；也可作为普通 CLI / Python 库使用。

## 功能

- **B 站** — BV 号 / `bilibili.com` URL / `b23.tv` 短链（自动展开），混合文本也能识别；纯标准库爬虫 + yt-dlp 自动兜底
- **抖音** — `v.douyin.com` 短链 / `douyin.com/video/<id>`；多级 fallback：H5 分享页直连 → Selenium cookie → API CDN（风控也不怕）
- **本地视频** — mp4, mkv, flv, avi, mov, webm 等（用 ffmpeg 抽音轨）
- **本地音频** — mp3, wav, m4a, aac, flac 等
- **输出** — 全文（带标点）+ 句级时间戳 + txt 缓存文件
- **两种 ASR 后端** — 本地 FunASR（GPU 最佳）/ 云端 SiliconFlow（零模型下载），自动切换
- **缓存** — 音频和文本都缓存，重复跑秒回
- **GPU 加速** — 配好 CUDA 后比 CPU 快 5–10 倍

## 新用户快速开始（一条命令）

```bash
git clone https://github.com/zwj-3193655211/read-bilibili-video.git
cd read-bilibili-video       # (clone 后的目录名)

# 方式 A：Windows 双击运行
run.bat --setup           # 自动：选 Python 环境 → 装依赖 → 下模型 → 写配置

# 方式 B：任意环境
python setup.py           # 同上（需要 python3.10–3.12；建议先装 uv 或已有 conda 环境）
```

装完就能用：

```bash
run.bat "BV1xx411c7mD"
run.bat "https://www.bilibili.com/video/BV1xx411c7mD"
run.bat "C:\Videos\lecture.mp4"
run.bat "D:\audios\interview.wav"
```

## 三种运行路径（按需选择，环境负担递减）

| 路径 | 适合谁 | 要什么 | 从零到用 |
|------|--------|--------|---------|
| **A. 本地 FunASR** | avtt/GPU 用户 | 已有模型或下载 ~1.1GB | 0 或 2–10 分钟 |
| **B. 云端 SiliconFlow** | 无 GPU 新用户 | 免费 API key（siliconflow.cn 注册） | ~1 分钟 |
| **C. 自动（默认）** | 大多数用户 | 本地模型优先，没模型但有 key 走云端 | 自动 |

- **路径 B**：`set SILICONFLOW_API_KEY=sk-xxx`（或填 config.json 的 `siliconflow_api_key`），立即可用——**不需要下载模型、不需要装 funasr/torch**，纯 Python 标准库
- **连 Python 都没有？** `run.bat` / `run.sh` 会自动安装 uv，uv 自动下载所需 Python 版本和依赖，全程无感
- 如果你已有 avtt / 任意 conda 环境（funasr + torch 已装），走路径 A，0 安装

## avtt 用户（0 安装，秒级可用）

如果你有 AI-VedioToText 项目的 **avtt conda 环境**（funasr + GPU torch + modelscope 全有），run.bat / run.sh 会自动检测并直接复用，**不装任何东西**：

```bash
run.bat --setup           # 自动复用 D:\Desktop_Archive\AI-VedioToText\model，不重复下载
run.bat "BV1xx411c7mD"
```

模型目录在 `D:\tools\Anaconda3\envs\avtt` 之外也可用 `setup_check.py --model-root <目录>` 指定任意已有模型目录复用。

## ASR 后端说明

`config.json` 的 `asr_backend` 控制转写引擎：

| 值 | 引擎 | 句级时间戳 | 需要 |
|----|------|-----------|------|
| `auto`（默认） | 本地优先，否则云端 | 本地有 | 无 |
| `local` | FunASR Paraformer-Large + VAD + CT-PUNC | ✅ | funasr + ~1.1GB 模型 |
| `cloud` | 云端转写 API（供应商可插拔） | 看供应商 | 仅 API key，零依赖 |

**云端供应商（`asr_provider`）**：

| 供应商 | 配置 | 说明 |
|--------|------|------|
| `siliconflow`（默认） | `asr_model` 任选官方支持模型（2025-08：SenseVoiceSmall / TeleAI/TeleSpeechASR） | 无时间戳 |
| `openai`（通用） | `asr_base_url` + `asr_api_key` + `asr_model` | 任意 OpenAI 兼容端点，如火山方舟 / OpenAI / 智谱 / Groq |

**用火山方舟（豆包）做供应商**：火山方舟 v3 API 是 OpenAI 兼容的，填 4 个字段即可：

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

`asr_verbose_json: true` 时请求 `response_format=verbose_json`，支持该格式的供应商（如豆包 seed-asr）会返回句级时间戳。云端通用限制：音频 ≤1 小时、文件 ≤50MB。

B 站下载已纯标准库化（urllib），直连失败自动降级 **yt-dlp** 兜底（`winget install yt-dlp` 可选安装）。

## 环境选择机制（run.bat / run.sh）

按优先级自动探测，无需配置：

1. **avtt conda env**（复用 GPU torch + funasr + 已下模型，0 安装）
2. **任意 conda env 名为 avtt**（自动扫描 `conda env list`）
3. **uv**（读 `pyproject.toml` 自动建 `.venv` + 装依赖）
4. **system python**（兜底）

## 在智能体中使用（Agent Skills）

把本目录（或软链）放到任意智能体的 skills 目录，例如：

- pi: `~/.pi/agent/skills/video-transcriber/`
- Claude Code: `~/.claude/skills/video-transcriber/`
- Codex: `~/.agents/skills/video-transcriber/`

之后直接说"转写这个 B 站视频 / 转写 C:\Videos\a.mp4"，智能体自动调用 skill。也可手动以 Python 模块方式调用：

```python
import video_transcriber

result = video_transcriber.run("BV1xx411c7mD")       # 模型缺失时自动下载
video_transcriber.check_status()                     # 模型/缓存/ffmpeg 状态
video_transcriber.initialize()                       # 手动下载模型
video_transcriber.setup()                            # 一键安装向导
video_transcriber.clear_cache()
```

`run()` 返回 JSON：

```json
{
  "status": "success",
  "type": "bilibili",
  "title": "视频标题",
  "transcription": "全文（带标点）",
  "transcription_path": "<cache>/text/视频标题.txt",
  "segments": [
    {"start": 0.0, "end": 4.2, "text": "第一句话。"},
    {"start": 4.2, "end": 9.1, "text": "第二句话？"}
  ],
  "duration": 930.5,
  "bv_id": "BV1xx411c7mD",
  "url": "https://...",
  "_skill": {"name": "video-transcriber", "version": "3.0.0"}
}
```

## 配置

`config.json` 首次运行自动生成（skill 根目录）：

```json
{
  "max_duration_minutes": 70,
  "use_punc": true,
  "device": "auto",
  "auto_download": true,
  "asr_backend": "auto",
  "asr_provider": "siliconflow",
  "asr_base_url": "",
  "asr_api_key": "",
  "asr_model": "FunAudioLLM/SenseVoiceSmall",
  "asr_verbose_json": false,
  "model_root": "<skill>/model",
  "cache_dir": "<skill>/cache",
  "cookie": ""
}
```

| 字段 | 说明 |
|------|------|
| `max_duration_minutes` | 单视频上限（0 = 不限） |
| `use_punc` | 本地后端启用 CT-PUNC 标点恢复 |
| `device` | `auto` / `cuda` / `cpu` |
| `auto_download` | 本地模型缺失时首次运行自动下载（默认 true） |
| `asr_backend` | `auto` / `local` / `cloud` |
| `asr_provider` | 云端供应商：`siliconflow` / `openai`（任意 OpenAI 兼容端点） |
| `asr_base_url` | openai 模式必填，如火山方舟 `https://ark.cn-beijing.volces.com/api/v3` |
| `asr_api_key` | 云端 key（也可用环境变量 `ASR_API_KEY`；兼容旧字段 `siliconflow_api_key` / `SILICONFLOW_API_KEY`） |
| `asr_model` | 供应商支持的转写模型名（默认 SenseVoiceSmall，换火山方舟填豆包语音模型） |
| `asr_verbose_json` | `true` 时请求 verbose_json 拿句级时间戳（OpenAI 兼容供应商） |
| `model_root` | 模型根目录（可指向**别处已下载的模型**，如 `D:\Desktop_Archive\AI-VedioToText\model`，跳过 1.1GB 下载） |
| `cache_dir` | 缓存目录 |
| `cookie` | B 站 cookie（可选，登录态可拉大会员） |

## 目录结构

```
video-transcriber/
├── SKILL.md                # Agent Skills 入口
├── README.md
├── setup.py                # 一键安装：环境检查 + 配置 ASR + 写配置
├── setup_check.py          # 向后兼容入口（默认复用 AI-VedioToText 模型）
├── video_transcriber.py    # 主入口（run / setup / info / check_status / ...）
├── asr_backend.py          # ASR 后端抽象：local / siliconflow / auto（纯标准库）
├── bilibili.py             # B 站爬虫（urllib + yt-dlp 兜底）
├── local_media.py          # 本地音视频 + ffmpeg
├── recognizer.py           # FunASR Paraformer 识别
├── download.py             # 模型下载/检查（--check / --force / --model-root）
├── cache.py                # 缓存管理
├── config.py               # 配置
├── run.bat / run.sh        # 一键启动（自动选 avtt / conda / uv / python）
├── manifest.json
├── pyproject.toml          # uv run / pip install . 自动装依赖
└── requirements.txt
```

## 故障排查

| 现象 | 解决 |
|------|------|
| `无法获取视频信息` | B 站地区限制/大会员/登录态失效。填 `cookie` 字段，或装 yt-dlp 自动兜底 |
| `ffmpeg 提取失败` | 装 ffmpeg 并加到 PATH（Windows: `winget install ffmpeg`） |
| `asr_unavailable` | 两条路：`python setup.py` 下本地模型，或设 `ASR_API_KEY` 走云端 |
| 模型下载慢/失败 | 已内置 3 次重试；可 `--model-root` 指定已有模型目录；或设 `MODELSCOPE_CACHE` |
| 云端 HTTP 4xx | 检查 `asr_api_key` / `asr_model` / `asr_base_url` 是否与供应商文档一致 |
| Python 3.13+ 报错 | 本地模式暂不支持 3.13（云端模式不受限）；建议 3.10–3.12 |
| B 站返回 FLV 格式 | 暂不支持 DASH 之外格式，可装 yt-dlp 兜底 |

## License

MIT
