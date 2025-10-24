# 快速开始指南

## 环境准备

### 树莓派端
```bash
# 安装依赖
sudo apt update
sudo apt install python3-pip python3-dev libcamera-dev
pip3 install picamera2 paho-mqtt pyyaml opencv-python

# 启用摄像头
sudo raspi-config  # 选择 Interface Options > Camera > Enable
```

### 网络配置
```bash
# 测试MQTT连接
mosquitto_pub -h voicevon.vicp.io -p 1883 -u admin -P admin1970 -t test -m "hello"
```

## 系统启动

### 1. 配置文件检查
```bash
# 检查MQTT配置
cat config/mqtt_config.json
```

### 2. 启动主程序
```bash
# 启动系统
cd ~/pi_sorter
python3 main.py

# 或者后台运行
nohup python3 main.py > logs/system.log 2>&1 &
```

### 3. 验证运行状态
```bash
# 检查进程
ps aux | grep main.py

# 查看日志
tail -f logs/system.log
```

## 基本测试

### 摄像头测试
```bash
# 测试摄像头
python3 -c "
from picamera2 import Picamera2
import time
cam = Picamera2()
cam.start()
time.sleep(2)
cam.capture_file('test.jpg')
cam.stop()
print('摄像头正常')
"
```

### MQTT测试
```bash
# 订阅状态主题
python3 -c "
import paho.mqtt.client as mqtt
import time
def on_message(client, userdata, msg):
    print(f'{msg.topic}: {msg.payload[:50]}')
client = mqtt.Client()
client.on_message = on_message
client.connect('voicevon.vicp.io', 1883)
client.subscribe('pi_sorter/status')
client.loop_start()
time.sleep(5)
client.loop_stop()
"
```

## 常见问题

### 摄像头无法启动
```bash
# 检查摄像头连接
libcamera-hello --timeout 1000

# 查找占用进程
ps aux | grep -E '(python|camera|picamera)'
kill -9 <PID>
```

### MQTT连接失败
```bash
# 检查网络
ping voicevon.vicp.io

# 检查配置
grep -E '(host|port|username)' config/mqtt_config.json
```

### 系统资源不足
```bash
# 检查内存
free -h

# 检查磁盘
df -h

# 清理临时文件
rm -rf /tmp/received_image_*.jpg
```

## 性能调优

### 图像质量调整
编辑 `config/integrated_config.yaml`:
```yaml
camera:
  resolution: [1280, 1024]  # 降低分辨率可提高速度
  quality: 85               # 降低质量减小文件大小
  capture_interval: 3.0      # 缩短捕获间隔
```

### 系统优化
```bash
# 禁用不必要的服务
sudo systemctl disable bluetooth
sudo systemctl disable avahi-daemon

# 增加交换空间
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile  # 修改CONF_SWAPSIZE=512
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

## 监控指标

| 指标 | 正常范围 | 检查命令 |
|------|----------|----------|
| CPU使用率 | <20% | `top -bn1 | grep Cpu` |
| 内存使用 | <80% | `free | grep Mem` |
| 磁盘空间 | >20% | `df -h /` |
| 网络延迟 | <100ms | `ping -c 4 voicevon.vicp.io` |
| 图像大小 | 200-400KB | `ls -lh /tmp/*.jpg | head -5` |

## 下一步

- 查看 [API参考](api_reference.md) 了解详细接口
- 阅读 [部署手册](deployment_manual.md) 进行生产部署
- 参考 [故障排查](troubleshooting.md) 解决复杂问题