#!/usr/bin/env python3
# 简单的Picamera2测试脚本

print("===== 简单Picamera2测试开始 =====")

# 导入系统包
try:
    import sys
    import os
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    print(f"当前目录: {os.getcwd()}")
except Exception as e:
    print(f"系统包导入失败: {e}")

# 导入Picamera2
try:
    # 直接从系统路径导入
    import picamera2
    print("✅ picamera2导入成功!")
    print(f"picamera2模块路径: {picamera2.__file__}")
    print(f"picamera2版本: {picamera2.__version__}")
except Exception as e:
    print(f"❌ picamera2导入失败: {e}")
    print("尝试使用绝对导入...")
    try:
        from picamera2 import Picamera2
        print("✅ 绝对导入Picamera2成功!")
    except Exception as e2:
        print(f"❌ 绝对导入也失败: {e2}")

# 测试摄像头检测
try:
    from picamera2 import Picamera2, Preview
    print("\n测试摄像头检测...")
    
    # 尝试创建摄像头实例
    camera = Picamera2()
    print("✅ 成功创建摄像头实例!")
    
    # 获取可用配置
    configs = camera.sensor_modes
    print(f"✅ 找到 {len(configs)} 个传感器模式")
    print("  支持的分辨率:")
    for i, mode in enumerate(configs[:5]):  # 只显示前5个
        print(f"  {i}: {mode['size']}, {mode['fps']}fps")
    
    # 设置配置并启动预览
    config = camera.create_preview_configuration(main={"size": (640, 480)})
    camera.configure(config)
    print("✅ 成功配置摄像头!")
    
    # 启动摄像头
    camera.start()
    print("✅ 摄像头已启动!")
    
    # 捕获一帧图像
    import time
    time.sleep(1)  # 等待摄像头预热
    frame = camera.capture_array()
    print(f"✅ 成功捕获图像! 形状: {frame.shape}")
    
    # 保存图像
    camera.capture_file("test_capture.jpg")
    print("✅ 图像已保存为 test_capture.jpg")
    
    # 停止摄像头
    camera.stop()
    print("✅ 摄像头已停止")
    
    # 检查文件是否存在
    if os.path.exists("test_capture.jpg"):
        size = os.path.getsize("test_capture.jpg") / 1024
        print(f"✅ 验证文件存在，大小: {size:.2f} KB")
    else:
        print("❌ 图像文件不存在")
        
except Exception as e:
    print(f"❌ 摄像头测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n===== 简单Picamera2测试完成 =====")