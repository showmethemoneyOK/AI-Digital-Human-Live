                    for comment in comments:
                    # 处理每个弹幕
                    await self.process_comment(comment)
                
                # 定期发送保持活跃的消息
                await self.send_keepalive_message()
                
                # 短暂休眠，避免过高频率
                await asyncio.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"处理循环异常: {e}")
                await asyncio.sleep(2)  # 异常后等待
    
    async def process_comment(self, comment: Dict):
        """处理单个弹幕"""
        try:
            content = comment.get("content", "").strip()
            if not content:
                return
            
            user_id = comment.get("user_id", "unknown")
            self.logger.info(f"处理弹幕 [{user_id}]: {content}")
            
            # 1. AI生成回复
            ai_response = await self.ai_host.generate_response(
                content,
                platform=self.config.platform_config.platform
            )
            
            # 2. TTS语音合成
            audio_path = await self.tts_service.text_to_speech(ai_response)
            if not audio_path:
                self.logger.error("TTS合成失败")
                return
            
            # 3. 数字人生成视频
            video_path = await self.digital_human.create_talk(
                audio_path,
                image_url=self.get_avatar_image(),
                output_path=f"temp/video_{self.interaction_count}.mp4"
            )
            
            if not video_path:
                self.logger.error("数字人生成失败")
                return
            
            # 4. 更新推流视频源
            await self.stream_controller.update_video_source(video_path)
            
            # 5. 记录交互
            self.interaction_count += 1
            self.log_interaction(comment, ai_response, video_path)
            
            # 6. 清理临时文件（可选）
            self.cleanup_temp_files([audio_path, video_path])
            
        except Exception as e:
            self.logger.error(f"处理弹幕异常: {e}")
    
    async def play_welcome_message(self):
        """播放欢迎语"""
        welcome_text = self.get_welcome_message()
        
        try:
            # 生成欢迎语音频
            audio_path = await self.tts_service.text_to_speech(welcome_text)
            if audio_path:
                # 生成欢迎视频
                video_path = await self.digital_human.create_talk(
                    audio_path,
                    image_url=self.get_avatar_image(),
                    output_path="temp/welcome.mp4"
                )
                
                if video_path:
                    # 更新视频源
                    await self.stream_controller.update_video_source(video_path)
                    self.logger.info("欢迎语播放完成")
        
        except Exception as e:
            self.logger.error(f"播放欢迎语异常: {e}")
    
    async def send_keepalive_message(self):
        """发送保持活跃的消息（每5分钟）"""
        current_time = datetime.now()
        
        # 每5分钟发送一次
        if hasattr(self, 'last_keepalive'):
            if (current_time - self.last_keepalive).seconds < 300:
                return
        
        try:
            keepalive_text = self.get_keepalive_message()
            audio_path = await self.tts_service.text_to_speech(keepalive_text)
            
            if audio_path:
                video_path = await self.digital_human.create_talk(
                    audio_path,
                    image_url=self.get_avatar_image(),
                    output_path=f"temp/keepalive_{current_time.strftime('%H%M')}.mp4"
                )
                
                if video_path:
                    await self.stream_controller.update_video_source(video_path)
                    self.last_keepalive = current_time
                    self.logger.info("保持活跃消息已发送")
        
        except Exception as e:
            self.logger.error(f"发送保持活跃消息异常: {e}")
    
    def get_welcome_message(self) -> str:
        """获取欢迎语"""
        if self.config.platform_config.platform == "douyin":
            return """欢迎来到AI数字人直播间！本直播间由AI数字人主播为您服务。
我是您的智能带货助手，可以回答商品相关问题，帮助您了解产品详情。
请随时在弹幕中提问，我会热情为您解答！"""
        else:
            return """Welcome to the AI Digital Human Live Stream!
I'm your AI shopping assistant, here to help you with product questions.
Feel free to ask anything in the chat, and I'll be happy to assist you! 🛍️"""
    
    def get_keepalive_message(self) -> str:
        """获取保持活跃消息"""
        if self.config.platform_config.platform == "douyin":
            messages = [
                "AI数字人主播持续为您服务中，有任何问题请随时提问！",
                "感谢大家观看，记得点击下方小黄车查看商品详情哦！",
                "本直播间24小时不间断直播，AI主播随时为您解答！"
            ]
        else:
            messages = [
                "AI Digital Host is here to help! Ask me anything about our products!",
                "Don't forget to check out the products in the shopping cart! 🛒",
                "24/7 AI live stream - I'm always here to assist you! 🤖"
            ]
        
        import random
        return random.choice(messages)
    
    def get_avatar_image(self) -> str:
        """获取数字人形象图片URL"""
        # 这里应该返回配置的数字人形象URL
        # 简化实现：返回默认图片
        if self.config.platform_config.platform == "douyin":
            return "https://example.com/douyin_avatar.png"  # 替换为实际URL
        else:
            return "https://example.com/tiktok_avatar.png"  # 替换为实际URL
    
    def log_interaction(self, comment: Dict, response: str, video_path: str):
        """记录交互日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "platform": self.config.platform_config.platform,
            "user_id": comment.get("user_id", "unknown"),
            "user_message": comment.get("content", ""),
            "ai_response": response,
            "video_file": video_path,
            "interaction_id": self.interaction_count
        }
        
        # 保存到JSON日志文件
        log_file = f"logs/interactions_{datetime.now().strftime('%Y%m%d')}.json"
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        try:
            # 读取现有日志
            existing_logs = []
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            existing_logs.append(json.loads(line))
            
            # 添加新日志
            existing_logs.append(log_entry)
            
            # 写入文件
            with open(log_file, 'w', encoding='utf-8') as f:
                for entry in existing_logs:
                    f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        except Exception as e:
            self.logger.error(f"记录交互日志异常: {e}")
    
    def cleanup_temp_files(self, file_paths: List[str]):
        """清理临时文件"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                self.logger.warning(f"清理临时文件失败 {file_path}: {e}")
    
    async def cleanup(self):
        """清理资源"""
        self.is_running = False
        
        # 停止推流
        await self.stream_controller.stop_stream()
        
        # 清理临时目录
        temp_dir = "temp"
        if os.path.exists(temp_dir):
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                self.logger.warning(f"清理临时目录失败: {e}")
        
        # 计算运行统计
        if self.start_time:
            run_time = datetime.now() - self.start_time
            self.logger.info(f"系统运行结束 - 总运行时间: {run_time}")
            self.logger.info(f"总交互次数: {self.interaction_count}")

