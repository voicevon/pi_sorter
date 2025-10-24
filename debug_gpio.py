#!/usr/bin/env python3
"""GPIO调试脚本"""

import RPi.GPIO as GPIO
import time

def test_gpio_pins():
    """测试各个GPIO引脚"""
    print("=== GPIO引脚测试 ===")
    
    # 测试的引脚
    test_pins = [4, 5, 6, 17, 27]
    
    try:
        GPIO.setmode(GPIO.BCM)
        print("✓ GPIO模式设置为BCM")
        
        for pin in test_pins:
            try:
                print(f"\n测试GPIO{pin}:")
                
                # 设置为输入模式
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                print(f"  ✓ GPIO{pin}设置为输入模式")
                
                # 读取当前状态
                state = GPIO.input(pin)
                print(f"  ✓ GPIO{pin}当前状态: {state}")
                
                # 尝试添加边沿检测
                def dummy_callback(channel):
                    print(f"  GPIO{pin}中断触发")
                
                GPIO.add_event_detect(pin, GPIO.BOTH, callback=dummy_callback)
                print(f"  ✓ GPIO{pin}边沿检测添加成功")
                
                # 移除检测
                GPIO.remove_event_detect(pin)
                print(f"  ✓ GPIO{pin}边沿检测移除成功")
                
            except Exception as e:
                print(f"  ✗ GPIO{pin}测试失败: {e}")
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"✗ GPIO初始化失败: {e}")
        
    finally:
        try:
            GPIO.cleanup()
            print("✓ GPIO清理完成")
        except:
            print("✗ GPIO清理失败")

def check_pin_usage():
    """检查引脚使用情况"""
    print("\n=== 引脚使用情况检查 ===")
    
    # 检查设备树覆盖
    try:
        import subprocess
        result = subprocess.run(['gpio', 'readall'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ gpio命令可用")
            print(result.stdout[:500])  # 只显示前500字符
        else:
            print("✗ gpio命令不可用")
    except Exception as e:
        print(f"✗ 无法检查引脚使用情况: {e}")

if __name__ == "__main__":
    test_gpio_pins()
    check_pin_usage()