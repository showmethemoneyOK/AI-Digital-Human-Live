#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web管理界面
提供系统状态监控、配置管理、日志查看等功能
"""

from flask import Flask, render_template, jsonify, request, send_file
import json
import os
import sys
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Any

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database_manager import DatabaseManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ai-digital-human-live-secret-key-2026'

# 初始化数据库
db = DatabaseManager()

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """获取系统状态"""
    try:
        # 从数据库获取最新状态
        status = {
            "system": {
                "uptime": "24小时",  # 这里应该从实际运行时间计算
                "interaction_count": get_interaction_count(),
                "error_count": get_error_count(),
                "last_restart": get_last_restart_time()
            },
            "apis": {
                "llm": {"status": "connected", "latency": "120ms"},
                "tts": {"status": "connected", "latency": "450ms"},
                "digital_human": {"status": "connected", "latency": "2.3s"},
                "danmaku": {"status": "connected", "messages_per_minute": 15}
            },
            "streaming": {
                "platform": "TikTok",
                "status": "live",
                "viewers": 125,
                "bitrate": "4500kbps",
                "uptime": "3小时25分钟"
            },
            "content_filter": {
                "blocked_today": 12,
                "warnings_today": 8,
                "sensitive_words": 245
            }
        }
        
        return jsonify({"success": True, "data": status})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/interactions')
def get_interactions():
    """获取交互记录"""
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        user_id = request.args.get('user_id')
        
        interactions = db.get_interactions(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        # 转换为字典列表
        data = []
        for interaction in interactions:
            data.append({
                "id": interaction.id,
                "timestamp": interaction.timestamp,
                "user_id": interaction.user_id,
                "platform": interaction.platform,
                "original_content": interaction.original_content[:100] + "..." if len(interaction.original_content) > 100 else interaction.original_content,
                "filtered_content": interaction.filtered_content[:100] + "..." if len(interaction.filtered_content) > 100 else interaction.filtered_content,
                "ai_response": interaction.ai_response[:100] + "..." if len(interaction.ai_response) > 100 else interaction.ai_response,
                "risk_level": interaction.risk_level,
                "response_time_ms": interaction.response_time_ms
            })
        
        return jsonify({"success": True, "data": data, "total": len(data)})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/products')
def get_products():
    """获取商品列表"""
    try:
        products = db.get_active_products()
        
        data = []
        for product in products:
            data.append({
                "id": product.id,
                "name": product.name,
                "category": product.category,
                "price": product.price,
                "original_price": product.original_price,
                "discount": product.discount,
                "promo": product.promo,
                "description": product.description[:200] + "..." if len(product.description) > 200 else product.description,
                "is_active": product.is_active,
                "updated_at": product.updated_at
            })
        
        return jsonify({"success": True, "data": data})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/logs')
def get_logs():
    """获取系统日志"""
    try:
        level = request.args.get('level')
        module = request.args.get('module')
        limit = request.args.get('limit', 100, type=int)
        
        # 这里需要实现获取日志的方法
        # 暂时返回模拟数据
        logs = get_system_logs(level, module, limit)
        
        return jsonify({"success": True, "data": logs})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/config')
def get_config():
    """获取配置"""
    try:
        config_path = "config/config.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 隐藏敏感信息
        hide_sensitive_info(config)
        
        return jsonify({"success": True, "data": config})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/config/update', methods=['POST'])
def update_config():
    """更新配置"""
    try:
        if not request.is_json:
            return jsonify({"success": False, "error": "请求必须是JSON格式"}), 400
        
        new_config = request.json
        
        # 验证配置
        if not validate_config(new_config):
            return jsonify({"success": False, "error": "配置验证失败"}), 400
        
        # 保存配置
        config_path = "config/config.json"
        backup_path = f"backups/config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # 备份原配置
        if os.path.exists(config_path):
            os.makedirs("backups", exist_ok=True)
            import shutil
            shutil.copy2(config_path, backup_path)
        
        # 保存新配置
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(new_config, f, ensure_ascii=False, indent=2)
        
        # 记录配置变更
        db.log_system_event(
            level="INFO",
            module="web_dashboard",
            message="配置已更新",
            details=f"配置备份: {backup_path}"
        )
        
        return jsonify({"success": True, "message": "配置更新成功", "backup": backup_path})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/control/start', methods=['POST'])
def start_system():
    """启动系统"""
    try:
        # 这里应该调用系统启动逻辑
        # 暂时返回成功
        db.log_system_event(
            level="INFO",
            module="web_dashboard",
            message="系统启动命令已发送"
        )
        
        return jsonify({"success": True, "message": "系统启动命令已发送"})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/control/stop', methods=['POST'])
def stop_system():
    """停止系统"""
    try:
        # 这里应该调用系统停止逻辑
        db.log_system_event(
            level="INFO",
            module="web_dashboard",
            message="系统停止命令已发送"
        )
        
        return jsonify({"success": True, "message": "系统停止命令已发送"})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/control/restart', methods=['POST'])
def restart_system():
    """重启系统"""
    try:
        db.log_system_event(
            level="INFO",
            module="web_dashboard",
            message="系统重启命令已发送"
        )
        
        return jsonify({"success": True, "message": "系统重启命令已发送"})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/analytics/daily')
def get_daily_analytics():
    """获取每日分析数据"""
    try:
        days = request.args.get('days', 7, type=int)
        
        # 模拟数据
        data = generate_daily_analytics(days)
        
        return jsonify({"success": True, "data": data})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/analytics/user_behavior')
def get_user_behavior():
    """获取用户行为分析"""
    try:
        # 模拟数据
        data = {
            "top_users": [
                {"user_id": "user123", "interaction_count": 45, "last_seen": "2小时前"},
                {"user_id": "user456", "interaction_count": 32, "last_seen": "5小时前"},
                {"user_id": "user789", "interaction_count": 28, "last_seen": "1天前"}
            ],
            "peak_hours": [
                {"hour": "09:00", "interactions": 120},
                {"hour": "14:00", "interactions": 85},
                {"hour": "20:00", "interactions": 150}
            ],
            "common_questions": [
                {"question": "多少钱？", "count": 56},
                {"question": "有什么功能？", "count": 42},
                {"question": "今天有优惠吗？", "count": 38}
            ]
        }
        
        return jsonify({"success": True, "data": data})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/content_filter/stats')
def get_content_filter_stats():
    """获取内容过滤统计"""
    try:
        # 从数据库获取统计
        stats = {
            "today": {
                "total_messages": 156,
                "blocked": 12,
                "warnings": 8,
                "passed": 136
            },
            "categories": {
                "political": 3,
                "advertising": 5,
                "violence": 2,
                "sexual": 1,
                "scam": 1
            },
            "risk_levels": {
                "safe": 136,
                "low_risk": 8,
                "medium_risk": 4,
                "high_risk": 5,
                "blocked": 3
            }
        }
        
        return jsonify({"success": True, "data": stats})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/export/logs')
def export_logs():
    """导出日志"""
    try:
        log_type = request.args.get('type', 'system')
        date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # 生成日志文件
        log_file = generate_log_file(log_type, date)
        
        if not log_file:
            return jsonify({"success": False, "error": "日志文件不存在"}), 404
        
        return send_file(log_file, as_attachment=True, download_name=f"logs_{log_type}_{date}.json")
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# 辅助函数
def get_interaction_count() -> int:
    """获取交互计数"""
    # 这里应该从数据库获取
    return 156

def get_error_count() -> int:
    """获取错误计数"""
    # 这里应该从数据库获取
    return 12

def get_last_restart_time() -> str:
    """获取最后重启时间"""
    # 这里应该从系统状态获取
    return "2026-03-05 09:00:00"

def get_system_logs(level: str = None, module: str = None, limit: int = 100) -> List[Dict]:
    """获取系统日志"""
    # 这里应该从数据库获取
    # 暂时返回模拟数据
    logs = []
    for i in range(min(limit, 20)):
        logs.append({
            "id": i + 1,
            "timestamp": (datetime.now() - timedelta(minutes=i*5)).isoformat(),
            "level": ["INFO", "WARNING", "ERROR"][i % 3],
            "module": ["main", "api", "streaming", "content_filter"][i % 4],
            "message": f"测试日志消息 {i+1}",
            "details": f"详细信息 {i+1}"
        })
    return logs

def hide_sensitive_info(config: Dict):
    """隐藏敏感信息"""
    if "apis" in config:
        for api_type, api_config in config["apis"].items():
            if "api_key" in api_config and api_config["api_key"]:
                api_config["api_key"] = "***" + api_config["api_key"][-4:] if len(api_config["api_key"]) > 4 else "***"
    
    if "platform" in config:
        platform_config = config["platform"]
        if "stream_key" in platform_config and platform_config["stream_key"]:
            platform_config["stream_key"] = "***" + platform_config["stream_key"][-4:] if len(platform_config["stream_key"]) > 4 else "***"

def validate_config(config: Dict) -> bool:
    """验证配置"""
    required_sections = ["platform", "apis"]
    
    for section in required_sections:
        if section not in config:
            return False
    
    return True

def generate_daily_analytics(days: int) -> List[Dict]:
    """生成每日分析数据"""
    data = []
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        data.append({
            "date": date,
            "interactions": 100 + i * 10,
            "unique_users": 50 + i * 5,
            "blocked_messages": 5 + i,
            "avg_response_time": 1200 + i * 50
        })
    
    return list(reversed(data))

def generate_log_file(log_type: str, date: str) -> Optional[str]:
    """生成日志文件"""
    # 这里应该从实际日志文件生成
    # 暂时创建临时文件
    import tempfile
    
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    
    logs = get_system_logs(limit=100)
    
    with open(temp_file.name, 'w', encoding='utf-8') as f:
        json.dump({"logs": logs}, f, ensure_ascii=False, indent=2)
    
    return temp_file.name

# 静态文件路由
@app.route('/dashboard')
def dashboard():
    """仪表盘页面"""
    return render_template('dashboard.html')

@app.route('/interactions')
def interactions_page():
    """交互记录页面"""
    return render_template('interactions.html')

@app.route('/products')
def products_page():
    """商品管理页面"""
    return render_template('products.html')

@app.route('/logs')
def logs_page():
    """日志查看页面"""
    return render_template('logs.html')

@app.route('/config')
def config_page():
    """配置管理页面"""
    return render_template('config.html')

@app.route('/analytics')
def analytics_page():
    """数据分析页面"""
    return render_template('analytics.html')

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": "资源未找到"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "error": "服务器内部错误"}), 500

if __name__ == '__main__':
    # 创建模板目录
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    os.makedirs(templates_dir, exist_ok=True)
    
    # 创建基础模板
    create_basic_templates(templates_dir)
    
    # 启动Web服务器
    app.run(host='0.0.0.0', port=5000, debug=True)

def create_basic_templates(templates_dir: str):
    """创建基础HTML模板"""
    
    # 基础布局模板
    base_html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}AI数字人直播系统{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        body { padding-top: 20px; background-color: #f8f9fa; }
        .sidebar { position: fixed; top: 0; bottom: 0; left: 0; z-index: 100; padding: 48px 0 0; box-shadow: inset -1px 0 0 rgba(0, 0, 0, .1); }
        .sidebar-sticky { position: relative; top: 0; height: calc(100vh - 48px); padding-top: .5rem; overflow-x: hidden; overflow-y: auto; }
        .nav-link { font-weight: 500; color: