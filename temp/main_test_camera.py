#!/usr/bin/env python3
"""
芦笋分拣系统主程序 - 测试版本，只测试摄像头功能
Asparagus sorting system main program - test version, camera only
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


class AsparagusSystemTest:
    """芦笋分拣系统测试类，只测试摄像头功能"""
    
    def __init__(self):
        """初始化测试系统"""
        self.logger = logging.getLogger(__name__)
        self.system_running = True
        self.config_manager = ConfigManager()
        self.integrated_system: Optional[IntegratedSorterSystem] = None
        
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
                logging.FileHandler(log_dir / "asparagus_sorter_test.log"),
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
    
    def initialize(self) -> bool:
        """初始化系统"""
        try:
            # 加载配置
            config = self.config_manager.get_all_config()
            
            # 设置日志
            log_level = self.config_manager.get_log_level()
            self._setup_logging(log_level)
            
            self.logger.info("芦笋分拣系统测试版本启动 - 仅摄像头测试")
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
    
    def test_camera_capture(self) -> bool:
        """测试摄像头捕获功能"""
        try:
            self.logger.info("开始测试摄像头捕获功能...")
            
            # 获取摄像头管理器
            camera_manager = self.integrated_system.camera_manager
            if not camera_manager:
                self.logger.error("摄像头管理器不可用")
                return False
            
            # 获取主摄像头
            main_camera = camera_manager.get_camera('main')
            if not main_camera:
                self.logger.error("主摄像头不可用")
                return False
            
            # 捕获图像
            image_data = main_camera.capture_frame()
            if image_data is None:
                self.logger.error("图像捕获失败")
                return False
            
            # 保存测试图像
            import time
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"test_capture_{timestamp}.jpg"
            filepath = f"data/images/{filename}"
            
            if main_camera.save_frame(filepath, image_data):
                self.logger.info(f"✅ 摄像头捕获测试成功，图像已保存: {filepath}")
                return True
            else:
                self.logger.error("❌ 图像保存失败")
                return False
                
        except Exception as e:
            self.logger.error(f"摄像头测试失败: {str(e)}")
            return False
    
    def run_test(self) -> int:
        """运行测试"""
        try:
            if not self.integrated_system.start_processing():
                self.logger.error("启动分拣处理失败")
                return 1
            
            self.logger.info("分拣处理已启动")
            self.logger.info("开始摄像头测试...")
            
            # 等待系统稳定
            time.sleep(2)
            
            # 测试摄像头捕获
            if self.test_camera_capture():
                self.logger.info("摄像头测试通过")
            else:
                self.logger.error("摄像头测试失败")
                return 1
            
            # 等待用户中断或自动退出
            self.logger.info("测试完成，按Ctrl+C退出或等待10秒...")
            
            start_time = time.time()
            while self.system_running and (time.time() - start_time) < 10:
                try:
                    time.sleep(1)
                except KeyboardInterrupt:
                    self.logger.info("用户中断程序")
                    break
            
            return 0
            
        except Exception as e:
            self.logger.error(f"测试运行错误: {str(e)}")
            return 1
    
    def shutdown(self) -> None:
        """关闭系统"""
        try:
            if self.integrated_system:
                self.logger.info("停止分拣处理...")
                self.integrated_system.stop_processing()
                
                self.logger.info("关闭集成系统...")
                self.integrated_system.shutdown()
            
            self.logger.info("测试完成")
            
        except Exception as e:
            self.logger.error(f"关闭错误: {str(e)}")
        finally:
            self.logger.info("芦笋分拣系统测试关闭")


def main() -> int:
    """主函数"""
    system = AsparagusSystemTest()
    
    try:
        if not system.initialize():
            return 1
        
        return system.run_test()
        
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        logging.error(f"程序运行错误: {str(e)}")
        return 1
    finally:
        system.shutdown()


if __name__ == "__main__":
    sys.exit(main())