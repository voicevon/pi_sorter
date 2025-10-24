#!/bin/bash

# 更新摄像头配置
CONFIG_FILE="/boot/firmware/config.txt"

echo "更新摄像头配置..."

# 备份原始配置
if [ ! -f "$CONFIG_FILE.bak" ]; then
    sudo cp "$CONFIG_FILE" "$CONFIG_FILE.bak"
    echo "已备份原始配置到 $CONFIG_FILE.bak"
fi

# 添加或更新摄像头配置
sudo bash -c "cat << 'EOF' >> $CONFIG_FILE

# 启用CSI摄像头
camera_auto_detect=1
dtoverlay=imx219
EOF"

echo "配置已更新，显示摄像头相关配置："
grep -i camera "$CONFIG_FILE"
echo "请重启系统以使配置生效"