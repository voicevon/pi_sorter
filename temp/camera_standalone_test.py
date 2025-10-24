#!/usr/bin/env python3
"""
独立的摄像头测试脚本
专注于测试picamera2的基本功能
"""

import sys
import time
import traceback

print("===== 独立摄像头测试开始 =====")
print(f"Python版本: {sys.version}")
print("开始导入picamera2...")

try:
    # 尝试导入picamera2
    import picamera2
    print("✓ picamera2导入成功")
    
    # 尝试导入pykms
    import pykms
    print("✓ pykms导入成功")
    
    # 检查libcamera
    try:
        from libcamera import Transform
        print("✓ libcamera Transform导入成功")
    except ImportError as e:
        print(f"✗ libcamera导入失败: {e}")
    
    # 初始化摄像头
    print("正在初始化摄像头...")
    try:
        # 先检查可用的摄像头列表
        print("检查可用的摄像头列表...")
        cameras = picamera2.Picamera2.global_camera_info()
        print(f"✓ global_camera_info() 结果: {cameras}")
        print(f"✓ 检测到摄像头数量: {len(cameras)}")
        
        # 如果有摄像头，再创建实例
        if len(cameras) > 0:
            # 创建Picamera2实例
            cam = picamera2.Picamera2()
            print("✓ Picamera2实例创建成功")
        else:
            print("⚠️ 未检测到摄像头，跳过实例创建")
            raise Exception("No cameras detected")
        
        if len(cameras) > 0:
            for i, camera_info in enumerate(cameras):
                print(f"\n摄像头 {i} 信息:")
                print(f"  型号: {camera_info['Model']}")
                print(f"  位置: {camera_info['Location']}")
                print(f"  唯一ID: {camera_info['Id']}")
                print(f"  支持的格式: {camera_info['formats']}")
            
            # 配置摄像头
            print("\n配置摄像头...")
            config = cam.create_preview_configuration(
                main={'size': (1280, 720)},
                controls={
                    "FrameRate": 30,
                    "AeEnable": True,
                    "AwbEnable": True
                }
            )
            print("✓ 摄像头配置创建成功")
            
            # 应用配置
            cam.configure(config)
            print("✓ 摄像头配置应用成功")
            
            # 启动摄像头
            print("启动摄像头...")
            cam.start()
            print("✓ 摄像头启动成功")
            
            # 等待自动曝光稳定
            print("等待2秒让自动曝光稳定...")
            time.sleep(2)
            
            # 捕获一帧图像
            print("捕获图像...")
            frame = cam.capture_array()
            print(f"✓ 图像捕获成功! 尺寸: {frame.shape}")
            
            # 停止摄像头
            print("停止摄像头...")
            cam.stop()
            print("✓ 摄像头停止成功")
            
            # 释放资源
            del cam
            print("✓ 摄像头资源释放成功")
            
        else:
            print("⚠️ 未检测到摄像头")
            
    except Exception as e:
        print(f"✗ 摄像头操作失败: {e}")
        print("详细错误:")
        traceback.print_exc()
        
    print("\n===== 独立摄像头测试完成 =====")
    
except ImportError as e:
    print(f"✗ picamera2导入失败: {e}")
    print("请检查符号链接或安装是否正确")
    print("详细错误:")
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"✗ 测试过程中出现未预期错误: {e}")
    print("详细错误:")
    traceback.print_exc()
    sys.exit(1)