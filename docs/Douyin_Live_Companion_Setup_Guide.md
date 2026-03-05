# 抖音直播伴侣安装与配置指南

## 一、直播伴侣下载与安装

### 1.1 官方下载地址
- **官方网站**: https://streamingtool.douyin.com/
- **最新版本**: 直播伴侣 3.0.0+
- **系统要求**: Windows 10/11 (64位)

### 1.2 安装步骤
```
1. 访问官网下载安装包
2. 运行 DouyinLiveCompanion_Setup.exe
3. 选择安装路径（建议：D:\Douyin\LiveCompanion\）
4. 完成安装并启动
5. 使用抖音APP扫码登录
```

### 1.3 安装路径示例
```bash
# 推荐安装路径
C:\Program Files\Douyin\LiveCompanion\LiveCompanion.exe

# 或自定义路径
D:\Software\Douyin\LiveCompanion\LiveCompanion.exe
```

## 二、直播权限申请

### 2.1 账号要求
- ✅ 抖音账号完成实名认证
- ✅ 粉丝数 ≥ 1000（开通直播权限）
- ✅ 账号无违规记录
- ✅ 绑定手机号

### 2.2 电脑直播权限开通
```
手机抖音APP操作流程：
1. 打开抖音APP → 我 → 右上角三横线
2. 创作者服务中心 → 主播中心
3. 电脑直播 → 立即开通
4. 完成人脸识别验证
5. 等待审核（通常1-3个工作日）
```

### 2.3 直播伴侣登录
```
1. 启动直播伴侣
2. 点击"扫码登录"
3. 使用抖音APP扫描二维码
4. 确认登录
5. 完成设备检测
```

## 三、直播伴侣基础配置

### 3.1 首次启动配置
```
1. 设备检测
   - 摄像头：选择虚拟摄像头或物理摄像头
   - 麦克风：选择虚拟音频输入
   - 扬声器：选择系统默认

2. 场景设置
   - 创建新场景：AI数字人直播
   - 添加素材：视频文件、图片、文字

3. 推流设置
   - 选择"电脑直播"
   - 设置直播标题和封面
   - 配置商品橱窗
```

### 3.2 推荐配置参数
| 参数 | 推荐值 | 说明 |
|------|--------|------|
| 分辨率 | 1080×1920 | 竖屏直播标准 |
| 帧率 | 30fps | 流畅观看 |
| 码率 | 6000kbps | 高清画质 |
| 音频码率 | 128kbps | 清晰音质 |
| 关键帧间隔 | 2秒 | 网络适应性 |

### 3.3 场景布局示例
```
┌─────────────────────────────────┐
│        抖音直播伴侣界面           │
├─────────────────────────────────┤
│                                 │
│  ┌─────────────┐               │
│  │             │               │
│  │  数字人视频   │               │
│  │  (主画面)    │               │
│  │             │               │
│  └─────────────┘               │
│                                 │
│  ┌─────────────────────────┐   │
│  │      商品展示区           │   │
│  │  (右下角小窗口)          │   │
│  └─────────────────────────┘   │
│                                 │
│  ┌─────────────────────────┐   │
│  │      弹幕显示区           │   │
│  │  (顶部滚动)             │   │
│  └─────────────────────────┘   │
│                                 │
└─────────────────────────────────┘
```

## 四、自动化控制配置

### 4.1 Python自动化库安装
```bash
# 安装必要的Python库
pip install pyautogui pygetwindow opencv-python pillow
```

