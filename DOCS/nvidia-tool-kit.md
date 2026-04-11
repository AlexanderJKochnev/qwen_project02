# ПРОВЕРКА И НАСТРОЙКА nvidia-tool-kit
1. cat /etc/nvidia-container-runtime/config.toml
2. nvidia-ctk --version
3. nvidia-ctk cdi generate --output=/dev/stdout
4. sudo apt update (сначала лучше не делать)
5. sudo apt install -y libnvidia-encode-550 libnvidia-compute-550 libnvidia-rtcore-550 libnvidia-ml-550
## обновление только драйверов nvidia-toolkit
6. sudo apt install --only-upgrade nvidia-container-toolkit nvidia-container-toolkit-base libnvidia-container1 libnvidia-container-tools 
7. sudo nvidia-ctk runtime configure --runtime=docker 
8. sudo systemctl restart docker



