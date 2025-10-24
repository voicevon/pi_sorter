#!/usr/bin/env python3
"""
简化测试脚本 - 测试基本功能
Simple test script for basic functionality
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

def test_imports():
    """测试模块导入"""
    print("测试模块导入...")
    
    try:
        # 测试基本模块
        import yaml
        print("✓ yaml模块导入成功")
    except ImportError as e:
        print(f"✗ yaml模块导入失败: {e}")
        return False
    
    try:
        # 测试自定义模块
        from external.config_manager import ConfigManager
        print("✓ ConfigManager导入成功")
    except ImportError as e:
        print(f"✗ ConfigManager导入失败: {e}")
        return False
    
    try:
        from external.ssh_pi_test_camera import PiCamera, CameraManager
        print("✓ Camera模块导入成功")
    except ImportError as e:
        print(f"✗ Camera模块导入失败: {e}")
        return False
    
    try:
        from external.ssh_pi_test_mqtt import MQTTClient, SorterMQTTManager
        print("✓ MQTT模块导入成功")
    except ImportError as e:
        print(f"✗ MQTT模块导入失败: {e}")
        return False
    
    try:
        from external.integrated_system import IntegratedSorterSystem
        print("✓ IntegratedSorterSystem导入成功")
    except ImportError as e:
        print(f"✗ IntegratedSorterSystem导入失败: {e}")
        return False
    
    return True

def test_config_manager():
    """测试配置管理器"""
    print("\n测试配置管理器...")
    
    try:
        from external.config_manager import ConfigManager
        
        # 创建配置管理器实例
        config_manager = ConfigManager()
        print("✓ ConfigManager实例创建成功")
        
        # 测试基本功能
        debug_mode = config_manager.is_debug_mode()
        print(f"✓ 调试模式: {debug_mode}")
        
        camera_enabled = config_manager.is_camera_enabled()
        print(f"✓ 摄像头启用: {camera_enabled}")
        
        mqtt_enabled = config_manager.is_mqtt_enabled()
        print(f"✓ MQTT启用: {mqtt_enabled}")
        
        return True
        
    except Exception as e:
        print(f"✗ 配置管理器测试失败: {e}")
        return False

def test_file_structure():
    """测试文件结构"""
    print("\n测试文件结构...")
    
    required_files = [
        "src/external/__init__.py",
        "src/external/config_manager.py",
        "src/external/ssh_pi_test_camera.py",
        "src/external/ssh_pi_test_mqtt.py",
        "src/external/integrated_system.py",
        "config/integrated_config.yaml",
        "requirements.txt",
        "main.py"
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = current_dir / file_path
        if full_path.exists():
            print(f"✓ {file_path} 存在")
        else:
            print(f"✗ {file_path} 不存在")
            all_exist = False
    
    return all_exist

def main():
    """主测试函数"""
    print("=== 简化集成系统测试 ===\n")
    
    # 测试文件结构
    file_test = test_file_structure()
    
    # 测试模块导入
    import_test = test_imports()
    
    # 测试配置管理器
    config_test = test_config_manager()
    
    # 总结
    print("\n=== 测试结果总结 ===")
    print(f"文件结构测试: {'通过' if file_test else '失败'}")
    print(f"模块导入测试: {'通过' if import_test else '失败'}")
    print(f"配置管理器测试: {'通过' if config_test else '失败'}")
    
    if file_test and import_test and config_test:
        print("\n🎉 所有基本测试通过！系统准备就绪。")
        return True
    else:
        print("\n❌ 部分测试失败，需要检查配置。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)