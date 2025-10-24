#!/bin/bash
# 树莓派芦笋分拣系统快速部署脚本
# 使用方法: bash quick_setup.sh

echo "🚀 开始部署树莓派芦笋分拣系统..."

# 1. 检查系统版本
echo "📋 检查系统信息..."
if [ "$(uname -m)" != "aarch64" ]; then
    echo "⚠️  警告: 建议在使用64位系统的树莓派上运行此脚本"
fi

# 2. 更新系统
echo "🔄 更新系统包..."
sudo apt update && sudo apt upgrade -y

# 3. 安装系统依赖
echo "📦 安装系统依赖..."
sudo apt install -y python3-pip python3-dev python3-venv libcamera-dev libcamera-apps libopencv-dev python3-opencv python3-rpi.gpio

# 4. 创建虚拟环境
echo "🐍 创建Python虚拟环境..."
python3 -m venv ~/pi_sorter_env
source ~/pi_sorter_env/bin/activate

# 5. 升级pip
echo "⬆️  升级pip..."
pip install --upgrade pip

# 6. 安装Python依赖
echo "📚 安装Python依赖包..."
pip install picamera2==0.3.17 paho-mqtt==1.6.1 opencv-python==4.8.1.78 numpy==1.24.3 PyYAML==6.0.1 RPi.GPIO==0.7.1

# 7. 创建项目目录
echo "📁 创建项目目录..."
mkdir -p ~/pi_sorter
cd ~/pi_sorter
mkdir -p data/images logs config

# 8. 检查摄像头配置
echo "📷 检查摄像头配置..."
if ! grep -q "start_x=1" /boot/firmware/config.txt; then
    echo "⚙️  配置摄像头接口..."
    sudo bash -c 'echo "start_x=1" >> /boot/firmware/config.txt'
    sudo bash -c 'echo "gpu_mem=128" >> /boot/firmware/config.txt'
    echo "🔧 摄像头配置已更新，需要重启系统生效"
    REBOOT_NEEDED=true
fi

# 9. 创建默认配置文件
echo "📝 创建默认配置文件..."
cat > config/mqtt_config.json << 'EOF'
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
EOF

cat > config/integrated_config.yaml << 'EOF'
system:
  name: "芦笋分拣系统"
  version: "1.0.0"
  debug: false
  log_level: "INFO"
  data_dir: "data"
  log_dir: "logs"

camera:
  enabled: true
  device_id: 0
  resolution: [1280, 1024]
  fps: 30
  auto_capture: true
  capture_interval: 5.0
  capture_only: true
  brightness: 0.5
  contrast: 0.5
  saturation: 0.5
  exposure: -1

mqtt:
  enabled: true
  config_file: "config/mqtt_config.json"

encoder:
  enabled: true
  pin_a: 5
  pin_b: 6
  pin_z: 13
  trigger_position: 150
EOF

# 10. 测试摄像头
echo "🧪 测试摄像头..."
python3 -c "
import time
from picamera2 import Picamera2
picam2 = Picamera2()
camera_config = picam2.create_still_configuration()
picam2.configure(camera_config)
picam2.start()
time.sleep(2)
picam2.capture_file('test_capture.jpg')
picam2.stop()
print('✅ 摄像头测试成功')
"

# 11. 清理测试文件
rm -f test_capture.jpg

# 12. 完成提示
echo ""
echo "🎉 部署完成！"
echo ""
echo "📋 后续步骤："
echo "1. 将项目代码复制到 ~/pi_sorter/ 目录"
echo "2. 如提示需要重启，请执行: sudo reboot"
echo "3. 运行测试: python3 main_test_camera.py"
echo "4. 启动系统: python3 main_fixed.py"
echo ""
echo "📖 详细说明请参考: docs/deployment_manual.md"
echo "🔍 调试信息请参考: docs/debugging_summary.md"

# 如果需要重启，给出提示
if [ "$REBOOT_NEEDED" = true ]; then
    echo ""
    echo "⚠️  重要: 系统需要重启以应用摄像头配置"
    echo "   请执行: sudo reboot"
fi