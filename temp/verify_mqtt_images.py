#!/usr/bin/env python3
"""
验证MQTT图像接收的脚本
"""
import paho.mqtt.client as mqtt
import time
import json
import base64
import os
from datetime import datetime

def on_message(client, userdata, msg):
    """处理接收到的MQTT消息"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 收到消息:")
    print(f"主题: {msg.topic}")
    print(f"消息大小: {len(msg.payload)} 字节")
    
    # 检查是否是二进制JPEG数据
    if len(msg.payload) > 100:
        # 检查JPEG文件头
        if msg.payload[:2] == b'\xff\xd8':
            print("✓ 检测到JPEG文件头 (FFD8)")
            
            # 检查JPEG文件尾
            if msg.payload[-2:] == b'\xff\xd9':
                print("✓ 检测到JPEG文件尾 (FFD9)")
                print("✓ 这是一个完整的JPEG图像")
                
                # 保存图像文件
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"/tmp/received_image_{timestamp}.jpg"
                try:
                    with open(filename, 'wb') as f:
                        f.write(msg.payload)
                    print(f"✓ 图像已保存到: {filename}")
                    print(f"✓ 图像大小: {len(msg.payload)} 字节")
                except Exception as e:
                    print(f"✗ 保存图像失败: {e}")
            else:
                print("✗ 未检测到有效的JPEG文件尾")
        else:
            print("✗ 未检测到JPEG文件头")
            
            # 尝试解析为JSON
            try:
                data = json.loads(msg.payload.decode('utf-8'))
                print("✓ 消息是JSON格式")
                if 'content' in data and data.get('encoding') == 'base64':
                    print("✓ 包含Base64编码的图像数据")
                    # 解码并保存
                    image_data = base64.b64decode(data['content'])
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"/tmp/received_image_{timestamp}.jpg"
                    with open(filename, 'wb') as f:
                        f.write(image_data)
                    print(f"✓ Base64图像已保存到: {filename}")
            except Exception as e:
                print(f"✗ 不是有效的JSON格式: {e}")
                # 显示前50字节的十六进制
                print(f"前50字节 (hex): {msg.payload[:50].hex()}")
    else:
        print(f"消息内容: {msg.payload.decode('utf-8', errors='ignore')}")
    
    print("-" * 50)

def main():
    """主函数"""
    print("正在连接MQTT代理...")
    
    client = mqtt.Client()
    client.on_message = on_message
    
    # 设置用户名密码
    client.username_pw_set('admin', 'admin1970')
    
    try:
        # 连接到MQTT代理
        client.connect('voicevon.vicp.io', 1883, 60)
        print("✓ 已连接到MQTT代理")
        
        # 订阅图像主题
        client.subscribe('pi_sorter/images')
        print("✓ 已订阅主题: pi_sorter/images")
        
        # 订阅状态主题
        client.subscribe('pi_sorter/status')
        print("✓ 已订阅主题: pi_sorter/status")
        
        # 订阅结果主题
        client.subscribe('pi_sorter/results')
        print("✓ 已订阅主题: pi_sorter/results")
        
        # 开始循环
        client.loop_start()
        print("\n正在监听MQTT消息，按 Ctrl+C 退出...")
        print("等待接收图像数据...\n")
        
        # 运行30秒
        time.sleep(30)
        
    except KeyboardInterrupt:
        print("\n用户中断，正在退出...")
    except Exception as e:
        print(f"错误: {e}")
    finally:
        client.loop_stop()
        client.disconnect()
        print("已断开连接")

if __name__ == "__main__":
    main()