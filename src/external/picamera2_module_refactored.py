#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSI摄像头模块 - 重构版本
提供统一的摄像头API接口，支持图像捕获和参数设置

重构改进：
1. 统一API命名规范：所有方法使用动词开头，如capture_image()、start_capture()等
2. 增强错误处理和日志记录
3. 完善文档字符串
4. 统一参数顺序和返回值格式
"""

import threading
import time
import logging
from pathlib import Path
from typing import Optional, Tuple, Callable, Dict, Any, Union
import numpy as np
from datetime import datetime

try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False
    logging.warning("Picamera2库不可用，摄像头功能将受限")


class CSICamera:
    """
    CSI摄像头类
    提供统一的摄像头控制和图像捕获接口
    
    主要功能：
    - 摄像头初始化和参数配置
    - 单张图像捕获
    - 连续图像捕获
    - 图像保存
    - 摄像头信息管理
    """
    
    def __init__(self, camera_id: int = 0, resolution: Tuple[int, int] = (1280, 1024)):
        """
        初始化CSI摄像头
        
        Args:
            camera_id: 摄像头ID，默认为0
            resolution: 图像分辨率，默认为(1280, 1024)
        """
        self.camera_id = camera_id
        self.resolution = resolution
        self.picam2: Optional[Picamera2] = None
        self.is_running = False
        self.is_capturing = False
        
        # 图像参数
        self.brightness = 0.5
        self.contrast = 0.5
        self.saturation = 0.5
        self.exposure_time = -1
        
        # 线程相关
        self.capture_thread: Optional[threading.Thread] = None
        self.frame_lock = threading.Lock()
        self.latest_frame: Optional[np.ndarray] = None
        self.frame_callback: Optional[Callable[[np.ndarray], None]] = None
        
        # 日志
        self.logger = logging.getLogger(f"{__name__}.CSICamera")
        
        self.logger.info(f"CSI摄像头初始化完成: camera_id={camera_id}, resolution={resolution}")
    
    def initialize(self) -> bool:
        """
        初始化摄像头硬件
        
        Returns:
            bool: 初始化成功返回True，失败返回False
        """
        try:
            if not PICAMERA2_AVAILABLE:
                self.logger.error("Picamera2库不可用，无法初始化摄像头")
                return False
                
            self.logger.info(f"开始初始化CSI摄像头: {self.camera_id}")
            
            # 创建Picamera2实例
            self.picam2 = Picamera2(camera_num=self.camera_id)
            
            # 配置摄像头
            camera_config = self.picam2.create_still_configuration(
                main={"size": self.resolution, "format": "RGB888"}
            )
            self.picam2.configure(camera_config)
            
            # 启动摄像头
            self.picam2.start()
            
            # 应用参数设置
            self._apply_camera_parameters()
            
            self.is_running = True
            self.logger.info(f"CSI摄像头初始化成功: {self.resolution}")
            return True
            
        except Exception as e:
            self.logger.error(f"CSI摄像头初始化失败: {str(e)}")
            self.is_running = False
            return False
    
    def release_camera(self) -> bool:
        """
        释放摄像头资源
        
        Returns:
            bool: 释放成功返回True
        """
        try:
            self.logger.info("开始释放CSI摄像头资源")
            
            # 停止连续捕获
            self.stop_continuous_capture()
            
            # 停止摄像头
            if self.picam2:
                self.picam2.stop()
                self.picam2.close()
                self.picam2 = None
                
            # 清理状态
            self.is_running = False
            self.is_capturing = False
            with self.frame_lock:
                self.latest_frame = None
                
            self.logger.info("CSI摄像头资源释放完成")
            return True
            
        except Exception as e:
            self.logger.error(f"释放摄像头资源失败: {str(e)}")
            return False
    
    def capture_image(self, save_path: Optional[str] = None) -> Optional[np.ndarray]:
        """
        捕获单张图像
        
        Args:
            save_path: 保存路径，为None时不保存
            
        Returns:
            np.ndarray: 捕获的图像数据，失败返回None
        """
        try:
            if not self.is_running or not self.picam2:
                self.logger.error("摄像头未初始化，无法捕获图像")
                return None
                
            self.logger.debug("开始捕获图像")
            
            # 捕获图像
            frame = self.picam2.capture_array()
            
            if frame is None:
                self.logger.error("图像捕获失败：返回None")
                return None
                
            # 更新最新帧
            with self.frame_lock:
                self.latest_frame = frame.copy()
                
            # 保存图像（如果指定了路径）
            if save_path:
                self.save_image(save_path, frame)
                
            self.logger.debug(f"图像捕获成功: shape={frame.shape}")
            return frame
            
        except Exception as e:
            self.logger.error(f"图像捕获失败: {str(e)}")
            return None
    
    def start_continuous_capture(self, callback: Optional[Callable[[np.ndarray], None]] = None) -> bool:
        """
        开始连续图像捕获
        
        Args:
            callback: 帧回调函数，每次捕获到新图像时调用
            
        Returns:
            bool: 启动成功返回True
        """
        try:
            if self.is_capturing:
                self.logger.warning("连续捕获已在运行")
                return True
                
            if not self.is_running:
                self.logger.error("摄像头未初始化")
                return False
                
            self.logger.info("开始连续图像捕获")
            
            # 设置回调函数
            self.frame_callback = callback
            self.is_capturing = True
            
            # 启动捕获线程
            self.capture_thread = threading.Thread(target=self._capture_loop, name="CameraCapture")
            self.capture_thread.daemon = True
            self.capture_thread.start()
            
            self.logger.info("连续图像捕获已启动")
            return True
            
        except Exception as e:
            self.logger.error(f"启动连续捕获失败: {str(e)}")
            self.is_capturing = False
            return False
    
    def stop_continuous_capture(self) -> bool:
        """
        停止连续图像捕获
        
        Returns:
            bool: 停止成功返回True
        """
        try:
            if not self.is_capturing:
                self.logger.debug("连续捕获未在运行")
                return True
                
            self.logger.info("停止连续图像捕获")
            
            # 停止捕获循环
            self.is_capturing = False
            
            # 等待线程结束
            if self.capture_thread and self.capture_thread.is_alive():
                self.capture_thread.join(timeout=5.0)
                
            self.logger.info("连续图像捕获已停止")
            return True
            
        except Exception as e:
            self.logger.error(f"停止连续捕获失败: {str(e)}")
            return False
    
    def save_image(self, file_path: str, image: Optional[np.ndarray] = None) -> bool:
        """
        保存图像到文件
        
        Args:
            file_path: 文件保存路径
            image: 图像数据，为None时使用最新帧
            
        Returns:
            bool: 保存成功返回True
        """
        try:
            # 获取图像数据
            if image is None:
                image = self.get_latest_frame()
                
            if image is None:
                self.logger.error("没有可保存的图像")
                return False
                
            # 确保目录存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 保存图像
            if self.picam2:
                # 使用picamera2直接保存
                self.picam2.capture_file(file_path)
            else:
                # 备用方案：使用OpenCV保存
                import cv2
                cv2.imwrite(file_path, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
                
            self.logger.info(f"图像已保存: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存图像失败: {str(e)}")
            return False
    
    def get_latest_frame(self) -> Optional[np.ndarray]:
        """
        获取最新捕获的图像帧
        
        Returns:
            np.ndarray: 最新图像帧，无则返回None
        """
        with self.frame_lock:
            return self.latest_frame.copy() if self.latest_frame is not None else None
    
    def set_camera_parameters(self, brightness: Optional[float] = None, 
                            contrast: Optional[float] = None,
                            saturation: Optional[float] = None,
                            exposure_time: Optional[int] = None) -> bool:
        """
        设置摄像头参数
        
        Args:
            brightness: 亮度 (0.0-1.0)
            contrast: 对比度 (0.0-2.0)
            saturation: 饱和度 (0.0-2.0)
            exposure_time: 曝光时间 (微秒，-1为自动)
            
        Returns:
            bool: 设置成功返回True
        """
        try:
            # 更新参数值
            if brightness is not None:
                self.brightness = max(0.0, min(1.0, brightness))
            if contrast is not None:
                self.contrast = max(0.0, min(2.0, contrast))
            if saturation is not None:
                self.saturation = max(0.0, min(2.0, saturation))
            if exposure_time is not None:
                self.exposure_time = exposure_time
                
            # 应用参数到硬件
            return self._apply_camera_parameters()
            
        except Exception as e:
            self.logger.error(f"设置摄像头参数失败: {str(e)}")
            return False
    
    def get_camera_info(self) -> Dict[str, Any]:
        """
        获取摄像头详细信息
        
        Returns:
            Dict[str, Any]: 摄像头信息字典
        """
        try:
            info = {
                'camera_id': self.camera_id,
                'resolution': self.resolution,
                'is_running': self.is_running,
                'is_capturing': self.is_capturing,
                'brightness': self.brightness,
                'contrast': self.contrast,
                'saturation': self.saturation,
                'exposure_time': self.exposure_time,
                'library': 'picamera2' if PICAMERA2_AVAILABLE else 'unavailable'
            }
            
            # 获取硬件信息（如果可用）
            if self.picam2 and self.is_running:
                try:
                    info['model'] = self.picam2.camera_properties.get('Model', 'Unknown')
                    info['sensor_modes'] = len(self.picam2.sensor_modes) if hasattr(self.picam2, 'sensor_modes') else 0
                except Exception:
                    info['model'] = 'Unknown'
                    info['sensor_modes'] = 0
            else:
                info['model'] = 'Not initialized'
                info['sensor_modes'] = 0
                
            return info
            
        except Exception as e:
            self.logger.error(f"获取摄像头信息失败: {str(e)}")
            return {'error': str(e)}
    
    def _apply_camera_parameters(self) -> bool:
        """
        应用摄像头参数到硬件（内部方法）
        
        Returns:
            bool: 应用成功返回True
        """
        try:
            if not self.picam2 or not self.is_running:
                self.logger.debug("摄像头未运行，跳过参数应用")
                return True
                
            # Note: Picamera2的参数设置需要在配置阶段完成
            # 这里可以添加具体的参数设置逻辑
            self.logger.debug(f"应用摄像头参数: brightness={self.brightness}, contrast={self.contrast}")
            return True
            
        except Exception as e:
            self.logger.error(f"应用摄像头参数失败: {str(e)}")
            return False
    
    def _capture_loop(self):
        """
        连续捕获循环（内部线程方法）
        """
        self.logger.info("捕获循环线程已启动")
        capture_count = 0
        
        while self.is_capturing:
            try:
                # 捕获图像
                frame = self.capture_image()
                
                if frame is not None:
                    capture_count += 1
                    
                    # 调用回调函数
                    if self.frame_callback:
                        try:
                            self.frame_callback(frame)
                        except Exception as e:
                            self.logger.error(f"帧回调函数错误: {str(e)}")
                            
                    self.logger.debug(f"捕获循环: 第{capture_count}帧, shape={frame.shape}")
                    
                # 控制捕获频率（约30fps）
                time.sleep(0.033)
                
            except Exception as e:
                self.logger.error(f"捕获循环错误: {str(e)}")
                time.sleep(1.0)  # 错误时降低频率
                
        self.logger.info(f"捕获循环线程已停止，共捕获{capture_count}帧")
    
    # 上下文管理器支持
    def __enter__(self):
        """
        上下文管理器入口
        
        Returns:
            CSICamera: 摄像头实例
        """
        if not self.initialize():
            raise RuntimeError("摄像头初始化失败")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        上下文管理器出口
        """
        self.release_camera()


