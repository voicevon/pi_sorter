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

# 创建一个简单的测试Python代码
test_code = 'print("Hello from main.py")\n'

# 使用echo和base64编码传输
# 这里我们使用Python的字符串处理来避免PowerShell的引号问题
command = f'''ssh -i {pi_ssh_key} {pi_username}@{pi_host} "cd ~/pi_sorter && \n'''
command += '''echo UHJpbnQgKGdldCAiSGVsbG8gZnJvbSBtYWluLnB5IiApCgo= | base64 -d > main.py && \n'''
command += '''cat main.py && \n'''
command += '''python3 -u main.py"'''

print("执行命令...")
result = subprocess.run(command, shell=True, capture_output=True, text=True)
print("标准输出:")
print(result.stdout)
print("标准错误:")
print(result.stderr)