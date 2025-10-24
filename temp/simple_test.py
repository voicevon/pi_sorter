import os
import sys
import importlib

print(f"Python版本: {sys.version}")
print(f"当前目录: {os.getcwd()}")
print(f"文件列表: {os.listdir('.')}")

print("\n尝试导入必要模块...")

# 尝试导入各个模块
modules_to_test = [
    ('paho.mqtt', 'paho.mqtt'),
    # 不再需要opencv-python
    ('numpy', 'numpy'),
    ('pyyaml', 'yaml'),
    ('picamera2', 'picamera2')
]

for display_name, module_name in modules_to_test:
    try:
        module = importlib.import_module(module_name)
        # 不再检查opencv-python
            print(f"✅ 成功导入 {display_name}, 版本: {module.__version__}")
        elif display_name == 'numpy':
            print(f"✅ 成功导入 {display_name}, 版本: {module.__version__}")
        else:
            print(f"✅ 成功导入 {display_name}")
    except ImportError as e:
        print(f"❌ 无法导入 {display_name}: {e}")

# 检查配置文件
print("\n检查配置文件...")
config_path = 'config/integrated_config.yaml'
if os.path.exists(config_path):
    print(f"✅ 找到 {config_path}")
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
        print(f"配置文件内容长度: {len(content)} 字符")
        # 打印前几行配置以验证
        print("配置文件前几行:")
        for i, line in enumerate(content.split('\n')[:5]):
            print(f"  {i+1}: {line}")
else:
    print(f"❌ 未找到 {config_path}")

print("\n测试完成！")
print("\n建议下一步操作:")
print("1. 检查是否需要使用libcamera-apps作为替代")
print("2. 或尝试不同版本的picamera2")
print("3. 或考虑使用rpicam-apps命令行工具进行摄像头操作")