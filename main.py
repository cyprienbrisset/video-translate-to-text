import logging
import yaml
import argparse
from pathlib import Path
from src.processors.whisper_processor import WhisperProcessor
from src.processors.argos_translator import ArgosTranslator
from src.processors.tts_processor import TTSProcessor
import os
import subprocess
from pydub import AudioSegment
import glob

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(config_path: str) -> dict:
    """Charge la configuration depuis un fichier YAML"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def extract_audio(video_path, output_path):
    """Extrait l'audio d'une vidéo."""
    command = [
        'ffmpeg', '-i', video_path,
        '-vn',  # Pas de vidéo
        '-acodec', 'pcm_s16le',  # Codec audio PCM
        '-ar', '16000',  # Taux d'échantillonnage
        '-ac', '1',  # Mono
        '-y',  # Écraser si existe
        output_path
    ]
    subprocess.run(command, check=True)

def sync_audio_with_original(original_audio_path, new_audio_path, timestamps, output_path):
    """Synchronise le nouvel audio avec l'original en utilisant les timestamps."""
    if not os.path.exists(new_audio_path):
        raise FileNotFoundError(f"Le fichier audio généré {new_audio_path} n'existe pas.")
    
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
    
    # Créer un fichier temporaire pour l'audio original
    original_audio_temp = os.path.join(os.path.dirname(output_path), 'original_temp.wav')
    subprocess.run([
        'ffmpeg', '-i', original_audio_path,
        '-acodec', 'pcm_s16le',
        '-ar', '16000',
        '-ac', '1',
        '-y', original_audio_temp
    ], check=True)
    
    # Liste pour stocker les segments
    segments = []
    tts_cursor = 0  # Position dans l'audio TTS
    
    for i, seg in enumerate(timestamps):
        start = seg["start"]
        end = seg["end"]
        text = seg["text"]
        
        # Pour les segments non vocaux, utiliser l'audio original
        if text.startswith('[') and text.endswith(']'):
            logger.info(f"Utilisation de l'audio original pour le segment {i} : {text}")
            segment_path = os.path.join(os.path.dirname(output_path), f'segment_{i}.wav')
            subprocess.run([
                'ffmpeg', '-i', original_audio_temp,
                '-ss', str(start),
                '-t', str(end - start),
                '-y', segment_path
            ], check=True)
        else:
            # Pour les segments vocaux, utiliser l'audio TTS
            if end - start < 0.1:  # Ignorer les segments trop courts
                continue
                
            segment_path = os.path.join(os.path.dirname(output_path), f'segment_{i}.wav')
            segment_duration = end - start
            
            subprocess.run([
                'ffmpeg', '-i', new_audio_path,
                '-ss', str(tts_cursor),
                '-t', str(segment_duration),
                '-acodec', 'pcm_s16le',
                '-ar', '16000',
                '-ac', '1',
                '-y', segment_path
            ], check=True)
            tts_cursor += segment_duration
        
        # Vérifier que le segment a été correctement extrait
        if not os.path.exists(segment_path) or os.path.getsize(segment_path) == 0:
            logger.warning(f"Le segment {i} n'a pas été correctement extrait, on le saute")
            continue
            
        segments.append((start, segment_path))
    
    # Trier les segments par ordre chronologique
    segments.sort(key=lambda x: x[0])
    
    # Créer le fichier de concaténation
    concat_file = os.path.join(os.path.dirname(output_path), 'concat.txt')
    with open(concat_file, 'w') as f:
        for start, segment_path in segments:
            f.write(f"file '{segment_path}'\n")
    
    # Concaténer tous les segments
    subprocess.run([
        'ffmpeg', '-f', 'concat', '-safe', '0',
        '-i', concat_file,
        '-y', output_path
    ], check=True)
    
    # Nettoyer les fichiers temporaires
    try:
        os.remove(silent_audio)
        os.remove(original_audio_temp)
        os.remove(concat_file)
        for _, segment_path in segments:
            os.remove(segment_path)
    except Exception as e:
        logger.warning(f"Impossible de supprimer un fichier temporaire: {e}")

def combine_video_audio(video_path, audio_path, output_path):
    """Combine la vidéo avec l'audio synchronisé."""
    command = [
        'ffmpeg',
        '-i', video_path,
        '-i', audio_path,
        '-c:v', 'copy',  # Copier le flux vidéo sans le réencoder
        '-c:a', 'aac',   # Encoder l'audio en AAC
        '-map', '0:v:0', # Prendre la vidéo de la première entrée
        '-map', '1:a:0', # Prendre l'audio de la deuxième entrée
        '-y',            # Écraser si existe
        output_path
    ]
    subprocess.run(command, check=True)

