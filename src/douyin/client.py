#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音官方开放平台API客户端
100%合规，禁止任何第三方协议/抓包
"""

import os
import asyncio
import json
import logging
import time
from typing import Dict, Optional, Any
import aiohttp
import websockets

logger = logging.getLogger(__name__)


class DouyinClient:
    """抖音官方开放平台客户端"""
    
    # 官方API端点
    BASE_URL = "https://open.douyin.com"
    OAUTH_TOKEN_URL = f"{BASE_URL}/oauth/client_token"
    LIVE_WEBSOCKET_URL = f"{BASE_URL}/api/gateway/v2/live/room/websocket"
    
    def __init__(self, config: Dict):
        """初始化抖音客户端
        
        Args:
            config: 配置字典，必须包含:
                - DOUYIN_APP_ID: 抖音开放平台应用ID
                - DOUYIN_APP_SECRET: 抖音开放平台应用密钥
                - ROOM_ID: 直播间ID
        """
        self.config = config
        self.app_id = config.get('DOUYIN_APP_ID')
        self.app_secret = config.get('DOUYIN_APP_SECRET')
        self.room_id = config.get('ROOM_ID')
        
        # 验证必要配置
        if not all([self.app_id, self.app_secret, self.room_id]):
            raise ValueError("缺少必要的抖音配置：DOUYIN_APP_ID, DOUYIN_APP_SECRET, ROOM_ID")
        
        # 认证状态
        self.access_token = None
        self.token_expires_at = 0
        
        # WebSocket连接
        self.websocket = None
        self.connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        
        # 频率限制
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms请求间隔
        
        # HTTP会话
        self.session = None
        
        logger.info("抖音客户端初始化完成")
    
    async def _ensure_session(self):
        """确保HTTP会话存在"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
    
    async def close(self):
        """关闭所有连接"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            self.connected = False
        
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
        
        logger.info("抖音客户端已关闭")
    
    def _check_rate_limit(self):
        """检查频率限制"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    async def get_access_token(self) -> str:
        """获取抖音开放平台访问令牌
        
        Returns:
            access_token字符串
            
        Raises:
            Exception: 获取令牌失败
        """
        self._check_rate_limit()
        
        try:
            await self._ensure_session()
            
            data = {
                "client_key": self.app_id,
                "client_secret": self.app_secret,
                "grant_type": "client_credential"
            }
            
            async with self.session.post(self.OAUTH_TOKEN_URL, json=data) as response:
                if response.status != 200:
                    raise Exception(f"获取access_token失败，状态码: {response.status}")
                
                result = await response.json()
                
                if result.get("error_code") != 0:
                    raise Exception(f"获取access_token失败: {result.get('description')}")
                
                token_data = result["data"]
                self.access_token = token_data["access_token"]
                self.token_expires_at = time.time() + token_data["expires_in"] - 300  # 提前5分钟刷新
                
                logger.info("抖音access_token获取成功")
                return self.access_token
                
        except Exception as e:
            logger.error(f"获取抖音access_token失败: {e}")
            raise
    
    async def ensure_valid_token(self) -> str:
        """确保有有效的访问令牌"""
        if not self.access_token or time.time() >= self.token_expires_at:
            return await self.get_access_token()
        return self.access_token
    
    async def get_live_websocket_url(self) -> str:
        """获取直播间WebSocket连接地址
        
        Returns:
            WebSocket连接URL
            
        Raises:
            Exception: 获取失败
        """
        self._check_rate_limit()
        
        try:
            access_token = await self.ensure_valid_token()
            
            await self._ensure_session()
            
            headers = {
                "access-token": access_token,
                "Content-Type": "application/json"
            }
            
            params = {
                "room_id": self.room_id
            }
            
            async with self.session.get(
                self.LIVE_WEBSOCKET_URL,
                headers=headers,
                params=params
            ) as response:
                if response.status != 200:
                    raise Exception(f"获取WebSocket URL失败，状态码: {response.status}")
                
                result = await response.json()
                
                if result.get("error_code") != 0:
                    raise Exception(f"获取WebSocket URL失败: {result.get('description')}")
                
                websocket_url = result["data"]["websocket_url"]
                logger.info(f"获取到直播间WebSocket URL: {websocket_url[:50]}...")
                return websocket_url
                
        except Exception as e:
            logger.error(f"获取直播间WebSocket URL失败: {e}")
            raise
    
    async def connect_to_live_room(self):
        """连接到直播间WebSocket"""
        try:
            if self.connected and self.websocket:
                logger.info("已连接到直播间")
                return
            
            websocket_url = await self.get_live_websocket_url()
            
            # 连接WebSocket
            self.websocket = await websockets.connect(
                websocket_url,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=5
            )
            
            self.connected = True
            self.reconnect_attempts = 0
            
            logger.info("✅ 已成功连接到抖音官方直播间")
            
            # 发送连接确认消息
            connect_msg = {
                "method": "connect",
                "room_id": self.room_id,
                "timestamp": int(time.time() * 1000)
            }
            await self.websocket.send(json.dumps(connect_msg))
            
        except Exception as e:
            self.connected = False
            logger.error(f"连接直播间失败: {e}")
            raise
    
    async def listen_for_messages(self, callback):
        """监听直播间消息
        
        Args:
            callback: 消息回调函数，接收消息字典
        """
        if not self.connected or not self.websocket:
            await self.connect_to_live_room()
        
        try:
            logger.info("开始监听直播间消息...")
            
            while self.connected:
                try:
                    # 接收消息
                    message = await self.websocket.recv()
                    
                    # 解析消息
                    try:
                        data = json.loads(message)
                        
                        # 处理不同类型的消息
                        await self._handle_message(data, callback)
                        
                    except json.JSONDecodeError:
                        logger.warning(f"收到非JSON消息: {message[:100]}")
                        
                except websockets.exceptions.ConnectionClosed:
                    logger.warning("WebSocket连接已关闭，尝试重连...")
                    await self._reconnect()
                    
                except Exception as e:
                    logger.error(f"处理消息时出错: {e}")
                    # 短暂延迟后继续
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(f"监听消息失败: {e}")
            raise
    
    async def _handle_message(self, data: Dict, callback):
        """处理收到的消息"""
        method = data.get("method")
        
        if method == "webcast_chat_message":
            # 弹幕消息
            payload = data.get("data", {})
            user_info = payload.get("user", {})
            
            message_info = {
                "type": "chat_message",
                "nickname": user_info.get("nickname", "未知用户"),
                "content": payload.get("content", ""),
                "user_id": user_info.get("id", ""),
                "timestamp": payload.get("timestamp", int(time.time() * 1000)),
                "room_id": self.room_id
            }
            
            logger.info(f"💬 弹幕: {message_info['nickname']}: {message_info['content']}")
            await callback(message_info)
            
        elif method == "webcast_gift_message":
            # 礼物消息
            payload = data.get("data", {})
            user_info = payload.get("user", {})
            
            message_info = {
                "type": "gift_message",
                "nickname": user_info.get("nickname", "未知用户"),
                "gift_name": payload.get("gift_name", ""),
                "gift_count": payload.get("gift_count", 1),
                "gift_value": payload.get("gift_value", 0),
                "user_id": user_info.get("id", ""),
                "timestamp": payload.get("timestamp", int(time.time() * 1000)),
                "room_id": self.room_id
            }
            
            logger.info(f"🎁 礼物: {message_info['nickname']} 赠送了 {message_info['gift_name']} x{message_info['gift_count']}")
            await callback(message_info)
            
        elif method == "webcast_like_message":
            # 点赞消息
            payload = data.get("data", {})
            user_info = payload.get("user", {})
            
            message_info = {
                "type": "like_message",
                "nickname": user_info.get("nickname", "未知用户"),
                "like_count": payload.get("like_count", 1),
                "user_id": user_info.get("id", ""),
                "timestamp": payload.get("timestamp", int(time.time() * 1000)),
                "room_id": self.room_id
            }
            
            logger.info(f"👍 点赞: {message_info['nickname']} 点赞 x{message_info['like_count']}")
            await callback(message_info)
            
        elif method == "heartbeat":
            # 心跳响应
            logger.debug("❤️ 收到心跳响应")
            
        elif method == "error":
            # 错误消息
            error_msg = data.get("data", {}).get("message", "未知错误")
            logger.error(f"❌ 收到错误消息: {error_msg}")
            
        else:
            # 其他消息类型
            logger.debug(f"收到未知类型消息: {method}")
    
    async def _reconnect(self):
        """重新连接"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error("达到最大重连次数，停止重连")
            self.connected = False
            return False
        
        self.reconnect_attempts += 1
        retry_delay = min(2 ** self.reconnect_attempts, 60)  # 指数退避
        
        logger.info(f"第 {self.reconnect_attempts} 次重连，等待 {retry_delay} 秒...")
        await asyncio.sleep(retry_delay)
        
        try:
            await self.connect_to_live_room()
            return True
        except Exception as e:
            logger.error(f"重连失败: {e}")
            return False
    
    async def send_chat_message(self, content: str):
        """发送聊天消息（需要特殊权限）
        
        Args:
            content: 消息内容
            
        Note:
            此功能需要额外权限，普通应用可能无法使用
        """
        if not self.connected or not self.websocket:
            raise Exception("未连接到直播间")
        
        try:
            message = {
                "method": "send_chat_message",
                "data": {
                    "content": content,
                    "room_id": self.room_id,
                    "timestamp": int(time.time() * 1000)
                }
            }
            
            await self.websocket.send(json.dumps(message))
            logger.info(f"已发送消息: {content}")
            
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            raise
    
    async def get_live_room_info(self) -> Dict:
        """获取直播间信息
        
        Returns:
            直播间信息字典
        """
        self._check_rate_limit()
        
        try:
            access_token = await self.ensure_valid_token()
            
            await self._ensure_session()
            
            headers = {
                "access-token": access_token,
                "Content-Type": "application/json"
            }
            
            # 注意：实际API端点可能需要调整
            url = f"{self.BASE_URL}/api/live/v2/room/info"
            params = {"room_id": self.room_id}
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status != 200:
                    raise Exception(f"获取直播间信息失败，状态码: {response.status}")
                
                result = await response.json()
                
                if result.get("error_code") != 0:
                    raise Exception(f"获取直播间信息失败: {result.get('description')}")
                
                return result.get("data", {})
                
        except Exception as e:
            logger.error(f"获取直播间信息失败: {e}")
            return {}


# 使用示例
async def example_usage():
    """使用示例"""
    config = {
        "DOUYIN_APP_ID": "your_app_id",
        "DOUYIN_APP_SECRET": "your_app_secret",
        "ROOM_ID": "your_room_id"
    }
    
    client = DouyinClient(config)
    
    async def message_callback(message):
        """消息回调函数"""
        print(f"收到消息: {message}")
        
        if message["type"] == "chat_message":
            # 这里可以调用AI生成回复
            reply = f"感谢 {message['nickname']} 的发言: {message['content']}"
            print(f"AI回复: {reply}")
    
    try:
        # 连接到直播间
        await client.connect_to_live_room()
        
        # 开始监听消息
        await client.listen_for_messages(message_callback)
        
    except KeyboardInterrupt:
        print("用户中断")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(example_usage())