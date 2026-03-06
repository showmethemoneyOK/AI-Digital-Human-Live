#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数字人接口
支持抖音白名单厂商和TikTok合规数字人
"""

import os
import json
import logging
import time
from typing import Dict, Optional, Any
import aiohttp

logger = logging.getLogger(__name__)


class DigitalHuman:
    """数字人接口"""
    
    def __init__(self, config: Dict):
        """初始化数字人接口
        
        Args:
            config: 配置字典，包含数字人相关配置
        """
        self.config = config
        self.provider = config.get("DIGITAL_HUMAN_PROVIDER", "guiji").lower()
        self.api_key = config.get("DIGITAL_HUMAN_API_KEY")
        self.api_url = config.get("DIGITAL_HUMAN_API_URL")
        
        # 数字人配置
        self.avatar_id = config.get("DIGITAL_HUMAN_AVATAR_ID")
        self.avatar_name = config.get("DIGITAL_HUMAN_AVATAR_NAME", "AI主播")
        self.avatar_image = config.get("DIGITAL_HUMAN_AVATAR_IMAGE")
        
        # 输出配置
        self.output_mode = config.get("DIGITAL_HUMAN_OUTPUT_MODE", "rtmp")  # rtmp, virtual_camera, file
        self.output_url = config.get("DIGITAL_HUMAN_OUTPUT_URL")
        self.virtual_camera_name = config.get("DIGITAL_HUMAN_VIRTUAL_CAMERA", "AI Digital Human")
        
        # 性能配置
        self.resolution = config.get("DIGITAL_HUMAN_RESOLUTION", "1080x1920")
        self.fps = config.get("DIGITAL_HUMAN_FPS", 30)
        self.bitrate = config.get("DIGITAL_HUMAN_BITRATE", 4000)
        
        # 状态
        self.initialized = False
        self.connected = False
        self.speaking = False
        
        # HTTP会话
        self.session = None
        
        logger.info(f"数字人接口初始化完成，提供商: {self.provider}")
    
    async def initialize(self) -> bool:
        """初始化数字人"""
        try:
            await self._ensure_session()
            
            # 测试连接
            if await self._test_connection():
                self.initialized = True
                logger.info("数字人接口初始化成功")
                return True
            else:
                logger.error("数字人接口连接测试失败")
                return False
                
        except Exception as e:
            logger.error(f"数字人接口初始化失败: {e}")
            return False
    
    async def _ensure_session(self):
        """确保HTTP会话存在"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
    
    async def close(self):
        """关闭数字人接口"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
        
        self.initialized = False
        self.connected = False
        
        logger.info("数字人接口已关闭")
    
    async def _test_connection(self) -> bool:
        """测试连接"""
        try:
            # 根据提供商测试连接
            if self.provider == "guiji":
                return await self._test_guiji_connection()
            elif self.provider == "youliao":
                return await self._test_youliao_connection()
            elif self.provider == "heygen":
                return await self._test_heygen_connection()
            elif self.provider == "d-id":
                return await self._test_did_connection()
            else:
                logger.warning(f"未知的数字人提供商: {self.provider}")
                return True  # 对于未知提供商，假设连接成功
                
        except Exception as e:
            logger.error(f"连接测试失败: {e}")
            return False
    
    async def _test_guiji_connection(self) -> bool:
        """测试硅基智能连接"""
        if not self.api_url:
            logger.warning("未配置硅基智能API URL，跳过连接测试")
            return True
        
        try:
            test_url = f"{self.api_url.rstrip('/')}/api/v1/status"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with self.session.get(test_url, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("code") == 0:
                        self.connected = True
                        return True
                    else:
                        logger.error(f"硅基智能状态异常: {result.get('message')}")
                        return False
                else:
                    logger.error(f"硅基智能连接失败: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"硅基智能连接测试异常: {e}")
            return False
    
    async def _test_youliao_connection(self) -> bool:
        """测试有料AI连接"""
        # 类似硅基智能的实现
        return await self._test_generic_connection()
    
    async def _test_heygen_connection(self) -> bool:
        """测试HeyGen连接"""
        if not self.api_key:
            logger.warning("未配置HeyGen API Key，跳过连接测试")
            return True
        
        try:
            test_url = "https://api.heygen.com/v1/account"
            
            headers = {
                "X-Api-Key": self.api_key,
                "Content-Type": "application/json"
            }
            
            async with self.session.get(test_url, headers=headers) as response:
                if response.status == 200:
                    self.connected = True
                    return True
                else:
                    logger.error(f"HeyGen连接失败: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"HeyGen连接测试异常: {e}")
            return False
    
    async def _test_did_connection(self) -> bool:
        """测试D-ID连接"""
        if not self.api_key:
            logger.warning("未配置D-ID API Key，跳过连接测试")
            return True
        
        try:
            test_url = "https://api.d-id.com/talks"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with self.session.get(test_url, headers=headers) as response:
                if response.status == 200:
                    self.connected = True
                    return True
                else:
                    logger.error(f"D-ID连接失败: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"D-ID连接测试异常: {e}")
            return False
    
    async def _test_generic_connection(self) -> bool:
        """通用连接测试"""
        if not self.api_url:
            logger.warning("未配置API URL，跳过连接测试")
            return True
        
        try:
            async with self.session.get(self.api_url) as response:
                if response.status < 400:
                    self.connected = True
                    return True
                else:
                    logger.error(f"通用连接失败: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"通用连接测试异常: {e}")
            return False
    
    async def speak(self, text: str, audio_data: bytes = None, audio_url: str = None, **kwargs) -> Dict:
        """让数字人说话
        
        Args:
            text: 要说的文本
            audio_data: 音频数据（可选）
            audio_url: 音频URL（可选）
            **kwargs: 其他参数
            
        Returns:
            执行结果字典
        """
        start_time = time.time()
        
        try:
            if not self.initialized:
                raise Exception("数字人接口未初始化")
            
            # 根据提供商调用相应接口
            if self.provider == "guiji":
                result = await self._guiji_speak(text, audio_data, audio_url, **kwargs)
            elif self.provider == "youliao":
                result = await self._youliao_speak(text, audio_data, audio_url, **kwargs)
            elif self.provider == "heygen":
                result = await self._heygen_speak(text, audio_data, audio_url, **kwargs)
            elif self.provider == "d-id":
                result = await self._did_speak(text, audio_data, audio_url, **kwargs)
            else:
                result = await self._generic_speak(text, audio_data, audio_url, **kwargs)
            
            # 更新状态
            self.speaking = True
            
            processing_time = time.time() - start_time
            
            result.update({
                "success": True,
                "processing_time_ms": round(processing_time * 1000, 2),
                "timestamp": time.time()
            })
            
            logger.info(f"数字人说话完成: {len(text)}字符, 耗时: {result['processing_time_ms']}ms")
            return result
            
        except Exception as e:
            logger.error(f"数字人说话失败: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "timestamp": time.time()
            }
    
    async def _guiji_speak(self, text: str, audio_data: bytes, audio_url: str, **kwargs) -> Dict:
        """硅基智能说话"""
        if not self.api_url:
            raise Exception("未配置硅基智能API URL")
        
        await self._ensure_session()
        
        # 准备请求数据
        request_data = {
            "avatar_id": self.avatar_id,
            "text": text,
            "voice_config": {
                "voice_type": "default",
                "speed": kwargs.get("speed", 1.0),
                "pitch": kwargs.get("pitch", 0),
                "volume": kwargs.get("volume", 1.0)
            },
            "video_config": {
                "resolution": self.resolution,
                "fps": self.fps,
                "bitrate": self.bitrate
            }
        }
        
        # 如果有音频数据或URL，添加音频配置
        if audio_data or audio_url:
            request_data["audio_config"] = {}
            
            if audio_data:
                import base64
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                request_data["audio_config"]["audio_data"] = audio_base64
                request_data["audio_config"]["audio_format"] = kwargs.get("audio_format", "mp3")
            
            if audio_url:
                request_data["audio_config"]["audio_url"] = audio_url
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        speak_url = f"{self.api_url.rstrip('/')}/api/v1/speak"
        
        async with self.session.post(speak_url, json=request_data, headers=headers) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"硅基智能说话失败: {response.status} - {error_text}")
            
            result = await response.json()
            
            if result.get("code") != 0:
                raise Exception(f"硅基智能错误: {result.get('message')}")
            
            # 提取视频URL或推流地址
            video_data = result.get("data", {})
            
            return {
                "task_id": video_data.get("task_id"),
                "video_url": video_data.get("video_url"),
                "stream_url": video_data.get("stream_url"),
                "estimated_duration": video_data.get("estimated_duration", 0),
                "provider": "guiji"
            }
    
    async def _youliao_speak(self, text: str, audio_data: bytes, audio_url: str, **kwargs) -> Dict:
        """有料AI说话"""
        # 实现类似硅基智能
        return await self._generic_speak(text, audio_data, audio_url, **kwargs)
    
    async def _heygen_speak(self, text: str, audio_data: bytes, audio_url: str, **kwargs) -> Dict:
        """HeyGen说话"""
        if not self.api_key:
            raise Exception("未配置HeyGen API Key")
        
        await self._ensure_session()
        
        # 准备请求数据
        request_data = {
            "avatar_id": self.avatar_id,
            "text": text,
            "voice_id": kwargs.get("voice_id", "1bd001e7e50f421d891986aad5158bc8"),
            "model": kwargs.get("model", "v2"),
            "version": kwargs.get("version", "v1")
        }
        
        # 如果有音频URL，使用音频驱动
        if audio_url:
            request_data["audio_url"] = audio_url
            request_data["driven_by"] = "audio"
        else:
            request_data["driven_by"] = "text"
        
        headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        speak_url = "https://api.heygen.com/v1/video.generate"
        
        async with self.session.post(speak_url, json=request_data, headers=headers) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"HeyGen说话失败: {response.status} - {error_text}")
            
            result = await response.json()
            
            if not result.get("data", {}).get("video_id"):
                raise Exception(f"HeyGen错误: {result.get('error', '未知错误')}")
            
            video_data = result["data"]
            
            return {
                "video_id": video_data.get("video_id"),
                "video_url": video_data.get("video_url"),
                "status_url": video_data.get("status_url"),
                "estimated_time": video_data.get("estimated_time", 30),
                "provider": "heygen"
            }
    
    async def _did_speak(self, text: str, audio_data: bytes, audio_url: str, **kwargs) -> Dict:
        """D-ID说话"""
        if not self.api_key:
            raise Exception("未配置D-ID API Key")
        
        await self._ensure_session()
        
        # 准备请求数据
        request_data = {
            "source_url": self.avatar_image,
            "script": {
                "type": "text",
                "input": text,
                "provider": {
                    "type": "microsoft",
                    "voice_id": kwargs.get("voice_id", "zh-CN-XiaoxiaoNeural")
                }
            },
            "config": {
                "fluent": "true",
                "pad_audio": "0.0"
            }
        }
        
        # 如果有音频URL，使用音频驱动
        if audio_url:
            request_data["script"] = {
                "type": "audio",
                "audio_url": audio_url
            }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        speak_url = "https://api.d-id.com/talks"
        
        async with self.session.post(speak_url, json=request_data, headers=headers) as response:
            if response.status != 201:
                error_text = await response.text()
                raise Exception(f"D-ID说话失败: {response.status} - {error_text}")
            
            result = await response.json()
            
            if not result.get("id"):
                raise Exception(f"D-ID错误: {result.get('error', '未知错误')}")
            
            return {
                "talk_id": result.get("id"),
                "status_url": result.get("status_url"),
                "result_url": result.get("result_url"),
                "estimated_time": result.get("estimated_time", 30),
                "provider": "d-id"
            }
    
    async def _generic_speak(self, text: str, audio_data: bytes, audio_url: str, **kwargs) -> Dict:
        """通用说话接口"""
        # 简单实现，记录日志但不实际调用
        logger.info(f"通用数字人说话: {text[:50]}...")
        
        return {
            "provider": "generic",
            "status": "simulated",
            "message": "通用数字人接口，实际使用时需要配置具体提供商"
        }
    
    async def get_status(self, task_id: str = None) -> Dict:
        """获取任务状态
        
        Args:
            task_id: 任务ID（可选）
            
        Returns:
            状态信息字典
        """
        try:
            if not self.initialized:
                raise Exception("数字人接口未初始化")
            
            # 根据提供商获取状态
            if self.provider == "guiji":
                return await self._guiji_get_status(task_id)
            elif self.provider == "heygen":
                return await self._heygen_get_status(task_id)
            elif self.provider == "d-id":
                return await self._did_get_status(task_id)
            else:
                return await self._generic_get_status(task_id)
                
        except Exception as e:
            logger.error(f"获取状态失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def _guiji_get_status(self, task_id: str) -> Dict:
        """获取硅基智能任务状态"""
        if not task_id:
            return {"status": "idle", "message": "无活跃任务"}
        
        status_url = f"{self.api_url.rstrip('/')}/api/v1/task/{task_id}"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with self.session.get(status_url, headers=headers) as response:
            if response.status != 200:
                return {"status": "error", "message": f"请求失败: {response.status}"}
            
            result = await response.json()
            
            if result.get("code") != 0:
                return {"status": "error", "message": result.get("message")}
            
            task_data = result.get("data", {})
            
            return {
                "success": True,
                "task_id": task_id,
