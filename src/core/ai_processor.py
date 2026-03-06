#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI对话处理器
支持多模型：通义、豆包、DeepSeek、GPT等
"""

import os
import json
import logging
import time
from typing import Dict, List, Optional, Any
import aiohttp
from enum import Enum

logger = logging.getLogger(__name__)


class AIModel(Enum):
    """AI模型枚举"""
    TONGYI = "tongyi"  # 通义千问
    DOUBAO = "doubao"  # 豆包
    DEEPSEEK = "deepseek"  # DeepSeek
    GPT = "gpt"  # OpenAI GPT
    CLAUDE = "claude"  # Anthropic Claude
    VOLCENGINE = "volcengine"  # 火山方舟


class AIProcessor:
    """AI对话处理器"""
    
    def __init__(self, config: Dict):
        """初始化AI处理器
        
        Args:
            config: 配置字典，包含AI相关配置
        """
        self.config = config
        self.model_type = config.get("AI_MODEL", "deepseek").lower()
        self.api_key = config.get("AI_API_KEY")
        self.api_url = config.get("AI_API_URL")
        
        # 模型特定配置
        self.model_configs = {
            "tongyi": {
                "url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                "model": "qwen-max",
                "headers": {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            },
            "doubao": {
                "url": "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
                "model": "Doubao-pro-32k",
                "headers": {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            },
            "deepseek": {
                "url": "https://api.deepseek.com/chat/completions",
                "model": "deepseek-chat",
                "headers": {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            },
            "gpt": {
                "url": "https://api.openai.com/v1/chat/completions",
                "model": "gpt-4o-mini",
                "headers": {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            }
        }
        
        # 会话历史
        self.conversation_history = []
        self.max_history_length = 10
        
        # 商品知识库
        self.product_knowledge = config.get("PRODUCT_KNOWLEDGE", {})
        
        # 带货话术模板
        self.sales_templates = [
            "感谢{user}的提问！{product}这款商品{features}，现在购买还有{offer}优惠哦！",
            "宝宝{user}眼光真好！{product}是我们家的爆款，{benefits}，今天下单立减{discount}！",
            "{user}问得好！{product}确实{advantages}，现在库存只剩{stock}件了，要抓紧哦！",
            "欢迎{user}来到直播间！{product}正在做活动，{promo}，喜欢的宝宝可以下单啦！"
        ]
        
        # 通用回复模板
        self.general_templates = [
            "感谢{user}的支持！有什么问题可以随时问我哦～",
            "欢迎{user}来到直播间！今天给大家带来很多好物，可以看看有没有喜欢的～",
            "{user}你好呀！我是AI主播，有什么想了解的可以问我～",
            "谢谢{user}的关注！直播间正在热卖中，有看中的商品可以告诉我～"
        ]
        
        # 敏感词过滤
        self.sensitive_words = config.get("SENSITIVE_WORDS", [])
        
        logger.info(f"AI处理器初始化完成，使用模型: {self.model_type}")
    
    def _get_model_config(self) -> Dict:
        """获取当前模型的配置"""
        config = self.model_configs.get(self.model_type)
        if not config:
            raise ValueError(f"不支持的模型类型: {self.model_type}")
        
        # 如果配置了自定义URL，使用自定义URL
        if self.api_url:
            config["url"] = self.api_url
        
        return config
    
    def _check_sensitive_content(self, content: str) -> bool:
        """检查是否包含敏感内容"""
        if not self.sensitive_words:
            return False
        
        content_lower = content.lower()
        for word in self.sensitive_words:
            if word.lower() in content_lower:
                logger.warning(f"检测到敏感词: {word}")
                return True
        
        return False
    
    def _extract_product_info(self, content: str) -> Optional[Dict]:
        """从用户提问中提取商品信息"""
        if not self.product_knowledge:
            return None
        
        products = self.product_knowledge.get("products", [])
        
        for product in products:
            product_name = product.get("name", "").lower()
            product_keywords = product.get("keywords", [])
            
            # 检查商品名称
            if product_name and product_name in content.lower():
                return product
            
            # 检查关键词
            for keyword in product_keywords:
                if keyword.lower() in content.lower():
                    return product
        
        return None
    
    def _generate_sales_reply(self, user: str, product: Dict, template_index: int = 0) -> str:
        """生成带货回复"""
        if template_index >= len(self.sales_templates):
            template_index = 0
        
        template = self.sales_templates[template_index]
        
        # 准备替换数据
        replacements = {
            "{user}": user,
            "{product}": product.get("name", "这个商品"),
            "{features}": "、".join(product.get("features", ["品质优良"])[:3]),
            "{benefits}": product.get("description", "非常实用"),
            "{advantages}": product.get("advantages", "性价比很高"),
            "{offer}": product.get("discount", "特别"),
            "{discount}": product.get("discount", "优惠"),
            "{promo}": product.get("promo", "限时特惠"),
            "{stock}": product.get("stock", 100)
        }
        
        # 替换模板中的占位符
        reply = template
        for key, value in replacements.items():
            reply = reply.replace(key, str(value))
        
        return reply
    
    def _generate_general_reply(self, user: str) -> str:
        """生成通用回复"""
        import random
        
        template = random.choice(self.general_templates)
        return template.replace("{user}", user)
    
    def _update_conversation_history(self, role: str, content: str):
        """更新会话历史"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": time.time()
        })
        
        # 保持历史记录长度
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history = self.conversation_history[-self.max_history_length:]
    
    async def generate_reply_simple(self, user_message: str, user_name: str = "用户") -> str:
        """简单模式生成回复（不使用API，快速响应）"""
        
        # 1. 检查敏感内容
        if self._check_sensitive_content(user_message):
            return "感谢您的发言，我们继续介绍商品吧～"
        
        # 2. 提取商品信息
        product_info = self._extract_product_info(user_message)
        
        # 3. 根据是否有商品信息选择回复策略
        if product_info:
            # 带货回复
            import random
            reply = self._generate_sales_reply(user_name, product_info, random.randint(0, 3))
        else:
            # 通用回复
            reply = self._generate_general_reply(user_name)
        
        # 4. 更新会话历史
        self._update_conversation_history("user", f"{user_name}: {user_message}")
        self._update_conversation_history("assistant", reply)
        
        logger.info(f"AI简单回复: {reply[:50]}...")
        return reply
    
    async def generate_reply_ai(self, user_message: str, user_name: str = "用户") -> str:
        """使用AI模型生成回复"""
        
        # 1. 检查敏感内容
        if self._check_sensitive_content(user_message):
            return "感谢您的发言，我们继续介绍商品吧～"
        
        # 2. 准备系统提示
        system_prompt = self._prepare_system_prompt(user_name)
        
        # 3. 准备消息历史
        messages = self._prepare_messages(system_prompt, user_message, user_name)
        
        # 4. 调用AI API
        try:
            reply = await self._call_ai_api(messages)
            
            # 5. 后处理回复
            reply = self._post_process_reply(reply, user_name)
            
            # 6. 更新会话历史
            self._update_conversation_history("user", f"{user_name}: {user_message}")
            self._update_conversation_history("assistant", reply)
            
            logger.info(f"AI模型回复: {reply[:50]}...")
            return reply
            
        except Exception as e:
            logger.error(f"AI模型调用失败: {e}")
            # 降级到简单模式
            return await self.generate_reply_simple(user_message, user_name)
    
    def _prepare_system_prompt(self, user_name: str) -> str:
        """准备系统提示"""
        
        # 基础系统提示
        system_prompt = """你是一个专业的直播带货AI助手，正在抖音/TikTok直播间与观众互动。
        
你的任务：
1. 热情友好地与观众互动
2. 专业地介绍商品特点和优势
3. 促进销售但不强行推销
4. 回答观众关于商品的问题
5. 保持回复简短（不超过50字）
6. 使用直播带货常用话术，如"宝宝"、"亲"、"欢迎"等
        
回复风格：
- 热情活泼，有感染力
- 使用表情符号（适度）
- 突出商品卖点和优惠
- 引导观众互动和下单
        
重要规则：
1. 不讨论政治、敏感话题
2. 不提供医疗、投资建议
3. 不泄露任何隐私信息
4. 不承诺无法保证的效果
"""
        
        # 添加商品知识
        if self.product_knowledge:
            products = self.product_knowledge.get("products", [])
            if products:
                system_prompt += "\n\n当前在售商品：\n"
                for i, product in enumerate(products[:3], 1):  # 只显示前3个商品
                    system_prompt += f"{i}. {product.get('name')} - {product.get('price')} ({product.get('discount', '无折扣')})\n"
                    system_prompt += f"   特点：{', '.join(product.get('features', [])[:3])}\n"
                    system_prompt += f"   促销：{product.get('promo', '无')}\n"
            
            # 添加促销信息
            current_promo = self.product_knowledge.get("current_promo")
            if current_promo:
                system_prompt += f"\n当前促销活动：{current_promo}"
        
        return system_prompt
    
    def _prepare_messages(self, system_prompt: str, user_message: str, user_name: str) -> List[Dict]:
        """准备消息列表"""
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # 添加历史对话
        for item in self.conversation_history[-5:]:  # 只保留最近5条历史
            messages.append({
                "role": item["role"],
                "content": item["content"]
            })
        
        # 添加当前用户消息
        messages.append({
            "role": "user",
            "content": f"观众{user_name}说：{user_message}"
        })
        
        return messages
    
    async def _call_ai_api(self, messages: List[Dict]) -> str:
        """调用AI API"""
        model_config = self._get_model_config()
        
        # 准备请求数据
        request_data = {
            "model": model_config["model"],
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 150,
            "top_p": 0.9,
            "frequency_penalty": 0.2,
            "presence_penalty": 0.1
        }
        
        # 发送请求
        async with aiohttp.ClientSession() as session:
            async with session.post(
                model_config["url"],
                headers=model_config["headers"],
                json=request_data,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API请求失败: {response.status} - {error_text}")
                
                result = await response.json()
                
                # 不同模型的响应格式可能不同
                if self.model_type == "tongyi":
                    reply = result["output"]["text"]
                elif self.model_type == "doubao":
                    reply = result["choices"][0]["message"]["content"]
                elif self.model_type == "deepseek":
                    reply = result["choices"][0]["message"]["content"]
                elif self.model_type == "gpt":
                    reply = result["choices"][0]["message"]["content"]
                else:
                    reply = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                return reply.strip()
    
    def _post_process_reply(self, reply: str, user_name: str) -> str:
        """后处理回复"""
        
        # 1. 确保回复不为空
        if not reply or len(reply.strip()) == 0:
            return self._generate_general_reply(user_name)
        
        # 2. 限制长度
        if len(reply) > 100:
            reply = reply[:97] + "..."
        
        # 3. 添加适当的称呼
        if user_name and user_name != "用户":
            if not reply.startswith(user_name) and f"{user_name}" not in reply:
                # 随机添加称呼
                import random
                greetings = [f"{user_name}宝宝", f"{user_name}亲", f"欢迎{user_name}"]
                if random.random() < 0.3:  # 30%概率添加称呼
                    reply = f"{random.choice(greetings)}，{reply}"
        
        # 4. 确保以标点结尾
        if reply[-1] not in ["。", "！", "？", ".", "!", "?", "~"]:
            reply += "～"
        
        return reply
    
    async def process_message(self, message_data: Dict, use_ai: bool = True) -> Dict:
        """处理消息并生成回复
        
        Args:
            message_data: 消息数据，包含type, nickname, content等
            use_ai: 是否使用AI模型，False则使用简单模式
            
        Returns:
            处理结果字典
        """
        start_time = time.time()
        
        try:
            message_type = message_data.get("type", "")
            nickname = message_data.get("nickname", "用户")
            content = message_data.get("content", "")
            
            # 根据消息类型处理
            if message_type == "chat_message":
                # 弹幕消息，生成回复
                if use_ai and self.api_key:
                    reply = await self.generate_reply_ai(content, nickname)
                else:
                    reply = await self.generate_reply_simple(content, nickname)
                
                result = {
                    "success": True,
                    "type": "reply",
                    "original_message": content,
                    "reply": reply,
                    "user": nickname,
                    "timestamp": time.time()
                }
                
            elif message_type == "gift_message":
                # 礼物消息，感谢回复
                gift_name = message_data.get("gift_name", "礼物")
                gift_count = message_data.get("gift_count", 1)
                
                if gift_count > 1:
                    reply = f"感谢{nickname}送的{gift_name} x{gift_count}！太给力了！"
                else:
                    reply = f"谢谢{nickname}送的{gift_name}！爱你哟～"
                
                result = {
                    "success": True,
                    "type": "gift_thanks",
                    "reply": reply,
                    "user": nickname,
                    "gift": gift_name,
                    "count": gift_count,
                    "timestamp": time.time()
                }
                
            elif message_type == "like_message":
                # 点赞消息，简单感谢
                like_count = message_data.get("like_count", 1)
                
                if like_count > 10:
                    reply = f"感谢{nickname}的疯狂点赞！"
                else:
                    reply = f"谢谢{nickname}的点赞支持！"
                
                result = {
                    "success": True,
                    "type": "like_thanks",
                    "reply": reply,
                    "user": nickname,
                    "count": like_count,
                    "timestamp": time.time()
                }
                
            else:
                # 其他类型消息
                result = {
                    "success": True,
                    "type": "acknowledge",
                    "message": f"收到{nickname}的{message_type}消息",
                    "timestamp": time.time()
                }
            
            # 计算处理时间
            processing_time = time.time() - start_time
            result["processing_time_ms"] = round(processing_time * 1000, 2)
            
            logger.info(f"消息处理完成: {message_type}, 耗时: {result['processing_time_ms']}ms")
            return result
            
        except Exception as e:
            logger.error(f"处理消息失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": time.time()
            }


# 使用示例