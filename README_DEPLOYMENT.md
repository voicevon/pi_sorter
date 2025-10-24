# Pi Sorter 部署文档

## 系统架构
```
Windows PC ←SSH→ 树莓派4B ←MQTT→ voicevon.vicp.io
    ↓              ↓              ↓
开发环境        摄像头+编码器     MQTT代理
```

## 核心配置

### MQTT主题 (统一为 pi_sorter/*)
- `pi_sorter/images` - 图像数据 (二进制传输)
- `pi_sorter/status` - 系统状态
- `pi_sorter/results` - 分拣结果
- `pi_sorter/alerts` - 告警信息
- `pi_sorter/heartbeat` - 心跳信号

### 质量分级标准
| 等级 | 长度(mm) | 直径(mm) | 弯曲度 | 缺陷比例 |
|------|----------|----------|--------|----------|
| A级  | 180-220  | 12-18    | ≤0.05  | ≤2%      |
| B级  | 150-250  | 10-20    | ≤0.08  | ≤5%      |
| C级  | 100-300  | 8-25     | ≤0.15  | ≤15%     |



## 部署步骤

### 1. 环境准备
```bash
# 树莓派端安装
sudo apt update
sudo apt install python3-picamera2 python3-paho-mqtt -y
```

### 2. 文件同步
```powershell
# Windows端执行
scp -i config/pi_id_ed25519 -r src/ feng@${RASPBERRY_PI_IP}:~/pi_sorter/
scp -i config/pi_id_ed25519 -r config/ feng@${RASPBERRY_PI_IP}:~/pi_sorter/
```

### 3. 启动系统
```bash
# 树莓派端运行
python3 -u main_fixed.py
```

## 性能指标
- **处理速度**: 30-60根/分钟
- **测量精度**: 长度±2mm, 直径±1mm
- **图像质量**: 1280×1024, JPEG质量95%
- **触发方式**: 编码器位置触发 (默认150脉冲，可配置)
- **系统资源**: CPU 5-8%, 内存~220MB

## 故障排查

### 摄像头占用
```bash
# 查找占用进程
ps aux | grep -E '(python|camera|picamera)' | grep -v grep
# 终止进程
kill -9 <PID>
```

### MQTT连接检查
```bash
# 订阅测试
python3 -c "
import paho.mqtt.client as mqtt
import time
def on_message(c,u,m): print(f'{m.topic}: {len(m.payload)}字节')
c=mqtt.Client(); c.on_message=on_message; c.connect('voicevon.vicp.io'); c.subscribe('pi_sorter/images'); c.loop_start(); time.sleep(10)
"
```

### 系统状态监控
```bash
# 查看主进程
ps aux | grep main_fixed.py
# 查看图像文件
ls -la /tmp/received_image_*.jpg | wc -l
```

## 注意事项
- 必须使用Picamera2库 (64位系统不支持libcamera)
- SSH密钥权限设置为600
- 重启后等待30秒再连接
- 所有硬件相关程序仅在树莓派运行