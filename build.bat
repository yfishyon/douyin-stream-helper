@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Python 未安装或未添加到环境变量！
    pause
    exit /b 1
)

pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] pip 未安装或未正确配置！
    pause
    exit /b 1
)

set "skip_confirm="
set "use_nuitka="
for %%a in (%*) do (
    if "%%a"=="-y" set "skip_confirm=1"
    if "%%a"=="nuitka" set "use_nuitka=1"
)

if not defined skip_confirm (
    set /p "confirm=是否继续安装依赖并打包？(Y/N): "
    if /i not "!confirm!"=="Y" (
        echo 操作已取消。
        pause
        exit /b 0
    )
)

pip install -r requirements.txt

if defined use_nuitka (
    echo 使用 Nuitka 打包...
    nuitka --standalone --onefile --windows-uac-admin main.py
) else (
    echo 使用 PyInstaller 打包...
    pyinstaller --onefile --uac-admin main.py
)

echo 打包完成！
pause