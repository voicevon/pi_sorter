#!/usr/bin/env python3
"""
集成系统测试脚本
Test script for integrated system
"""

import sys
import time
import logging
from pathlib import Path

# 添加src目录到Python路径
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from external.integrated_system import IntegratedSorterSystem
from external.config_manager import ConfigManager

def setup_test_logging():
    """设置测试日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def test_config_manager():
    """测试配置管理器"""
    print("\n=== 测试配置管理器 ===")
    
    try:
        config_manager = ConfigManager()
        
        # 验证配置
        validation = config_manager.validate_config()
        print(f"配置验证: {'通过' if validation['valid'] else '失败'}")
        
        if validation['errors']:
            print("错误:")
            for error in validation['errors']:
                print(f"  - {error}")
        
        if validation['warnings']:
            print("警告:")
            for warning in validation['warnings']:
                print(f"  - {warning}")
        
        # 显示关键配置
        print(f"摄像头启用: {config_manager.is_camera_enabled()}")
        print(f"MQTT启用: {config_manager.is_mqtt_enabled()}")
        print(f"调试模式: {config_manager.is_debug_mode()}")
        print(f"日志级别: {config_manager.get_log_level()}")
        
        return config_manager
        
    except Exception as e:
        print(f"配置管理器测试失败: {str(e)}")
        return None

def test_integrated_system(config_manager):
    """测试集成系统"""
    print("\n=== 测试集成系统 ===")
    
    try:
        config = config_manager.get_all_config()
        
        # 创建集成系统
        system = IntegratedSorterSystem(config)
        
        # 初始化系统
        print("初始化系统...")
        if system.initialize():
            print("✓ 系统初始化成功")
            
            # 获取系统状态
            status = system.get_system_status()
            print(f"系统状态: {status.get('system', {})}")
            print(f"摄像头状态: {status.get('camera', {})}")
            print(f"MQTT状态: {status.get('mqtt', {})}")
            
            # 测试手动拍照 (如果摄像头可用)
            if status.get('camera', {}).get('available', False):
                print("测试手动拍照...")
                if system.capture_manual_image("test_capture.jpg"):
                    print("✓ 手动拍照成功")
                else:
                    print("✗ 手动拍照失败")
            
            # 测试短时间处理
            print("启动处理测试...")
            if system.start_processing():
                print("✓ 处理启动成功")
                
                # 运行5秒
                print("运行5秒测试...")
                time.sleep(5)
                
                # 获取统计信息
                final_status = system.get_system_status()
                stats = final_status.get('statistics', {})
                print(f"处理统计: {stats}")
                
                # 停止处理
                system.stop_processing()
                print("✓ 处理停止成功")
            else:
                print("✗ 处理启动失败")
            
            # 关闭系统
            system.shutdown()
            print("✓ 系统关闭成功")
            
            return True
            
        else:
            print("✗ 系统初始化失败")
            return False
            
    except Exception as e:
        print(f"集成系统测试失败: {str(e)}")
        return False

def test_camera_only():
    """仅测试摄像头功能"""
    print("\n=== 测试CSI摄像头功能 ===")
    
    try:
        from external.picamera2_module import CSICameraManager
        
        camera_manager = CSICameraManager()
        
        # 添加摄像头
        if camera_manager.add_camera('test', 0, (640, 480)):
            print("✓ CSI摄像头添加成功")
            
            camera = camera_manager.get_camera('test')
            if camera:
                # 获取摄像头信息
                info = camera.get_camera_info()
                print(f"CSI摄像头信息: {info}")
                
                # 测试捕获
                frame = camera.capture_frame()
                if frame is not None:
                    print(f"✓ 图像捕获成功，尺寸: {frame.shape}")
                    
                    # 保存测试图像
                    if camera.save_frame("test_camera.jpg", frame):
                        print("✓ 图像保存成功")
                    else:
                        print("✗ 图像保存失败")
                else:
                    print("✗ 图像捕获失败")
            
            # 释放摄像头
            camera_manager.release_all()
            print("✓ CSI摄像头释放成功")
            
            return True
        else:
            print("✗ CSI摄像头添加失败")
            return False
            
    except Exception as e:
        print(f"CSI摄像头测试失败: {str(e)}")
        print("请确保:")
        print("1. CSI摄像头已正确连接")
        print("2. 已安装picamera2: sudo apt install python3-picamera2")
        print("3. 摄像头硬件正常工作")
        return False

def test_mqtt_only():
    """仅测试MQTT功能"""
    print("\n=== 测试MQTT功能 ===")
    
    try:
        from external.ssh_pi_test_mqtt import SorterMQTTManager
        
        # 创建测试配置
        config = {
            'mqtt': {
                'enabled': True,
                'broker_host': 'localhost',
                'broker_port': 1883,
                'client_id': 'test_client'
            },
            'topics': {
                'status': 'test/status',
                'results': 'test/results',
                'alerts': 'test/alerts'
            }
        }
        
        mqtt_manager = SorterMQTTManager(config)
        
        # 初始化MQTT
        if mqtt_manager.initialize():
            print("✓ MQTT初始化成功")
            
            # 发布测试消息
            test_result = {
                'item_id': 'test_001',
                'grade': 'A',
                'timestamp': time.time()
            }
            
            if mqtt_manager.publish_sorting_result(test_result):
                print("✓ 结果发布成功")
            
            if mqtt_manager.publish_alert('test', '测试告警', 'info'):
                print("✓ 告警发布成功")
            
            # 等待一下
            time.sleep(1)
            
            # 关闭MQTT
            mqtt_manager.shutdown()
            print("✓ MQTT关闭成功")
            
            return True
        else:
            print("✗ MQTT初始化失败 (可能是因为没有MQTT代理)")
            return False
            
    except Exception as e:
        print(f"MQTT测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("芦笋分拣系统集成测试")
    print("=" * 50)
    
    # 设置日志
    setup_test_logging()
    
    # 测试配置管理器
    config_manager = test_config_manager()
    if not config_manager:
        print("配置管理器测试失败，退出")
        return 1
    
    # 测试摄像头功能
    camera_ok = test_camera_only()
    
    # 测试MQTT功能
    mqtt_ok = test_mqtt_only()
    
    # 测试集成系统
    if config_manager:
        system_ok = test_integrated_system(config_manager)
    else:
        system_ok = False
    
    # 总结
    print("\n" + "=" * 50)
    print("测试结果总结:")
    print(f"配置管理器: {'✓ 通过' if config_manager else '✗ 失败'}")
    print(f"摄像头功能: {'✓ 通过' if camera_ok else '✗ 失败'}")
    print(f"MQTT功能: {'✓ 通过' if mqtt_ok else '✗ 失败'}")
    print(f"集成系统: {'✓ 通过' if system_ok else '✗ 失败'}")
    
    if config_manager and (camera_ok or mqtt_ok):
        print("\n✓ 基本功能测试通过，系统可以运行")
        return 0
    else:
        print("\n✗ 关键功能测试失败，请检查配置和依赖")
        return 1

if __name__ == "__main__":
    sys.exit(main())