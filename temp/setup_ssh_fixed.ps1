# 将SSH公钥复制到树莓派
$pubKey = Get-Content -Path config/pi_id_ed25519.pub

Write-Host "正在将公钥复制到树莓派..."

# 在树莓派上创建.ssh目录并设置权限
# 使用密码登录进行初始配置
Write-Host "请在弹出的SSH提示中输入树莓派用户'feng'的密码"
ssh feng@192.168.121.115 "mkdir -p ~/.ssh; echo '$pubKey' >> ~/.ssh/authorized_keys; chmod 700 ~/.ssh; chmod 600 ~/.ssh/authorized_keys"

Write-Host "SSH密钥配置完成，可以尝试免密登录了。"