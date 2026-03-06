@echo off
chcp 65001 >nul
echo.
echo ========================================
echo    AI数字人直播系统 - 快速启动脚本
echo ========================================
echo.

REM 检查Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ 未找到Python，请先安装Python 3.9+
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查Python版本
for /f "tokens=2" %%i in ('python --version 2^>nul') do set PYTHON_VERSION=%%i
echo ✅ 检测到Python版本: %PYTHON_VERSION%

REM 创建虚拟环境
if not exist "venv" (
    echo.
    echo 正在创建虚拟环境...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ❌ 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo ✅ 虚拟环境创建成功
)

REM 激活虚拟环境
echo.
echo 激活虚拟环境...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ❌ 激活虚拟环境失败
    pause
    exit /b 1
)

REM 安装依赖
echo.
echo 安装依赖包...
pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ 安装依赖失败
    pause
    exit /b 1
)
echo ✅ 依赖安装完成

REM 创建必要目录
echo.
echo 创建必要目录...
if not exist "config" mkdir config
if not exist "logs" mkdir logs
if not exist "temp" mkdir temp
if not exist "cache" mkdir cache
if not exist "backups" mkdir backups
echo ✅ 目录创建完成

REM 检查配置文件
echo.
echo 检查配置文件...
if not exist "config\config.json" (
    echo ⚠️  未找到配置文件 config.json
    echo.
    echo 请选择平台：
    echo 1. 抖音 (Douyin)
    echo 2. TikTok
    echo.
    set /p PLATFORM="请输入选择 (1/2): "
    
    if "%PLATFORM%"=="1" (
        copy config\douyin_config_example.json config\config.json >nul
        echo ✅ 已创建抖音配置文件模板
        echo.
        echo 请编辑 config\config.json 文件，填入你的API密钥
        echo 然后重新运行此脚本
    ) else if "%PLATFORM%"=="2" (
        copy config\tiktok_config_example.json config\config.json >nul
        echo ✅ 已创建TikTok配置文件模板
        echo.
        echo 请编辑 config\config.json 文件，填入你的API密钥
        echo 然后重新运行此脚本
    ) else (
        echo ❌ 无效选择
    )
    pause
    exit /b 0
)
echo ✅ 配置文件已就绪

REM 检查环境变量文件
if not exist ".env" (
    echo.
    echo ⚠️  未找到环境变量文件 .env
    copy .env.example .env >nul 2>nul
    if exist ".env.example" (
        echo ✅ 已创建环境变量文件模板
        echo.
        echo 请编辑 .env 文件，填入你的API密钥（可选）
    )
)

REM 选择运行模式
echo.
echo ========================================
echo           选择运行模式
echo ========================================
echo.
echo 1. 抖音模式 (Douyin)
echo 2. TikTok模式
echo 3. 测试模式
echo 4. 退出
echo.
set /p MODE="请选择模式 (1/2/3/4): "

if "%MODE%"=="1" (
    echo.
    echo 🚀 启动抖音模式...
    echo.
    python src/main.py --platform douyin --config config/config.json
) else if "%MODE%"=="2" (
    echo.
    echo 🚀 启动TikTok模式...
    echo.
    echo ⚠️  TikTok模式需要Webhook服务器
    echo     请确保已配置WEBHOOK_URL并暴露公网
    echo.
    python src/main.py --platform tiktok --config config/config.json
) else if "%MODE%"=="3" (
    echo.
    echo 🔧 启动测试模式...
    echo.
    if exist "test_start.py" (
        python test_start.py
    ) else (
        echo ❌ 测试脚本不存在
        pause
    )
) else if "%MODE%"=="4" (
    echo.
    echo 👋 再见！
) else (
    echo.
    echo ❌ 无效选择
    pause
)

REM 暂停查看结果
echo.
pause