#!/usr/bin/env python3
"""
Pi Sorter - 测试配置和环境设置
为测试提供配置和环境支持
"""

import os
import sys
import json
import yaml
import tempfile
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../src/external'))


class TestEnvironment:
    """测试环境管理器"""
    
    def __init__(self):
        """初始化测试环境"""
        self.temp_dir = None
        self.config_files = {}
        self.mock_objects = {}
        
    def setup_environment(self):
        """设置测试环境"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp(prefix='pi_sorter_test_')
        
        # 创建测试配置文件
        self._create_test_configurations()
        
        # 设置模拟对象
        self._setup_mock_objects()
        
        print(f"🧪 测试环境已设置: {self.temp_dir}")
        
    def cleanup_environment(self):
        """清理测试环境"""
        # 清理临时文件
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
            
        # 清理模拟对象
        self.mock_objects.clear()
        
        print("🧹 测试环境已清理")
        
    def _create_test_configurations(self):
        """创建测试配置"""
        # 基础系统配置
        base_config = {
            'system': {
                'name': 'Pi Sorter Test System',
                'version': '1.0.0',
                'debug': True,
                'log_level': 'DEBUG',
                'data_dir': os.path.join(self.temp_dir, 'data'),
                'log_dir': os.path.join(self.temp_dir, 'logs')
            },
            'camera': {
                'enabled': True,
                'device_id': 0,
                'resolution': [1280, 1024],
                'fps': 30,
                'auto_capture': True,
                'capture_interval': 5.0,
                'capture_only': True,
                'brightness': 0.5,
                'contrast': 0.5,
                'saturation': 0.5,
                'exposure_time': -1
            },
            'mqtt': {
                'enabled': True,
                'broker': {
                    'host': 'localhost',
                    'port': 1883,
                    'username': 'test_user',
                    'password': 'test_pass',
                    'client_id': 'pi_sorter_test'
                },
                'topics': {
                    'status': 'pi_sorter/test/status',
                    'results': 'pi_sorter/test/results',
                    'images': 'pi_sorter/test/images',
                    'alerts': 'pi_sorter/test/alerts',
                    'heartbeat': 'pi_sorter/test/heartbeat',
                    'commands': 'pi_sorter/test/commands'
                },
                'settings': {
                    'qos': 1,
                    'retain': False,
                    'keepalive': 60,
                    'reconnect_delay': 5,
                    'max_reconnect_attempts': 10
                }
            },
            'encoder': {
                'enabled': True,
                'pin_a': 17,
                'pin_b': 27,
                'pin_z': 22,
                'trigger_position': 150,
                'debounce_ms': 50
            },
            'monitoring': {
                'enabled': True,
                'check_interval': 30,
                'alert_rules': [
                    {
                        'name': 'high_cpu_usage',
                        'metric': 'cpu_percent',
                        'threshold': 80.0,
                        'operator': '>',
                        'severity': 'warning'
                    },
                    {
                        'name': 'low_disk_space',
                        'metric': 'disk_usage',
                        'threshold': 90.0,
                        'operator': '>',
                        'severity': 'critical'
                    }
                ]
            },
            'sorting': {
                'grade_thresholds': {
                    'A': 15000,
                    'B': 5000,
                    'C': 0
                },
                'image_processing': {
                    'quality': 95,
                    'format': 'JPEG',
                    'save_processed': True
                }
            }
        }
        
        # 保存配置文件
        config_path = os.path.join(self.temp_dir, 'test_config.yaml')
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(base_config, f, default_flow_style=False, allow_unicode=True)
            
        self.config_files['base_config'] = config_path
        
        # MQTT配置
        mqtt_config = {
            'broker': {
                'host': 'localhost',
                'port': 1883,
                'username': 'test_user',
                'password': 'test_pass',
                'client_id': 'pi_sorter_test'
            },
            'topics': {
                'status': 'pi_sorter/test/status',
                'results': 'pi_sorter/test/results',
                'images': 'pi_sorter/test/images',
                'alerts': 'pi_sorter/test/alerts',
                'heartbeat': 'pi_sorter/test/heartbeat',
                'commands': 'pi_sorter/test/commands'
            },
            'settings': {
                'qos': 1,
                'retain': False,
                'keepalive': 60,
                'reconnect_delay': 5,
                'max_reconnect_attempts': 10
            }
        }
        
        mqtt_path = os.path.join(self.temp_dir, 'test_mqtt_config.json')
        with open(mqtt_path, 'w', encoding='utf-8') as f:
            json.dump(mqtt_config, f, indent=2, ensure_ascii=False)
            
        self.config_files['mqtt_config'] = mqtt_path
        
        # 创建数据目录
        data_dir = os.path.join(self.temp_dir, 'data')
        logs_dir = os.path.join(self.temp_dir, 'logs')
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(logs_dir, exist_ok=True)
        
    def _setup_mock_objects(self):
        """设置模拟对象"""
        # 模拟Picamera2
        self.mock_objects['picamera2'] = Mock()
        
        # 模拟MQTT客户端
        self.mock_objects['mqtt_client'] = Mock()
        self.mock_objects['mqtt_client'].is_connected.return_value = True
        self.mock_objects['mqtt_client'].publish.return_value = Mock(rc=0)
        self.mock_objects['mqtt_client'].subscribe.return_value = Mock(rc=0)
        
        # 模拟GPIO
        self.mock_objects['gpio'] = Mock()
        self.mock_objects['gpio'].getmode.return_value = 11  # BCM模式
        
        # 模拟系统监控指标
        self.mock_objects['system_metrics'] = {
            'cpu_percent': 25.0,
            'memory_percent': 40.0,
            'disk_usage': 60.0,
            'cpu_count': 4,
            'memory_total': 4 * 1024 * 1024 * 1024,  # 4GB
            'memory_available': 2 * 1024 * 1024 * 1024,  # 2GB
            'disk_total': 32 * 1024 * 1024 * 1024,  # 32GB
            'disk_free': 12 * 1024 * 1024 * 1024  # 12GB
        }
        
    def get_config_file_path(self, config_type: str) -> Optional[str]:
        """获取配置文件路径"""
        return self.config_files.get(config_type)
        
    def get_mock_object(self, object_name: str) -> Optional[Mock]:
        """获取模拟对象"""
        return self.mock_objects.get(object_name)
        
    def create_test_image(self, width: int = 1280, height: int = 1024) -> bytes:
        """创建测试图像数据"""
        import numpy as np
        from PIL import Image
        import io
        
        # 创建随机图像
        array = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
        image = Image.fromarray(array)
        
        # 保存为JPEG格式
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=95)
        
        return buffer.getvalue()
        
    def create_test_sorting_result(self, item_id: str = "test_item") -> Dict[str, Any]:
        """创建测试分拣结果"""
        return {
            'item_id': item_id,
            'grade': 'A',
            'length': 18.5,
            'diameter': 2.3,
            'defects': [],
            'confidence': 0.95,
            'timestamp': int(time.time() * 1000),
            'processing_time': 0.25
        }


class TestDataGenerator:
    """测试数据生成器"""
    
    def __init__(self):
        """初始化数据生成器"""
        self.item_counter = 0
        
    def generate_item_id(self) -> str:
        """生成物品ID"""
        self.item_counter += 1
        return f"item_{self.item_counter:06d}"
        
    def generate_grade(self) -> str:
        """生成分级"""
        import random
        grades = ['A', 'B', 'C']
        weights = [0.6, 0.3, 0.1]  # A级60%，B级30%，C级10%
        return random.choices(grades, weights=weights)[0]
        
    def generate_dimensions(self, grade: str) -> tuple:
        """生成长度和直径"""
        import random
        
        if grade == 'A':
            length = random.uniform(15.0, 25.0)
            diameter = random.uniform(1.8, 2.8)
        elif grade == 'B':
            length = random.uniform(10.0, 20.0)
            diameter = random.uniform(1.5, 2.5)
        else:  # C级
            length = random.uniform(5.0, 15.0)
            diameter = random.uniform(1.0, 2.0)
            
        return round(length, 1), round(diameter, 2)
        
    def generate_defects(self, grade: str) -> list:
        """生成缺陷列表"""
        import random
        
        all_defects = ['弯曲', '断裂', '变色', '斑点', '虫蛀', '机械损伤']
        
        if grade == 'A':
            # A级很少缺陷
            if random.random() < 0.1:  # 10%概率有缺陷
                return [random.choice(all_defects[:2])]  # 只选轻微缺陷
            return []
        elif grade == 'B':
            # B级可能有轻微缺陷
            if random.random() < 0.3:  # 30%概率有缺陷
                defect_count = random.randint(1, 2)
                return random.sample(all_defects[:4], defect_count)
            return []
        else:  # C级
            # C级可能有多个缺陷
            if random.random() < 0.7:  # 70%概率有缺陷
                defect_count = random.randint(1, 3)
                return random.sample(all_defects, defect_count)
            return []
            
    def generate_sorting_result(self) -> Dict[str, Any]:
        """生成分拣结果"""
        grade = self.generate_grade()
        length, diameter = self.generate_dimensions(grade)
        defects = self.generate_defects(grade)
        
        # 根据缺陷调整置信度
        confidence = 0.95
        if defects:
            confidence -= len(defects) * 0.1  # 每个缺陷降低10%置信度
            confidence = max(0.5, confidence)  # 最低50%置信度
            
        return {
            'item_id': self.generate_item_id(),
            'grade': grade,
            'length': length,
            'diameter': diameter,
            'defects': defects,
            'confidence': round(confidence, 2),
            'timestamp': int(time.time() * 1000),
            'processing_time': round(random.uniform(0.1, 0.5), 3)
        }
        
    def generate_batch_results(self, count: int) -> List[Dict[str, Any]]:
        """生成一批分拣结果"""
        return [self.generate_sorting_result() for _ in range(count)]


class TestAssertions:
    """测试断言工具"""
    
    @staticmethod
    def assert_config_valid(config: Dict[str, Any]):
        """断言配置有效"""
        assert isinstance(config, dict), "配置必须是字典类型"
        assert 'system' in config, "配置必须包含system段"
        assert 'camera' in config, "配置必须包含camera段"
        assert 'mqtt' in config, "配置必须包含mqtt段"
        
    @staticmethod
    def assert_mqtt_connected(mqtt_manager):
        """断言MQTT已连接"""
        assert mqtt_manager.is_connected(), "MQTT应该已连接"
        
    @staticmethod
    def assert_camera_initialized(camera_manager, camera_name: str):
        """断言摄像头已初始化"""
        cameras = camera_manager.get_all_cameras()
        assert camera_name in cameras, f"摄像头 {camera_name} 应该已初始化"
        
    @staticmethod
    def assert_encoder_position(encoder_manager, expected_position: int):
        """断言编码器位置"""
        current_position = encoder_manager.get_current_position()
        assert current_position == expected_position, f"编码器位置应该是 {expected_position}, 实际是 {current_position}"
        
    @staticmethod
    def assert_sorting_result_valid(result: Dict[str, Any]):
        """断言分拣结果有效"""
        required_fields = ['item_id', 'grade', 'length', 'diameter', 'confidence', 'timestamp']
        for field in required_fields:
            assert field in result, f"分拣结果必须包含字段 {field}"
            
        assert result['grade'] in ['A', 'B', 'C'], "分级必须是 A, B, 或 C"
        assert 0.0 <= result['confidence'] <= 1.0, "置信度必须在0.0到1.0之间"
        assert result['length'] > 0, "长度必须大于0"
        assert result['diameter'] > 0, "直径必须大于0"
        
    @staticmethod
    def assert_system_healthy(system_status: Dict[str, Any]):
        """断言系统健康"""
        assert 'overall_status' in system_status, "系统状态必须包含overall_status"
        assert system_status['overall_status'] in ['healthy', 'warning', 'critical'], "系统状态必须是 healthy, warning, 或 critical"
        
        if system_status['overall_status'] == 'healthy':
            assert 'system_metrics' in system_status, "健康状态应该包含系统指标"
            assert 'health_status' in system_status, "健康状态应该包含健康状态详情"


def create_test_environment() -> TestEnvironment:
    """创建测试环境"""
    env = TestEnvironment()
    env.setup_environment()
    return env


def generate_test_data(count: int = 1) -> list:
    """生成测试数据"""
    generator = TestDataGenerator()
    return generator.generate_batch_results(count)


# 全局测试工具
test_assertions = TestAssertions()


if __name__ == '__main__':
    # 测试测试环境
    print("🧪 测试测试环境设置...")
    
    env = create_test_environment()
    
    print(f"✅ 测试环境已创建: {env.temp_dir}")
    print(f"📁 配置文件: {list(env.config_files.keys())}")
    print(f"🎭 模拟对象: {list(env.mock_objects.keys())}")
    
    # 生成测试数据
    generator = TestDataGenerator()
    test_results = generator.generate_batch_results(5)
    
    print(f"\n📊 生成测试数据:")
    for i, result in enumerate(test_results):
        print(f"  {i+1}. {result['item_id']} - 等级: {result['grade']}, 长度: {result['length']}cm, 置信度: {result['confidence']}")
    
    # 验证测试断言
    try:
        for result in test_results:
            test_assertions.assert_sorting_result_valid(result)
        print("\n✅ 所有测试断言通过")
    except AssertionError as e:
        print(f"\n❌ 测试断言失败: {e}")
    
    # 清理环境
    env.cleanup_environment()
    print("\n🧹 测试环境已清理完成")