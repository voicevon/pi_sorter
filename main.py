#!/usr/bin/env python3
"""
芦笋分拣系统主程序 - 集成摄像头和MQTT功能
Asparagus sorting system main program - integrated with camera and MQTT
"""

import logging
import sys
import os
import signal
import time
from pathlib import Path
from typing import Dict, Any, Optional
import RPi.GPIO as GPIO

# 添加src目录到Python路径
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# 导入集成系统模块
from external.integrated_system import IntegratedSorterSystem
from external.config_manager import ConfigManager
from external.encoder_module_lgpio import RotaryEncoderLGPIO as RotaryEncoder


class AsparagusSystem:
    """芦笋分拣系统主类，负责管理整个系统的生命周期"""
    
    def __init__(self):
        """初始化芦笋分拣系统"""
        self.logger = logging.getLogger(__name__)
        self.system_running = True
        self.config_manager = ConfigManager()
        self.integrated_system: Optional[IntegratedSorterSystem] = None
        self.encoder: Optional[RotaryEncoder] = None
        
        # LED监控引脚配置（BCM编码）
        self.LED_PIN = 16  # GPIO16 - 主进程LED监控
        self.ENCODER_LED_PIN = 12  # GPIO12 - 编码器LED监控
        self.led_state = False
        self.last_led_toggle = time.time()
        self.encoder_led_state = False
        self.encoder_zero_triggered = False
        self.encoder_count_since_zero = 0
        
        # 注册信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _trigger_camera(self):
        """编码器触发位置的相机回调函数"""
        if self.integrated_system:
            self.logger.info("编码器触发位置到达，开始拍摄")
            self.integrated_system.capture_and_process()
    
    def _setup_logging(self, log_level: str = "INFO") -> None:
        """设置日志配置
        
        Args:
            log_level: 日志级别，默认为 "INFO"
        """
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
        """检查运行环境
        
        Returns:
            bool: 环境检查是否通过
        """
        # 不再使用OpenCV，仅使用picamera2
        
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
    
    def _signal_handler(self, signum: int, frame: Any) -> None:
        """信号处理器
        
        Args:
            signum: 信号编号
            frame: 当前栈帧
        """
        self.logger.info(f"接收到信号 {signum}，准备关闭系统...")
        self.system_running = False
    
    def _process_status(self, status: Dict[str, Any]) -> None:
        """处理系统状态信息
        
        Args:
            status: 系统状态字典
        """
        stats = status.get('statistics', {})
        if stats.get('total_processed', 0) % 10 == 0:
            self.logger.info(
                f"处理统计: 总计={stats.get('total_processed', 0)}, "
                f"A级={stats.get('grade_a_count', 0)}, "
                f"B级={stats.get('grade_b_count', 0)}, "
                f"C级={stats.get('grade_c_count', 0)}"
            )
    
    def initialize(self) -> bool:
        """初始化系统
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 加载配置
            config = self.config_manager.get_all_config()
            
            # 设置日志
            log_level = self.config_manager.get_log_level()
            self._setup_logging(log_level)
            
            self.logger.info("芦笋分拣系统启动 - 集成版本")
            self.logger.info(f"系统版本: {config.get('system', {}).get('version', '1.0.0')}")
            
            # 初始化LED
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(self.LED_PIN, GPIO.OUT)
                GPIO.setup(self.ENCODER_LED_PIN, GPIO.OUT)
                GPIO.output(self.LED_PIN, GPIO.LOW)
                GPIO.output(self.ENCODER_LED_PIN, GPIO.LOW)
                self.logger.info(f"LED监控初始化成功，主进程LED使用GPIO{self.LED_PIN}，编码器LED使用GPIO{self.ENCODER_LED_PIN}")
            except Exception as e:
                self.logger.error(f"LED监控初始化失败: {str(e)}")
                # LED初始化失败不影响系统运行，只记录错误
            
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
            
            # 初始化编码器
            try:
                self.logger.info("初始化编码器...")
                # GPIO引脚配置（BCM编码）
                PIN_A = 15   # GPIO15 - 编码器A相
                PIN_B = 18   # GPIO18 - 编码器B相  
                PIN_Z = 14   # GPIO14 - 编码器Z相（归零信号）
                
                self.encoder = RotaryEncoder(PIN_A, PIN_B, PIN_Z)
                # 设置触发位置和回调函数
                trigger_position = config.get('encoder', {}).get('trigger_position', 150)
                self.encoder.set_trigger(trigger_position, self._trigger_camera)
                self.logger.info(f"编码器初始化成功，触发位置设置为: {trigger_position}")
            except Exception as e:
                self.logger.error(f"编码器初始化失败: {str(e)}")
                return False
            
            self.logger.info("系统初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"初始化错误: {str(e)}")
            return False
    
    def run(self) -> int:
        """运行系统主循环
        
        Returns:
            int: 退出码，0表示正常退出，1表示异常退出
        """
        try:
            if not self.integrated_system.start_processing():
                self.logger.error("启动分拣处理失败")
                return 1
            
            # 启动编码器
            if self.encoder:
                self.encoder.start()
                self.logger.info("编码器开始运行")
            
            self.logger.info("分拣处理已启动")
            self.logger.info("进入主循环...")
            
            # 初始化LED状态
            self.led_state = False
            self.last_led_toggle = time.time()
            self.encoder_led_state = False
            self.encoder_zero_triggered = False
            self.encoder_count_since_zero = 0
            
            while self.system_running:
                try:
                    status = self.integrated_system.get_system_status()
                    self._process_status(status)
                    
                    if not status.get('system', {}).get('running', False):
                        self.logger.warning("系统运行状态异常")
                        break
                    
                    # 记录编码器位置
                    if self.encoder:
                        position = self.encoder.get_position()
                        if position % 50 == 0:  # 每50个脉冲记录一次位置
                            self.logger.info(f"当前编码器位置: {position}")
                    
                    # LED监控：每秒钟切换一次状态
                    current_time = time.time()
                    if current_time - self.last_led_toggle >= 1.0:
                        self.led_state = not self.led_state
                        try:
                            GPIO.output(self.LED_PIN, GPIO.HIGH if self.led_state else GPIO.LOW)
                        except Exception as e:
                            self.logger.error(f"主进程LED控制失败: {str(e)}")
                        self.last_led_toggle = current_time
                    
                    # 编码器状态监控LED
                    if self.encoder:
                        position = self.encoder.get_position()
                        
                        # 检测编码器归零信号（通过位置变化判断）
                        if position == 0 and not self.encoder_zero_triggered:
                            self.encoder_zero_triggered = True
                            self.encoder_count_since_zero = 0
                            self.encoder_led_state = True
                            try:
                                GPIO.output(self.ENCODER_LED_PIN, GPIO.HIGH)
                                self.logger.info("编码器Z相触发，LED亮起")
                            except Exception as e:
                                self.logger.error(f"编码器LED控制失败: {str(e)}")
                        
                        # 计数并控制LED
                        if self.encoder_zero_triggered:
                            self.encoder_count_since_zero += 1
                            if self.encoder_count_since_zero >= 5:
                                self.encoder_led_state = False
                                self.encoder_zero_triggered = False
                                try:
                                    GPIO.output(self.ENCODER_LED_PIN, GPIO.LOW)
                                    self.logger.info("编码器计数达到5，LED关闭")
                                except Exception as e:
                                    self.logger.error(f"编码器LED控制失败: {str(e)}")
                    
                    time.sleep(0.1)  # 缩短睡眠时间以提高编码器响应性
                    
                except KeyboardInterrupt:
                    self.logger.info("用户中断程序")
                    break
                except Exception as e:
                    self.logger.error(f"主循环错误: {str(e)}")
                    time.sleep(1.0)
            
            # 清理编码器资源
            if self.encoder:
                self.encoder.cleanup()
                self.logger.info("编码器资源已清理")
            
            return 0
            
        except Exception as e:
            self.logger.error(f"运行错误: {str(e)}")
            return 1
    
    def shutdown(self) -> None:
        """关闭系统"""
        try:
            if self.integrated_system:
                self.logger.info("停止分拣处理...")
                self.integrated_system.stop_processing()
                
                self.logger.info("关闭集成系统...")
                self.integrated_system.shutdown()
            
            # 关闭LED
            try:
                GPIO.output(self.LED_PIN, GPIO.LOW)
                GPIO.output(self.ENCODER_LED_PIN, GPIO.LOW)
                GPIO.cleanup([self.LED_PIN, self.ENCODER_LED_PIN])
                self.logger.info("所有LED监控已关闭")
            except Exception as e:
                self.logger.error(f"LED清理失败: {str(e)}")
            
            self.logger.info("系统运行完成")
            
        except Exception as e:
            self.logger.error(f"关闭错误: {str(e)}")
        finally:
            self.logger.info("芦笋分拣系统关闭")


def main() -> int:
    """主函数
    
    Returns:
        int: 退出码，0表示正常退出，1表示异常退出
    """
    system = AsparagusSystem()
    
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