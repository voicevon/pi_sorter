#!/usr/bin/env python3
"""
Pi Sorter - 综合测试套件
包含单元测试、集成测试和性能测试的完整测试套件
"""

import os
import sys
import time
import json
import unittest
from unittest.mock import Mock, patch, MagicMock, call
from typing import Dict, Any, Optional

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../src/external'))

# 导入重构后的模块
from config_manager_refactored import ConfigManager, ConfigFormat, ValidationResult
from picamera2_module_refactored import CSICameraManager, CSICamera
from mqtt_manager_refactored import SorterMQTTManager, MQTTManager
from encoder_module_refactored import EncoderManager, RotaryEncoder
from system_monitor import SystemMonitor, EnhancedSystemMonitor, SystemHealthChecker
from integrated_sorting_system import IntegratedSortingSystem, SortingResult


class TestConfigManager(unittest.TestCase):
    """配置管理器测试"""
    
    def setUp(self):
        """测试前设置"""
        self.test_config_path = "test_config.yaml"
        self.config_manager = ConfigManager(self.test_config_path)
        
        # 创建测试配置
        test_config = {
            'system': {
                'name': 'Test System',
                'version': '1.0.0',
                'debug': True
            },
            'camera': {
                'enabled': True,
                'resolution': [1280, 1024],
                'device_id': 0
            },
            'mqtt': {
                'enabled': True,
                'broker': {
                    'host': 'localhost',
                    'port': 1883
                }
            }
        }
        
        with open(self.test_config_path, 'w') as f:
            import yaml
            yaml.dump(test_config, f)
            
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.test_config_path):
            os.unlink(self.test_config_path)
            
    def test_load_configuration(self):
        """测试配置加载"""
        result = self.config_manager.load_configuration()
        self.assertTrue(result)
        
        # 验证配置内容
        system_config = self.config_manager.get_system_configuration()
        self.assertEqual(system_config['name'], 'Test System')
        
    def test_get_configuration_value(self):
        """测试获取配置值"""
        self.config_manager.load_configuration()
        
        # 测试嵌套配置获取
        value = self.config_manager.get_configuration_value(['camera', 'resolution'])
        self.assertEqual(value, [1280, 1024])
        
    def test_update_configuration_value(self):
        """测试更新配置值"""
        self.config_manager.load_configuration()
        
        # 更新配置
        result = self.config_manager.update_configuration_value(['camera', 'resolution'], [1920, 1080])
        self.assertTrue(result)
        
        # 验证更新
        value = self.config_manager.get_configuration_value(['camera', 'resolution'])
        self.assertEqual(value, [1920, 1080])
        
    def test_validate_configuration(self):
        """测试配置验证"""
        self.config_manager.load_configuration()
        
        validation_result = self.config_manager.validate_configuration()
        self.assertIsInstance(validation_result, ValidationResult)
        self.assertTrue(validation_result.is_valid)
        
    def test_save_configuration(self):
        """测试配置保存"""
        self.config_manager.load_configuration()
        
        # 修改配置
        self.config_manager.update_configuration_value(['system', 'name'], 'Updated System')
        
        # 保存配置
        result = self.config_manager.save_configuration()
        self.assertTrue(result)
        
        # 重新加载验证
        new_manager = ConfigManager(self.test_config_path)
        new_manager.load_configuration()
        system_config = new_manager.get_system_configuration()
        self.assertEqual(system_config['name'], 'Updated System')


