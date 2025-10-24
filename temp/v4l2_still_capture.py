#!/usr/bin/env python3
# V4L2静态图像捕获测试脚本

import subprocess
import os
import time

def run_command(cmd):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

print("===== V4L2静态图像捕获测试开始 =====")

# 检查v4l2-ctl是否可用
ret, out, err = run_command("which v4l2-ctl")
if ret != 0:
    print("❌ v4l2-ctl不可用，请安装v4l-utils")
else:
    print(f"✅ v4l2-ctl路径: {out.strip()}")

# 检查/dev/video0是否存在
if os.path.exists("/dev/video0"):
    print("✅ /dev/video0 设备存在")
else:
    print("❌ /dev/video0 设备不存在")

# 获取设备功能
print("\n获取设备功能:")
ret, out, err = run_command("v4l2-ctl -d /dev/video0 --list-ctrls")
if ret == 0:
    print("✅ 设备功能列表:")
    print(out)
else:
    print(f"❌ 获取设备功能失败: {err}")

# 获取支持的格式
print("\n获取支持的格式:")
ret, out, err = run_command("v4l2-ctl -d /dev/video0 --list-formats-ext")
if ret == 0:
    print("✅ 支持的格式:")
    print(out)
else:
    print(f"❌ 获取格式失败: {err}")

# 尝试使用v4l2-ctl捕获静态图像
print("\n尝试捕获静态图像:")
print("注意: 这是一个静态模式摄像头，可能需要特殊处理")

# 尝试使用不同的方法捕获
methods = [
    "v4l2-ctl -d /dev/video0 --set-fmt-video=width=1280,height=720,pixelformat=JPEG --stream-mmap --stream-to=test_v4l2.jpg --stream-count=1",
    "v4l2-ctl -d /dev/video0 --set-fmt-video=width=640,height=480,pixelformat=YUV420 --stream-mmap --stream-to=test_v4l2.yuv --stream-count=1",
    "v4l2-ctl -d /dev/video0 --set-fmt-video=width=1920,height=1080,pixelformat=JPEG --stream-mmap --stream-to=test_v4l2_full.jpg --stream-count=1"
]

for i, method in enumerate(methods):
    print(f"\n方法 {i+1}: {method}")
    ret, out, err = run_command(method)
    if ret == 0:
        print("✅ 命令执行成功")
        output_file = method.split("--stream-to=")[1].split(" ")[0]
        if os.path.exists(output_file):
            size = os.path.getsize(output_file) / 1024
            print(f"✅ 图像已保存: {output_file}, 大小: {size:.2f} KB")
        else:
            print(f"❌ 文件 {output_file} 不存在")
    else:
        print(f"❌ 命令执行失败: {err}")

# 检查是否有其他视频设备
print("\n检查其他视频设备:")
ret, out, err = run_command("ls -la /dev/video*")
if ret == 0:
    print("可用的视频设备:")
    print(out)
else:
    print(f"检查设备失败: {err}")

# 检查MMAL服务状态
print("\n检查MMAL服务状态:")
ret, out, err = run_command("ps aux | grep mmal | grep -v grep")
if ret == 0:
    print("MMAL相关进程:")
    print(out)
else:
    print("没有找到MMAL进程")

print("\n===== V4L2静态图像捕获测试完成 =====")