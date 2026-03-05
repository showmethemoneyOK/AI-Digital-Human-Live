# OBS Studio 安装与配置指南 (TikTok版)

## 一、OBS Studio 下载与安装

### 1.1 官方下载地址
- **官方网站**: https://obsproject.com/
- **最新版本**: OBS Studio 30.0+
- **系统要求**: Windows 10/11, macOS, Linux

### 1.2 Windows安装步骤
```
1. 访问官网下载 Windows 安装包
2. 运行 obs-studio-xxx-windows-x64.exe
3. 选择安装组件（建议全选）
4. 设置安装路径（建议：D:\OBS\）
5. 完成安装
```

### 1.3 推荐安装路径
```bash
# 默认路径
C:\Program Files\obs-studio\bin\64bit\obs64.exe

# 自定义路径（推荐）
D:\Software\OBS Studio\bin\64bit\obs64.exe
```

## 二、OBS基础配置

### 2.1 首次启动向导
```
1. 运行OBS Studio
2. 自动运行配置向导
3. 选择优化设置：
   - 用途：流媒体
   - 分辨率：1080×1920（竖屏）
   - 帧率：30fps
   - 编码器：硬件（NVENC）或软件（x264）
4. 完成配置
```

### 2.2 视频设置
```
文件 → 设置 → 视频
├─ 基础画布分辨率：1080×1920
├─ 输出缩放分辨率：1080×1920
├─ 常用FPS值：30
└─ 缩小方法：双线性
```

### 2.3 输出设置
```
文件 → 设置 → 输出
├─ 输出模式：高级
├─ 编码器：硬件（NVENC H.264）或软件（x264）
├─ 码率控制：CBR
├─ 比特率：4000-6000 Kbps
├─ 关键帧间隔：2秒
├─ 预设：质量 或 max-quality
└─ 配置：高
```

## 三、场景与源配置

### 3.1 创建直播场景
```
1. 在"场景"面板点击"+"按钮
2. 命名场景：TikTok_AI_Live
3. 添加以下源：
```

### 3.2 必需源配置

#### 1. 数字人视频源
```
类型：媒体源
名称：Digital_Human_Video
设置：
├─ 本地文件：选择数字人生成的视频
├─ 循环：是
├─ 重启播放当源变为活动时：是
└─ 关闭文件当不活动时：否
```

#### 2. 背景图像源
```
类型：图像
名称：Background
设置：
├─ 图像文件：选择背景图片
└─ 适合：拉伸到屏幕
```

#### 3. 商品展示源
```
类型：浏览器
名称：Product_Display
设置：
├─ URL：http://localhost:8080/products
├─ 宽度：400
├─ 高度：600
└─ 自定义CSS：添加样式
```

#### 4. 弹幕显示源
```
类型：文本（GDI+）
名称：Danmaku_Display
设置：
├─ 文本：欢迎来到AI数字人直播间！
├─ 字体：Microsoft YaHei，24px
├─ 颜色：白色
├─ 背景颜色：半透明黑色
└─ 聊天模式：是
```

### 3.3 场景布局示例
```
┌─────────────────────────────────┐
│        OBS Studio 预览           │
├─────────────────────────────────┤
│                                 │
│  ┌─────────────────────────┐   │
│  │                         │   │
│  │     数字人视频           │   │
│  │    (主画面)             │   │
│  │                         │   │
│  └─────────────────────────┘   │
│                                 │
│  ┌─────┐ ┌─────┐ ┌─────┐     │
│  │商品1 │ │商品2 │ │商品3 │     │
│  │     │ │     │ │     │     │
│  └─────┘ └─────┘ └─────┘     │
│                                 │
│  ┌─────────────────────────┐   │
│  │ 弹幕滚动区域             │   │
│  │                         │   │
│  └─────────────────────────┘   │
│                                 │
└─────────────────────────────────┘
```

## 四、推流配置（TikTok）

### 4.1 获取TikTok推流信息
```
TikTok Creator Center操作：
1. 登录 TikTok Creator Center
2. 进入 Live Studio
3. 创建直播活动
4. 获取：
   - 服务器：rtmp://live.tiktok.com/rtmp/
   - 流密钥：唯一的密钥字符串
```

### 4.2 OBS推流设置
```
文件 → 设置 → 流
├─ 服务类型：自定义
├─ 服务器：rtmp://live.tiktok.com/rtmp/
├─ 流密钥：粘贴从TikTok获取的密钥
└─ 自动重连：启用
```

### 4.3 推流测试命令
```bash
# 使用FFmpeg测试TikTok推流
ffmpeg -re -i test.mp4 -c:v libx264 -preset veryfast \
  -maxrate 4000k -bufsize 8000k -pix_fmt yuv420p \
  -g 60 -c:a aac -b:a 128k -ar 44100 \
  -f flv "rtmp://live.tiktok.com/rtmp/your_stream_key"
```

## 五、OBS Websocket 插件安装

### 5.1 插件下载
- **官方地址**: https://github.com/obsproject/obs-websocket/releases
- **版本**: obs-websocket 5.0+

