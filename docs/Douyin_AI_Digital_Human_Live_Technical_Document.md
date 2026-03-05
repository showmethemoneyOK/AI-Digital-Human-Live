# 抖音国内版 AI数字人实时互动带货直播方案

## 1. 项目概述

### 场景描述
- **平台**: 抖音（国内版）
- **模式**: 合规24小时无人直播带货
- **互动**: 官方弹幕接口，AI智能回复
- **语言**: 中文普通话
- **延迟**: 全链路延迟 ≤ 600ms
- **特点**: 强合规、官方接口、无爬虫

### 技术架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   官方弹幕接口    │───▶│   国产LLM引擎    │───▶│   国内TTS服务    │───▶│   数字人渲染     │
│   (抖音开放平台)   │    │   (火山/通义)    │    │   (阿里/讯飞)    │    │   (硅基/相芯)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
                                                                               │
                                                                               ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   商品合规库     │    │   合规控制器     │    │   直播伴侣推流    │    │   抖音直播平台   │
│   (审核通过)     │    │   (Python)       │    │   (官方工具)      │    │   (官方接口)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 2. 必备账号与API

### 2.1 平台账号要求
1. **抖音账号要求**
   - 完成实名认证（身份证+人脸识别）
   - 粉丝数 ≥ 1000（开通直播权限）
   - 账号无违规记录
   - 绑定手机号

2. **抖音开放平台账号**
   - 注册企业/个人开发者账号
   - 申请直播API权限
   - 创建应用获取App Key/Secret
   - 配置回调地址

### 2.2 国产API服务清单
| 服务类型 | 推荐提供商 | 用途 | 合规认证 |
|----------|------------|------|----------|
| 弹幕采集 | 抖音开放平台 | 官方弹幕接口 | 已认证 |
| LLM引擎 | 火山方舟/通义千问 | 智能问答 | 国产合规 |
| TTS语音 | 阿里云/讯飞 | 语音合成 | 国产合规 |
| 数字人 | 硅基智能/相芯科技 | 数字人驱动 | 国产合规 |
| 推流工具 | 抖音直播伴侣 | 官方推流 | 强制使用 |

### 2.3 开发环境要求
- **操作系统**: Windows 10/11（必须，直播伴侣仅支持Windows）
- **Python版本**: 3.9+
- **网络要求**: 上传带宽 ≥ 10Mbps（抖音要求更高）
- **硬件要求**:
  - CPU: i7/Ryzen7 以上
  - 内存: 16GB+
  - GPU: RTX 3060+（推荐，加速渲染）

## 3. 搭建步骤

### 步骤1：开通抖音电脑直播权限
1. **账号准备**
   - 登录抖音APP
   - 进入"我" → "创作者服务中心"
   - 申请"电脑直播"权限
   - 完成实名认证和人脸识别

2. **安装直播伴侣**
   - 下载抖音直播伴侣（官方工具）
   - 安装并登录抖音账号
   - 完成设备检测和网络测试

3. **获取推流权限**
   - 在直播伴侣中创建直播
   - 获取推流地址和密钥（仅官方通道）

### 步骤2：申请官方直播接口
1. **注册开放平台**
   - 访问 https://open.douyin.com/
   - 注册开发者账号
   - 创建应用，选择"直播"能力

2. **申请接口权限**
   - 申请"直播管理"权限
   - 申请"弹幕消息"权限
   - 申请"商品管理"权限

3. **配置回调地址**
   ```python
   # 回调服务器配置示例
   from flask import Flask, request, jsonify
   
   app = Flask(__name__)
   
   @app.route('/douyin/callback', methods=['POST'])
   def douyin_callback():
       """抖音开放平台回调接口"""
       data = request.json
       
       # 验证签名
       if not verify_signature(data):
           return jsonify({"code": 4001, "msg": "签名验证失败"})
       
       # 处理不同类型的事件
       event_type = data.get("event")
       
       if event_type == "im.message":
           # 处理弹幕消息
           handle_danmaku(data)
       elif event_type == "live.status":
           # 处理直播状态变化
           handle_live_status(data)
       elif event_type == "gift.message":
           # 处理礼物消息
           handle_gift_message(data)
       
       return jsonify({"code": 0, "msg": "success"})
   ```

