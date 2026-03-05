# TikTok 海外版 AI数字人实时互动带货直播方案
## 版本：v1.0 | 更新日期：2026-03-05

---

## 📋 项目概述

### 核心场景
- **平台**: TikTok 国际版
- **模式**: 24小时无人带货直播 + 实时弹幕交互
- **语言**: 英语、西班牙语、葡萄牙语等多语种支持
- **延迟**: ≤800ms（端到端全链路）
- **合规**: 完全遵守TikTok社区规范

### 技术架构
```
用户弹幕 → TikTok弹幕采集 → LLM智能问答 → TTS语音合成 → 数字人驱动 → RTMP推流 → TikTok直播间
```

### 核心优势
1. **全自动化**: 7×24小时不间断直播
2. **实时交互**: 用户弹幕即时响应
3. **多语种**: 支持全球主要语言
4. **低成本**: 无需真人主播，降低人力成本
5. **可扩展**: 模块化设计，易于扩展功能

---

## 🔧 技术栈与必备资源

### 1. 账号与权限
| 资源 | 要求 | 获取方式 |
|------|------|----------|
| **TikTok账号** | 支持直播功能 + RTMP推流权限 | TikTok Creator账号，开启直播权限 |
| **TikTok直播权限** | 电脑端直播权限 | 账号需满足：1000粉丝 + 过去30天直播≥3次 |
| **RTMP推流地址** | 直播推流密钥 | TikTok直播设置中获取 |

### 2. API服务（海外版）
| 服务 | 推荐提供商 | 用途 | 成本估算 |
|------|------------|------|----------|
| **弹幕采集** | TikHub API / TikTokLive | 实时获取直播间弹幕 | $20-50/月 |
| **LLM大模型** | OpenAI GPT-4o-mini | 智能问答生成 | $0.15/百万tokens |
| **TTS语音合成** | ElevenLabs | 自然语音生成 | $5/月起 |
| **数字人驱动** | D-ID / HeyGen | 数字人视频生成 | $20-100/月 |
| **云服务器** | AWS / DigitalOcean | 部署运行环境 | $10-50/月 |

### 3. 本地工具
| 工具 | 版本 | 用途 |
|------|------|------|
| **Python** | 3.9+ | 主控程序开发 |
| **FFmpeg** | 最新版 | 视频流处理 |
| **OBS Studio** | 29.0+ | RTMP推流 |
| **Git** | 2.40+ | 版本控制 |

---

## 🚀 详细搭建步骤

### 第1步：获取TikTok直播推流信息
1. **登录TikTok账号**，进入创作者中心
2. **开启直播功能**，选择"电脑直播"
3. **获取RTMP信息**：
   ```
   服务器: rtmp://live.tiktok.com/rtmp/
   流密钥: [你的唯一Stream Key]
   ```
4. **测试推流**：使用OBS测试连接

### 第2步：搭建弹幕实时监听系统
#### 方案A：TikHub API（推荐）
```python
import requests
import asyncio

class TikTokDanmaku:
    def __init__(self, api_key, room_id):
        self.api_key = api_key
        self.room_id = room_id
        self.base_url = "https://api.tikhub.io/api/v1/tiktok/web/fetch_live_im_fetch"
    
    async def fetch_comments(self):
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"room_id": self.room_id}
        
        while True:
            try:
                response = requests.get(self.base_url, headers=headers, params=params)
                data = response.json()
                
                if data.get("success") and data.get("comments"):
                    for comment in data["comments"]:
                        user = comment.get("user", {}).get("nickname", "匿名")
                        content = comment.get("content", "")
                        timestamp = comment.get("timestamp", "")
                        
                        yield {
                            "user": user,
                            "content": content,
                            "timestamp": timestamp
                        }
                
                await asyncio.sleep(1)  # 1秒轮询
                
            except Exception as e:
                print(f"弹幕获取失败: {e}")
                await asyncio.sleep(5)
```

#### 方案B：TikTokLive（开源方案）
```python
from TikTokLive import TikTokLiveClient
from TikTokLive.types.events import CommentEvent

client = TikTokLiveClient(unique_id="@你的账号")

@client.on("comment")
async def on_comment(event: CommentEvent):
    print(f"{event.user.nickname} -> {event.comment}")
    # 处理弹幕逻辑

if __name__ == "__main__":
    client.run()
```

