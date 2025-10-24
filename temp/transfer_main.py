import base64
import subprocess
import yaml
import os

# 读取配置文件
def get_raspberry_pi_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'integrated_config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config.get('raspberry_pi', {})

# 获取树莓派配置信息
pi_config = get_raspberry_pi_config()
pi_host = pi_config.get('host', '192.168.2.192')
pi_username = pi_config.get('username', 'feng')
pi_ssh_key = pi_config.get('ssh_key', 'config/pi_id_ed25519')

# 读取main.py内容并编码
with open('main.py', 'rb') as f:
    encoded = base64.b64encode(f.read()).decode('utf-8')

# 创建SSH命令
ssh_command = f'ssh -i {pi_ssh_key} {pi_username}@{pi_host} "echo \"{encoded}\" | base64 -d > ~/pi_sorter/main.py"'

# 执行命令
print(f"执行命令: {ssh_command[:50]}...")
subprocess.run(ssh_command, shell=True)
print("文件传输完成")