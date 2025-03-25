@echo off
chcp 65001
title 安装依赖 - TikTok视频混剪应用

echo ╔════════════════════════════════════════╗
echo ║          依赖安装程序启动中...        ║
echo ╚════════════════════════════════════════╝
echo.

:: 请求管理员权限
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo 请求管理员权限...
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    if exist "%temp%\getadmin.vbs" ( del "%temp%\getadmin.vbs" )
    pushd "%CD%"
    CD /D "%~dp0"

:: 检查Python是否安装
echo [1/5] 检查Python环境...
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
echo [2/5] 安装Python依赖包...
if exist requirements.txt (
    pip install -r requirements.txt --progress-bar on
    echo [成功] Python依赖安装完成
) else (
    echo [警告] 未找到requirements.txt文件
)

:: 配置winget源
echo.
echo [3/5] 配置winget源...
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
echo [4/5] 安装FFmpeg...
echo 正在下载并安装FFmpeg（这可能需要几分钟时间）...
winget install ffmpeg --accept-source-agreements --accept-package-agreements

:: 添加FFmpeg到环境变量
echo.
echo [5/5] 配置FFmpeg环境变量...
set "FFMPEG_PATH=%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-7.1.1-full_build\bin"

:: 使用PowerShell添加到系统环境变量
powershell -Command "$oldPath = [Environment]::GetEnvironmentVariable('Path', 'Machine'); if (-not $oldPath.Contains('%FFMPEG_PATH%')) { $newPath = $oldPath + ';%FFMPEG_PATH%'; [Environment]::SetEnvironmentVariable('Path', $newPath, 'Machine'); }"

:: 使用PowerShell添加到用户环境变量
powershell -Command "$oldPath = [Environment]::GetEnvironmentVariable('Path', 'User'); if (-not $oldPath.Contains('%FFMPEG_PATH%')) { $newPath = $oldPath + ';%FFMPEG_PATH%'; [Environment]::SetEnvironmentVariable('Path', $newPath, 'User'); }"

:: 刷新当前会话的环境变量
set "PATH=%PATH%;%FFMPEG_PATH%"

:: 检查FFmpeg是否可用
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [警告] FFmpeg环境变量设置可能未成功
    echo [提示] 请手动将以下路径添加到系统环境变量：
    echo %FFMPEG_PATH%
    echo [提示] 或重启系统后重试
) else (
    echo [成功] FFmpeg环境变量配置完成并可以使用
)

echo.
echo ╔════════════════════════════════════════╗
echo ║          所有依赖安装已完成！         ║
echo ║      现在您可以运行一键启动.bat       ║
echo ╚════════════════════════════════════════╝

pause 