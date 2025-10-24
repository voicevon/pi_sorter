#!/usr/bin/env python3
# 简单的Picamera2测试脚本

print("===== 简单Picamera2测试开始 =====")

# 导入必要的库
try:
    import sys
    import os
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    print(f"当前目录: {os.getcwd()}")
    
    # 尝试导入picamera2
    try:
        from picamera2 import Picamera2
        print("✅ picamera2导入成功!")
    except ImportError as e:
        print(f"❌ picamera2导入失败: {e}")
        sys.exit(1)
    
    # 打印picamera2模块路径
    import picamera2 as picamera2_module
    print(f"picamera2模块路径: {picamera2_module.__file__ if hasattr(picamera2_module, '__file__') else '未知'}")
    
    # 方法1: 尝试使用全局摄像头信息
    print("\n方法1: 使用global_camera_info()...")
    try:
        from picamera2.picamera2 import global_camera_info
        cameras = global_camera_info()
        print(f"✅ global_camera_info() 结果: {cameras}")
        print(f"✅ 检测到摄像头数量: {len(cameras)}")
    except Exception as e:
        print(f"❌ 获取全局摄像头信息失败: {e}")
    
    # 方法2: 尝试使用libcamera CameraManager
    print("\n方法2: 使用libcamera CameraManager...")
    try:
        from picamera2.picamera2 import libcamera
        if hasattr(libcamera, 'CameraManager'):
            cm = libcamera.CameraManager.singleton()
            cameras = cm.cameras
            print(f"✅ CameraManager找到 {len(cameras)} 个摄像头")
            for i, cam in enumerate(cameras):
                print(f"  摄像头 {i}: {cam.properties}")
        else:
            print("❌ libcamera.CameraManager不可用")
    except Exception as e:
        print(f"❌ CameraManager方法失败: {e}")
    
    # 方法3: 直接尝试创建Picamera2实例（不指定索引）
    print("\n方法3: 直接创建Picamera2实例...")
    try:
        print("尝试创建默认实例...")
        picam2 = Picamera2()
        print("✅ Picamera2实例创建成功!")
        
        # 获取基本信息
        try:
            info = picam2.camera_properties
            print(f"✅ 摄像头信息: {info}")
        except Exception as e:
            print(f"❌ 获取摄像头信息失败: {e}")
        
        # 尝试获取配置
        try:
            config = picam2.create_still_configuration()
            print(f"✅ 获取配置成功")
        except Exception as e:
            print(f"❌ 获取配置失败: {e}")
        
        # 清理
        picam2.close()
        print("✅ 已关闭摄像头实例")
        
    except Exception as e:
        print(f"❌ 创建默认实例失败: {e}")
    
    # 方法4: 尝试以索引0创建实例
    print("\n方法4: 以索引0创建实例...")
    try:
        print("尝试以索引0创建实例...")
        picam2 = Picamera2(0)
        print("✅ 索引0实例创建成功!")
        picam2.close()
        print("✅ 已关闭摄像头实例")
    except Exception as e:
        print(f"❌ 索引0实例创建失败: {e}")
    
    # 系统信息
    print("\n系统诊断信息:")
    print(f"用户ID: {os.getuid() if hasattr(os, 'getuid') else 'N/A'}")
    
    print("\n===== 简单Picamera2测试完成 =====")
    
except Exception as e:
    print(f"发生未预期的错误: {e}")
    import traceback
    traceback.print_exc()