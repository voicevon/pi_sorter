# 故障排查指南

## 摄像头问题

### 摄像头初始化失败
**现象**: `Camera __init__ sequence did not complete`
**原因**: 资源被占用或硬件连接问题
**解决**:
```bash
# 1. 查找占用进程
ps aux | grep -E '(python|camera|picamera|unicam)' | grep -v grep

# 2. 终止相关进程
kill -9 <PID>

# 3. 检查硬件连接
libcamera-hello --timeout 1000
```

### 图像质量差
**现象**: 模糊、过曝、颜色异常
**解决**:
```yaml
# 调整摄像头参数
camera:
  brightness: 0.3    # 降低亮度
  contrast: 1.2      # 增加对比度
  exposure: -1       # 自动曝光
  resolution: [1280, 1024]  # 确保分辨率合适
```

## MQTT连接问题

### 连接超时
**现象**: `ConnectionRefusedError: [Errno 111] Connection refused`
**排查**:
```bash
# 1. 检查网络连通性
ping voicevon.vicp.io

# 2. 检查端口
nc -zv voicevon.vicp.io 1883

# 3. 验证凭据
mosquitto_pub -h voicevon.vicp.io -p 1883 -u admin -P admin1970 -t test -m "ok"
```

### 消息发送失败
**现象**: 消息发布返回False
**解决**:
```python
# 检查连接状态
if mqtt_manager.is_connected():
    result = mqtt_manager.publish_message(topic, payload)
    if not result:
        logger.error("消息发送失败")
else:
    logger.error("MQTT未连接")
```

## 系统性能问题

### CPU使用率过高
**现象**: CPU使用率>50%
**优化**:
```yaml
# 降低处理频率
camera:
  capture_interval: 10.0  # 增加间隔
  
# 降低图像质量
  resolution: [640, 480]
  quality: 75
```

### 内存不足
**现象**: `MemoryError` 或系统卡顿
**解决**:
```bash
# 1. 清理缓存
sudo sync && sudo sysctl -w vm.drop_caches=3

# 2. 检查内存使用
free -h

# 3. 增加交换空间
sudo dphys-swapfile swapoff
sudo sed -i 's/CONF_SWAPSIZE=.*/CONF_SWAPSIZE=512/' /etc/dphys-swapfile
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

## 编码器问题

### 计数不准确
**现象**: 位置计数跳变或丢失
**排查**:
```bash
# 1. 检查接线
# A相 -> GPIO4
# B相 -> GPIO5  
# Z相 -> GPIO6

# 2. 检查消抖设置
encoder = RotaryEncoder(pin_a=4, pin_b=5, pin_z=6, debounce_time=0.01)
```

### 不触发拍照
**现象**: 编码器达到位置但不拍照
**解决**:
```python
# 检查触发设置
encoder.set_trigger_position(150, callback_function)

# 验证回调函数
def callback_function():
    logger.info(f"触发位置: {encoder.get_position()}")
    camera.capture_single_image()
```

## 图像处理问题

### 分级结果异常
**现象**: 所有物品都被分为同一等级
**排查**:
```python
# 检查分级参数
grade_config = {
    'A': {'min_area': 15000, 'min_length': 180, 'max_defect_ratio': 0.02},
    'B': {'min_area': 5000, 'min_length': 150, 'max_defect_ratio': 0.05},
    'C': {'min_area': 1000, 'min_length': 100, 'max_defect_ratio': 0.15}
}

# 验证轮廓检测
contours, _ = cv2.findContours(processed_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
logger.info(f"检测到 {len(contours)} 个轮廓")
```

### 图像传输失败
**现象**: 图像消息过大或传输超时
**解决**:
```python
# 使用Base64编码（文件过大时）
if os.path.getsize(image_path) > 500000:  # 500KB
    mqtt_manager.publish_image_data(image_path, encoding="base64")
else:
    # 直接发送二进制
    with open(image_path, 'rb') as f:
        image_data = f.read()
    mqtt_manager.publish_message("pi_sorter/images", image_data)
```

## 系统稳定性

### 自动重启问题
**现象**: 程序频繁重启
**排查**:
```bash
# 1. 检查系统日志
journalctl -xe | grep python

# 2. 检查资源限制
ulimit -a

# 3. 检查看门狗
ps aux | grep watchdog
```

### 连接断开
**现象**: MQTT连接不稳定
**解决**:
```python
# 启用自动重连
mqtt_manager = SorterMQTTManager(
    broker_config,
    auto_reconnect=True,
    max_reconnect_attempts=10
)

# 设置心跳
mqtt_manager.publish_heartbeat(interval=30)
```

## 日志分析

### 关键日志位置
```bash
# 系统日志
~/pi_sorter/logs/system.log

# MQTT日志
~/pi_sorter/logs/mqtt.log

# 摄像头日志
~/pi_sorter/logs/camera.log

# 系统日志
/var/log/syslog
```

### 常用排查命令
```bash
# 实时监控系统日志
tail -f logs/system.log

# 查找错误信息
grep -i error logs/system.log

# 统计重启次数
grep -c "系统启动" logs/system.log

# 检查MQTT消息
grep -i "mqtt" logs/system.log | tail -20
```

## 紧急处理

### 系统完全无响应
```bash
# 1. 强制重启程序
pkill -f main.py
sleep 5
cd ~/pi_sorter && python3 main.py

# 2. 重启树莓派
sudo reboot

# 3. 等待30秒后重新连接
sleep 30
ssh -i config/pi_id_ed25519 feng@${RASPBERRY_PI_IP}
```

### 数据丢失恢复
```bash
# 1. 检查备份文件
ls -la data/backup/

# 2. 恢复配置
cp config/backup/integrated_config.yaml.backup config/integrated_config.yaml

# 3. 清理损坏的图像
find data/images/ -size 0 -delete
```

## 联系支持

如果以上方法无法解决问题：

1. 收集完整的错误日志
2. 记录问题发生的时间和条件
3. 提供系统状态信息：`python3 -c "import system_info; print(system_info.get_status())"`
4. 联系技术支持并提供相关信息