### 4.2 直播伴侣控制脚本
```python
# live_companion_controller.py
import pyautogui
import time
import os

class DouyinLiveCompanionController:
    def __init__(self, companion_path=None):
        """初始化直播伴侣控制器"""
        self.companion_path = companion_path or self.find_companion_path()
        self.window_title = "抖音直播伴侣"
        
    def find_companion_path(self):
        """查找直播伴侣安装路径"""
        possible_paths = [
            r"C:\Program Files\Douyin\LiveCompanion\LiveCompanion.exe",
            r"C:\Program Files (x86)\Douyin\LiveCompanion\LiveCompanion.exe",
            r"D:\Douyin\LiveCompanion\LiveCompanion.exe",
            r"E:\Douyin\LiveCompanion\LiveCompanion.exe"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        raise FileNotFoundError("未找到抖音直播伴侣，请手动安装")
    
    def start_companion(self):
        """启动直播伴侣"""
        import subprocess
        subprocess.Popen([self.companion_path])
        time.sleep(10)  # 等待启动
        
        # 激活窗口
        self.activate_window()
        
    def activate_window(self):
        """激活直播伴侣窗口"""
        try:
            import pygetwindow as gw
            windows = gw.getWindowsWithTitle(self.window_title)
            if windows:
                window = windows[0]
                window.activate()
                time.sleep(1)
                return True
        except:
            pass
        return False
    
    def start_live_stream(self, title="AI数字人直播", cover_image=None):
        """开始直播"""
        # 点击"开始直播"按钮（坐标需要根据实际界面调整）
        # 注意：坐标会根据屏幕分辨率和界面布局变化
        
        # 步骤1: 点击"开播"按钮
        pyautogui.click(x=100, y=100)  # 示例坐标，需要调整
        
        # 步骤2: 输入直播标题
        pyautogui.click(x=200, y=150)
        pyautogui.write(title)
        
        # 步骤3: 选择封面（如果有）
        if cover_image:
            pyautogui.click(x=200, y=200)
            # 这里需要实现文件选择对话框的自动化
        
        # 步骤4: 点击"开始直播"
        pyautogui.click(x=300, y=300)
        time.sleep(5)
        
        # 步骤5: 确认开始
        pyautogui.click(x=350, y=350)
        
        print("直播已开始")
        
    def stop_live_stream(self):
        """停止直播"""
        # 点击"结束直播"按钮
        pyautogui.click(x=400, y=100)  # 示例坐标
        
        # 确认结束
        pyautogui.click(x=450, y=150)
        
        print("直播已结束")
    
    def update_video_source(self, video_path):
        """更新视频源"""
        # 步骤1: 点击"添加素材"
        pyautogui.click(x=500, y=100)
        
        # 步骤2: 选择"视频文件"
        pyautogui.click(x=550, y=150)
        
        # 步骤3: 输入文件路径
        pyautogui.click(x=600, y=200)
        pyautogui.write(video_path)
        
        # 步骤4: 确认添加
        pyautogui.click(x=650, y=250)
        
        print(f"已更新视频源: {video_path}")
    
    def get_screen_coordinates(self):
        """获取界面元素坐标（调试用）"""
        print("将鼠标移动到目标位置，按Ctrl+C获取坐标")
        try:
            while True:
                x, y = pyautogui.position()
                print(f"当前位置: ({x}, {y})", end='\r')
                time.sleep(0.1)
        except KeyboardInterrupt:
            print(f"\n最终坐标: ({x}, {y})")
            return x, y

# 使用示例
if __name__ == "__main__":
    controller = DouyinLiveCompanionController()
    
    # 启动直播伴侣
    controller.start_companion()
    
    # 开始直播
    controller.start_live_stream("AI数字人24小时带货直播")
    
    # 更新视频源
    controller.update_video_source("temp/digital_human_video.mp4")
    
    # 运行一段时间后停止
    time.sleep(3600)  # 运行1小时
    controller.stop_live_stream()
```

### 4.3 坐标校准工具
```python
# coordinate_calibrator.py
import pyautogui
import time

def calibrate_coordinates():
    """坐标校准工具"""
    print("抖音直播伴侣界面坐标校准工具")
    print("=" * 50)
    
    coordinates = {}
    
    # 定义需要校准的按钮
    buttons = {
        "start_button": "开始直播按钮",
        "stop_button": "结束直播按钮",
        "add_material": "添加素材按钮",
        "video_file": "视频文件选项",
        "file_path": "文件路径输入框",
        "confirm_add": "确认添加按钮"
    }
    
    for key, description in buttons.items():
        print(f"\n请将鼠标移动到 [{description}] 上，然后按 Enter 键")
        input("准备好后按 Enter...")
        x, y = pyautogui.position()
        coordinates[key] = {"x": x, "y": y, "description": description}
        print(f"已记录: {description} -> ({x}, {y})")
    
    # 保存坐标配置
    import json
    with open("live_companion_coordinates.json", "w", encoding="utf-8") as f:
        json.dump(coordinates, f, ensure_ascii=False, indent=2)
    
    print(f"\n坐标配置已保存到: live_companion_coordinates.json")
    
    return coordinates

if __name__ == "__main__":
    calibrate_coordinates()
```

## 五、推流配置

### 5.1 获取推流地址和密钥
```
直播伴侣内操作：
1. 点击"开始直播"
2. 在推流设置中获取：
   - 服务器地址: rtmp://push.douyin.com/rtmp/
   - 流密钥: 一串唯一的字符数字组合
3. 保存到配置文件
```

### 5.2 配置文件示例
```json
{
  "douyin_stream": {
    "server": "rtmp://push.douyin.com/rtmp/",
    "stream_key": "your_unique_stream_key_here",
    "full_url": "rtmp://push.douyin.com/rtmp/your_unique_stream_key_here"
  }
}
```

