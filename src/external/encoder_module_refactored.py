#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
旋转编码器模块 - 重构版本
提供高精度的旋转编码器位置检测和触发功能

重构改进：
1. 统一API命名规范：所有方法使用动词开头，如start_monitoring()、reset_position()等
2. 增强错误处理和边界检查
3. 完善文档字符串和类型注解
4. 统一参数顺序和返回值格式
"""

import threading
import time
import logging
from typing import Optional, Callable, Dict, Any
from datetime import datetime

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    logging.warning("RPi.GPIO库不可用，编码器功能将受限")


class RotaryEncoder:
    """
    旋转编码器类
    提供高精度的位置计数和触发功能
    
    主要功能：
    - A/B相位置计数
    - Z相归零检测
    - 位置触发回调
    - 速度计算
    - 边界保护
    """
    
    def __init__(self, pin_a: int, pin_b: int, pin_z: int = None, 
                 name: str = "encoder"):
        """
        初始化旋转编码器
        
        Args:
            pin_a: A相引脚编号（BCM）
            pin_b: B相引脚编号（BCM）
            pin_z: Z相引脚编号（BCM），可选
            name: 编码器名称，用于日志标识
        """
        self.pin_a = pin_a
        self.pin_b = pin_b
        self.pin_z = pin_z
        self.name = name
        
        # 位置计数
        self.position = 0
        self.position_lock = threading.Lock()
        
        # 运行状态
        self.is_monitoring = False
        self.is_initialized = False
        
        # 触发设置
        self.trigger_position = 150
        self.trigger_callback: Optional[Callable[[int], None]] = None
        self.last_trigger_position = 0
        self.trigger_enabled = True
        
        # 速度计算
        self.speed = 0.0
        self.last_position_time = None
        self.last_position = 0
        
        # 边界保护
        self.min_position = None
        self.max_position = None
        
        # 统计信息
        self.stats = {
            'total_rotations': 0,
            'zero_crossings': 0,
            'trigger_count': 0,
            'start_time': datetime.now().isoformat()
        }
        
        # 线程相关
        self.monitor_thread: Optional[threading.Thread] = None
        self.speed_thread: Optional[threading.Thread] = None
        
        # 日志
        self.logger = logging.getLogger(f"{__name__}.RotaryEncoder.{name}")
        
        self.logger.info(f"旋转编码器初始化完成: A={pin_a}, B={pin_b}, Z={pin_z}")
    
    def initialize_hardware(self) -> bool:
        """
        初始化硬件接口
        
        Returns:
            bool: 初始化成功返回True
        """
        try:
            if not GPIO_AVAILABLE:
                self.logger.error("RPi.GPIO库不可用，无法初始化硬件")
                return False
                
            self.logger.info(f"开始初始化编码器硬件: {self.name}")
            
            # 设置GPIO模式
            GPIO.setmode(GPIO.BCM)
            
            # 配置A/B相引脚
            GPIO.setup(self.pin_a, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.pin_b, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # 配置Z相引脚（如果提供）
            if self.pin_z is not None:
                GPIO.setup(self.pin_z, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                
            # 添加中断检测
            GPIO.add_event_detect(self.pin_a, GPIO.BOTH, 
                                callback=self._handle_encoder_pulse, 
                                bouncetime=1)
            
            if self.pin_z is not None:
                GPIO.add_event_detect(self.pin_z, GPIO.FALLING, 
                                    callback=self._handle_zero_pulse, 
                                    bouncetime=10)
                
            self.is_initialized = True
            self.logger.info(f"编码器硬件初始化成功: {self.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"编码器硬件初始化失败: {str(e)}")
            self.is_initialized = False
            return False
    
    def start_monitoring(self, callback: Optional[Callable[[int], None]] = None) -> bool:
        """
        开始位置监控
        
        Args:
            callback: 位置变化回调函数
            
        Returns:
            bool: 启动成功返回True
        """
        try:
            if self.is_monitoring:
                self.logger.warning(f"编码器'{self.name}'已在监控中")
                return True
                
            if not self.is_initialized:
                self.logger.error(f"编码器'{self.name}'未初始化")
                return False
                
            self.logger.info(f"开始编码器位置监控: {self.name}")
            
            # 设置回调函数
            self.trigger_callback = callback
            
            # 重置状态
            self.reset_position()
            self.last_position_time = datetime.now()
            
            # 启动监控线程
            self.is_monitoring = True
            
            self.monitor_thread = threading.Thread(
                target=self._monitoring_loop, 
                name=f"EncoderMonitor-{self.name}"
            )
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            
            # 启动速度计算线程
            self.speed_thread = threading.Thread(
                target=self._speed_calculation_loop, 
                name=f"EncoderSpeed-{self.name}"
            )
            self.speed_thread.daemon = True
            self.speed_thread.start()
            
            self.logger.info(f"编码器位置监控已启动: {self.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"启动编码器监控失败: {str(e)}")
            self.is_monitoring = False
            return False
    
    def stop_monitoring(self) -> bool:
        """
        停止位置监控
        
        Returns:
            bool: 停止成功返回True
        """
        try:
            if not self.is_monitoring:
                self.logger.debug(f"编码器'{self.name}'未在监控中")
                return True
                
            self.logger.info(f"停止编码器位置监控: {self.name}")
            
            # 停止监控循环
            self.is_monitoring = False
            
            # 等待线程结束
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=5)
                
            if self.speed_thread and self.speed_thread.is_alive():
                self.speed_thread.join(timeout=5)
                
            self.logger.info(f"编码器位置监控已停止: {self.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"停止编码器监控失败: {str(e)}")
            return False
    
    def reset_position(self, position: int = 0) -> bool:
        """
        重置位置计数器
        
        Args:
            position: 新位置值，默认为0
            
        Returns:
            bool: 重置成功返回True
        """
        try:
            with self.position_lock:
                old_position = self.position
                self.position = position
                self.last_trigger_position = position
                
            self.logger.info(f"编码器位置已重置: {self.name}, {old_position} -> {position}")
            return True
            
        except Exception as e:
            self.logger.error(f"重置编码器位置失败: {str(e)}")
            return False
    
    def set_trigger_position(self, position: int, enabled: bool = True) -> bool:
        """
        设置触发位置
        
        Args:
            position: 触发位置
            enabled: 是否启用触发
            
        Returns:
            bool: 设置成功返回True
        """
        try:
            self.trigger_position = position
            self.trigger_enabled = enabled
            
            self.logger.info(f"触发位置已设置: {self.name}, position={position}, enabled={enabled}")
            return True
            
        except Exception as e:
            self.logger.error(f"设置触发位置失败: {str(e)}")
            return False
    
    def set_position_limits(self, min_position: Optional[int] = None, 
                           max_position: Optional[int] = None) -> bool:
        """
        设置位置边界限制
        
        Args:
            min_position: 最小位置，None表示无限制
            max_position: 最大位置，None表示无限制
            
        Returns:
            bool: 设置成功返回True
        """
        try:
            self.min_position = min_position
            self.max_position = max_position
            
            self.logger.info(f"位置边界已设置: {self.name}, min={min_position}, max={max_position}")
            return True
            
        except Exception as e:
            self.logger.error(f"设置位置边界失败: {str(e)}")
            return False
    
    def get_position(self) -> int:
        """
        获取当前位置
        
        Returns:
            int: 当前位置值
        """
        with self.position_lock:
            return self.position
    
    def get_speed(self) -> float:
        """
        获取当前速度
        
        Returns:
            float: 当前速度（位置/秒）
        """
        return self.speed
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息字典
        """
        try:
            uptime = 0
            if self.stats['start_time']:
                start_time = datetime.fromisoformat(self.stats['start_time'])
                uptime = (datetime.now() - start_time).total_seconds()
                
            return {
                'name': self.name,
                'position': self.get_position(),
                'speed': self.get_speed(),
                'trigger_position': self.trigger_position,
                'trigger_enabled': self.trigger_enabled,
                'is_monitoring': self.is_monitoring,
                'is_initialized': self.is_initialized,
                'total_rotations': self.stats['total_rotations'],
                'zero_crossings': self.stats['zero_crossings'],
                'trigger_count': self.stats['trigger_count'],
                'uptime_seconds': uptime,
                'pin_a': self.pin_a,
                'pin_b': self.pin_b,
                'pin_z': self.pin_z
            }
            
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {str(e)}")
            return {'error': str(e)}
    
    def cleanup_resources(self) -> bool:
        """
        清理资源
        
        Returns:
            bool: 清理成功返回True
        """
        try:
            self.logger.info(f"开始清理编码器资源: {self.name}")
            
            # 停止监控
            self.stop_monitoring()
            
            # 清理GPIO
            if GPIO_AVAILABLE and self.is_initialized:
                try:
                    GPIO.remove_event_detect(self.pin_a)
                    if self.pin_z is not None:
                        GPIO.remove_event_detect(self.pin_z)
                    self.logger.debug(f"GPIO事件检测已移除: {self.name}")
                except Exception as e:
                    self.logger.warning(f"移除GPIO事件检测失败: {str(e)}")
                    
            self.is_initialized = False
            
            self.logger.info(f"编码器资源清理完成: {self.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"清理编码器资源失败: {str(e)}")
            return False
    
    def _handle_encoder_pulse(self, channel):
        """
        处理编码器脉冲（内部中断回调）
        """
        try:
            # 读取A/B相状态
            a_state = GPIO.input(self.pin_a)
            b_state = GPIO.input(self.pin_b)
            
            # 根据状态变化更新位置
            with self.position_lock:
                old_position = self.position
                
                if a_state == b_state:
                    self.position += 1  # 顺时针
                else:
                    self.position -= 1  # 逆时针
                    
                # 边界检查
                if self.min_position is not None:
                    self.position = max(self.min_position, self.position)
                if self.max_position is not None:
                    self.position = min(self.max_position, self.position)
                    
                new_position = self.position
                
            # 检查触发条件
            if (self.trigger_enabled and 
                self.trigger_callback and
                abs(new_position - self.last_trigger_position) >= self.trigger_position):
                
                self.last_trigger_position = new_position
                self.stats['trigger_count'] += 1
                
                # 异步调用回调函数（避免在中断中执行耗时操作）
                threading.Thread(
                    target=self._execute_trigger_callback,
                    args=(new_position,),
                    name=f"TriggerCallback-{self.name}"
                ).start()
                
            self.logger.debug(f"编码器脉冲: {old_position} -> {new_position}")
            
        except Exception as e:
            self.logger.error(f"处理编码器脉冲失败: {str(e)}")
    
    def _handle_zero_pulse(self, channel):
        """
        处理零位脉冲（内部中断回调）
        """
        try:
            self.logger.info(f"检测到零位脉冲: {self.name}")
            
            with self.position_lock:
                self.position = 0
                self.last_trigger_position = 0
                self.stats['zero_crossings'] += 1
                
            self.logger.info(f"编码器位置已归零: {self.name}")
            
        except Exception as e:
            self.logger.error(f"处理零位脉冲失败: {str(e)}")
    
    def _execute_trigger_callback(self, position: int):
        """
        执行触发回调（内部方法）
        
        Args:
            position: 当前位置
        """
        try:
            if self.trigger_callback:
                self.trigger_callback(position)
                
        except Exception as e:
            self.logger.error(f"执行触发回调失败: {str(e)}")
    
    def _monitoring_loop(self):
        """
        监控循环（内部线程方法）
        """
        self.logger.info(f"编码器监控循环已启动: {self.name}")
        
        while self.is_monitoring:
            try:
                # 监控循环主要用于状态检查和日志记录
                time.sleep(1.0)
                
                # 记录位置变化
                current_position = self.get_position()
                self.logger.debug(f"编码器状态: {self.name}, position={current_position}")
                
            except Exception as e:
                self.logger.error(f"监控循环错误: {str(e)}")
                time.sleep(5.0)
                
        self.logger.info(f"编码器监控循环已停止: {self.name}")
    
    def _speed_calculation_loop(self):
        """
        速度计算循环（内部线程方法）
        """
        self.logger.info(f"编码器速度计算循环已启动: {self.name}")
        
        while self.is_monitoring:
            try:
                # 计算速度
                current_time = datetime.now()
                current_position = self.get_position()
                
                if self.last_position_time and self.last_position_time != current_time:
                    time_delta = (current_time - self.last_position_time).total_seconds()
                    position_delta = current_position - self.last_position
                    
                    if time_delta > 0:
                        self.speed = position_delta / time_delta
                        
                # 更新状态
                self.last_position_time = current_time
                self.last_position = current_position
                
                # 休眠
                time.sleep(0.1)  # 10Hz更新频率
                
            except Exception as e:
                self.logger.error(f"速度计算循环错误: {str(e)}")
                time.sleep(1.0)
                
        self.logger.info(f"编码器速度计算循环已停止: {self.name}")
    
    # 上下文管理器支持
    def __enter__(self):
        """
        上下文管理器入口
        
        Returns:
            RotaryEncoder: 编码器实例
        """
        if not self.initialize_hardware():
            raise RuntimeError("编码器硬件初始化失败")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        上下文管理器出口
        """
        self.cleanup_resources()


class EncoderManager:
    """
    编码器管理器
    管理多个旋转编码器实例，提供统一的访问接口
    """
    
    def __init__(self):
        """
        初始化编码器管理器
        """
        self.encoders: Dict[str, RotaryEncoder] = {}
        self.logger = logging.getLogger(f"{__name__}.EncoderManager")
        self.logger.info("编码器管理器初始化完成")
    
    def add_encoder(self, name: str, pin_a: int, pin_b: int, 
                   pin_z: Optional[int] = None) -> bool:
        """
        添加编码器到管理器
        
        Args:
            name: 编码器名称
            pin_a: A相引脚
            pin_b: B相引脚
            pin_z: Z相引脚（可选）
            
        Returns:
            bool: 添加成功返回True
        """
        try:
            self.logger.info(f"添加编码器: {name}")
            
            # 检查是否已存在
            if name in self.encoders:
                self.logger.warning(f"编码器'{name}'已存在，将重新创建")
                self.remove_encoder(name)
                
            # 创建编码器实例
            encoder = RotaryEncoder(pin_a, pin_b, pin_z, name)
            
            # 初始化硬件
            if encoder.initialize_hardware():
                self.encoders[name] = encoder
                self.logger.info(f"编码器'{name}'添加成功")
                return True
            else:
                self.logger.error(f"编码器'{name}'硬件初始化失败")
                return False
                
        except Exception as e:
            self.logger.error(f"添加编码器'{name}'失败: {str(e)}")
            return False
    
    def remove_encoder(self, name: str) -> bool:
        """
        从管理器中移除编码器
        
        Args:
            name: 编码器名称
            
        Returns:
            bool: 移除成功返回True
        """
        try:
            if name not in self.encoders:
                self.logger.warning(f"编码器'{name}'不存在")
                return True
                
            self.logger.info(f"移除编码器: {name}")
            
            # 清理编码器资源
            encoder = self.encoders[name]
            encoder.cleanup_resources()
            
            # 从管理器中移除
            del self.encoders[name]
            
            self.logger.info(f"编码器'{name}'已移除")
            return True
            
        except Exception as e:
            self.logger.error(f"移除编码器'{name}'失败: {str(e)}")
            return False
    
    def get_encoder(self, name: str) -> Optional[RotaryEncoder]:
        """
        获取指定名称的编码器
        
        Args:
            name: 编码器名称
            
        Returns:
            RotaryEncoder: 编码器实例，不存在返回None
        """
        return self.encoders.get(name)
    
    def list_encoders(self) -> list:
        """
        获取所有编码器名称列表
        
        Returns:
            list: 编码器名称列表
        """
        return list(self.encoders.keys())
    
    def get_all_statistics(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有编码器的统计信息
        
        Returns:
            Dict[str, Dict[str, Any]]: 编码器统计信息
        """
        stats = {}
        for name, encoder in self.encoders.items():
            stats[name] = encoder.get_statistics()
        return stats
    
    def cleanup_all_encoders(self) -> bool:
        """
        清理所有编码器资源
        
        Returns:
            bool: 全部清理成功返回True
        """
        try:
            self.logger.info("开始清理所有编码器资源")
            
            success_count = 0
            for name, encoder in list(self.encoders.items()):
                if encoder.cleanup_resources():
                    success_count += 1
                    
            self.encoders.clear()
            self.logger.info(f"所有编码器资源已清理 ({success_count})")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"清理所有编码器资源失败: {str(e)}")
            return False


