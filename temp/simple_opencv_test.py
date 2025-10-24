#!/usr/bin/env python3
# 简单的OpenCV摄像头测试脚本

import cv2
import time
import os

print("===== 简单OpenCV摄像头测试开始 =====")
print(f"OpenCV版本: {cv2.__version__}")

# 尝试打开摄像头
print("\n尝试打开摄像头...")
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

if cap.isOpened():
    print("✅ 成功打开摄像头!")
    
    # 设置分辨率
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"分辨率: {width}x{height}, FPS: {fps}")
    
    # 尝试多次捕获以增加成功率
    max_attempts = 5
    success = False
    
    for i in range(max_attempts):
        print(f"\n尝试 {i+1}/{max_attempts} 捕获图像...")
        
        # 清除缓冲区
        for _ in range(3):
            cap.grab()
        
        # 尝试读取图像
        ret, frame = cap.read()
        
        if ret and frame is not None:
            print(f"✅ 成功捕获图像! 形状: {frame.shape}")
            
            # 保存图像
            filename = f"opencv_capture_{i+1}.jpg"
            cv2.imwrite(filename, frame)
            
            if os.path.exists(filename):
                size = os.path.getsize(filename) / 1024
                print(f"✅ 图像已保存为 {filename}, 大小: {size:.2f} KB")
                success = True
                break
            else:
                print(f"❌ 文件 {filename} 保存失败")
        else:
            print(f"❌ 捕获失败，等待1秒后重试...")
            time.sleep(1)
    
    if not success:
        print("\n❌ 所有捕获尝试均失败")
    
    # 释放资源
    cap.release()
    print("✅ 摄像头已释放")
else:
    print("❌ 无法打开摄像头")
    print("\n检查摄像头设备信息:")
    try:
        import subprocess
        result = subprocess.run(['ls', '-la', '/dev/video0'], stdout=subprocess.PIPE, text=True)
        print(result.stdout)
        
        result = subprocess.run(['v4l2-ctl', '-d', '/dev/video0', '--info'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print("设备信息:")
        print(result.stdout if result.returncode == 0 else result.stderr)
        
    except Exception as e:
        print(f"检查失败: {e}")

print("\n===== 简单OpenCV摄像头测试完成 =====")