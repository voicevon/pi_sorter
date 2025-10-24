# 部署项目到树莓派脚本

Write-Host "开始部署项目到树莓派..."

# 创建树莓派上的项目目录
ssh -i config/pi_id_ed25519 feng@192.168.121.115 "mkdir -p ~/pi_sorter"

Write-Host "正在同步配置文件..."
# 同步配置文件
scp -i config/pi_id_ed25519 -r config/ feng@192.168.121.115:~/pi_sorter/config/

Write-Host "正在同步源代码..."
# 同步源代码
scp -i config/pi_id_ed25519 -r src/ feng@192.168.121.115:~/pi_sorter/src/

Write-Host "正在同步测试文件..."
# 同步测试文件
scp -i config/pi_id_ed25519 -r tests/ feng@192.168.121.115:~/pi_sorter/tests/

Write-Host "正在同步主程序..."
# 同步主程序文件
scp -i config/pi_id_ed25519 main.py feng@192.168.121.115:~/pi_sorter/
scp -i config/pi_id_ed25519 fix_config.py feng@192.168.121.115:~/pi_sorter/

# 在树莓派上创建必要的目录
ssh -i config/pi_id_ed25519 feng@192.168.121.115 "mkdir -p ~/pi_sorter/data ~/pi_sorter/logs"

Write-Host "项目部署完成！"
Write-Host "可以运行以下命令启动程序："
Write-Host "ssh -i config/pi_id_ed25519 feng@192.168.121.115 'python3 -u ~/pi_sorter/main.py'"