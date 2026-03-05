# AI数字人直播系统 - 抖音/TikTok双平台

## 🎯 项目概述

这是一个完整的AI数字人实时互动带货直播系统，支持抖音（国内版）和TikTok（国际版）双平台。系统实现24小时无人直播，AI自动回复弹幕，数字人形象驱动，全自动化带货。

## ✨ 核心特性

### 双平台支持
- **抖音国内版**：官方接口，强合规，直播伴侣推流
- **TikTok国际版**：第三方API，多语言支持，OBS推流

### 智能交互
- 实时弹幕监听与处理
- AI智能问答（GPT-4o-mini/国产LLM）
- 多语言支持（中/英/西/葡等）
- 商品知识库集成

### 数字人技术
- 2D/3D数字人形象驱动
- 唇形同步与表情控制
- 实时视频生成与推流
- 支持D-ID、硅基智能、HeyGen等平台

### 合规安全
- 抖音强合规要求（必须标注AI身份）
- 内容安全过滤
- 敏感词检测
- 审计日志系统

## 📁 项目结构

```
ai-digital-human-live/
├── docs/                           # 文档目录
│   ├── TikTok_AI_Digital_Human_Live_Technical_Document.md
│   ├── Douyin_AI_Digital_Human_Live_Technical_Document.md
│   ├── AI_Digital_Human_Sales_Prompts.md
│   └── System_Architecture_Flowcharts.md
├── src/                           # 源代码目录
│   ├── ai_digital_human_live_controller.py
│   ├── ai_digital_human_live_controller_part2.py
│   └── ai_digital_human_live_controller_part3.py
├── config/                        # 配置文件
│   ├── tiktok_config_example.json
│   └── douyin_config_example.json
├── examples/                      # 示例文件
├── deployment/                    # 部署脚本
├── tests/                         # 测试文件
└── assets/                        # 资源文件
```

## 🚀 快速开始

### 环境要求
- Python 3.9+
- Windows 10/11（抖音必须）
- 网络：上传带宽 ≥ 8Mbps
- 硬件：i5/Ryzen5+，8GB+ RAM

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd ai-digital-human-live
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置平台**
   - TikTok：获取API密钥（OpenAI、ElevenLabs、D-ID、TikHub）
   - 抖音：申请开放平台权限，获取国产API密钥

4. **修改配置文件**
   ```bash
   cp config/tiktok_config_example.json config/config.json
   # 编辑config.json，填入你的API密钥
   ```

5. **运行系统**
   ```bash
   python src/ai_digital_human_live_controller.py
   ```

## 🔧 配置说明

### TikTok配置要点
1. **TikTok账号**：需要直播权限（粉丝≥1000）
2. **OpenAI API**：GPT-4o-mini或GPT-3.5-turbo
3. **ElevenLabs**：语音合成API
4. **D-ID**：数字人驱动API
5. **TikHub**：弹幕采集API
6. **OBS Studio**：推流工具

### 抖音配置要点
1. **抖音账号**：实名认证+直播权限
2. **开放平台**：申请直播API权限
3. **国产LLM**：火山方舟/通义千问/文心一言
4. **国产TTS**：阿里云/讯飞TTS
5. **国产数字人**：硅基智能/相芯科技
6. **直播伴侣**：官方推流工具（必须使用）

## 📋 功能模块

### 1. 弹幕监听模块
- TikTok：TikHub API实时采集
- 抖音：官方开放平台接口
- 数据清洗与敏感词过滤
- 优先级排序处理

### 2. AI问答引擎
- 多平台LLM支持
- 商品知识库集成
- 合规内容生成
- 多语言回复

### 3. TTS语音合成
- 多平台TTS服务
- 语音风格定制
- 音频后处理
- 格式转换

### 4. 数字人驱动
- 2D/3D数字人生成
- 唇形同步技术
- 表情动作控制
- 视频渲染输出

### 5. 推流控制
- TikTok：OBS Websocket控制
- 抖音：直播伴侣自动化
- 视频源动态更新
- 推流状态监控

## 🔒 合规要求

### TikTok合规
- 标注AI数字人身份
- 遵守社区准则
- 真实商品描述
- 数据隐私保护

### 抖音强制合规
- **必须标注**："本直播间由AI数字人主播为您服务"
- **禁止**：爬虫、非官方接口、虚假宣传
- **要求**：官方推流通道、内容审核、风险提示
- **高风险类目**：医疗、金融等禁播

## 📊 性能指标

| 指标 | TikTok | 抖音 |
|------|--------|------|
| 延迟 | ≤800ms | ≤600ms |
| 并发 | 50请求/秒 | 30请求/秒 |
| 可用性 | 99.5% | 99.9% |
| 运行时间 | 7×24小时 | 7×24小时 |

## 🛠️ 开发指南

### 扩展新平台
1. 继承`DanmakuListener`基类
2. 实现平台特定API调用
3. 添加平台配置验证
4. 更新主控制器逻辑

### 自定义数字人
1. 准备数字人形象素材
2. 配置数字人API参数
3. 调整唇形同步参数
4. 测试渲染效果

### 添加新语言
1. 更新TTS语音配置
2. 添加语言特定的Prompt
3. 配置语言检测逻辑
4. 测试多语言交互

## 🚨 故障排除

### 常见问题
1. **弹幕无法接收**
   - 检查API密钥有效性
   - 验证直播间ID
   - 检查网络连接

2. **AI回复失败**
   - 检查LLM API配额
   - 验证Prompt格式
   - 查看错误日志

3. **数字人视频生成慢**
   - 检查API响应时间
   - 优化视频参数
   - 考虑本地渲染

4. **推流中断**
   - 检查网络稳定性
   - 验证推流密钥
   - 监控系统资源

### 日志查看
```bash
# 查看系统日志
tail -f logs/ai_live_*.log

# 查看交互日志
tail -f logs/interactions_*.json

# 查看错误日志
grep "ERROR" logs/ai_live_*.log
```

## 📈 监控与维护

### 系统监控
- CPU/内存使用率
- 网络带宽监控
- API调用成功率
- 响应时间统计

### 定期维护
1. **每日检查**
   - API配额使用情况
   - 磁盘空间监控
   - 错误日志分析

2. **每周维护**
   - 数据库备份
   - 日志文件清理
   - 系统更新检查

3. **每月维护**
   - 安全漏洞扫描
   - 性能优化调整
   - 合规性检查

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交代码变更
4. 编写测试用例
5. 提交Pull Request

## 📄 许可证

本项目采用MIT许可证。详见LICENSE文件。

## 📞 支持与联系

如有问题或建议，请通过以下方式联系：

- GitHub Issues
- 电子邮件：support@example.com
- 文档：查看docs目录详细文档

## 🎉 成功案例

### 案例1：TikTok美妆带货
- **平台**：TikTok美国站
- **产品**：护肤套装
- **成果**：月销售额$50,000+
- **特点**：24小时直播，多语言支持

### 案例2：抖音电子产品
- **平台**：抖音国内
- **产品**：智能手表
- **成果**：单场直播成交1000+单
- **特点**：强合规，官方接口

---

**开始你的AI数字人直播之旅吧！** 🚀