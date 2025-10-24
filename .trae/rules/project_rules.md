# 项目规则文档

本文档定义了pi_sorter项目的开发、调试和部署规范。

sudo reboot raspberry-pi 之后，需要等待30秒左右，才能重新连接。
64bit 系统下，不要使用 libcamera, 而是使用Picamera2 库。

## ⚠️ PowerShell命令执行注意事项

PowerShell不支持`&&`操作符。在执行需要多步操作的命令时，请使用以下方法：

### 方法1：使用引号包裹完整命令
```powershell
# 在单个SSH命令中执行多个操作
ssh -i config/pi_id_ed25519 feng@${RASPBERRY_PI_IP} "cd ~/pi_sorter && python3 -u src/external/integrated_system.py"
```

### 方法2：创建临时脚本执行（适用于复杂操作）
```powershell
# 创建临时脚本文件
$tempScript = "$env:TEMP\sync_and_run.ps1"
@"
scp -i config/pi_id_ed25519 c:/my_source/pi_sorter/src/external/integrated_system.py feng@${RASPBERRY_PI_IP}:~/pi_sorter/src/external/integrated_system.py
ssh -i config/pi_id_ed25519 feng@${RASPBERRY_PI_IP} "cd ~/pi_sorter && python3 -u src/external/integrated_system.py"
"@ | Out-File -FilePath $tempScript -Encoding utf8

# 执行临时脚本
powershell -ExecutionPolicy Bypass -File $tempScript
```

## 🔒 全局工作模式约定（强制）

AI助手必须严格遵守以下规则：

- **远程执行原则**：仅通过SSH在树莓派上执行所有依赖硬件的程序（main.py、摄像头相关脚本、MQTT通信等），禁止在本地Windows环境运行。
- **本地操作限制**：本地仅用于查看/编辑代码文档、生成补丁、静态分析；除非用户明确要求，否则禁止本地执行。
- **连接配置**：使用`config/pi_id_ed25519`密钥进行免密登录，远程项目目录统一为`~/pi_sorter`。
- **故障处理**：SSH连接失败时，必须报告原因并等待用户指示，不得回退为本地运行。
- **高风险操作**：涉及重启、终止进程等操作需先征得用户同意。
- **技术要求**：强制使用Picamera2库，不允许使用其他摄像头库。
- **代码迭代**：代码变更后应立即部署并进行测试。

## 🏗️ 系统架构

```
┌─────────────────┐    SSH    ┌─────────────────┐    MQTT    ┌─────────────────┐
│   Windows PC    │ ────────► │  Raspberry Pi   │ ─────────► │   MQTT Broker   │
│   (开发环境)     │           │   (摄像头端)     │            │ voicevon.vicp.io│
└─────────────────┘           └─────────────────┘            └─────────────────┘
                                       │                              │
                                       ▼                              ▼
                              ┌─────────────────┐            ┌─────────────────┐
                              │   Picamera2     │            │  其他MQTT客户端  │
                              │   (摄像头控制)   │            │   (数据接收)     │
                              └─────────────────┘            └─────────────────┘
```

## 🛠️ 远程调试环境配置

### 连接信息
- **主机**：`${RASPBERRY_PI_IP}`（主机名：pi4），默认为192.168.2.192
- **用户**：feng
- **认证**：使用`config/pi_id_ed25519`密钥

> **注意**：本文档使用`${RASPBERRY_PI_IP}`作为IP地址变量，实际使用时替换为具体值。后续修改IP地址只需在一处修改，无需更新所有命令示例。

### 技术环境要求
- **树莓派端**：Python3、pip3、Picamera2、paho-mqtt
- **网络要求**：Windows与树莓派网络互通，MQTT Broker（voicevon.vicp.io）可达

### 常用操作命令

#### 1. SSH连接与验证
```bash
# 验证SSH连通性
ssh -i config/pi_id_ed25519 feng@${RASPBERRY_PI_IP}

# 检查密钥权限
ssh -i config/pi_id_ed25519 feng@${RASPBERRY_PI_IP} "chmod 600 ~/pi_sorter/config/pi_id_ed25519"
```

