@echo off
echo ========================================
echo AI数字人直播系统 - 部署脚本
echo ========================================
echo.

REM 检查Python版本
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.9+
    pause
    exit /b 1
)

echo [1/8] 检查Python版本...
python -c "import sys; print('Python版本: ' + sys.version)" 2>nul
if errorlevel 1 (
    echo [错误] Python版本检查失败
    pause
    exit /b 1
)

echo [2/8] 创建项目目录结构...
if not exist "config" mkdir config
if not exist "logs" mkdir logs
if not exist "temp" mkdir temp
if not exist "backups" mkdir backups
if not exist "assets" mkdir assets

echo [3/8] 安装Python依赖...
pip install --upgrade pip
if exist "requirements.txt" (
    pip install -r requirements.txt
) else (
    echo [信息] 未找到requirements.txt，安装基础依赖...
    pip install requests aiohttp flask pyautogui websockets redis
)

echo [4/8] 复制配置文件...
if not exist "config\config.json" (
    echo [信息] 请选择平台配置：
    echo 1. TikTok (国际版)
    echo 2. 抖音 (国内版)
    set /p platform="请输入选择 (1/2): "
    
    if "%platform%"=="1" (
        copy "config\tiktok_config_example.json" "config\config.json"
        echo [成功] 已复制TikTok配置文件
    ) else if "%platform%"=="2" (
        copy "config\douyin_config_example.json" "config\config.json"
        echo [成功] 已复制抖音配置文件
    ) else (
        echo [错误] 无效选择
        pause
        exit /b 1
    )
)

echo [5/8] 配置环境检查...
echo [信息] 请确保已安装以下工具：
echo.
echo TikTok平台需要：
echo   - OBS Studio (推流工具)
echo   - 有效的API密钥 (OpenAI, ElevenLabs, D-ID, TikHub)
echo.
echo 抖音平台需要：
echo   - 抖音直播伴侣 (官方推流工具)
echo   - 抖音开放平台权限
echo   - 国产API密钥 (火山方舟、阿里云、硅基智能)
echo.
pause

echo [6/8] 创建启动脚本...
echo @echo off > start_live.bat
echo echo 启动AI数字人直播系统... >> start_live.bat
echo python src\ai_digital_human_live_controller.py >> start_live.bat
echo pause >> start_live.bat

echo [7/8] 创建停止脚本...
echo @echo off > stop_live.bat
echo echo 停止AI数字人直播系统... >> stop_live.bat
echo taskkill /f /im python.exe 2>nul >> stop_live.bat
echo echo 系统已停止 >> stop_live.bat
echo pause >> stop_live.bat

echo [8/8] 部署完成！
echo.
echo ========================================
echo 部署步骤完成！
echo ========================================
echo.
echo 下一步操作：
echo 1. 编辑 config\config.json 文件，填入你的API密钥
echo 2. 根据平台安装必要的工具：
echo    - TikTok: 安装OBS Studio并配置推流
echo    - 抖音: 安装抖音直播伴侣并登录账号
echo 3. 运行 start_live.bat 启动系统
echo 4. 运行 stop_live.bat 停止系统
echo.
echo 详细文档请查看 docs\ 目录
echo.

pause