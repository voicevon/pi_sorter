#!/usr/bin/env python3
"""
基于picamera2的CSI摄像头模块
CSI Camera module based on picamera2
"""

import numpy as np
import threading
import time
import logging
from datetime import datetime
from typing import Optional, Tuple, Callable, Dict, Any
from pathlib import Path

try:
    from picamera2 import Picamera2
    from libcamera import controls
    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False
    print("警告: picamera2库未安装，请运行: sudo apt install python3-picamera2")

class CSICamera:
    """
    基于picamera2的CSI摄像头控制类
    CSI Camera control class based on picamera2
    """
    
    def __init__(self, camera_num: int = 0, resolution: Tuple[int, int] = (1280, 1024)):
        """
        初始化CSI摄像头
        
        Args:
            camera_num: 摄像头编号 (通常为0)
            resolution: 分辨率 (width, height)
        """
        if not PICAMERA2_AVAILABLE:
            raise ImportError("picamera2库未安装")
            
        self.camera_num = camera_num
        self.resolution = resolution
        self.picam2 = None
        self.is_running = False
        self.frame_callback = None
        self.capture_thread = None
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        
        # 摄像头参数
        self.brightness = 0.0  # picamera2使用-1.0到1.0
        self.contrast = 1.0    # picamera2使用0.0到2.0
        self.saturation = 1.0  # picamera2使用0.0到2.0
        self.exposure_time = None  # 自动曝光
        
        self.logger = logging.getLogger(__name__)
        
    def initialize(self) -> bool:
        """
        初始化CSI摄像头连接
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 创建Picamera2实例
            self.picam2 = Picamera2(self.camera_num)
            
            # 配置摄像头
            config = self.picam2.create_still_configuration(
                main={"size": self.resolution, "format": "RGB888"}
            )
            self.picam2.configure(config)
            
            # 启动摄像头
            self.picam2.start()
            
            # 等待摄像头稳定
            time.sleep(2)
            
            # 设置初始参数
            self._apply_camera_settings()
            
            self.logger.info(f"CSI摄像头初始化成功: {self.resolution[0]}x{self.resolution[1]}")
            return True
            
        except Exception as e:
            self.logger.error(f"CSI摄像头初始化失败: {str(e)}")
            if self.picam2:
                try:
                    self.picam2.close()
                except:
                    pass
                self.picam2 = None
            return False
    
    def _apply_camera_settings(self):
        """应用摄像头设置"""
        if not self.picam2:
            return
            
        try:
            controls_dict = {}
            
            # 设置亮度（使用 Brightness 控制）
            if self.brightness != 0.0:
                controls_dict["Brightness"] = float(self.brightness)
                
            # 设置对比度（使用 Contrast 控制）
            if self.contrast != 1.0:
                controls_dict["Contrast"] = float(self.contrast)
                
            # 设置饱和度（使用 Saturation 控制）
            if self.saturation != 1.0:
                controls_dict["Saturation"] = float(self.saturation)
                
            # 设置曝光时间
            if self.exposure_time:
                controls_dict["ExposureTime"] = int(self.exposure_time)
            else:
                # 自动曝光
                controls_dict["AeEnable"] = True
                
            if controls_dict:
                self.picam2.set_controls(controls_dict)
                
            self.logger.info("CSI摄像头参数设置完成")
            
        except Exception as e:
            self.logger.error(f"设置CSI摄像头参数失败: {str(e)}")
    
    def set_parameters(self, brightness: float = None, contrast: float = None, 
                      saturation: float = None, exposure_time: int = None):
        """
        设置摄像头参数
        
        Args:
            brightness: 亮度 (-1.0 到 1.0)
            contrast: 对比度 (0.0 到 2.0)
            saturation: 饱和度 (0.0 到 2.0)
            exposure_time: 曝光时间 (微秒，None为自动)
        """
        if not self.picam2:
            self.logger.error("摄像头未初始化")
            return
            
        try:
            if brightness is not None:
                self.brightness = max(-1.0, min(1.0, brightness))
            if contrast is not None:
                self.contrast = max(0.0, min(2.0, contrast))
            if saturation is not None:
                self.saturation = max(0.0, min(2.0, saturation))
            if exposure_time is not None:
                self.exposure_time = exposure_time
                
            self._apply_camera_settings()
            
        except Exception as e:
            self.logger.error(f"设置摄像头参数失败: {str(e)}")
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """
        捕获单帧图像
        
        Returns:
            np.ndarray: 图像数据，失败返回None
        """
        if not self.picam2:
            self.logger.error("摄像头未初始化")
            return None
            
        try:
            # 捕获图像
            frame = self.picam2.capture_array()
            
            if frame is not None:
                with self.frame_lock:
                    self.latest_frame = frame.copy()
                return frame
            else:
                self.logger.warning("捕获的图像为空")
                return None
                
        except Exception as e:
            self.logger.error(f"捕获图像失败: {str(e)}")
            return None
    
    def start_continuous_capture(self, callback: Callable[[np.ndarray], None] = None):
        """
        开始连续捕获
        
        Args:
            callback: 帧回调函数
        """
        if self.is_running:
            self.logger.warning("连续捕获已在运行")
            return
            
        self.frame_callback = callback
        self.is_running = True
        self.capture_thread = threading.Thread(target=self._capture_loop)
        self.capture_thread.daemon = True
        self.capture_thread.start()
        self.logger.info("开始连续捕获")
    
    def stop_continuous_capture(self):
        """停止连续捕获"""
        if not self.is_running:
            return
            
        self.is_running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=5)
        self.logger.info("停止连续捕获")
    
    def _capture_loop(self):
        """捕获循环"""
        while self.is_running:
            try:
                frame = self.capture_frame()
                if frame is not None and self.frame_callback:
                    self.frame_callback(frame)
                time.sleep(0.033)  # 约30fps
            except Exception as e:
                self.logger.error(f"捕获循环错误: {str(e)}")
                time.sleep(1)
    
    def get_latest_frame(self) -> Optional[np.ndarray]:
        """
        获取最新帧
        
        Returns:
            np.ndarray: 最新图像，无则返回None
        """
        with self.frame_lock:
            return self.latest_frame.copy() if self.latest_frame is not None else None
    
    def save_frame(self, filename: str, frame: np.ndarray = None) -> bool:
        """
        保存图像到文件
        
        Args:
            filename: 文件名
            frame: 图像数据，None则使用最新帧
            
        Returns:
            bool: 保存是否成功
        """
        try:
            if frame is None:
                frame = self.get_latest_frame()
                
            if frame is None:
                self.logger.error("没有可保存的图像")
                return False
                
            # 确保目录存在
            Path(filename).parent.mkdir(parents=True, exist_ok=True)
            
            # 使用picamera2的方式保存
            if self.picam2:
                # 直接使用picamera2保存
                self.picam2.capture_file(filename)
                self.logger.info(f"图像已保存: {filename}")
                return True
            else:
                # 备用方案：使用PIL保存
                from PIL import Image
                img = Image.fromarray(frame)
                img.save(filename)
                self.logger.info(f"图像已保存: {filename}")
                return True
                
        except Exception as e:
            self.logger.error(f"保存图像失败: {str(e)}")
            return False
    
    def get_camera_info(self) -> dict:
        """
        获取摄像头信息
        
        Returns:
            dict: 摄像头信息
        """
        try:
            if not self.picam2:
                return {'error': '摄像头未初始化'}
                
            # 获取摄像头属性（不需要停止摄像头）
            info = {
                'camera_num': self.camera_num,
                'resolution': self.resolution,
                'brightness': self.brightness,
                'contrast': self.contrast,
                'saturation': self.saturation,
                'exposure_time': self.exposure_time,
                'is_running': self.is_running,
                'library': 'picamera2'
            }
            
            # 尝试获取其他属性（如果可用）
            try:
                info['model'] = self.picam2.camera_properties.get('Model', 'Unknown')
            except:
                info['model'] = 'Unknown'
                
            try:
                info['sensor_modes_count'] = len(self.picam2.sensor_modes) if self.picam2.sensor_modes else 0
            except:
                info['sensor_modes_count'] = 0
            
            return info
            
        except Exception as e:
            self.logger.error(f"获取摄像头信息失败: {str(e)}")
            return {'error': str(e)}
    
    def release(self):
        """释放摄像头资源"""
        try:
            # 停止连续捕获
            self.stop_continuous_capture()
            
            # 释放摄像头
            if self.picam2:
                self.picam2.stop()
                self.picam2.close()
                self.picam2 = None
                
            # 清理状态
            self.is_running = False
            with self.frame_lock:
                self.latest_frame = None
                
            self.logger.info("CSI摄像头资源已释放")
            
        except Exception as e:
            self.logger.error(f"释放摄像头资源时发生错误: {str(e)}")
    
    def __enter__(self):
        """上下文管理器入口"""
        if not self.initialize():
            raise RuntimeError("摄像头初始化失败")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.release()


class CSICameraManager:
    """
    CSI摄像头管理器
    CSI Camera manager
    """
    
    def __init__(self):
        self.cameras = {}
        self.logger = logging.getLogger(__name__)
    
    def add_camera(self, name: str, camera_num: int = 0,
                   resolution: Tuple[int, int] = (1280, 1024)) -> bool:
        """
        添加摄像头
        
        Args:
            name: 摄像头名称
            camera_num: 摄像头编号
            resolution: 分辨率
            
        Returns:
            bool: 添加是否成功
        """
        try:
            camera = CSICamera(camera_num, resolution)
            
            if camera.initialize():
                self.cameras[name] = camera
                self.logger.info(f"CSI摄像头 '{name}' 添加成功")
                return True
            else:
                self.logger.error(f"CSI摄像头 '{name}' 初始化失败")
                return False
                
        except Exception as e:
            self.logger.error(f"添加CSI摄像头 '{name}' 时发生错误: {str(e)}")
            return False
    
    def get_camera(self, name: str) -> Optional[CSICamera]:
        """
        获取摄像头实例
        
        Args:
            name: 摄像头名称
            
        Returns:
            CSICamera: 摄像头实例，不存在返回None
        """
        return self.cameras.get(name)
    
    def remove_camera(self, name: str) -> bool:
        """
        移除摄像头
        
        Args:
            name: 摄像头名称
            
        Returns:
            bool: 移除是否成功
        """
        try:
            if name in self.cameras:
                # 释放摄像头资源
                self.cameras[name].release()
                del self.cameras[name]
                self.logger.info(f"CSI摄像头 '{name}' 已移除")
                return True
        except Exception as e:
            self.logger.error(f"移除CSI摄像头 '{name}' 时发生错误: {str(e)}")
            return False
        
        self.logger.warning(f"CSI摄像头 '{name}' 不存在")
        return False
    
    def list_cameras(self) -> list:
        """
        列出所有摄像头
        
        Returns:
            list: 摄像头名称列表
        """
        return list(self.cameras.keys())
    
    def release_all(self):
        """释放所有摄像头资源"""
        for name in list(self.cameras.keys()):
            self.remove_camera(name)
        
        self.logger.info("所有CSI摄像头资源已释放")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 测试CSI摄像头功能
    print("测试CSI摄像头功能...")
    
    try:
        # 测试单个摄像头
        with CSICamera(camera_num=0, resolution=(1280, 1024)) as camera:
            print("CSI摄像头初始化成功")
            
            # 捕获图像
            frame = camera.capture_frame()
            if frame is not None:
                print(f"捕获图像成功: {frame.shape}")
                
                # 保存测试图像
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"csi_test_capture_{timestamp}.jpg"
                camera.save_frame(filename, frame)
                
            # 获取摄像头信息
            info = camera.get_camera_info()
            print(f"CSI摄像头信息: {info}")
            
    except Exception as e:
        print(f"测试失败: {str(e)}")
        print("请确保:")
        print("1. CSI摄像头已正确连接")
        print("2. 已安装picamera2: sudo apt install python3-picamera2")
        print("3. 摄像头硬件正常工作")