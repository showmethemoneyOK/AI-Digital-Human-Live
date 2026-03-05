    async def xunfei_tts(self, text: str, output_path: str) -> Optional[str]:
        """讯飞TTS"""
        # 讯飞TTS需要WebSocket连接，这里简化处理
        try:
            import hashlib
            import base64
            import hmac
            import uuid
            from urllib.parse import urlencode
            import websockets
            
            # 讯飞TTS参数
            api_key = self.config.api_key
            app_id = self.config.voice_id  # 这里用voice_id存储app_id
            
            # 生成请求参数
            ts = str(int(time.time()))
            nonce = str(uuid.uuid4())
            
            # 生成签名
            signature_origin = f"{app_id}{ts}{nonce}"
            signature = hmac.new(
                api_key.encode('utf-8'),
                signature_origin.encode('utf-8'),
                hashlib.sha256
            ).digest()
            signature = base64.b64encode(signature).decode('utf-8')
            
            # 构建WebSocket URL
            url = f"wss://tts-api.xfyun.cn/v2/tts?{urlencode({
                'authorization': signature,
                'date': ts,
                'host': 'tts-api.xfyun.cn'
            })}"
            
            # WebSocket连接（简化实现）
            self.logger.warning("讯飞TTS需要WebSocket连接，这里使用模拟实现")
            
            # 模拟生成音频文件
            with open(output_path, "wb") as f:
                # 这里应该写入实际的音频数据
                f.write(b'')  # 实际使用时需要替换
            
            self.logger.info(f"讯飞TTS模拟成功: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"讯飞TTS异常: {e}")
            return None

# ===================== 4. 数字人驱动模块 =====================

class DigitalHumanDriver:
    """数字人驱动服务"""
    
    def __init__(self, config: DigitalHumanConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def create_talk(self, audio_path: str, image_url: str = None, output_path: str = None) -> Optional[str]:
        """创建数字人讲话视频"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"temp/video_{timestamp}.mp4"
        
        # 确保目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 根据API URL判断服务提供商
        if "d-id.com" in self.config.api_url:
            return await self.d_id_create_talk(audio_path, image_url, output_path)
        elif "guiji.ai" in self.config.api_url:
            return await self.guiji_create_talk(audio_path, output_path)
        elif "heygen.com" in self.config.api_url:
            return await self.heygen_create_talk(audio_path, output_path)
        else:
            self.logger.error(f"不支持的数字人服务: {self.config.api_url}")
            return None
    
    async def d_id_create_talk(self, audio_path: str, image_url: str, output_path: str) -> Optional[str]:
        """D-ID数字人生成"""
        # 上传音频
        upload_url = f"{self.config.api_url}/uploads"
        
        headers = {
            "Authorization": f"Basic {self.config.api_key}",
            "accept": "application/json"
        }
        
        try:
            # 上传音频文件
            with open(audio_path, "rb") as audio_file:
                files = {"audio": audio_file}
                upload_response = requests.post(
                    upload_url,
                    files=files,
                    headers=headers
                )
            
            if upload_response.status_code != 200:
                self.logger.error(f"D-ID音频上传失败: {upload_response.status_code}")
                return None
            
            audio_id = upload_response.json()["id"]
            
            # 创建讲话任务
            talk_data = {
                "source_url": image_url or "https://cdn.d-id.com/default-avatar.png",
                "script": {
                    "type": "audio",
                    "audio_url": f"{self.config.api_url}/uploads/{audio_id}"
                },
                "config": {
                    "fluent": True,
                    "pad_audio": 0.0,
                    "result_format": "mp4"
                }
            }
            
            talk_response = requests.post(
                self.config.api_url,
                json=talk_data,
                headers=headers
            )
            
            if talk_response.status_code != 201:
                self.logger.error(f"D-ID创建任务失败: {talk_response.status_code}")
                return None
            
            talk_id = talk_response.json()["id"]
            
            # 轮询任务状态
            for _ in range(60):  # 最多等待3分钟
                status_response = requests.get(
                    f"{self.config.api_url}/{talk_id}",
                    headers=headers
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data["status"]
                    
                    if status == "done":
                        result_url = status_data["result_url"]
                        # 下载视频
                        video_response = requests.get(result_url)
                        with open(output_path, "wb") as f:
                            f.write(video_response.content)
                        
                        self.logger.info(f"D-ID数字人生成成功: {output_path}")
                        return output_path
                    
                    elif status == "failed":
                        self.logger.error("D-ID数字人生成失败")
                        return None
                
                await asyncio.sleep(3)  # 每3秒检查一次
            
            self.logger.error("D-ID数字人生成超时")
            return None
            
        except Exception as e:
            self.logger.error(f"D-ID数字人生成异常: {e}")
            return None
    
    async def guiji_create_talk(self, audio_path: str, output_path: str) -> Optional[str]:
        """硅基智能数字人生成"""
        headers = {
            "X-API-Key": self.config.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            # 上传音频
            with open(audio_path, "rb") as audio_file:
                files = {"file": ("audio.mp3", audio_file, "audio/mpeg")}
                upload_response = requests.post(
                    f"{self.config.api_url}/upload/audio",
                    files=files,
                    headers=headers
                )
            
            if upload_response.status_code != 200:
                self.logger.error(f"硅基音频上传失败: {upload_response.status_code}")
                return None
            
            audio_url = upload_response.json()["url"]
            
            # 创建数字人任务
            task_data = {
                "avatar_id": self.config.avatar_id,
                "audio_url": audio_url,
                "output_format": "mp4",
                "resolution": "1080x1920",
                "fps": 30,
                "render_mode": self.config.render_mode
            }
            
            task_response = requests.post(
                f"{self.config.api_url}/digital_human/tasks",
                json=task_data,
                headers=headers
            )
            
            if task_response.status_code != 200:
                self.logger.error(f"硅基创建任务失败: {task_response.status_code}")
                return None
            
            task_id = task_response.json()["task_id"]
            
            # 轮询任务状态
            for _ in range(60):
                status_response = requests.get(
                    f"{self.config.api_url}/digital_human/tasks/{task_id}",
                    headers=headers
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data["status"]
                    
                    if status == "completed":
                        video_url = status_data["video_url"]
                        # 下载视频
                        video_response = requests.get(video_url)
                        with open(output_path, "wb") as f:
                            f.write(video_response.content)
                        
                        self.logger.info(f"硅基数字人生成成功: {output_path}")
                        return output_path
                    
                    elif status == "failed":
                        self.logger.error("硅基数字人生成失败")
                        return None
                
                await asyncio.sleep(3)
            
            self.logger.error("硅基数字人生成超时")
            return None
            
        except Exception as e:
            self.logger.error(f"硅基数字人生成异常: {e}")
            return None
    
    async def heygen_create_talk(self, audio_path: str, output_path: str) -> Optional[str]:
        """HeyGen数字人生成"""
        headers = {
            "X-Api-Key": self.config.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            # 上传音频
            with open(audio_path, "rb") as audio_file:
                files = {"file": audio_file}
                upload_response = requests.post(
                    f"{self.config.api_url}/uploads",
                    files=files,
                    headers={"X-Api-Key": self.config.api_key}
                )
            
            if upload_response.status_code != 200:
                self.logger.error(f"HeyGen音频上传失败: {upload_response.status_code}")
                return None
            
            upload_data = upload_response.json()
            audio_url = upload_data["url"]
            
            # 创建视频任务
            video_data = {
                "video_inputs": [
                    {
                        "character": {
                            "type": "avatar",
                            "avatar_id": self.config.avatar_id,
                            "avatar_style": "normal"
                        },
                        "voice": {
                            "type": "audio",
                            "audio_url": audio_url
                        },
                        "background": {
                            "type": "color",
                            "value": "#FFFFFF"
                        }
                    }
                ],
                "dimension": {
                    "width": 1080,
                    "height": 1920
                },
                "test": False
            }
            
            video_response = requests.post(
                f"{self.config.api_url}/videos",
                json=video_data,
                headers=headers
            )
            
            if video_response.status_code != 200:
                self.logger.error(f"HeyGen创建视频失败: {video_response.status_code}")
                return None
            
            video_id = video_response.json()["data"]["video_id"]
            
            # 轮询视频状态
            for _ in range(60):
                status_response = requests.get(
                    f"{self.config.api_url}/videos/{video_id}",
                    headers=headers
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data["data"]["status"]
                    
                    if status == "completed":
                        video_url = status_data["data"]["video_url"]
                        # 下载视频
                        video_response = requests.get(video_url)
                        with open(output_path, "wb") as f:
                            f.write(video_response.content)
                        
                        self.logger.info(f"HeyGen数字人生成成功: {output_path}")
                        return output_path
                    
                    elif status == "failed":
                        self.logger.error("HeyGen数字人生成失败")
                        return None
                
                await asyncio.sleep(3)
            
            self.logger.error("HeyGen数字人生成超时")
            return None
            
        except Exception as e:
            self.logger.error(f"HeyGen数字人生成异常: {e}")
            return None

# ===================== 5. 推流控制模块 =====================

class StreamController:
    """推流控制器"""
    
    def __init__(self, platform_config: PlatformConfig):
        self.config = platform_config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.obs_process = None
    
    async def start_stream(self):
        """开始推流"""
        if self.config.platform == "douyin":
            return await self.start_douyin_stream()
        else:
            return await self.start_tiktok_stream()
    
    async def start_douyin_stream(self):
        """启动抖音直播伴侣推流"""
        try:
            import subprocess
            import pyautogui
            import time
            
            # 启动直播伴侣
            companion_path = r"C:\Program Files\Douyin\LiveCompanion\LiveCompanion.exe"
            if os.path.exists(companion_path):
                self.obs_process = subprocess.Popen([companion_path])
                time.sleep(10)  # 等待启动
                
                # 自动化配置（简化实现）
                self.logger.info("抖音直播伴侣已启动，请手动配置推流参数")
                
                # 这里应该是自动化点击和配置的代码
                # 由于直播伴侣界面可能变化，建议手动配置
                
                return True
            else:
                self.logger.error("未找到抖音直播伴侣，请手动安装")
                return False
                
        except Exception as e:
            self.logger.error(f"启动抖音直播伴侣异常: {e}")
            return False
    
    async def start_tiktok_stream(self):
        """启动TikTok OBS推流"""
        try:
            import subprocess
            
            # OBS推流命令（简化）
            # 实际应该通过OBS Websocket控制
            obs_command = [
                "obs",
                "--startstreaming",
                "--minimize-to-tray"
            ]
            
            # 检查OBS是否安装
            try:
                self.obs_process = subprocess.Popen(obs_command)
                self.logger.info("OBS推流已启动")
                return True
            except FileNotFoundError:
                self.logger.error("OBS未安装，请先安装OBS Studio")
                return False
                
        except Exception as e:
            self.logger.error(f"启动OBS推流异常: {e}")
            return False
    
    async def update_video_source(self, video_path: str):
        """更新视频源"""
        # 这里应该通过OBS Websocket或直播伴侣API更新视频源
        # 简化实现：记录日志
        self.logger.info(f"更新视频源: {video_path}")
        
        # 实际实现应该调用OBS Websocket API
        # 或直播伴侣的自动化接口
        
        return True
    
    async def stop_stream(self):
        """停止推流"""
        if self.obs_process:
            self.obs_process.terminate()
            self.obs_process = None
            self.logger.info("推流已停止")
        
        return True

# ===================== 6. 主控系统 =====================

class AIDigitalHumanLiveSystem:
    """AI数字人直播主控系统"""
    
    def __init__(self, system_config: SystemConfig):
        self.config = system_config
        self.setup_logging()
        
        # 初始化各模块
        if self.config.platform_config.platform == "douyin":
            # 抖音需要额外的app_secret
            app_secret = os.getenv("DOUYIN_APP_SECRET", "")
            self.danmaku_listener = DouyinDanmakuListener(
                self.config.platform_config,
                self.config.platform_config.user_unique_id,  # 作为app_key
                app_secret
            )
        else:
            # TikTok
            self.danmaku_listener = TikTokDanmakuListener(
                self.config.platform_config,
                self.config.llm_config.api_key  # 复用作为TikHub API Key
            )
        
        self.ai_host = AILiveHost(self.config.llm_config)
        self.tts_service = TTSService(self.config.tts_config)
        self.digital_human = DigitalHumanDriver(self.config.digital_human_config)
        self.stream_controller = StreamController(self.config.platform_config)
        
        # 状态跟踪
        self.is_running = False
        self.interaction_count = 0
        self.start_time = None
        
    def setup_logging(self):
        """设置日志系统"""
        log_level = getattr(logging, self.config.log_level.upper())
        
        # 创建日志目录
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # 文件处理器
        file_handler = logging.FileHandler(
            f"{log_dir}/ai_live_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        )
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter('%(levelname)s: %(message)s')
        )
        
        # 配置根日志器
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def run(self):
        """运行主循环"""
        self.is_running = True
        self.start_time = datetime.now()
        
        self.logger.info(f"启动AI数字人直播系统 - 平台: {self.config.platform_config.platform}")
        self.logger.info(f"直播间ID: {self.config.platform_config.room_id}")
        
        try:
            # 1. 启动推流
            stream_started = await self.stream_controller.start_stream()
            if not stream_started:
                self.logger.error("推流启动失败，系统退出")
                return
            
            # 2. 开始弹幕监听和处理循环
            await self.process_loop()
            
        except KeyboardInterrupt:
            self.logger.info("收到中断信号，正在停止...")
        except Exception as e:
            self.logger.error(f"系统运行异常: {e}")
        finally:
            await self.cleanup()
    
    async def process_loop(self):
        """处理循环"""
        self.logger.info("开始弹幕监听和处理循环...")
        
        # 初始欢迎语
        await self.play_welcome_message()
        
        # 主循环
        while self.is_running:
            try:
                # 获取弹幕
                comments = await self.danmaku_listener.fetch_danmaku()
                
                for comment in comments:
                    # 处理每个弹幕
