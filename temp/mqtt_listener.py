#!/usr/bin/env python3
"""
简单的MQTT监听器，用于调试图像数据格式
"""
import paho.mqtt.client as mqtt
import time
import sys

def on_message(client, userdata, msg):
    print(f"\n=== 收到MQTT消息 ===")
    print(f"主题: {msg.topic}")
    print(f"消息大小: {len(msg.payload)} 字节")
    
    # 检查消息类型
    if len(msg.payload) > 100:
        # 大消息，可能是图像
        print("消息类型: 可能是图像数据")
        print(f"前20字节 (hex): {msg.payload[:20].hex()}")
        print(f"JPEG文件头检查: {msg.payload[:2].hex()} (期望: ffd8)")
        print(f"JPEG文件尾检查: {msg.payload[-2:].hex()} (期望: ffd9)")
    else:
        # 小消息，可能是文本
        print("消息类型: 文本消息")
        try:
            text_content = msg.payload.decode('utf-8')
            print(f"文本内容: {text_content[:200]}")
        except UnicodeDecodeError:
            print("无法解码为文本，可能是二进制数据")
            print(f"内容 (hex): {msg.payload[:50].hex()}")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("已连接到MQTT代理")
        client.subscribe("pi_sorter/images")
        print("已订阅 pi_sorter/images 主题")
    else:
        print(f"连接失败，错误码: {rc}")

def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        print("连接到MQTT代理 voicevon.vicp.io:1883...")
        client.connect("voicevon.vicp.io", 1883, 60)
        
        client.loop_start()
        print("开始监听消息，按 Ctrl+C 退出...")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n正在退出...")
        client.loop_stop()
        client.disconnect()
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    main()