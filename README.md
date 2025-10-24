# 芦笋分拣机项目 (Pi Sorter)

基于OpenCV和MQTT的智能芦笋质量分级系统，运行在树莓派平台上，集成摄像头和远程通信功能。

## 🤖 AI智能体协作指南

本项目配置了完整的AI智能体上下文系统，支持智能化的开发协作。

### 快速开始 (AI智能体)

**新对话时，AI智能体应该首先执行：**

```bash
# 1. 读取项目上下文
cat .ai-context.yaml

# 2. 检查开发环境
cat config/ssh_config.txt

# 3. 确认SSH连接（如需要）
ssh -i config/pi_id_ed25519 feng@192.168.2.192
```

### 📁 AI协作关键文件

| 文件 | 用途 |
|------|------|
| `.ai-context.yaml` | **AI智能体项目上下文配置** |
| `docs/AI智能体启动指南.md` | 通用环境识别指南 |
| `docs/AI智能体上下文使用示例.md` | 使用示例和最佳实践 |
| `config/ssh_config.txt` | SSH远程开发配置 |

### 🔧 开发环境信息

- **开发模式：** SSH远程开发
- **目标设备：** 树莓派4 (192.168.2.192)
- **用户：** feng
- **Python版本：** 3.13.5
- **项目路径：** /home/feng/remote_debug_test

## 🎯 项目概述

本项目是一个智能芦笋分拣系统，通过图像处理和特征提取技术，自动识别和分级芦笋的质量等级，并通过MQTT协议实现远程监控和数据传输。

### ✨ 核心功能

#### 基础功能
- **图像采集**: 摄像头实时采集芦笋图像
- **特征检测**: 基于OpenCV的形状、颜色、尺寸分析
- **质量分级**: 基于特征的规则分类算法
- **数据管理**: 分级结果的存储和管理

#### 集成功能 (来自ssh pi test项目)
- **摄像头控制**: PiCamera和CameraManager类，支持多摄像头管理
- **MQTT通信**: 实时数据发布和远程命令接收
- **系统监控**: 性能监控、状态报告、错误处理
- **配置管理**: 统一的YAML配置文件管理

### 🛠 技术栈

- **图像处理**: OpenCV 4.x
- **通信协议**: MQTT (paho-mqtt)
- **配置管理**: YAML
- **数据存储**: CSV, JSON
- **开发语言**: Python 3.8+
- **硬件平台**: Raspberry Pi 4B

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd pi_sorter

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置系统

编辑配置文件 `config/integrated_config.yaml`:

```yaml
# 摄像头配置
camera:
  enabled: true
  device_id: 0
  resolution: [1280, 1024]
  fps: 30

# MQTT配置
mqtt:
  enabled: true
  broker_host: "localhost"
  broker_port: 1883
  client_id: "pi_sorter_001"

# 系统配置
system:
  debug: false
  log_level: "INFO"
```

### 3. 运行系统

#### 3.2 完整系统

```bash
# 运行基础测试
python tests/simple_test.py

# 启动完整系统
python main.py
```

### 4. 测试验证

```bash
# 运行集成测试
python tests/test_integrated_system.py

# 或使用脚本
./run_test.ps1    # PowerShell
```

## 📁 项目结构

```
pi_sorter/
├── README.md                          # 项目说明 (本文档)
├── main.py                            # 主程序入口 (已集成)
├── requirements.txt                   # 项目依赖 (已更新)
├── run_test.ps1                       # 测试运行脚本
├── config/
│   ├── integrated_config.yaml         # 集成系统配置
│   ├── mqtt_config.json              # MQTT配置
│   └── ssh_config.txt                 # SSH配置
├── src/
│   ├── image_processing/              # 图像处理模块
│   ├── feature_detection/             # 特征检测模块
│   ├── classification/                # 质量分级模块
│   ├── data_management/               # 数据管理模块
│   └── external/                      # 外部集成模块
│       ├── ssh_pi_test_camera.py      # 摄像头功能 (引用自ssh pi test)
│       ├── ssh_pi_test_mqtt.py        # MQTT功能 (引用自ssh pi test)
│       ├── integrated_system.py       # 集成系统主类
│       ├── config_manager.py          # 配置管理器
│       
├── docs/                              # 文档目录 (重新组织)
│   ├── 01-项目概述/                   # 项目介绍和规格
│   ├── 02-需求与设计/                 # 需求文档和设计
│   ├── 03-开发环境/                   # 环境配置指南
│   ├── 04-技术实现/                   # 技术实现细节
│   ├── 05-配置说明/                   # 配置文档
│   ├── 06-使用指南/                   # 使用和API文档
│   └── 07-测试与部署/                 # 测试和部署指南
├── tests/                             # 测试目录
│   ├── simple_test.py                 # 简化测试脚本
│   ├── test_integrated_system.py      # 集成系统测试
│   ├── test_env.py                    # 环境测试脚本
│   ├── auto_camera_test.py            # 摄像头自动测试
│   ├── test_ai_context.py             # AI上下文验证脚本
│   └── verify_structure.bat           # 项目结构验证
└── 历史文档/                          # 历史文档存档
```