### 5.2 安装步骤
```
1. 下载 obs-websocket-x.x.x-Windows.zip
2. 解压到 OBS 安装目录
3. 运行 data\obs-plugins\obs-websocket\enable_websocket.bat
4. 重启 OBS Studio
```

### 5.3 配置Websocket
```
OBS内设置：
工具 → WebSocket服务器设置
├─ 启用WebSocket服务器：是
├─ 服务器端口：4455（默认）
├─ 密码：设置安全密码
└─ 启用身份验证：是
```

## 六、Python自动化控制

### 6.1 安装Python库
```bash
pip install obs-websocket-py
```

### 6.2 OBS控制脚本
```python
# obs_controller.py
import asyncio
from obswebsocket import obsws, requests

class OBSController:
    def __init__(self, host="localhost", port=4455, password=""):
        self.host = host
        self.port = port
        self.password = password
        self.ws = None
        
    async def connect(self):
        """连接OBS Websocket"""
        self.ws = obsws(self.host, self.port, self.password)
        self.ws.connect()
        print("OBS Websocket连接成功")
        
    async def disconnect(self):
        """断开连接"""
        if self.ws:
            self.ws.disconnect()
            print("OBS Websocket断开连接")
            
    async def start_streaming(self):
        """开始推流"""
        self.ws.call(requests.StartStream())
        print("开始推流")
        
    async def stop_streaming(self):
        """停止推流"""
        self.ws.call(requests.StopStream())
        print("停止推流")
        
    async def set_current_scene(self, scene_name):
        """切换场景"""
        self.ws.call(requests.SetCurrentProgramScene(sceneName=scene_name))
        print(f"切换到场景: {scene_name}")
        
    async def update_media_source(self, source_name, file_path):
        """更新媒体源"""
        self.ws.call(requests.SetInputSettings(
            inputName=source_name,
            inputSettings={"local_file": file_path}
        ))
        print(f"更新媒体源 {source_name}: {file_path}")
        
    async def get_scene_list(self):
        """获取场景列表"""
        response = self.ws.call(requests.GetSceneList())
        return response.getScenes()
        
    async def get_source_list(self, scene_name):
        """获取场景中的源列表"""
        response = self.ws.call(requests.GetSceneItemList(sceneName=scene_name))
        return response.getSceneItems()

# 使用示例
async def main():
    controller = OBSController(password="your_password")
    
    try:
        # 连接OBS
        await controller.connect()
        
        # 获取场景列表
        scenes = await controller.get_scene_list()
        print("可用场景:", scenes)
        
        # 切换到AI直播场景
        await controller.set_current_scene("TikTok_AI_Live")
        
        # 更新数字人视频
        await controller.update_media_source(
            "Digital_Human_Video",
            "temp/digital_human_video.mp4"
        )
        
        # 开始推流
        await controller.start_streaming()
        
        # 保持运行
        await asyncio.sleep(3600)  # 运行1小时
        
        # 停止推流
        await controller.stop_streaming()
        
    finally:
        await controller.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

### 6.3 高级控制功能
```python
# obs_advanced_controller.py
import asyncio
from obswebsocket import obsws, requests

class OBSAdvancedController(OBSController):
    async def get_stream_status(self):
        """获取推流状态"""
        response = self.ws.call(requests.GetStreamStatus())
        return {
            "streaming": response.getOutputActive(),
            "recording": response.getOutputActive(),
            "bytes_per_sec": response.getOutputBytes(),
            "fps": response.getOutputFps()
        }
    
    async def set_stream_settings(self, server, key):
        """设置推流参数"""
        self.ws.call(requests.SetStreamServiceSettings(
            streamServiceType="rtmp_custom",
            streamServiceSettings={
                "server": server,
                "key": key
            }
        ))
        
    async def create_scene(self, scene_name):
        """创建新场景"""
        self.ws.call(requests.CreateScene(sceneName=scene_name))
        
    async def create_source(self, scene_name, source_name, source_type, settings=None):
        """创建源"""
        self.ws.call(requests.CreateInput(
            sceneName=scene_name,
            inputName=source_name,
            inputKind=source_type,
            inputSettings=settings or {}
        ))
    
    async def set_source_visibility(self, scene_name, source_name, visible):
        """设置源可见性"""
        # 首先获取源ID
        items = await self.get_source_list(scene_name)
        source_id = None
        for item in items:
            if item['sourceName'] == source_name:
                source_id = item['sceneItemId']
                break
        
        if source_id:
            self.ws.call(requests.SetSceneItemEnabled(
                sceneName=scene_name,
                sceneItemId=source_id,
                sceneItemEnabled=visible
            ))
    
    async def take_screenshot(self, source_name, file_path):
        """截图"""
        self.ws.call(requests.SaveSourceScreenshot(
            sourceName=source_name,
            imageFilePath=file_path,
            imageFormat="png",
            imageWidth=1920,
            imageHeight=1080
        ))
