#!/bin/bash
# 更新树莓派摄像头配置的脚本
echo "# 强制使用传统MMAL驱动" >> /boot/firmware/config.txt
echo "camera_auto_detect=0" >> /boot/firmware/config.txt
echo "start_x=1" >> /boot/firmware/config.txt
echo "gpu_mem=128" >> /boot/firmware/config.txt
echo "配置已更新，需要重启"