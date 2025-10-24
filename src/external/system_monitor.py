import unittest
from unittest.mock import Mock, patch, MagicMock, call
import threading
import time
import json
import psutil
from typing import Dict, Any, Optional

# 导入重构后的模块
import sys
sys.path.append('c:/my_source/pi_sorter/src/external')

from config_manager_refactored import ConfigManager
from picamera2_module_refactored import CSICameraManager
from mqtt_manager_refactored import SorterMQTTManager
from encoder_module_refactored import EncoderManager


class SystemMonitor:
    """系统监控器 - 增强版本"""
    
    def __init__(self, config_manager: ConfigManager):
        """初始化系统监控器"""
        self.config_manager = config_manager
        self.is_monitoring = False
        self.monitoring_thread = None
        self.alert_rules = {}
        self.notification_channels = []
        self.metrics_history = []
        self.max_history_size = 1000
        
        # 监控指标
        self.metrics = {
            'cpu_percent': 0.0,
            'memory_percent': 0.0,
            'disk_usage': 0.0,
            'temperature': 0.0,
            'network_bytes_sent': 0,
            'network_bytes_recv': 0,
            'process_count': 0,
            'thread_count': 0
        }
        
        # 告警状态
        self.alert_status = {}
        
        # 日志记录器
        import logging
        self.logger = logging.getLogger(f"{__name__}.SystemMonitor")
        
    def start_system_monitoring(self, interval: float = 5.0) -> bool:
        """启动系统监控"""
        try:
            self.is_monitoring = True
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                args=(interval,),
                daemon=True
            )
            self.monitoring_thread.start()
            
            self.logger.info(f"系统监控已启动，间隔: {interval}秒")
            return True
            
        except Exception as e:
            self.logger.error(f"启动系统监控失败: {e}")
            return False
            
    def stop_system_monitoring(self) -> bool:
        """停止系统监控"""
        try:
            self.is_monitoring = False
            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=5.0)
                
            self.logger.info("系统监控已停止")
            return True
            
        except Exception as e:
            self.logger.error(f"停止系统监控失败: {e}")
            return False
            
    def _monitoring_loop(self, interval: float):
        """监控循环"""
        while self.is_monitoring:
            try:
                # 收集系统指标
                self._collect_system_metrics()
                
                # 检查告警规则
                self._check_alert_rules()
                
                # 保存历史数据
                self._save_metrics_to_history()
                
                time.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"监控循环错误: {e}")
                time.sleep(interval)
                
    def _collect_system_metrics(self):
        """收集系统指标"""
        try:
            # CPU使用率
            self.metrics['cpu_percent'] = psutil.cpu_percent(interval=1)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            self.metrics['memory_percent'] = memory.percent
            
            # 磁盘使用率
            disk = psutil.disk_usage('/')
            self.metrics['disk_usage'] = disk.percent
            
            # 网络统计
            network = psutil.net_io_counters()
            self.metrics['network_bytes_sent'] = network.bytes_sent
            self.metrics['network_bytes_recv'] = network.bytes_recv
            
            # 进程和线程数
            self.metrics['process_count'] = len(psutil.pids())
            self.metrics['thread_count'] = threading.active_count()
            
            # 温度（如果可用）
            try:
                temperatures = psutil.sensors_temperatures()
                if 'cpu_thermal' in temperatures:
                    self.metrics['temperature'] = temperatures['cpu_thermal'][0].current
                else:
                    self.metrics['temperature'] = 0.0
            except (AttributeError, IOError):
                self.metrics['temperature'] = 0.0
                
        except Exception as e:
            self.logger.error(f"收集系统指标失败: {e}")
            
    def _check_alert_rules(self):
        """检查告警规则"""
        for rule_name, rule_config in self.alert_rules.items():
            try:
                metric_name = rule_config.get('metric')
                threshold = rule_config.get('threshold')
                operator = rule_config.get('operator', '>')
                severity = rule_config.get('severity', 'warning')
                
                if metric_name not in self.metrics:
                    continue
                    
                current_value = self.metrics[metric_name]
                
                # 检查阈值
                triggered = False
                if operator == '>':
                    triggered = current_value > threshold
                elif operator == '<':
                    triggered = current_value < threshold
                elif operator == '>=':
                    triggered = current_value >= threshold
                elif operator == '<=':
                    triggered = current_value <= threshold
                elif operator == '==':
                    triggered = current_value == threshold
                elif operator == '!=':
                    triggered = current_value != threshold
                    
                # 更新告警状态
                if triggered:
                    if not self.alert_status.get(rule_name, False):
                        # 新触发的告警
                        self._trigger_alert(rule_name, rule_config, current_value)
                        self.alert_status[rule_name] = True
                else:
                    if self.alert_status.get(rule_name, False):
                        # 恢复的告警
                        self._recover_alert(rule_name, rule_config, current_value)
                        self.alert_status[rule_name] = False
                        
            except Exception as e:
                self.logger.error(f"检查告警规则 {rule_name} 失败: {e}")
                
    def _trigger_alert(self, rule_name: str, rule_config: Dict[str, Any], current_value: float):
        """触发告警"""
        try:
            alert_data = {
                'rule_name': rule_name,
                'severity': rule_config.get('severity', 'warning'),
                'metric': rule_config.get('metric'),
                'current_value': current_value,
                'threshold': rule_config.get('threshold'),
                'operator': rule_config.get('operator', '>'),
                'timestamp': time.time(),
                'message': f"告警: {rule_name} 当前值 {current_value} 触发阈值 {rule_config.get('operator', '>')} {rule_config.get('threshold')}"
            }
            
            self.logger.warning(f"告警触发: {alert_data['message']}")
            
            # 发送通知
            self._send_alert_notifications(alert_data)
            
        except Exception as e:
            self.logger.error(f"触发告警失败: {e}")
            
    def _recover_alert(self, rule_name: str, rule_config: Dict[str, Any], current_value: float):
        """恢复告警"""
        try:
            recovery_data = {
                'rule_name': rule_name,
                'severity': 'info',
                'metric': rule_config.get('metric'),
                'current_value': current_value,
                'threshold': rule_config.get('threshold'),
                'operator': rule_config.get('operator', '>'),
                'timestamp': time.time(),
                'message': f"恢复: {rule_name} 当前值 {current_value} 已恢复正常"
            }
            
            self.logger.info(f"告警恢复: {recovery_data['message']}")
            
            # 发送恢复通知
            self._send_alert_notifications(recovery_data)
            
        except Exception as e:
            self.logger.error(f"恢复告警失败: {e}")
            
    def _send_alert_notifications(self, alert_data: Dict[str, Any]):
        """发送告警通知"""
        for channel in self.notification_channels:
            try:
                channel(alert_data)
            except Exception as e:
                self.logger.error(f"发送通知失败: {e}")
                
    def _save_metrics_to_history(self):
        """保存指标到历史记录"""
        try:
            metrics_copy = self.metrics.copy()
            metrics_copy['timestamp'] = time.time()
            
            self.metrics_history.append(metrics_copy)
            
            # 限制历史记录大小
            if len(self.metrics_history) > self.max_history_size:
                self.metrics_history.pop(0)
                
        except Exception as e:
            self.logger.error(f"保存历史指标失败: {e}")
            
    def add_alert_rule(self, name: str, metric: str, threshold: float, 
                      operator: str = '>', severity: str = 'warning') -> bool:
        """添加告警规则"""
        try:
            self.alert_rules[name] = {
                'metric': metric,
                'threshold': threshold,
                'operator': operator,
                'severity': severity
            }
            
            self.logger.info(f"添加告警规则: {name} - {metric} {operator} {threshold}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加告警规则失败: {e}")
            return False
            
    def remove_alert_rule(self, name: str) -> bool:
        """移除告警规则"""
        try:
            if name in self.alert_rules:
                del self.alert_rules[name]
                if name in self.alert_status:
                    del self.alert_status[name]
                    
                self.logger.info(f"移除告警规则: {name}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"移除告警规则失败: {e}")
            return False
            
    def add_notification_channel(self, channel: callable) -> bool:
        """添加通知渠道"""
        try:
            self.notification_channels.append(channel)
            self.logger.info("添加通知渠道成功")
            return True
            
        except Exception as e:
            self.logger.error(f"添加通知渠道失败: {e}")
            return False
            
    def get_current_system_status(self) -> Dict[str, Any]:
        """获取当前系统状态"""
        return {
            'metrics': self.metrics.copy(),
            'alert_rules': self.alert_rules.copy(),
            'alert_status': self.alert_status.copy(),
            'is_monitoring': self.is_monitoring,
            'history_size': len(self.metrics_history)
        }
        
    def get_metrics_history(self, duration: int = 3600) -> list:
        """获取指标历史"""
        try:
            current_time = time.time()
            cutoff_time = current_time - duration
            
            filtered_history = [
                metrics for metrics in self.metrics_history
                if metrics.get('timestamp', 0) >= cutoff_time
            ]
            
            return filtered_history
            
        except Exception as e:
            self.logger.error(f"获取指标历史失败: {e}")
            return []
            
    def export_metrics_to_file(self, filepath: str, format: str = 'json') -> bool:
        """导出指标到文件"""
        try:
            data = {
                'current_metrics': self.metrics,
                'alert_rules': self.alert_rules,
                'alert_status': self.alert_status,
                'metrics_history': self.metrics_history[-100:],  # 最近100条
                'export_time': time.time()
            }
            
            if format.lower() == 'json':
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)
            elif format.lower() == 'csv':
                import csv
                with open(filepath, 'w', newline='') as f:
                    if self.metrics_history:
                        writer = csv.DictWriter(f, fieldnames=self.metrics_history[0].keys())
                        writer.writeheader()
                        writer.writerows(self.metrics_history[-100:])
            else:
                self.logger.error(f"不支持的导出格式: {format}")
                return False
                
            self.logger.info(f"指标导出成功: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出指标失败: {e}")
            return False


