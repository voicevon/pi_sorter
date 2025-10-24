#!/usr/bin/env python3
"""
Pi Sorter - 重构版本主程序
集成摄像头、MQTT通信、编码器控制和系统监控的完整分拣系统
"""

import os
import sys
import time
import signal
import logging
import argparse
from typing import Optional

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'external'))

from integrated_sorting_system import IntegratedSortingSystem
from config_manager_refactored import ConfigManager


class MainSystem:
    """主系统类"""
    
    def __init__(self):
        """初始化主系统"""
        self.sorting_system = None
        self.is_running = False
        self.shutdown_requested = False
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # 设置日志
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
    def _setup_logging(self):
        """设置日志系统"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('logs/main_system.log')
            ]
        )
        
    def _signal_handler(self, signum, frame):
        """信号处理"""
        self.logger.info(f"接收到信号 {signum}，开始优雅关闭")
        self.shutdown_requested = True
        
    def parse_arguments(self):
        """解析命令行参数"""
        parser = argparse.ArgumentParser(
            description='Pi Sorter - 芦笋分拣系统',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
示例:
    python main_refactored.py                    # 使用默认配置
    python main_refactored.py -c custom.yaml     # 使用自定义配置
    python main_refactored.py --debug           # 启用调试模式
    python main_refactored.py --test            # 运行测试模式
            """
        )
        
        parser.add_argument(
            '-c', '--config',
            type=str,
            default='config/integrated_config.yaml',
            help='配置文件路径 (默认: config/integrated_config.yaml)'
        )
        
        parser.add_argument(
            '--debug',
            action='store_true',
            help='启用调试模式'
        )
        
        parser.add_argument(
            '--test',
            action='store_true',
            help='运行测试模式，不启动实际系统'
        )
        
        parser.add_argument(
            '--no-camera',
            action='store_true',
            help='禁用摄像头功能'
        )
        
        parser.add_argument(
            '--no-mqtt',
            action='store_true',
            help='禁用MQTT通信'
        )
        
        parser.add_argument(
            '--no-encoder',
            action='store_true',
            help='禁用编码器功能'
        )
        
        parser.add_argument(
            '--no-monitor',
            action='store_true',
            help='禁用系统监控'
        )
        
        return parser.parse_args()
        
    def initialize_system(self, args) -> bool:
        """初始化系统"""
        try:
            self.logger.info("开始初始化主系统")
            
            # 创建配置管理器以修改配置
            config_manager = ConfigManager(args.config)
            if not config_manager.load_configuration():
                self.logger.error("配置文件加载失败")
                return False
                
            # 根据命令行参数修改配置
            if args.no_camera:
                config_manager.update_configuration_value(['camera', 'enabled'], False)
                self.logger.info("摄像头功能已禁用")
                
            if args.no_mqtt:
                config_manager.update_configuration_value(['mqtt', 'enabled'], False)
                self.logger.info("MQTT通信已禁用")
                
            if args.no_encoder:
                config_manager.update_configuration_value(['encoder', 'enabled'], False)
                self.logger.info("编码器功能已禁用")
                
            if args.no_monitor:
                config_manager.update_configuration_value(['monitor', 'enabled'], False)
                self.logger.info("系统监控已禁用")
                
            # 保存修改后的配置
            config_manager.save_configuration()
            
            # 创建分拣系统
            self.sorting_system = IntegratedSortingSystem(args.config)
            
            # 初始化系统
            if not self.sorting_system.initialize_system():
                self.logger.error("分拣系统初始化失败")
                return False
                
            self.logger.info("主系统初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"主系统初始化失败: {e}")
            return False
            
    def run_system(self) -> bool:
        """运行系统"""
        try:
            self.logger.info("开始运行系统")
            
            if not self.sorting_system.start_system_operation():
                self.logger.error("系统运行启动失败")
                return False
                
            self.is_running = True
            
            # 主循环
            while self.is_running and not self.shutdown_requested:
                try:
                    # 定期发布系统状态
                    if hasattr(self.sorting_system, 'mqtt_manager') and self.sorting_system.mqtt_manager:
                        self.sorting_system.mqtt_manager.publish_system_status("系统运行正常")
                        
                    # 检查系统健康状态
                    self._check_system_health()
                    
                    time.sleep(30)  # 每30秒检查一次
                    
                except KeyboardInterrupt:
                    self.logger.info("用户中断，开始关闭系统")
                    break
                except Exception as e:
                    self.logger.error(f"主循环错误: {e}")
                    time.sleep(5)
                    
            self.logger.info("主循环结束")
            return True
            
        except Exception as e:
            self.logger.error(f"系统运行失败: {e}")
            return False
            
    def _check_system_health(self):
        """检查系统健康状态"""
        try:
            if hasattr(self.sorting_system, 'system_monitor'):
                status = self.sorting_system.system_monitor.get_comprehensive_system_status()
                
                if status['overall_status'] == 'critical':
                    self.logger.warning("系统状态严重，需要关注")
                elif status['overall_status'] == 'warning':
                    self.logger.info("系统状态警告")
                else:
                    self.logger.debug("系统状态健康")
                    
        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
            
    def shutdown_system(self):
        """关闭系统"""
        try:
            self.logger.info("开始关闭系统")
            
            self.is_running = False
            
            # 停止分拣系统
            if self.sorting_system:
                self.sorting_system.stop_system_operation()
                
            # 清理资源
            if self.sorting_system:
                self.sorting_system.cleanup_system_resources()
                
            self.logger.info("系统已安全关闭")
            
        except Exception as e:
            self.logger.error(f"系统关闭失败: {e}")
            
    def run_test_mode(self):
        """运行测试模式"""
        try:
            self.logger.info("运行测试模式")
            
            # 运行单元测试
            import unittest
            from test_refactored_modules import TestSystemMonitor
            
            # 创建测试套件
            suite = unittest.TestLoader().loadTestsFromTestCase(TestSystemMonitor)
            
            # 运行测试
            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(suite)
            
            if result.wasSuccessful():
                self.logger.info("所有测试通过")
                return True
            else:
                self.logger.error(f"测试失败: {len(result.failures)} 失败, {len(result.errors)} 错误")
                return False
                
        except Exception as e:
            self.logger.error(f"测试模式运行失败: {e}")
            return False
            
    def main(self):
        """主函数"""
        try:
            self.logger.info("Pi Sorter 重构版本启动")
            
            # 解析命令行参数
            args = self.parse_arguments()
            
            # 设置调试模式
            if args.debug:
                logging.getLogger().setLevel(logging.DEBUG)
                self.logger.info("调试模式已启用")
                
            # 运行测试模式
            if args.test:
                success = self.run_test_mode()
                return 0 if success else 1
                
            # 初始化系统
            if not self.initialize_system(args):
                self.logger.error("系统初始化失败")
                return 1
                
            # 运行系统
            if not self.run_system():
                self.logger.error("系统运行失败")
                return 1
                
            # 正常关闭
            self.shutdown_system()
            
            self.logger.info("Pi Sorter 正常退出")
            return 0
            
        except KeyboardInterrupt:
            self.logger.info("用户中断")
            self.shutdown_system()
            return 0
            
        except Exception as e:
            self.logger.error(f"主程序异常: {e}")
            self.shutdown_system()
            return 1


def main():
    """主入口函数"""
    main_system = MainSystem()
    exit_code = main_system.main()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()