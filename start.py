#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动脚本 - AI数字人直播系统
开箱即用的启动入口
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/startup.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def check_environment():
    """检查运行环境"""
    logger.info("检查运行环境...")
    
    # 检查Python版本
    if sys.version_info < (3, 9):
        logger.error("需要Python 3.9或更高版本")
        return False
    
    # 检查必要目录
    required_dirs = ['config', 'logs', 'data', 'temp', 'backups', 'assets']
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            logger.info(f"创建目录: {dir_name}")
            os.makedirs(dir_name, exist_ok=True)
    
    # 检查配置文件
    if not os.path.exists('config/config.json'):
        logger.error("配置文件不存在: config/config.json")
        logger.info("请先运行 setup.bat 进行配置")
        return False
    
    # 检查依赖
    try:
        import requests
        import aiohttp
        import flask
        logger.info("核心依赖检查通过")
    except ImportError as e:
        logger.error(f"缺少依赖: {e}")
        logger.info("请运行: pip install -r requirements.txt")
        return False
    
    return True

def check_configuration():
    """检查配置"""
    logger.info("检查配置...")
    
    try:
        import json
        with open('config/config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 检查必要配置
        required_configs = [
            ('platform.type', '平台类型'),
            ('platform.room_id', '直播间ID'),
            ('platform.stream_url', '推流地址'),
            ('platform.stream_key', '推流密钥'),
            ('apis.llm.api_key', 'LLM API密钥'),
            ('apis.tts.api_key', 'TTS API密钥'),
            ('apis.digital_human.api_key', '数字人API密钥'),
            ('apis.danmaku.api_key', '弹幕API密钥')
        ]
        
        missing_configs = []
        for config_path, config_name in required_configs:
            keys = config_path.split('.')
            value = config
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    missing_configs.append(config_name)
                    break
        
        if missing_configs:
            logger.warning(f"以下配置缺失或为空: {', '.join(missing_configs)}")
            logger.info("请编辑 config/config.json 文件补充配置")
            return False
        
        logger.info("配置检查通过")
        return True
        
    except Exception as e:
        logger.error(f"配置检查失败: {e}")
        return False

def start_web_dashboard():
    """启动Web管理界面"""
    logger.info("启动Web管理界面...")
    
    try:
        import subprocess
        import threading
        
        def run_web():
            subprocess.run([sys.executable, 'web_dashboard.py'], 
                          stdout=subprocess.DEVNULL, 
                          stderr=subprocess.DEVNULL)
        
        # 在新线程中启动Web界面
        web_thread = threading.Thread(target=run_web, daemon=True)
        web_thread.start()
        
        logger.info("Web管理界面已启动: http://localhost:5000")
        return True
        
    except Exception as e:
        logger.error(f"启动Web管理界面失败: {e}")
        return False

async def main():
    """主函数"""
    print("=" * 60)
    print("AI数字人直播系统 - 启动")
    print("=" * 60)
    print()
    
    # 1. 检查环境
    if not check_environment():
        print("\n环境检查失败，请解决上述问题后重试")
        return
    
    # 2. 检查配置
    if not check_configuration():
        print("\n配置检查失败，请编辑 config/config.json 文件")
        print("或运行 setup.bat 重新配置")
        return
    
    # 3. 启动Web管理界面
    start_web_dashboard()
    
    # 4. 导入主应用
    try:
        from main import AIDigitalHumanLiveApp
    except ImportError as e:
        logger.error(f"导入主应用失败: {e}")
        print("\n请确保所有依赖已安装: pip install -r requirements.txt")
        return
    
    # 5. 创建并运行应用
    print("\n" + "=" * 60)
    print("正在启动AI数字人直播系统...")
    print("=" * 60)
    print()
    
    app = AIDigitalHumanLiveApp('config/config.json')
    
    # 初始化系统
    print("初始化系统...")
    if not await app.initialize():
        print("\n系统初始化失败，请检查日志文件: logs/system.log")
        return
    
    print("\n系统初始化完成！")
    print("\n访问以下地址管理系统:")
    print("  Web管理界面: http://localhost:5000")
    print("  系统状态: http://localhost:5000/dashboard")
    print("\n按 Ctrl+C 停止系统")
    print()
    
    # 运行系统
    try:
        await app.run()
    except KeyboardInterrupt:
        print("\n\n收到停止信号，正在关闭系统...")
    except Exception as e:
        logger.error(f"系统运行异常: {e}")
        print(f"\n系统运行异常: {e}")
        print("详细日志请查看: logs/system.log")
    
    print("\n系统已停止")

if __name__ == '__main__':
    # 设置Windows控制台编码
    if sys.platform == 'win32':
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)  # UTF-8
    
    # 运行主函数
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n程序已终止")
    except Exception as e:
        logger.error(f"程序异常: {e}")
        print(f"\n程序异常: {e}")
        print("请查看日志文件: logs/startup.log")
    
    print("\n按Enter键退出...")
    input()