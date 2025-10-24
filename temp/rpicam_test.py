#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用rpicam-still命令行工具测试摄像头功能
作为picamera2的替代方案
"""

import os
import sys
import subprocess
import time

def test_camera_access():
    """测试摄像头访问权限"""
    print("测试摄像头访问权限...")
    try:
        # 列出可用的摄像头
        result = subprocess.run(
            ["rpicam-still", "--list-cameras"],
            capture_output=True,
            text=True,
            check=True
        )
        print("✅ 摄像头列表:")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 无法访问摄像头: {e.stderr}")
        return False

def capture_test_photo():
    """拍摄测试照片"""
    print("\n拍摄测试照片...")
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    photo_path = f"test_photo_{timestamp}.jpg"
    
    try:
        # 使用rpicam-still拍摄照片，设置较短的超时时间
        subprocess.run(
            [
                "rpicam-still",
                "-o", photo_path,
                "--timeout", "2000",  # 2秒超时
                "--width", "1280",
                "--height", "1024",
                "--quality", "90"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        if os.path.exists(photo_path):
            file_size = os.path.getsize(photo_path)
            print(f"✅ 成功拍摄照片: {photo_path}")
            print(f"   文件大小: {file_size} 字节 ({file_size/1024:.2f} KB)")
            return photo_path
        else:
            print("❌ 照片文件不存在")
            return None
    except subprocess.CalledProcessError as e:
        print(f"❌ 拍摄失败: {e.stderr}")
        return None

def main():
    print(f"Python版本: {sys.version}")
    print(f"当前目录: {os.getcwd()}")
    
    # 检查rpicam-still命令是否可用
    try:
        subprocess.run(["which", "rpicam-still"], check=True, stdout=subprocess.PIPE)
        print("✅ rpicam-still 命令可用")
    except subprocess.CalledProcessError:
        print("❌ rpicam-still 命令不可用")
        return
    
    # 测试摄像头访问
    if test_camera_access():
        # 拍摄测试照片
        photo_path = capture_test_photo()
        
        if photo_path:
            print("\n🎉 测试成功！可以使用rpicam-still作为picamera2的替代方案")
            print("建议在集成系统中使用subprocess调用rpicam-still命令")
            print(f"示例代码:\n")
            print(f"import subprocess")
            print(f"def capture_image(output_path, width=1280, height=1024):")
            print(f"    subprocess.run([")
            print(f"        'rpicam-still',")
            print(f"        '-o', output_path,")
            print(f"        '--timeout', '1000',")
            print(f"        '--width', str(width),")
            print(f"        '--height', str(height)")
            print(f"    ])")

if __name__ == "__main__":
    main()