#!/usr/bin/env python3
"""
编码器读取模块 - 处理旋转编码器的A/B相和Z相信号
"""

import RPi.GPIO as GPIO
import threading
import time
import logging
from typing import Optional, Callable

class RotaryEncoder:
    """旋转编码器控制类"""
    
    def __init__(self, pin_a: int, pin_b: int, pin_z: int):
        """
        初始化编码器
        
        Args:
            pin_a: A相信号GPIO引脚
            pin_b: B相信号GPIO引脚
            pin_z: Z相信号GPIO引脚（归零信号）
        """
        self.pin_a = pin_a
        self.pin_b = pin_b
        self.pin_z = pin_z
        
        # 位置计数器
        self.position = 0
        self.position_lock = threading.Lock()
        
        # 运行状态
        self.is_running = False
        self.read_thread = None
        
        # 位置触发回调
        self.trigger_position = 150  # 默认触发位置
        self.trigger_callback = None
        self.last_trigger_position = 0  # 上次触发位置
        
        # 日志
        self.logger = logging.getLogger(__name__)
        
        # GPIO初始化
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin_a, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.pin_b, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.pin_z, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # 配置中断
        GPIO.add_event_detect(self.pin_a, GPIO.BOTH, callback=self._handle_encoder)
        GPIO.add_event_detect(self.pin_z, GPIO.FALLING, callback=self._handle_zero)
    
    def _handle_encoder(self, channel):
        """处理A/B相信号"""
        a_state = GPIO.input(self.pin_a)
        b_state = GPIO.input(self.pin_b)
        
        with self.position_lock:
            if a_state == b_state:
                self.position += 1
            else:
                self.position -= 1
            
            # 检查是否到达触发位置
            if (self.trigger_callback is not None and 
                self.position >= self.trigger_position and 
                self.position > self.last_trigger_position + 100):  # 防止连续触发
                self.last_trigger_position = self.position
                self.trigger_callback()
    
    def _handle_zero(self, channel):
        """处理Z相归零信号"""
        with self.position_lock:
            self.position = 0
            self.logger.info("编码器位置已归零")
    
    def start(self):
        """开始读取编码器"""
        if self.is_running:
            return
        
        self.is_running = True
        self.logger.info("开始读取编码器")
    
    def stop(self):
        """停止读取编码器"""
        if not self.is_running:
            return
        
        self.is_running = False
        self.logger.info("停止读取编码器")
    
    def get_position(self) -> int:
        """获取当前位置"""
        with self.position_lock:
            return self.position
    
    def set_trigger(self, position: int, callback: Callable[[], None]):
        """
        设置位置触发
        
        Args:
            position: 触发位置
            callback: 触发回调函数
        """
        self.trigger_position = position
        self.trigger_callback = callback
        self.logger.info(f"设置触发位置: {position}")
    
    def reset_position(self):
        """手动重置位置计数器"""
        with self.position_lock:
            self.position = 0
            self.logger.info("手动重置编码器位置")
    
    def cleanup(self):
        """清理GPIO资源"""
        self.stop()
        GPIO.cleanup([self.pin_a, self.pin_b, self.pin_z])
        self.logger.info("编码器资源已清理")
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.cleanup()