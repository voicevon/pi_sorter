#!/usr/bin/env python3
"""测试lgpio编码器模块"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from external.encoder_module_lgpio import RotaryEncoderLGPIO
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    print('正在初始化编码器...')
    encoder = RotaryEncoderLGPIO(15, 18, 14)
    print('编码器初始化成功！')
    
    # 测试位置读取
    print(f'当前位置: {encoder.get_position()}')
    
    # 启动编码器
    encoder.start()
    print('编码器已启动，等待10秒...')
    
    # 监控10秒
    for i in range(10):
        pos = encoder.get_position()
        print(f'位置 {i}: {pos}')
        time.sleep(1)
    
    encoder.cleanup()
    print('测试完成！')
    
except Exception as e:
    print(f'错误: {e}')
    import traceback
    traceback.print_exc()