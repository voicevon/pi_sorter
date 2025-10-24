#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import json
import time

print("正在连接MQTT代理...")
client = mqtt.Client()
client.username_pw_set('admin', 'admin1970')

try:
    client.connect('voicevon.vicp.io', 1883)
    print("已连接")
    
    # 简单订阅和监听
    def on_message(client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode('utf-8'))
            if msg.topic == 'pi_sorter/status':
                print('状态:', data.get('status', '未知'))
            elif msg.topic == 'pi_sorter/results':
                print('结果 - 项目:', data.get('item_id'), '等级:', data.get('grade'))
        except:
            print(msg.topic + ':', msg.payload.decode('utf-8', errors='ignore')[:100])
    
    client.on_message = on_message
    client.subscribe('pi_sorter/status')
    client.subscribe('pi_sorter/results')
    client.loop_start()
    
    print("监听中...")
    time.sleep(8)
    client.loop_stop()
    
except Exception as e:
    print("错误:", e)