# ===================== 7. 配置文件 =====================

def load_config(config_file: str = "config/config.json") -> SystemConfig:
    """加载配置文件"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # 创建配置对象
        platform_config = PlatformConfig(**config_data["platform"])
        llm_config = LLMConfig(**config_data["llm"])
        tts_config = TTSConfig(**config_data["tts"])
        digital_human_config = DigitalHumanConfig(**config_data["digital_human"])
        
        system_config = SystemConfig(
            platform_config=platform_config,
            llm_config=llm_config,
            tts_config=tts_config,
            digital_human_config=digital_human_config,
            **config_data.get("system", {})
        )
        
        return system_config
        
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        
        # 返回默认配置
        return get_default_config()

def get_default_config() -> SystemConfig:
    """获取默认配置"""
    # TikTok默认配置
    platform_config = PlatformConfig(
        platform="tiktok",
        room_id="your_tiktok_room_id",
        user_unique_id="@your_tiktok_username",
        stream_url="rtmp://live.tiktok.com/rtmp/",
        stream_key="your_stream_key"
    )
    
    llm_config = LLMConfig(
        api_key="your_openai_api_key",
        api_url="https://api.openai.com/v1/chat/completions",
        model="gpt-3.5-turbo"
    )
    
    tts_config = TTSConfig(
        api_key="your_elevenlabs_api_key",
        api_url="https://api.elevenlabs.io/v1/text-to-speech",
        voice_id="21m00Tcm4TlvDq8ikWAM"
    )
    
    digital_human_config = DigitalHumanConfig(
        api_key="your_d_id_api_key",
        api_url="https://api.d-id.com/talks",
        avatar_id="your_avatar_id"
    )
    
    return SystemConfig(
        platform_config=platform_config,
        llm_config=llm_config,
        tts_config=tts_config,
        digital_human_config=digital_human_config
    )

# ===================== 8. 主函数 =====================

async def main():
    """主函数"""
    print("=" * 60)
    print("AI数字人直播系统 - 抖音/TikTok双平台")
    print("版本: 2.0.0")
    print("=" * 60)
    
    # 加载配置
    config = load_config()
    
    # 创建系统实例
    system = AIDigitalHumanLiveSystem(config)
    
    # 运行系统
    try:
        await system.run()
    except KeyboardInterrupt:
        print("\n系统被用户中断")
    except Exception as e:
        print(f"系统运行异常: {e}")
    finally:
        print("系统已停止")

if __name__ == "__main__":
    # 创建必要的目录
    for directory in ["config", "logs", "temp"]:
        os.makedirs(directory, exist_ok=True)
    
    # 运行主函数
    asyncio.run(main())

# ===================== 9. 使用示例 =====================

"""
使用步骤：

1. 安装依赖：
   pip install requests aiohttp pyautogui websockets

2. 创建配置文件 config/config.json：
   {
     "platform": {
       "platform": "tiktok",
       "room_id": "your_room_id",
       "user_unique_id": "@your_username",
       "stream_url": "rtmp://live.tiktok.com/rtmp/",
       "stream_key": "your_stream_key"
     },
     "llm": {
       "api_key": "sk-...",
       "api_url": "https://api.openai.com/v1/chat/completions",
       "model": "gpt-3.5-turbo"
     },
     "tts": {
       "api_key": "elevenlabs_api_key",
       "api_url": "https://api.elevenlabs.io/v1/text-to-speech",
       "voice_id": "21m00Tcm4TlvDq8ikWAM"
     },
     "digital_human": {
       "api_key": "d_id_api_key",
       "api_url": "https://api.d-id.com/talks",
       "avatar_id": "your_avatar_id"
     },
     "system": {
       "log_level": "INFO",
       "max_retries": 3,
       "timeout": 30
     }
   }

3. 运行系统：
   python ai_digital_human_live_controller.py

4. 监控日志：
   tail -f logs/ai_live_*.log

注意事项：
1. 确保所有API密钥有效
2. 抖音平台需要额外申请官方接口权限
3. 推流前需要先配置好OBS或直播伴侣
4. 遵守各平台的内容规范
"""