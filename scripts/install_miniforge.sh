#!/bin/bash

# Téléchargement et installation de Miniforge pour Mac Intel
curl -LO https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-x86_64.sh
chmod +x Miniforge3-MacOSX-x86_64.sh
./Miniforge3-MacOSX-x86_64.sh

# Activation de Miniforge
source ~/miniforge3/bin/activate

# Création d'un nouvel environnement Conda
conda create -n video-to-text python=3.10 -y
conda activate video-to-text

# Installation des dépendances via conda
conda install -c conda-forge ffmpeg sentencepiece protobuf numpy pyyaml accelerate -y

# Installation des dépendances via pip avec support CPU
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install transformers boto3 python-dotenv ffmpeg-python tqdm
pip install git+https://github.com/openai/whisper.git

# Vérification de l'installation
python -c "import sentencepiece; import whisper; import tqdm; print('OK')"

echo "Installation terminée. Pour activer l'environnement, exécutez : conda activate video-to-text" 