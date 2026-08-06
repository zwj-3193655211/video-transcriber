@echo off
REM ============================================================
REM  video-transcriber launcher (Windows)
REM  Auto-detects Python environment in this priority:
REM    1. avtt conda env          (reuse your GPU torch + funasr + models)
REM    2. any conda env           (scan `conda env list`)
REM    3. uv                      (auto-creates .venv + installs Python if needed)
REM    4. system python           (last resort)
REM    5. bootstrap: install uv automatically, then retry step 3
REM
REM  Usage:
REM    run.bat "BV1xx411c7mD"
REM    run.bat "C:\Videos\lecture.mp4"
REM    run.bat --setup            one-shot install: deps + models + config
REM    run.bat --status
REM    run.bat --init             download missing models
REM
REM  Custom avtt path: edit AVTT_PY below.
REM ============================================================
setlocal EnableExtensions
chcp 65001 >nul

set "SCRIPT_DIR=%~dp0"
set "SCRIPT=%SCRIPT_DIR%video_transcriber.py"
set "SETUP=%SCRIPT_DIR%setup.py"

REM ---- 1. custom avtt path (edit if yours differs) ----
set "AVTT_PY=D:\tools\Anaconda3\envs\avtt\python.exe"
if exist "%AVTT_PY%" goto :use_avtt

REM ---- 2. auto-scan conda envs for one named avtt ----
where conda >nul 2>&1
if %ERRORLEVEL% equ 0 (
    for /f "tokens=*" %%i in ('conda env list') do (
        echo %%i | findstr /i /c:"avtt" >nul 2>&1
        if not errorlevel 1 goto :use_avtt_scan
    )
)
goto :try_uv

:use_avtt
"%AVTT_PY%" "%SCRIPT%" %*
exit /b %ERRORLEVEL%

:use_avtt_scan
for /f "tokens=*" %%i in ('conda env list ^| findstr /i "avtt"') do (
    for %%j in (%%i) do set "AVTT_ROOT=%%j"
)
if exist "%AVTT_ROOT%\python.exe" (
    set "AVTT_PY=%AVTT_ROOT%\python.exe"
    "%AVTT_PY%" "%SCRIPT%" %*
    exit /b %ERRORLEVEL%
)
goto :try_uv

:try_uv
REM ---- 3. uv (auto venv + install; uv auto-downloads Python 3.10-3.12 if missing) ----
where uv >nul 2>&1
if %ERRORLEVEL% equ 0 goto :run_uv

REM ---- 4. system python fallback ----
where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo %* | findstr /i "--setup" >nul 2>&1
    if not errorlevel 1 (
        python "%SETUP%" %*
        exit /b %ERRORLEVEL%
    )
    python "%SCRIPT%" %*
    exit /b %ERRORLEVEL%
)

REM ---- 5. bootstrap: no Python at all, auto-install uv (one-time ~30MB) ----
echo [run.bat] No Python found. Installing uv automatically (one-time, ~30MB)...
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
where uv >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [run.bat] uv installed. First run downloads Python 3.11 + deps automatically, please wait...
    goto :run_uv
)
echo [run.bat] ERROR: auto-install of uv failed. Install Python 3.10-3.12 manually, then retry.
exit /b 1

:run_uv
echo %* | findstr /i "--setup" >nul 2>&1
if not errorlevel 1 (
    uv run --project "%SCRIPT_DIR%" python "%SETUP%" %*
    exit /b %ERRORLEVEL%
)
uv run --project "%SCRIPT_DIR%" python "%SCRIPT%" %*
exit /b %ERRORLEVEL%
