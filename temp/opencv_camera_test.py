#!/usr/bin/env python3
"""
基于OpenCV的摄像头测试脚本
直接使用v4l2接口测试/dev/video设备
"""

import sys
import time
import traceback

print("===== OpenCV摄像头测试开始 =====")
print(f"Python版本: {sys.version}")

# 尝试导入OpenCV
try:
    import cv2
    print(f"✓ OpenCV导入成功，版本: {cv2.__version__}")
except ImportError:
    print("✗ OpenCV未安装，尝试安装...")
    print("请先运行: pip install opencv-python")
    sys.exit(1)

try:
    # 列出所有可用的视频设备
    print("\n检测视频设备...")
    import subprocess
    result = subprocess.run(["ls", "-la", "/dev/video*"], capture_output=True, text=True)
    print("视频设备列表:")
    print(result.stdout)
    
    # 尝试打开每个视频设备
    max_devices = 10
    found_camera = False
    
    for device_id in range(max_devices):
        print(f"\n尝试打开摄像头 {device_id} (/dev/video{device_id})...")
        cap = cv2.VideoCapture(device_id, cv2.CAP_V4L2)
        
        if cap.isOpened():
            print(f"✓ 成功打开摄像头 {device_id}!")
            found_camera = True
            
            # 获取摄像头属性
            width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            fps = cap.get(cv2.CAP_PROP_FPS)
            print(f"  分辨率: {width}x{height}")
            print(f"  FPS: {fps}")
            
            # 尝试捕获一帧
            print("  尝试捕获一帧...")
            ret, frame = cap.read()
            if ret:
                print(f"  ✓ 成功捕获图像! 尺寸: {frame.shape}")
                # 保存图像用于验证
                cv2.imwrite(f"camera_test_{device_id}.jpg", frame)
                print(f"  ✓ 图像已保存为: camera_test_{device_id}.jpg")
            else:
                print("  ✗ 无法捕获图像")
            
            # 释放摄像头
            cap.release()
            print(f"  ✓ 摄像头 {device_id} 已释放")
        else:
            print(f"  ✗ 无法打开摄像头 {device_id}")
    
    if not found_camera:
        print("\n⚠️ 未找到可用的摄像头设备")
        print("请检查:")
        print("1. 摄像头硬件连接")
        print("2. 摄像头模块是否正确安装")
        print("3. 是否有权限访问/dev/video设备")
    
    print("\n===== OpenCV摄像头测试完成 =====")
    
except Exception as e:
    print(f"\n✗ 测试过程中出现错误: {e}")
    print("详细错误:")
    traceback.print_exc()
    sys.exit(1)