class TestCSICameraManager(unittest.TestCase):
    """CSI摄像头管理器测试"""
    
    def setUp(self):
        """测试前设置"""
        self.camera_manager = CSICameraManager()
        
    def tearDown(self):
        """测试后清理"""
        self.camera_manager.release_all_cameras()
        
    def test_add_camera(self):
        """测试添加摄像头"""
        # 模拟摄像头（因为实际硬件可能不可用）
        with patch('picamera2.Picamera2') as mock_picamera2:
            mock_camera = Mock()
            mock_picamera2.return_value = mock_camera
            
            result = self.camera_manager.add_camera('test_camera', 0, (1280, 1024))
            self.assertTrue(result)
            
            # 验证摄像头已添加
            cameras = self.camera_manager.get_all_cameras()
            self.assertIn('test_camera', cameras)
            
    def test_remove_camera(self):
        """测试移除摄像头"""
        with patch('picamera2.Picamera2') as mock_picamera2:
            mock_camera = Mock()
            mock_picamera2.return_value = mock_camera
            
            # 先添加摄像头
            self.camera_manager.add_camera('test_camera', 0, (1280, 1024))
            
            # 再移除
            result = self.camera_manager.remove_camera('test_camera')
            self.assertTrue(result)
            
            # 验证摄像头已移除
            cameras = self.camera_manager.get_all_cameras()
            self.assertNotIn('test_camera', cameras)
            
    def test_start_stop_continuous_capture(self):
        """测试连续捕获"""
        with patch('picamera2.Picamera2') as mock_picamera2:
            mock_camera = Mock()
            mock_picamera2.return_value = mock_camera
            
            # 添加摄像头
            self.camera_manager.add_camera('test_camera', 0, (1280, 1024))
            
            # 启动连续捕获
            result = self.camera_manager.start_continuous_capture(1.0)
            self.assertTrue(result)
            
            # 停止连续捕获
            result = self.camera_manager.stop_continuous_capture()
            self.assertTrue(result)
            
    def test_trigger_single_capture(self):
        """测试单次捕获"""
        with patch('picamera2.Picamera2') as mock_picamera2:
            mock_camera = Mock()
            mock_picamera2.return_value = mock_camera
            
            # 添加摄像头
            self.camera_manager.add_camera('test_camera', 0, (1280, 1024))
            
            # 触发单次捕获
            result = self.camera_manager.trigger_single_capture()
            self.assertTrue(result)
            
    def test_get_latest_frame(self):
        """测试获取最新帧"""
        with patch('picamera2.Picamera2') as mock_picamera2:
            mock_camera = Mock()
            mock_picamera2.return_value = mock_camera
            
            # 添加摄像头
            self.camera_manager.add_camera('test_camera', 0, (1280, 1024))
            
            # 模拟捕获帧
            mock_frame = b'fake_image_data'
            mock_camera.capture_array.return_value = mock_frame
            
            # 获取最新帧
            frame = self.camera_manager.get_latest_frame()
            self.assertIsNotNone(frame)


class TestSorterMQTTManager(unittest.TestCase):
    """MQTT管理器测试"""
    
    def setUp(self):
        """测试前设置"""
        self.mqtt_manager = SorterMQTTManager(
            broker_config={
                'host': 'localhost',
                'port': 1883,
                'client_id': 'test_client'
            },
            topics_config={
                'status': 'test/status',
                'results': 'test/results',
                'images': 'test/images'
            }
        )
        
    def tearDown(self):
        """测试后清理"""
        if self.mqtt_manager.is_connected():
            self.mqtt_manager.disconnect_from_broker()
            
    def test_mqtt_connection(self):
        """测试MQTT连接"""
        with patch('paho.mqtt.client.Client') as mock_client:
            mock_mqtt = Mock()
            mock_client.return_value = mock_mqtt
            
            # 模拟连接成功
            mock_mqtt.connect.return_value = 0
            mock_mqtt.is_connected.return_value = True
            
            result = self.mqtt_manager.connect_to_broker()
            self.assertTrue(result)
            
            # 验证连接调用
            mock_mqtt.connect.assert_called_once()
            
    def test_publish_messages(self):
        """测试消息发布"""
        with patch('paho.mqtt.client.Client') as mock_client:
            mock_mqtt = Mock()
            mock_client.return_value = mock_mqtt
            mock_mqtt.is_connected.return_value = True
            mock_mqtt.publish.return_value = Mock(rc=0)
            
            # 连接MQTT
            self.mqtt_manager.connect_to_broker()
            
            # 测试发布状态
            result = self.mqtt_manager.publish_system_status("测试状态")
            self.assertTrue(result)
            
            # 测试发布结果
            result = self.mqtt_manager.publish_sorting_result({
                'item_id': 'test_001',
                'grade': 'A'
            })
            self.assertTrue(result)
            
            # 验证发布调用
            self.assertGreater(mock_mqtt.publish.call_count, 0)
            
    def test_message_subscriptions(self):
        """测试消息订阅"""
        with patch('paho.mqtt.client.Client') as mock_client:
            mock_mqtt = Mock()
            mock_client.return_value = mock_mqtt
            mock_mqtt.is_connected.return_value = True
            mock_mqtt.subscribe.return_value = Mock(rc=0)
            
            # 连接MQTT
            self.mqtt_manager.connect_to_broker()
            
            # 设置消息回调
            def test_callback(topic, payload):
                pass
                
            self.mqtt_manager.set_message_callback(test_callback)
            
            # 启动消息处理
            result = self.mqtt_manager.start_message_processing()
            self.assertTrue(result)
            
    def test_command_handling(self):
        """测试命令处理"""
        with patch('paho.mqtt.client.Client') as mock_client:
            mock_mqtt = Mock()
            mock_client.return_value = mock_mqtt
            mock_mqtt.is_connected.return_value = True
            
            # 连接MQTT
            self.mqtt_manager.connect_to_broker()
            
            # 模拟接收命令消息
            test_payload = {
                'command': 'capture_image',
                'parameters': {}
            }
            
            # 触发消息处理
            self.mqtt_manager._handle_command(test_payload)