class SystemHealthChecker:
    """系统健康检查器"""
    
    def __init__(self, config_manager: ConfigManager):
        """初始化健康检查器"""
        self.config_manager = config_manager
        self.health_checks = {}
        self.last_check_results = {}
        
        import logging
        self.logger = logging.getLogger(f"{__name__}.SystemHealthChecker")
        
    def register_health_check(self, name: str, check_func: callable) -> bool:
        """注册健康检查"""
        try:
            self.health_checks[name] = check_func
            self.logger.info(f"注册健康检查: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"注册健康检查失败: {e}")
            return False
            
    def run_health_checks(self) -> Dict[str, Any]:
        """运行所有健康检查"""
        results = {
            'overall_status': 'healthy',
            'checks': {},
            'timestamp': time.time()
        }
        
        failed_checks = []
        
        for name, check_func in self.health_checks.items():
            try:
                check_result = check_func()
                results['checks'][name] = check_result
                
                if not check_result.get('status', False):
                    failed_checks.append(name)
                    
            except Exception as e:
                self.logger.error(f"健康检查 {name} 失败: {e}")
                results['checks'][name] = {
                    'status': False,
                    'message': f"检查异常: {str(e)}",
                    'error': str(e)
                }
                failed_checks.append(name)
                
        # 确定整体状态
        if failed_checks:
            results['overall_status'] = 'unhealthy' if len(failed_checks) > 2 else 'degraded'
            results['failed_checks'] = failed_checks
            
        self.last_check_results = results
        return results
        
    def get_system_health_report(self) -> str:
        """获取系统健康报告"""
        results = self.run_health_checks()
        
        report = f"系统健康检查报告\n"
        report += f"时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(results['timestamp']))}\n"
        report += f"整体状态: {results['overall_status']}\n\n"
        
        for name, check in results['checks'].items():
            status_symbol = "✓" if check.get('status', False) else "✗"
            report += f"{status_symbol} {name}: {check.get('message', '未知')}\n"
            
        if 'failed_checks' in results:
            report += f"\n失败检查: {', '.join(results['failed_checks'])}\n"
            
        return report


class EnhancedSystemMonitor:
    """增强系统监控器 - 整合所有监控功能"""
    
    def __init__(self, config_manager: ConfigManager, mqtt_manager: Optional[SorterMQTTManager] = None):
        """初始化增强系统监控器"""
        self.config_manager = config_manager
        self.mqtt_manager = mqtt_manager
        
        # 创建子监控器
        self.system_monitor = SystemMonitor(config_manager)
        self.health_checker = SystemHealthChecker(config_manager)
        
        # 默认告警规则
        self._setup_default_alert_rules()
        
        # 默认健康检查
        self._setup_default_health_checks()
        
        # 如果配置了MQTT，添加MQTT通知渠道
        if mqtt_manager:
            self._setup_mqtt_notifications()
            
        import logging
        self.logger = logging.getLogger(f"{__name__}.EnhancedSystemMonitor")
        
    def _setup_default_alert_rules(self):
        """设置默认告警规则"""
        # CPU使用率告警
        self.system_monitor.add_alert_rule(
            'high_cpu_usage',
            'cpu_percent',
            80.0,
            '>',
            'warning'
        )
        
        # 内存使用率告警
        self.system_monitor.add_alert_rule(
            'high_memory_usage',
            'memory_percent',
            85.0,
            '>',
            'warning'
        )
        
        # 磁盘使用率告警
        self.system_monitor.add_alert_rule(
            'high_disk_usage',
            'disk_usage',
            90.0,
            '>',
            'critical'
        )
        
        # 温度过高告警
        self.system_monitor.add_alert_rule(
            'high_temperature',
            'temperature',
            70.0,
            '>',
            'warning'
        )
        
    def _setup_default_health_checks(self):
        """设置默认健康检查"""
        # 配置文件检查
        def check_config_files():
            config_path = self.config_manager.get_configuration_value('config_path')
            if config_path and os.path.exists(config_path):
                return {
                    'status': True,
                    'message': f'配置文件存在: {config_path}'
                }
            return {
                'status': False,
                'message': '配置文件不存在或路径未设置'
            }
            
        self.health_checker.register_health_check('config_files', check_config_files)
        
        # 磁盘空间检查
        def check_disk_space():
            disk_usage = psutil.disk_usage('/')
            free_percent = 100 - disk_usage.percent
            
            if free_percent > 10:  # 至少10%可用空间
                return {
                    'status': True,
                    'message': f'磁盘空间充足: {free_percent:.1f}% 可用'
                }
            else:
                return {
                    'status': False,
                    'message': f'磁盘空间不足: 仅 {free_percent:.1f}% 可用'
                }
                
        self.health_checker.register_health_check('disk_space', check_disk_space)
        
        # 内存使用检查
        def check_memory_usage():
            memory = psutil.virtual_memory()
            if memory.percent < 95:  # 内存使用率小于95%
                return {
                    'status': True,
                    'message': f'内存使用正常: {memory.percent:.1f}%'
                }
            else:
                return {
                    'status': False,
                    'message': f'内存使用过高: {memory.percent:.1f}%'
                }
                
        self.health_checker.register_health_check('memory_usage', check_memory_usage)
        
    def _setup_mqtt_notifications(self):
        """设置MQTT通知"""
        def mqtt_notification(alert_data):
            """MQTT通知回调"""
            try:
                # 发布到告警主题
                self.mqtt_manager.publish_alert(
                    alert_data['severity'],
                    alert_data['message']
                )
                
                # 同时发布到状态主题
                self.mqtt_manager.publish_system_status(
                    f"监控告警: {alert_data['message']}"
                )
                
            except Exception as e:
                self.logger.error(f"MQTT通知失败: {e}")
                
        self.system_monitor.add_notification_channel(mqtt_notification)
        
    def start_monitoring(self, interval: float = 5.0) -> bool:
        """启动监控"""
        try:
            # 启动系统监控
            self.system_monitor.start_system_monitoring(interval)
            
            # 运行初始健康检查
            self.health_checker.run_health_checks()
            
            self.logger.info("增强系统监控已启动")
            return True
            
        except Exception as e:
            self.logger.error(f"启动增强监控失败: {e}")
            return False
            
    def stop_monitoring(self) -> bool:
        """停止监控"""
        try:
            self.system_monitor.stop_system_monitoring()
            self.logger.info("增强系统监控已停止")
            return True
            
        except Exception as e:
            self.logger.error(f"停止增强监控失败: {e}")
            return False
            
    def get_comprehensive_system_status(self) -> Dict[str, Any]:
        """获取综合系统状态"""
        system_status = self.system_monitor.get_current_system_status()
        health_status = self.health_checker.run_health_checks()
        
        return {
            'system_metrics': system_status,
            'health_status': health_status,
            'overall_status': self._calculate_overall_status(system_status, health_status),
            'timestamp': time.time()
        }
        
    def _calculate_overall_status(self, system_status: Dict[str, Any], 
                                 health_status: Dict[str, Any]) -> str:
        """计算整体状态"""
        # 基于系统指标
        if system_status['metrics']['cpu_percent'] > 90:
            return 'critical'
        if system_status['metrics']['memory_percent'] > 90:
            return 'critical'
        if system_status['metrics']['disk_usage'] > 95:
            return 'critical'
            
        # 基于健康检查
        if health_status['overall_status'] == 'unhealthy':
            return 'critical'
        if health_status['overall_status'] == 'degraded':
            return 'warning'
            
        # 基于告警状态
        active_alerts = sum(1 for status in system_status['alert_status'].values() if status)
        if active_alerts > 3:
            return 'critical'
        if active_alerts > 0:
            return 'warning'
            
        return 'healthy'
        
    def publish_system_status_via_mqtt(self) -> bool:
        """通过MQTT发布系统状态"""
        if not self.mqtt_manager:
            return False
            
        try:
            status = self.get_comprehensive_system_status()
            
            # 发布到状态主题
            self.mqtt_manager.publish_system_status(
                f"系统状态: {status['overall_status']}"
            )
            
            # 发布详细状态到专用主题
            self.mqtt_manager.publish_message(
                'pi_sorter/system/detailed',
                status
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"MQTT发布系统状态失败: {e}")
            return False


# 测试类
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
            
    def test_start_stop_monitoring(self):
        """测试启动和停止监控"""
        # 启动监控
        result = self.system_monitor.start_system_monitoring(interval=0.1)
        self.assertTrue(result)
        self.assertTrue(self.system_monitor.is_monitoring)
        
        # 等待收集一些数据
        time.sleep(0.5)
        
        # 停止监控
        result = self.system_monitor.stop_system_monitoring()
        self.assertTrue(result)
        self.assertFalse(self.system_monitor.is_monitoring)
        
    def test_add_remove_alert_rule(self):
        """测试添加和移除告警规则"""
        # 添加告警规则
        result = self.system_monitor.add_alert_rule(
            'test_rule',
            'cpu_percent',
            50.0,
            '>',
            'warning'
        )
        self.assertTrue(result)
        self.assertIn('test_rule', self.system_monitor.alert_rules)
        
        # 验证规则配置
        rule = self.system_monitor.alert_rules['test_rule']
        self.assertEqual(rule['metric'], 'cpu_percent')
        self.assertEqual(rule['threshold'], 50.0)
        self.assertEqual(rule['operator'], '>')
        self.assertEqual(rule['severity'], 'warning')
        
        # 移除告警规则
        result = self.system_monitor.remove_alert_rule('test_rule')
        self.assertTrue(result)
        self.assertNotIn('test_rule', self.system_monitor.alert_rules)
        
    def test_notification_channel(self):
        """测试通知渠道"""
        notification_received = threading.Event()
        received_data = {}
        
        def test_channel(alert_data):
            received_data.update(alert_data)
            notification_received.set()
            
        # 添加通知渠道
        result = self.system_monitor.add_notification_channel(test_channel)
        self.assertTrue(result)
        
        # 手动触发告警
        test_alert = {
            'rule_name': 'test',
            'severity': 'warning',
            'message': '测试告警'
        }
        
        self.system_monitor._send_alert_notifications(test_alert)
        
        # 等待通知
        notification_received.wait(timeout=1.0)
        self.assertTrue(notification_received.is_set())
        self.assertEqual(received_data['message'], '测试告警')
        
    def test_get_current_system_status(self):
        """测试获取当前系统状态"""
        status = self.system_monitor.get_current_system_status()
        
        self.assertIn('metrics', status)
        self.assertIn('alert_rules', status)
        self.assertIn('alert_status', status)
        self.assertIn('is_monitoring', status)
        self.assertIn('history_size', status)
        
        # 验证指标格式
        metrics = status['metrics']
        self.assertIn('cpu_percent', metrics)
        self.assertIn('memory_percent', metrics)
        self.assertIn('disk_usage', metrics)
        
    def test_export_metrics_to_file(self):
        """测试导出指标到文件"""
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
            
        try:
            # 启动监控收集一些数据
            self.system_monitor.start_system_monitoring(interval=0.1)
            time.sleep(0.3)
            self.system_monitor.stop_system_monitoring()
            
            # 导出指标
            result = self.system_monitor.export_metrics_to_file(temp_file, 'json')
            self.assertTrue(result)
            
            # 验证文件内容
            with open(temp_file, 'r') as f:
                data = json.load(f)
                
            self.assertIn('current_metrics', data)
            self.assertIn('alert_rules', data)
            self.assertIn('metrics_history', data)
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


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
        if self.enhanced_monitor.system_monitor.is_monitoring:
            self.enhanced_monitor.stop_monitoring()
            
    def test_start_stop_monitoring(self):
        """测试启动和停止增强监控"""
        result = self.enhanced_monitor.start_monitoring(interval=0.1)
        self.assertTrue(result)
        self.assertTrue(self.enhanced_monitor.system_monitor.is_monitoring)
        
        result = self.enhanced_monitor.stop_monitoring()
        self.assertTrue(result)
        self.assertFalse(self.enhanced_monitor.system_monitor.is_monitoring)
        
    def test_get_comprehensive_system_status(self):
        """测试获取综合系统状态"""
        status = self.enhanced_monitor.get_comprehensive_system_status()
        
        self.assertIn('system_metrics', status)
        self.assertIn('health_status', status)
        self.assertIn('overall_status', status)
        self.assertIn('timestamp', status)
        
        # 验证整体状态
        self.assertIn(status['overall_status'], ['healthy', 'warning', 'critical'])
        
    def test_publish_system_status_via_mqtt(self):
        """测试通过MQTT发布系统状态"""
        # 模拟MQTT发布成功
        self.mqtt_manager.publish_system_status.return_value = True
        self.mqtt_manager.publish_message.return_value = True
        
        result = self.enhanced_monitor.publish_system_status_via_mqtt()
        self.assertTrue(result)
        
        # 验证MQTT调用
        self.mqtt_manager.publish_system_status.assert_called_once()
        self.mqtt_manager.publish_message.assert_called_once()
        
    def test_default_alert_rules(self):
        """测试默认告警规则"""
        alert_rules = self.enhanced_monitor.system_monitor.alert_rules
        
        # 验证存在默认规则
        self.assertIn('high_cpu_usage', alert_rules)
        self.assertIn('high_memory_usage', alert_rules)
        self.assertIn('high_disk_usage', alert_rules)
        self.assertIn('high_temperature', alert_rules)
        
    def test_default_health_checks(self):
        """测试默认健康检查"""
        health_checks = self.enhanced_monitor.health_checker.health_checks
        
        # 验证存在默认检查
        self.assertIn('config_files', health_checks)
        self.assertIn('disk_space', health_checks)
        self.assertIn('memory_usage', health_checks)
        
    def test_overall_status_calculation(self):
        """测试整体状态计算"""
        # 模拟高CPU使用率
        self.enhanced_monitor.system_monitor.metrics['cpu_percent'] = 95.0
        
        status = self.enhanced_monitor.get_comprehensive_system_status()
        
        # CPU使用率高应该导致critical状态
        self.assertEqual(status['overall_status'], 'critical')


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)