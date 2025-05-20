import json
import logging
import numpy as np
from pathlib import Path
from datetime import datetime
import soundfile as sf
import tempfile
import os
from pydub import AudioSegment
from pydub.effects import speedup
from .tts_processor import TTSProcessor

logger = logging.getLogger(__name__)

class AudioGenerator:
    """Générateur de fichier audio à partir d'une transcription"""
    
    def __init__(self, config: dict, sample_rate=16000):
        self.sample_rate = sample_rate
        self.tts_processor = TTSProcessor(config.get('tts', {}))
        
    def generate_audio(self, json_path: str, output_path: str, language: str = "fr") -> None:
        """
        Génère un fichier audio à partir d'un fichier JSON de transcription.
        
        Args:
            json_path (str): Chemin vers le fichier JSON de transcription
            output_path (str): Chemin de sortie pour le fichier audio
            language (str): Langue pour la synthèse vocale (par défaut: "fr")
        """
        try:
            # Lecture du fichier JSON
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Concaténation de tous les segments en un seul texte
            full_text = ""
            for segment in data['segments']:
                # Utilisation du texte traduit si disponible, sinon le texte original
                text = segment.get('text_translated', segment.get('text_original', segment['text']))
                full_text += text + " "
            
            # Génération de la synthèse vocale avec le texte complet
            self.tts_processor.generate_speech(full_text.strip(), language, output_path)
            
            logger.info(f"Fichier audio généré avec succès : {output_path}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de l'audio : {str(e)}")
            raise
            
    def generate_audio_with_timestamps(self, json_path: str, output_path: str, language: str = "fr", adjust_speed: bool = True) -> None:
        """
        Génère un fichier audio à partir d'un fichier JSON de transcription en respectant les timestamps.
        
        Args:
            json_path (str): Chemin vers le fichier JSON de transcription
            output_path (str): Chemin de sortie pour le fichier audio
            language (str): Langue pour la synthèse vocale (par défaut: "fr")
            adjust_speed (bool): Ajuster la vitesse de la synthèse vocale pour correspondre aux timestamps (par défaut: True)
        """
        try:
            # Lecture du fichier JSON
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Création d'un fichier audio temporaire pour chaque segment
            temp_files = []
            for segment in data['segments']:
                # Utilisation du texte traduit si disponible, sinon le texte original
                text = segment.get('text_translated', segment.get('text_original', segment['text']))
                
                # Génération de la synthèse vocale
                temp_file = self.tts_processor.generate_speech(text, language)
                temp_files.append((temp_file, segment['start'], segment['end']))
            
            # Création d'un fichier audio vide de la durée totale
            total_duration = max(segment['end'] for segment in data['segments'])
            combined = AudioSegment.silent(duration=int(total_duration * 1000))  # Conversion en millisecondes
            
            # Paramètres pour le fondu enchaîné
            fade_duration = 100  # 100ms de fondu
            
            # Insertion des segments aux bons timestamps
            for i, (temp_file, start, end) in enumerate(temp_files):
                segment_audio = AudioSegment.from_wav(temp_file)
                # Ajustement de la durée du segment
                segment_duration = (end - start) * 1000  # Conversion en millisecondes
                
                if adjust_speed and len(segment_audio) > 0:
                    # Calcul du facteur de vitesse pour correspondre à la durée cible
                    speed_factor = len(segment_audio) / segment_duration
                    
                    # Limites de vitesse plus strictes
                    min_speed = 0.8  # Ne pas ralentir plus que 20%
                    max_speed = 1.2  # Ne pas accélérer plus que 20%
                    
                    if speed_factor > max_speed:
                        # Si l'audio est trop long, on le coupe plutôt que de trop l'accélérer
                        segment_audio = segment_audio[:int(segment_duration)]
                    elif speed_factor < min_speed:
                        # Si l'audio est trop court, on ajoute du silence
                        silence = AudioSegment.silent(duration=int(segment_duration - len(segment_audio)))
                        segment_audio += silence
                    else:
                        # Ajustement de vitesse dans les limites acceptables
                        segment_audio = speedup(segment_audio, speed_factor)
                
                # Ajustement final de la durée avec une transition plus douce
                if len(segment_audio) > segment_duration:
                    # Au lieu de couper brutalement, on fait un fondu
                    fade_out_duration = min(200, int(segment_duration * 0.1))  # 10% de la durée ou 200ms max
                    segment_audio = segment_audio[:int(segment_duration)].fade_out(fade_out_duration)
                elif len(segment_audio) < segment_duration:
                    # Ajout d'un silence avec fondu
                    silence = AudioSegment.silent(duration=int(segment_duration - len(segment_audio)))
                    segment_audio = segment_audio.fade_out(100) + silence.fade_in(100)
                
                # Ajout des effets de fondu
                if i > 0:  # Fondu en entrée pour tous les segments sauf le premier
                    segment_audio = segment_audio.fade_in(fade_duration)
                if i < len(temp_files) - 1:  # Fondu en sortie pour tous les segments sauf le dernier
                    segment_audio = segment_audio.fade_out(fade_duration)
                
                # Insertion du segment
                combined = combined.overlay(segment_audio, position=int(start * 1000))
                
                # Suppression du fichier temporaire
                os.unlink(temp_file)
            
            # Export du fichier final
            combined.export(output_path, format="wav")
            
            logger.info(f"Fichier audio généré avec succès : {output_path}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de l'audio : {str(e)}")
            raise 