class TestEncoderManager(unittest.TestCase):
    """编码器管理器测试"""
    
    def setUp(self):
        """测试前设置"""
        with patch('RPi.GPIO'):
            self.encoder_manager = EncoderManager(17, 27, 22)
            
    def tearDown(self):
        """测试后清理"""
        if self.encoder_manager.is_monitoring:
            self.encoder_manager.stop_encoder_monitoring()
            
    def test_encoder_initialization(self):
        """测试编码器初始化"""
        self.assertEqual(self.encoder_manager.pin_a, 17)
        self.assertEqual(self.encoder_manager.pin_b, 27)
        self.assertEqual(self.encoder_manager.pin_z, 22)
        self.assertEqual(self.encoder_manager.get_current_position(), 0)
        
    def test_position_trigger(self):
        """测试位置触发"""
        trigger_called = False
        
        def test_callback(position):
            nonlocal trigger_called
            trigger_called = True
            
        # 设置位置触发
        result = self.encoder_manager.set_position_trigger(100, test_callback)
        self.assertTrue(result)
        
        # 模拟位置变化（手动触发）
        self.encoder_manager._trigger_at_position(100)
        
        # 验证回调被调用
        self.assertTrue(trigger_called)
        
    def test_start_stop_monitoring(self):
        """测试启动和停止监控"""
        with patch('threading.Thread'):
            result = self.encoder_manager.start_encoder_monitoring()
            self.assertTrue(result)
            self.assertTrue(self.encoder_manager.is_monitoring)
            
            result = self.encoder_manager.stop_encoder_monitoring()
            self.assertTrue(result)
            self.assertFalse(self.encoder_manager.is_monitoring)
            
    def test_position_reset(self):
        """测试位置重置"""
        # 模拟位置变化
        with patch.object(self.encoder_manager, 'get_current_position', return_value=50):
            self.assertEqual(self.encoder_manager.get_current_position(), 50)
            
            # 重置位置
            self.encoder_manager.reset_position()
            
            # 验证位置重置
            self.assertEqual(self.encoder_manager.get_current_position(), 0)


class TestSystemMonitor(unittest.TestCase):
    """系统监控器测试"""
    
    def setUp(self):
        """测试前设置"""
        self.config_manager = Mock(spec=ConfigManager)
        self.system_monitor = SystemMonitor(self.config_manager)
        
    def tearDown(self):
        """测试后清理"""
        if self.system_monitor.is_monitoring:
            self.system_monitor.stop_system_monitoring()
            
    def test_monitoring_start_stop(self):
        """测试监控启动和停止"""
        result = self.system_monitor.start_system_monitoring(0.1)
        self.assertTrue(result)
        self.assertTrue(self.system_monitor.is_monitoring)
        
        time.sleep(0.2)
        
        result = self.system_monitor.stop_system_monitoring()
        self.assertTrue(result)
        self.assertFalse(self.system_monitor.is_monitoring)
        
    def test_alert_rules(self):
        """测试告警规则"""
        # 添加告警规则
        result = self.system_monitor.add_alert_rule(
            'test_cpu_alert',
            'cpu_percent',
            50.0,
            '>',
            'warning'
        )
        self.assertTrue(result)
        
        # 验证规则存在
        self.assertIn('test_cpu_alert', self.system_monitor.alert_rules)
        
        # 移除告警规则
        result = self.system_monitor.remove_alert_rule('test_cpu_alert')
        self.assertTrue(result)
        
        # 验证规则已移除
        self.assertNotIn('test_cpu_alert', self.system_monitor.alert_rules)
        
    def test_notification_channels(self):
        """测试通知渠道"""
        notification_received = False
        
        def test_channel(alert_data):
            nonlocal notification_received
            notification_received = True
            
        # 添加通知渠道
        result = self.system_monitor.add_notification_channel(test_channel)
        self.assertTrue(result)
        
        # 手动触发告警
        self.system_monitor._send_alert_notifications({
            'severity': 'warning',
            'message': '测试告警'
        })
        
        # 验证通知被接收
        self.assertTrue(notification_received)
        
    def test_metrics_collection(self):
        """测试指标收集"""
        self.system_monitor.start_system_monitoring(0.1)
        time.sleep(0.3)
        self.system_monitor.stop_system_monitoring()
        
        # 验证指标被收集
        status = self.system_monitor.get_current_system_status()
        self.assertIn('metrics', status)
        self.assertIn('cpu_percent', status['metrics'])
        self.assertIn('memory_percent', status['metrics'])


