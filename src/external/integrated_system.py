#!/usr/bin/env python3
"""
集成系统模块 - 整合摄像头和MQTT功能
Integrated system module - combining camera and MQTT functionality
"""

import json
import logging
import threading
import time
import base64
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import cv2
import numpy as np

# 使用picamera2模块 (CSI摄像头)
from .picamera2_module import CSICamera, CSICameraManager
CAMERA_TYPE = "CSI"

from .ssh_pi_test_mqtt import SorterMQTTManager


class IntegratedSorterSystem:
    """
    集成芦笋分拣系统 - 整合摄像头和MQTT功能
    Integrated asparagus sorting system - combining camera and MQTT functionality
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化集成系统
        
        Args:
            config: 系统配置
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 组件初始化
        self.camera_manager = CSICameraManager()
        self.mqtt_manager = None
        self.main_camera = None
        
        # 记录摄像头类型
        self.logger.info(f"使用摄像头类型: {CAMERA_TYPE}")
        
        # 系统状态
        self.is_running = False
        self.is_processing = False
        self.processing_thread = None
        
        # 统计信息
        self.stats = {
            'total_processed': 0,
            'grade_a_count': 0,
            'grade_b_count': 0,
            'grade_c_count': 0,
            'defect_count': 0,
            'start_time': None,
            'last_process_time': None
        }
        
        # 处理参数（优先使用摄像头的拍照间隔）
        self.processing_interval = (
            config.get('camera', {}).get('capture_interval',
            config.get('processing', {}).get('interval', 5.0))
        )
        self.auto_capture = config.get('camera', {}).get('auto_capture', True)
        self.save_images = config.get('processing', {}).get('save_images', True)
        # 仅拍照模式：不做图像算法与MQTT发布
        self.capture_only = config.get('camera', {}).get('capture_only', False)
        
    def initialize(self) -> bool:
        """
        初始化系统所有组件
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            self.logger.info("开始初始化集成分拣系统...")
            
            # 初始化摄像头（若失败，则降级为无摄像头模式继续运行）
            if not self._initialize_camera():
                self.logger.warning("摄像头初始化失败，系统将以无摄像头模式运行")
                self.main_camera = None
            
            # 初始化MQTT (可选)
            # 即使在仅拍照模式下，只要开启了MQTT，也初始化用于发送抓拍图片
            if self.config.get('mqtt', {}).get('enabled', False):
                if not self._initialize_mqtt():
                    self.logger.warning("MQTT初始化失败，系统将在无MQTT模式下运行")
            
            self.logger.info("集成分拣系统初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"系统初始化失败: {str(e)}")
            return False
    
    def _initialize_camera(self) -> bool:
        """初始化摄像头"""
        try:
            camera_config = self.config.get('camera', {})
            # 支持通过配置禁用摄像头，便于在仅验证MQTT时运行
            if camera_config.get('enabled', True) is False:
                self.logger.info("摄像头已在配置中禁用，跳过初始化")
                self.main_camera = None
                return True
            
            # 添加主摄像头
            if CAMERA_TYPE == "CSI":
                # CSI摄像头使用camera_num参数
                success = self.camera_manager.add_camera(
                    name='main',
                    camera_num=camera_config.get('device_id', 0),
                    resolution=tuple(camera_config.get('resolution', [1280, 1024]))
                )
            else:
                # USB摄像头使用camera_id参数
                success = self.camera_manager.add_camera(
                    name='main',
                    camera_id=camera_config.get('device_id', 0),
                    resolution=tuple(camera_config.get('resolution', [1280, 1024]))
                )
            
            if success:
                self.main_camera = self.camera_manager.get_camera('main')
                
                # 设置摄像头参数
                if CAMERA_TYPE == "CSI":
                    # picamera2参数范围不同
                    self.main_camera.set_parameters(
                        brightness=camera_config.get('brightness', 0.0),  # -1.0 到 1.0
                        contrast=camera_config.get('contrast', 1.0),      # 0.0 到 2.0
                        saturation=camera_config.get('saturation', 1.0),  # 0.0 到 2.0
                        exposure_time=camera_config.get('exposure_time', None)  # 微秒或None
                    )
                else:
                    # OpenCV参数
                    self.main_camera.set_parameters(
                        brightness=camera_config.get('brightness', 0.5),
                        contrast=camera_config.get('contrast', 0.5),
                        saturation=camera_config.get('saturation', 0.5),
                        exposure=camera_config.get('exposure', -1)
                    )
                
                self.logger.info("摄像头初始化成功")
                return True
            else:
                self.logger.error("摄像头初始化失败")
                return False
                
        except Exception as e:
            self.logger.error(f"摄像头初始化错误: {str(e)}")
            return False
    
    def _initialize_mqtt(self) -> bool:
        """初始化MQTT"""
        try:
            # 加载 MQTT 配置文件
            mqtt_config_path = Path(__file__).parent.parent.parent / "config" / "mqtt_config.json"
            if mqtt_config_path.exists():
                with open(mqtt_config_path, 'r', encoding='utf-8') as f:
                    mqtt_config = json.load(f)
            else:
                self.logger.error(f"MQTT配置文件不存在: {mqtt_config_path}")
                return False

            # 确保使用配置文件中的代理服务器地址
            broker_config = mqtt_config.get('broker', {})
            self.mqtt_manager = SorterMQTTManager({
                'broker': {
                    'host': broker_config.get('host', 'voicevon.vicp.io'),
                    'port': broker_config.get('port', 1883),
                    'username': broker_config.get('username', 'admin'),
                    'password': broker_config.get('password', 'admin1970'),
                    'client_id': broker_config.get('client_id', 'pi_sorter_integrated')
                },
                'topics': mqtt_config.get('topics', {}),
                'settings': mqtt_config.get('settings', {})
            })
            
            if self.mqtt_manager.initialize():
                self.logger.info(f"MQTT初始化成功，连接到 {broker_config.get('host')}:{broker_config.get('port')}")
                return True
            else:
                self.logger.error("MQTT初始化失败")
                return False
                
        except Exception as e:
            self.logger.error(f"MQTT初始化错误: {str(e)}")
            return False
    
    def start_processing(self) -> bool:
        """
        开始分拣处理
        
        Returns:
            bool: 启动是否成功
        """
        if self.is_running:
            self.logger.warning("系统已在运行中")
            return True
        
        try:
            self.is_running = True
            self.is_processing = True
            self.stats['start_time'] = datetime.now()
            
            # 启动处理线程
            self.processing_thread = threading.Thread(target=self._processing_loop)
            self.processing_thread.daemon = True
            self.processing_thread.start()
            
            # 发布MQTT状态
            if self.mqtt_manager:
                self.mqtt_manager.publish_alert('system', '分拣系统已启动', 'info')
            
            self.logger.info("分拣处理已启动")
            return True
            
        except Exception as e:
            self.logger.error(f"启动分拣处理失败: {str(e)}")
            self.is_running = False
            self.is_processing = False
            return False
    
    def stop_processing(self):
        """停止分拣处理"""
        try:
            self.is_running = False
            self.is_processing = False
            
            # 等待处理线程结束
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=5.0)
            
            # 发布MQTT状态
            if self.mqtt_manager:
                self.mqtt_manager.publish_alert('system', '分拣系统已停止', 'info')
            
            self.logger.info("分拣处理已停止")
            
        except Exception as e:
            self.logger.error(f"停止分拣处理时发生错误: {str(e)}")
    
    def _processing_loop(self):
        """处理循环"""
        self.logger.info("开始分拣处理循环")

        while self.is_running:
            try:
                if self.is_processing:
                    # 捕获图像
                    frame = self._capture_image()

                    if frame is not None:
                        if self.capture_only:
                            # 仅拍照模式：保存原图，不进行处理
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            filename = f"capture_{timestamp}.jpg"

                            data_dir = self.config.get('system', {}).get('data_dir', 'data')
                            images_subdir = self.config.get('data_management', {}).get('subdirectories', {}).get('images', 'images')
                            image_dir = Path(data_dir) / images_subdir
                            image_dir.mkdir(parents=True, exist_ok=True)
                            save_path = str(image_dir / filename)

                            if self.main_camera:
                                self.main_camera.save_frame(save_path, frame)

                            # 统计
                            self.stats['total_processed'] += 1
                            self.stats['last_process_time'] = datetime.now()
                            self.logger.info(f"已保存抓拍图片: {save_path}")

                            # 抓拍成功后通过MQTT发送图片（若MQTT已启用并连接）
                            try:
                                if self.mqtt_manager:
                                    self._publish_captured_image(save_path)
                            except Exception as e:
                                self.logger.warning(f"抓拍图片MQTT发送失败: {str(e)}")
                        else:
                            # 正常模式：处理与发布
                            result = self._process_image(frame)
                            if result:
                                self._update_stats(result)
                                self._publish_result(result, frame)
                                self.stats['last_process_time'] = datetime.now()
                
                # 等待下次处理
                time.sleep(self.processing_interval)
                
            except Exception as e:
                self.logger.error(f"处理循环错误: {str(e)}")
                time.sleep(1.0)
        
        self.logger.info("分拣处理循环结束")
    
    def _capture_image(self) -> Optional[np.ndarray]:
        """捕获图像"""
        try:
            if not self.main_camera:
                return None
            
            frame = self.main_camera.capture_frame()
            
            if frame is not None:
                self.logger.debug("图像捕获成功")
                return frame
            else:
                self.logger.warning("图像捕获失败")
                return None
                
        except Exception as e:
            self.logger.error(f"图像捕获错误: {str(e)}")
            return None
    
    def _process_image(self, frame: np.ndarray) -> Optional[Dict[str, Any]]:
        """
        处理图像 (简化版本，实际需要集成完整的分拣算法)
        
        Args:
            frame: 输入图像
            
        Returns:
            Dict: 处理结果
        """
        try:
            # 这里是简化的处理逻辑，实际需要集成完整的芦笋分拣算法
            
            # 图像预处理
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # 简单的轮廓检测
            _, thresh = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # 找到最大轮廓
                largest_contour = max(contours, key=cv2.contourArea)
                
                # 计算基本特征
                area = cv2.contourArea(largest_contour)
                perimeter = cv2.arcLength(largest_contour, True)
                
                # 简化的分级逻辑
                if area > 5000:
                    grade = 'A'
                elif area > 2000:
                    grade = 'B'
                else:
                    grade = 'C'
                
                # 构造结果
                result = {
                    'item_id': f"item_{int(time.time())}",
                    'timestamp': datetime.now().isoformat(),
                    'grade': grade,
                    'area': float(area),
                    'perimeter': float(perimeter),
                    'length': float(perimeter / 2),  # 简化计算
                    'diameter': float(np.sqrt(area / np.pi) * 2),  # 简化计算
                    'defects': [],
                    'confidence': 0.85,
                    'processing_time': 0.1
                }
                
                self.logger.debug(f"图像处理完成: {result}")
                return result
            else:
                self.logger.debug("未检测到有效轮廓")
                return None
                
        except Exception as e:
            self.logger.error(f"图像处理错误: {str(e)}")
            return None
    
    def _update_stats(self, result: Dict[str, Any]):
        """更新统计信息"""
        try:
            self.stats['total_processed'] += 1
            
            grade = result.get('grade', 'C')
            if grade == 'A':
                self.stats['grade_a_count'] += 1
            elif grade == 'B':
                self.stats['grade_b_count'] += 1
            else:
                self.stats['grade_c_count'] += 1
            
            if result.get('defects'):
                self.stats['defect_count'] += 1
                
        except Exception as e:
            self.logger.error(f"更新统计信息错误: {str(e)}")
    
    def _publish_result(self, result: Dict[str, Any], frame: np.ndarray = None):
        """发布处理结果"""
        try:
            # 发布到MQTT
            if self.mqtt_manager:
                self.mqtt_manager.publish_sorting_result(result)
            
            # 保存图像 (如果启用)
            if self.save_images and frame is not None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"sorted_{result['item_id']}_{timestamp}.jpg"

                # 依据配置构建保存路径：data/images/
                data_dir = self.config.get('system', {}).get('data_dir', 'data')
                images_subdir = self.config.get('data_management', {}).get('subdirectories', {}).get('images', 'images')
                image_dir = Path(data_dir) / images_subdir
                image_dir.mkdir(parents=True, exist_ok=True)
                save_path = str(image_dir / filename)

                if self.main_camera:
                    self.main_camera.save_frame(save_path, frame)

            self.logger.info(f"处理结果: {result['item_id']} -> {result['grade']}")
            
        except Exception as e:
            self.logger.error(f"发布结果错误: {str(e)}")

    def _publish_captured_image(self, file_path: str) -> bool:
        """
        发布抓拍图片到MQTT的 images 主题。
        优先发送Base64内容，若文件过大则仅发送元数据与路径。
        
        Args:
            file_path: 已保存图片的文件路径
        Returns:
            bool: 发布是否成功
        """
        try:
            if not self.mqtt_manager:
                return False

            # 读取文件并估算大小
            p = Path(file_path)
            if not p.exists():
                self.logger.warning(f"抓拍图片不存在，无法MQTT发送: {file_path}")
                return False

            file_size = p.stat().st_size
            max_msg_size = self.config.get('mqtt', {}).get('max_message_size', 1048576)
            # Base64后大小约增加33%-37%，取1.37系数估算
            estimated_b64_size = int(file_size * 1.37)

            if estimated_b64_size > max_msg_size:
                # 文件过大，发送元数据与路径
                payload = {
                    'type': 'image_ref',
                    'filename': p.name,
                    'path': str(p.as_posix()),
                    'size_bytes': file_size,
                    'timestamp': datetime.now().isoformat(),
                    'note': 'image too large to inline; sending path only'
                }
                self.logger.warning(f"抓拍图片过大({file_size}B)，仅发送路径与元数据")
                return self.mqtt_manager.publish_message(
                    self.config.get('mqtt', {}).get('topics', {}).get('images', 'pi_sorter/images'),
                    payload,
                    qos=self.config.get('mqtt', {}).get('qos_level', 0),
                    retain=self.config.get('mqtt', {}).get('retain_messages', False)
                )

            # 发送Base64内容
            with p.open('rb') as f:
                data = f.read()
            b64 = base64.b64encode(data).decode('ascii')
            payload = {
                'type': 'image',
                'filename': p.name,
                'size_bytes': file_size,
                'encoding': 'base64',
                'content': b64,
                'timestamp': datetime.now().isoformat()
            }
            return self.mqtt_manager.publish_message(
                self.config.get('mqtt', {}).get('topics', {}).get('images', 'pi_sorter/images'),
                payload,
                qos=self.config.get('mqtt', {}).get('qos_level', 0),
                retain=self.config.get('mqtt', {}).get('retain_messages', False)
            )
        except Exception as e:
            self.logger.error(f"发布抓拍图片失败: {str(e)}")
            return False
    
    def capture_manual_image(self, filename: str = None) -> bool:
        """
        手动拍照
        
        Args:
            filename: 保存文件名
            
        Returns:
            bool: 拍照是否成功
        """
        try:
            if not self.main_camera:
                self.logger.error("摄像头未初始化")
                return False
            
            frame = self.main_camera.capture_frame()
            
            if frame is not None:
                if filename is None:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"manual_capture_{timestamp}.jpg"
                
                success = self.main_camera.save_frame(filename, frame)
                
                if success and self.mqtt_manager:
                    # 发布拍照事件
                    self.mqtt_manager.publish_alert('camera', f'手动拍照完成: {filename}', 'info')
                
                return success
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"手动拍照错误: {str(e)}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        获取系统状态
        
        Returns:
            Dict: 系统状态信息
        """
        try:
            camera_info = {}
            if self.main_camera:
                camera_info = self.main_camera.get_camera_info()
            
            # MQTT连接状态安全获取
            mqtt_connected = False
            if self.mqtt_manager and getattr(self.mqtt_manager, 'client', None):
                try:
                    mqtt_connected = bool(self.mqtt_manager.client.is_alive())
                except Exception:
                    mqtt_connected = False

            status = {
                'system': {
                    'running': self.is_running,
                    'processing': self.is_processing,
                    'uptime': None
                },
                'camera': camera_info,
                'mqtt': {
                    'connected': mqtt_connected
                },
                'statistics': self.stats.copy(),
                'timestamp': datetime.now().isoformat()
            }
            
            # 计算运行时间
            if self.stats['start_time']:
                uptime = datetime.now() - self.stats['start_time']
                status['system']['uptime'] = str(uptime)
            
            return status
            
        except Exception as e:
            self.logger.error(f"获取系统状态错误: {str(e)}")
            return {}
    
    def shutdown(self):
        """关闭系统"""
        try:
            self.logger.info("开始关闭集成分拣系统...")
            
            # 停止处理
            self.stop_processing()
            
            # 关闭MQTT
            if self.mqtt_manager:
                self.mqtt_manager.shutdown()
            
            # 释放摄像头
            if self.camera_manager:
                self.camera_manager.release_all()
            
            self.logger.info("集成分拣系统已关闭")
            
        except Exception as e:
            self.logger.error(f"关闭系统时发生错误: {str(e)}")


# 使用示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 系统配置
    config = {
        'camera': {
            'device_id': 0,
            'resolution': [1280, 1024],
            'brightness': 0.5,
            'contrast': 0.5,
            'saturation': 0.5,
            'exposure': -1,
            'auto_capture': True
        },
        'mqtt': {
            'enabled': True,
            'broker_host': 'localhost',
            'broker_port': 1883,
            'client_id': 'pi_sorter_integrated',
            'username': None,
            'password': None
        },
        'topics': {
            'status': 'pi_sorter/status',
            'results': 'pi_sorter/results',
            'commands': 'pi_sorter/commands',
            'images': 'pi_sorter/images',
            'alerts': 'pi_sorter/alerts',
            'statistics': 'pi_sorter/statistics',
            'heartbeat': 'pi_sorter/heartbeat'
        },
        'processing': {
            'interval': 5.0,  # 处理间隔（秒）
            'save_images': True,
            'save_raw_images': True,
            'image_format': 'jpg',
            'image_quality': 95
        }
    }
    
    # 测试集成系统
    print("测试集成分拣系统...")
    
    try:
        system = IntegratedSorterSystem(config)
        
        if system.initialize():
            print("系统初始化成功")
            
            # 启动处理
            if system.start_processing():
                print("分拣处理已启动")
                
                # 运行一段时间
                time.sleep(10)
                
                # 手动拍照测试
                system.capture_manual_image()
                
                # 获取系统状态
                status = system.get_system_status()
                print(f"系统状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
                
                # 停止处理
                system.stop_processing()
                print("分拣处理已停止")
            
            # 关闭系统
            system.shutdown()
            print("系统已关闭")
            
        else:
            print("系统初始化失败")
            
    except Exception as e:
        print(f"测试失败: {str(e)}")