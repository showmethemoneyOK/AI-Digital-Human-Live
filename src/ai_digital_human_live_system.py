#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI数字人直播系统 - 完整集成版本
集成内容过滤、Prompt管理、商品知识库等所有模块
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any

# 添加src目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from content_filter import ContentFilter, FilterResult, ContentRiskLevel
from prompt_manager import PromptManager, ProductInfo

class AIDigitalHumanLiveSystem:
    """AI数字人直播系统 - 完整版"""
    
    def __init__(self, config_path: str = "config/config.json"):
        self.config_path = config_path
        self.config = self.load_config()
        
        # 初始化各模块
        self.content_filter = ContentFilter()
        self.prompt_manager = PromptManager()
        
        # 系统状态
        self.is_running = False
        self.interaction_count = 0
        self.start_time = None
        
        # 会话上下文
        self.session_context = {
            "current_product": None,
            "current_promo": "",
            "recent_interactions": [],
            "user_preferences": {}
        }
    
    def load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "platform": "tiktok",
            "api_keys": {
                "openai": "",
                "elevenlabs": "",
                "d_id": "",
                "tikhub": ""
            },
            "content_filter": {
                "enabled": True,
                "strict_mode": True,
                "auto_block_high_risk": True
            },
            "prompt_settings": {
                "default_template": "tiktok_sales_host",
                "language": "en-US",
                "response_style": "concise",
                "emoji_enabled": True
            },
            "compliance": {
                "ai_disclosure_required": True,
                "disclosure_interval": 600,
                "risk_warnings_enabled": True
            }
        }
    
    async def process_danmaku(self, danmaku: Dict) -> Optional[Dict]:
        """处理弹幕消息"""
        try:
            # 1. 提取弹幕内容
            content = danmaku.get("content", "").strip()
            user_id = danmaku.get("user_id", "unknown")
            
            if not content:
                return None
            
            print(f"[{datetime.now()}] 收到弹幕 [{user_id}]: {content}")
            
            # 2. 内容安全过滤
            filter_result = self.content_filter.filter_text(
                content, 
                context={"platform": self.config["platform"]}
            )
            
            if not filter_result.passed:
                print(f"内容过滤未通过: {filter_result.blocked_reasons}")
                return await self.handle_blocked_content(filter_result, user_id)
            
            # 3. 构建Prompt上下文
            prompt_context = self.build_prompt_context(content, danmaku)
            
            # 4. 生成AI回复
            ai_response = await self.generate_ai_response(
                content, 
                prompt_context,
                filtered_text=filter_result.filtered_text
            )
            
            # 5. 回复内容过滤
            response_filter_result = self.content_filter.filter_text(
                ai_response,
                context={"platform": self.config["platform"]}
            )
            
            if not response_filter_result.passed:
                print(f"回复内容过滤未通过，使用降级回复")
                ai_response = self.get_fallback_response()
            
            # 6. 记录交互
            self.record_interaction(
                user_id=user_id,
                original_content=content,
                filtered_content=filter_result.filtered_text,
                ai_response=ai_response,
                filter_result=filter_result
            )
            
            return {
                "user_id": user_id,
                "original_content": content,
                "filtered_content": filter_result.filtered_text,
                "ai_response": ai_response,
                "should_respond": True,
                "response_priority": self.calculate_response_priority(danmaku)
            }
            
        except Exception as e:
            print(f"处理弹幕异常: {e}")
            return None
    
    def build_prompt_context(self, content: str, danmaku: Dict) -> Dict:
        """构建Prompt上下文"""
        platform = self.config["platform"]
        
        # 获取当前商品信息
        current_product = self.session_context.get("current_product")
        product_info = ""
        
        if current_product and current_product in self.prompt_manager.products:
            product = self.prompt_manager.products[current_product]
            product_info = self.format_product_info(product)
        
        # 构建上下文
        context = {
            "platform": platform,
            "user_id": danmaku.get("user_id", "unknown"),
            "user_level": danmaku.get("user_level", "new"),
            "is_gift_user": danmaku.get("has_sent_gift", False),
            "current_time": datetime.now().strftime("%H:%M"),
            "product_info": product_info,
            "current_promo": self.session_context.get("current_promo", ""),
            "recent_interactions": self.session_context["recent_interactions"][-5:],  # 最近5条
            "language": self.detect_language(content)
        }
        
        # 添加商品相关变量
        if current_product and current_product in self.prompt_manager.products:
            product = self.prompt_manager.products[current_product]
            context.update({
                "product_name": product.name,
                "product_price": product.price,
                "product_features": product.features,
                "product_discount": product.discount,
                "product_promo": product.promo
            })
        
        return context
    
    def format_product_info(self, product: ProductInfo) -> str:
        """格式化商品信息"""
        info_lines = []
        
        info_lines.append(f"产品名称: {product.name}")
        info_lines.append(f"产品类别: {product.category}")
        info_lines.append(f"价格: {product.price}")
        
        if product.original_price:
            info_lines.append(f"原价: {product.original_price}")
        
        if product.discount:
            info_lines.append(f"折扣: {product.discount}")
        
        if product.promo:
            info_lines.append(f"促销: {product.promo}")
        
        if product.features:
            info_lines.append("主要功能:")
            for feature in product.features[:5]:  # 最多5个功能
                info_lines.append(f"  - {feature}")
        
        if product.description:
            info_lines.append(f"产品描述: {product.description}")
        
        return "\n".join(info_lines)
    
    def detect_language(self, text: str) -> str:
        """检测语言"""
        # 简单的语言检测
        if any(char in text for char in ['¿', '¡', 'á', 'é', 'í', 'ó', 'ú']):
            return "es-ES"  # 西班牙语
        elif any(char in text for char in ['ã', 'õ', 'ç', 'â', 'ê', 'ô']):
            return "pt-PT"  # 葡萄牙语
        elif any(0x4E00 <= ord(char) <= 0x9FFF for char in text):
            return "zh-CN"  # 中文
        else:
            return "en-US"  # 默认英语
    
    async def generate_ai_response(self, user_message: str, context: Dict, filtered_text: str = "") -> str:
        """生成AI回复"""
        # 这里应该调用实际的LLM API
        # 暂时返回模拟回复
        
        platform = context["platform"]
        language = context.get("language", "en-US")
        
        if platform == "douyin":
            # 抖音回复模板
            templates = [
                f"本直播间由AI数字人主播为您服务。{filtered_text}的相关问题，这款产品现在优惠中，点击小黄车查看详情！",
                f"本直播间由AI数字人主播为您服务。感谢您的提问！{filtered_text}的问题，产品详情请查看商品页面。"
            ]
        else:
            # TikTok回复模板
            if language == "es-ES":
                templates = [
                    f"¡Gracias por tu pregunta sobre {filtered_text}! El producto está en oferta hoy. ¡Haz clic en el enlace para comprar! 🚀",
                    f"Excelente pregunta sobre {filtered_text}! Tenemos una promoción especial hoy. ¡No te la pierdas! 🎉"
                ]
            elif language == "pt-PT":
                templates = [
                    f"Obrigado pela sua pergunta sobre {filtered_text}! O produto está em promoção hoje. Clique no link para comprar! 🚀",
                    f"Ótima pergunta sobre {filtered_text}! Temos uma promoção especial hoje. Não perca! 🎉"
                ]
            else:
                templates = [
                    f"Thanks for your question about {filtered_text}! The product is on sale today. Click the link to buy! 🚀",
                    f"Great question about {filtered_text}! We have a special promotion today. Don't miss out! 🎉"
                ]
        
        import random
        return random.choice(templates)
    
    async def handle_blocked_content(self, filter_result: FilterResult, user_id: str) -> Optional[Dict]:
        """处理被拦截的内容"""
        if filter_result.risk_level == ContentRiskLevel.BLOCKED:
            # 高风险内容，不回复
            print(f"高风险内容被拦截，用户: {user_id}, 原因: {filter_result.blocked_reasons}")
            return None
        elif filter_result.risk_level == ContentRiskLevel.HIGH_RISK:
            # 高风险内容，返回通用回复
            return {
                "user_id": user_id,
                "original_content": "[内容被过滤]",
                "filtered_content": "[内容被过滤]",
                "ai_response": self.get_safe_response(),
                "should_respond": True,
                "response_priority": 0  # 低优先级
            }
        else:
            # 中低风险，可以回复但需要谨慎
            return {
                "user_id": user_id,
                "original_content": filter_result.filtered_text,
                "filtered_content": filter_result.filtered_text,
                "ai_response": self.get_cautious_response(filter_result),
                "should_respond": True,
                "response_priority": 1
            }
    
    def get_safe_response(self) -> str:
        """获取安全回复"""
        platform = self.config["platform"]
        
        if platform == "douyin":
            return "本直播间由AI数字人主播为您服务。感谢您的关注，请查看商品详情了解更多信息。"
        else:
            return "Thanks for your message! Please check the product details for more information. 🛍️"
    
    def get_cautious_response(self, filter_result: FilterResult) -> str:
        """获取谨慎回复"""
        platform = self.config["platform"]
        
        if platform == "douyin":
            response = "本直播间由AI数字人主播为您服务。"
            if filter_result.warning_reasons:
                response += "请注意发言内容符合社区规范。"
            response += "请问有什么商品相关问题吗？"
            return response
        else:
            response = "I'm here to help with product questions. "
            if filter_result.warning_reasons:
                response += "Please keep the conversation appropriate. "
            response += "How can I assist you with our products today?"
            return response
    
    def get_fallback_response(self) -> str:
        """获取降级回复"""
        platform = self.config["platform"]
        
        if platform == "douyin":
            return "本直播间由AI数字人主播为您服务。系统正在处理您的请求，请稍候或查看商品详情页。"
        else:
            return "I'm processing your request. Please wait or check the product page for details. ⏳"
    
    def calculate_response_priority(self, danmaku: Dict) -> int:
        """计算回复优先级"""
        priority = 1  # 默认优先级
        
        # 礼物用户优先级高
        if danmaku.get("has_sent_gift", False):
            priority += 3
        
        # 高级用户优先级较高
        user_level = danmaku.get("user_level", "new")
        if user_level == "vip":
            priority += 2
        elif user_level == "regular":
            priority += 1
        
        # 问题类型优先级
        content = danmaku.get("content", "").lower()
        high_priority_keywords = ["价格", "多少钱", "price", "cost", "how much"]
        medium_priority_keywords = ["功能", "怎么用", "feature", "how to use"]
        
        if any(keyword in content for keyword in high_priority_keywords):
            priority += 2
        elif any(keyword in content for keyword in medium_priority_keywords):
            priority += 1
        
        return min(priority, 5)  # 最大优先级为5
    
    def record_interaction(self, user_id: str, original_content: str, 
                          filtered_content: str, ai_response: str, 
                          filter_result: FilterResult):
        """记录交互"""
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "original_content": original_content,
            "filtered_content": filtered_content,
            "ai_response": ai_response,
            "risk_level": filter_result.risk_level.value,
            "blocked_reasons": filter_result.blocked_reasons,
            "warning_reasons": filter_result.warning_reasons
        }
        
        # 添加到最近交互记录
        self.session_context["recent_interactions"].append(interaction)
        
        # 保持最近交互记录不超过50条
        if len(self.session_context["recent_interactions"]) > 50:
            self.session_context["recent_interactions"] = self.session_context["recent_interactions"][-50:]
        
        # 更新交互计数
        self.interaction_count += 1
        
        # 保存到日志文件
        self.save_interaction_log(interaction)
    
    def save_interaction_log(self, interaction: Dict):
        """保存交互日志"""
        log_dir = "logs/interactions"
        os.makedirs(log_dir, exist_ok=True)
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(log_dir, f"interactions_{date_str}.json")
        
        try:
            # 读取现有日志
            existing_logs = []
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            existing_logs.append(json.loads(line))
            
            # 添加新日志
            existing_logs.append(interaction)
            
            # 写入文件
            with open(log_file, 'w', encoding='utf-8') as f:
                for entry in existing_logs:
                    f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        except Exception as e:
            print(f"保存交互日志失败: {e}")
    
    async def run_keepalive_tasks(self):
        """运行保持活跃的任务"""
        while self.is_running:
            try:
                # 定期发送保持活跃的消息
                await self.send_keepalive_message()
                
                # 定期更新促销信息
                await self.update_promotion_info()
                
                # 定期检查系统健康
                await self.check_system_health()
                
                # 等待一段时间
                await asyncio.sleep(300)  # 5分钟
                
            except Exception as e:
                print(f"保持活跃任务异常: {e}")
                await asyncio.sleep(60)  # 异常后等待1分钟
    
    async def send_keepalive_message(self):
        """发送保持活跃的消息"""
        platform = self.config["platform"]
        
        if platform == "douyin":
            messages = [
                "本直播间由AI数字人主播为您服务，24小时在线解答！",
                "AI主播持续为您服务中，有任何商品问题请随时提问！",
                "感谢大家观看，记得点击下方小黄车查看热门商品！"
            ]
        else:
            messages = [
                "AI Digital Host is here 24/7! Ask me anything! 🤖",
                "Don't forget to check out today's special deals! 🎁",
                "Thanks for watching! Click the link to see our products! 🛍️"
            ]
        
        import random
        message = random.choice(messages)
        
        # 这里应该触发数字人生成和推流
        print(f"[Keepalive] {message}")
    
    async def update_promotion_info(self):
        """更新促销信息"""
        # 这里可以轮询数据库或API获取最新促销信息
        # 暂时使用模拟数据
        
        if self.session_context.get("current_product"):
            # 更新当前商品的促销信息
            pass
    
    async def check_system_health(self):
        """检查系统健康"""
        # 检查各模块状态
        health_status = {
            "content_filter": True,
            "prompt_manager": True,
            "api_connections": True,
            "system_resources": self.check_system_resources()
        }
        
        # 如果有问题，记录日志
        if not all(health_status.values()):
            print(f"系统健康检查异常: {health_status}")
    
    def check_system_resources(self) -> bool:
        """检查系统资源"""
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            
            if cpu_percent > 90 or memory_percent > 90:
                return False
            
            return True
        except ImportError:
            #