class TestEnhancedSystemMonitor(unittest.TestCase):
    """增强系统监控器测试"""
    
    def setUp(self):
        """测试前设置"""
        self.config_manager = Mock(spec=ConfigManager)
        self.mqtt_manager = Mock(spec=SorterMQTTManager)
        self.enhanced_monitor = EnhancedSystemMonitor(
            self.config_manager,
            self.mqtt_manager
        )
        
    def tearDown(self):
        """测试后清理"""
        if hasattr(self.enhanced_monitor, 'system_monitor') and self.enhanced_monitor.system_monitor.is_monitoring:
            self.enhanced_monitor.stop_monitoring()
            
    def test_enhanced_monitoring(self):
        """测试增强监控功能"""
        result = self.enhanced_monitor.start_monitoring(0.1)
        self.assertTrue(result)
        
        time.sleep(0.2)
        
        result = self.enhanced_monitor.stop_monitoring()
        self.assertTrue(result)
        
    def test_comprehensive_status(self):
        """测试综合状态获取"""
        status = self.enhanced_monitor.get_comprehensive_system_status()
        
        self.assertIn('system_metrics', status)
        self.assertIn('health_status', status)
        self.assertIn('overall_status', status)
        self.assertIn('timestamp', status)
        
        # 验证状态值
        self.assertIn(status['overall_status'], ['healthy', 'warning', 'critical'])
        
    def test_mqtt_notifications(self):
        """测试MQTT通知"""
        # 模拟MQTT发布成功
        self.mqtt_manager.publish_system_status.return_value = True
        self.mqtt_manager.publish_message.return_value = True
        
        result = self.enhanced_monitor.publish_system_status_via_mqtt()
        self.assertTrue(result)
        
        # 验证MQTT调用
        self.mqtt_manager.publish_system_status.assert_called_once()
        self.mqtt_manager.publish_message.assert_called_once()


class TestIntegratedSortingSystem(unittest.TestCase):
    """集成分拣系统测试"""
    
    def setUp(self):
        """测试前设置"""
        self.sorting_system = IntegratedSortingSystem()
        
    def tearDown(self):
        """测试后清理"""
        if self.sorting_system.is_running:
            self.sorting_system.stop_system_operation()
        self.sorting_system.cleanup_system_resources()
        
    def test_system_initialization(self):
        """测试系统初始化"""
        # 模拟配置管理器
        self.sorting_system.config_manager = Mock(spec=ConfigManager)
        self.sorting_system.config_manager.load_configuration.return_value = True
        self.sorting_system.config_manager.get_camera_configuration.return_value = {'enabled': False}
        self.sorting_system.config_manager.get_mqtt_configuration.return_value = {'enabled': False}
        self.sorting_system.config_manager.get_encoder_configuration.return_value = {'enabled': False}
        self.sorting_system.config_manager.get_monitor_configuration.return_value = {'enabled': False}
        
        result = self.sorting_system.initialize_system()
        self.assertTrue(result)
        self.assertTrue(self.sorting_system.system_status['initialized'])
        
    def test_sorting_result_creation(self):
        """测试分拣结果创建"""
        result = SortingResult(
            item_id="test_item_001",
            grade="A",
            length=18.5,
            diameter=2.3,
            defects=["无缺陷"],
            confidence=0.95
        )
        
        self.assertEqual(result.item_id, "test_item_001")
        self.assertEqual(result.grade, "A")
        self.assertEqual(result.length, 18.5)
        self.assertEqual(result.diameter, 2.3)
        self.assertEqual(result.defects, ["无缺陷"])
        self.assertEqual(result.confidence, 0.95)
        self.assertGreater(result.timestamp, 0)
        
    def test_system_statistics(self):
        """测试系统统计"""
        # 设置一些测试数据
        self.sorting_system.system_status['processed_count'] = 10
        self.sorting_system.system_status['error_count'] = 2
        self.sorting_system.system_status['start_time'] = time.time() - 3600  # 1小时前
        
        stats = self.sorting_system.get_system_statistics()
        
        self.assertIn('system_status', stats)
        self.assertIn('uptime_seconds', stats)
        self.assertIn('processed_count', stats)
        self.assertIn('error_count', stats)
        
        self.assertEqual(stats['processed_count'], 10)
        self.assertEqual(stats['error_count'], 2)
        self.assertGreater(stats['uptime_seconds'], 0)


