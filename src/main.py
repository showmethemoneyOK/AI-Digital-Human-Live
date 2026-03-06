#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI数字人直播系统 - 主程序入口
支持抖音/TikTok双平台合规方案
"""

import os
import sys
import asyncio
import json
import logging
import time
from typing import Dict, Optional
from pathlib import Path

# 添加src目录到Python路径
sys.path.append(str(Path(__file__).parent))

from douyin.client import DouyinClient
from tiktok.client import TikTokClient
from core.ai_processor import AIProcessor
from core.tts_service import TTSService
from core.digital_human import DigitalHuman
from core.compliance_checker import ComplianceChecker

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


class AIDigitalHumanLiveSystem:
    """AI数字人直播系统主控制器"""
    
    def __init__(self, platform: str = "douyin", config_path: str = "config/config.json"):
        """初始化系统
        
        Args:
            platform: 平台类型，douyin或tiktok
            config_path: 配置文件路径
        """
        self.platform = platform.lower()
        self.config_path = config_path
        self.config = self._load_config()
        
        # 系统状态
        self.running = False
        self.start_time = None
        self.message_count = 0
        self.reply_count = 0
        
        # 初始化组件
        self._init_components()
        
        logger.info(f"AI数字人直播系统初始化完成，平台: {self.platform}")
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 根据平台选择配置
            platform_config = config.get(self.platform, {})
            general_config = config.get("general", {})
            
            # 合并配置
            merged_config = {**general_config, **platform_config}
            
            # 加载环境变量
            self._load_env_variables(merged_config)
            
            logger.info(f"配置文件加载成功: {self.config_path}")
            return merged_config
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            sys.exit(1)
    
    def _load_env_variables(self, config: Dict):
        """加载环境变量到配置中"""
        env_mapping = {
            "DOUYIN_APP_ID": "DOUYIN_APP_ID",
            "DOUYIN_APP_SECRET": "DOUYIN_APP_SECRET",
            "TIKTOK_APP_ID": "TIKTOK_APP_ID",
            "TIKTOK_APP_SECRET": "TIKTOK_APP_SECRET",
            "TIKTOK_ACCESS_TOKEN": "TIKTOK_ACCESS_TOKEN",
            "AI_API_KEY": "AI_API_KEY",
            "TTS_API_KEY": "TTS_API_KEY",
            "DIGITAL_HUMAN_API_KEY": "DIGITAL_HUMAN_API_KEY"
        }
        
        for env_key, config_key in env_mapping.items():
            env_value = os.getenv(env_key)
            if env_value and config_key not in config:
                config[config_key] = env_value
                logger.debug(f"从环境变量加载: {config_key}")
    
    def _init_components(self):
        """初始化各组件"""
        try:
            # 1. 合规检查器
            self.compliance_checker = ComplianceChecker(self.config)
            
            # 2. AI处理器
            self.ai_processor = AIProcessor(self.config)
            
            # 3. TTS服务
            self.tts_service = TTSService(self.config)
            
            # 4. 数字人接口
            self.digital_human = DigitalHuman(self.config)
            
            # 5. 平台客户端
            if self.platform == "douyin":
                self.platform_client = DouyinClient(self.config)
                logger.info("使用抖音客户端")
            elif self.platform == "tiktok":
                self.platform_client = TikTokClient(self.config)
                logger.info("使用TikTok客户端")
            else:
                raise ValueError(f"不支持的平台: {self.platform}")
            
            logger.info("所有组件初始化完成")
            
        except Exception as e:
            logger.error(f"初始化组件失败: {e}")
            raise
    
    async def start(self):
        """启动系统"""
        try:
            logger.info("正在启动AI数字人直播系统...")
            
            # 1. 合规检查
            await self._check_compliance()
            
            # 2. 启动各组件
            await self._start_components()
            
            # 3. 连接到平台
            await self._connect_to_platform()
            
            # 4. 开始主循环
            self.running = True
            self.start_time = time.time()
            
            logger.info("✅ 系统启动成功，开始运行...")
            await self._main_loop()
            
        except KeyboardInterrupt:
            logger.info("收到中断信号，正在关闭...")
        except Exception as e:
            logger.error(f"系统运行失败: {e}")
        finally:
            await self.stop()
    
    async def _check_compliance(self):
        """检查合规性"""
        logger.info("进行合规检查...")
        
        compliance_result = await self.compliance_checker.check_all()
        
        if not compliance_result["passed"]:
            errors = compliance_result.get("errors", [])
            for error in errors:
                logger.error(f"合规检查失败: {error}")
            
            raise Exception("合规检查未通过，请修正配置后重试")
        
        logger.info("✅ 合规检查通过")
    
    async def _start_components(self):
        """启动各组件"""
        logger.info("启动各组件...")
        
        # 启动TTS服务
        await self.tts_service.initialize()
        
        # 启动数字人
        await self.digital_human.initialize()
        
        logger.info("✅ 组件启动完成")
    
    async def _connect_to_platform(self):
        """连接到平台"""
        logger.info(f"连接到{self.platform}平台...")
        
        if self.platform == "douyin":
            # 抖音：连接到WebSocket
            await self.platform_client.connect_to_live_room()
            
        elif self.platform == "tiktok":
            # TikTok：注册Webhook
            webhook_url = self.config.get("WEBHOOK_URL")
            if not webhook_url:
                raise ValueError("TikTok模式需要配置WEBHOOK_URL")
            
            events = self.config.get("WEBHOOK_EVENTS", [
                "live_comment",
                "live_gift",
                "live_like"
            ])
            
            await self.platform_client.register_webhook(webhook_url, events)
        
        logger.info(f"✅ 已连接到{self.platform}平台")
    
    async def _main_loop(self):
        """主循环"""
        logger.info("进入主循环...")
        
        if self.platform == "douyin":
            # 抖音：WebSocket监听模式
            await self._douyin_listen_loop()
        elif self.platform == "tiktok":
            # TikTok：Webhook模式，这里只是保持运行
            await self._tiktok_keepalive_loop()
    
    async def _douyin_listen_loop(self):
        """抖音监听循环"""
        try:
            await self.platform_client.listen_for_messages(self._handle_message)
        except Exception as e:
            logger.error(f"抖音监听循环异常: {e}")
            raise
    
    async def _tiktok_keepalive_loop(self):
        """TikTok保活循环"""
        logger.info("TikTok Webhook模式已启动，等待接收事件...")
        logger.info("请确保Webhook服务器正在运行并已正确配置")
        
        # 保持运行，等待Webhook事件
        while self.running:
            try:
                # 定期检查连接状态
                await asyncio.sleep(60)
                
                # 可以在这里添加定期任务，如发送心跳等
                if time.time() - self.start_time > 3600:  # 每小时
                    await self._perform_periodic_tasks()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"TikTok保活循环异常: {e}")
                await asyncio.sleep(5)
    
    async def _handle_message(self, message_data: Dict):
        """处理收到的消息"""
        try:
            self.message_count += 1
            
            # 1. 记录消息
            logger.info(f"收到消息 #{self.message_count}: {message_data.get('type')}")
            
            # 2. 合规检查
            compliance_check = await self.compliance_checker.check_message(message_data)
            if not compliance_check["passed"]:
                logger.warning(f"消息未通过合规检查: {compliance_check.get('reason')}")
                return
            
            # 3. AI处理生成回复
            ai_result = await self.ai_processor.process_message(message_data)
            
            if not ai_result["success"]:
                logger.error(f"AI处理失败: {ai_result.get('error')}")
                return
            
            # 4. 如果有回复，继续处理
            if ai_result.get("type") == "reply" and "reply" in ai_result:
                self.reply_count += 1
                
                reply_text = ai_result["reply"]
                logger.info(f"生成回复 #{self.reply_count}: {reply_text[:50]}...")
                
                # 5. TTS转换
                tts_result = await self.tts_service.text_to_speech(reply_text)
                
                if tts_result["success"]:
                    # 6. 数字人播报
                    await self.digital_human.speak(
                        text=reply_text,
                        audio_data=tts_result.get("audio_data"),
                        audio_url=tts_result.get("audio_url")
                    )
                    
                    logger.info(f"✅ 完整处理完成: 消息→AI→TTS→数字人")
                else:
                    logger.error(f"TTS转换失败: {tts_result.get('error')}")
            
            # 7. 定期状态报告
            if self.message_count % 10 == 0:
                await self._report_status()
                
        except Exception as e:
            logger.error(f"处理消息异常: {e}")
    
    async def handle_tiktok_webhook(self, webhook_data: Dict) -> Dict:
        """处理TikTok Webhook事件（供Webhook服务器调用）"""
        try:
            # 验证Webhook签名
            if self.platform == "tiktok":
                signature = webhook_data.get("_signature", "")
                payload = json.dumps(webhook_data.get("_payload", {}))
                
                if not self.platform_client.verify_webhook_signature(payload, signature):
                    logger.warning("Webhook签名验证失败")
                    return {"status": "error", "message": "Invalid signature"}
            
            # 处理事件
            event_data = self.platform_client.process_webhook_event(webhook_data)
            
            # 交给消息处理器
            await self._handle_message(event_data)
            
            return {"status": "success", "message": "Webhook processed"}
            
        except Exception as e:
            logger.error(f"处理Webhook异常: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _perform_periodic_tasks(self):
        """执行定期任务"""
        try:
            logger.info("执行定期任务...")
            
            # 1. 状态报告
            await self._report_status()
            
            # 2. 清理旧数据
            self._cleanup_old_data()
            
            # 3. 检查组件健康
            await self._check_components_health()
            
            # 4. TikTok特定：真人互动提醒
            if self.platform == "tiktok":
                await self._remind_human_interaction()
            
            logger.info("定期任务完成")
            
        except Exception as e:
            logger.error(f"执行定期任务异常: {e}")
    
    async def _report_status(self):
        """报告系统状态"""
        uptime = time.time() - self.start_time if self.start_time else 0
        hours = uptime / 3600
        
        status_report = {
            "platform": self.platform,
            "running": self.running,
            "uptime_hours": round(hours, 2),
            "messages_received": self.message_count,
            "replies_sent": self.reply_count,
            "timestamp": time.time()
        }
        
        logger.info(f"系统状态: {json.dumps(status_report, ensure_ascii=False)}")
        
        # 可以在这里发送状态到监控系统
        return status_report
    
    def _cleanup_old_data(self):
        """清理旧数据"""
        # 清理AI历史记录
        if hasattr(self.ai_processor, 'conversation_history'):
            max_history = self.config.get("MAX_CONVERSATION_HISTORY", 50)
            if len(self.ai_processor.conversation_history) > max_history:
                self.ai_processor.conversation_history = self.ai_processor.conversation_history[-max_history:]
                logger.info(f"清理AI历史记录，保留最近{max_history}条")
    
    async def _check_components_health(self):
        """检查组件健康状态"""
        components = {
            "AI Processor": self.ai_processor,
            "TTS Service": self.tts_service,
            "Digital Human": self.digital_human,
            "Platform Client": self.platform_client
        }
        
        for name, component in components.items():
            try:
                # 简单健康检查：检查必要属性是否存在
                if hasattr(component, 'config'):
                    logger.debug(f"{name} 健康检查通过")
                else:
                    logger.warning(f"{name} 健康检查警告：缺少config属性")
            except Exception as e:
                logger.error(f"{name} 健康检查失败: {e}")
    
    async def _remind_human_interaction(self):
        """提醒真人互动（TikTok合规要求）"""
        uptime = time.time() - self.start_time
        hours = uptime / 3600
        
        # 每30分钟提醒一次
        if hours > 0.5 and int(hours * 2) % 1 == 0:  # 每0.5小时
            reminder = "⚠️ TikTok合规提醒：请进行真人互动（出镜或说话），避免被判定为无人直播"
            logger.warning(reminder)
            
            # 可以在这里发送提醒到管理界面
            # await self.send_alert_to_dashboard(reminder)
    
    async def stop(self):
        """停止系统"""
        if not self.running:
            return
        
        logger.info("正在停止系统...")
        self.running = False
        
        try:
            # 停止平台客户端
            if hasattr(self, 'platform_client'):
                await self.platform_client.close()
            
            # 停止数字人
            if hasattr(self, 'digital_human'):
                await self.digital_human.close()
            
            # 停止TTS服务
            if hasattr(self, 'tts_service'):
                await self.tts_service.close()
            
            # TikTok：取消注册Webhook
            if self.platform == "tiktok" and hasattr(self, 'platform_client'):
                await self.platform_client.unregister_webhook()
            
            # 生成最终报告
            await self._generate_final_report()
            
            logger.info("✅ 系统已安全停止")
            
        except Exception as e:
            logger.error(f"停止系统时发生错误: {e}")
    
    async def _generate_final_report(self):
        """生成最终运行报告"""
        if not self.start_time:
            return
        
        uptime = time.time() - self.start_time
        hours = uptime / 3600
        
        final_report = {
            "platform": self.platform,
            "start_time": self.start_time,
            "end_time": time.time(),
            "total_uptime_hours": round(hours, 2),
            "total_messages": self.message_count,
            "total_replies": self.reply_count,
            "average_response_time": "N/A",  # 可以添加响应时间统计
            "compliance_status": "PASSED",
            "timestamp": time.time()
        }
        
        report_path = f"logs/final_report_{int(time.time())}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"最终报告已保存: {report_path}")
        return final_report


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI数字人直播系统")
    parser.add_argument("--platform", choices=["douyin", "tiktok"], default="douyin",
                       help="平台类型：douyin（抖音）或tiktok")
    parser.add_argument("--config", default="config/config.json",
                       help="配置文件路径")
    parser.add_argument("--env", default=".env",
                       help="环境变量文件路径")
    
    args = parser.parse_args()
    
    # 加载环境变量
    if os.path.exists(args.env):
        from dotenv import load_dotenv
        load_dotenv(args.env)
        logger.info(f"已加载环境变量文件: {args.env}")
    
    # 创建并启动系统
    system = AIDigitalHumanLiveSystem(
        platform=args.platform,
        config_path=args.config
    )
    
    try:
        await system.start()
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序运行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 确保logs目录存在
    os.makedirs("logs", exist_ok=True)
    
    # 运行主程序
    asyncio.run(main())