@echo off
chcp 65001
title 安装依赖 - TikTok视频混剪应用

echo ╔════════════════════════════════════════╗
echo ║          依赖安装程序启动中...        ║
echo ╚════════════════════════════════════════╝
echo.

:: 检查Python是否安装
echo [1/4] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python未安装！请先安装Python 3.9或更高版本。
    pause
    exit /b 1
) else (
    echo [成功] Python已安装
)

:: 安装pip依赖
echo.
echo [2/4] 安装Python依赖包...
if exist requirements.txt (
    pip install -r requirements.txt --progress-bar on
    echo [成功] Python依赖安装完成
) else (
    echo [警告] 未找到requirements.txt文件
)

:: 配置winget源
echo.
echo [3/4] 配置winget源...
echo 正在切换到USTC镜像源...
winget source remove winget >nul 2>&1
winget source add winget https://mirrors.ustc.edu.cn/winget-source
if errorlevel 1 (
    echo [警告] winget源配置失败，将使用默认源继续安装
) else (
    echo [成功] winget源配置完成
)

:: 安装FFmpeg
echo.
echo [4/4] 安装FFmpeg...
echo 正在下载并安装FFmpeg（这可能需要几分钟时间）...
winget install ffmpeg --accept-source-agreements --accept-package-agreements

:: 检查FFmpeg是否安装成功
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [警告] FFmpeg安装可能未成功，请手动检查
) else (
    echo [成功] FFmpeg安装完成
)

echo.
echo ╔════════════════════════════════════════╗
echo ║          所有依赖安装已完成！         ║
echo ║      现在您可以运行一键启动.bat       ║
echo ╚════════════════════════════════════════╝

pause 