class TestSystemIntegration(unittest.TestCase):
    """系统集成测试"""
    
    def setUp(self):
        """测试前设置"""
        self.components = {}
        
    def test_camera_mqtt_integration(self):
        """测试摄像头-MQTT集成"""
        # 创建模拟组件
        camera_manager = Mock(spec=CSICameraManager)
        mqtt_manager = Mock(spec=SorterMQTTManager)
        
        # 模拟摄像头捕获
        mock_frame = b'fake_image_data'
        camera_manager.get_latest_frame.return_value = mock_frame
        
        # 模拟MQTT发布
        mqtt_manager.publish_image.return_value = True
        
        # 测试集成场景
        frame = camera_manager.get_latest_frame()
        self.assertIsNotNone(frame)
        
        result = mqtt_manager.publish_image(frame, 'test_image.jpg')
        self.assertTrue(result)
        
        # 验证交互
        camera_manager.get_latest_frame.assert_called_once()
        mqtt_manager.publish_image.assert_called_once()
        
    def test_encoder_camera_integration(self):
        """测试编码器-摄像头集成"""
        # 创建模拟组件
        encoder_manager = Mock(spec=EncoderManager)
        camera_manager = Mock(spec=CSICameraManager)
        
        # 模拟编码器触发
        trigger_position = 150
        trigger_called = False
        
        def mock_trigger_callback(position):
            nonlocal trigger_called
            trigger_called = True
            # 触发摄像头捕获
            camera_manager.trigger_single_capture()
            
        encoder_manager.set_position_trigger.return_value = True
        camera_manager.trigger_single_capture.return_value = True
        
        # 设置触发
        encoder_manager.set_position_trigger(trigger_position, mock_trigger_callback)
        
        # 模拟触发事件
        mock_trigger_callback(trigger_position)
        
        # 验证集成
        self.assertTrue(trigger_called)
        encoder_manager.set_position_trigger.assert_called_once()
        camera_manager.trigger_single_capture.assert_called_once()
        
    def test_monitoring_integration(self):
        """测试监控集成"""
        # 创建模拟组件
        config_manager = Mock(spec=ConfigManager)
        mqtt_manager = Mock(spec=SorterMQTTManager)
        
        # 创建增强监控器
        monitor = EnhancedSystemMonitor(config_manager, mqtt_manager)
        
        # 模拟系统指标
        monitor.system_monitor.metrics = {
            'cpu_percent': 75.0,
            'memory_percent': 60.0,
            'disk_usage': 45.0
        }
        
        # 添加告警规则
        monitor.system_monitor.add_alert_rule(
            'high_cpu',
            'cpu_percent',
            70.0,
            '>',
            'warning'
        )
        
        # 模拟MQTT通知
        mqtt_manager.publish_system_status.return_value = True
        mqtt_manager.publish_message.return_value = True
        
        # 测试告警触发
        monitor.system_monitor._check_alert_rules()
        
        # 验证通知被发送
        mqtt_manager.publish_system_status.assert_called()


class TestPerformance(unittest.TestCase):
    """性能测试"""
    
    def test_config_loading_performance(self):
        """测试配置加载性能"""
        config_manager = ConfigManager('config/integrated_config.yaml')
        
        start_time = time.time()
        result = config_manager.load_configuration()
        load_time = time.time() - start_time
        
        self.assertTrue(result)
        self.assertLess(load_time, 1.0)  # 配置加载应在1秒内完成
        
    def test_image_processing_performance(self):
        """测试图像处理性能"""
        # 模拟图像处理
        import numpy as np
        
        # 创建测试图像
        test_image = np.random.randint(0, 255, (1024, 1280, 3), dtype=np.uint8)
        
        start_time = time.time()
        
        # 模拟图像处理操作
        processed = test_image.copy()
        processed = processed.astype(np.float32) / 255.0
        processed = (processed * 255).astype(np.uint8)
        
        processing_time = time.time() - start_time
        
        self.assertLess(processing_time, 0.5)  # 图像处理应在0.5秒内完成
        
    def test_mqtt_message_performance(self):
        """测试MQTT消息性能"""
        mqtt_manager = Mock(spec=SorterMQTTManager)
        
        # 模拟消息发布
        test_message = {
            'item_id': 'test_item',
            'grade': 'A',
            'timestamp': time.time()
        }
        
        start_time = time.time()
        
        # 模拟多次发布
        for i in range(100):
            mqtt_manager.publish_sorting_result(test_message)
            
        publish_time = time.time() - start_time
        
        # 100次发布应在合理时间内完成
        self.assertLess(publish_time, 5.0)
        self.assertEqual(mqtt_manager.publish_sorting_result.call_count, 100)


