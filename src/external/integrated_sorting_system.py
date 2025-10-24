import os
import sys
import time
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

# 添加项目路径到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../external'))

from config_manager_refactored import ConfigManager
from picamera2_module_refactored import CSICameraManager
from mqtt_manager_refactored import SorterMQTTManager
from encoder_module_refactored import EncoderManager
from system_monitor import EnhancedSystemMonitor


@dataclass
class SortingResult:
    """分拣结果数据类"""
    item_id: str
    grade: str
    length: float
    diameter: float
    defects: List[str]
    image_path: Optional[str] = None
    timestamp: float = 0.0
    confidence: float = 0.0
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class IntegratedSortingSystem:
    """集成分拣系统 - 重构版本"""
    
    def __init__(self, config_path: str = "config/integrated_config.yaml"):
        """初始化集成分拣系统"""
        self.config_path = config_path
        self.is_running = False
        self.main_thread = None
        
        # 初始化日志
        self._setup_logging()
        self.logger = logging.getLogger(f"{__name__}.IntegratedSortingSystem")
        
        # 初始化组件
        self.config_manager = None
        self.camera_manager = None
        self.mqtt_manager = None
        self.encoder_manager = None
        self.system_monitor = None
        
        # 系统状态
        self.system_status = {
            'initialized': False,
            'components_ready': {},
            'last_error': None,
            'start_time': None,
            'processed_count': 0,
            'error_count': 0
        }
        
        # 分拣结果缓存
        self.sorting_results = []
        self.max_results_cache = 1000
        
        self.logger.info("集成分拣系统初始化开始")
        
    def _setup_logging(self):
        """设置日志系统"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('logs/integrated_system.log')
            ]
        )
        
    def initialize_system(self) -> bool:
        """初始化系统组件"""
        try:
            self.logger.info("开始系统初始化")
            
            # 1. 初始化配置管理器
            self.config_manager = ConfigManager(self.config_path)
            if not self.config_manager.load_configuration():
                raise RuntimeError("配置管理器初始化失败")
            self.system_status['components_ready']['config'] = True
            self.logger.info("配置管理器初始化成功")
            
            # 2. 初始化摄像头管理器
            self.camera_manager = CSICameraManager()
            camera_config = self.config_manager.get_camera_configuration()
            if camera_config.get('enabled', True):
                success = self._initialize_cameras()
                if not success:
                    self.logger.warning("摄像头初始化失败，系统将继续运行但无摄像头功能")
            else:
                self.logger.info("摄像头功能已禁用")
                
            # 3. 初始化MQTT管理器
            mqtt_config = self.config_manager.get_mqtt_configuration()
            if mqtt_config.get('enabled', True):
                success = self._initialize_mqtt()
                if not success:
                    self.logger.warning("MQTT初始化失败，系统将继续运行但无通信功能")
            else:
                self.logger.info("MQTT功能已禁用")
                
            # 4. 初始化编码器管理器
            encoder_config = self.config_manager.get_encoder_configuration()
            if encoder_config.get('enabled', True):
                success = self._initialize_encoder()
                if not success:
                    self.logger.warning("编码器初始化失败，系统将继续运行但无编码器功能")
            else:
                self.logger.info("编码器功能已禁用")
                
            # 5. 初始化系统监控器
            self.system_monitor = EnhancedSystemMonitor(
                self.config_manager,
                self.mqtt_manager
            )
            
            # 6. 验证系统状态
            self._validate_system_readiness()
            
            self.system_status['initialized'] = True
            self.system_status['start_time'] = time.time()
            
            self.logger.info("系统集成初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"系统初始化失败: {e}")
            self.system_status['last_error'] = str(e)
            return False
            
    def _initialize_cameras(self) -> bool:
        """初始化摄像头"""
        try:
            camera_config = self.config_manager.get_camera_configuration()
            
            # 添加主摄像头
            success = self.camera_manager.add_camera(
                name='main',
                camera_num=camera_config.get('device_id', 0),
                resolution=tuple(camera_config.get('resolution', [1280, 1024]))
            )
            
            if success:
                self.system_status['components_ready']['camera'] = True
                self.logger.info("摄像头初始化成功")
                return True
            else:
                self.logger.error("摄像头添加失败")
                return False
                
        except Exception as e:
            self.logger.error(f"摄像头初始化异常: {e}")
            return False
            
    def _initialize_mqtt(self) -> bool:
        """初始化MQTT"""
        try:
            mqtt_config = self.config_manager.get_mqtt_configuration()
            
            self.mqtt_manager = SorterMQTTManager(
                broker_config=mqtt_config.get('broker', {}),
                topics_config=mqtt_config.get('topics', {}),
                settings_config=mqtt_config.get('settings', {})
            )
            
            if self.mqtt_manager.connect_to_broker():
                self.system_status['components_ready']['mqtt'] = True
                self.logger.info("MQTT初始化成功")
                return True
            else:
                self.logger.error("MQTT连接失败")
                return False
                
        except Exception as e:
            self.logger.error(f"MQTT初始化异常: {e}")
            return False
            
    def _initialize_encoder(self) -> bool:
        """初始化编码器"""
        try:
            encoder_config = self.config_manager.get_encoder_configuration()
            
            self.encoder_manager = EncoderManager(
                pin_a=encoder_config.get('pin_a', 17),
                pin_b=encoder_config.get('pin_b', 27),
                pin_z=encoder_config.get('pin_z', 22)
            )
            
            # 设置编码器触发回调
            self.encoder_manager.set_position_trigger(
                position=encoder_config.get('trigger_position', 150),
                callback=self._handle_encoder_trigger
            )
            
            if self.encoder_manager.start_encoder_monitoring():
                self.system_status['components_ready']['encoder'] = True
                self.logger.info("编码器初始化成功")
                return True
            else:
                self.logger.error("编码器启动失败")
                return False
                
        except Exception as e:
            self.logger.error(f"编码器初始化异常: {e}")
            return False
            
    def _validate_system_readiness(self):
        """验证系统就绪状态"""
        required_components = ['config']
        optional_components = ['camera', 'mqtt', 'encoder']
        
        ready_components = []
        failed_components = []
        
        for component in required_components + optional_components:
            if component in self.system_status['components_ready']:
                if self.system_status['components_ready'][component]:
                    ready_components.append(component)
                else:
                    failed_components.append(component)
                    
        self.logger.info(f"就绪组件: {ready_components}")
        if failed_components:
            self.logger.warning(f"失败组件: {failed_components}")
            
        # 如果有必需组件失败，则系统不可用
        for component in required_components:
            if component in failed_components:
                raise RuntimeError(f"必需组件 {component} 初始化失败")
                
    def start_system_operation(self) -> bool:
        """启动系统运行"""
        try:
            if not self.system_status['initialized']:
                self.logger.error("系统未初始化，无法启动")
                return False
                
            self.logger.info("开始启动系统运行")
            
            # 启动系统监控
            monitor_config = self.config_manager.get_monitor_configuration()
            if monitor_config.get('enabled', True):
                monitor_interval = monitor_config.get('interval', 5.0)
                self.system_monitor.start_monitoring(monitor_interval)
                
            # 启动摄像头连续捕获（如果可用）
            if self.camera_manager and 'camera' in self.system_status['components_ready']:
                camera_config = self.config_manager.get_camera_configuration()
                if camera_config.get('auto_capture', True):
                    capture_interval = camera_config.get('capture_interval', 5.0)
                    self.camera_manager.start_continuous_capture(capture_interval)
                    
            # 启动MQTT消息处理（如果可用）
            if self.mqtt_manager and 'mqtt' in self.system_status['components_ready']:
                self.mqtt_manager.start_message_processing()
                
                # 发布系统启动状态
                self.mqtt_manager.publish_system_status("分拣系统已启动")
                
            self.is_running = True
            self.main_thread = threading.Thread(target=self._main_operation_loop, daemon=True)
            self.main_thread.start()
            
            self.logger.info("系统运行已启动")
            return True
            
        except Exception as e:
            self.logger.error(f"启动系统运行失败: {e}")
            self.system_status['last_error'] = str(e)
            return False
            
    def stop_system_operation(self) -> bool:
        """停止系统运行"""
        try:
            self.logger.info("开始停止系统运行")
            
            self.is_running = False
            
            # 等待主线程结束
            if self.main_thread:
                self.main_thread.join(timeout=10.0)
                
            # 停止系统监控
            if self.system_monitor:
                self.system_monitor.stop_monitoring()
                
            # 停止摄像头捕获
            if self.camera_manager:
                self.camera_manager.stop_continuous_capture()
                
            # 停止MQTT
            if self.mqtt_manager:
                self.mqtt_manager.publish_system_status("分拣系统已停止")
                self.mqtt_manager.disconnect_from_broker()
                
            # 停止编码器
            if self.encoder_manager:
                self.encoder_manager.stop_encoder_monitoring()
                
            self.logger.info("系统运行已停止")
            return True
            
        except Exception as e:
            self.logger.error(f"停止系统运行失败: {e}")
            return False
            
    def _main_operation_loop(self):
        """主操作循环"""
        self.logger.info("主操作循环开始")
        
        while self.is_running:
            try:
                # 处理分拣任务
                self._process_sorting_tasks()
                
                # 发布系统状态
                self._publish_system_status()
                
                # 处理MQTT消息
                if self.mqtt_manager:
                    self._process_mqtt_commands()
                    
                time.sleep(0.1)  # 主循环间隔
                
            except Exception as e:
                self.logger.error(f"主操作循环错误: {e}")
                self.system_status['error_count'] += 1
                time.sleep(1.0)  # 错误后等待更长时间
                
        self.logger.info("主操作循环结束")
        
    def _process_sorting_tasks(self):
        """处理分拣任务"""
        try:
            # 检查是否有新的图像需要处理
            if self.camera_manager:
                latest_frame = self.camera_manager.get_latest_frame()
                if latest_frame:
                    self._process_image_and_sort(latest_frame)
                    
        except Exception as e:
            self.logger.error(f"处理分拣任务失败: {e}")
            
    def _process_image_and_sort(self, image_data):
        """处理图像并进行分拣"""
        try:
            # 图像处理和分级逻辑
            sorting_result = self._analyze_image_and_grade(image_data)
            
            if sorting_result:
                # 保存结果
                self.sorting_results.append(sorting_result)
                
                # 限制结果缓存大小
                if len(self.sorting_results) > self.max_results_cache:
                    self.sorting_results.pop(0)
                    
                # 发布结果
                self._publish_sorting_result(sorting_result)
                
                self.system_status['processed_count'] += 1
                
        except Exception as e:
            self.logger.error(f"图像处理和分拣失败: {e}")
            
    def _analyze_image_and_grade(self, image_data) -> Optional[SortingResult]:
        """分析图像并进行分级"""
        try:
            # 模拟图像分析过程
            import random
            
            # 生成模拟结果（实际应用中这里应该是真实的图像处理逻辑）
            grades = ['A', 'B', 'C']
            defects_list = [['无缺陷'], ['轻微缺陷'], ['明显缺陷']]
            
            result = SortingResult(
                item_id=f"item_{int(time.time() * 1000)}",
                grade=random.choice(grades),
                length=random.uniform(15.0, 25.0),
                diameter=random.uniform(1.0, 3.0),
                defects=random.choice(defects_list),
                confidence=random.uniform(0.7, 0.95)
            )
            
            self.logger.info(f"分拣结果: {result.item_id} - 等级: {result.grade}")
            return result
            
        except Exception as e:
            self.logger.error(f"图像分析失败: {e}")
            return None
            
    def _publish_sorting_result(self, result: SortingResult):
        """发布分拣结果"""
        try:
            if self.mqtt_manager:
                result_data = {
                    'item_id': result.item_id,
                    'grade': result.grade,
                    'length': result.length,
                    'diameter': result.diameter,
                    'defects': result.defects,
                    'confidence': result.confidence,
                    'timestamp': result.timestamp
                }
                
                self.mqtt_manager.publish_sorting_result(result_data)
                
        except Exception as e:
            self.logger.error(f"发布分拣结果失败: {e}")
            
    def _handle_encoder_trigger(self, position: int):
        """处理编码器触发"""
        try:
            self.logger.info(f"编码器触发 - 位置: {position}")
            
            # 触发拍照
            if self.camera_manager:
                self.camera_manager.trigger_single_capture()
                
            # 发布触发事件
            if self.mqtt_manager:
                self.mqtt_manager.publish_system_status(f"编码器触发 - 位置: {position}")
                
        except Exception as e:
            self.logger.error(f"处理编码器触发失败: {e}")
            
    def _publish_system_status(self):
        """发布系统状态"""
        try:
            if self.mqtt_manager and self.system_monitor:
                self.system_monitor.publish_system_status_via_mqtt()
                
        except Exception as e:
            self.logger.error(f"发布系统状态失败: {e}")
            
    def _process_mqtt_commands(self):
        """处理MQTT命令"""
        try:
            # 这里可以添加MQTT命令处理逻辑
            pass
            
        except Exception as e:
            self.logger.error(f"处理MQTT命令失败: {e}")
            
    def get_system_statistics(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        try:
            uptime = time.time() - self.system_status['start_time'] if self.system_status['start_time'] else 0
            
            return {
                'system_status': self.system_status.copy(),
                'uptime_seconds': uptime,
                'processed_count': self.system_status['processed_count'],
                'error_count': self.system_status['error_count'],
                'sorting_results_count': len(self.sorting_results),
                'component_status': self.system_status['components_ready'].copy(),
                'timestamp': time.time()
            }
            
        except Exception as e:
            self.logger.error(f"获取系统统计信息失败: {e}")
            return {}
            
    def export_sorting_results(self, filepath: str, format: str = 'json') -> bool:
        """导出分拣结果"""
        try:
            if format.lower() == 'json':
                results_data = []
                for result in self.sorting_results:
                    results_data.append({
                        'item_id': result.item_id,
                        'grade': result.grade,
                        'length': result.length,
                        'diameter': result.diameter,
                        'defects': result.defects,
                        'confidence': result.confidence,
                        'timestamp': result.timestamp
                    })
                    
                with open(filepath, 'w') as f:
                    json.dump(results_data, f, indent=2)
                    
            elif format.lower() == 'csv':
                import csv
                
                with open(filepath, 'w', newline='') as f:
                    if self.sorting_results:
                        fieldnames = ['item_id', 'grade', 'length', 'diameter', 
                                    'defects', 'confidence', 'timestamp']
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        
                        for result in self.sorting_results:
                            writer.writerow({
                                'item_id': result.item_id,
                                'grade': result.grade,
                                'length': result.length,
                                'diameter': result.diameter,
                                'defects': ';'.join(result.defects),
                                'confidence': result.confidence,
                                'timestamp': result.timestamp
                            })
            else:
                self.logger.error(f"不支持的导出格式: {format}")
                return False
                
            self.logger.info(f"分拣结果导出成功: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出分拣结果失败: {e}")
            return False
            
    def cleanup_system_resources(self):
        """清理系统资源"""
        try:
            self.logger.info("开始清理系统资源")
            
            # 停止系统运行
            if self.is_running:
                self.stop_system_operation()
                
            # 清理各个组件
            if self.camera_manager:
                self.camera_manager.release_all_cameras()
                
            if self.encoder_manager:
                self.encoder_manager.cleanup_encoder_resources()
                
            if self.mqtt_manager:
                self.mqtt_manager.disconnect_from_broker()
                
            self.logger.info("系统资源清理完成")
            
        except Exception as e:
            self.logger.error(f"清理系统资源失败: {e}")


# 测试类
class TestIntegratedSortingSystem(unittest.TestCase):
    """集成分拣系统测试"""
    
    def setUp(self):
        """测试前设置"""
        self.system = IntegratedSortingSystem()
        
    def tearDown(self):
        """测试后清理"""
        if self.system.is_running:
            self.system.stop_system_operation()
        self.system.cleanup_system_resources()
        
    def test_system_initialization(self):
        """测试系统初始化"""
        # 模拟配置管理器
        self.system.config_manager = Mock(spec=ConfigManager)
        self.system.config_manager.load_configuration.return_value = True
        self.system.config_manager.get_camera_configuration.return_value = {
            'enabled': False
        }
        self.system.config_manager.get_mqtt_configuration.return_value = {
            'enabled': False
        }
        self.system.config_manager.get_encoder_configuration.return_value = {
            'enabled': False
        }
        self.system.config_manager.get_monitor_configuration.return_value = {
            'enabled': False
        }
        
        # 初始化系统
        result = self.system.initialize_system()
        self.assertTrue(result)
        self.assertTrue(self.system.system_status['initialized'])
        
    def test_system_start_stop(self):
        """测试系统启动和停止"""
        # 先初始化系统（模拟）
        self.system.system_status['initialized'] = True
        self.system.system_status['components_ready'] = {
            'config': True
        }
        
        # 启动系统
        result = self.system.start_system_operation()
        self.assertTrue(result)
        self.assertTrue(self.system.is_running)
        
        # 停止系统
        result = self.system.stop_system_operation()
        self.assertTrue(result)
        self.assertFalse(self.system.is_running)
        
    def test_sorting_result_creation(self):
        """测试分拣结果创建"""
        result = SortingResult(
            item_id="test_001",
            grade="A",
            length=20.0,
            diameter=2.0,
            defects=["无缺陷"],
            confidence=0.9
        )
        
        self.assertEqual(result.item_id, "test_001")
        self.assertEqual(result.grade, "A")
        self.assertEqual(result.length, 20.0)
        self.assertEqual(result.diameter, 2.0)
        self.assertEqual(result.defects, ["无缺陷"])
        self.assertEqual(result.confidence, 0.9)
        self.assertGreater(result.timestamp, 0)
        
    def test_system_statistics(self):
        """测试系统统计"""
        stats = self.system.get_system_statistics()
        
        self.assertIn('system_status', stats)
        self.assertIn('uptime_seconds', stats)
        self.assertIn('processed_count', stats)
        self.assertIn('error_count', stats)
        self.assertIn('timestamp', stats)
        
    def test_export_sorting_results(self):
        """测试导出分拣结果"""
        import tempfile
        
        # 添加一些测试结果
        self.system.sorting_results.append(SortingResult(
            item_id="test_001",
            grade="A",
            length=20.0,
            diameter=2.0,
            defects=["无缺陷"]
        ))
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
            
        try:
            # 导出结果
            result = self.system.export_sorting_results(temp_file, 'json')
            self.assertTrue(result)
            
            # 验证文件内容
            with open(temp_file, 'r') as f:
                data = json.load(f)
                
            self.assertIsInstance(data, list)
            self.assertGreater(len(data), 0)
            
            # 验证数据格式
            item = data[0]
            self.assertIn('item_id', item)
            self.assertIn('grade', item)
            self.assertIn('length', item)
            self.assertIn('diameter', item)
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)