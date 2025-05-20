#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import requests
from pathlib import Path
import json

# Ajout du répertoire src au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def download_piper_model():
    """Télécharge le modèle Piper UPMC Pierre"""
    try:
        # Création du répertoire pour les modèles
        model_dir = Path.home() / ".local" / "share" / "piper"
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # URL du modèle
        model_name = "fr_FR-upmc-pierre-medium"
        model_url = f"https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/upmc/pierre/medium/{model_name}.onnx"
        config_url = f"https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/upmc/pierre/medium/{model_name}.onnx.json"
        
        # Téléchargement du modèle
        logger.info("Téléchargement du modèle UPMC Pierre...")
        model_path = model_dir / f"{model_name}.onnx"
        config_path = model_dir / f"{model_name}.onnx.json"
        
        # Téléchargement du fichier de configuration
        logger.info("Téléchargement de la configuration...")
        response = requests.get(config_url)
        response.raise_for_status()
        with open(config_path, 'wb') as f:
            f.write(response.content)
        
        # Téléchargement du modèle
        logger.info("Téléchargement du modèle...")
        response = requests.get(model_url)
        response.raise_for_status()
        with open(model_path, 'wb') as f:
            f.write(response.content)
        
        logger.info("Modèle téléchargé avec succès")
        
    except Exception as e:
        logger.error(f"Erreur lors du téléchargement du modèle : {str(e)}")
        raise

if __name__ == "__main__":
    download_piper_model() 