def replace_speech_with_tts(original_audio_path, tts_audio_path, timestamps, output_path):
    """
    Remplace les segments de parole de l'audio original par l'audio TTS,
    en gardant la musique/bruit d'ambiance.
    """
    original = AudioSegment.from_wav(original_audio_path)
    tts = AudioSegment.from_wav(tts_audio_path)
    output = original
    tts_cursor = 0  # Position dans l'audio TTS
    for seg in timestamps:
        start = int(seg["start"] * 1000)
        end = int(seg["end"] * 1000)
        seg_duration = end - start
        # Extraire le segment TTS correspondant
        tts_seg = tts[tts_cursor:tts_cursor + seg_duration]
        # Mixer le TTS sur l'original (remplacement, mais on peut aussi faire un mix léger si besoin)
        output = output.overlay(tts_seg, position=start)
        tts_cursor += seg_duration

def clean_temp_files():
    """Nettoie les fichiers temporaires générés lors du traitement."""
    temp_files = glob.glob("output/*.wav") + glob.glob("output/temp/*.wav")
    for file in temp_files:
        try:
            os.remove(file)
        except Exception as e:
            logging.warning(f"Impossible de supprimer {file}: {e}")

def is_non_vocal_segment(text):
    """Vérifie si un segment est non vocal (musique, applaudissements, etc.)"""
    return text.strip().startswith('[') and text.strip().endswith(']')

def split_long_segment(text, max_length=100):
    """Divise un segment trop long en segments plus courts."""
    if len(text) <= max_length:
        return [text]
    
    # Diviser sur les points ou les virgules
    parts = []
    current_part = ""
    
    for char in text:
        current_part += char
        if len(current_part) >= max_length and (char in '.!?,;'):
            parts.append(current_part.strip())
            current_part = ""
    
    if current_part:
        parts.append(current_part.strip())
    
    return parts

