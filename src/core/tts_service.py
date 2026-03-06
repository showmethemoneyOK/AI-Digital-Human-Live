#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTS语音合成服务
支持多平台：阿里云、腾讯云、讯飞、ElevenLabs等
"""

import os
import json
import logging
import time
import base64
from typing import Dict, Optional, Any
import aiohttp
from enum import Enum

logger = logging.getLogger(__name__)


class TTSProvider(Enum):
    """TTS提供商枚举"""
    ALIYUN = "aliyun"  # 阿里云
    TENCENT = "tencent"  # 腾讯云
    XUNFEI = "xunfei"  # 讯飞
    ELEVENLABS = "elevenlabs"  # ElevenLabs
    GOOGLE = "google"  # Google TTS


class TTSService:
    """TTS语音合成服务"""
    
    def __init__(self, config: Dict):
        """初始化TTS服务
        
        Args:
            config: 配置字典，包含TTS相关配置
        """
        self.config = config
        self.provider = config.get("TTS_PROVIDER", "aliyun").lower()
        self.api_key = config.get("TTS_API_KEY")
        self.api_secret = config.get("TTS_API_SECRET")
        self.app_id = config.get("TTS_APP_ID")
        
        # 语音配置
        self.voice = config.get("TTS_VOICE", "zh-CN-XiaoxiaoNeural")
        self.speed = config.get("TTS_SPEED", 1.0)
        self.pitch = config.get("TTS_PITCH", 0)
        self.volume = config.get("TTS_VOLUME", 1.0)
        
        # 音频格式
        self.format = config.get("TTS_FORMAT", "mp3")
        self.sample_rate = config.get("TTS_SAMPLE_RATE", 16000)
        
        # 缓存
        self.cache_enabled = config.get("TTS_CACHE_ENABLED", True)
        self.cache_dir = config.get("TTS_CACHE_DIR", "cache/tts")
        self.cache_max_size = config.get("TTS_CACHE_MAX_SIZE", 100)
        
        # 初始化缓存目录
        if self.cache_enabled:
            os.makedirs(self.cache_dir, exist_ok=True)
        
        # 提供商配置
        self.provider_configs = {
            "aliyun": {
                "url": "https://nls-gateway.cn-shanghai.aliyuncs.com/stream/v1/tts",
                "method": "POST",
                "auth_type": "access_key"
            },
            "tencent": {
                "url": "https://tts.cloud.tencent.com/stream",
                "method": "POST",
                "auth_type": "secret"
            },
            "xunfei": {
                "url": "https://tts-api.xfyun.cn/v2/tts",
                "method": "POST",
                "auth_type": "api_key"
            },
            "elevenlabs": {
                "url": "https://api.elevenlabs.io/v1/text-to-speech",
                "method": "POST",
                "auth_type": "api_key"
            }
        }
        
        # HTTP会话
        self.session = None
        
        logger.info(f"TTS服务初始化完成，提供商: {self.provider}")
    
    async def initialize(self):
        """初始化服务"""
        try:
            await self._ensure_session()
            logger.info("TTS服务初始化成功")
            return True
        except Exception as e:
            logger.error(f"TTS服务初始化失败: {e}")
            return False
    
    async def _ensure_session(self):
        """确保HTTP会话存在"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
    
    async def close(self):
        """关闭服务"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
        
        logger.info("TTS服务已关闭")
    
    def _get_cache_key(self, text: str, voice: str = None) -> str:
        """获取缓存键"""
        import hashlib
        
        voice = voice or self.voice
        cache_str = f"{text}_{voice}_{self.speed}_{self.pitch}_{self.volume}_{self.format}"
        
        return hashlib.md5(cache_str.encode('utf-8')).hexdigest()
    
    def _get_cached_audio(self, cache_key: str) -> Optional[bytes]:
        """获取缓存的音频"""
        if not self.cache_enabled:
            return None
        
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.{self.format}")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    audio_data = f.read()
                
                # 检查文件是否过期（24小时）
                file_age = time.time() - os.path.getmtime(cache_file)
                if file_age < 86400:  # 24小时
                    logger.debug(f"从缓存读取音频: {cache_key}")
                    return audio_data
                else:
                    os.remove(cache_file)  # 删除过期缓存
            except Exception as e:
                logger.warning(f"读取缓存失败: {e}")
        
        return None
    
    def _save_to_cache(self, cache_key: str, audio_data: bytes):
        """保存到缓存"""
        if not self.cache_enabled:
            return
        
        try:
            # 清理旧缓存
            self._cleanup_cache()
            
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.{self.format}")
            
            with open(cache_file, 'wb') as f:
                f.write(audio_data)
            
            logger.debug(f"音频已缓存: {cache_key}")
            
        except Exception as e:
            logger.warning(f"保存缓存失败: {e}")
    
    def _cleanup_cache(self):
        """清理缓存"""
        if not os.path.exists(self.cache_dir):
            return
        
        try:
            files = os.listdir(self.cache_dir)
            if len(files) <= self.cache_max_size:
                return
            
            # 按修改时间排序，删除最旧的文件
            file_times = []
            for file in files:
                file_path = os.path.join(self.cache_dir, file)
                mtime = os.path.getmtime(file_path)
                file_times.append((file_path, mtime))
            
            # 按修改时间升序排序
            file_times.sort(key=lambda x: x[1])
            
            # 删除超出数量的文件
            files_to_delete = len(file_times) - self.cache_max_size
            for i in range(files_to_delete):
                os.remove(file_times[i][0])
                logger.debug(f"清理缓存文件: {os.path.basename(file_times[i][0])}")
                
        except Exception as e:
            logger.warning(f"清理缓存失败: {e}")
    
    async def text_to_speech(self, text: str, voice: str = None, **kwargs) -> Dict:
        """文本转语音
        
        Args:
            text: 要转换的文本
            voice: 语音名称（可选）
            **kwargs: 其他参数
            
        Returns:
            包含音频数据和元数据的字典
        """
        start_time = time.time()
        
        try:
            # 参数处理
            voice = voice or self.voice
            speed = kwargs.get("speed", self.speed)
            pitch = kwargs.get("pitch", self.pitch)
            volume = kwargs.get("volume", self.volume)
            
            # 检查缓存
            cache_key = self._get_cache_key(text, voice)
            cached_audio = self._get_cached_audio(cache_key)
            
            if cached_audio:
                processing_time = time.time() - start_time
                return {
                    "success": True,
                    "audio_data": cached_audio,
                    "audio_format": self.format,
                    "text": text,
                    "voice": voice,
                    "from_cache": True,
                    "processing_time_ms": round(processing_time * 1000, 2)
                }
            
            # 调用TTS API
            audio_data = await self._call_tts_api(text, voice, speed, pitch, volume)
            
            if audio_data:
                # 保存到缓存
                self._save_to_cache(cache_key, audio_data)
                
                processing_time = time.time() - start_time
                
                result = {
                    "success": True,
                    "audio_data": audio_data,
                    "audio_format": self.format,
                    "text": text,
                    "voice": voice,
                    "from_cache": False,
                    "processing_time_ms": round(processing_time * 1000, 2)
                }
                
                # 可以生成临时URL供数字人使用
                if self.config.get("GENERATE_AUDIO_URL", False):
                    audio_url = await self._generate_audio_url(audio_data)
                    result["audio_url"] = audio_url
                
                logger.info(f"TTS转换成功: {len(text)}字符 -> {len(audio_data)}字节, 耗时: {result['processing_time_ms']}ms")
                return result
            else:
                raise Exception("TTS API返回空数据")
                
        except Exception as e:
            logger.error(f"TTS转换失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": text,
                "processing_time_ms": round((time.time() - start_time) * 1000, 2)
            }
    
    async def _call_tts_api(self, text: str, voice: str, speed: float, pitch: int, volume: float) -> bytes:
        """调用TTS API"""
        provider_config = self.provider_configs.get(self.provider)
        if not provider_config:
            raise ValueError(f"不支持的TTS提供商: {self.provider}")
        
        await self._ensure_session()
        
        # 根据提供商准备请求
        if self.provider == "aliyun":
            return await self._call_aliyun_tts(text, voice, speed)
        elif self.provider == "tencent":
            return await self._call_tencent_tts(text, voice, speed)
        elif self.provider == "xunfei":
            return await self._call_xunfei_tts(text, voice, speed, pitch)
        elif self.provider == "elevenlabs":
            return await self._call_elevenlabs_tts(text, voice)
        else:
            raise ValueError(f"未实现的TTS提供商: {self.provider}")
    
    async def _call_aliyun_tts(self, text: str, voice: str, speed: float) -> bytes:
        """调用阿里云TTS"""
        import uuid
        
        # 准备请求数据
        request_data = {
            "appkey": self.app_id,
            "token": self.api_key,
            "text": text,
            "format": self.format,
            "sample_rate": self.sample_rate,
            "voice": voice,
            "volume": int(self.volume * 100),
            "speech_rate": int(speed * 100),
            "pitch_rate": self.pitch
        }
        
        # 移除空值
        request_data = {k: v for k, v in request_data.items() if v is not None}
        
        headers = {
            "Content-Type": "application/json",
            "X-NLS-Token": self.api_key
        }
        
        url = self.provider_configs["aliyun"]["url"]
        
        async with self.session.post(url, json=request_data, headers=headers) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"阿里云TTS失败: {response.status} - {error_text}")
            
            # 阿里云返回二进制音频数据
            audio_data = await response.read()
            
            # 检查是否是错误响应
            if len(audio_data) < 100 and b"error" in audio_data.lower():
                error_text = audio_data.decode('utf-8', errors='ignore')
                raise Exception(f"阿里云TTS错误: {error_text}")
            
            return audio_data
    
    async def _call_tencent_tts(self, text: str, voice: str, speed: float) -> bytes:
        """调用腾讯云TTS"""
        import hashlib
        import hmac
        
        # 腾讯云需要签名
        timestamp = int(time.time())
        nonce = str(timestamp)
        
        # 构建签名字符串
        sign_str = f"appid={self.app_id}&nonce={nonce}&project=0&time={timestamp}"
        
        # 计算签名
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            sign_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # 准备请求数据
        request_data = {
            "appid": int(self.app_id),
            "time": timestamp,
            "nonce": nonce,
            "sign": signature,
            "project": 0,
            "text": text,
            "model_type": 1,
            "speed": speed,
            "voice_type": self._get_tencent_voice_type(voice),
            "volume": self.volume
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        url = self.provider_configs["tencent"]["url"]
        
        async with self.session.post(url, json=request_data, headers=headers) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"腾讯云TTS失败: {response.status} - {error_text}")
            
            result = await response.json()
            
            if result.get("code") != 0:
                raise Exception(f"腾讯云TTS错误: {result.get('message')}")
            
            # 腾讯云返回base64编码的音频
            audio_base64 = result["data"]["voice"]
            audio_data = base64.b64decode(audio_base64)
            
            return audio_data
    
    def _get_tencent_voice_type(self, voice: str) -> int:
        """获取腾讯云语音类型"""
        voice_mapping = {
            "zh-CN-XiaoxiaoNeural": 1,
            "zh-CN-YunxiNeural": 1001,
            "zh-CN-YunxiaNeural": 1002,
            "zh-CN-YunyangNeural": 1003,
            "en-US-JennyNeural": 1004,
            "en-US-GuyNeural": 1005
        }
        
        return voice_mapping.get(voice, 1)
    
    async def _call_xunfei_tts(self, text: str, voice: str, speed: float, pitch: int) -> bytes:
        """调用讯飞TTS"""
        import hashlib
        import base64
        import json
        
        # 讯飞需要API Key和API Secret
        api_key = self.api_key
        api_secret = self.api_secret
        
        # 准备请求数据
        request_data = {
            "common": {
                "app_id": self.app_id
            },
            "business": {
                "aue": "lame" if self.format == "mp3" else "raw",
                "sfl": 1,
                "auf": f"audio/L16;rate={self.sample_rate}",
                "vcn": voice,
                "speed": speed,
                "volume": self.volume,
                "pitch": pitch,
                "bgs": 0,
                "tte": "utf8"
            },
            "data": {
                "text": base64.b64encode(text.encode('utf-8')).decode('utf-8'),
                "status": 2
            }
        }
        
        # 生成请求URL（带鉴权）
        url = self._generate_xunfei_url()
        
        headers = {
            "Content-Type": "application/json",
            "X-Appid": self.app_id
        }
        
        async with self.session.post(url, json=request_data, headers=headers) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"讯飞TTS失败: {response.status} - {error_text}")
            
            result = await response.json()
            
            if result.get("code") != 0:
                raise Exception(f"讯飞TTS错误: {result.get('message')}")
            
            # 讯飞返回base64编码的音频
            audio_base64 = result["data"]["audio"]
            audio_data = base64.b64decode(audio_base64)
            
            return audio_data
    
    def _generate_xunfei_url(self) -> str:
        """生成讯飞请求URL（带鉴权）"""
        import hashlib
        import hmac
        import base64
        from urllib.parse import urlencode
        
        # 生成RFC1123格式的时间戳
        from datetime import datetime
        import time
        
        date = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        
        # 生成签名
        signature_origin = f"host: tts-api.xfyun.cn\ndate: {date}\nGET /v2/tts HTTP/1.1"
        
        signature_sha = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_origin.encode