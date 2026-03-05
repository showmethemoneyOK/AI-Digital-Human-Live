#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
推流控制模块
控制OBS Studio和抖音直播伴侣
"""

import asyncio
import json
import subprocess
import time
import os
import sys
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import logging
import psutil

logger = logging.getLogger(__name__)

@dataclass
class StreamConfig:
    """推流配置"""
    platform: str  # "tiktok" 或 "douyin"
    stream_url: str
    stream_key: str
    video_source: str  # 视频源路径或URL
    audio_source: str  # 音频源路径
    resolution: str = "1920x1080"
    fps: int = 30
    bitrate: int = 6000  # kbps
    audio_bitrate: int = 128  # kbps

class OBSController:
    """OBS Studio控制器"""
    
    def __init__(self, host: str = "localhost", port: int = 4455, 
                 password: str = ""):
        self.host = host
        self.port = port
        self.password = password
        self.ws_url = f"ws://{host}:{port}"
        self.connected = False
        self.ws_client = None
        
        # 检查OBS是否安装
        self.obs_path = self._find_obs_path()
    
    def _find_obs_path(self) -> Optional[str]:
        """查找OBS安装路径"""
        common_paths = [
            "C:\\Program Files\\obs-studio\\bin\\64bit\\obs64.exe",
            "C:\\Program Files (x86)\\obs-studio\\bin\\64bit\\obs64.exe",
            "C:\\Program Files\\OBS Studio\\obs64.exe",
            "/usr/bin/obs",
            "/Applications/OBS.app/Contents/MacOS/OBS"
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        # 尝试从环境变量查找
        import shutil
        obs_executable = shutil.which("obs") or shutil.which("obs64")
        if obs_executable:
            return obs_executable
        
        return None
    
    def is_obs_installed(self) -> bool:
        """检查OBS是否安装"""
        return self.obs_path is not None
    
    def is_obs_running(self) -> bool:
        """检查OBS是否运行"""
        for proc in psutil.process_iter(['name']):
            try:
                if 'obs' in proc.info['name'].lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return False
    
    async def start_obs(self) -> bool:
        """启动OBS"""
        if not self.obs_path:
            logger.error("未找到OBS安装路径")
            return False
        
        if self.is_obs_running():
            logger.info("OBS已在运行")
            return True
        
        try:
            subprocess.Popen([self.obs_path], 
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
            
            # 等待OBS启动
            for _ in range(30):  # 最多等待30秒
                if self.is_obs_running():
                    logger.info("OBS启动成功")
                    return True
                await asyncio.sleep(1)
            
            logger.error("OBS启动超时")
            return False
            
        except Exception as e:
            logger.error(f"启动OBS失败: {e}")
            return False
    
    async def connect_websocket(self) -> bool:
        """连接OBS WebSocket"""
        try:
            import websockets
            self.ws_client = await websockets.connect(self.ws_url)
            
            # 如果需要密码，进行认证
            if self.password:
                auth_response = await self._authenticate()
                if not auth_response:
                    await self.ws_client.close()
                    self.ws_client = None
                    return False
            
            self.connected = True
            logger.info("OBS WebSocket连接成功")
            return True
            
        except Exception as e:
            logger.error(f"连接OBS WebSocket失败: {e}")
            self.connected = False
            return False
    
    async def _authenticate(self) -> bool:
        """WebSocket认证"""
        try:
            # 获取认证挑战
            import base64
            import hashlib
            
            response = await self.ws_client.recv()
            auth_data = json.loads(response)
            
            if auth_data.get("op") == 1:  # Hello
                # 计算认证响应
                import secrets
                import string
                
                challenge = auth_data["d"]["authentication"]["challenge"]
                salt = auth_data["d"]["authentication"]["salt"]
                
                # 生成随机字符串
                random_chars = ''.join(secrets.choice(string.ascii_letters + string.digits) 
                                      for _ in range(32))
                
                # 计算认证哈希
                secret_string = self.password + salt
                secret_hash = base64.b64encode(
                    hashlib.sha256(secret_string.encode()).digest()
                ).decode()
                
                auth_response = base64.b64encode(
                    hashlib.sha256((secret_hash + challenge).encode()).digest()
                ).decode()
                
                # 发送认证请求
                auth_request = {
                    "op": 2,
                    "d": {
                        "rpcVersion": 1,
                        "authentication": auth_response
                    }
                }
                
                await self.ws_client.send(json.dumps(auth_request))
                
                # 等待认证响应
                response = await self.ws_client.recv()
                auth_result = json.loads(response)
                
                if auth_result.get("op") == 2:  # Identified
                    return True
                
            return False
            
        except Exception as e:
            logger.error(f"OBS认证失败: {e}")
            return False
    
    async def send_request(self, request_type: str, data: Dict = None) -> Optional[Dict]:
        """发送WebSocket请求"""
        if not self.connected or not self.ws_client:
            logger.error("OBS WebSocket未连接")
            return None
        
        try:
            request_id = str(int(time.time() * 1000))
            request = {
                "op": 6,
                "d": {
                    "requestType": request_type,
                    "requestId": request_id,
                    "requestData": data or {}
                }
            }
            
            await self.ws_client.send(json.dumps(request))
            
            # 等待响应
            response = await self.ws_client.recv()
            response_data = json.loads(response)
            
            if (response_data.get("op") == 7 and 
                response_data["d"]["requestId"] == request_id):
                return response_data["d"].get("responseData")
            
            return None
            
        except Exception as e:
            logger.error(f"发送OBS请求失败: {e}")
            return None
    
    async def start_streaming(self) -> bool:
        """开始推流"""
        response = await self.send_request("StartStream")
        return response is not None
    
    async def stop_streaming(self) -> bool:
        """停止推流"""
        response = await self.send_request("StopStream")
        return response is not None
    
    async def set_stream_settings(self, stream_url: str, stream_key: str) -> bool:
        """设置推流参数"""
        settings = {
            "type": "rtmp_custom",
            "settings": {
                "server": stream_url,
                "key": stream_key
            }
        }
        
        response = await self.send_request("SetStreamServiceSettings", settings)
        return response is not None
    
    async def create_scene(self, scene_name: str) -> bool:
        """创建场景"""
        response = await self.send_request("CreateScene", {"sceneName": scene_name})
        return response is not None
    
    async def add_video_source(self, scene_name: str, source_name: str, 
                              video_path: str) -> bool:
        """添加视频源"""
        source_settings = {
            "sceneName": scene_name,
            "sourceName": source_name,
            "sourceKind": "ffmpeg_source",
            "sourceSettings": {
                "local_file": video_path,
                "looping": True
            }
        }
        
        response = await self.send_request("CreateSource", source_settings)
        return response is not None
    
    async def get_stream_status(self) -> Optional[Dict]:
        """获取推流状态"""
        response = await self.send_request("GetStreamStatus")
        return response
    
    async def disconnect(self):
        """断开连接"""
        if self.ws_client:
            await self.ws_client.close()
            self.ws_client = None
            self.connected = False

class DouyinLiveCompanionController:
    """抖音直播伴侣控制器"""
    
    def __init__(self, executable_path: str = None):
        self.executable_path = executable_path or self._find_companion_path()
        self.process = None
    
    def _find_companion_path(self) -> Optional[str]:
        """查找抖音直播伴侣路径"""
        common_paths = [
            "C:\\Program Files\\Douyin\\LiveCompanion\\LiveCompanion.exe",
            "C:\\Program Files (x86)\\Douyin\\LiveCompanion\\LiveCompanion.exe",
            "D:\\Program Files\\Douyin\\LiveCompanion\\LiveCompanion.exe"
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def is_installed(self) -> bool:
        """检查是否安装"""
        return self.executable_path is not None and os.path.exists(self.executable_path)
    
    def is_running(self) -> bool:
        """检查是否运行"""
        for proc in psutil.process_iter(['name']):
            try:
                if 'livecompanion' in proc.info['name'].lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return False
    
    async def start_companion(self) -> bool:
        """启动直播伴侣"""
        if not self.executable_path:
            logger.error("未找到抖音直播伴侣路径")
            return False
        
        if self.is_running():
            logger.info("抖音直播伴侣已在运行")
            return True
        
        try:
            self.process = subprocess.Popen(
                [self.executable_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # 等待启动
            for _ in range(30):
                if self.is_running():
                    logger.info("抖音直播伴侣启动成功")
                    return True
                await asyncio.sleep(1)
            
            logger.error("抖音直播伴侣启动超时")
            return False
            
        except Exception as e:
            logger.error(f"启动抖音直播伴侣失败: {e}")
            return False
    
    async def stop_companion(self) -> bool:
        """停止直播伴侣"""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
                logger.info("抖音直播伴侣已停止")
                return True
            except subprocess.TimeoutExpired:
                self.process.kill()
                logger.warning("强制停止抖音直播伴侣")
                return True
        
        # 如果进程不是由我们启动的，尝试查找并终止
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'livecompanion' in proc.info['name'].lower():
                    proc.terminate()
                    logger.info("终止抖音直播伴侣进程")
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return False
    
    async def start_streaming(self, stream_url: str, stream_key: str) -> bool:
        """开始推流"""
        # 抖音直播伴侣通常通过UI操作
        # 这里可以实现自动化控制，但需要具体分析UI结构
        logger.warning("抖音直播伴侣推流需要手动操作或UI自动化")
        return False
    
    async def stop_streaming(self) -> bool:
        """停止推流"""
        logger.warning("抖音直播伴侣停止推流需要手动操作")
        return False

class StreamingManager:
    """推流管理器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.platform = config.get("platform", {}).get("type", "tiktok")
        self.stream_config = None
        self.controller = None
        
        self.initialize_controller()
    
    def initialize_controller(self):
        """初始化推流控制器"""
        streaming_config = self.config.get("streaming", {})
        
        if self.platform == "tiktok":
            obs_config = streaming_config.get("obs", {})
            self.controller = OBSController(
                host=obs_config.get("host", "localhost"),
                port=obs_config.get("port", 4455),
                password=obs_config.get("password", "")
            )
            
        elif self.platform == "douyin":
            companion_config = streaming_config.get("douyin_companion", {})
            self.controller = DouyinLiveCompanionController(
                executable_path=companion_config.get("executable_path")
            )
    
    async def setup_streaming(self, video_source: str, audio_source: str = None) -> bool:
        """设置推流"""
        platform_config = self.config.get("platform", {})
        
        self.stream_config = StreamConfig(
            platform=self.platform,
            stream_url=platform_config.get("stream_url", ""),
            stream_key=platform_config.get("stream_key", ""),
            video_source=video_source,
            audio_source=audio_source or "",
            resolution="1920x1080",
            fps=30,
            bitrate=6000,
            audio_bitrate=128
        )
        
        # 检查控制器
        if not self.controller:
            logger.error("推流控制器未初始化")
            return False
        
        # 启动推流软件
        if hasattr(self.controller, "start_obs"):
            if not await self.controller.start_obs():
                return False
            
            # 连接WebSocket
            if not await self.controller.connect_websocket():
                return False
            
            # 设置推流参数
            if not await self.controller.set_stream_settings(
                self.stream_config.stream_url,
                self.stream_config.stream_key
            ):
                return False
            
            # 创建场景和视频源
            scene_name = "AI Digital Human"
            source_name = "Digital Human Video"
            
            if not await self.controller.create_scene(scene_name):
                return False
            
            if not await self.controller.add_video_source(
                scene_name, source_name, video_source
            ):
                return False
        
        elif hasattr(self.controller, "start_companion"):
            if not await self.controller.start_companion():
                return False
        
        return True
    
    async def start_streaming(self) -> bool:
        """开始推流"""
        if not self.controller:
            logger.error("推流控制器未初始化")
            return False
        
        if hasattr(self.controller, "start_streaming"):
            return await self.controller.start_streaming()
        
        return False
    
    async def stop_streaming(self) -> bool:
        """停止推流"""
        if not self.controller:
            return True
        
        if hasattr(self.controller, "stop_streaming"):
            return await self.controller.stop_streaming()
        
        return False
    
    async def get_status(self) -> Dict:
        """获取推流状态"""
        status = {
            "platform": self.platform,
            "controller_initialized": self.controller is not None,
            "streaming": False,
            "error": None
        }
        
        if self.controller:
            if hasattr(self.controller, "get_stream_status"):
                obs_status = await self.controller.get_stream_status()
                if obs_status:
                    status["streaming"] = obs_status.get("outputActive", False)
                    status["bytes_sent"] = obs_status.get("outputBytes", 0)
                    status["fps"] = obs_status.get("outputFps", 0)
            
            elif hasattr(self.controller, "is_running"):
                status["companion_running"] = self.controller.is_running()
        
        return status
    
    async def cleanup(self):
        """清理资源"""
        if self.controller:
            if hasattr(self.controller, "disconnect"):
                await self.controller.disconnect()
            
            if hasattr(self.controller, "stop_companion"):
                await self.controller.stop_companion()