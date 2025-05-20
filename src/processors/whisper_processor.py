import logging
import torch
import whisper
import numpy as np
from src.utils.types import TranscriptionResult

logger = logging.getLogger(__name__)

class WhisperProcessor:
    """Gestionnaire des opérations Whisper"""
    def __init__(self, model_name: str = "base"):
        self.model = whisper.load_model(model_name)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Utilisation du modèle Whisper {model_name} sur {self.device}")

    def detect_speech_boundaries(self, audio: np.ndarray, min_silence_duration: float = 0.1) -> tuple[float, float]:
        """
        Détecte le début et la fin de la parole en utilisant le modèle Whisper.
        
        Args:
            audio (np.ndarray): Signal audio
            min_silence_duration (float): Durée minimale du silence en secondes
            
        Returns:
            tuple[float, float]: Timestamps du début et de la fin de la parole
        """
        # Découpage de l'audio en segments de 5 secondes pour une meilleure précision
        segment_duration = 5
        sample_rate = 16000  # Whisper utilise 16kHz
        segment_samples = segment_duration * sample_rate
        
        # Analyse des segments pour détecter la parole
        speech_segments = []
        speech_probs = []
        
        # Analyse des 30 premières secondes avec une précision plus fine
        for i in range(0, min(len(audio), 30 * sample_rate), segment_samples):
            segment = audio[i:i + segment_samples]
            if len(segment) < sample_rate:  # Ignorer les segments trop courts
                continue
                
            # Création du spectrogramme pour le segment
            mel = whisper.log_mel_spectrogram(segment).to(self.device)
            
            # Détection de la parole avec Whisper
            result = self.model.transcribe(
                segment,
                verbose=False,
                task="transcribe",
                fp16=False if self.device == "cpu" else True,
                beam_size=5,
                best_of=5,
                temperature=0.0
            )
            
            # Log détaillé pour chaque segment
            segment_start = i / sample_rate
            segment_end = (i + len(segment)) / sample_rate
            no_speech_prob = result["segments"][0].get("no_speech_prob", 1.0) if result["segments"] else 1.0
            has_speech = no_speech_prob < 0.5  # Seuil plus permissif
            
            logger.info(f"Segment {segment_start:.2f}-{segment_end:.2f}s: "
                       f"Parole détectée: {has_speech}, "
                       f"Probabilité de non-parole: {no_speech_prob:.3f}")
            
            speech_probs.append((segment_start, no_speech_prob))
            
            if has_speech:
                speech_segments.append((segment_start, segment_end))
        
        if not speech_segments:
            logger.warning("Aucun segment de parole détecté")
            return 0.0, len(audio) / sample_rate
            
        # Analyse des probabilités pour trouver le point de transition
        speech_probs = np.array(speech_probs)
        # Chercher le premier point où la probabilité de non-parole chute significativement
        for i in range(1, len(speech_probs)):
            if speech_probs[i-1][1] > 0.8 and speech_probs[i][1] < 0.5:
                start_time = speech_probs[i][0]
                logger.info(f"Transition détectée à {start_time:.2f}s "
                          f"(prob: {speech_probs[i-1][1]:.3f} -> {speech_probs[i][1]:.3f})")
                break
        else:
            start_time = speech_segments[0][0]
        
        # Trouver le dernier segment avec de la parole
        end_time = speech_segments[-1][1]
        
        logger.info(f"Segments de parole détectés: {speech_segments}")
        logger.info(f"Début de la parole détecté à {start_time:.2f} secondes")
        logger.info(f"Fin de la parole détecté à {end_time:.2f} secondes")
        
        return start_time, end_time

    def transcribe(self, audio_path: str, target_language: str = None) -> TranscriptionResult:
        """Transcrit une vidéo avec Whisper"""
        try:
            # Chargement de l'audio sans padding ni trimming
            audio = whisper.load_audio(audio_path)
            logger.info(f"Durée totale de l'audio: {len(audio)/16000:.2f} secondes")

            # Pour la détection de langue, Whisper attend un spectrogramme de 30s max
            audio_30s = audio[:30*16000]  # 30 secondes à 16kHz
            mel = whisper.log_mel_spectrogram(audio_30s).to(self.device)
            logger.info(f"Forme du spectrogramme (30s): {mel.shape}")

            # Détection de la langue si non spécifiée
            if target_language is None:
                _, probs = self.model.detect_language(mel)
                detected_language = max(probs, key=probs.get)
            else:
                detected_language = target_language
            logger.info(f"Langue détectée: {detected_language}")

            # Transcription avec les paramètres optimisés pour la précision des timestamps
            result = self.model.transcribe(
                audio_path,  # On repasse le chemin du fichier audio
                verbose=False,
                language=detected_language,
                task="transcribe",
                fp16=False if self.device == "cpu" else True,
                beam_size=5,  # Réduction pour éviter le crash
                best_of=5,    # Réduction pour éviter le crash
                temperature=0.0,
                condition_on_previous_text=True,
                no_speech_threshold=0.6,
                compression_ratio_threshold=2.4,
                logprob_threshold=-1.0,
                # word_timestamps=True,  # Désactivé pour test
                initial_prompt=None,   # Pas de prompt initial pour éviter les biais
                suppress_tokens=[]    # Pas de suppression de tokens
            )

            # Vérification et ajustement des timestamps
            segments = result["segments"]
            for i, seg in enumerate(segments):
                # Vérification de la cohérence des timestamps
                if i > 0:
                    prev_end = segments[i-1]["end"]
                    if seg["start"] < prev_end:
                        logger.warning(f"Chevauchement détecté entre les segments {i-1} et {i}")
                        # Ajustement du début du segment actuel
                        seg["start"] = prev_end
                
                # Vérification de la durée minimale
                if seg["end"] - seg["start"] < 0.1:  # 100ms minimum
                    logger.warning(f"Segment {i} trop court: {seg['end'] - seg['start']:.3f}s")
                    if i > 0:
                        # Fusion avec le segment précédent
                        segments[i-1]["end"] = seg["end"]
                        segments[i-1]["text"] += " " + seg["text"]
                        segments.pop(i)
                        i -= 1

            # Log détaillé des segments avec vérification des timestamps
            logger.info("Segments détectés avec timestamps:")
            for i, seg in enumerate(segments):
                logger.info(f"Segment {i}: {seg['start']:.3f}s - {seg['end']:.3f}s (durée: {seg['end'] - seg['start']:.3f}s): {seg['text']}")
                if "words" in seg:
                    logger.info(f"  Mots: {[(w['word'], w['start'], w['end']) for w in seg['words']]}")

            return TranscriptionResult(
                text=result["text"],
                segments=segments,
                timestamps=[{
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"],
                    "confidence": seg.get("confidence", 0.0),
                    "words": seg.get("words", [])  # Inclusion des timestamps au niveau des mots
                } for seg in segments],
                language=detected_language
            )
        except Exception as e:
            logger.error(f"Erreur lors de la transcription: {e}")
            raise 