### 5.3 推流测试
```bash
# 使用FFmpeg测试推流
ffmpeg -re -i test_video.mp4 -c:v libx264 -preset veryfast \
  -maxrate 6000k -bufsize 12000k -pix_fmt yuv420p \
  -g 60 -c:a aac -b:a 128k -ar 44100 \
  -f flv "rtmp://push.douyin.com/rtmp/your_stream_key"
```

## 六、常见问题解决

### 6.1 安装问题
**问题**: 安装失败，提示"无法访问指定设备"
**解决**: 
1. 关闭杀毒软件和防火墙
2. 以管理员身份运行安装程序
3. 检查磁盘空间（需要至少2GB）

**问题**: 启动时闪退
**解决**:
1. 更新显卡驱动
2. 安装Visual C++ Redistributable
3. 重新安装直播伴侣

### 6.2 直播问题
**问题**: 无法开始直播，提示"未开通权限"
**解决**:
1. 确认粉丝数≥1000
2. 完成实名认证和人脸识别
3. 在手机APP上重新申请电脑直播权限

**问题**: 直播卡顿、掉帧
**解决**:
1. 降低码率到4000kbps
2. 关闭其他占用网络的程序
3. 使用有线网络连接
4. 更新直播伴侣到最新版本

**问题**: 声音不同步
**解决**:
1. 检查音频采样率设置为44100Hz
2. 调整音频延迟设置
3. 使用独立的声卡或音频接口

### 6.3 自动化问题
**问题**: 坐标不准，点击错误位置
**解决**:
1. 使用校准工具重新获取坐标
2. 确保屏幕分辨率不变
3. 直播伴侣界面不要缩放

**问题**: 无法找到直播伴侣窗口
**解决**:
1. 检查窗口标题是否正确
2. 使用pygetwindow列出所有窗口
3. 确保直播伴侣已启动并可见

## 七、最佳实践建议

### 7.1 硬件配置建议
- **CPU**: Intel i7或AMD Ryzen 7以上
- **内存**: 16GB以上
- **显卡**: NVIDIA GTX 1060或以上（支持硬件编码）
- **网络**: 上传带宽≥10Mbps
- **存储**: SSD硬盘，至少50GB可用空间

### 7.2 软件配置建议
1. **系统优化**:
   - 关闭不必要的后台程序
   - 设置高性能电源模式
   - 更新操作系统和驱动

2. **直播伴侣设置**:
   - 使用管理员身份运行
   - 添加到杀毒软件白名单
   - 定期清理缓存文件

3. **网络优化**:
   - 使用有线网络连接
   - 设置QoS优先级
   - 关闭P2P下载软件

### 7.3 监控与维护
1. **实时监控**:
   - CPU和内存使用率
   - 网络上传速度
   - 推流帧率和码率
   - 直播延迟

2. **定期维护**:
   - 清理临时文件
   - 更新软件版本
   - 备份配置文件
   - 检查磁盘空间

## 八、合规注意事项

### 8.1 必须遵守的规定
1. **AI身份声明**: 必须明确标注"本直播间由AI数字人主播为您服务"
2. **内容合规**: 禁止政治、色情、暴力、虚假宣传等内容
3. **商品描述**: 真实准确，不夸大功效
4. **价格透明**: 明确标注价格，不误导消费者

### 8.2 风险提示要求
1. **特殊商品**: 化妆品、保健品等需要风险提示
2. **使用说明**: 明确使用方法和注意事项
3. **售后政策**: 清晰说明退换货规则
4. **免责声明**: AI回复仅供参考，以商品页面为准

### 8.3 数据安全
1. **用户隐私**: 不收集、不存储用户个人信息
2. **数据加密**: API通信使用HTTPS加密
3. **访问控制**: 限制API访问权限
4. **日志管理**: 定期清理操作日志

## 九、故障应急方案

### 9.1 直播中断处理
```
应急流程：
1. 自动检测推流状态
2. 发现中断后立即重连
3. 重连失败切换备用视频
4. 发送告警通知管理员
5. 记录故障日志
```

### 9.2 备用方案配置
```json
{
  "fallback_config": {
    "enable_fallback": true,
    "fallback_video": "assets/fallback_video.mp4",
    "fallback_message": "系统维护中，请稍候...",
    "auto_recover": true,
    "recover_delay": 30
  }
}
```

### 9.3 人工接管流程
```
1. 系统检测到严重故障
2. 自动发送告警到管理员
3. 切换到人工接管模式
4. 管理员手动干预
5. 故障修复后切回自动模式
```

---

**重要提示**: 直播伴侣界面可能随版本更新而变化，自动化脚本的坐标需要定期校准。建议在测试环境充分测试后再投入生产使用。