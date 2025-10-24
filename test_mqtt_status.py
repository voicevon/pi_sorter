#!/usr/bin/env python3
"""测试MQTT状态发送"""

import paho.mqtt.client as mqtt
import json
import time

client = mqtt.Client()
client.connect('voicevon.vicp.io', 1883)

status_msg = {
    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
    'client_id': 'pi_sorter_integrated',
    'status': '系统正常运行 - 编码器已初始化，摄像头就绪'
}

client.publish('pi_sorter/status', json.dumps(status_msg))
client.disconnect()
print('状态消息已发送')