def main():
    # Configuration des arguments en ligne de commande
    parser = argparse.ArgumentParser(description='Traduction et synchronisation de vidéo')
    parser.add_argument('video_path', type=str, help='Chemin vers le fichier vidéo à traiter')
    args = parser.parse_args()

    # Vérification que le fichier vidéo existe
    video_path = Path(args.video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Le fichier vidéo {video_path} n'existe pas")
    
    # Chargement de la configuration
    config = load_config('config.yaml')
    
    # Initialisation des processeurs
    transcription_processor = WhisperProcessor(config['whisper']['model'])
    translation_processor = ArgosTranslator(from_code="en", to_code="fr")
    tts_processor = TTSProcessor(config['tts'])
    
    # Configuration des dossiers de sortie
    output_dir = Path(config['output']['directory'])
    temp_dir = Path(config['output']['temp_directory'])
    
    # Création des dossiers s'ils n'existent pas
    for directory in [output_dir, temp_dir]:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Vérification du dossier {directory} : {'existe' if directory.exists() else 'créé'}")
    
    try:
        # Extraction de l'audio original
        original_audio_path = temp_dir / 'original_audio.wav'
        extract_audio(str(video_path), str(original_audio_path))
        logger.info("Audio original extrait")
        
        # Vérification de l'audio original
        if not original_audio_path.exists():
            raise FileNotFoundError(f"L'audio original n'a pas été extrait correctement : {original_audio_path}")
        
        # Transcription
        logger.info("Début de la transcription...")
        transcription = transcription_processor.transcribe(str(video_path))
        logger.info("Transcription terminée")
        
        # Vérification des timestamps
        if not transcription.timestamps:
            raise ValueError("Aucun timestamp n'a été généré lors de la transcription")
        
        # Traduction et génération audio segment par segment
        logger.info("Début de la traduction et génération audio segment par segment...")
        segments_audio = []
        
        for i, seg in enumerate(transcription.timestamps):
            text = seg["text"]
            
            # Pour les segments non vocaux, on ne fait rien
            if is_non_vocal_segment(text):
                logger.info(f"Segment {i} ignoré (non vocal) : {text}")
                continue
            
            logger.info(f"Traitement du segment vocal {i} : {text}")
            
            try:
                # Diviser le segment s'il est trop long
                text_parts = split_long_segment(text)
                if len(text_parts) > 1:
                    logger.info(f"Segment {i} divisé en {len(text_parts)} parties")
                
                translated_parts = []
                for j, part in enumerate(text_parts):
                    try:
                        # Traduction du segment
                        logger.info(f"Traduction de la partie {j+1}/{len(text_parts)} du segment {i}...")
                        translated_part = translation_processor.translate(part)
                        if not translated_part:
                            raise ValueError("La traduction est vide")
                        logger.info(f"Partie {j+1} du segment {i} traduite : {part} -> {translated_part}")
                        translated_parts.append(translated_part)
                    except Exception as e:
                        logger.error(f"Erreur lors de la traduction de la partie {j+1} du segment {i} : {str(e)}")
                        translated_parts.append(part)
                
                # Recombiner les parties traduites
                translated_text = " ".join(translated_parts)
                
                # Génération audio pour ce segment
                segment_audio_path = temp_dir / f'segment_tts_{i}.wav'
                logger.info(f"Génération audio pour le segment {i}...")
                tts_processor.generate_audio(translated_text, str(segment_audio_path))
                
                # Vérification que le fichier audio a été généré
                if not segment_audio_path.exists():
                    raise FileNotFoundError(f"Le fichier audio pour le segment {i} n'a pas été généré")
                
                logger.info(f"Audio généré pour le segment {i} : {segment_audio_path}")
                segments_audio.append((seg["start"], seg["end"], str(segment_audio_path)))
                
            except Exception as e:
                logger.error(f"Erreur lors du traitement du segment {i} : {str(e)}")
                continue
        
        if not segments_audio:
            raise ValueError("Aucun segment audio n'a été généré")
        
        # Synchronisation de l'audio
        logger.info("Début de la synchronisation de l'audio...")
        synced_audio_path = output_dir / 'synced_audio.wav'
        
        try:
            # Créer un fichier audio silencieux de la même durée que l'original
            logger.info("Création du fichier audio silencieux...")
            original_duration = float(subprocess.check_output([
                'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1', str(original_audio_path)
            ]).decode().strip())
            
            silent_audio = temp_dir / 'silent.wav'
            subprocess.run([
                'ffmpeg', '-f', 'lavfi', '-i', f'anullsrc=r=16000:cl=mono',
                '-t', str(original_duration), '-y', str(silent_audio)
            ], check=True)
            logger.info("Fichier audio silencieux créé")
            
            # Créer un fichier temporaire pour l'audio original
            logger.info("Préparation de l'audio original...")
            original_audio_temp = temp_dir / 'original_temp.wav'
            subprocess.run([
                'ffmpeg', '-i', str(original_audio_path),
                '-acodec', 'pcm_s16le',
                '-ar', '16000',
                '-ac', '1',
                '-y', str(original_audio_temp)
            ], check=True)
            logger.info("Audio original préparé")
            
            # Liste pour stocker les segments
            segments = []
            
            # Ajouter les segments TTS
            logger.info("Préparation des segments TTS...")
            for start, end, audio_path in segments_audio:
                try:
                    segment_path = temp_dir / f'segment_{start}_{end}.wav'
                    logger.info(f"Conversion du segment {start}-{end}...")
                    subprocess.run([
                        'ffmpeg', '-i', audio_path,
                        '-acodec', 'pcm_s16le',
                        '-ar', '16000',
                        '-ac', '1',
                        '-y', str(segment_path)
                    ], check=True)
                    segments.append((start, str(segment_path)))
                    logger.info(f"Segment {start}-{end} préparé")
                except Exception as e:
                    logger.error(f"Erreur lors de la préparation du segment {start}-{end} : {str(e)}")
                    continue
            
            # Ajouter les segments non vocaux de l'audio original
            logger.info("Préparation des segments non vocaux...")
            for seg in transcription.timestamps:
                if is_non_vocal_segment(seg["text"]):
                    try:
                        segment_path = temp_dir / f'segment_orig_{seg["start"]}_{seg["end"]}.wav'
                        logger.info(f"Extraction du segment original {seg['start']}-{seg['end']}...")
                        subprocess.run([
                            'ffmpeg', '-i', str(original_audio_temp),
                            '-ss', str(seg["start"]),
                            '-t', str(seg["end"] - seg["start"]),
                            '-y', str(segment_path)
                        ], check=True)
                        segments.append((seg["start"], str(segment_path)))
                        logger.info(f"Segment original {seg['start']}-{seg['end']} extrait")
                    except Exception as e:
                        logger.error(f"Erreur lors de l'extraction du segment original {seg['start']}-{seg['end']} : {str(e)}")
                        continue
            
            if not segments:
                raise ValueError("Aucun segment n'a été préparé pour la concaténation")
            
            # Trier les segments par ordre chronologique
            segments.sort(key=lambda x: x[0])
            
            # Créer le fichier de concaténation
            logger.info("Création du fichier de concaténation...")
            concat_file = temp_dir / 'concat.txt'
            with open(concat_file, 'w') as f:
                for _, segment_path in segments:
                    f.write(f"file '{segment_path}'\n")
            
            # Concaténer tous les segments
            logger.info("Concaténation des segments...")
            subprocess.run([
                'ffmpeg', '-f', 'concat', '-safe', '0',
                '-i', str(concat_file),
                '-y', str(synced_audio_path)
            ], check=True)
            logger.info("Segments concaténés avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation audio : {str(e)}")
            raise
        
        # Combinaison vidéo + audio
        logger.info("Début de la combinaison vidéo + audio...")
        output_video = output_dir / f"{video_path.stem}_traduit.mp4"
        combine_video_audio(str(video_path), str(synced_audio_path), str(output_video))
        logger.info("Vidéo finale générée")
        
        # Nettoyage des fichiers temporaires
        try:
            os.remove(silent_audio)
            os.remove(original_audio_temp)
            os.remove(concat_file)
            for _, segment_path in segments:
                os.remove(segment_path)
            for _, _, audio_path in segments_audio:
                os.remove(audio_path)
        except Exception as e:
            logger.warning(f"Impossible de supprimer un fichier temporaire: {e}")
        
        logger.info("Traitement terminé avec succès!")
        logger.info(f"Vidéo finale générée : {output_video}")
        
    except Exception as e:
        logger.error(f"Une erreur est survenue : {str(e)}")
        raise

if __name__ == "__main__":
    main() 