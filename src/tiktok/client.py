#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TikTok官方开发者平台API客户端
100%合规，使用官方API和Webhook
"""

import os
import asyncio
import json
import logging
import time
import hmac
import hashlib
from typing import Dict, Optional, Any, List
import aiohttp
from datetime import datetime

logger = logging.getLogger(__name__)


class TikTokClient:
    """TikTok官方开发者平台客户端"""
    
    # TikTok API端点
    BASE_URL = "https://open.tiktokapis.com"
    OAUTH_TOKEN_URL = f"{BASE_URL}/v2/oauth/token/"
    LIVE_WEBHOOK_URL = f"{BASE_URL}/v2/live/webhook/"
    
    def __init__(self, config: Dict):
        """初始化TikTok客户端
        
        Args:
            config: 配置字典，必须包含:
                - TIKTOK_APP_ID: TikTok开发者应用ID
                - TIKTOK_APP_SECRET: TikTok开发者应用密钥
                - TIKTOK_ACCESS_TOKEN: 访问令牌（可选，可自动获取）
                - TIKTOK_ROOM_ID: 直播间ID
                - WEBHOOK_SECRET: Webhook签名密钥
        """
        self.config = config
        self.app_id = config.get('TIKTOK_APP_ID')
        self.app_secret = config.get('TIKTOK_APP_SECRET')
        self.access_token = config.get('TIKTOK_ACCESS_TOKEN')
        self.room_id = config.get('TIKTOK_ROOM_ID')
        self.webhook_secret = config.get('WEBHOOK_SECRET')
        
        # 验证必要配置
        if not all([self.app_id, self.app_secret]):
            raise ValueError("缺少必要的TikTok配置：TIKTOK_APP_ID, TIKTOK_APP_SECRET")
        
        # 认证状态
        self.token_expires_at = 0
        
        # HTTP会话
        self.session = None
        
        # Webhook状态
        self.webhook_registered = False
        self.webhook_url = None
        
        # 频率限制
        self.last_request_time = 0
        self.min_request_interval = 0.2  # 200ms请求间隔
        
        logger.info("TikTok客户端初始化完成")
    
    async def _ensure_session(self):
        """确保HTTP会话存在"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
    
    async def close(self):
        """关闭所有连接"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
        
        logger.info("TikTok客户端已关闭")
    
    def _check_rate_limit(self):
        """检查频率限制"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    async def get_access_token(self) -> str:
        """获取TikTok访问令牌
        
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
                "grant_type": "client_credentials"
            }
            
            async with self.session.post(self.OAUTH_TOKEN_URL, json=data) as response:
                if response.status != 200:
                    raise Exception(f"获取access_token失败，状态码: {response.status}")
                
                result = await response.json()
                
                if result.get("error", {}).get("code") != 0:
                    error_msg = result.get("error", {}).get("message", "未知错误")
                    raise Exception(f"获取access_token失败: {error_msg}")
                
                token_data = result["data"]
                self.access_token = token_data["access_token"]
                self.token_expires_at = time.time() + token_data["expires_in"] - 300  # 提前5分钟刷新
                
                logger.info("TikTok access_token获取成功")
                return self.access_token
                
        except Exception as e:
            logger.error(f"获取TikTok access_token失败: {e}")
            raise
    
    async def ensure_valid_token(self) -> str:
        """确保有有效的访问令牌"""
        if not self.access_token or time.time() >= self.token_expires_at:
            return await self.get_access_token()
        return self.access_token
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """验证Webhook签名
        
        Args:
            payload: 请求体原始字符串
            signature: 请求头中的签名
            
        Returns:
            True如果签名验证通过
        """
        if not self.webhook_secret:
            logger.warning("未配置WEBHOOK_SECRET，跳过签名验证")
            return True
        
        try:
            # 计算HMAC SHA256签名
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # 比较签名
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"验证Webhook签名失败: {e}")
            return False
    
    async def register_webhook(self, webhook_url: str, events: List[str] = None) -> bool:
        """注册Webhook
        
        Args:
            webhook_url: Webhook接收URL
            events: 要监听的事件列表，默认为所有直播事件
            
        Returns:
            True如果注册成功
        """
        self._check_rate_limit()
        
        try:
            access_token = await self.ensure_valid_token()
            
            await self._ensure_session()
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            if events is None:
                events = [
                    "live_comment",
                    "live_gift",
                    "live_like",
                    "live_share",
                    "live_follow",
                    "live_join"
                ]
            
            data = {
                "webhook_url": webhook_url,
                "events": events
            }
            
            async with self.session.post(self.LIVE_WEBHOOK_URL, json=data, headers=headers) as response:
                if response.status not in [200, 201]:
                    raise Exception(f"注册Webhook失败，状态码: {response.status}")
                
                result = await response.json()
                
                if result.get("error", {}).get("code") != 0:
                    error_msg = result.get("error", {}).get("message", "未知错误")
                    raise Exception(f"注册Webhook失败: {error_msg}")
                
                self.webhook_url = webhook_url
                self.webhook_registered = True
                
                logger.info(f"Webhook注册成功: {webhook_url}")
                logger.info(f"监听事件: {', '.join(events)}")
                return True
                
        except Exception as e:
            logger.error(f"注册Webhook失败: {e}")
            return False
    
    async def unregister_webhook(self) -> bool:
        """取消注册Webhook"""
        if not self.webhook_registered or not self.webhook_url:
            logger.warning("Webhook未注册，无需取消")
            return True
        
        self._check_rate_limit()
        
        try:
            access_token = await self.ensure_valid_token()
            
            await self._ensure_session()
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "webhook_url": self.webhook_url
            }
            
            async with self.session.delete(self.LIVE_WEBHOOK_URL, json=data, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"取消注册Webhook失败，状态码: {response.status}")
                
                result = await response.json()
                
                if result.get("error", {}).get("code") != 0:
                    error_msg = result.get("error", {}).get("message", "未知错误")
                    raise Exception(f"取消注册Webhook失败: {error_msg}")
                
                self.webhook_registered = False
                self.webhook_url = None
                
                logger.info("Webhook取消注册成功")
                return True
                
        except Exception as e:
            logger.error(f"取消注册Webhook失败: {e}")
            return False
    
    async def get_live_comments(self, limit: int = 50, cursor: str = None) -> Dict:
        """获取直播间评论（轮询方式）
        
        Args:
            limit: 每次获取的评论数量
            cursor: 分页游标
            
        Returns:
            评论数据字典
        """
        self._check_rate_limit()
        
        try:
            access_token = await self.ensure_valid_token()
            
            await self._ensure_session()
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            params = {
                "room_id": self.room_id,
                "limit": limit
            }
            
            if cursor:
                params["cursor"] = cursor
            
            url = f"{self.BASE_URL}/v2/live/comment/list/"
            
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"获取评论失败，状态码: {response.status}")
                
                result = await response.json()
                
                if result.get("error", {}).get("code") != 0:
                    error_msg = result.get("error", {}).get("message", "未知错误")
                    raise Exception(f"获取评论失败: {error_msg}")
                
                return result.get("data", {})
                
        except Exception as e:
            logger.error(f"获取直播间评论失败: {e}")
            return {}
    
    async def get_live_info(self) -> Dict:
        """获取直播间信息
        
        Returns:
            直播间信息字典
        """
        self._check_rate_limit()
        
        try:
            access_token = await self.ensure_valid_token()
            
            await self._ensure_session()
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            params = {"room_id": self.room_id}
            url = f"{self.BASE_URL}/v2/live/room/info/"
            
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"获取直播间信息失败，状态码: {response.status}")
                
                result = await response.json()
                
                if result.get("error", {}).get("code") != 0:
                    error_msg = result.get("error", {}).get("message", "未知错误")
                    raise Exception(f"获取直播间信息失败: {error_msg}")
                
                return result.get("data", {})
                
        except Exception as e:
            logger.error(f"获取直播间信息失败: {e}")
            return {}
    
    async def send_chat_message(self, content: str, reply_to: str = None) -> bool:
        """发送聊天消息（需要特殊权限）
        
        Args:
            content: 消息内容
            reply_to: 回复的评论ID（可选）
            
        Returns:
            True如果发送成功
            
        Note:
            此功能需要额外权限，普通应用可能无法使用
        """
        self._check_rate_limit()
        
        try:
            access_token = await self.ensure_valid_token()
            
            await self._ensure_session()
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "room_id": self.room_id,
                "content": content
            }
            
            if reply_to:
                data["reply_to"] = reply_to
            
            url = f"{self.BASE_URL}/v2/live/comment/create/"
            
            async with self.session.post(url, json=data, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"发送消息失败，状态码: {response.status}")
                
                result = await response.json()
                
                if result.get("error", {}).get("code") != 0:
                    error_msg = result.get("error", {}).get("message", "未知错误")
                    raise Exception(f"发送消息失败: {error_msg}")
                
                logger.info(f"消息发送成功: {content[:50]}...")
                return True
                
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            return False
    
    async def get_streaming_url(self) -> Dict:
        """获取推流地址
        
        Returns:
            推流地址信息字典
        """
        self._check_rate_limit()
        
        try:
            access_token = await self.ensure_valid_token()
            
            await self._ensure_session()
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            params = {"room_id": self.room_id}
            url = f"{self.BASE_URL}/v2/live/stream/url/"
            
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"获取推流地址失败，状态码: {response.status}")
                
                result = await response.json()
                
                if result.get("error", {}).get("code") != 0:
                    error_msg = result.get("error", {}).get("message", "未知错误")
                    raise Exception(f"获取推流地址失败: {error_msg}")
                
                stream_info = result.get("data", {})
                
                logger.info(f"获取到推流地址: {stream_info.get('rtmp_url', 'N/A')[:50]}...")
                return stream_info
                
        except Exception as e:
            logger.error(f"获取推流地址失败: {e}")
            return {}
    
    def process_webhook_event(self, event_data: Dict) -> Dict:
        """处理Webhook事件
        
        Args:
            event_data: Webhook事件数据
            
        Returns:
            标准化的事件信息
        """
        event_type = event_data.get("event")
        data = event_data.get("data", {})
        
        base_info = {
            "type": event_type,
            "timestamp": event_data.get("timestamp", int(time.time() * 1000)),
            "room_id": data.get("room_id", self.room_id)
        }
        
        if event_type == "live_comment":
            # 评论事件
            user_info = data.get("user", {})
            comment_info = data.get("comment", {})
            
            return {
                **base_info,
                "nickname": user_info.get("nickname", "Unknown User"),
                "content": comment_info.get("content", ""),
                "user_id": user_info.get("id", ""),
                "comment_id": comment_info.get("id", ""),
                "is_owner": user_info.get("is_owner", False)
            }
            
        elif event_type == "live_gift":
            # 礼物事件
            user_info = data.get("user", {})
            gift_info = data.get("gift", {})
            
            return {
                **base_info,
                "nickname": user_info.get("nickname", "Unknown User"),
                "gift_name": gift_info.get("name", ""),
                "gift_count": gift_info.get("count", 1),
                "gift_value": gift_info.get("value", 0),
                "user_id": user_info.get("id", ""),
                "gift_id": gift_info.get("id", "")
            }
            
        elif event_type == "live_like":
            # 点赞事件
            user_info = data.get("user", {})
            
            return {
                **base_info,
                "nickname": user_info.get("nickname", "Unknown User"),
                "like_count": data.get("like_count", 1),
                "user_id": user_info.get("id", ""),
                "total_likes": data.get("total_likes", 0)
            }
            
        elif event_type == "live_share":
            # 分享事件
            user_info = data.get("user", {})
            
            return {
                **base_info,
                "nickname": user_info.get("nickname", "Unknown User"),
                "user_id": user_info.get("id", ""),
                "share_type": data.get("share_type", "unknown")
            }
            
        elif event_type == "live_follow":
            # 关注事件
            user_info = data.get("user", {})
            
            return {
                **base_info,
                "nickname": user_info.get("nickname", "Unknown User"),
                "user_id": user_info.get("id", ""),
                "follower_count": data.get("follower_count", 0)
            }
            
        elif event_type == "live_join":
            # 加入直播间事件
            user_info = data.get("user", {})
            
            return {
                **base_info,
                "nickname": user_info.get("nickname", "Unknown User"),
                "user_id": user_info.get("id", ""),
                "viewer_count": data.get("viewer_count", 0)
            }
            
        else:
            # 未知事件类型
            return {
                **base_info,
                "raw_data": event_data
            }


# Webhook服务器示例
async def webhook_server_example():
    """Webhook服务器示例"""
    from fastapi import FastAPI, Request, HTTPException
    import uvicorn
    
    app = FastAPI()
    
    # 初始化客户端
    config = {
        "TIKTOK_APP_ID": "your_app_id",
        "TIKTOK_APP_SECRET": "your_app_secret",
        "TIKTOK_ROOM_ID": "your_room_id",
        "WEBHOOK_SECRET": "your_webhook_secret"
    }
    
    client = TikTokClient(config)
    
    @app.post("/tiktok/webhook")
    async def handle