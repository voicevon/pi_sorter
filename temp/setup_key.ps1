# Simple SSH key setup
Write-Host "Setting up SSH key..."

# Create .ssh directory
ssh feng@192.168.121.115 "mkdir -p ~/.ssh"

# Add public key
ssh feng@192.168.121.115 "echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPuuGe+JXn4d0uLsx70CiRnRAa7EeDDQ8NNVx+nLe8kG feng@DESKTOP-DG0E00H' >> ~/.ssh/authorized_keys"

# Set permissions
ssh feng@192.168.121.115 "chmod 700 ~/.ssh; chmod 600 ~/.ssh/authorized_keys"

Write-Host "Setup complete"