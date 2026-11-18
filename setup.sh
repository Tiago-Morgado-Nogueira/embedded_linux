#!/bin/bash

# Parar o script imediatamente se ocorrer algum erro
set -e

echo "=== A iniciar o setup unificado do projeto Embedded Linux & Hardware ==="

# 1. Atualizar pacotes e instalar dependências do sistema operativo (Câmara e Servos)
echo "[1/4] A instalar pacotes do sistema (python3-pip, python3-venv, python3-picamera2, gpiozero, lgpio)..."
sudo apt update
sudo apt install -y python3-pip python3-venv python3-picamera2 python3-gpiozero python3-lgpio

# 2. Criar o ambiente virtual na RAIZ do repositório (~/embedded_linux/venv)
echo "[2/4] A criar o ambiente virtual (venv) unificado na raiz com --system-site-packages..."
if [ ! -d "venv" ]; then
    python3 -m venv --system-site-packages venv
    echo "Ambiente virtual criado com sucesso na raiz."
else
    echo "O ambiente virtual 'venv' já existe na raiz. A saltar criação."
fi

# 3. Ativar o ambiente virtual e instalar dependências do Python
echo "[3/4] A instalar dependências Python (Flask, OpenCV)..."
source venv/bin/activate
pip install --upgrade pip
pip install flask opencv-python

echo "[4/4] Setup concluído com sucesso!"
echo "--------------------------------------------------------"
echo "Podes testar a câmara com:"
echo "  python3 Computer_Vision/color_detection/color_stream.py"
echo "Podes testar os servos com:"
echo "  python3 Components_testing/Servo_mg995_test/servo_infinite.py"
echo "--------------------------------------------------------"