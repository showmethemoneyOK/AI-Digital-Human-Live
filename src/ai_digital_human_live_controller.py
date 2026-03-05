#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI数字人直播主控脚本 (抖音/TikTok通用)
版本: 2.0.0
作者: AI Digital Human Live System
描述: 支持双平台的AI数字人实时互动带货直播系统
"""

import asyncio
import json
import requests
import time
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

# ===================== 配置项 =====================

@dataclass
class PlatformConfig:
    """平台配置基类"""
    platform: str  # "douyin" 或 "tiktok"
    room_id: str
    user_unique_id: str
    stream_url: str
    stream_key: str
    
@dataclass
class LLMConfig:
    """LLM配置"""
    api_key: str
    api_url: str
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 200
    
@dataclass
class TTSConfig:
    """TTS配置"""
    api_key: str
    api_url: str
    voice_id: str
    language: str = "zh-CN"  # 或 "en-US", "es-ES" 等
    
@dataclass
class DigitalHumanConfig:
    """数字人配置"""
    api_key: str
    api_url: str
    avatar_id: str
    render_mode: str = "cloud"  # cloud 或 local
    
@dataclass
class SystemConfig:
    """系统配置"""
    platform_config: PlatformConfig
    llm_config: LLMConfig
    tts_config: TTSConfig
    digital_human_config: DigitalHumanConfig
    log_level: str = "INFO"
    max_retries: int = 3
    timeout: int = 30

# ===================== 1. 弹幕监听模块 =====================

class DanmakuListener:
    """弹幕监听基类"""
    
    def __init__(self, config: PlatformConfig):
        self.config = config
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        
    async def fetch_danmaku(self) -> List[Dict]:
        """获取弹幕（子类必须实现）"""
        raise NotImplementedError
        
    def clean_comment(self, comment: Dict) -> Dict:
        """清洗弹幕内容"""
        cleaned = comment.copy()
        # 移除特殊字符
        cleaned["content"] = self.remove_special_chars(comment.get("content", ""))
        # 过滤敏感词
        cleaned["content"] = self.filter_sensitive_words(cleaned["content"])
        return cleaned
    
    @staticmethod
    def remove_special_chars(text: str) -> str:
        """移除特殊字符"""
        import re
        # 保留中文、英文、数字、常用标点
        return re.sub(r'[^\w\u4e00-\u9fff\s.,!?;:\'\"-]', '', text)
    
    @staticmethod
    def filter_sensitive_words(text: str) -> str:
        """过滤敏感词（基础实现）"""
        sensitive_words = ["政治敏感词1", "政治敏感词2"]  # 实际使用时需要完整的敏感词库
        for word in sensitive_words:
            if word in text:
                text = text.replace(word, "***")
        return text

class TikTokDanmakuListener(DanmakuListener):
    """TikTok弹幕监听器"""
    
    def __init__(self, config: PlatformConfig, api_key: str):
        super().__init__(config)
        self.api_key = api_key
        self.base_url = "https://api.tikhub.io/api/v1/tiktok/web/fetch_live_im_fetch"
        
    async def fetch_danmaku(self) -> List[Dict]:
        """获取TikTok直播间弹幕"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        params = {
            "room_id": self.config.room_id,
            "limit": 50,
            "cursor": 0
        }
        
        try:
            response = requests.get(
                self.base_url,
                headers=headers,
                params=params,
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                comments = data.get("comments", [])
                
                # 清洗弹幕
                cleaned_comments = [self.clean_comment(comment) for comment in comments]
                return cleaned_comments
            else:
                self.logger.error(f"TikTok API请求失败: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"获取TikTok弹幕异常: {e}")
            return []

class DouyinDanmakuListener(DanmakuListener):
    """抖音弹幕监听器（官方接口）"""
    
    def __init__(self, config: PlatformConfig, app_key: str, app_secret: str):
        super().__init__(config)
        self.app_key = app_key
        self.app_secret = app_secret
        self.base_url = "https://open.douyin.com"
        self.access_token = None
        
    async def get_access_token(self) -> str:
        """获取抖音开放平台Access Token"""
        if self.access_token and not self.is_token_expired():
            return self.access_token
            
        url = f"{self.base_url}/oauth/access_token/"
        params = {
            "client_key": self.app_key,
            "client_secret": self.app_secret,
            "grant_type": "client_credential"
        }
        
        try:
            response = requests.post(url, params=params)
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                self.token_expires_at = time.time() + data.get("expires_in", 7200) - 300
                return self.access_token
        except Exception as e:
            self.logger.error(f"获取抖音Access Token失败: {e}")
            
        return ""
    
    def is_token_expired(self) -> bool:
        """检查Token是否过期"""
        return not hasattr(self, 'token_expires_at') or time.time() >= self.token_expires_at
    
    async def fetch_danmaku(self) -> List[Dict]:
        """获取抖音直播间弹幕（官方接口）"""
        access_token = await self.get_access_token()
        if not access_token:
            return []
        
        url = f"{self.base_url}/api/live/data/room/comment/list/"
        headers = {
            "access-token": access_token,
            "Content-Type": "application/json"
        }
        
        data = {
            "room_id": self.config.room_id,
            "cursor": 0,
            "count": 50
        }
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=self.config.timeout)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("data"):
                    comments = result["data"].get("comments", [])
                    
                    # 抖音合规要求：必须标注AI身份
                    for comment in comments:
                        comment["is_ai_host"] = True
                    
                    # 清洗弹幕
                    cleaned_comments = [self.clean_comment(comment) for comment in comments]
                    return cleaned_comments
            else:
                self.logger.error(f"抖音API请求失败: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"获取抖音弹幕异常: {e}")
            
        return []

# ===================== 2. AI问答模块 =====================

class AILiveHost:
    """AI直播主播"""
    
    def __init__(self, config: LLMConfig, product_knowledge: Dict = None):
        self.config = config
        self.product_knowledge = product_knowledge or self.default_product_knowledge()
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def default_product_knowledge(self) -> Dict:
        """默认商品知识库"""
        return {
            "products": [
                {
                    "name": "无线蓝牙耳机 Pro",
                    "features": ["主动降噪", "30小时续航", "IPX5防水"],
                    "price": "¥599",
                    "promo": "今日限时买一送一！"
                },
                {
                    "name": "智能手表 X1",
                    "features": ["健康监测", "GPS定位", "NFC支付"],
                    "price": "¥1299",
                    "promo": "前100名送原装表带"
                }
            ],
            "current_promo": "全场满300减50，新人专享券",
            "shipping_info": "全国包邮，24小时内发货",
            "return_policy": "7天无理由退换货"
        }
    
    def build_system_prompt(self, platform: str = "tiktok") -> str:
        """构建系统提示词"""
        if platform == "douyin":
            return self.build_douyin_system_prompt()
        else:
            return self.build_tiktok_system_prompt()
    
    def build_tiktok_system_prompt(self) -> str:
        """TikTok系统提示词"""
        return f"""You are a professional TikTok live-streaming host. Your characteristics:
1. Energetic, enthusiastic, and persuasive
2. Speak in short, engaging sentences (max 2 sentences per response)
3. Focus on product benefits and features
4. Use emojis occasionally to make responses lively 🎉
5. Always end with a call-to-action (e.g., "Click the link below!", "Limited time offer!")
6. Handle objections professionally
7. Stay within TikTok community guidelines

Product knowledge:
{json.dumps(self.product_knowledge, ensure_ascii=False, indent=2)}

Current promotion: {self.product_knowledge.get('current_promo', 'Special discount today!')}

Remember: Keep responses natural, conversational, and sales-oriented."""
    
    def build_douyin_system_prompt(self) -> str:
        """抖音系统提示词（强合规）"""
        return f"""你是抖音直播间的AI数字人主播，必须严格遵守以下规定：

【身份声明】每次回复前必须说明"本直播间由AI数字人主播为您服务"
【内容合规】绝不涉及政治、色情、暴力、谣言等内容
【商品描述】真实准确，不夸大宣传，不虚假承诺
【价格说明】明确标注价格，不误导消费者
【风险提示】对特殊商品进行必要提示
【互动规范】文明用语，不攻击、不贬低他人
【广告标识】明确说明"广告"性质

商品信息：
{json.dumps(self.product_knowledge, ensure_ascii=False, indent=2)}

当前活动：{self.product_knowledge.get('current_promo', '限时优惠中')}

回复要求：
- 简洁明了，不超过2句话
- 热情亲切，有感染力
- 包含行动号召
- 必须标注AI身份
- 符合抖音社区规范"""
    
    async def generate_response(self, question: str, platform: str = "tiktok") -> str:
        """生成AI回复"""
        system_prompt = self.build_system_prompt(platform)
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens
        }
        
        # 平台特定配置
        if platform == "douyin":
            # 抖音需要更严格的合规控制
            payload["temperature"] = 0.6
            payload["top_p"] = 0.8
            # 添加安全设置（如果API支持）
            if "volces.com" in self.config.api_url:  # 火山方舟
                payload["safety_settings"] = {
                    "violence": "BLOCK_MEDIUM_AND_ABOVE",
                    "sexual": "BLOCK_MEDIUM_AND_ABOVE",
                    "political": "BLOCK_MEDIUM_AND_ABOVE"
                }
        
        for retry in range(self.config.max_retries):
            try:
                response = requests.post(
                    self.config.api_url,
                    json=payload,
                    headers=headers,
                    timeout=self.config.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    answer = result["choices"][0]["message"]["content"]
                    
                    # 后处理
                    answer = self.post_process_answer(answer, platform)
                    
                    self.logger.info(f"AI回复生成成功: {answer[:50]}...")
                    return answer
                else:
                    self.logger.warning(f"LLM API请求失败 (尝试 {retry+1}/{self.config.max_retries}): {response.status_code}")
                    
            except Exception as e:
                self.logger.error(f"生成AI回复异常 (尝试 {retry+1}/{self.config.max_retries}): {e}")
            
            if retry < self.config.max_retries - 1:
                await asyncio.sleep(2 ** retry)  # 指数退避
        
        # 所有重试都失败，返回默认回复
        return self.get_fallback_response(platform)
    
    def post_process_answer(self, answer: str, platform: str) -> str:
        """后处理AI回复"""
        # 移除多余的空格和换行
        answer = ' '.join(answer.split())
        
        if platform == "douyin":
            # 抖音必须标注AI身份
            if "本直播间由AI数字人主播为您服务" not in answer:
                answer = f"本直播间由AI数字人主播为您服务。{answer}"
        
        return answer
    
    def get_fallback_response(self, platform: str) -> str:
        """获取降级回复"""
        if platform == "douyin":
            return "本直播间由AI数字人主播为您服务。感谢您的提问，请查看商品详情了解更多信息。"
        else:
            return "Thanks for your question! Please check the product details for more information. 🛍️"

# ===================== 3. TTS语音合成模块 =====================

class TTSService:
    """TTS语音合成服务"""
    
    def __init__(self, config: TTSConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def text_to_speech(self, text: str, output_path: str = None) -> Optional[str]:
        """文本转语音"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"temp/audio_{timestamp}.mp3"
        
        # 确保目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 根据API URL判断服务提供商
        if "elevenlabs.io" in self.config.api_url:
            return await self.elevenlabs_tts(text, output_path)
        elif "aliyuncs.com" in self.config.api_url:
            return await self.aliyun_tts(text, output_path)
        elif "xfyun.cn" in self.config.api_url:
            return await self.xunfei_tts(text, output_path)
        else:
            self.logger.error(f"不支持的TTS服务: {self.config.api_url}")
            return None
    
    async def elevenlabs_tts(self, text: str, output_path: str) -> Optional[str]:
        """ElevenLabs TTS"""
        url = f"{self.config.api_url}/{self.config.voice_id}"
        
        headers = {
            "xi-api-key": self.config.api_key,
            "Content-Type": "application/json"
        }
        
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.3,
                "use_speaker_boost": True
            }
        }
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=self.config.timeout)
            
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                self.logger.info(f"ElevenLabs TTS成功: {output_path}")
                return output_path
            else:
                self.logger.error(f"ElevenLabs TTS失败: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"ElevenLabs TTS异常: {e}")
            
        return None
    
    async def aliyun_tts(self, text: str, output_path: str) -> Optional[str]:
        """阿里云TTS"""
        # 简化实现，实际需要阿里云SDK
        try:
            # 这里应该是阿里云TTS的实际调用
            # 由于阿里云需要SDK，这里用模拟实现
            self.logger.warning("阿里云TTS需要安装aliyun-python-sdk-core，这里使用模拟实现")
            
            # 模拟生成音频文件（实际应该调用阿里云API）
            with open(output_path, "wb") as f:
                # 这里应该写入实际的音频数据
                # 暂时写入一个空的MP3头
                f.write(b'')  # 实际使用时需要替换为真实音频数据
            
            self.logger.info(f"阿里云TTS模拟成功: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"阿里云TTS异常: {e}")
            return None
    
    async def xunfei_tts(self, text: str, output_path: str) -> Optional[str]:
        """讯飞TTS"""
        # 讯飞TTS