#### 2. 远程程序执行（正确方法）

在PowerShell中执行远程命令的正确格式：

```powershell
# 运行主程序
ssh -i config/pi_id_ed25519 feng@${RASPBERRY_PI_IP} "python3 -u ~/pi_sorter/main.py"

# 运行集成系统
ssh -i config/pi_id_ed25519 feng@${RASPBERRY_PI_IP} "python3 -u ~/pi_sorter/src/external/integrated_system.py"

# 运行测试（使用引号包裹cd和命令组合）
ssh -i config/pi_id_ed25519 feng@${RASPBERRY_PI_IP} "cd ~/pi_sorter && python3 -u tests/mqtt_conn_test.py"

# 查看目录内容并运行程序
ssh -i config/pi_id_ed25519 feng@${RASPBERRY_PI_IP} "cd ~/pi_sorter && ls -la tests/ && python3 -u tests/mqtt_conn_test.py"
```

#### 3. 摄像头资源管理（增强方法）

查找并终止占用摄像头资源的进程的有效命令：

```powershell
# 方法1：查找与摄像头相关的进程
ssh -i config/pi_id_ed25519 feng@${RASPBERRY_PI_IP} "ps aux | grep -E '(camera|picamera|libcamera)' | grep -v grep"

# 方法2：查找与Python和摄像头相关的所有进程（更全面）
ssh -i config/pi_id_ed25519 feng@${RASPBERRY_PI_IP} "ps aux | grep -E '(python|media|unicam|camera)' | grep -v grep"

# 终止特定进程（正常终止）
ssh -i config/pi_id_ed25519 feng@${RASPBERRY_PI_IP} "kill 1390"

# 强制终止进程（当正常终止无效时）
ssh -i config/pi_id_ed25519 feng@${RASPBERRY_PI_IP} "kill -9 1390"

# 同时终止多个进程
ssh -i config/pi_id_ed25519 feng@${RASPBERRY_PI_IP} "kill 1390 1708"
```

#### 4. 文件同步（正确方法）

在PowerShell中进行文件同步的有效命令：

```powershell
# 同步单个文件
scp -i config/pi_id_ed25519 c:/my_source/pi_sorter/src/external/integrated_system.py feng@${RASPBERRY_PI_IP}:~/pi_sorter/src/external/integrated_system.py

# 同步整个目录（增量同步）
scp -i config/pi_id_ed25519 -r c:/my_source/pi_sorter/src/external/ feng@${RASPBERRY_PI_IP}:~/pi_sorter/src/external/

# 同步配置文件
scp -i config/pi_id_ed25519 -r c:/my_source/pi_sorter/config/ feng@${RASPBERRY_PI_IP}:~/pi_sorter/config/

#### 4. MQTT验证（可选）
```bash
# 订阅状态主题
mosquitto_sub -h voicevon.vicp.io -t pi_sorter/status -u admin -P admin1970

# 订阅图片元数据主题
mosquitto_sub -h voicevon.vicp.io -t pi_sorter/images -u admin -P admin1970

