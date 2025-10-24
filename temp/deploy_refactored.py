#!/usr/bin/env python3
"""
Pi Sorter - 部署脚本
用于在树莓派上部署和运行重构后的系统
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime
from typing import Dict, Any, Optional

# 项目配置
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
REMOTE_PROJECT_DIR = "~/pi_sorter"
REMOTE_CONFIG_DIR = f"{REMOTE_PROJECT_DIR}/config"
REMOTE_SRC_DIR = f"{REMOTE_PROJECT_DIR}/src/external"
REMOTE_LOGS_DIR = f"{REMOTE_PROJECT_DIR}/logs"

# 默认配置
DEFAULT_CONFIG = {
    "raspberry_pi_ip": "192.168.121.115",  # 需要根据实际情况修改
    "ssh_key": "config/pi_id_ed25519",
    "ssh_user": "feng",
    "mqtt_broker": "voicevon.vicp.io",
    "mqtt_port": 1883,
    "mqtt_username": "admin",
    "mqtt_password": "admin1970"
}


class PiSorterDeployment:
    """Pi Sorter部署管理器"""
    
    def __init__(self, config_file: str = "deploy_config.json"):
        """初始化部署管理器"""
        self.config_file = config_file
        self.config = self._load_config()
        self.raspberry_pi_ip = self.config.get('raspberry_pi_ip', DEFAULT_CONFIG['raspberry_pi_ip'])
        self.ssh_key = self.config.get('ssh_key', DEFAULT_CONFIG['ssh_key'])
        self.ssh_user = self.config.get('ssh_user', DEFAULT_CONFIG['ssh_user'])
        
    def _load_config(self) -> Dict[str, Any]:
        """加载部署配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  加载配置文件失败: {e}，使用默认配置")
                return DEFAULT_CONFIG.copy()
        else:
            return DEFAULT_CONFIG.copy()
            
    def save_config(self):
        """保存部署配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"✅ 配置已保存到: {self.config_file}")
        except Exception as e:
            print(f"❌ 保存配置失败: {e}")
            
    def _run_ssh_command(self, command: str, timeout: int = 30) -> tuple:
        """运行SSH命令"""
        ssh_command = [
            "ssh",
            "-i", self.ssh_key,
            "-o", "ConnectTimeout=10",
            "-o", "StrictHostKeyChecking=no",
            f"{self.ssh_user}@{self.raspberry_pi_ip}",
            command
        ]
        
        try:
            result = subprocess.run(ssh_command, capture_output=True, text=True, timeout=timeout)
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "命令执行超时"
        except Exception as e:
            return False, "", str(e)
            
    def _run_scp_command(self, local_path: str, remote_path: str, direction: str = "upload") -> bool:
        """运行SCP命令"""
        if direction == "upload":
            scp_command = [
                "scp",
                "-i", self.ssh_key,
                "-o", "ConnectTimeout=10",
                "-o", "StrictHostKeyChecking=no",
                local_path,
                f"{self.ssh_user}@{self.raspberry_pi_ip}:{remote_path}"
            ]
        else:  # download
            scp_command = [
                "scp",
                "-i", self.ssh_key,
                "-o", "ConnectTimeout=10",
                "-o", "StrictHostKeyChecking=no",
                f"{self.ssh_user}@{self.raspberry_pi_ip}:{remote_path}",
                local_path
            ]
            
        try:
            result = subprocess.run(scp_command, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                print(f"❌ SCP命令失败: {result.stderr}")
                return False
            return True
        except Exception as e:
            print(f"❌ SCP命令异常: {e}")
            return False
            
    def check_connection(self) -> bool:
        """检查树莓派连接"""
        print(f"🔍 检查连接到树莓派 {self.raspberry_pi_ip}...")
        
        success, stdout, stderr = self._run_ssh_command("hostname && uptime")
        if success:
            print(f"✅ 连接成功")
            print(f"主机名: {stdout.strip()}")
            return True
        else:
            print(f"❌ 连接失败: {stderr}")
            return False
            
    def setup_remote_environment(self) -> bool:
        """设置远程环境"""
        print("🔧 设置远程环境...")
        
        commands = [
            f"mkdir -p {REMOTE_PROJECT_DIR}",
            f"mkdir -p {REMOTE_CONFIG_DIR}",
            f"mkdir -p {REMOTE_SRC_DIR}",
            f"mkdir -p {REMOTE_LOGS_DIR}",
            f"ls -la {REMOTE_PROJECT_DIR}"
        ]
        
        for cmd in commands:
            success, stdout, stderr = self._run_ssh_command(cmd)
            if not success:
                print(f"❌ 命令失败: {cmd}")
                print(f"错误: {stderr}")
                return False
                
        print("✅ 远程环境设置完成")
        return True
        
    def deploy_files(self) -> bool:
        """部署文件到树莓派"""
        print("📁 部署文件到树莓派...")
        
        # 需要部署的文件列表
        files_to_deploy = [
            # 配置文件
            ("config/integrated_config.yaml", f"{REMOTE_CONFIG_DIR}/"),
            ("config/mqtt_config.json", f"{REMOTE_CONFIG_DIR}/"),
            
            # 重构后的模块
            ("src/external/config_manager_refactored.py", f"{REMOTE_SRC_DIR}/"),
            ("src/external/picamera2_module_refactored.py", f"{REMOTE_SRC_DIR}/"),
            ("src/external/mqtt_manager_refactored.py", f"{REMOTE_SRC_DIR}/"),
            ("src/external/encoder_module_refactored.py", f"{REMOTE_SRC_DIR}/"),
            ("src/external/system_monitor.py", f"{REMOTE_SRC_DIR}/"),
            ("src/external/integrated_sorting_system.py", f"{REMOTE_SRC_DIR}/"),
            
            # 主程序
            ("main_refactored.py", f"{REMOTE_PROJECT_DIR}/"),
            
            # 依赖文件
            ("requirements.txt", f"{REMOTE_PROJECT_DIR}/"),
        ]
        
        success_count = 0
        for local_file, remote_dir in files_to_deploy:
            local_path = os.path.join(PROJECT_ROOT, local_file)
            if not os.path.exists(local_path):
                print(f"⚠️  文件不存在，跳过: {local_file}")
                continue
                
            print(f"上传 {local_file}...")
            if self._run_scp_command(local_path, remote_dir):
                success_count += 1
                print(f"✅ {local_file} 上传成功")
            else:
                print(f"❌ {local_file} 上传失败")
                
        print(f"📊 文件部署完成: {success_count}/{len(files_to_deploy)} 个文件成功")
        return success_count > 0
        
    def install_dependencies(self) -> bool:
        """安装依赖"""
        print("📦 安装依赖...")
        
        commands = [
            f"cd {REMOTE_PROJECT_DIR} && python3 -m pip install --user -r requirements.txt",
            "python3 -c \"import picamera2; print('Picamera2版本:', picamera2.__version__)\"",
            "python3 -c \"import paho.mqtt.client; print('MQTT客户端已安装')\"",
        ]
        
        for cmd in commands:
            print(f"执行: {cmd}")
            success, stdout, stderr = self._run_ssh_command(cmd, timeout=120)
            if success:
                print(f"✅ 命令成功")
                if stdout:
                    print(f"输出: {stdout.strip()}")
            else:
                print(f"⚠️  命令失败: {stderr}")
                
        print("✅ 依赖安装完成")
        return True
        
    def configure_system(self) -> bool:
        """配置系统"""
        print("⚙️  配置系统...")
        
        # 配置摄像头
        camera_config_commands = [
            "sudo bash -c 'echo \"start_x=1\" >> /boot/firmware/config.txt'",
            "sudo bash -c 'echo \"gpu_mem=128\" >> /boot/firmware/config.txt'",
            "sudo bash -c 'echo \"# 手动启用CSI摄像头\" >> /boot/firmware/config.txt'",
            "cat /boot/firmware/config.txt | grep -i camera"
        ]
        
        print("配置摄像头...")
        for cmd in camera_config_commands:
            success, stdout, stderr = self._run_ssh_command(cmd)
            if success and stdout:
                print(f"输出: {stdout.strip()}")
                
        # 设置文件权限
        permission_commands = [
            f"chmod +x {REMOTE_PROJECT_DIR}/main_refactored.py",
            f"chmod 600 {REMOTE_CONFIG_DIR}/pi_id_ed25519",
            f"ls -la {REMOTE_PROJECT_DIR}/"
        ]
        
        print("设置文件权限...")
        for cmd in permission_commands:
            self._run_ssh_command(cmd)
            
        print("✅ 系统配置完成")
        return True
        
    def test_deployment(self) -> bool:
        """测试部署"""
        print("🧪 测试部署...")
        
        # 测试Python导入
        test_commands = [
            f"cd {REMOTE_PROJECT_DIR} && python3 -c \"import sys; print('Python版本:', sys.version)\"",
            f"cd {REMOTE_PROJECT_DIR} && python3 -c \"from src.external.config_manager_refactored import ConfigManager; print('配置管理器导入成功')\"",
            f"cd {REMOTE_PROJECT_DIR} && python3 -c \"from src.external.picamera2_module_refactored import CSICameraManager; print('摄像头管理器导入成功')\"",
            f"cd {REMOTE_PROJECT_DIR} && python3 -c \"from src.external.mqtt_manager_refactored import SorterMQTTManager; print('MQTT管理器导入成功')\"",
        ]
        
        for cmd in test_commands:
            print(f"测试: {cmd}")
            success, stdout, stderr = self._run_ssh_command(cmd)
            if success:
                print(f"✅ 测试通过")
                if stdout:
                    print(f"输出: {stdout.strip()}")
            else:
                print(f"❌ 测试失败: {stderr}")
                return False
                
        print("✅ 部署测试完成")
        return True
        
    def start_system(self) -> bool:
        """启动系统"""
        print("🚀 启动Pi Sorter系统...")
        
        # 检查是否已有进程在运行
        check_command = "ps aux | grep -E '(main_refactored|integrated_system)' | grep -v grep"
        success, stdout, stderr = self._run_ssh_command(check_command)
        
        if stdout.strip():
            print("⚠️  检测到已有进程在运行:")
            print(stdout)
            response = input("是否终止现有进程并重新启动? (y/N): ")
            if response.lower() == 'y':
                # 终止现有进程
                kill_command = "pkill -f 'main_refactored|integrated_system'"
                self._run_ssh_command(kill_command)
                time.sleep(2)
            else:
                print("取消启动")
                return False
                
        # 启动系统
        start_command = f"cd {REMOTE_PROJECT_DIR} && nohup python3 -u main_refactored.py > logs/system.log 2>&1 &"
        success, stdout, stderr = self._run_ssh_command(start_command)
        
        if success:
            print("✅ 系统启动命令已发送")
            
            # 等待系统启动
            time.sleep(3)
            
            # 检查系统状态
            status_command = "ps aux | grep main_refactored | grep -v grep"
            success, stdout, stderr = self._run_ssh_command(status_command)
            
            if success and stdout.strip():
                print("✅ 系统已成功启动")
                print(f"进程信息: {stdout.strip()}")
                
                # 显示日志
                log_command = f"tail -n 20 {REMOTE_LOGS_DIR}/system.log"
                success, stdout, stderr = self._run_ssh_command(log_command)
                if success and stdout:
                    print("\n📋 最近日志:")
                    print(stdout)
                    
                return True
            else:
                print("❌ 系统启动失败，请检查日志")
                return False
        else:
            print(f"❌ 启动失败: {stderr}")
            return False
            
    def stop_system(self) -> bool:
        """停止系统"""
        print("🛑 停止Pi Sorter系统...")
        
        # 查找并终止进程
        commands = [
            "pkill -f 'main_refactored'",
            "pkill -f 'integrated_system'",
            "pkill -f 'python3.*pi_sorter'"
        ]
        
        for cmd in commands:
            self._run_ssh_command(cmd)
            
        time.sleep(2)
        
        # 验证进程已终止
        check_command = "ps aux | grep -E '(main_refactored|integrated_system)' | grep -v grep"
        success, stdout, stderr = self._run_ssh_command(check_command)
        
        if not stdout.strip():
            print("✅ 系统已成功停止")
            return True
        else:
            print("⚠️  仍有进程在运行，尝试强制终止")
            self._run_ssh_command("pkill -9 -f 'main_refactored|integrated_system'")
            return True
            
    def check_system_status(self) -> bool:
        """检查系统状态"""
        print("📊 检查系统状态...")
        
        commands = [
            "ps aux | grep -E '(main_refactored|integrated_system)' | grep -v grep",
            f"tail -n 10 {REMOTE_LOGS_DIR}/system.log",
            "systemctl status pigpiod 2>/dev/null || echo 'pigpiod 未运行'",
            "free -h",
            "df -h /"
        ]
        
        for cmd in commands:
            print(f"\n执行: {cmd}")
            success, stdout, stderr = self._run_ssh_command(cmd)
            if success and stdout:
                print(stdout)
            if stderr:
                print(f"错误: {stderr}")
                
        return True
        
    def view_logs(self, lines: int = 50) -> bool:
        """查看日志"""
        print(f"📋 查看最近 {lines} 行日志...")
        
        log_command = f"tail -n {lines} {REMOTE_LOGS_DIR}/system.log"
        success, stdout, stderr = self._run_ssh_command(log_command)
        
        if success and stdout:
            print("="*60)
            print(stdout)
            print("="*60)
        else:
            print(f"❌ 无法读取日志: {stderr}")
            
        return success
        
    def run_tests(self) -> bool:
        """运行测试"""
        print("🧪 运行测试套件...")
        
        # 上传测试文件
        test_files = [
            ("tests/test_comprehensive.py", f"{REMOTE_PROJECT_DIR}/tests/"),
            ("tests/test_environment.py", f"{REMOTE_PROJECT_DIR}/tests/"),
        ]
        
        for local_file, remote_dir in test_files:
            local_path = os.path.join(PROJECT_ROOT, local_file)
            if os.path.exists(local_path):
                print(f"上传测试文件: {local_file}")
                self._run_scp_command(local_path, remote_dir)
                
        # 运行测试
        test_command = f"cd {REMOTE_PROJECT_DIR} && python3 -m pytest tests/test_comprehensive.py -v"
        success, stdout, stderr = self._run_ssh_command(test_command, timeout=300)
        
        if success:
            print("✅ 测试运行完成")
            if stdout:
                print("\n测试结果:")
                print(stdout)
        else:
            print(f"❌ 测试失败: {stderr}")
            
        return success


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Pi Sorter 部署脚本')
    parser.add_argument('--ip', type=str, help='树莓派IP地址')
    parser.add_argument('--deploy', action='store_true', help='部署系统')
    parser.add_argument('--start', action='store_true', help='启动系统')
    parser.add_argument('--stop', action='store_true', help='停止系统')
    parser.add_argument('--status', action='store_true', help='查看系统状态')
    parser.add_argument('--logs', type=int, nargs='?', const=50, help='查看日志')
    parser.add_argument('--test', action='store_true', help='运行测试')
    parser.add_argument('--full-deploy', action='store_true', help='完整部署流程')
    parser.add_argument('--config', type=str, default='deploy_config.json', help='配置文件')
    
    args = parser.parse_args()
    
    # 创建部署管理器
    deployment = PiSorterDeployment(args.config)
    
    # 更新IP地址（如果提供）
    if args.ip:
        deployment.raspberry_pi_ip = args.ip
        
    # 检查连接
    if not deployment.check_connection():
        print("❌ 无法连接到树莓派，请检查网络和配置")
        return 1
        
    # 执行操作
    if args.full_deploy:
        print("🚀 开始完整部署流程...")
        
        steps = [
            ("设置远程环境", deployment.setup_remote_environment),
            ("部署文件", deployment.deploy_files),
            ("安装依赖", deployment.install_dependencies),
            ("配置系统", deployment.configure_system),
            ("测试部署", deployment.test_deployment),
        ]
        
        for step_name, step_func in steps:
            print(f"\n{'='*60}")
            print(f"📍 {step_name}")
            print('='*60)
            
            if not step_func():
                print(f"❌ {step_name}失败，部署中止")
                return 1
                
        print("\n🎉 完整部署流程完成！")
        
    elif args.deploy:
        deployment.deploy_files()
        
    elif args.start:
        deployment.start_system()
        
    elif args.stop:
        deployment.stop_system()
        
    elif args.status:
        deployment.check_system_status()
        
    elif args.logs:
        deployment.view_logs(args.logs)
        
    elif args.test:
        deployment.run_tests()
        
    else:
        parser.print_help()
        
    return 0


if __name__ == '__main__':
    sys.exit(main())