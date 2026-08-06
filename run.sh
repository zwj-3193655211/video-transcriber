#!/usr/bin/env bash
# ============================================================
#  video-transcriber launcher (Linux / macOS)
#  Auto-detects Python environment in this priority:
#    1. avtt conda env          (reuse your GPU torch + funasr + models)
#    2. any conda env named avtt (scan `conda env list`)
#    3. uv                      (auto-creates .venv + installs Python if needed)
#    4. system python3          (last resort)
#    5. bootstrap: install uv automatically, then retry step 3
#
#  Usage:
#    ./run.sh "BV1xx411c7mD"
#    ./run.sh "~/Videos/lecture.mp4"
#    ./run.sh --setup            one-shot install: deps + models + config
#    ./run.sh --status
#    ./run.sh --init             download missing models
# ============================================================
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$SCRIPT_DIR/video_transcriber.py"
SETUP="$SCRIPT_DIR/setup.py"

# 1. known avtt paths (customize if yours differs)
for AVTT_PY in \
    "$HOME/anaconda3/envs/avtt/bin/python" \
    "$HOME/miniconda3/envs/avtt/bin/python" \
    "/opt/anaconda3/envs/avtt/bin/python" \
    "/opt/miniconda3/envs/avtt/bin/python" \
    "/usr/local/anaconda3/envs/avtt/bin/python" \
    "/usr/local/miniconda3/envs/avtt/bin/python"; do
  if [ -x "$AVTT_PY" ]; then
    exec "$AVTT_PY" "$SCRIPT" "$@"
  fi
done

# 2. scan conda env list for a name containing "avtt"
if command -v conda >/dev/null 2>&1; then
  AVTT_ROOT="$(conda env list | awk '{print $1, $NF}' | grep -i avtt | awk '{print $NF}' | head -1)"
  if [ -n "$AVTT_ROOT" ] && [ -x "$AVTT_ROOT/bin/python" ]; then
    exec "$AVTT_ROOT/bin/python" "$SCRIPT" "$@"
  fi
fi

# 3. uv (auto venv + install; uv auto-downloads Python if missing)
if command -v uv >/dev/null 2>&1; then
  run_uv() {
    if [ "$1" = "--setup" ]; then
      exec uv run --project "$SCRIPT_DIR" python "$SETUP" "${@:2}"
    fi
    exec uv run --project "$SCRIPT_DIR" python "$SCRIPT" "$@"
  }
  run_uv "$@"
fi

# 4. system python3 fallback
if command -v python3 >/dev/null 2>&1; then
  if [ "$1" = "--setup" ]; then
    exec python3 "$SETUP" "${@:2}"
  fi
  exec python3 "$SCRIPT" "$@"
fi

# 5. bootstrap: install uv automatically (one-time)
echo "[run.sh] No Python found. Installing uv automatically (one-time)..."
if command -v curl >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
elif command -v wget >/dev/null 2>&1; then
  wget -qO- https://astral.sh/uv/install.sh | sh
fi
export PATH="$HOME/.local/bin:$PATH"
if command -v uv >/dev/null 2>&1; then
  echo "[run.sh] uv installed. First run downloads Python + deps automatically, please wait..."
  run_uv() {
    if [ "$1" = "--setup" ]; then
      exec uv run --project "$SCRIPT_DIR" python "$SETUP" "${@:2}"
    fi
    exec uv run --project "$SCRIPT_DIR" python "$SCRIPT" "$@"
  }
  run_uv "$@"
fi
echo "[run.sh] ERROR: auto-install of uv failed. Install Python 3.10-3.12 manually, then retry." >&2
exit 1
