# Deploy project to Raspberry Pi
Write-Host "Deploying project to Raspberry Pi..."

# Create project directory
ssh -i config/pi_id_ed25519 feng@192.168.121.115 "mkdir -p ~/pi_sorter"

# Sync config files
scp -i config/pi_id_ed25519 -r config/ feng@192.168.121.115:~/pi_sorter/config/

# Sync source code
scp -i config/pi_id_ed25519 -r src/ feng@192.168.121.115:~/pi_sorter/src/

# Sync test files
scp -i config/pi_id_ed25519 -r tests/ feng@192.168.121.115:~/pi_sorter/tests/

# Sync main files
scp -i config/pi_id_ed25519 main.py feng@192.168.121.115:~/pi_sorter/
scp -i config/pi_id_ed25519 fix_config.py feng@192.168.121.115:~/pi_sorter/

# Create necessary directories
ssh -i config/pi_id_ed25519 feng@192.168.121.115 "mkdir -p ~/pi_sorter/data ~/pi_sorter/logs"

Write-Host "Deployment complete!"