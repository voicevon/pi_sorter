# Deploy project to Raspberry Pi
Write-Host "开始部署项目到树莓派..."

# Create project directory
ssh -i config/pi_id_ed25519 feng@192.168.121.115 "mkdir -p ~/pi_sorter"

Write-Host "正在同步配置文件..."
# Sync config files
scp -i config/pi_id_ed25519 -r config/ feng@192.168.121.115:~/pi_sorter/config/

Write-Host "正在同步源代码..."
# Sync source code
scp -i config/pi_id_ed25519 -r src/ feng@192.168.121.115:~/pi_sorter/src/

Write-Host "正在同步测试文件..."
# Sync test files
scp -i config/pi_id_ed25519 -r tests/ feng@192.168.121.115:~/pi_sorter/tests/

Write-Host "正在同步主程序..."
# Sync main files
scp -i config/pi_id_ed25519 main.py feng@192.168.121.115:~/pi_sorter/
scp -i config/pi_id_ed25519 fix_config.py feng@192.168.121.115:~/pi_sorter/

# Create necessary directories
ssh -i config/pi_id_ed25519 feng@192.168.121.115 "mkdir -p ~/pi_sorter/data ~/pi_sorter/logs"

Write-Host "项目部署完成！"
Write-Host "可以运行以下命令启动程序："
Write-Host "ssh -i config/pi_id_ed25519 feng@192.168.121.115 \"python3 -u ~/pi_sorter/main.py\""