#!/bin/bash

# Téléchargement et installation de Miniforge pour Mac ARM
curl -LO https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-arm64.sh
chmod +x Miniforge3-MacOSX-arm64.sh
./Miniforge3-MacOSX-arm64.sh

# Activation de Miniforge
source ~/miniforge3/bin/activate

# Création d'un nouvel environnement Conda
conda create -n video-to-text python=3.10 -y
conda activate video-to-text

# Installation des dépendances via conda
conda install -c conda-forge ffmpeg sentencepiece protobuf numpy pyyaml accelerate -y

# Installation des dépendances via pip
pip install torch transformers boto3 python-dotenv ffmpeg-python
pip install git+https://github.com/openai/whisper.git

# Vérification de l'installation
python -c "import sentencepiece; import whisper; print('OK')"

echo "Installation terminée. Pour activer l'environnement, exécutez : conda activate video-to-text" 