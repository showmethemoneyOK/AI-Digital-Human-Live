#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试启动脚本
"""

import os
import sys
import json

print("=" * 60)
print("AI数字人直播系统 - 启动测试")
print("=" * 60)
print()

# 1. 检查Python版本
print("1. 检查Python版本...")
try:
    print(f"Python版本: {sys.version}")
    if sys.version_info < (3, 9):
        print("⚠️ 需要Python 3.9或更高版本")
    else:
        print("✅ Python版本检查通过")
except Exception as e:
    print(f"❌ Python版本检查失败: {e}")

print()

# 2. 检查必要目录
print("2. 检查目录结构...")
required_dirs = ['config', 'logs', 'data', 'temp', 'backups', 'assets']
for dir_name in required_dirs:
    if os.path.exists(dir_name):
        print(f"  ✅ {dir_name}/")
    else:
        print(f"  ⚠️ {dir_name}/ (不存在，将创建)")
        os.makedirs(dir_name, exist_ok=True)

print()

# 3. 检查配置文件
print("3. 检查配置文件...")
config_path = 'config/config.json'
if os.path.exists(config_path):
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"  ✅ 配置文件存在: {config_path}")
        
        # 检查必要配置
        required_configs = [
            ('platform.type', '平台类型'),
            ('platform.room_id', '直播间ID'),
            ('platform.stream_url', '推流地址'),
            ('platform.stream_key', '推流密钥')
        ]
        
        missing = []
        for config_path_str, config_name in required_configs:
            keys = config_path_str.split('.')
            value = config
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    missing.append(config_name)
                    break
        
        if missing:
            print(f"  ⚠️ 以下配置缺失: {', '.join(missing)}")
        else:
            print("  ✅ 基础配置检查通过")
            
    except Exception as e:
        print(f"  ❌ 配置文件读取失败: {e}")
else:
    print(f"  ❌ 配置文件不存在: {config_path}")
    print("  请运行 setup.bat 或复制示例配置文件")

print()

# 4. 检查依赖
print("4. 检查Python依赖...")
required_modules = ['requests', 'aiohttp', 'flask', 'asyncio']
for module in required_modules:
    try:
        __import__(module)
        print(f"  ✅ {module}")
    except ImportError:
        print(f"  ❌ {module} (未安装)")

print()

# 5. 检查源代码
print("5. 检查源代码模块...")
src_files = [
    'src/api_clients.py',
    'src/streaming_controller.py', 
    'src/database_manager.py',
    'src/content_filter.py',
    'src/prompt_manager.py',
    'src/ai_digital_human_live_system.py',
    'main.py',
    'start.py',
    'web_dashboard.py'
]

for file_path in src_files:
    if os.path.exists(file_path):
        print(f"  ✅ {file_path}")
    else:
        print(f"  ❌ {file_path} (不存在)")

print()

# 6. 总结
print("=" * 60)
print("启动测试总结")
print("=" * 60)

print("\n下一步操作:")
print("1. 如果缺少依赖，运行: pip install -r requirements.txt")
print("2. 如果缺少配置文件，运行: setup.bat")
print("3. 编辑 config/config.json 填入API密钥")
print("4. 启动系统: python start.py")
print("5. 访问管理界面: http://localhost:5000")

print("\n按Enter键退出...")
input()