## 🔧 开发环境

### 目标运行环境
- **硬件平台**: 树莓派 4B (推荐8GB内存)
- **操作系统**: Raspberry Pi OS (64位)
- **Python版本**: 3.8+
- **摄像头**: CSI接口摄像头 (使用picamera2库)

### SSH远程开发

#### 树莓派配置
```bash
# 启用SSH服务
sudo systemctl enable ssh
sudo systemctl start ssh

# 查看IP地址
hostname -I
```

#### 开发端连接
```bash
# SSH连接
ssh pi@<树莓派IP地址>

# 文件同步
rsync -avz --exclude='.git' ./ pi@<树莓派IP地址>:~/pi_sorter/
```

## 📊 系统功能

### 集成系统架构

```python
# 系统初始化
from src.external.integrated_system import IntegratedSorterSystem
from src.external.config_manager import ConfigManager

# 加载配置
config_manager = ConfigManager()
system = IntegratedSorterSystem(config_manager)

# 启动系统
system.initialize()
system.start_processing()
```

### MQTT主题

- `pi_sorter/status` - 系统状态
- `pi_sorter/results` - 分拣结果
- `pi_sorter/commands` - 远程命令
- `pi_sorter/alerts` - 系统告警
- `pi_sorter/statistics` - 统计信息

### API接口

#### IntegratedSorterSystem
```python
# 主要方法
system.initialize()              # 初始化系统
system.start_processing()        # 开始处理
system.stop_processing()         # 停止处理
system.capture_manual_image()    # 手动拍照
system.get_system_status()       # 获取状态
system.shutdown()                # 关闭系统
```

#### ConfigManager
```python
# 配置管理
config.get('camera.resolution')  # 获取配置
config.set('camera.enabled', True)  # 设置配置
config.save_config()             # 保存配置
```

## 📈 性能指标

- **处理速度**: 30-60根/分钟
- **分拣精度**: ≥90%
- **测量精度**: 长度±2mm, 直径±1mm
- **连续工作时间**: ≥20小时
- **MQTT延迟**: <100ms
- **图像处理**: 30 FPS

## 🔍 质量等级

| 等级 | 长度范围 | 直径范围 | 质量要求 |
|------|----------|----------|----------|
| A级  | 18-22cm  | 12-16mm  | 无缺陷   |
| B级  | 15-25cm  | 10-18mm  | 轻微缺陷 |
| C级  | 12-28cm  | 8-20mm   | 明显缺陷 |

## 🛡️ 错误处理

- **自动重试机制**: 摄像头连接失败自动重试
- **优雅降级**: MQTT断线时本地缓存数据
- **错误日志**: 详细的错误记录和分析
- **系统监控**: 实时性能和状态监控

## 📚 文档导航

> 📖 **[完整文档导航](docs/文档导航.md)** - 查看所有文档的详细索引和使用指南

### 🚀 快速入门
- [快速开始指南](docs/06-使用指南/快速开始.md) - 5分钟快速部署
- [环境配置指南](docs/03-开发环境/环境配置指南.md) - 完整环境配置
- [硬件规格说明](docs/01-项目概述/硬件规格说明文档.md) - 硬件要求

### 💻 技术文档
- [集成系统架构](docs/04-技术实现/集成系统架构.md) - 系统架构设计
- [技术实现细节](docs/04-技术实现/技术实现细节.md) - 核心算法实现
- [系统配置说明](docs/05-配置说明/系统配置.md) - 配置文件详解

### 🔧 开发文档
- [软件产品需求](docs/02-需求与设计/软件产品需求文档.md) - 功能需求
- [测试与部署指南](docs/07-测试与部署/测试与部署指南.md) - 完整测试部署流程
- [SSH远程开发](docs/03-开发环境/SSH远程开发配置指南.md) - 远程开发配置

### 📊 项目信息
- [芦笋特性分析](docs/01-项目概述/芦笋特性分析.md) - 分级标准和特征
- [开发环境验证](docs/03-开发环境/开发环境验证清单.md) - 环境检查清单

## 🤝 贡献

欢迎提交Issue和Pull Request来改进项目。

## 📄 许可证

本项目遵循MIT许可证。

## 🙏 致谢

本项目中的摄像头和MQTT功能代码引用自"ssh pi test"项目，感谢原项目的贡献。

---

**注意**: 确保在树莓派上运行时已正确配置摄像头和网络环境。