### 第3步：配置LLM主播人设与商品知识库
#### 主播人设配置
```python
SYSTEM_PROMPT_EN = """
You are a professional TikTok live stream sales host.

PERSONALITY:
- Energetic, friendly, and persuasive
- Speak in short, clear sentences (1-2 sentences max)
- Use simple, conversational English
- Always positive and enthusiastic

SALES TECHNIQUES:
1. Highlight product VALUE and BENEFITS
2. Mention PRICE and any DISCOUNTS
3. Create URGENCY (limited stock/time)
4. Guide viewers to CLICK SHOPPING CART
5. Use social proof (e.g., "Many customers love this")

RULES:
- Never make false claims
- Only answer product-related questions
- If unsure, say "Great question! Check the product details in our shop"
- Always end with a call-to-action
"""

SYSTEM_PROMPT_ES = """
Eres un presentador profesional de ventas en vivo de TikTok.

PERSONALIDAD:
- Energético, amigable y persuasivo
- Habla en oraciones cortas y claras (máximo 1-2 oraciones)
- Usa español conversacional simple
- Siempre positivo y entusiasta

TÉCNICAS DE VENTA:
1. Destaca el VALOR y los BENEFICIOS del producto
2. Menciona el PRECIO y cualquier DESCUENTO
3. Crea URGENCIA (stock/tiempo limitado)
4. Guía a los espectadores a HACER CLIC EN EL CARRITO DE COMPRAS
5. Usa prueba social (ej. "Muchos clientes aman esto")

REGLAS:
- Nunca hagas afirmaciones falsas
- Solo responde preguntas relacionadas con productos
- Si no estás seguro, di "¡Buena pregunta! Consulta los detalles del producto en nuestra tienda"
- Siempre termina con una llamada a la acción
"""
```

#### 商品知识库
```python
PRODUCT_KNOWLEDGE_BASE = {
    "beauty_products": {
        "skincare_set": {
            "name": "Glow Up Skincare Set",
            "price": "$49.99",
            "discount": "30% OFF today only",
            "features": [
                "5-step skincare routine",
                "Natural ingredients",
                "Suitable for all skin types",
                "Results in 2 weeks"
            ],
            "selling_points": [
                "Limited edition packaging",
                "Free shipping over $50",
                "30-day money-back guarantee"
            ]
        }
    },
    "electronics": {
        "wireless_earbuds": {
            "name": "SoundFlow Pro Wireless Earbuds",
            "price": "$79.99",
            "discount": "Buy 1 Get 1 50% OFF",
            "features": [
                "40-hour battery life",
                "Noise cancellation",
                "IPX7 waterproof",
                "Wireless charging case"
            ]
        }
    }
}
```

### 第4步：接入TTS语音合成（ElevenLabs）
```python
import requests
import json

class ElevenLabsTTS:
    def __init__(self, api_key, voice_id="21m00Tcm4TlvDq8ikWAM"):
        self.api_key = api_key
        self.voice_id = voice_id
        self.base_url = "https://api.elevenlabs.io/v1/text-to-speech"
    
    def text_to_speech(self, text, output_file="output.mp3"):
        """将文本转换为语音"""
        url = f"{self.base_url}/{self.voice_id}"
        
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.3,
                "use_speaker_boost": True
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                with open(output_file, "wb") as f:
                    f.write(response.content)
                print(f"✅ TTS生成成功: {output_file}")
                return output_file
            else:
                print(f"❌ TTS失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ TTS异常: {e}")
            return None
    
    def get_available_voices(self):
        """获取可用音色列表"""
        url = f"{self.base_url}/voices"
        headers = {"xi-api-key": self.api_key}
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
```

### 第5步：数字人驱动（D-ID API）
```python
import requests
import time

class DIDDigitalHuman:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.d-id.com"
    
    def create_talk(self, image_url, audio_url, driver="audio"):
        """创建数字人讲话视频"""
        url = f"{self.base_url}/talks"
        
        headers = {
            "Authorization": f"Basic {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "source_url": image_url,
            "script": {
                "type": driver,
                "audio_url": audio_url
            },
            "config": {
                "fluent": True,
                "pad_audio": 0.0
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 201:
                talk_id = response.json().get("id")
                print(f"✅ 数字人任务创建成功: {talk_id}")
                return talk_id
            else:
                print(f"❌ 数字人创建失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 数字人异常: {e}")
            return None
    
    def get_talk_result(self, talk_id, timeout=60):
        """获取数字人视频结果"""
        url = f"{self.base_url}/talks/{talk_id}"
        headers = {"Authorization": f"Basic {self.api_key}"}
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status")
                
                if status == "done":
                    result_url = data.get("result_url")
                    print(f"✅ 数字人视频生成完成: {result_url}")
                    return result_url
                elif status == "failed":
                    print(f"❌ 数字人生成失败")
                    return None
                else:
                    print(f"⏳ 数字人生成中... ({status})")
            
            time.sleep(2)
        
        print(f"❌ 数字人生成超时")
        return None
```

