#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
import argparse
import tempfile
from pathlib import Path

from src.utils.config import load_config
from src.processors.s3_handler import S3Handler
from src.processors.audio_extractor import AudioExtractor
from src.processors.whisper_processor import WhisperProcessor
from src.processors.summary_generator import SummaryGenerator

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_video(
    video_path: str,
    whisper_processor: WhisperProcessor,
    summary_generator: SummaryGenerator,
    audio_extractor: AudioExtractor
) -> dict:
    """Traite une vidéo et génère les résultats"""
    try:
        # Extraction de l'audio
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as audio_file:
            audio_extractor.extract_audio(video_path, audio_file.name)
            
            # Transcription
            transcription = whisper_processor.transcribe(audio_file.name)
            
            # Nettoyage du fichier audio temporaire
            os.unlink(audio_file.name)
        
        # Génération des résumés
        summaries = summary_generator.generate_summaries(transcription.text)
        
        # Création du résultat final
        result = {
            "video_path": video_path,
            "transcription": {
                "full_text": transcription.text,
                "language": transcription.language,
                "segments": transcription.segments,
                "timestamps": transcription.timestamps
            },
            "summaries": {
                "short": summaries.short,
                "medium": summaries.medium,
                "long": summaries.long
            }
        }
        
        return result
    except Exception as e:
        logger.error(f"Erreur lors du traitement de la vidéo {video_path}: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description="Traitement de vidéos avec Whisper")
    parser.add_argument("--config", required=True, help="Chemin vers le fichier de configuration")
    parser.add_argument("--output-dir", required=True, help="Répertoire de sortie pour les résultats")
    args = parser.parse_args()

    try:
        # Chargement de la configuration
        config = load_config(args.config)
        
        # Initialisation des composants
        s3_handler = S3Handler(config['s3'])
        whisper_processor = WhisperProcessor(config['whisper']['model_name'])
        summary_generator = SummaryGenerator()
        audio_extractor = AudioExtractor()
        
        # Création du répertoire de sortie
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Traitement des vidéos
        for video_key in s3_handler.list_video_files():
            logger.info(f"Traitement de {video_key}")
            
            # Téléchargement temporaire
            with tempfile.NamedTemporaryFile(suffix=Path(video_key).suffix, delete=False) as temp_file:
                s3_handler.download_file(video_key, temp_file.name)
                
                # Traitement
                result = process_video(
                    temp_file.name,
                    whisper_processor,
                    summary_generator,
                    audio_extractor
                )
                
                # Sauvegarde des résultats
                output_file = output_dir / f"{Path(video_key).stem}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                # Nettoyage
                os.unlink(temp_file.name)
                
            logger.info(f"Traitement terminé pour {video_key}")
            
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution: {e}")
        raise

if __name__ == "__main__":
    main() 