#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API客户端模块
包含所有外部API的客户端实现
"""

import asyncio
import aiohttp
import requests
import json
import time
import hashlib
import hmac
import base64
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class APIProvider(Enum):
    """API提供商"""
    OPENAI = "openai"
    CLAUDE = "claude"
    VOLCENGINE = "volcengine"  # 火山方舟
    ALIBABA = "alibaba"  # 阿里通义
    ELEVENLABS = "elevenlabs"
    ALIYUN_TTS = "aliyun_tts"
    XUNFEI_TTS = "xunfei_tts"
    DID = "d_id"
    HEYGEN = "heygen"
    GUIJI_AI = "guiji_ai"  # 硅基智能
    TIKHUB = "tikhub"
    DOUYIN = "douyin"

@dataclass
class APIResponse:
    """API响应"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    status_code: int = 200
    latency_ms: float = 0.0

class BaseAPIClient:
    """API客户端基类"""
    
    def __init__(self, api_key: str, api_url: str, timeout: int = 30):
        self.api_key = api_key
        self.api_url = api_url
        self.timeout = timeout
        self.session = None
        self.request_count = 0
        self.error_count = 0
        
    async def _ensure_session(self):
        """确保会话存在"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
    
    async def close(self):
        """关闭会话"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Content-Type": "application/json",
            "User-Agent": "AI-Digital-Human-Live/2.0.0"
        }
    
    async def _make_request(self, method: str, endpoint: str, 
                           data: Optional[Dict] = None, 
                           params: Optional[Dict] = None) -> APIResponse:
        """发送请求"""
        start_time = time.time()
        self.request_count += 1
        
        try:
            await self._ensure_session()
            
            url = f"{self.api_url.rstrip('/')}/{endpoint.lstrip('/')}"
            
            async with self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=self._get_headers()
            ) as response:
                
                latency_ms = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    response_data = await response.json()
                    return APIResponse(
                        success=True,
                        data=response_data,
                        status_code=response.status,
                        latency_ms=latency_ms
                    )
                else:
                    error_text = await response.text()
                    logger.error(f"API请求失败: {response.status} - {error_text}")
                    self.error_count += 1
                    
                    return APIResponse(
                        success=False,
                        error=f"HTTP {response.status}: {error_text[:200]}",
                        status_code=response.status,
                        latency_ms=latency_ms
                    )
                    
        except asyncio.TimeoutError:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"API请求超时: {endpoint}")
            self.error_count += 1
            
            return APIResponse(
                success=False,
                error="请求超时",
                status_code=408,
                latency_ms=latency_ms
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"API请求异常: {e}")
            self.error_count += 1
            
            return APIResponse(
                success=False,
                error=str(e),
                status_code=500,
                latency_ms=latency_ms
            )

class LLMClient(BaseAPIClient):
    """LLM API客户端"""
    
    def __init__(self, provider: APIProvider, api_key: str, api_url: str, 
                 model: str = "gpt-3.5-turbo", **kwargs):
        super().__init__(api_key, api_url, kwargs.get("timeout", 30))
        self.provider = provider
        self.model = model
        self.temperature = kwargs.get("temperature", 0.7)
        self.max_tokens = kwargs.get("max_tokens", 200)
        
    def _get_headers(self) -> Dict[str, str]:
        """获取LLM请求头"""
        headers = super()._get_headers()
        
        if self.provider == APIProvider.OPENAI:
            headers["Authorization"] = f"Bearer {self.api_key}"
        elif self.provider == APIProvider.CLAUDE:
            headers["x-api-key"] = self.api_key
            headers["anthropic-version"] = "2023-06-01"
        elif self.provider == APIProvider.VOLCENGINE:
            headers["Authorization"] = f"Bearer {self.api_key}"
        elif self.provider == APIProvider.ALIBABA:
            # 阿里云需要特殊签名
            pass
            
        return headers
    
    async def generate_chat_completion(self, messages: List[Dict], 
                                      **kwargs) -> APIResponse:
        """生成聊天补全"""
        
        if self.provider == APIProvider.OPENAI:
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "stream": False
            }
            return await self._make_request("POST", "chat/completions", data)
            
        elif self.provider == APIProvider.CLAUDE:
            data = {
                "model": self.model,
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "temperature": kwargs.get("temperature", self.temperature)
            }
            return await self._make_request("POST", "v1/messages", data)
            
        elif self.provider == APIProvider.VOLCENGINE:
            data = {
                "model": self.model,
                "messages": messages,
                "parameters": {
                    "temperature": kwargs.get("temperature", self.temperature),
                    "max_tokens": kwargs.get("max_tokens", self.max_tokens)
                }
            }
            return await self._make_request("POST", "api/v1/chat/completions", data)
            
        else:
            return APIResponse(
                success=False,
                error=f"不支持的LLM提供商: {self.provider}"
            )
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """生成文本（简化接口）"""
        messages = [{"role": "user", "content": prompt}]
        response = await self.generate_chat_completion(messages, **kwargs)
        
        if response.success:
            if self.provider == APIProvider.OPENAI:
                return response.data["choices"][0]["message"]["content"]
            elif self.provider == APIProvider.CLAUDE:
                return response.data["content"][0]["text"]
            elif self.provider == APIProvider.VOLCENGINE:
                return response.data["choices"][0]["message"]["content"]
        
        return f"[LLM错误] {response.error}"

