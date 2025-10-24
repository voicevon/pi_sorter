#!/usr/bin/env python3
# 极简的picamera2导入测试

import sys
import traceback

print("Python版本:", sys.version)
print("开始测试picamera2导入...")

try:
    # 先尝试导入基础模块
    import picamera2
    print("✅ 成功导入picamera2模块")
    print("模块路径:", picamera2.__file__)
    
    # 检查模块内容
    print("\n模块内容:")
    for item in dir(picamera2):
        if not item.startswith('__'):
            print(f"  - {item}")
    
    # 尝试导入具体类
    print("\n尝试导入Picamera2类...")
    from picamera2 import Picamera2
    print("✅ 成功导入Picamera2类")
    
    # 检查libcamera依赖
    print("\n检查libcamera依赖...")
    try:
        import libcamera
        print("✅ 成功导入libcamera")
    except ImportError:
        print("❌ 无法导入libcamera")
    
    print("\n🎉 导入测试完成！")
    
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("\n错误详情:")
    traceback.print_exc()
    
    # 检查虚拟环境中的已安装包
    print("\n检查虚拟环境中的picamera2安装...")
    import subprocess
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'show', 'picamera2'], 
                              capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"检查安装失败: {e}")

print("\n测试结束")