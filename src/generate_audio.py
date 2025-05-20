#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import logging
import os
import json
from pathlib import Path
import yaml
from processors.audio_generator import AudioGenerator

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(config_path: str = "config.yaml") -> dict:
    """Charge la configuration depuis le fichier YAML"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la configuration : {e}")
        return {}

def generate_audio(json_path: str, output_path: str, language: str = "fr", use_timestamps: bool = True, adjust_speed: bool = True) -> None:
    """
    Génère un fichier audio à partir d'un fichier JSON de transcription.
    
    Args:
        json_path (str): Chemin vers le fichier JSON de transcription
        output_path (str): Chemin de sortie pour le fichier audio
        language (str): Langue pour la synthèse vocale
        use_timestamps (bool): Utiliser les timestamps pour la génération
        adjust_speed (bool): Ajuster la vitesse de la synthèse vocale
    """
    try:
        # Chargement de la configuration
        config = load_config()
        
        # Création du générateur d'audio
        generator = AudioGenerator(config)
        
        # Génération de l'audio
        if use_timestamps:
            generator.generate_audio_with_timestamps(json_path, output_path, language, adjust_speed)
        else:
            generator.generate_audio(json_path, output_path, language)
            
        logger.info(f"Audio généré avec succès : {output_path}")
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération de l'audio : {e}")
        raise

def main():
    """Point d'entrée principal du script"""
    parser = argparse.ArgumentParser(description="Génère un fichier audio à partir d'une transcription JSON")
    parser.add_argument("json_path", help="Chemin vers le fichier JSON de transcription")
    parser.add_argument("--output", "-o", required=True, help="Chemin de sortie pour le fichier audio")
    parser.add_argument("--language", "-l", default="fr", help="Langue pour la synthèse vocale (par défaut: fr)")
    parser.add_argument("--no-timestamps", action="store_true", help="Ne pas utiliser les timestamps")
    parser.add_argument("--no-speed-adjust", action="store_true", help="Ne pas ajuster la vitesse de la synthèse vocale")
    
    args = parser.parse_args()
    
    try:
        generate_audio(args.json_path, args.output, args.language, not args.no_timestamps, not args.no_speed_adjust)
    except Exception as e:
        logger.error(f"Erreur lors de la génération de l'audio : {e}")
        exit(1)

if __name__ == "__main__":
    main() 