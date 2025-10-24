@echo off
echo Setting up SSH key...
echo Please enter password when prompted

rem 创建树莓派上的.ssh目录
ssh feng@192.168.121.115 "mkdir -p ~/.ssh"

rem 将公钥添加到authorized_keys
ssh feng@192.168.121.115 "echo ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPuuGe+JXn4d0uLsx70CiRnRAa7EeDDQ8NNVx+nLe8kG feng@DESKTOP-DG0E00H >> ~/.ssh/authorized_keys"

rem 设置权限
ssh feng@192.168.121.115 "chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"

echo SSH setup complete