# 订阅分拣结果主题
mosquitto_sub -h voicevon.vicp.io -t pi_sorter/results -u admin -P admin1970
```

### 安全注意事项
- 私钥必须设置600权限，禁止泄露
- 远程执行使用`python3 -u`以确保实时日志输出
- 网络不稳定时采用QoS=1与断线重连策略


## 📁 项目结构

```
pi_sorter/
├── config/                      # 配置文件目录
│   ├── integrated_config.yaml   # 集成系统配置（使用 pi_sorter/* 主题）
│   ├── mqtt_config.json        # MQTT代理与主题配置（含用户名密码）
│   ├── pi_id_ed25519          # SSH私钥
│   └── pi_id_ed25519.pub      # SSH公钥
├── src/                         # 源代码目录
│   └── external/
│       ├── integrated_system.py # 集成系统：摄像头+MQTT，图片默认Base64或元数据
│       ├── ssh_pi_test_mqtt.py  # MQTT管理器与客户端封装
│       ├── picamera2_module.py  # 树莓派Picamera2支持
│       ├── config_manager.py    # 配置管理器，加载integrated_config.yaml
│       └── encoder_module.py    # 旋转编码器模块，处理A/B相和Z相信号
├── tests/                       # 测试脚本
│   └── test_integrated_system.py
├── main.py                      # 系统主入口，整合所有组件
└── docs/                        # 文档目录
```

## 🔧 技术实现

### 0. 系统主入口 (main.py)

系统通过`main.py`作为统一入口，整合所有组件并管理生命周期：

- 初始化配置管理器、集成系统和编码器
- 设置GPIO监控LED（GPIO17用于主进程，GPIO27用于编码器）
- 实现编码器触发拍照机制（编码器位置达到150时触发）
- 管理系统主循环、错误处理和资源清理

### 1. 摄像头控制 (Picamera2)

摄像头控制通过`src/external/picamera2_module.py`中的`CSICamera`类实现，支持CSI摄像头，可设置分辨率、亮度、对比度等参数：

```python
# 摄像头初始化（CSI摄像头）
camera_config = self.config.get('camera', {})
success = self.camera_manager.add_camera(
    name='main',
    camera_num=camera_config.get('device_id', 0),
    resolution=tuple(camera_config.get('resolution', [1280, 1024]))
)

# 设置摄像头参数
self.main_camera.set_parameters(
    brightness=camera_config.get('brightness', 0.5),  # 0.0 到 1.0
    contrast=camera_config.get('contrast', 0.5),      # 0.0 到 2.0
    saturation=camera_config.get('saturation', 0.5),  # 0.0 到 2.0
    exposure_time=camera_config.get('exposure', -1)   # -1表示自动曝光
)

# 自动捕获设置
if camera_config.get('auto_capture', True):
    # 设置自动捕获间隔
    capture_interval = camera_config.get('capture_interval', 5.0)  # 默认5秒
```

### 2. MQTT通信协议（统一为 pi_sorter/*）

MQTT通信通过`src/external/ssh_pi_test_mqtt.py`中的`SorterMQTTManager`类实现，当前系统统一使用 pi_sorter/* 主题，并采用 JSON + Base64 或元数据引用的图片发送方式。

配置读取优先级：
- 首先读取`broker`节点中的配置
- 如果`broker`节点不存在，则读取`mqtt`节点中的配置
- 主题配置优先读取`mqtt.topics`，其次读取顶层`topics`

支持的主题包括：status、results、commands、images、alerts、statistics、heartbeat

#### 图片发送（pi_sorter/images）
- 内容类型1：JSON，内含 Base64 编码的图片
```json
{
  "type": "image",
  "filename": "sorted_001.jpg",
  "size_bytes": 485123,
  "encoding": "base64",
  "content": "<base64字符串>",
  "timestamp": "2024-01-01T12:34:56.789"
}
```
- 内容类型2：JSON，仅元数据与路径（当文件过大时）
```json
{
  "type": "image_ref",
  "filename": "sorted_001.jpg",
  "path": "/data/images/sorted_001.jpg",
  "size_bytes": 1850123,
  "timestamp": "2024-01-01T12:34:56.789",
  "note": "image too large to inline; sending path only"
}
```

#### 状态发送（pi_sorter/status）
```json
{
  "timestamp": "2024-01-01T12:34:56.789",
  "client_id": "pi_sorter_integrated",
  "status": "分拣系统已启动"
}
```

#### 结果发送（pi_sorter/results）
```json
{
  "item_id": "0001",
  "grade": "A",
  "length": 180.5,
  "diameter": 12.3,
  "defects": []
}
```

#### 告警发送（pi_sorter/alerts）
```json
{
  "type": "system",
  "level": "info",
  "message": "分拣系统已停止",
  "timestamp": "2024-01-01T13:00:00.000"
}
```

说明：编号主题 camera/number 在当前统一方案中不使用，如有需要可作为可选扩展。

### 3. 自我验证机制

配置管理器`ConfigManager`提供了配置验证功能，确保配置的有效性：

```python
# 配置验证
def validate_config(self) -> Dict[str, Any]:
    validation_result = {
        'valid': True,
        'errors': [],
        'warnings': []
    }
    
    # 验证摄像头配置
    camera_config = self.get_camera_config()
    if camera_config.get('enabled', True):
        resolution = camera_config.get('resolution', [1280, 1024])
        if not isinstance(resolution, list) or len(resolution) != 2:
            validation_result['errors'].append("摄像头分辨率配置无效")
    
    # 验证MQTT配置
    # ...
    
    return validation_result
