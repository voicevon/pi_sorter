#!/usr/bin/env python3
# OpenCV V4L2摄像头测试脚本

print("===== OpenCV V4L2摄像头测试开始 =====")

# 导入系统包
try:
    import sys
    import os
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    print(f"当前目录: {os.getcwd()}")
except Exception as e:
    print(f"系统包导入失败: {e}")

# 导入OpenCV
try:
    import cv2
    print(f"✅ OpenCV导入成功! 版本: {cv2.__version__}")
except Exception as e:
    print(f"❌ OpenCV导入失败: {e}")

# 测试V4L2设备访问
try:
    print("\n测试/dev/video0访问...")
    
    # 使用V4L2后端打开摄像头
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    
    if cap.isOpened():
        print("✅ 成功打开摄像头设备!")
        
        # 获取摄像头属性
        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        fps = cap.get(cv2.CAP_PROP_FPS)
        print(f"  分辨率: {width}x{height}")
        print(f"  FPS: {fps}")
        
        # 尝试设置分辨率
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        new_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        new_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print(f"  设置后分辨率: {new_width}x{new_height}")
        
        # 捕获一帧图像
        print("\n尝试捕获图像...")
        ret, frame = cap.read()
        
        if ret:
            print(f"✅ 成功捕获图像! 形状: {frame.shape}")
            
            # 保存图像
            cv2.imwrite("opencv_test.jpg", frame)
            print("✅ 图像已保存为 opencv_test.jpg")
            
            # 验证文件
            if os.path.exists("opencv_test.jpg"):
                size = os.path.getsize("opencv_test.jpg") / 1024
                print(f"✅ 文件大小: {size:.2f} KB")
            else:
                print("❌ 文件保存失败")
        else:
            print("❌ 图像捕获失败")
            
        # 释放摄像头
        cap.release()
        print("✅ 摄像头已释放")
    else:
        print("❌ 无法打开摄像头设备")
        
        # 检查权限
        print("\n检查摄像头设备权限...")
        try:
            import subprocess
            result = subprocess.run(['ls', '-la', '/dev/video0'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            print(f"设备信息: {result.stdout}")
            
            # 检查用户组
            result = subprocess.run(['groups'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            print(f"用户组: {result.stdout}")
            
        except Exception as e:
            print(f"权限检查失败: {e}")
            
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n===== OpenCV V4L2摄像头测试完成 =====")