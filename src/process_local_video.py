#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
import yaml
from tqdm import tqdm

# Ajout du répertoire src au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.processors.audio_extractor import AudioExtractor
from src.processors.whisper_processor import WhisperProcessor
from src.processors.summary_generator import SummaryGenerator
from src.processors.translator import Translator
from src.utils.config import load_config

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_local_video(video_path: str, config_path: str, output_dir: str):
    """
    Traite une vidéo locale en extrayant l'audio, en le transcrivant et en générant des résumés.
    
    Args:
        video_path (str): Chemin vers le fichier vidéo
        config_path (str): Chemin vers le fichier de configuration
        output_dir (str): Répertoire de sortie pour les résultats
    """
    try:
        # Chargement de la configuration
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        # Création des répertoires de sortie
        output_dir = Path(output_dir)
        temp_dir = output_dir / config['output']['temp_directory']
        output_dir.mkdir(parents=True, exist_ok=True)
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialisation des processeurs
        logger.info("Initialisation des processeurs...")
        audio_extractor = AudioExtractor()
        whisper_processor = WhisperProcessor(config['whisper']['model'])
        translator = Translator(config['translation']['model'])
        
        # Extraction de l'audio
        logger.info("Extraction de l'audio...")
        audio_path = temp_dir / f"{Path(video_path).stem}.wav"
        audio_extractor.extract_audio(video_path, str(audio_path))
        
        # Transcription avec Whisper
        logger.info("Transcription avec Whisper...")
        with tqdm(total=100, desc="Transcription", unit="%") as pbar:
            transcription = whisper_processor.transcribe(str(audio_path))
            pbar.update(100)
        
        # Traduction du texte
        if config['whisper']['translate']:
            logger.info("Traduction du texte...")
            translated_text = translator.translate(transcription.text)
            
            # Traduction des segments individuels
            logger.info("Traduction des segments...")
            translated_segments = []
            for segment in transcription.segments:
                translated_segment = translator.translate(segment['text'])
                # Conserver tous les éléments existants et ajouter les textes traduits
                segment_copy = segment.copy()
                segment_copy['text_original'] = segment['text']
                segment_copy['text_translated'] = translated_segment
                translated_segments.append(segment_copy)
            
            # Création d'un dictionnaire avec les résultats
            result = {
                'original_text': transcription.text,
                'translated_text': translated_text,
                'segments': translated_segments,
                'language': transcription.language,
                'processing_date': datetime.now().isoformat()
            }
        else:
            # Pour les segments sans traduction, ajouter juste le texte original
            segments = []
            for segment in transcription.segments:
                segment_copy = segment.copy()
                segment_copy['text_original'] = segment['text']
                segments.append(segment_copy)
                
            result = {
                'text': transcription.text,
                'segments': segments,
                'language': transcription.language,
                'processing_date': datetime.now().isoformat()
            }

        # Sauvegarde des résultats
        output_file = output_dir / f"{Path(video_path).stem}_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Résultats sauvegardés dans {output_file}")
        
        # Nettoyage des fichiers temporaires
        if audio_path.exists():
            audio_path.unlink()
            
    except Exception as e:
        logger.error(f"Erreur lors du traitement de la vidéo : {str(e)}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Traitement de vidéo locale avec Whisper')
    parser.add_argument('video_path', help='Chemin vers le fichier vidéo')
    parser.add_argument('--config', default='config.yaml', help='Chemin vers le fichier de configuration')
    parser.add_argument('--output', default='./output', help='Répertoire de sortie')
    
    args = parser.parse_args()
    
    process_local_video(args.video_path, args.config, args.output)

if __name__ == "__main__":
    main() 