class CSICameraManager:
    """
    CSI摄像头管理器
    管理多个摄像头实例，提供统一的访问接口
    """
    
    def __init__(self):
        """
        初始化摄像头管理器
        """
        self.cameras: Dict[str, CSICamera] = {}
        self.logger = logging.getLogger(f"{__name__}.CSICameraManager")
        self.logger.info("CSI摄像头管理器初始化完成")
    
    def add_camera(self, name: str, camera_id: int = 0,
                   resolution: Tuple[int, int] = (1280, 1024)) -> bool:
        """
        添加摄像头到管理器
        
        Args:
            name: 摄像头名称
            camera_id: 摄像头ID
            resolution: 图像分辨率
            
        Returns:
            bool: 添加成功返回True
        """
        try:
            self.logger.info(f"添加摄像头: name={name}, camera_id={camera_id}")
            
            # 检查是否已存在
            if name in self.cameras:
                self.logger.warning(f"摄像头'{name}'已存在，将重新创建")
                self.remove_camera(name)
                
            # 创建摄像头实例
            camera = CSICamera(camera_id, resolution)
            
            # 初始化摄像头
            if camera.initialize():
                self.cameras[name] = camera
                self.logger.info(f"摄像头'{name}'添加成功")
                return True
            else:
                self.logger.error(f"摄像头'{name}'初始化失败")
                return False
                
        except Exception as e:
            self.logger.error(f"添加摄像头'{name}'失败: {str(e)}")
            return False
    
    def remove_camera(self, name: str) -> bool:
        """
        从管理器中移除摄像头
        
        Args:
            name: 摄像头名称
            
        Returns:
            bool: 移除成功返回True
        """
        try:
            if name not in self.cameras:
                self.logger.warning(f"摄像头'{name}'不存在")
                return True
                
            self.logger.info(f"移除摄像头: {name}")
            
            # 释放摄像头资源
            camera = self.cameras[name]
            camera.release_camera()
            
            # 从管理器中移除
            del self.cameras[name]
            
            self.logger.info(f"摄像头'{name}'已移除")
            return True
            
        except Exception as e:
            self.logger.error(f"移除摄像头'{name}'失败: {str(e)}")
            return False
    
    def get_camera(self, name: str) -> Optional[CSICamera]:
        """
        获取指定名称的摄像头
        
        Args:
            name: 摄像头名称
            
        Returns:
            CSICamera: 摄像头实例，不存在返回None
        """
        return self.cameras.get(name)
    
    def list_cameras(self) -> list:
        """
        获取所有摄像头名称列表
        
        Returns:
            list: 摄像头名称列表
        """
        return list(self.cameras.keys())
    
    def get_all_camera_info(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有摄像头的信息
        
        Returns:
            Dict[str, Dict[str, Any]]: 摄像头信息字典
        """
        info = {}
        for name, camera in self.cameras.items():
            info[name] = camera.get_camera_info()
        return info
    
    def release_all_cameras(self) -> bool:
        """
        释放所有摄像头资源
        
        Returns:
            bool: 全部释放成功返回True
        """
        try:
            self.logger.info("开始释放所有摄像头资源")
            
            success_count = 0
            for name, camera in list(self.cameras.items()):
                if camera.release_camera():
                    success_count += 1
                    
            self.cameras.clear()
            self.logger.info(f"所有摄像头资源已释放 ({success_count}/{len(self.cameras)})")
            return success_count == len(self.cameras)
            
        except Exception as e:
            self.logger.error(f"释放所有摄像头资源失败: {str(e)}")
            return False


# 向后兼容的别名（用于过渡期）
class CSICameraLegacy:
    """
    遗留API兼容类
    提供旧版本的方法名映射，用于向后兼容
    """
    
    def __init__(self, camera: CSICamera):
        self.camera = camera
        self.logger = logging.getLogger(f"{__name__}.CSICameraLegacy")
    
    # 旧方法名映射
    def capture_single(self, save_path: Optional[str] = None) -> Optional[np.ndarray]:
        """兼容旧版本的capture_single方法"""
        self.logger.warning("capture_single() 已弃用，请使用 capture_image()")
        return self.camera.capture_image(save_path)
    
    def save_frame(self, file_path: str, frame: Optional[np.ndarray] = None) -> bool:
        """兼容旧版本的save_frame方法"""
        self.logger.warning("save_frame() 已弃用，请使用 save_image()")
        return self.camera.save_image(file_path, frame)
    
    def start_continuous_capture(self, callback: Optional[Callable[[np.ndarray], None]] = None) -> bool:
        """兼容旧版本的start_continuous_capture方法"""
        return self.camera.start_continuous_capture(callback)
    
    def stop_continuous_capture(self) -> bool:
        """兼容旧版本的stop_continuous_capture方法"""
        return self.camera.stop_continuous_capture()
    
    def release(self) -> bool:
        """兼容旧版本的release方法"""
        self.logger.warning("release() 已弃用，请使用 release_camera()")
        return self.camera.release_camera()


# 模块测试
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🧪 CSI摄像头模块测试")
    
    try:
        # 测试单个摄像头
        with CSICamera(camera_id=0, resolution=(1280, 1024)) as camera:
            print(f"✅ 摄像头初始化成功")
            
            # 获取摄像头信息
            info = camera.get_camera_info()
            print(f"📷 摄像头信息: {info}")
            
            # 捕获测试图像
            frame = camera.capture_image(save_path="test_capture.jpg")
            if frame is not None:
                print(f"✅ 图像捕获成功: shape={frame.shape}")
            else:
                print("❌ 图像捕获失败")
                
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        
    print("🧪 测试完成")