# 向后兼容的别名（用于过渡期）
class EncoderModule:
    """
    编码器模块（向后兼容）
    提供旧版本的方法名映射
    """
    
    def __init__(self, pin_a: int, pin_b: int, pin_z: int):
        """
        初始化编码器模块（兼容旧版本）
        
        Args:
            pin_a: A相引脚
            pin_b: B相引脚
            pin_z: Z相引脚
        """
        self.encoder = RotaryEncoder(pin_a, pin_b, pin_z, "legacy")
        self.logger = logging.getLogger(f"{__name__}.EncoderModule")
    
    def start(self, callback: Optional[Callable[[int], None]] = None) -> bool:
        """
        开始监控（兼容旧版本）
        
        Args:
            callback: 位置变化回调函数
            
        Returns:
            bool: 启动成功返回True
        """
        self.logger.warning("start() 已弃用，请使用 start_monitoring()")
        return self.encoder.start_monitoring(callback)
    
    def stop(self) -> bool:
        """
        停止监控（兼容旧版本）
        
        Returns:
            bool: 停止成功返回True
        """
        self.logger.warning("stop() 已弃用，请使用 stop_monitoring()")
        return self.encoder.stop_monitoring()
    
    def reset_position(self, position: int = 0) -> bool:
        """
        重置位置（兼容旧版本）
        
        Args:
            position: 新位置值
            
        Returns:
            bool: 重置成功返回True
        """
        return self.encoder.reset_position(position)
    
    def set_trigger(self, position: int) -> bool:
        """
        设置触发位置（兼容旧版本）
        
        Args:
            position: 触发位置
            
        Returns:
            bool: 设置成功返回True
        """
        self.logger.warning("set_trigger() 已弃用，请使用 set_trigger_position()")
        return self.encoder.set_trigger_position(position)
    
    def get_position(self) -> int:
        """
        获取位置（兼容旧版本）
        
        Returns:
            int: 当前位置
        """
        return self.encoder.get_position()
    
    def cleanup(self) -> bool:
        """
        清理资源（兼容旧版本）
        
        Returns:
            bool: 清理成功返回True
        """
        self.logger.warning("cleanup() 已弃用，请使用 cleanup_resources()")
        return self.encoder.cleanup_resources()


# 模块测试
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🧪 旋转编码器模块测试")
    
    try:
        # 测试单个编码器
        with RotaryEncoder(pin_a=5, pin_b=6, pin_z=13, name="test_encoder") as encoder:
            print(f"✅ 编码器初始化成功")
            
            # 获取统计信息
            stats = encoder.get_statistics()
            print(f"📊 编码器统计: {stats}")
            
            # 设置触发位置
            encoder.set_trigger_position(100)
            
            # 模拟位置变化
            def position_callback(position):
                print(f"🎯 位置触发: {position}")
                
            # 开始监控
            if encoder.start_monitoring(position_callback):
                print("✅ 编码器监控已启动")
                
                # 测试运行5秒
                print("⏱️  测试运行5秒...")
                time.sleep(5)
                
                # 停止监控
                encoder.stop_monitoring()
                print("✅ 编码器监控已停止")
                
            else:
                print("❌ 编码器监控启动失败")
                
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        
    print("🧪 测试完成")