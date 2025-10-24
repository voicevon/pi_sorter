#!/usr/bin/env python3
"""
检查MQTT状态和分拣结果的脚本
"""
import paho.mqtt.client as mqtt
import json
import time

def on_message(client, userdata, msg):
    """处理接收到的MQTT消息"""
    try:
        data = json.loads(msg.payload.decode('utf-8'))
        if msg.topic == 'pi_sorter/status':
            print(f"状态更新: {data.get('status', '未知状态')}")
        elif msg.topic == 'pi_sorter/results':
            item_id = data.get('item_id', '未知')
            grade = data.get('grade', '未知')
            length = data.get('length', '未知')
            diameter = data.get('diameter', '未知')
            print(f"分拣结果 - 项目ID: {item_id}, 等级: {grade}, 长度: {length}mm, 直径: {diameter}mm")
    except Exception as e:
        print(f"{msg.topic}: {msg.payload.decode('utf-8', errors='ignore')}")

def main():
    """主函数"""
    print("正在连接MQTT代理检查状态和结果...")
    
    client = mqtt.Client()
    client.on_message = on_message
    
    # 设置用户名密码
    client.username_pw_set('admin', 'admin1970')
    
    try:
        # 连接到MQTT代理
        client.connect('voicevon.vicp.io', 1883, 60)
        print("✓ 已连接到MQTT代理")
        
        # 订阅状态主题
        client.subscribe('pi_sorter/status')
        print("✓ 已订阅主题: pi_sorter/status")
        
        # 订阅结果主题
        client.subscribe('pi_sorter/results')
        print("✓ 已订阅主题: pi_sorter/results")
        
        # 开始循环
        client.loop_start()
        print("\n正在监听状态和结果消息，等待10秒...")
        
        # 运行10秒
        time.sleep(10)
        
    except Exception as e:
        print(f"错误: {e}")
    finally:
        client.loop_stop()
        client.disconnect()
        print("已断开连接")

if __name__ == "__main__":
    main()