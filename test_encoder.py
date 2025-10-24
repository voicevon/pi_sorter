#!/usr/bin/env python3
"""编码器测试脚本"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src/external'))

import RPi.GPIO as GPIO
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_encoder():
    print("Testing encoder GPIO setup...")
    
    try:
        from encoder_module import RotaryEncoder
        print("✓ Encoder module imported successfully")
        
        # 创建编码器实例
        encoder = RotaryEncoder(pin_a=4, pin_b=5, pin_z=6)
        print("✓ Encoder instance created")
        
        # 测试位置读取
        pos = encoder.get_position()
        print(f"✓ Current position: {pos}")
        
        # 清理
        encoder.cleanup()
        print("✓ Encoder cleanup successful")
        
        return True
        
    except Exception as e:
        print(f"✗ Encoder test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_encoder()
    sys.exit(0 if success else 1)