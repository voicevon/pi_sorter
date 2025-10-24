#!/usr/bin/env python3
"""
编码器读取模块 - 使用lgpio库处理旋转编码器的A/B相和Z相信号
用于替代RPi.GPIO，解决边沿检测问题
"""

import lgpio as GPIO
import threading
import time
import logging
from typing import Optional, Callable

class RotaryEncoderLGPIO:
    """使用lgpio的旋转编码器控制类"""
    
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
        
        # 打开GPIO芯片
        self.chip = GPIO.gpiochip_open(0)
        if self.chip < 0:
            raise RuntimeError(f"无法打开GPIO芯片: {self.chip}")
        
        # 配置引脚为输入模式
        GPIO.gpio_claim_input(self.chip, self.pin_a, GPIO.SET_PULL_UP)
        GPIO.gpio_claim_input(self.chip, self.pin_b, GPIO.SET_PULL_UP)
        GPIO.gpio_claim_input(self.chip, self.pin_z, GPIO.SET_PULL_UP)
        
        # 设置边沿检测
        try:
            GPIO.gpio_claim_alert(self.chip, self.pin_a, GPIO.RISING_EDGE, lFlags=0)
            GPIO.gpio_claim_alert(self.chip, self.pin_z, GPIO.FALLING_EDGE, lFlags=0)
            
            # 启动监控线程
            self.monitor_thread = threading.Thread(target=self._monitor_gpio, daemon=True)
            self.monitor_thread.start()
            
        except Exception as e:
            GPIO.gpiochip_close(self.chip)
            raise RuntimeError(f"GPIO边沿检测设置失败: {e}")
    
    def _monitor_gpio(self):
        """监控GPIO状态变化的线程"""
        while self.is_running or not hasattr(self, '_stop_monitor'):
            try:
                # 检查A相变化
                if GPIO.gpio_read(self.chip, self.pin_a) == 0:  # 假设低电平触发
                    self._handle_encoder_change()
                
                # 检查Z相变化（归零）
                if GPIO.gpio_read(self.chip, self.pin_z) == 0:
                    self._handle_zero()
                
                time.sleep(0.001)  # 1ms轮询间隔
                
            except Exception as e:
                self.logger.error(f"GPIO监控错误: {e}")
                break
    
    def _handle_encoder_change(self):
        """处理编码器信号变化"""
        a_state = GPIO.gpio_read(self.chip, self.pin_a)
        b_state = GPIO.gpio_read(self.chip, self.pin_b)
        
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
    
    def _handle_zero(self):
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
        
        # 停止监控线程
        if hasattr(self, 'monitor_thread'):
            self._stop_monitor = True
            self.monitor_thread.join(timeout=1.0)
    
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
        
        if hasattr(self, 'chip') and self.chip >= 0:
            try:
                GPIO.gpio_free(self.chip, self.pin_a)
                GPIO.gpio_free(self.chip, self.pin_b)
                GPIO.gpio_free(self.chip, self.pin_z)
                GPIO.gpiochip_close(self.chip)
                self.logger.info("编码器GPIO资源已清理")
            except Exception as e:
                self.logger.error(f"GPIO清理错误: {e}")
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.cleanup()