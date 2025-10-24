#!/usr/bin/env python3
# 直接使用v4l2测试摄像头的脚本

import os
import sys
import subprocess

print("===== V4L2摄像头测试开始 =====")

# 检查v4l2-ctl是否可用
try:
    subprocess.run(['v4l2-ctl', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("✓ v4l2-ctl命令可用")
except (subprocess.SubprocessError, FileNotFoundError):
    print("✗ v4l2-ctl命令不可用")

# 列出所有视频设备
print("\n列出视频设备:")
try:
    result = subprocess.run(['v4l2-ctl', '--list-devices'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print(result.stdout)
except subprocess.SubprocessError as e:
    print(f"✗ 列出设备失败: {e}")

# 检查/dev/video0的详细信息
print("\n检查/dev/video0信息:")
try:
    result = subprocess.run(['v4l2-ctl', '-d', '/dev/video0', '--all'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print(result.stdout)
except subprocess.SubprocessError as e:
    print(f"✗ 获取设备信息失败: {e}")

# 尝试捕获一帧图像
print("\n尝试使用ffmpeg捕获一帧图像:")
try:
    # 先检查ffmpeg是否可用
    subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("✓ ffmpeg可用，尝试捕获图像...")
    result = subprocess.run([
        'ffmpeg', '-f', 'v4l2', '-video_size', '640x480', '-i', '/dev/video0', 
        '-frames', '1', '-y', 'test_frame.jpg'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    if os.path.exists('test_frame.jpg'):
        file_size = os.path.getsize('test_frame.jpg')
        print(f"✓ 成功捕获图像! 文件大小: {file_size} 字节")
    else:
        print(f"✗ 图像捕获失败，但命令执行完成")
        print(f"错误输出: {result.stderr}")
        
except (subprocess.SubprocessError, FileNotFoundError) as e:
    print(f"✗ ffmpeg不可用或捕获失败: {e}")

print("\n===== V4L2摄像头测试完成 =====")