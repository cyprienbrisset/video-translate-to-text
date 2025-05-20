import logging
import subprocess
import os
from pathlib import Path
import tempfile
import cv2
import numpy as np

logger = logging.getLogger(__name__)

class LipsyncProcessor:
    """Gestionnaire de la synchronisation des lèvres"""
    
    def __init__(self, config: dict):
        self.config = config
        self.wav2lip_path = config.get('wav2lip_path', 'Wav2Lip')
        self.checkpoint_path = os.path.join(self.wav2lip_path, "checkpoints", "Wav2Lip-SD-GAN.pt")
        self.face_det_batch_size = config.get('face_det_batch_size', 16)
        self.wav2lip_batch_size = config.get('wav2lip_batch_size', 128)
        self.resize_factor = config.get('resize_factor', 1)
        self.pads = config.get('pads', [0, 20, 0, 0])
        self.no_smooth = config.get('no_smooth', False)
        self.box = config.get('box', None)
        
    def extract_video_segment(self, video_path: str, start_time: float, end_time: float, output_path: str) -> None:
        """Extrait un segment de la vidéo entre start_time et end_time"""
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Calcul des frames de début et de fin
        start_frame = int(start_time * fps)
        end_frame = int(end_time * fps)
        
        # Création du writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # Positionnement au début du segment
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        # Lecture et écriture des frames
        for _ in range(end_frame - start_frame):
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)
        
        cap.release()
        out.release()
        
    def sync_audio_with_original(self, original_audio_path, new_audio_path, timestamps, output_path):
        """Synchronise le nouvel audio avec l'original en utilisant les timestamps."""
        # Créer un fichier audio silencieux de la même durée que l'original
        original_duration = float(subprocess.check_output([
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', original_audio_path
        ]).decode().strip())
        
        # Créer un fichier audio silencieux
        silent_audio = os.path.join(os.path.dirname(output_path), 'silent.wav')
        subprocess.run([
            'ffmpeg', '-f', 'lavfi', '-i', f'anullsrc=r=16000:cl=mono',
            '-t', str(original_duration), '-y', silent_audio
        ], check=True)
        
        # Pour chaque segment de parole, insérer le nouvel audio aux bons timestamps
        temp_segments = []
        for i, (start, end) in enumerate(timestamps):
            if end - start < 0.1:  # Ignorer les segments trop courts
                continue
                
            # Extraire le segment correspondant du nouvel audio
            segment_path = os.path.join(os.path.dirname(output_path), f'segment_{i}.wav')
            subprocess.run([
                'ffmpeg', '-i', new_audio_path,
                '-ss', str(i * (end - start)),  # Prendre le segment correspondant du nouvel audio
                '-t', str(end - start),
                '-y', segment_path
            ], check=True)
            
            # Insérer ce segment dans l'audio silencieux
            temp_output = os.path.join(os.path.dirname(output_path), f'synced_{i}.wav')
            subprocess.run([
                'ffmpeg', '-i', silent_audio,
                '-i', segment_path,
                '-filter_complex', f'[0:a][1:a]amix=inputs=2:duration=first[aout]',
                '-map', '[aout]',
                '-y', temp_output
            ], check=True)
            
            silent_audio = temp_output
            temp_segments.append(temp_output)
        
        # Copier le résultat final
        subprocess.run(['cp', silent_audio, output_path], check=True)
        
        # Nettoyer les fichiers temporaires
        for temp_file in temp_segments:
            os.remove(temp_file)
        os.remove(os.path.join(os.path.dirname(output_path), 'silent.wav'))

    def generate_lipsync(self, video_path: str, audio_path: str, output_path: str, timestamps: list = None) -> None:
        """
        Génère une vidéo avec les lèvres synchronisées avec l'audio.
        
        Args:
            video_path (str): Chemin vers la vidéo source
            audio_path (str): Chemin vers l'audio à synchroniser
            output_path (str): Chemin de sortie pour la vidéo synchronisée
            timestamps (list): Liste des timestamps des segments contenant de la parole
        """
        try:
            # Création d'un dossier temporaire pour les fichiers intermédiaires
            with tempfile.TemporaryDirectory() as temp_dir:
                # Préparation des chemins
                temp_video = os.path.join(temp_dir, "temp_video.mp4")
                temp_audio = os.path.join(temp_dir, "temp_audio.wav")
                
                if timestamps:
                    # Trouver le premier segment de parole
                    speech_segment = None
                    for start, end in timestamps:
                        if end - start > 0.1:  # Ignorer les segments trop courts
                            speech_segment = (start, end)
                            break
                    
                    if speech_segment:
                        start_time, end_time = speech_segment
                        # Extraire le segment vidéo
                        self.extract_video_segment(
                            video_path,
                            start_time,
                            end_time,
                            temp_video
                        )
                        video_path = temp_video
                        
                        # Synchroniser l'audio avec l'original
                        synced_audio = os.path.join(temp_dir, 'synced_audio.wav')
                        self.sync_audio_with_original(audio_path, audio_path, timestamps, synced_audio)
                        audio_path = synced_audio
                else:
                    # Copie de la vidéo complète si pas de timestamps
                    subprocess.run(["cp", video_path, temp_video], check=True)
                
                # Copie de l'audio
                subprocess.run(["cp", audio_path, temp_audio], check=True)
                
                # Appel à Wav2Lip
                command = [
                    "python", os.path.join(self.wav2lip_path, "inference.py"),
                    "--checkpoint_path", self.checkpoint_path,
                    "--face", temp_video,
                    "--audio", temp_audio,
                    "--outfile", output_path,
                    "--face_det_batch_size", str(self.face_det_batch_size),
                    "--wav2lip_batch_size", str(self.wav2lip_batch_size),
                    "--resize_factor", str(self.resize_factor),
                    "--no_smooth" if self.no_smooth else '',
                ]
                # Ajout dynamique des pads
                if self.pads:
                    command += ["--pads"] + [str(p) for p in self.pads]
                # Ajouter la box si spécifiée
                if self.box:
                    command += ["--box"] + [str(b) for b in self.box]
                
                logger.info(f"Lancement de Wav2Lip avec la commande : {' '.join(command)}")
                result = subprocess.run(command, capture_output=True, text=True)
                
                if result.returncode != 0:
                    logger.error(f"Erreur Wav2Lip : {result.stderr}")
                    raise RuntimeError(f"Erreur Wav2Lip : {result.stderr}")
                
                logger.info(f"Vidéo synchronisée générée avec succès : {output_path}")
                
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation des lèvres : {str(e)}")
            raise 