### 第6步：OBS推流配置
#### OBS设置步骤：
1. **安装OBS Studio**（最新版）
2. **场景设置**：
   - 创建新场景：`TikTok_Digital_Human`
   - 添加来源：`浏览器` → 输入数字人视频URL
   - 添加来源：`文本` → 显示实时弹幕
   - 添加来源：`图像` → 商品图片轮播

3. **推流设置**：
   ```
   服务: 自定义
   服务器: rtmp://live.tiktok.com/rtmp/
   流密钥: [你的TikTok Stream Key]
   ```

4. **输出设置**：
   ```
   编码器: x264
   码率: 3000-6000 Kbps
   关键帧间隔: 2秒
   预设: veryfast
   配置: main
   ```

5. **音频设置**：
   ```
   采样率: 44.1kHz
   声道: 立体声
   音频码率: 160
   ```

### 第7步：全链路自动化闭环
```python
import asyncio
from datetime import datetime

class TikTokAutoLiveSystem:
    def __init__(self, config):
        self.config = config
        self.danmaku_client = None
        self.tts_client = None
        self.digital_human = None
        self.is_running = False
        
    async def start_live(self):
        """启动全自动直播"""
        print("🚀 启动TikTok AI数字人直播系统...")
        self.is_running = True
        
        # 初始化各模块
        await self.initialize_modules()
        
        # 开始弹幕监听循环
        await self.danmaku_loop()
        
    async def initialize_modules(self):
        """初始化所有模块"""
        print("🔧 初始化模块...")
        
        # 初始化弹幕客户端
        self.danmaku_client = TikTokDanmaku(
            api_key=self.config["tikhub_api_key"],
            room_id=self.config["room_id"]
        )
        
        # 初始化TTS
        self.tts_client = ElevenLabsTTS(
            api_key=self.config["elevenlabs_api_key"],
            voice_id=self.config["voice_id"]
        )
        
        # 初始化数字人
        self.digital_human = DIDDigitalHuman(
            api_key=self.config["did_api_key"]
        )
        
        print("✅ 所有模块初始化完成")
    
    async def danmaku_loop(self):
        """弹幕处理主循环"""
        print("🎯 开始监听弹幕...")
        
        async for comment in self.danmaku_client.fetch_comments():
            if not self.is_running:
                break
                
            # 处理弹幕
            await self.process_comment(comment)
    
    async def process_comment(self, comment):
        """处理单条弹幕"""
        user = comment["user"]
        content = comment["content"]
        
        print(f"💬 [{datetime.now()}] {user}: {content}")
        
        # 1. 过滤无效弹幕
        if not self.is_valid_comment(content):
            return
        
        # 2. LLM生成回答
        answer = await self.generate_answer(content)
        
        # 3. TTS生成语音
        audio_file = self.tts_client.text_to_speech(answer)
        
        if audio_file:
            # 4. 数字人驱动
            talk_id = self.digital_human.create_talk(
                image_url=self.config["avatar_image_url"],
                audio_url=f"file://{audio_file}"
            )
            
            if talk_id:
                # 5. 获取视频并推流
                video_url = self.digital_human.get_talk_result(talk_id)
                
                if video_url:
                    # 6. 更新OBS源（通过OBS WebSocket）
                    await self.update_obs_source(video_url)
    
    def is_valid_comment(self, content):
        """验证弹幕有效性"""
        # 过滤规则
        invalid_patterns = [
            "http://", "https://",  # 链接
            "@everyone", "@here",   # 提及
            len(content) > 100,     # 过长内容
            len(content) < 2,       # 过短内容
        ]
        
        for pattern in invalid_patterns:
            if isinstance(pattern, str) and pattern in content:
                return False
            elif isinstance(pattern, bool) and pattern:
                return False
        
        return True
    
    async def generate_answer(self, question):
        """LLM生成回答"""
        # 这里调用LLM API
        # 实际实现需要调用OpenAI等API
        return f"Thanks for your question about {question}! Check out our products in the shopping cart!"
    
    async def update_obs_source(self, video_url):
        """更新OBS浏览器源"""
        # 通过OBS WebSocket API更新
        print(f"🔄 更新OBS源: {video_url}")
        # 实际实现需要OBS WebSocket连接

# 配置示例
CONFIG = {
    "tikhub_api_key": "your_tikhub_key",
    "room_id": "your_room_id",
    "elevenlabs_api_key": "your_elevenlabs_key",
    "voice_id": "21m00Tcm4TlvDq8ikWAM",
    "did_api_key": "your_did_key",
    "avatar_image_url": "https://your-avatar-image.jpg",
    "obs_websocket_host": "localhost",
    "obs_websocket_port": 4455,
    "obs_websocket_password": "your_password"
}

# 启动系统
async def main():
    system = TikTokAutoLiveSystem(CONFIG)
    await system.start_l