# project_rules.md

现在请你告诉我，你正在阅读这个文档，说两遍。第一遍用英文，第二遍用中文。
从现在开始，所有的对话基于中文。包括你的思考过程。

## 🔒 全局工作模式约定（强制）

为保证后续“所有新对话”严格按照远程调试定位开展，AI助手必须遵守以下强约束：

- 仅使用 SSH 进行远程运行/调试/测试，不在本地 Windows 环境启动任何依赖硬件或环境的程序（如 main.py、Picamera2 相关脚本、MQTT 发布/订阅等）。
- 本地仅用于：查看/编辑代码与文档、生成补丁、静态分析；除非用户以明确文字指令要求“在本地运行”，否则禁止本地执行。
- 默认远程目标与路径：使用 config/pi_id_ed25519 进行免密登录；远程项目目录统一为 `~/pi_sorter`。
- 新对话开始时，助手应主动读取本文件与 `config/ssh_config.txt`，并据此采用 SSH 远程模式执行后续操作。
- 如 SSH 不可达或认证失败：必须报告失败原因与复现信息，暂停执行，等待用户指示；不得回退为本地运行。
- 涉及高风险操作（重启、停止占用摄像头的进程等）需先告知并征得用户同意。
- 因为操作系统是 64bit， 所以强制使用 picamera2, 不允许使用 picamera 或其他摄像头库。
- 依赖项目已经在 Raspberry Pi 上安装好，无需额外操作。
- 代码变更后，立刻进行部署，运行，调试。


以上约定为全局强制要求，后续对话均默认遵守。

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

## 🤖 智能体运行环境与远程调试（SSH）

智能体的运行环境定位：在 Windows 开发机上，通过 SSH 远程调试运行在 Raspberry Pi 上的 Python 程序（摄像头采集与 MQTT 发布）。

- 连接配置：
  - 主机：192.168.2.192（主机名：pi4）
  - 用户：feng
  - 认证：使用 ed25519 密钥（位于 config/pi_id_ed25519）
- 远程目标：在树莓派上运行集成程序（例如 src/external/integrated_system.py 或 main.py），调试摄像头与 MQTT 行为
- 依赖环境（树莓派端）：
  - Python3、pip3
  - Picamera2（sudo apt install python3-picamera2）
  - paho-mqtt（pip3 install paho-mqtt）
- 网络要求：Windows 与树莓派网络互通；如使用外部 MQTT Broker（voicevon.vicp.io），需可达且凭据正确

### 远程调试工作流（建议）
1) 准备与验证
   - 确认 config/pi_id_ed25519 权限正确（600）
   - 验证 SSH 连通：
     - `ssh -i config/pi_id_ed25519 feng@192.168.2.192`
2) 环境与依赖安装（树莓派）
   - `sudo apt update && sudo apt install python3-picamera2`
   - `pip3 install -U paho-mqtt`
3) 远程启动与日志观察
   - 启动程序（示例）：
     - `ssh -i config/pi_id_ed25519 feng@192.168.2.192 "python3 -u ~/pi_sorter/main.py"`
   - 或直接运行集成系统：
     - `ssh -i config/pi_id_ed25519 feng@192.168.2.192 "python3 -u ~/pi_sorter/src/external/integrated_system.py"`
   - 观察标准输出日志或将日志重定向到文件并使用 `tail -f`
4) 摄像头资源冲突处理
   - 查找占用进程：`ps aux | grep -E '(camera|picamera|libcamera)' | grep -v grep`
   - 终止进程：`kill <PID>`
5) MQTT 验证（可选）
   - 订阅状态：
     - `mosquitto_sub -h voicevon.vicp.io -t pi_sorter/status -u admin -P admin1970`
   - 订阅图片元数据：
     - `mosquitto_sub -h voicevon.vicp.io -t pi_sorter/images -u admin -P admin1970`
6) 文件同步（如需远程更新代码）
   - `scp -i config/pi_id_ed25519 -r c:/my_source/pi_sorter feng@192.168.2.192:~/pi_sorter`
   - 或使用 Git 在树莓派拉取更新

### AI助手任务执行规则（务必遵守）

为确保“让我运行/调试”的指令始终在树莓派远程环境执行，而不是在本地 Windows 端执行，AI助手在接到运行相关指令时必须遵循以下强约束：

- 运行原则
  - 默认通过 SSH 在树莓派上执行所有“运行/调试/测试”相关命令（main.py、src/external/integrated_system.py、pytest 等）。
  - 本地仅进行：查看文件、编辑文档/代码、生成补丁、静态检查（不依赖硬件）；除非用户明确说明“在本地运行”。
  - 使用 `config/pi_id_ed25519` 作为密钥，远程项目路径统一为 `~/pi_sorter`。

- 信息缺失时的询问流程
  1) 若缺少树莓派 IP/用户/密钥路径/远程项目路径，先读取 `config/ssh_config.txt`；若不一致或缺失，向用户确认并建议更新该文件。
  2) 所需信息确认后，再执行 SSH 远程命令。

