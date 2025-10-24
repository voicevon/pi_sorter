#!/usr/bin/env python3
# 简单的摄像头测试脚本

import sys
import os
import time

print("Python版本:", sys.version)
print("Python路径:", sys.executable)
print("Python模块路径:", sys.path)
print("当前工作目录:", os.getcwd())
print("环境变量PYTHONPATH:", os.environ.get('PYTHONPATH', '未设置'))

# 测试Picamera2导入
try:
    print("🔍 尝试导入Picamera2...")
    import picamera2
    print(f"✅ 成功导入picamera2模块，版本: {getattr(picamera2, '__version__', '未知')}")
    print(f"Picamera2模块路径: {picamera2.__file__}")
    from picamera2 import Picamera2
    print("✅ 成功导入 Picamera2 类")
    
    # 尝试初始化摄像头
    try:
        picam2 = Picamera2()
        print("✅ 初始化 Picamera2 成功")
        
        # 列出可用的摄像头
        camera_ids = picam2.sensor_modes
        print(f"✅ 找到可用的摄像头传感器模式: {len(camera_ids)}")
        
        # 尝试预览配置
        config = picam2.create_preview_configuration(main={'size': (640, 480)})
        print("✅ 创建预览配置成功")
        
        # 尝试配置摄像头
        picam2.configure(config)
        print("✅ 配置摄像头成功")
        
        # 尝试启动摄像头（不实际拍照，只是验证启动）
        try:
            print("🔄 尝试启动摄像头...")
            picam2.start()
            print("✅ 摄像头启动成功")
            
            # 短暂暂停
            time.sleep(1)
            
            # 停止摄像头
            picam2.stop()
            print("✅ 摄像头停止成功")
            
            print("\n🎉 摄像头测试成功！")
            
        except Exception as e:
            print(f"❌ 启动摄像头失败: {e}")
            print("💡 可能是权限问题或硬件连接问题")
            
    except Exception as e:
        print(f"❌ 初始化Picamera2失败: {e}")
        
    # 清理资源
    try:
        if 'picam2' in locals():
            picam2.close()
            print("✅ 摄像头资源已释放")
    except:
        pass
        
except ImportError:
    print("❌ 无法导入Picamera2")
    print("请确保已安装picamera2: sudo apt install python3-picamera2")
    print("请确保CSI摄像头已正确连接")
        
print("\n📋 测试完成")