class TTSClient(BaseAPIClient):
    """TTS API客户端"""
    
    def __init__(self, provider: APIProvider, api_key: str, api_url: str, 
                 voice_id: str, **kwargs):
        super().__init__(api_key, api_url, kwargs.get("timeout", 30))
        self.provider = provider
        self.voice_id = voice_id
        self.language = kwargs.get("language", "zh-CN")
        
    def _get_headers(self) -> Dict[str, str]:
        """获取TTS请求头"""
        headers = super()._get_headers()
        
        if self.provider == APIProvider.ELEVENLABS:
            headers["xi-api-key"] = self.api_key
            headers["Content-Type"] = "application/json"
        elif self.provider == APIProvider.ALIYUN_TTS:
            # 阿里云需要特殊签名
            pass
            
        return headers
    
    async def generate_speech(self, text: str, **kwargs) -> Optional[bytes]:
        """生成语音"""
        
        if self.provider == APIProvider.ELEVENLABS:
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": kwargs.get("stability", 0.5),
                    "similarity_boost": kwargs.get("similarity_boost", 0.75)
                }
            }
            
            endpoint = f"text-to-speech/{self.voice_id}"
            response = await self._make_request("POST", endpoint, data)
            
            if response.success:
                # ElevenLabs返回音频数据
                return response.data
            else:
                logger.error(f"TTS生成失败: {response.error}")
                return None
                
        elif self.provider == APIProvider.ALIYUN_TTS:
            # 阿里云TTS实现
            return await self._generate_aliyun_tts(text, **kwargs)
            
        else:
            logger.error(f"不支持的TTS提供商: {self.provider}")
            return None
    
    async def _generate_aliyun_tts(self, text: str, **kwargs) -> Optional[bytes]:
        """生成阿里云TTS"""
        # 这里实现阿里云TTS的具体逻辑
        # 需要处理签名和认证
        pass

class DigitalHumanClient(BaseAPIClient):
    """数字人API客户端"""
    
    def __init__(self, provider: APIProvider, api_key: str, api_url: str, 
                 avatar_id: str, **kwargs):
        super().__init__(api_key, api_url, kwargs.get("timeout", 60))
        self.provider = provider
        self.avatar_id = avatar_id
        self.driver_id = kwargs.get("driver_id", "")
        
    def _get_headers(self) -> Dict[str, str]:
        """获取数字人请求头"""
        headers = super()._get_headers()
        
        if self.provider == APIProvider.DID:
            headers["Authorization"] = f"Basic {self.api_key}"
        elif self.provider == APIProvider.HEYGEN:
            headers["X-Api-Key"] = self.api_key
            
        return headers
    
    async def create_talk(self, script: str, audio_url: Optional[str] = None, 
                         **kwargs) -> Optional[str]:
        """创建数字人讲话视频"""
        
        if self.provider == APIProvider.DID:
            data = {
                "script": {
                    "type": "text",
                    "input": script,
                    "provider": {
                        "type": "elevenlabs",
                        "voice_id": kwargs.get("voice_id", "21m00Tcm4TlvDq8ikWAM")
                    }
                },
                "config": {
                    "result_format": "mp4",
                    "fluent": True
                },
                "source_url": f"https://api.d-id.com/avatars/{self.avatar_id}"
            }
            
            response = await self._make_request("POST", "talks", data)
            
            if response.success:
                talk_id = response.data.get("id")
                return talk_id
            else:
                logger.error(f"创建数字人讲话失败: {response.error}")
                return None
                
        elif self.provider == APIProvider.HEYGEN:
            # HeyGen实现
            pass
            
        elif self.provider == APIProvider.GUIJI_AI:
            # 硅基智能实现
            pass
            
        return None
    
    async def get_talk_status(self, talk_id: str) -> Optional[Dict]:
        """获取讲话状态"""
        response = await self._make_request("GET", f"talks/{talk_id}")
        
        if response.success:
            return response.data
        else:
            logger.error(f"获取讲话状态失败: {response.error}")
            return None
    
    async def get_talk_result(self, talk_id: str) -> Optional[str]:
        """获取讲话结果（视频URL）"""
        status = await self.get_talk_status(talk_id)
        
        if status and status.get("status") == "done":
            return status.get("result_url")
        
        return None