- PowerShell 命令模板（Windows 端）
  - 运行 main.py（实时日志输出）：
    - `ssh -i config/pi_id_ed25519 feng@192.168.2.192 "python3 -u ~/pi_sorter/main.py"`
  - 运行集成系统：
    - `ssh -i config/pi_id_ed25519 feng@192.168.2.192 "python3 -u ~/pi_sorter/src/external/integrated_system.py"`
  - 远程查看日志（示例，将输出同时写入文件）：
    - `ssh -i config/pi_id_ed25519 feng@192.168.2.192 "cd ~/pi_sorter && python3 -u main.py 2>&1 | tee -a logs/run.log"`
  - 运行单测：
    - `ssh -i config/pi_id_ed25519 feng@192.168.2.192 "cd ~/pi_sorter && pytest -q tests/test_integrated_system.py"`
  - 同步代码：
    - `scp -i config/pi_id_ed25519 -r c:/my_source/pi_sorter feng@192.168.2.192:~/pi_sorter`

- 配置一致性规范（很重要）
  - SSH 密钥统一使用：`config/pi_id_ed25519`
  - 远程项目路径统一为：`~/pi_sorter`

- 本地执行的限制
  - 涉及摄像头/Picamera2/MQTT 的运行，必须走 SSH 远程，避免本地因硬件不可用或环境差异导致失败。
  - 仅当用户明确要求或任务为纯文本/静态检查时，才允许在本地执行。

- 交互确认示例（当用户说“运行 main.py”时）：
  1) 读取 `config/ssh_config.txt`，若存在不一致则提示修正；
  2) 确认 IP 与用户，例如：`feng@192.168.2.192`；
  3) 使用上述命令模板通过 SSH 在树莓派执行；
  4) 实时返回远程日志，并在需要时提供停止/重启/查看状态等操作。

以上规则确保助手不会误在本地运行依赖硬件的程序，并与项目的远程调试定位保持一致。

### 安全与限制
- 勿泄露私钥与账号密码；私钥需设置 600 权限
- 远程执行命令建议使用 `python3 -u` 以便实时日志输出
- Picamera2 仅在树莓派具备 CSI 摄像头与对应驱动时可用；Windows 端无法直接访问摄像头硬件
- 若代理或网络不稳定，统一采用 QoS=1 与断线重连策略


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
│       └── config_manager.py    # 配置管理器，加载integrated_config.yaml
├── tests/                       # 测试脚本
│   └── test_integrated_system.py
└── docs/                        # 文档目录
```

## 🔧 技术实现

### 1. 摄像头控制 (Picamera2)

```python
# 摄像头初始化
self.picam2 = Picamera2()
config = self.picam2.create_still_configuration(
    main={"size": (1920, 1080), "format": "BGR888"},
    buffer_count=2
)
self.picam2.configure(config)
self.picam2.start()

# 拍摄到内存
stream = io.BytesIO()
self.picam2.capture_file(stream, format='jpeg')
photo_data = stream.getvalue()
```

### 2. MQTT通信协议（统一为 pi_sorter/*）

当前系统统一使用 pi_sorter/* 主题，并采用 JSON + Base64 或元数据引用的图片发送方式。

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

```python
# 示例：验证 JSON 消息结构（images/status/results/alerts）
def verify_json_message(payload: bytes) -> bool:
    try:
        data = json.loads(payload.decode('utf-8'))
        return isinstance(data, dict) and 'timestamp' in data
    except Exception:
        return False
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
```bash
# 查找占用进程
ps aux | grep -E '(camera|picamera|libcamera)' | grep -v grep
# 终止占用进程
kill <PID>
```

### 问题5: SSH连接配置
**现象**: 连接失败，IP地址错误
**解决方案**: 使用正确的配置
```
Host: 192.168.2.192
User: feng
Key: keys/pi_id_ed25519
```

## 📊 性能指标

### 传输性能
- **照片大小**: 约480-490KB (1920x1080 JPEG)
- **传输间隔**: 30秒/张（示例）
- **传输格式**: JSON + Base64（约增加33%-37%），过大时发送元数据与路径
- **MQTT QoS**: 1（确保送达）
- **传输成功率**: 视代理与网络而定（含重试机制）

### 系统资源
- **CPU使用率**: 约6-8% (树莓派4B)
- **内存使用**: 约100MB
- **网络带宽**: 约16KB/s (平均，30秒间隔)



## 🚀 部署指南

### 1. 环境准备
```bash
# 树莓派端
sudo apt update
sudo apt install python3-pip python3-picamera2
pip3 install paho-mqtt

# Windows端
# 安装SSH客户端和Python环境
```

### 2. 配置文件设置
```json
// mqtt_config.json
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
        "keepalive": 60
    }
}
```



