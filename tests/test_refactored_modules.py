import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
import json
import yaml
import os
import tempfile
import threading
import time
from typing import Dict, Any, Optional

# 导入重构后的模块
import sys
sys.path.append('c:/my_source/pi_sorter/src/external')

from config_manager_refactored import ConfigManager, ConfigFormat, ValidationResult
from picamera2_module_refactored import CSICamera, CSICameraManager, CSICameraLegacy
from mqtt_manager_refactored import MQTTManager, SorterMQTTManager
from encoder_module_refactored import RotaryEncoder, EncoderManager, EncoderModule


class TestConfigManager(unittest.TestCase):
    """配置管理器单元测试"""
    
    def setUp(self):
        """测试前设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigManager()
        
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_load_valid_json_configuration(self):
        """测试加载有效的JSON配置"""
        test_config = {
            'system': {
                'name': 'Test System',
                'version': '1.0.0'
            },
            'camera': {
                'enabled': True,
                'resolution': [1280, 1024],
                'brightness': 0.5
            }
        }
        
        config_path = os.path.join(self.temp_dir, 'test_config.json')
        with open(config_path, 'w') as f:
            json.dump(test_config, f)
            
        result = self.config_manager.load_configuration(config_path)
        
        self.assertTrue(result)
        self.assertEqual(self.config_manager.get_configuration_value('system.name'), 'Test System')
        self.assertEqual(self.config_manager.get_configuration_value('camera.resolution'), [1280, 1024])
        
    def test_load_valid_yaml_configuration(self):
        """测试加载有效的YAML配置"""
        test_config = {
            'system': {
                'name': 'Test System',
                'version': '1.0.0'
            },
            'camera': {
                'enabled': True,
                'resolution': [1280, 1024]
            }
        }
        
        config_path = os.path.join(self.temp_dir, 'test_config.yaml')
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
            
        result = self.config_manager.load_configuration(config_path)
        
        self.assertTrue(result)
        self.assertEqual(self.config_manager.get_configuration_value('system.name'), 'Test System')
        
    def test_load_nonexistent_configuration(self):
        """测试加载不存在的配置文件"""
        result = self.config_manager.load_configuration('nonexistent.json')
        
        self.assertFalse(result)
        
    def test_validate_valid_configuration(self):
        """测试验证有效的配置"""
        test_config = {
            'camera': {
                'enabled': True,
                'resolution': [1280, 1024],
                'brightness': 0.5,
                'contrast': 1.0
            }
        }
        
        self.config_manager.config_data = test_config
        result = self.config_manager.validate_configuration()
        
        self.assertIsInstance(result, ValidationResult)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
        
    def test_validate_invalid_camera_resolution(self):
        """测试验证无效的摄像头分辨率"""
        test_config = {
            'camera': {
                'enabled': True,
                'resolution': 'invalid_resolution'
            }
        }
        
        self.config_manager.config_data = test_config
        result = self.config_manager.validate_configuration()
        
        self.assertFalse(result.is_valid)
        self.assertIn('摄像头分辨率配置无效', result.errors)
        
    def test_validate_missing_required_fields(self):
        """测试验证缺少必填字段"""
        test_config = {
            'camera': {
                'enabled': True
                # 缺少resolution字段
            }
        }
        
        self.config_manager.config_data = test_config
        result = self.config_manager.validate_configuration()
        
        self.assertFalse(result.is_valid)
        self.assertTrue(any('分辨率' in error for error in result.errors))
        
    def test_get_configuration_value_with_nested_keys(self):
        """测试使用嵌套键获取配置值"""
        test_config = {
            'system': {
                'mqtt': {
                    'broker': {
                        'host': 'test.mosquitto.org',
                        'port': 1883
                    }
                }
            }
        }
        
        self.config_manager.config_data = test_config
        
        self.assertEqual(
            self.config_manager.get_configuration_value('system.mqtt.broker.host'),
            'test.mosquitto.org'
        )
        self.assertEqual(
            self.config_manager.get_configuration_value('system.mqtt.broker.port'),
            1883
        )
        
    def test_set_configuration_value(self):
        """测试设置配置值"""
        self.config_manager.config_data = {}
        
        result = self.config_manager.set_configuration_value('test.key', 'test_value')
        
        self.assertTrue(result)
        self.assertEqual(self.config_manager.get_configuration_value('test.key'), 'test_value')
        
    def test_get_camera_configuration(self):
        """测试获取摄像头配置"""
        test_config = {
            'camera': {
                'enabled': True,
                'resolution': [1280, 1024],
                'brightness': 0.5
            }
        }
        
        self.config_manager.config_data = test_config
        camera_config = self.config_manager.get_camera_configuration()
        
        self.assertIsInstance(camera_config, dict)
        self.assertEqual(camera_config['enabled'], True)
        self.assertEqual(camera_config['resolution'], [1280, 1024])
        
    def test_get_mqtt_configuration(self):
        """测试获取MQTT配置"""
        test_config = {
            'mqtt': {
                'broker': {
                    'host': 'test.mosquitto.org',
                    'port': 1883,
                    'username': 'testuser',
                    'password': 'testpass'
                }
            }
        }
        
        self.config_manager.config_data = test_config
        mqtt_config = self.config_manager.get_mqtt_configuration()
        
        self.assertIsInstance(mqtt_config, dict)
        self.assertEqual(mqtt_config['host'], 'test.mosquitto.org')
        self.assertEqual(mqtt_config['port'], 1883)
        
    def test_configuration_change_callback(self):
        """测试配置变更回调"""
        callback_called = threading.Event()
        callback_data = {}
        
        def test_callback(old_config: Dict[str, Any], new_config: Dict[str, Any]):
            callback_data['old'] = old_config
            callback_data['new'] = new_config
            callback_called.set()
            
        self.config_manager.add_configuration_change_callback(test_callback)
        
        old_config = self.config_manager.config_data.copy()
        self.config_manager.set_configuration_value('test.key', 'test_value')
        
        # 等待回调执行
        callback_called.wait(timeout=1.0)
        
        self.assertTrue(callback_called.is_set())
        self.assertEqual(callback_data['old'], old_config)
        self.assertEqual(callback_data['new']['test']['key'], 'test_value')
        
    def test_hot_reload_configuration(self):
        """测试配置热重载"""
        test_config = {
            'system': {'name': 'Original System'}
        }
        
        config_path = os.path.join(self.temp_dir, 'test_config.json')
        with open(config_path, 'w') as f:
            json.dump(test_config, f)
            
        self.config_manager.load_configuration(config_path)
        
        # 修改配置文件
        test_config['system']['name'] = 'Updated System'
        with open(config_path, 'w') as f:
            json.dump(test_config, f)
            
        # 模拟文件系统变更事件
        self.config_manager._handle_configuration_file_change(config_path)
        
        # 验证配置已更新
        self.assertEqual(
            self.config_manager.get_configuration_value('system.name'),
            'Updated System'
        )


class TestCSICamera(unittest.TestCase):
    """CSI摄像头单元测试"""
    
    def setUp(self):
        """测试前设置"""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    @patch('picamera2_module_refactored.Picamera2')
    def test_initialize_camera_success(self, mock_picamera2):
        """测试成功初始化摄像头"""
        mock_camera = Mock()
        mock_picamera2.return_value = mock_camera
        
        camera = CSICamera(camera_num=0, resolution=(1280, 1024))
        result = camera.initialize_camera()
        
        self.assertTrue(result)
        mock_picamera2.assert_called_once()
        
    @patch('picamera2_module_refactored.Picamera2')
    def test_capture_single_image(self, mock_picamera2):
        """测试单张图像捕获"""
        mock_camera = Mock()
        mock_picamera2.return_value = mock_camera
        
        camera = CSICamera(camera_num=0, resolution=(1280, 1024))
        camera.initialize_camera()
        
        image_path = os.path.join(self.temp_dir, 'test_image.jpg')
        result = camera.capture_single_image(image_path)
        
        self.assertTrue(result)
        mock_camera.start_and_capture_file.assert_called_once_with(image_path)
        
    @patch('picamera2_module_refactored.Picamera2')
    def test_set_camera_parameters(self, mock_picamera2):
        """测试设置摄像头参数"""
        mock_camera = Mock()
        mock_picamera2.return_value = mock_camera
        
        camera = CSICamera(camera_num=0, resolution=(1280, 1024))
        camera.initialize_camera()
        
        result = camera.set_camera_parameters(
            brightness=0.8,
            contrast=1.2,
            saturation=0.9,
            exposure_time=1000
        )
        
        self.assertTrue(result)
        # 验证参数设置调用
        self.assertTrue(mock_camera.set_controls.called)
        
    @patch('picamera2_module_refactored.Picamera2')
    def test_start_continuous_capture(self, mock_picamera2):
        """测试开始连续捕获"""
        mock_camera = Mock()
        mock_picamera2.return_value = mock_camera
        
        camera = CSICamera(camera_num=0, resolution=(1280, 1024))
        camera.initialize_camera()
        
        capture_dir = self.temp_dir
        result = camera.start_continuous_capture(capture_dir, interval=1.0)
        
        self.assertTrue(result)
        self.assertTrue(camera.is_capturing)
        
        # 停止捕获
        camera.stop_continuous_capture()
        self.assertFalse(camera.is_capturing)
        
    def test_camera_context_manager(self):
        """测试摄像头上下文管理器"""
        with patch('picamera2_module_refactored.Picamera2'):
            with CSICamera(camera_num=0, resolution=(1280, 1024)) as camera:
                self.assertIsNotNone(camera)
                self.assertTrue(hasattr(camera, 'camera'))
                
            # 退出上下文后摄像头应被释放
            self.assertIsNone(camera.camera)
            
    def test_get_camera_info(self):
        """测试获取摄像头信息"""
        camera = CSICamera(camera_num=0, resolution=(1280, 1024))
        
        info = camera.get_camera_info()
        
        self.assertIsInstance(info, dict)
        self.assertEqual(info['camera_num'], 0)
        self.assertEqual(info['resolution'], (1280, 1024))
        self.assertIn('initialized', info)
        
    def test_camera_error_handling(self):
        """测试摄像头错误处理"""
        camera = CSICamera(camera_num=999)  # 不存在的摄像头
        
        # 初始化应该失败
        result = camera.initialize_camera()
        self.assertFalse(result)
        
        # 捕获图像应该失败
        result = camera.capture_single_image('test.jpg')
        self.assertFalse(result)


class TestCSICameraManager(unittest.TestCase):
    """CSI摄像头管理器单元测试"""
    
    def setUp(self):
        """测试前设置"""
        self.manager = CSICameraManager()
        
    @patch('picamera2_module_refactored.Picamera2')
    def test_add_camera_success(self, mock_picamera2):
        """测试成功添加摄像头"""
        result = self.manager.add_camera('main_camera', camera_num=0, resolution=(1280, 1024))
        
        self.assertTrue(result)
        self.assertIn('main_camera', self.manager.list_cameras())
        
    @patch('picamera2_module_refactored.Picamera2')
    def test_get_camera(self, mock_picamera2):
        """测试获取摄像头"""
        self.manager.add_camera('test_camera', camera_num=0)
        
        camera = self.manager.get_camera('test_camera')
        
        self.assertIsNotNone(camera)
        self.assertIsInstance(camera, CSICamera)
        
    def test_get_nonexistent_camera(self):
        """测试获取不存在的摄像头"""
        camera = self.manager.get_camera('nonexistent')
        
        self.assertIsNone(camera)
        
    @patch('picamera2_module_refactored.Picamera2')
    def test_remove_camera(self, mock_picamera2):
        """测试移除摄像头"""
        self.manager.add_camera('test_camera', camera_num=0)
        
        result = self.manager.remove_camera('test_camera')
        
        self.assertTrue(result)
        self.assertNotIn('test_camera', self.manager.list_cameras())
        
    def test_remove_nonexistent_camera(self):
        """测试移除不存在的摄像头"""
        result = self.manager.remove_camera('nonexistent')
        
        self.assertFalse(result)
        
    @patch('picamera2_module_refactored.Picamera2')
    def test_list_cameras(self, mock_picamera2):
        """测试列出摄像头"""
        self.manager.add_camera('camera1', camera_num=0)
        self.manager.add_camera('camera2', camera_num=1)
        
        cameras = self.manager.list_cameras()
        
        self.assertEqual(len(cameras), 2)
        self.assertIn('camera1', cameras)
        self.assertIn('camera2', cameras)
        
    @patch('picamera2_module_refactored.Picamera2')
    def test_release_all_cameras(self, mock_picamera2):
        """测试释放所有摄像头"""
        self.manager.add_camera('camera1', camera_num=0)
        self.manager.add_camera('camera2', camera_num=1)
        
        self.manager.release_all_cameras()
        
        self.assertEqual(len(self.manager.list_cameras()), 0)
        
    def test_camera_manager_context_manager(self):
        """测试摄像头管理器上下文管理器"""
        with patch('picamera2_module_refactored.Picamera2'):
            with CSICameraManager() as manager:
                manager.add_camera('test_camera', camera_num=0)
                self.assertIn('test_camera', manager.list_cameras())
                
            # 退出上下文后所有摄像头应被释放
            self.assertEqual(len(manager.list_cameras()), 0)


class TestMQTTManager(unittest.TestCase):
    """MQTT管理器单元测试"""
    
    def setUp(self):
        """测试前设置"""
        self.broker_config = {
            'host': 'test.mosquitto.org',
            'port': 1883,
            'client_id': 'test_client',
            'username': 'testuser',
            'password': 'testpass'
        }
        self.mqtt_manager = MQTTManager(self.broker_config)
        
    @patch('mqtt_manager_refactored.mqtt.Client')
    def test_connect_to_broker_success(self, mock_client_class):
        """测试成功连接到MQTT代理"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.connect.return_value = 0
        
        result = self.mqtt_manager.connect_to_broker(timeout=5)
        
        self.assertTrue(result)
        mock_client.connect.assert_called_once_with(
            self.broker_config['host'],
            self.broker_config['port'],
            60
        )
        
    @patch('mqtt_manager_refactored.mqtt.Client')
    def test_publish_message_success(self, mock_client_class):
        """测试成功发布消息"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.publish.return_value = Mock(rc=0)
        
        self.mqtt_manager.connect_to_broker()
        
        result = self.mqtt_manager.publish_message('test/topic', 'test message')
        
        self.assertTrue(result)
        mock_client.publish.assert_called_once_with('test/topic', 'test message', qos=1)
        
    @patch('mqtt_manager_refactored.mqtt.Client')
    def test_subscribe_to_topic(self, mock_client_class):
        """测试订阅主题"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        callback = Mock()
        self.mqtt_manager.connect_to_broker()
        
        result = self.mqtt_manager.subscribe_to_topic('test/topic', callback)
        
        self.assertTrue(result)
        mock_client.subscribe.assert_called_once_with('test/topic', qos=1)
        
    @patch('mqtt_manager_refactored.mqtt.Client')
    def test_disconnect_from_broker(self, mock_client_class):
        """测试断开MQTT连接"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        self.mqtt_manager.connect_to_broker()
        result = self.mqtt_manager.disconnect_from_broker()
        
        self.assertTrue(result)
        mock_client.disconnect.assert_called_once()
        
    def test_message_formatting(self):
        """测试消息格式化"""
        message = self.mqtt_manager.format_system_message('test_status')
        
        self.assertIsInstance(message, dict)
        self.assertIn('timestamp', message)
        self.assertIn('status', message)
        self.assertEqual(message['status'], 'test_status')
        
    def test_topic_validation(self):
        """测试主题验证"""
        valid_topics = ['test/topic', 'pi_sorter/status', 'camera/image']
        invalid_topics = ['test topic', 'test\\topic', 'test\n\ntopic']
        
        for topic in valid_topics:
            self.assertTrue(self.mqtt_manager.validate_topic_name(topic))
            
        for topic in invalid_topics:
            self.assertFalse(self.mqtt_manager.validate_topic_name(topic))


class TestSorterMQTTManager(unittest.TestCase):
    """分拣系统MQTT管理器单元测试"""
    
    def setUp(self):
        """测试前设置"""
        self.broker_config = {
            'broker': {
                'host': 'test.mosquitto.org',
                'port': 1883,
                'client_id': 'sorter_client',
                'username': 'admin',
                'password': 'admin1970'
            },
            'topics': {
                'status': 'pi_sorter/status',
                'images': 'pi_sorter/images',
                'results': 'pi_sorter/results',
                'alerts': 'pi_sorter/alerts'
            }
        }
        self.sorter_manager = SorterMQTTManager(self.broker_config)
        
    @patch('mqtt_manager_refactored.mqtt.Client')
    def test_publish_system_status(self, mock_client_class):
        """测试发布系统状态"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.publish.return_value = Mock(rc=0)
        
        self.sorter_manager.connect_to_broker()
        
        result = self.sorter_manager.publish_system_status('系统运行正常')
        
        self.assertTrue(result)
        mock_client.publish.assert_called_once()
        
        # 验证发布的消息格式
        call_args = mock_client.publish.call_args
        self.assertEqual(call_args[0][0], 'pi_sorter/status')
        
    @patch('mqtt_manager_refactored.mqtt.Client')
    def test_publish_sorting_result(self, mock_client_class):
        """测试发布分拣结果"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.publish.return_value = Mock(rc=0)
        
        self.sorter_manager.connect_to_broker()
        
        result_data = {
            'item_id': '001',
            'grade': 'A',
            'length': 180.5,
            'diameter': 12.3
        }
        
        result = self.sorter_manager.publish_sorting_result(result_data)
        
        self.assertTrue(result)
        mock_client.publish.assert_called_once_with(
            'pi_sorter/results',
            unittest.mock.ANY,  # JSON字符串
            qos=1
        )
        
    @patch('mqtt_manager_refactored.mqtt.Client')
    def test_publish_image(self, mock_client_class):
        """测试发布图像"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.publish.return_value = Mock(rc=0)
        
        self.sorter_manager.connect_to_broker()
        
        # 创建测试图像数据
        test_image_data = b'fake_image_data'
        
        result = self.sorter_manager.publish_image(
            'test_image.jpg',
            test_image_data,
            use_base64=True
        )
        
        self.assertTrue(result)
        mock_client.publish.assert_called_once_with(
            'pi_sorter/images',
            unittest.mock.ANY,  # Base64编码的JSON
            qos=1
        )
        
    @patch('mqtt_manager_refactored.mqtt.Client')
    def test_publish_alert(self, mock_client_class):
        """测试发布告警"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.publish.return_value = Mock(rc=0)
        
        self.sorter_manager.connect_to_broker()
        
        result = self.sorter_manager.publish_alert('warning', '测试告警')
        
        self.assertTrue(result)
        mock_client.publish.assert_called_once_with(
            'pi_sorter/alerts',
            unittest.mock.ANY,  # JSON字符串
            qos=1
        )


class TestRotaryEncoder(unittest.TestCase):
    """旋转编码器单元测试"""
    
    def setUp(self):
        """测试前设置"""
        # 模拟GPIO模块
        self.mock_gpio = Mock()
        self.gpio_patch = patch('encoder_module_refactored.GPIO', self.mock_gpio)
        self.gpio_patch.start()
        
        self.encoder = RotaryEncoder(pin_a=17, pin_b=27, pin_z=22)
        
    def tearDown(self):
        """测试后清理"""
        self.gpio_patch.stop()
        
    def test_encoder_initialization(self):
        """测试编码器初始化"""
        self.assertEqual(self.encoder.pin_a, 17)
        self.assertEqual(self.encoder.pin_b, 27)
        self.assertEqual(self.encoder.pin_z, 22)
        self.assertEqual(self.encoder.get_encoder_position(), 0)
        
    def test_reset_encoder_position(self):
        """测试重置编码器位置"""
        # 模拟位置变化
        self.encoder.position = 100
        
        self.encoder.reset_encoder_position()
        
        self.assertEqual(self.encoder.get_encoder_position(), 0)
        
    def test_set_trigger_position(self):
        """测试设置触发位置"""
        callback = Mock()
        
        result = self.encoder.set_trigger_position(150, callback)
        
        self.assertTrue(result)
        self.assertEqual(self.encoder.trigger_position, 150)
        self.assertEqual(self.encoder.trigger_callback, callback)
        
    def test_start_encoder_monitoring(self):
        """测试开始编码器监控"""
        result = self.encoder.start_encoder_monitoring()
        
        self.assertTrue(result)
        self.assertTrue(self.encoder.is_running)
        self.mock_gpio.add_event_detect.assert_called()
        
    def test_stop_encoder_monitoring(self):
        """测试停止编码器监控"""
        self.encoder.start_encoder_monitoring()
        
        result = self.encoder.stop_encoder_monitoring()
        
        self.assertTrue(result)
        self.assertFalse(self.encoder.is_running)
        
    def test_encoder_context_manager(self):
        """测试编码器上下文管理器"""
        with RotaryEncoder(pin_a=17, pin_b=27, pin_z=22) as encoder:
            self.assertIsNotNone(encoder)
            self.assertTrue(encoder.is_running)
            
        # 退出上下文后应该停止监控
        self.assertFalse(encoder.is_running)
        
    def test_handle_encoder_callback(self):
        """测试编码器回调处理"""
        callback = Mock()
        self.encoder.set_trigger_position(2, callback)
        
        # 模拟编码器旋转
        self.encoder.position = 1
        self.encoder._handle_encoder_position_change(2)
        
        # 触发位置应该调用回调
        callback.assert_called_once_with(2)
        
    def test_handle_zero_position(self):
        """测试归零处理"""
        self.encoder.position = 100
        
        # 模拟Z相触发
        self.encoder._handle_zero_position(22)
        
        self.assertEqual(self.encoder.get_encoder_position(), 0)


class TestEncoderManager(unittest.TestCase):
    """编码器管理器单元测试"""
    
    def setUp(self):
        """测试前设置"""
        self.mock_gpio = Mock()
        self.gpio_patch = patch('encoder_module_refactored.GPIO', self.mock_gpio)
        self.gpio_patch.start()
        
        self.manager = EncoderManager()
        
    def tearDown(self):
        """测试后清理"""
        self.gpio_patch.stop()
        
    def test_add_encoder(self):
        """测试添加编码器"""
        result = self.manager.add_encoder('test_encoder', pin_a=17, pin_b=27, pin_z=22)
        
        self.assertTrue(result)
        self.assertIn('test_encoder', self.manager.list_encoders())
        
    def test_get_encoder(self):
        """测试获取编码器"""
        self.manager.add_encoder('test_encoder', pin_a=17, pin_b=27, pin_z=22)
        
        encoder = self.manager.get_encoder('test_encoder')
        
        self.assertIsNotNone(encoder)
        self.assertIsInstance(encoder, RotaryEncoder)
        
    def test_remove_encoder(self):
        """测试移除编码器"""
        self.manager.add_encoder('test_encoder', pin_a=17, pin_b=27, pin_z=22)
        
        result = self.manager.remove_encoder('test_encoder')
        
        self.assertTrue(result)
        self.assertNotIn('test_encoder', self.manager.list_encoders())
        
    def test_start_all_encoders(self):
        """测试启动所有编码器"""
        self.manager.add_encoder('encoder1', pin_a=17, pin_b=27, pin_z=22)
        self.manager.add_encoder('encoder2', pin_a=23, pin_b=24, pin_z=25)
        
        result = self.manager.start_all_encoders()
        
        self.assertTrue(result)
        
        encoder1 = self.manager.get_encoder('encoder1')
        encoder2 = self.manager.get_encoder('encoder2')
        
        self.assertTrue(encoder1.is_running)
        self.assertTrue(encoder2.is_running)
        
    def test_stop_all_encoders(self):
        """测试停止所有编码器"""
        self.manager.add_encoder('encoder1', pin_a=17, pin_b=27, pin_z=22)
        self.manager.add_encoder('encoder2', pin_a=23, pin_b=24, pin_z=25)
        
        self.manager.start_all_encoders()
        self.manager.stop_all_encoders()
        
        encoder1 = self.manager.get_encoder('encoder1')
        encoder2 = self.manager.get_encoder('encoder2')
        
        self.assertFalse(encoder1.is_running)
        self.assertFalse(encoder2.is_running)
        
    def test_encoder_manager_context_manager(self):
        """测试编码器管理器上下文管理器"""
        with EncoderManager() as manager:
            manager.add_encoder('test_encoder', pin_a=17, pin_b=27, pin_z=22)
            self.assertIn('test_encoder', manager.list_encoders())
            
        # 退出上下文后所有编码器应被停止
        self.assertEqual(len(manager.list_encoders()), 0)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def setUp(self):
        """测试前设置"""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    @patch('picamera2_module_refactored.Picamera2')
    @patch('mqtt_manager_refactored.mqtt.Client')
    def test_camera_mqtt_integration(self, mock_mqtt_client, mock_picamera2):
        """测试摄像头和MQTT集成"""
        # 设置模拟对象
        mock_camera = Mock()
        mock_picamera2.return_value = mock_camera
        
        mock_mqtt = Mock()
        mock_mqtt_client.return_value = mock_mqtt
        mock_mqtt.publish.return_value = Mock(rc=0)
        
        # 创建配置
        config_data = {
            'camera': {
                'enabled': True,
                'resolution': [640, 480]
            },
            'mqtt': {
                'broker': {
                    'host': 'test.mosquitto.org',
                    'port': 1883
                }
            }
        }
        
        config_path = os.path.join(self.temp_dir, 'config.json')
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
            
        # 初始化系统组件
        config_manager = ConfigManager()
        config_manager.load_configuration(config_path)
        
        camera_manager = CSICameraManager()
        camera_manager.add_camera('main', camera_num=0)
        
        mqtt_manager = SorterMQTTManager(config_manager.get_mqtt_configuration())
        mqtt_manager.connect_to_broker()
        
        # 测试捕获并发布图像
        camera = camera_manager.get_camera('main')
        image_path = os.path.join(self.temp_dir, 'test.jpg')
        
        # 模拟图像捕获
        camera.capture_single_image(image_path)
        
        # 模拟发布图像
        with open(image_path, 'rb') as f:
            image_data = f.read()
            
        result = mqtt_manager.publish_image('test.jpg', image_data)
        
        self.assertTrue(result)
        mock_mqtt.publish.assert_called()
        
        # 清理
        camera_manager.release_all_cameras()
        mqtt_manager.disconnect_from_broker()
        
    @patch('encoder_module_refactored.GPIO')
    def test_encoder_config_integration(self, mock_gpio):
        """测试编码器和配置集成"""
        # 创建测试配置
        config_data = {
            'encoder': {
                'pin_a': 17,
                'pin_b': 27,
                'pin_z': 22,
                'trigger_position': 150
            }
        }
        
        config_path = os.path.join(self.temp_dir, 'config.json')
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
            
        # 加载配置
        config_manager = ConfigManager()
        config_manager.load_configuration(config_path)
        
        # 创建编码器管理器
        encoder_manager = EncoderManager()
        
        # 从配置创建编码器
        encoder_config = config_manager.get_configuration_value('encoder', {})
        if encoder_config:
            encoder_manager.add_encoder(
                'main_encoder',
                pin_a=encoder_config.get('pin_a', 17),
                pin_b=encoder_config.get('pin_b', 27),
                pin_z=encoder_config.get('pin_z', 22)
            )
            
        # 验证编码器创建
        encoder = encoder_manager.get_encoder('main_encoder')
        self.assertIsNotNone(encoder)
        
        # 验证触发位置设置
        trigger_pos = encoder_config.get('trigger_position', 150)
        encoder.set_trigger_position(trigger_pos, lambda pos: None)
        self.assertEqual(encoder.trigger_position, trigger_pos)
        
        # 清理
        encoder_manager.stop_all_encoders()


if __name__ == '__main__':
    # 运行所有测试
    unittest.main(verbosity=2)