```

## 七、性能优化

### 7.1 编码器选择
| 编码器 | 优点 | 缺点 | 适用场景 |
|--------|------|------|----------|
| **NVENC** | GPU编码，CPU占用低 | 需要NVIDIA显卡 | 游戏直播，高性能 |
| **x264** | 软件编码，质量高 | CPU占用高 | 非游戏内容，CPU强 |
| **AMD AMF** | AMD显卡专用 | 兼容性一般 | AMD显卡用户 |
| **Intel QSV** | Intel核显编码 | 质量一般 | 轻薄本，核显 |

### 7.2 推荐设置组合
```yaml
# 高性能配置（RTX显卡）
encoder: "nvenc"
rate_control: "CBR"
bitrate: 6000
preset: "p5"  # max-quality
profile: "high"
look_ahead: false
psycho_aq: true

# 平衡配置（无独立显卡）
encoder: "x264"
rate_control: "CBR"
bitrate: 4000
preset: "veryfast"
profile: "high"
tune: "zerolatency"
```

### 7.3 系统优化建议
1. **Windows设置**:
   - 电源模式：高性能
   - 游戏模式：关闭
   - 硬件加速GPU调度：开启

2. **OBS设置**:
   - 以管理员身份运行
   - 图形API：Direct3D 11
   - 颜色格式：NV12
   - 颜色空间：709

3. **网络优化**:
   - 使用有线网络
   - 关闭后台更新
   - 设置网络优先级

## 八、常见问题解决

### 8.1 推流问题
**问题**: 推流失败，提示"连接失败"
**解决**:
1. 检查推流密钥是否正确
2. 验证网络连接
3. 关闭防火墙或杀毒软件
4. 尝试不同的服务器地址

**问题**: 直播卡顿、掉帧
**解决**:
1. 降低码率（4000→3000）
2. 降低分辨率（1080p→720p）
3. 降低帧率（30→25）
4. 更换编码器预设（quality→performance）

**问题**: 声音不同步
**解决**:
1. 检查音频采样率（44100Hz）
2. 调整音频同步偏移
3. 使用独立的音频接口
4. 更新声卡驱动

### 8.2 性能问题
**问题**: OBS占用CPU过高
**解决**:
1. 使用硬件编码（NVENC）
2. 降低输出分辨率
3. 关闭预览窗口
4. 减少场景中的源数量

**问题**: 游戏卡顿（游戏捕获）
**解决**:
1. 使用游戏捕获而不是窗口捕获
2. 开启游戏模式
3. 降低游戏画质设置
4. 使用显示器捕获替代

### 8.3 插件问题
**问题**: Websocket连接失败
**解决**:
1. 确认插件安装正确
2. 检查端口是否被占用
3. 验证密码是否正确
4. 重启OBS和插件服务

## 九、监控与维护

### 9.1 实时监控指标
```python
# 监控脚本示例
async def monitor_obs():
    controller = OBSController()
    await controller.connect()
    
    while True:
        try:
            # 获取状态
            status = await controller.get_stream_status()
            
            # 检查关键指标
            if status['streaming']:
                print(f"推流中 - FPS: {status['fps']}, 码率: {status['bytes_per_sec']/1024:.1f}KB/s")
            
            # 检查性能
            import psutil
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            
            if cpu_percent > 80:
                print(f"警告: CPU使用率过高: {cpu_percent}%")
            
            if memory_percent > 85:
                print(f"警告: 内存使用率过高: {memory_percent}%")
            
            await asyncio.sleep(5)
            
        except Exception as e:
            print(f"监控错误: {e}")
            await asyncio.sleep(10)
```

### 9.2 日志管理
```
OBS日志位置：
C:\Users\<用户名>\AppData\Roaming\obs-studio\logs\

重要日志文件：
- 最新日志：%appdata%\obs-studio\logs\当前日期.log
- 崩溃日志：%appdata%\obs-studio\crashes\
- 配置备份：%appdata%\obs-studio\basic\profiles\
```

### 9.3 定期维护
1. **每日检查**:
   - 清理临时文件
   - 检查磁盘空间
   - 验证推流设置

2. **每周维护**:
   - 更新OBS和插件
   - 备份配置文件
   - 清理日志文件

3. **每月维护**:
   - 性能优化调整
   - 场景布局更新
   - 硬件检查

## 十、高级功能

### 10.1 虚拟摄像头
```
OBS虚拟摄像头设置：
1. 工具 → 虚拟摄像头
2. 点击"启动"
3. 在其他软件中选择"OBS Virtual Camera"
```

### 10.2 场景过渡
```python
# 场景过渡控制
async def scene_transition(controller, from_scene, to_scene, transition_name="Fade"):
    """场景过渡"""
    # 设置过渡
    controller.ws.call(requests.SetCurrentSceneTransition(
        transitionName=transition_name
    ))
    
    # 设置过渡时间
    controller.ws.call(requests.SetCurrentSceneTransitionDuration(
        transitionDuration=1000  # 1秒
    ))
    
    # 执行过渡
    controller.ws.call(requests.SetCurrentProgramScene(
        sceneName=to_scene
    ))
```

### 10.3 音频混音
```python
# 音频控制
async def audio_control(controller):
