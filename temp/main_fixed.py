#!/usr/bin/env python3
"""
芦笋分拣系统主程序 - 修正版本，处理编码器问题
Asparagus sorting system main program - fixed version
"""

import logging
import sys
import os
import signal
import time
from pathlib import Path
from typing import Dict, Any, Optional

# 添加src目录到Python路径
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# 导入集成系统模块
from external.integrated_system import IntegratedSorterSystem
from external.config_manager import ConfigManager


class AsparagusSystemFixed:
    """芦笋分拣系统类 - 修正版本"""
    
    def __init__(self):
        """初始化系统"""
        self.logger = logging.getLogger(__name__)
        self.system_running = True
        self.config_manager = ConfigManager()
        self.integrated_system: Optional[IntegratedSorterSystem] = None
        self.main_led_pin = 16  # 主进程监控LED引脚
        self.encoder_led_pin = 27  # 编码器监控LED引脚
        
        # 注册信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum: int, frame: Any) -> None:
        """信号处理器"""
        self.logger.info(f"接收到信号 {signum}，准备关闭系统...")
        self.system_running = False
    
    def _setup_logging(self, log_level: str = "INFO") -> None:
        """设置日志配置"""
        log_dir = current_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        
        level = getattr(logging, log_level.upper(), logging.INFO)
        
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "asparagus_sorter.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def _check_environment(self) -> bool:
        """检查运行环境"""
        try:
            import numpy as np
            self.logger.info(f"NumPy版本: {np.__version__}")
        except ImportError:
            self.logger.error("NumPy未安装")
            return False
        
        try:
            import yaml
            self.logger.info("YAML支持可用")
        except ImportError:
            self.logger.warning("YAML未安装，将使用JSON配置")
        
        try:
            import paho.mqtt.client as mqtt
            self.logger.info("MQTT客户端可用")
        except ImportError:
            self.logger.warning("MQTT客户端未安装，MQTT功能将不可用")
        
        return True
    
    def _setup_led_monitoring(self) -> bool:
        """设置LED监控"""
        try:
            import RPi.GPIO as GPIO
            
            # 设置GPIO模式
            GPIO.setmode(GPIO.BCM)
            
            # 设置LED引脚为输出
            GPIO.setup(self.main_led_pin, GPIO.OUT)
            GPIO.setup(self.encoder_led_pin, GPIO.OUT)
            
            # 初始状态为关闭
            GPIO.output(self.main_led_pin, GPIO.LOW)
            GPIO.output(self.encoder_led_pin, GPIO.LOW)
            
            self.logger.info(f"LED监控初始化成功，主进程LED使用GPIO{self.main_led_pin}，编码器LED使用GPIO{self.encoder_led_pin}")
            return True
            
        except ImportError:
            self.logger.warning("RPi.GPIO未安装，LED监控功能将不可用")
            return False
        except Exception as e:
            self.logger.error(f"LED监控初始化失败: {str(e)}")
            return False
    
    def _monitor_main_process(self) -> None:
        """监控主进程状态"""
        try:
            import RPi.GPIO as GPIO
            
            # 主进程LED闪烁表示系统运行正常
            if self.system_running:
                GPIO.output(self.main_led_pin, GPIO.HIGH)
                time.sleep(0.5)
                GPIO.output(self.main_led_pin, GPIO.LOW)
                time.sleep(0.5)
            else:
                # 系统关闭时保持常亮
                GPIO.output(self.main_led_pin, GPIO.HIGH)
                
        except Exception:
            pass
    
    def initialize(self) -> bool:
        """初始化系统"""
        try:
            # 加载配置
            config = self.config_manager.get_all_config()
            
            # 设置日志
            log_level = self.config_manager.get_log_level()
            self._setup_logging(log_level)
            
            self.logger.info("芦笋分拣系统启动 - 集成版本")
            self.logger.info(f"系统版本: {config.get('system', {}).get('version', '1.0.0')}")
            
            # 验证配置
            validation = self.config_manager.validate_config()
            if not validation['valid']:
                self.logger.error("配置验证失败:")
                for error in validation['errors']:
                    self.logger.error(f"  - {error}")
                return False
            
            if validation['warnings']:
                self.logger.warning("配置警告:")
                for warning in validation['warnings']:
                    self.logger.warning(f"  - {warning}")
            
            # 检查环境
            if not self._check_environment():
                self.logger.error("环境检查失败")
                return False
            
            # 设置LED监控
            self._setup_led_monitoring()
            
            # 创建并初始化集成系统
            self.logger.info("初始化集成分拣系统...")
            self.integrated_system = IntegratedSorterSystem(config)
            
            if not self.integrated_system.initialize():
                self.logger.error("系统初始化失败")
                return False
            
            # 验证摄像头是否可用
            if not self.integrated_system.camera_available:
                self.logger.warning("摄像头不可用，系统将以模拟模式运行")
            else:
                self.logger.info("摄像头初始化成功，系统可以正常捕获图像")
            
            self.logger.info("系统初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"初始化错误: {str(e)}")
            return False
    
    def run(self) -> int:
        """运行主循环"""
        try:
            if not self.integrated_system.start_processing():
                self.logger.error("启动分拣处理失败")
                return 1
            
            self.logger.info("分拣处理已启动")
            self.logger.info("系统正在运行，按Ctrl+C退出...")
            
            # 主循环
            while self.system_running:
                try:
                    # 监控主进程状态
                    self._monitor_main_process()
                    
                    # 检查系统状态
                    if not self.integrated_system.is_running:
                        self.logger.warning("分拣处理已停止")
                        break
                    
                    # 短暂休眠，避免CPU占用过高
                    time.sleep(0.1)
                    
                except KeyboardInterrupt:
                    self.logger.info("用户中断程序")
                    break
                except Exception as e:
                    self.logger.error(f"主循环错误: {str(e)}")
                    time.sleep(1)
            
            return 0
            
        except Exception as e:
            self.logger.error(f"运行错误: {str(e)}")
            return 1
    
    def shutdown(self) -> None:
        """关闭系统"""
        try:
            self.logger.info("停止分拣处理...")
            if self.integrated_system:
                self.integrated_system.stop_processing()
                
                self.logger.info("关闭集成系统...")
                self.integrated_system.shutdown()
            
            # 清理GPIO
            try:
                import RPi.GPIO as GPIO
                GPIO.output(self.main_led_pin, GPIO.LOW)
                GPIO.output(self.encoder_led_pin, GPIO.LOW)
                GPIO.cleanup()
            except Exception:
                pass
            
            self.logger.info("系统关闭完成")
            
        except Exception as e:
            self.logger.error(f"关闭错误: {str(e)}")
        finally:
            self.logger.info("芦笋分拣系统关闭")


def main() -> int:
    """主函数"""
    system = AsparagusSystemFixed()
    
    try:
        if not system.initialize():
            return 1
        
        return system.run()
        
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        logging.error(f"程序运行错误: {str(e)}")
        return 1
    finally:
        system.shutdown()


if __name__ == "__main__":
    sys.exit(main())