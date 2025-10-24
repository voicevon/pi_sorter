import json
import os

# 修复后的MQTT配置
config = {
    "broker": {
        "host": "voicevon.vicp.io",
        "port": 1883,
        "username": "admin",
        "password": "admin1970",
        "client_id": "pi_sorter_integrated"
    },
    "topics": {
        "images": "pi_sorter/images",
        "status": "pi_sorter/status",
        "results": "pi_sorter/results",
        "alerts": "pi_sorter/alerts",
        "statistics": "pi_sorter/statistics",
        "heartbeat": "pi_sorter/heartbeat",
        "commands": "pi_sorter/commands"
    },
    "settings": {
        "qos": 1,
        "retain": False,
        "keepalive": 60,
        "clean_session": True,
        "reconnect_delay": 2,
        "max_reconnect_attempts": 5,
        "max_photo_size": 5242880
    },
    "metadata": {
        "include_timestamp": True,
        "include_device_info": True,
        "include_camera_settings": True
    }
}

# 确保目录存在
os.makedirs(os.path.dirname("~/pi_sorter/config/mqtt_config.json"), exist_ok=True)

# 写入配置文件
with open("~/pi_sorter/config/mqtt_config.json", "w") as f:
    json.dump(config, f, indent=2)

print("MQTT配置文件修复完成")