class DanmakuClient(BaseAPIClient):
    """弹幕API客户端"""
    
    def __init__(self, provider: APIProvider, api_key: str, api_url: str, 
                 room_id: str, **kwargs):
        super().__init__(api_key, api_url, kwargs.get("timeout", 10))
        self.provider = provider
        self.room_id = room_id
        self.poll_interval = kwargs.get("poll_interval", 3)
        self.last_message_id = ""
        
    async def get_danmaku(self, limit: int = 50) -> List[Dict]:
        """获取弹幕"""
        
        if self.provider == APIProvider.TIKHUB:
            params = {
                "room_id": self.room_id,
                "limit": limit,
                "since": self.last_message_id
            }
            
            response = await self._make_request("GET", "live/danmaku", params=params)
            
            if response.success:
                messages = response.data.get("messages", [])
                if messages:
                    self.last_message_id = messages[-1].get("id", "")
                return messages
            else:
                logger.error(f"获取弹幕失败: {response.error}")
                return []
                
        elif self.provider == APIProvider.DOUYIN:
            # 抖音开放平台弹幕接口
            return await self._get_douyin_danmaku(limit)
            
        return []
    
    async def _get_douyin_danmaku(self, limit: int) -> List[Dict]:
        """获取抖音弹幕"""
        # 抖音开放平台需要特殊处理
        # 需要处理签名和认证
        return []

class APIManager:
    """API管理器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.clients = {}
        self.initialize_clients()
    
    def initialize_clients(self):
        """初始化所有客户端"""
        api_config = self.config.get("apis", {})
        
        # LLM客户端
        llm_config = api_config.get("llm", {})
        if llm_config.get("api_key"):
            provider = APIProvider(llm_config.get("provider", "openai"))
            self.clients["llm"] = LLMClient(
                provider=provider,
                api_key=llm_config["api_key"],
                api_url=llm_config["api_url"],
                model=llm_config.get("model", "gpt-3.5-turbo"),
                temperature=llm_config.get("temperature", 0.7),
                max_tokens=llm_config.get("max_tokens", 200)
            )
        
        # TTS客户端
        tts_config = api_config.get("tts", {})
        if tts_config.get("api_key"):
            provider = APIProvider(tts_config.get("provider", "elevenlabs"))
            self.clients["tts"] = TTSClient(
                provider=provider,
                api_key=tts_config["api_key"],
                api_url=tts_config["api_url"],
                voice_id=tts_config.get("voice_id", ""),
                language=tts_config.get("language", "en-US")
            )
        
        # 数字人客户端
        dh_config = api_config.get("digital_human", {})
        if dh_config.get("api_key"):
            provider = APIProvider(dh_config.get("provider", "d_id"))
            self.clients["digital_human"] = DigitalHumanClient(
                provider=provider,
                api_key=dh_config["api_key"],
                api_url=dh_config["api_url"],
                avatar_id=dh_config.get("avatar_id", ""),
                driver_id=dh_config.get("driver_id", "")
            )
        
        # 弹幕客户端
        dm_config = api_config.get("danmaku", {})
        if dm_config.get("api_key"):
            provider = APIProvider(dm_config.get("provider", "tikhub"))
            platform_config = self.config.get("platform", {})
            self.clients["danmaku"] = DanmakuClient(
                provider=provider,
                api_key=dm_config["api_key"],
                api_url=dm_config["api_url"],
                room_id=platform_config.get("room_id", ""),
                poll_interval=dm_config.get("poll_interval", 3)
            )
    
    def get_client(self, client_type: str) -> Optional[BaseAPIClient]:
        """获取客户端"""
        return self.clients.get(client_type)
    
    async def close_all(self):
        """关闭所有客户端"""
        for client in self.clients.values():
            if hasattr(client, "close"):
                await client.close()
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        stats = {}
        
        for name, client in self.clients.items():
            stats[name] = {
                "request_count": getattr(client, "request_count", 0),
                "error_count": getattr(client, "error_count", 0),
                "error_rate": (getattr(client, "error_count", 0) / 
                              max(getattr(client, "request_count", 1), 1))
            }
        
        return stats