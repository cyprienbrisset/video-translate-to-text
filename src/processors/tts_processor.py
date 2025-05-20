import logging
import tempfile
import os
from pathlib import Path
from typing import Optional
import subprocess
import json
import numpy as np
import soundfile as sf
import shutil

logger = logging.getLogger(__name__)

class TTSProcessor:
    """Gestionnaire de la synthèse vocale"""
    
    def __init__(self, config: dict):
        self.config = config
        self.engine = config.get('engine', 'piper')
        self.voice = config.get('voice')
        self.model_path = config.get('model_path')
        self.config_path = config.get('config_path')
        self.output_format = config.get('output_format')
        self.sample_rate = config.get('sample_rate')
        self.speaker_id = config.get('speaker_id', 1)
        self.logger = logging.getLogger(__name__)
        
        if self.engine == 'piper':
            logger.info(f"Initialisation de Piper TTS avec le modèle {self.model_path}")
            # Vérification que le modèle existe
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Le modèle Piper {self.model_path} n'existe pas")
            if not os.path.exists(self.config_path):
                raise FileNotFoundError(f"Le fichier de configuration {self.config_path} n'existe pas")
        else:
            self.model_path = None
            self.config_path = None
            logger.info("Aucun moteur TTS configuré")
    
    def generate_audio(self, text, output_path=None):
        """Génère un fichier audio à partir du texte traduit."""
        try:
            # Créer un fichier temporaire pour l'audio si aucun chemin de sortie n'est spécifié
            if output_path is None:
                temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                output_path = temp_audio.name
                temp_audio.close()
            else:
                # Vérifier que le dossier de sortie existe
                output_dir = os.path.dirname(output_path)
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir, exist_ok=True)
                    self.logger.info(f"Dossier de sortie créé : {output_dir}")
            
            # Créer un fichier temporaire pour l'audio
            temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_audio_path = temp_audio.name
            temp_audio.close()
            
            # Générer l'audio avec Piper
            command = [
                'piper',
                '--model', self.model_path,
                '--config', self.config_path,
                '--output-file', temp_audio_path,
                '--speaker', str(self.speaker_id)
            ]
            
            # Exécuter la commande en passant le texte via stdin
            self.logger.info(f"Commande Piper : {' '.join(command)}")
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(input=text)
            
            if process.returncode != 0:
                self.logger.error(f"Erreur lors de la génération audio : {stderr}")
                raise RuntimeError(f"Erreur lors de la génération audio : {stderr}")
            
            # Copier le fichier audio généré vers le chemin de sortie spécifié
            shutil.copy2(temp_audio_path, output_path)
            
            # Nettoyer les fichiers temporaires
            os.unlink(temp_audio_path)
            
            self.logger.info(f"Audio généré avec succès : {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la génération audio : {str(e)}")
            raise 