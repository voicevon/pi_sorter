#!/usr/bin/env python3
"""
简单的 MQTT 连接测试脚本，用于在树莓派上验证到外部代理的连通性与认证。
运行方式：python3 tests/mqtt_conn_test.py
"""

import time
import sys

try:
    import paho.mqtt.client as mqtt
except Exception as e:
    print("paho-mqtt 未安装:", e)
    sys.exit(1)

HOST = "voicevon.vicp.io"
PORT = 1883
USERNAME = "admin"
PASSWORD = "admin1970"

connected_rc = None
is_connected = False

def on_connect(client, userdata, flags, rc, properties=None):
    global connected_rc, is_connected
    connected_rc = rc
    is_connected = (rc == 0)
    print(f"on_connect rc={rc}")

client = mqtt.Client(client_id="pi_sorter_conn_test")
client.username_pw_set(USERNAME, PASSWORD)
client.on_connect = on_connect

print(f"尝试连接 {HOST}:{PORT} ...")
try:
    client.connect(HOST, PORT, keepalive=10)
    client.loop_start()
    start = time.time()
    while connected_rc is None and time.time() - start < 8:
        time.sleep(0.2)
    client.loop_stop()
except Exception as e:
    print("connect 异常:", e)
    sys.exit(2)

print("连接结果:")
print("  rc=", connected_rc)
print("  connected=", is_connected)

if not is_connected:
    print("连接失败，可能原因：端口不可达/用户名密码错误/需要TLS或WebSocket。")
    sys.exit(3)
else:
    print("连接成功。尝试发布测试消息...")
    try:
        r = client.publish("pi_sorter/status", "conn_test_ok", qos=0, retain=False)
        print("publish rc=", getattr(r, 'rc', r))
    except Exception as e:
        print("publish 异常:", e)
        sys.exit(4)
    print("测试完成。")