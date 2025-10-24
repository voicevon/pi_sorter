# Pi Sorter - 芦笋分拣系统

基于树莓派的智能芦笋分拣系统，集成摄像头、MQTT通信和旋转编码器。

## 系统特性

- **摄像头**: 支持CSI摄像头，1280×1024分辨率
- **通信**: MQTT协议，统一 `pi_sorter/*` 主题
- **分级**: A/B/C三级质量分级
- **触发**: 旋转编码器位置触发拍照
- **性能**: 30-60根/分钟处理速度

## 快速开始

### 1. 环境准备
```bash
# 树莓派端安装依赖
sudo apt update
sudo apt install python3-pip python3-dev libcamera-dev
pip3 install picamera2 paho-mqtt pyyaml opencv-python
```

### 2. 启动系统
```bash
cd ~/pi_sorter
python3 main.py
```

### 3. 验证运行
```bash
# 检查进程
ps aux | grep main.py

# 查看日志
tail -f logs/system.log
```

## 文档结构

- [快速开始指南](docs/quick_start.md) - 环境配置和基本使用
- [API参考](docs/api_reference.md) - 接口文档和消息格式
- [故障排查](docs/troubleshooting.md) - 常见问题解决
- [部署指南](README_DEPLOYMENT.md) - 生产环境部署

## 核心配置

### MQTT主题
```
pi_sorter/images    - 图像数据
pi_sorter/status    - 系统状态
pi_sorter/results   - 分拣结果
pi_sorter/alerts    - 告警信息
```

### 质量分级标准
| 等级 | 长度(mm) | 直径(mm) | 弯曲度 | 缺陷比例 |
|------|----------|----------|--------|----------|
| A级  | 180-220  | 12-18    | ≤0.05  | ≤2%      |
| B级  | 150-250  | 10-20    | ≤0.08  | ≤5%      |
| C级  | 100-300  | 8-25     | ≤0.15  | ≤15%     |

## 系统架构

```
Windows PC ←SSH→ 树莓派 ←MQTT→ Broker
    ↓              ↓
开发环境        摄像头+编码器
```

## 性能指标

- **处理速度**: 30-60根/分钟
- **测量精度**: 长度±2mm, 直径±1mm
- **系统资源**: CPU 5-8%, 内存~220MB
- **图像传输**: 5秒间隔, QoS 1

## 技术支持

系统运行异常时：
1. 查看 [故障排查指南](docs/troubleshooting.md)
2. 检查日志文件 `logs/system.log`
3. 验证MQTT连接和网络状态
4. 重启系统或联系技术支持

## 更新日志

- v1.0.0 - 基础功能实现
- 支持CSI摄像头和MQTT通信
- A/B/C三级质量分级
- 编码器触发拍照机制