#!/usr/bin/env python3
"""GPIO测试脚本"""

import RPi.GPIO as GPIO
import time

def test_gpio():
    print("Testing GPIO access...")
    try:
        GPIO.setmode(GPIO.BCM)
        print("GPIO mode set to BCM")
        
        # 测试GPIO4
        GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        print("GPIO4 setup successful")
        
        # 测试GPIO5  
        GPIO.setup(5, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        print("GPIO5 setup successful")
        
        # 测试GPIO6
        GPIO.setup(6, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        print("GPIO6 setup successful")
        
        # 测试读取
        print(f"GPIO4 state: {GPIO.input(4)}")
        print(f"GPIO5 state: {GPIO.input(5)}")
        print(f"GPIO6 state: {GPIO.input(6)}")
        
        GPIO.cleanup()
        print("GPIO test passed!")
        
    except Exception as e:
        print(f"GPIO test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_gpio()