### 步骤3：搭建LLM问答与商品知识库
```python
# 国产LLM集成（以火山方舟为例）
import json
import requests

class DomesticLLMService:
    def __init__(self, api_key, model="skylark-lite"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        
    def generate_response(self, user_message, context=None):
        """生成合规的直播回复"""
        system_prompt = self.build_compliant_prompt()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        if context:
            messages.insert(1, {"role": "assistant", "content": context})
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.6,
            "max_tokens": 150,
            "top_p": 0.8,
            "stream": False
        }
        
        # 添加合规过滤器
        data["safety_settings"] = {
            "violence": "BLOCK_MEDIUM_AND_ABOVE",
            "sexual": "BLOCK_MEDIUM_AND_ABOVE",
            "political": "BLOCK_MEDIUM_AND_ABOVE",
            "advertising": "BLOCK_ONLY_HIGH"
        }
        
        response = requests.post(self.base_url, json=data, headers=headers)
        result = response.json()
        
        # 二次合规检查
        if self.check_compliance(result["choices"][0]["message"]["content"]):
            return result["choices"][0]["message"]["content"]
        else:
            return self.get_fallback_response()
    
    def build_compliant_prompt(self):
        """构建符合抖音规范的提示词"""
        return """你是抖音直播间的AI数字人主播，必须严格遵守以下规定：

1. 身份声明：每次回复前必须说明"本直播间由AI数字人主播为您服务"
2. 内容合规：绝不涉及政治、色情、暴力、谣言等内容
3. 商品描述：真实准确，不夸大宣传，不虚假承诺
4. 价格说明：明确标注价格，不误导消费者
5. 风险提示：对特殊商品（如化妆品、保健品）进行必要提示
6. 互动规范：文明用语，不攻击、不贬低他人
7. 广告标识：明确说明"广告"性质

商品信息：
{product_info}

当前活动：
{current_activity}

回复要求：
- 简洁明了，不超过2句话
- 热情亲切，有感染力
- 包含行动号召
- 符合抖音社区规范"""
```

### 步骤4：接入国内TTS服务
```python
# 阿里云TTS集成
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest

class AliyunTTSService:
    def __init__(self, access_key_id, access_key_secret):
        self.client = AcsClient(
            access_key_id,
            access_key_secret,
            'cn-shanghai'
        )
        
    def text_to_speech(self, text, voice="xiaoyun", output_format="mp3"):
        """使用阿里云TTS合成语音"""
        request = CommonRequest()
        request.set_domain('nls-meta.cn-shanghai.aliyuncs.com')
        request.set_version('2019-02-28')
        request.set_action_name('CreateToken')
        
        response = self.client.do_action_with_exception(request)
        token = json.loads(response)['Token']['Id']
        
        # 调用TTS服务
        tts_request = {
            "text": text,
            "voice": voice,
            "format": output_format,
            "sample_rate": 16000,
            "volume": 50,
            "speech_rate": 0,
            "pitch_rate": 0
        }
        
        headers = {
            "X-NLS-Token": token,
            "Content-Type": "application/json"
        }
        
        tts_response = requests.post(
            "https://nls-gateway.cn-shanghai.aliyuncs.com/stream/v1/tts",
            json=tts_request,
            headers=headers
        )
        
        if tts_response.status_code == 200:
            return tts_response.content  # 音频数据
        else:
            raise Exception(f"TTS失败: {tts_response.text}")
```

### 步骤5：数字人本地/云端渲染
```python
# 硅基智能数字人集成
class GuijiDigitalHuman:
    def __init__(self, api_key, app_id):
        self.api_key = api_key
        self.app_id = app_id
        self.base_url = "https://api.guiji.ai/v1"
        
    def create_digital_human_video(self, audio_data, avatar_id, background=None):
        """创建数字人视频（支持本地渲染）"""
        headers = {
            "X-API-Key": self.api_key,
            "X-App-ID": self.app_id,
            "Content-Type": "application/json"
        }
        
        # 上传音频
        upload_url = f"{self.base_url}/upload/audio"
        files = {"file": ("audio.mp3", audio_data, "audio/mpeg")}
        upload_response = requests.post(upload_url, files=files, headers=headers)
        audio_url = upload_response.json()["url"]
        
        # 创建数字人任务
        task_data = {
            "avatar_id": avatar_id,
            "audio_url": audio_url,
            "output_format": "mp4",
            "resolution": "1080x1920",
            "fps": 30,
            "render_mode": "cloud"  # 可选：cloud（云端）或 local（本地）
        }
        
        if background:
            task_data["background_url"] = background
        
        task_response = requests.post(
            f"{self.base_url}/digital_human/tasks",
            json=task_data,
            headers=headers
        )
        
        task_id = task_response.json()["task_id"]
        
        # 轮询任务状态
        while True:
            status_response = requests.get(
                f"{self.base_url}/digital_human/tasks/{task_id}",
                headers=headers
            )
            
            status = status_response.json()["status"]
            
            if status == "completed":
                video_url = status_response.json()["video_url"]
                # 下载视频
                video_response = requests.get(video_url)
                return video_response.content
            elif status == "failed":
                raise Exception("数字人生成失败")
            
            time.sleep(3)
```

