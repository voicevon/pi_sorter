#!/usr/bin/env python3
"""
测试当前发送的二进制图像格式
"""
import paho.mqtt.client as mqtt
import time
import json
import base64
import struct

def on_message(client, userdata, msg):
    print(f"\n=== 收到MQTT消息 ===")
    print(f"主题: {msg.topic}")
    print(f"消息大小: {len(msg.payload)} 字节")
    
    # 检查是否为JPEG文件
    if len(msg.payload) > 100:  # 可能是图像
        # JPEG文件头: FF D8
        # JPEG文件尾: FF D9
        jpg_header = msg.payload[:2]
        jpg_footer = msg.payload[-2:]
        
        print(f"JPEG文件头: {jpg_header.hex()} (期望: ffd8)")
        print(f"JPEG文件尾: {jpg_footer.hex()} (期望: ffd9)")
        
        if jpg_header == b'\xff\xd8' and jpg_footer == b'\xff\xd9':
            print("✅ 这是一个有效的JPEG文件")
            
            # 尝试保存为文件
            filename = f"/tmp/received_image_{int(time.time())}.jpg"
            try:
                with open(filename, 'wb') as f:
                    f.write(msg.payload)
                print(f"✅ 图像已保存到: {filename}")
            except Exception as e:
                print(f"保存文件失败: {e}")
        else:
            print("❌ 这不是一个有效的JPEG文件")
            
            # 检查是否为JSON格式
            try:
                json_data = json.loads(msg.payload.decode('utf-8'))
                print("📄 这是一个JSON消息")
                if 'content' in json_data and json_data.get('encoding') == 'base64':
                    print("📄 JSON中包含Base64编码的图像")
                    # 解码Base64
                    image_data = base64.b64decode(json_data['content'])
                    print(f"解码后的图像大小: {len(image_data)} 字节")
                    
                    # 检查解码后的数据
                    jpg_header = image_data[:2]
                    jpg_footer = image_data[-2:]
                    print(f"解码后的JPEG文件头: {jpg_header.hex()}")
                    print(f"解码后的JPEG文件尾: {jpg_footer.hex()}")
                    
                    if jpg_header == b'\xff\xd8' and jpg_footer == b'\xff\xd9':
                        print("✅ 解码后的数据是有效的JPEG文件")
                        filename = f"/tmp/received_image_{int(time.time())}.jpg"
                        with open(filename, 'wb') as f:
                            f.write(image_data)
                        print(f"✅ 解码后的图像已保存到: {filename}")
                    else:
                        print("❌ 解码后的数据不是有效的JPEG文件")
                else:
                    print(f"JSON内容: {json.dumps(json_data, indent=2, ensure_ascii=False)[:500]}...")
            except (json.JSONDecodeError, UnicodeDecodeError):
                print("❌ 既不是JPEG也不是JSON格式")
                print(f"前50字节 (hex): {msg.payload[:50].hex()}")
                print(f"前50字节 (ascii, 忽略错误): {msg.payload[:50].decode('ascii', errors='ignore')}")
    else:
        # 小消息，可能是文本
        try:
            text_content = msg.payload.decode('utf-8')
            print(f"📄 文本消息: {text_content}")
        except UnicodeDecodeError:
            print("❌ 无法解码为文本")
            print(f"内容 (hex): {msg.payload[:50].hex()}")

def main():
    client = mqtt.Client()
    client.on_message = on_message
    
    try:
        print("连接到MQTT代理 voicevon.vicp.io:1883...")
        client.connect("voicevon.vicp.io", 1883, 60)
        
        client.loop_start()
        print("开始监听消息，按 Ctrl+C 退出...")
        
        # 订阅相关主题
        client.subscribe("pi_sorter/images")
        client.subscribe("pi_sorter/status")
        client.subscribe("pi_sorter/results")
        
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