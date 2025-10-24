#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的环境测试脚本
"""

print("Python环境测试开始...")

try:
    import sys
    print(f"Python版本: {sys.version}")
    
    # 测试基础模块
    import os
    print("✓ os模块可用")
    
    import json
    print("✓ json模块可用")
    
    print("✓ 基础Python环境正常")
    
except Exception as e:
    print(f"✗ 环境测试失败: {e}")

print("环境测试完成")