### 步骤6：直播伴侣推流集成
```python
# 直播伴侣自动化控制
import pyautogui
import time

class DouyinLiveCompanionController:
    def __init__(self):
        self.companion_path = r"C:\Program Files\Douyin\LiveCompanion\LiveCompanion.exe"
        
    def start_live_companion(self):
        """启动直播伴侣"""
        import subprocess
        subprocess.Popen([self.companion_path])
        time.sleep(10)  # 等待启动
        
    def configure_stream(self, stream_url, stream_key):
        """配置推流参数"""
        # 点击"开播"按钮
        pyautogui.click(x=100, y=100)  # 坐标需要根据实际界面调整
        
        # 选择"自定义推流"
        pyautogui.click(x=200, y=150)
        
        # 输入推流地址
        pyautogui.click(x=300, y=200)
        pyautogui.write(stream_url)
        
        # 输入流密钥
        pyautogui.click(x=300, y=250)
        pyautogui.write(stream_key)
        
        # 保存配置
        pyautogui.click(x=400, y=300)
        
    def start_streaming(self):
        """开始推流"""
        # 点击"开始直播"按钮
        pyautogui.click(x=500, y=350)
        time.sleep(5)
        
        # 确认开始
        pyautogui.click(x=550, y=400)
        
    def update_media_source(self, video_path):
        """更新媒体源（播放数字人视频）"""
        # 点击"添加素材"
        pyautogui.click(x=600, y=100)
        
        # 选择"视频文件"
        pyautogui.click(x=650, y=150)
        
        # 输入文件路径
        pyautogui.click(x=700, y=200)
        pyautogui.write(video_path)
        
        # 确认添加
        pyautogui.click(x=750, y=250)
```

### 步骤7：全自动运行系统
```python
# 主控系统 - 抖音合规版
import asyncio
import logging
from datetime import datetime

class DouyinAILiveSystem:
    def __init__(self, config):
        self.config = config
        self.logger = self.setup_logger()
        
        # 初始化各模块
        self.danmaku_service = DouyinOfficialDanmakuService(
            config["douyin_app_key"],
            config["douyin_app_secret"]
        )
        
        self.llm_service = DomesticLLMService(
            config["volcengine_api_key"],
            model="skylark-lite"
        )
        
        self.tts_service = AliyunTTSService(
            config["aliyun_access_key_id"],
            config["aliyun_access_key_secret"]
        )
        
        self.digital_human = GuijiDigitalHuman(
            config["guiji_api_key"],
            config["guiji_app_id"]
        )
        
        self.live_controller = DouyinLiveCompanionController()
        
    def setup_logger(self):
        """设置合规日志系统"""
        logger = logging.getLogger("douyin_ai_live")
        logger.setLevel(logging.INFO)
        
        # 文件日志（保留30天）
        file_handler = logging.FileHandler(
            f"logs/douyin_live_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        )
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        
        # 控制台日志
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter('%(levelname)s: %(message)s')
        )
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        return logger
    
    async def run_compliant_live(self):
        """运行合规直播主循环"""
        self.logger.info("启动抖音AI数字人直播系统")
        
        # 1. 启动直播伴侣并开始推流
        self.live_controller.start_live_companion()
        self.live_controller.configure_stream(
            self.config["stream_url"],
            self.config["stream_key"]
        )
        self.live_controller.start_streaming()
        
        # 2. 开始弹幕监听
        async for danmaku in self.danmaku_service.listen_danmaku():
            try:
                # 合规检查
                if not self.content_compliance_check(danmaku):
                    self.logger.warning(f"弹幕内容不合规: {danmaku}")
                    continue
                
                # 3. AI生成回复（带合规过滤）
                ai_response = self.llm_service.generate_response(
                    danmaku,
                    context=self.get_current_context()
                )
                
                # 4. TTS语音合成
                audio_data = self.tts_service.text_to_speech(ai_response)
                
                # 5. 数字人生成视频
                video_data = self.digital_human.create_digital_human_video(
                    audio_data,
                    avatar_id=self.config["avatar_id"],
                    background=self.config["background_image"]
                )
                
                # 6. 保存视频文件并更新直播伴侣
                video_path = f"temp/video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                with open(video_path, "wb") as f:
                    f.write(video_data)
                
                self.live_controller.update_media_source(video_path)
                
                # 7. 记录交互日志（用于合规审计）
                self.log_interaction(danmaku, ai_response, video_path)
                
                # 8. 定期合规声明
                await self.periodic_compliance_announcement()
                
            except Exception as e:
                self.logger.error(f"处理异常: {e}")
                # 播放预设的