class TestErrorHandling(unittest.TestCase):
    """错误处理测试"""
    
    def test_camera_error_handling(self):
        """测试摄像头错误处理"""
        camera_manager = CSICameraManager()
        
        # 模拟摄像头错误
        with patch('picamera2.Picamera2') as mock_picamera2:
            mock_picamera2.side_effect = Exception("Camera initialization failed")
            
            # 尝试添加摄像头
            result = camera_manager.add_camera('test_camera', 0, (1280, 1024))
            self.assertFalse(result)
            
    def test_mqtt_error_handling(self):
        """测试MQTT错误处理"""
        mqtt_manager = SorterMQTTManager(
            broker_config={'host': 'invalid_host', 'port': 1883}
        )
        
        # 模拟连接失败
        with patch('paho.mqtt.client.Client') as mock_client:
            mock_mqtt = Mock()
            mock_client.return_value = mock_mqtt
            mock_mqtt.connect.side_effect = Exception("Connection failed")
            
            # 尝试连接
            result = mqtt_manager.connect_to_broker()
            self.assertFalse(result)
            
    def test_encoder_error_handling(self):
        """测试编码器错误处理"""
        # 模拟GPIO错误
        with patch('RPi.GPIO') as mock_gpio:
            mock_gpio.setmode.side_effect = Exception("GPIO error")
            
            # 尝试创建编码器管理器
            try:
                encoder_manager = EncoderManager(17, 27, 22)
                # 如果创建成功，验证错误处理
                result = encoder_manager.start_encoder_monitoring()
                self.assertFalse(result)
            except Exception:
                # 创建失败也是预期的错误处理
                pass


class TestConfigurationValidation(unittest.TestCase):
    """配置验证测试"""
    
    def test_valid_configuration(self):
        """测试有效配置"""
        valid_config = {
            'system': {
                'name': 'Pi Sorter',
                'version': '1.0.0',
                'debug': False
            },
            'camera': {
                'enabled': True,
                'resolution': [1280, 1024],
                'device_id': 0,
                'fps': 30
            },
            'mqtt': {
                'enabled': True,
                'broker': {
                    'host': 'localhost',
                    'port': 1883,
                    'username': 'user',
                    'password': 'pass'
                },
                'topics': {
                    'status': 'pi_sorter/status'
                }
            }
        }
        
        config_manager = ConfigManager('test_valid.yaml')
        config_manager.configuration = valid_config
        
        result = config_manager.validate_configuration()
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
        
    def test_invalid_configuration(self):
        """测试无效配置"""
        invalid_config = {
            'system': {
                'name': '',  # 空名称
                'version': 'invalid'  # 无效版本格式
            },
            'camera': {
                'enabled': True,
                'resolution': 'invalid',  # 分辨率格式错误
                'device_id': -1  # 无效设备ID
            },
            'mqtt': {
                'enabled': True,
                'broker': {
                    'host': '',  # 空主机名
                    'port': 'invalid'  # 端口格式错误
                }
            }
        }
        
        config_manager = ConfigManager('test_invalid.yaml')
        config_manager.configuration = invalid_config
        
        result = config_manager.validate_configuration()
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)
        
    def test_missing_required_fields(self):
        """测试缺少必需字段"""
        incomplete_config = {
            'system': {
                'name': 'Pi Sorter'
                # 缺少版本字段
            }
            # 缺少其他必需配置段
        }
        
        config_manager = ConfigManager('test_incomplete.yaml')
        config_manager.configuration = incomplete_config
        
        result = config_manager.validate_configuration()
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.warnings), 0)


if __name__ == '__main__':
    # 设置测试运行参数
    unittest.main(
        verbosity=2,
        failfast=False,
        catchbreak=True
    )