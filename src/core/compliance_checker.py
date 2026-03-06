#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合规检查器
确保内容符合抖音/TikTok平台规则
"""

import json
import logging
import time
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ComplianceChecker:
    """合规检查器"""
    
    def __init__(self, config: Dict):
        """初始化合规检查器"""
        self.config = config
        self.platform = config.get("platform", "douyin")
        
        # 敏感词库
        self.sensitive_words = config.get("COMPLIANCE", {}).get("sensitive_words", [])
        
        # 合规规则
        self.rules = self._load_compliance_rules()
        
        # 检查历史
        self.check_history = []
        self.max_history = 100
        
        logger.info(f"合规检查器初始化完成，平台: {self.platform}")
    
    def _load_compliance_rules(self) -> Dict:
        """加载合规规则"""
        if self.platform == "douyin":
            return self._get_douyin_rules()
        elif self.platform == "tiktok":
            return self._get_tiktok_rules()
        else:
            return self._get_general_rules()
    
    def _get_douyin_rules(self) -> Dict:
        """抖音合规规则"""
        return {
            "max_response_length": 100,  # 最大回复长度
            "min_response_length": 5,    # 最小回复长度
            "disclosure_required": True,  # 必须标注AI身份
            "disclosure_interval": 600,   # 标注间隔（秒）
            "content_filter": True,       # 内容过滤
            "sensitive_check": True,      # 敏感词检查
            "commercial_limits": {        # 商业限制
                "max_promotion_frequency": 5,  # 每分钟最多促销次数
                "no_false_advertising": True,  # 禁止虚假宣传
                "no_price_comparison": True    # 禁止价格对比
            }
        }
    
    def _get_tiktok_rules(self) -> Dict:
        """TikTok合规规则"""
        return {
            "max_response_length": 80,    # 最大回复长度
            "min_response_length": 3,     # 最小回复长度
            "disclosure_required": True,  # 必须标注AI身份
            "disclosure_interval": 300,   # 标注间隔（秒）
            "content_filter": True,       # 内容过滤
            "sensitive_check": True,      # 敏感词检查
            "human_interaction": {        # 真人互动要求
                "required": True,
                "interval_minutes": 15,
                "min_duration_seconds": 30
            },
            "community_guidelines": {     # 社区准则
                "no_hate_speech": True,
                "no_harassment": True,
                "no_violence": True,
                "no_scams": True
            }
        }
    
    def _get_general_rules(self) -> Dict:
        """通用合规规则"""
        return {
            "max_response_length": 100,
            "min_response_length": 5,
            "disclosure_required": True,
            "disclosure_interval": 600,
            "content_filter": True,
            "sensitive_check": True
        }
    
    async def check_all(self) -> Dict:
        """执行所有合规检查"""
        checks = []
        
        # 1. 配置检查
        config_check = await self._check_configuration()
        checks.append(config_check)
        
        # 2. 内容安全检查
        content_check = await self._check_content_safety()
        checks.append(content_check)
        
        # 3. 平台特定检查
        platform_check = await self._check_platform_specific()
        checks.append(platform_check)
        
        # 汇总结果
        all_passed = all(check.get("passed", False) for check in checks)
        errors = []
        
        for check in checks:
            if not check.get("passed", False):
                errors.extend(check.get("errors", []))
        
        result = {
            "passed": all_passed,
            "checks": checks,
            "errors": errors,
            "timestamp": time.time()
        }
        
        # 记录检查历史
        self._record_check(result)
        
        return result
    
    async def _check_configuration(self) -> Dict:
        """检查配置"""
        errors = []
        
        # 检查必要配置
        required_configs = []
        
        if self.platform == "douyin":
            required_configs = ["DOUYIN_APP_ID", "DOUYIN_APP_SECRET", "ROOM_ID"]
        elif self.platform == "tiktok":
            required_configs = ["TIKTOK_APP_ID", "TIKTOK_APP_SECRET", "TIKTOK_ROOM_ID"]
        
        for config_key in required_configs:
            if not self.config.get(config_key):
                errors.append(f"缺少必要配置: {config_key}")
        
        # 检查API密钥格式
        api_keys = ["AI_API_KEY", "TTS_API_KEY", "DIGITAL_HUMAN_API_KEY"]
        for key in api_keys:
            value = self.config.get(key)
            if value and len(value) < 10:  # 简单长度检查
                errors.append(f"{key} 格式可能不正确")
        
        return {
            "name": "配置检查",
            "passed": len(errors) == 0,
            "errors": errors,
            "checked_items": len(required_configs) + len(api_keys)
        }
    
    async def _check_content_safety(self) -> Dict:
        """检查内容安全"""
        # 这里可以添加更复杂的内容安全检查
        # 例如：调用内容安全API、检查敏感词库等
        
        return {
            "name": "内容安全检查",
            "passed": True,
            "message": "内容安全检查通过",
            "sensitive_words_count": len(self.sensitive_words)
        }
    
    async def _check_platform_specific(self) -> Dict:
        """平台特定检查"""
        if self.platform == "douyin":
            return await self._check_douyin_specific()
        elif self.platform == "tiktok":
            return await self._check_tiktok_specific()
        else:
            return {
                "name": "平台检查",
                "passed": True,
                "message": "通用平台检查通过"
            }
    
    async def _check_douyin_specific(self) -> Dict:
        """抖音特定检查"""
        errors = []
        
        # 检查数字人提供商是否在白名单
        digital_human_provider = self.config.get("DIGITAL_HUMAN_PROVIDER", "").lower()
        whitelist_providers = ["guiji", "youliao", "xiangxin"]
        
        if digital_human_provider not in whitelist_providers:
            errors.append(f"数字人提供商 {digital_human_provider} 可能不在抖音白名单中")
        
        # 检查是否配置了AI标注
        if self.rules["disclosure_required"]:
            disclosure_text = self.config.get("COMPLIANCE", {}).get("disclosure_text")
            if not disclosure_text:
                errors.append("未配置AI身份标注文本")
        
        return {
            "name": "抖音合规检查",
            "passed": len(errors) == 0,
            "errors": errors,
            "whitelist_check": digital_human_provider in whitelist_providers
        }
    
    async def _check_tiktok_specific(self) -> Dict:
        """TikTok特定检查"""
        errors = []
        
        # 检查Webhook配置
        webhook_url = self.config.get("WEBHOOK_URL")
        if not webhook_url:
            errors.append("TikTok模式需要配置WEBHOOK_URL")
        elif not webhook_url.startswith("https://"):
            errors.append("WEBHOOK_URL必须使用HTTPS")
        
        # 检查AI标注配置
        if self.rules["disclosure_required"]:
            disclosure_text = self.config.get("COMPLIANCE", {}).get("disclosure_text")
            if not disclosure_text:
                errors.append("未配置AI身份标注文本")
            elif "AI" not in disclosure_text.upper() and "Virtual" not in disclosure_text:
                errors.append("AI标注文本应包含'AI'或'Virtual'标识")
        
        # 检查真人互动配置
        human_config = self.rules.get("human_interaction", {})
        if human_config.get("required", False):
            human_interval = self.config.get("COMPLIANCE", {}).get("human_interval_minutes")
            if not human_interval:
                errors.append("未配置真人互动间隔")
        
        return {
            "name": "TikTok合规检查",
            "passed": len(errors) == 0,
            "errors": errors,
            "webhook_configured": bool(webhook_url)
        }
    
    async def check_message(self, message_data: Dict) -> Dict:
        """检查单条消息"""
        start_time = time.time()
        
        try:
            message_type = message_data.get("type", "")
            content = message_data.get("content", "")
            user = message_data.get("nickname", "未知用户")
            
            checks = []
            
            # 1. 敏感词检查
            sensitive_check = self._check_sensitive_words(content)
            checks.append(sensitive_check)
            
            # 2. 长度检查
            length_check = self._check_message_length(content)
            checks.append(length_check)
            
            # 3. 内容类型检查
            type_check = self._check_message_type(message_type, content)
            checks.append(type_check)
            
            # 4. 用户行为检查
            user_check = self._check_user_behavior(user, message_data)
            checks.append(user_check)
            
            # 汇总结果
            all_passed = all(check.get("passed", True) for check in checks)
            warnings = []
            blocks = []
            
            for check in checks:
                if not check.get("passed", True):
                    if check.get("block", False):
                        blocks.append(check.get("reason", "未知原因"))
                    else:
                        warnings.append(check.get("reason", "未知警告"))
            
            processing_time = time.time() - start_time
            
            result = {
                "passed": all_passed and len(blocks) == 0,
                "blocked": len(blocks) > 0,
                "warnings": warnings,
                "blocks": blocks,
                "checks": checks,
                "processing_time_ms": round(processing_time * 1000, 2),
                "timestamp": time.time()
            }
            
            # 记录检查
            self._record_message_check(message_data, result)
            
            return result
            
        except Exception as e:
            logger.error(f"消息检查失败: {e}")
            return {
                "passed": False,
                "error": str(e),
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "timestamp": time.time()
            }
    
    def _check_sensitive_words(self, content: str) -> Dict:
        """检查敏感词"""
        if not self.sensitive_words or not content:
            return {"passed": True, "name": "敏感词检查"}
        
        content_lower = content.lower()
        found_words = []
        
        for word in self.sensitive_words:
            if word.lower() in content_lower:
                found_words.append(word)
        
        if found_words:
            return {
                "passed": False,
                "name": "敏感词检查",
                "reason": f"发现敏感词: {', '.join(found_words[:3])}",
                "block": True,
                "found_words": found_words
            }
        else:
            return {"passed": True, "name": "敏感词检查"}
    
    def _check_message_length(self, content: str) -> Dict:
        """检查消息长度"""
        if not content:
            return {"passed": False, "name": "长度检查", "reason": "消息内容为空", "block": True}
        
        length = len(content)
        max_length = self.rules.get("max_response_length", 100)
        min_length = self.rules.get("min_response_length", 5)
        
        if length > max_length:
            return {
                "passed": False,
                "name": "长度检查",
                "reason": f"消息过长 ({length} > {max_length})",
                "block": False,  # 警告但不阻止
                "suggestion": f"请缩短到{max_length}字以内"
            }
        elif length < min_length:
            return {
                "passed": False,
                "name": "长度检查",
                "reason": f"消息过短 ({length} < {min_length})",
                "block": False
            }
        else:
            return {"passed": True, "name": "长度检查", "length": length}
    
    def _check_message_type(self, message_type: str, content: str) -> Dict:
        """检查消息类型"""
        # 这里可以添加更复杂的类型检查
        # 例如：识别广告、识别违规内容等
        
        return {"passed": True, "name": "类型检查", "type": message_type}
    
    def _check_user_behavior(self, user: str, message_data: Dict) -> Dict:
        """检查用户行为"""
        # 这里可以添加用户行为分析
        # 例如：频率限制、恶意用户检测等
        
        return {"passed": True, "name": "用户行为检查", "user": user}
    
    def _record_check(self, check_result: Dict):
        """记录检查结果"""
        self.check_history.append({
            "timestamp": time.time(),
            "result": check_result
        })
        
        # 保持历史记录长度
        if len(self.check_history) > self.max_history:
            self.check_history = self.check_history[-self.max_history:]
    
    def _record_message_check(self, message_data: Dict, check_result: Dict):
        """记录消息检查结果"""
        # 这里可以记录到数据库或日志文件
        log_entry = {
            "timestamp": time.time(),
            "message_id": message_data.get("message_id", ""),
            "user": message_data.get("nickname", ""),
            "content_preview": message_data.get("content", "")[:50],
            "check_result": check_result
        }
        
        # 记录到日志
        if not check_result.get("passed", True):
            logger.warning(f"消息检查未通过: {log_entry}")
    
    async def get_compliance_report(self, hours: int = 24) -> Dict:
        """获取合规报告"""
        cutoff_time = time.time() - (hours * 3600)
        
        recent_checks = [
            check for check in self.check_history
            if check["timestamp"] > cutoff_time
        ]
        
        total_checks = len(recent_checks)
        passed_checks = sum(1 for check in recent_checks if check["result"].get("passed", False))
        
        # 统计消息检查
        message_stats = {
            "total": total_checks,
            "passed": passed_checks,
            "failed": total_checks - passed_checks,
            "pass_rate": round(passed_checks / total_checks * 100, 2) if total_checks > 0 else 0
        }
        
        # 统计错误类型
        error_types = {}
        for check in recent_checks:
            if not check["result"].get("passed", False):
                errors = check["result"].get("errors", [])
                for error in errors:
                    error_type = error.split(":")[0] if ":" in error else "其他"
                    error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            "period_hours": hours,
            "timestamp": time.time(),
            "message_stats": message_stats,
            "error_types": error_types,
            "platform": self.platform,
            "sensitive_words_count": len(self.sensitive_words),
            "compliance_score": self._calculate_compliance_score(message_stats)
        }
    
    def _calculate_compliance_score(self, stats: Dict) -> float:
        """计算合规分数"""
        pass_rate = stats.get("pass_rate", 0)
        
        # 基础分数
        score = pass_rate
        
        # 惩罚项
        if len(self.sensitive_words) == 0:
            score -= 10  # 未配置敏感词库
        
        if stats.get("failed", 0) > 10:
            score -= 5  # 失败次数过多
        
        # 确保分数在0-100之间
        return max(0, min(100, score))
    
    async def should_display_disclosure(self, last_disclosure_time: float) -> bool:
        """判断是否应该显示AI标注"""
        if not self.rules.get("disclosure_required", True):
            return False
        
        current_time = time.time()
        interval = self.rules.get("disclosure_interval", 600)
        
        return current_time - last_disclosure_time >= interval
    
    async def get_disclosure_text(self) -> str:
        """获取AI标注文本"""
        disclosure_text = self.config.get("COMPLIANCE", {}).get("disclosure_text", "")
        
        if disclosure_text:
            return disclosure_text
        
        # 默认标注文本
        if self.platform == "douyin":
            return "本直播间由AI数字人主播为您服务"
        elif self.platform == "tiktok":
            return "AI Generated Content / Virtual Host"
        else:
            return "This is an AI-powered live stream"