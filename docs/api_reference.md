# API参考文档

## MQTT通信协议

### 主题结构
所有主题统一使用 `pi_sorter/*` 前缀：
- `pi_sorter/images` - 图像数据
- `pi_sorter/status` - 系统状态
- `pi_sorter/results` - 分拣结果
- `pi_sorter/alerts` - 告警信息
- `pi_sorter/heartbeat` - 心跳信号

### 消息格式

#### 图像消息 (pi_sorter/images)
**二进制模式** (当前配置):
直接发送JPEG二进制数据，无JSON包装

#### 状态消息 (pi_sorter/status)
```json
{
  "timestamp": "2024-01-01T12:34:56.789",
  "client_id": "pi_sorter_integrated",
  "status": "online"
}
```

#### 分拣结果 (pi_sorter/results)
```json
{
  "item_id": "item_1234567890",
  "grade": "A",
  "length": 180.5,
  "diameter": 12.3,
  "defects": [],
  "confidence": 0.95,
  "timestamp": "2024-01-01T12:34:56.789"
}
```

## 核心类

### CSICamera (摄像头控制)
```python
# 初始化
camera = CSICamera(camera_id=0, resolution=(1280, 1024))

# 设置参数
camera.set_parameters(brightness=0.5, contrast=0.5, saturation=0.5)

# 捕获图像
frame = camera.capture_frame()
```

### SorterMQTTManager (MQTT管理)
```python
# 初始化
manager = SorterMQTTManager(config)

# 发布消息
manager.publish_message(topic, payload, qos=1)

# 订阅主题
manager.subscribe_to_topic(topic, callback)
```

### RotaryEncoder (编码器)
```python
# 初始化
encoder = RotaryEncoder(pin_a=4, pin_b=5, pin_z=6)

# 设置触发位置
encoder.set_trigger_position(150, callback)

# 获取位置
position = encoder.get_position()
```

## 质量分级标准

| 等级 | 长度(mm) | 直径(mm) | 弯曲度 | 缺陷比例 | 最小评分 |
|------|----------|----------|--------|----------|----------|
| A级  | 180-220  | 12-18    | ≤0.05  | ≤2%      | 85       |
| B级  | 150-250  | 10-20    | ≤0.08  | ≤5%      | 70       |
| C级  | 100-300  | 8-25     | ≤0.15  | ≤15%     | 50       |

## 配置参数

### 摄像头配置
```yaml
camera:
  resolution: [1280, 1024]
  fps: 30
  brightness: 0.5
  contrast: 0.5
  saturation: 0.5
```

### MQTT配置
```json
{
  "broker": {
    "host": "voicevon.vicp.io",
    "port": 1883,
    "username": "admin",
    "password": "admin1970"
  },
  "topics": {
    "images": "pi_sorter/images",
    "status": "pi_sorter/status",
    "results": "pi_sorter/results"
  }
}
```

## 性能指标
- **处理速度**: 30-60根/分钟
- **测量精度**: 长度±2mm, 直径±1mm
- **图像质量**: 1280×1024, JPEG质量95%
- **传输间隔**: 5秒/张
- **系统资源**: CPU 5-8%, 内存~220MB