```

### 4. 编码器模块

编码器模块`encoder_module.py`实现了旋转编码器的位置计数、归零和触发拍照功能：

- 支持A/B相计数和Z相归零
- 使用GPIO中断实现精确计数
- 提供位置触发机制，当位置达到设定值时调用回调函数
- 包含资源管理和清理功能

### 5. 图像处理与分级逻辑

系统实现了基于图像处理的芦笋分级功能，通过轮廓检测确定芦笋等级：

- **图像处理流程**：图像捕获 → 预处理 → 轮廓检测 → 特征分析 → 等级判断
- **分级标准**：
  - A级：轮廓面积大于15000像素
  - B级：轮廓面积在5000-15000像素之间
  - C级：轮廓面积小于5000像素
- **预处理方法**: 去噪、调整亮度、对比度、饱和度、曝光时间
- **阈值处理**: 自适应阈值、边缘检测
- **图像质量**: 95% JPEG质量
- **图像尺寸**: 1280x1024 (默认), 可配置

### 6. 系统主流程

1. 系统初始化（配置加载、组件初始化）
2. 编码器和摄像头启动
3. 主循环：
   - 监控编码器位置
   - 达到触发位置时拍照
   - 图像处理和分级
   - MQTT发布结果
   - 统计信息更新
4. 系统关闭（资源清理、离线状态发布）

```python
# 编码器初始化
def __init__(self, pin_a: int, pin_b: int, pin_z: int):
    self.pin_a = pin_a
    self.pin_b = pin_b
    self.pin_z = pin_z
    
    # 位置计数器
    self.position = 0
    self.position_lock = threading.Lock()
    
    # 运行状态
    self.is_running = False
    
    # 位置触发回调
    self.trigger_position = 150  # 默认触发位置
    self.trigger_callback = None
    self.last_trigger_position = 0  # 上次触发位置
    
    # GPIO初始化
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(self.pin_a, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(self.pin_b, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(self.pin_z, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    # 配置中断
    GPIO.add_event_detect(self.pin_a, GPIO.BOTH, callback=self._handle_encoder)
    GPIO.add_event_detect(self.pin_z, GPIO.FALLING, callback=self._handle_zero)
```

## 🐛 问题解决记录

### 问题1: 编号格式错误
**现象**: 客户端接收到timestamp而不是number值
**原因**: 编号被包装在JSON状态消息中
```json
{
    "timestamp": "2024-01-01T12:34:56",
    "client_id": "pi_camera_xxx",
    "status": "照片编号: 3456"  # 问题所在
}
```

**解决方案**: 创建专用的`publish_number()`方法
```python
def publish_number(self, number: str, topic: str = "camera/number") -> bool:
    # 直接发送编号值，不包装在JSON中
    result = self.client.publish(topic, number, qos=1)
```

### 问题2: 照片格式兼容性
**现象**: 接收端无法正确显示图片，期望二进制数据而非Base64
**原因**: 早期实现与接收端约定不一致（二进制直传 vs JSON+Base64）
```json
{
    "type": "image",
    "encoding": "base64",
    "content": "..."
}
```

**解决方案**: 统一采用 pi_sorter/images 主题，发送 JSON + Base64；当文件过大时发送 `image_ref` 元数据与路径以避免消息超限。

### 问题3: 消息处理编码错误
**现象**: `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff`
**原因**: 处理二进制负载时尝试按UTF-8解码
**解决方案**: 统一使用 JSON 文本消息（Base64或元数据引用），接收端按文本解析，避免对原始二进制进行UTF-8解码。
```python
def _on_message(self, client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode('utf-8'))
        # 处理 JSON 消息
    except Exception:
        # 非预期格式，记录告警
        pass
```

### 问题4: 摄像头资源冲突
**现象**: `Camera __init__ sequence did not complete`
**原因**: 多个进程同时访问摄像头资源
**解决方案**: 

使用增强的进程查找方法，确保找到所有可能占用摄像头的进程：

```bash
# 查找所有相关进程（包括Python进程）
ps aux | grep -E '(python|media|unicam|camera)' | grep -v grep

# 正常终止进程
kill <PID>

# 如正常终止无效，使用强制终止
kill -9 <PID>

# 一次性终止多个占用进程
kill <PID1> <PID2>
```

**注意**: 系统中可能存在长期运行的Python进程（如main.py）占用摄像头资源，需要优先终止这些进程。


## 📊 性能指标

### 传输性能
- **照片大小**: 约1280x1024分辨率，JPEG格式，质量95%（实际大小约200-300KB）
- **传输间隔**: 5.0秒/张（可配置）
- **传输格式**: JSON + Base64（约增加33%-37%），过大时发送元数据与路径
- **MQTT QoS**: 1（确保送达）
- **传输成功率**: 视代理与网络而定（含自动重连机制，最多10次重连尝试）

### 系统资源
- **CPU使用率**: 约6-8% (树莓派4B)
- **内存使用**: 约100MB
- **网络带宽**: 约16KB/s (平均，5秒间隔)



## 🚀 部署指南

### 配置文件设置

系统使用两种配置文件：

#### YAML配置文件（integrated_config.yaml）
```yaml
# 系统基本配置
system:
  name: "芦笋分拣系统"
  version: "1.0.0"
  debug: false
  log_level: "INFO"
  data_dir: "data"
  log_dir: "logs"

# 摄像头配置
camera:
  enabled: true
  device_id: 0
  resolution: [1280, 1024]
  fps: 30
  auto_capture: true
  capture_interval: 5.0  # 五秒间隔拍照
  capture_only: true     # 仅拍照模式
```

#### JSON配置文件（mqtt_config.json）
```json
{
    "broker": {
        "host": "voicevon.vicp.io",
        "port": 1883,
        "username": "admin",
        "password": "admin1970",
        "client_id": "pi_sorter_integrated"
    },
    "topics": {
        "images": "pi_sorter/images",
        "status": "pi_sorter/status",
        "results": "pi_sorter/results",
        "alerts": "pi_sorter/alerts",
        "heartbeat": "pi_sorter/heartbeat"
    },
    "settings": {
        "qos": 1,
        "retain": false,
        "keepalive": 60,
        "reconnect_delay": 5,
        "max_reconnect_attempts": 10
    }
}
```

### 系统稳定性保障

系统设计强调关键组件的可靠性，采用以下机制确保稳定运行：

- **组件初始化验证**：所有关键组件（摄像头、MQTT等）必须成功初始化，否则系统将无法启动
- **错误处理机制**：完善的异常捕获和日志记录，便于问题诊断
- **资源管理**：严格的资源获取和释放机制，避免资源泄露

### 日志配置

系统日志配置遵循以下原则：
- 使用Python标准logging模块
- 日志级别可通过配置文件设置（默认为INFO）
- 支持debug模式下的详细日志
- 日志输出包括系统状态、错误信息和操作记录

### 图像处理与分级逻辑

系统实现了基于图像处理的芦笋分级功能，通过轮廓检测确定芦笋等级：

- **图像处理流程**：图像捕获 → 预处理 → 轮廓检测 → 特征分析 → 等级判断
- **分级标准**：
  - A级：轮廓面积大于15000像素
  - B级：轮廓面积在5000-15000像素之间
  - C级：轮廓面积小于5000像素
- **预处理方法**: 高斯模糊、中值滤波、双边滤波、调整亮度、对比度
- **阈值处理**: 自适应阈值、Otsu阈值、边缘检测
- **图像质量**: JPEG格式，质量95%
- **图像尺寸**: 1280x1024像素



