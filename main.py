#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI数字人直播系统 - 主程序入口
开箱即用的完整直播系统
"""

import asyncio
import json
import os
import sys
import signal
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ai_digital_human_live_system import AIDigitalHumanLiveSystem
from api_clients import APIManager
from streaming_controller import StreamingManager
from database_manager import DatabaseManager
from content_filter import ContentFilter
from prompt_manager import PromptManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class AIDigitalHumanLiveApp:
    """AI数字人直播应用"""
    
    def __init__(self, config_path: str = "config/config.json"):
        self.config_path = config_path
        self.config = self.load_config()
        self.running = False
        
        # 初始化各模块
        self.database = DatabaseManager()
        self.content_filter = ContentFilter()
        self.prompt_manager = PromptManager()
        self.api_manager = APIManager(self.config)
        self.streaming_manager = StreamingManager(self.config)
        self.live_system = AIDigitalHumanLiveSystem(config_path)
        
        # 状态监控
        self.start_time = None
        self.interaction_count = 0
        self.error_count = 0
        
        # 信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            sys.exit(1)
    
    def signal_handler(self, signum, frame):
        """信号处理"""
        logger.info(f"收到信号 {signum}，正在关闭...")
        self.running = False
    
    async def initialize(self) -> bool:
        """初始化系统"""
        logger.info("正在初始化AI数字人直播系统...")
        
        try:
            # 1. 检查配置
            if not self.check_config():
                return False
            
            # 2. 初始化数据库
            logger.info("初始化数据库...")
            # 数据库已在构造函数中初始化
            
            # 3. 测试API连接
            logger.info("测试API连接...")
            if not await self.test_api_connections():
                return False
            
            # 4. 初始化推流
            logger.info("初始化推流系统...")
            if not await self.initialize_streaming():
                return False
            
            # 5. 记录启动日志
            self.database.log_system_event(
                level="INFO",
                module="main",
                message="系统启动成功",
                details=json.dumps({
                    "config_path": self.config_path,
                    "platform": self.config.get("platform", {}).get("type", "unknown")
                })
            )
            
            logger.info("系统初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"系统初始化失败: {e}")
            self.database.log_system_event(
                level="ERROR",
                module="main",
                message="系统初始化失败",
                details=str(e)
            )
            return False
    
    def check_config(self) -> bool:
        """检查配置"""
        required_sections = ["platform", "apis", "content_filter"]
        
        for section in required_sections:
            if section not in self.config:
                logger.error(f"配置缺少必要部分: {section}")
                return False
        
        # 检查平台配置
        platform_config = self.config["platform"]
        required_platform_fields = ["type", "room_id", "stream_url", "stream_key"]
        
        for field in required_platform_fields:
            if not platform_config.get(field):
                logger.error(f"平台配置缺少字段: {field}")
                return False
        
        # 检查API配置
        api_config = self.config["apis"]
        required_apis = ["llm", "tts", "digital_human", "danmaku"]
        
        for api in required_apis:
            if api not in api_config:
                logger.error(f"API配置缺少: {api}")
                return False
            
            api_config_section = api_config[api]
            if not api_config_section.get("api_key"):
                logger.warning(f"API {api} 缺少api_key，部分功能可能不可用")
        
        return True
    
    async def test_api_connections(self) -> bool:
        """测试API连接"""
        try:
            # 测试LLM API
            llm_client = self.api_manager.get_client("llm")
            if llm_client:
                test_prompt = "Hello, this is a connection test."
                response = await llm_client.generate_text(test_prompt)
                if "[LLM错误]" in response:
                    logger.warning(f"LLM API连接测试失败: {response}")
                else:
                    logger.info("LLM API连接测试成功")
            
            # 测试弹幕API
            danmaku_client = self.api_manager.get_client("danmaku")
            if danmaku_client:
                # 尝试获取弹幕（可能为空）
                messages = await danmaku_client.get_danmaku(limit=1)
                logger.info(f"弹幕API连接测试成功，获取到 {len(messages)} 条消息")
            
            return True
            
        except Exception as e:
            logger.error(f"API连接测试失败: {e}")
            return False
    
    async def initialize_streaming(self) -> bool:
        """初始化推流"""
        try:
            # 检查推流配置
            platform = self.config["platform"]["type"]
            
            if platform == "tiktok":
                # TikTok使用OBS
                if not self.streaming_manager.controller.is_obs_installed():
                    logger.error("未找到OBS Studio，请先安装")
                    return False
                
                # 测试视频源
                test_video_source = "assets/test_video.mp4"
                if not os.path.exists(test_video_source):
                    logger.warning(f"测试视频文件不存在: {test_video_source}")
                    # 创建占位视频
                    self.create_test_video(test_video_source)
                
                # 设置推流
                if not await self.streaming_manager.setup_streaming(test_video_source):
                    logger.error("推流设置失败")
                    return False
                
            elif platform == "douyin":
                # 抖音使用直播伴侣
                if not self.streaming_manager.controller.is_installed():
                    logger.error("未找到抖音直播伴侣，请先安装")
                    return False
            
            logger.info("推流系统初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"推流初始化失败: {e}")
            return False
    
    def create_test_video(self, output_path: str):
        """创建测试视频"""
        try:
            import cv2
            import numpy as np
            
            # 创建简单的测试视频
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 创建黑色背景视频
            width, height = 1920, 1080
            fps = 30
            duration = 10  # 10秒
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            for i in range(fps * duration):
                # 创建帧
                frame = np.zeros((height, width, 3), dtype=np.uint8)
                
                # 添加文字
                text = "AI Digital Human Live System"
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 2
                thickness = 3
                
                text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
                text_x = (width - text_size[0]) // 2
                text_y = (height + text_size[1]) // 2
                
                cv2.putText(frame, text, (text_x, text_y), font, font_scale, 
                           (255, 255, 255), thickness, cv2.LINE_AA)
                
                out.write(frame)
            
            out.release()
            logger.info(f"已创建测试视频: {output_path}")
            
        except ImportError:
            logger.warning("OpenCV未安装，无法创建测试视频")
            # 创建空文件
            with open(output_path, 'wb') as f:
                f.write(b'')
    
    async def run(self):
        """运行主循环"""
        logger.info("启动AI数字人直播系统...")
        self.start_time = datetime.now()
        self.running = True
        
        try:
            # 1. 开始推流
            logger.info("开始推流...")
            if not await self.streaming_manager.start_streaming():
                logger.error("推流启动失败")
                return
            
            # 2. 启动弹幕监听
            logger.info("启动弹幕监听...")
            danmaku_task = asyncio.create_task(self.listen_danmaku())
            
            # 3. 启动保持活跃任务
            logger.info("启动保持活跃任务...")
            keepalive_task = asyncio.create_task(self.run_keepalive_tasks())
            
            # 4. 启动监控任务
            logger.info("启动系统监控...")
            monitor_task = asyncio.create_task(self.monitor_system())
            
            # 5. 等待停止信号
            logger.info("系统运行中，按Ctrl+C停止...")
            while self.running:
                await asyncio.sleep(1)
            
            # 6. 清理任务
            logger.info("正在停止系统...")
            danmaku_task.cancel()
            keepalive_task.cancel()
            monitor_task.cancel()
            
            # 等待任务结束
            try:
                await asyncio.gather(danmaku_task, keepalive_task, monitor_task, 
                                   return_exceptions=True)
            except asyncio.CancelledError:
                pass
            
            # 7. 停止推流
            logger.info("停止推流...")
            await self.streaming_manager.stop_streaming()
            
            # 8. 关闭API连接
            logger.info("关闭API连接...")
            await self.api_manager.close_all()
            
            # 9. 记录关闭日志
            runtime = (datetime.now() - self.start_time).total_seconds()
            self.database.log_system_event(
                level="INFO",
                module="main",
                message="系统正常关闭",
                details=json.dumps({
                    "runtime_seconds": runtime,
                    "interaction_count": self.interaction_count,
                    "error_count": self.error_count
                })
            )
            
            logger.info(f"系统运行时间: {runtime:.1f}秒")
            logger.info(f"处理交互: {self.interaction_count}次")
            logger.info(f"错误次数: {self.error_count}")
            
        except Exception as e:
            logger.error(f"系统运行异常: {e}")
            self.database.log_system_event(
                level="ERROR",
                module="main",
                message="系统运行异常",
                details=str(e)
            )
    
    async def listen_danmaku(self):
        """监听弹幕"""
        danmaku_client = self.api_manager.get_client("danmaku")
        
        if not danmaku_client:
            logger.error("弹幕客户端未初始化")
            return
        
        logger.info("开始监听弹幕...")
        
        while self.running:
            try:
                # 获取弹幕
                messages = await danmaku_client.get_danmaku(limit=10)
                
                for message in messages:
                    # 处理弹幕
                    result = await self.live_system.process_danmaku(message)
                    
                    if result and result.get("should_respond"):
                        # 生成数字人回复
                        await self.generate_digital_human_response(result)
                        
                        # 更新统计
                        self.interaction_count += 1
                
                # 等待下一次轮询
                poll_interval = self.config["apis"]["danmaku"].get("poll_interval", 3)
                await asyncio.sleep(poll_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"弹幕监听异常: {e}")
                self.error_count += 1
                await asyncio.sleep(5)  # 错误后等待5秒
    
    async def generate_digital_human_response(self, result: Dict):
        """生成数字人回复"""
        try:
            # 1. 生成TTS音频
            tts_client = self.api_manager.get_client("tts")
            if tts_client:
                audio_data = await tts_client.generate_speech(result["ai_response"])
                if audio_data:
                    # 保存音频文件
                    audio_path = f"temp/audio_{int(time.time())}.mp3"
                    with open(audio_path, 'wb') as f:
                        f.write(audio_data)
                    
                    # 2. 生成数字人视频
                    dh_client = self.api_manager.get_client("digital_human")
                    if dh_client:
                        talk_id = await dh_client.create_talk(
                            script=result["ai_response"],
                            audio_url=f"file://{os.path.abspath(audio_path)}"
                        )
                        
                        if talk_id:
                            # 等待视频生成
                            video_url = await self.wait_for_digital_human_video(dh_client, talk_id)
                            if video_url:
                                # 3. 更新推流视频源
                                await self.update_streaming_source(video_url)
            
        except Exception as e:
            logger.error(f"生成数字人回复失败: {e}")
    
    async def wait_for_digital_human_video(self, dh_client, talk_id: str, 
                                         timeout: int = 60) -> Optional[str]:
        """等待数字人视频生成"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = await dh_client.get_talk_status(talk_id)
            
            if status:
                status_value = status.get("status")
                
                if status_value == "done":
                    return status.get("result_url")
                elif status_value == "failed":
                    logger.error(f"数字人视频生成失败: {status.get('error')}")
                    return None
            
            await asyncio.sleep(2)
        
        logger.error(f"数字人视频生成超时: {timeout}秒")
        return None
    
    async def update_streaming_source(self, video_url: str):
        """更新推流视频源"""
        try:
            # 下载视频文件
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get(video_url) as response:
                    if response.status == 200:
                        video_data = await response.read()
                        
                        # 保存视频文件
                        video_path = f"temp/video_{int(time.time())}.mp4"
                        with open(video_path, 'wb') as f:
                            f.write(video_data)
                        
                        # 更新OBS视频源
                        if hasattr(self.streaming_manager.controller, "add_video_source"):
                            await self.streaming_manager.controller.add_video_source(
                                scene_name="AI Digital Human",
                                source_name="Digital Human Video",
                                video_path=video_path
                            )
            
        except Exception as e:
            logger.error(f"更新推流视频源失败: {e}")
    
    async def run_keepalive_tasks(self):
        """运行保持活跃任务"""
        while self.running:
            try:
                # 发送保持活跃消息
                await self.live_system.send_keepalive_message()
                
                # 更新促销信息
                await self.live_system.update_promotion_info()
                
                # 等待下一次执行
                interval = self.config.get("scheduler", {}).get("keepalive_interval", 300)
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"保持活跃任务异常: {e}")
                await asyncio.sleep(60)
    
    async def monitor_system(self):
        """监控系统状态"""
        while self.running:
            try:
                # 检查系统健康
                await self.live_system.check_system_health()
                
                # 获取API统计
                api_stats = self.api_manager.get_stats()
                
                # 获取推流状态
                stream_status = await self.streaming_manager.get_status()
                
                # 记录监控数据
                self.database.log_system_event(
                    level="INFO",
                    module="monitor",
                    message="系统状态检查",
                    details=json.dumps({
                        "api_stats": api_stats,
                        "stream_status": stream_status,
                        "interaction_count": self.interaction_count,
                        "uptime_seconds": (datetime.now() - self.start_time).total_seconds()
                    })
                )
                
                # 检查是否需要重启
                if self.should_restart():
                    logger.warning("检测到系统异常，准备重启...")
                    self.running = False
                
                # 等待下一次检查
                interval = self.config.get("monitoring", {}).get("health_check_interval", 60)
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"系统监控异常: {e}")
                await asyncio.sleep(30)
    
    def should_restart(self) -> bool:
        """检查是否需要重启"""
        # 检查错误率
        if self.interaction_count > 0:
            error_rate = self.error_count / self.interaction_count
            if error_rate > 0.5:  # 错误率超过50%
                return True
        
        # 检查API错误
        api_stats = self.api_manager.get_stats()
        for api_name, stats in api_stats.items():
            if