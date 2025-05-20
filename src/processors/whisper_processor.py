import logging
import torch
import whisper
from src.utils.types import TranscriptionResult

logger = logging.getLogger(__name__)

class WhisperProcessor:
    """Gestionnaire des opérations Whisper"""
    def __init__(self, model_name: str = "base"):
        self.model = whisper.load_model(model_name)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Utilisation du modèle Whisper {model_name} sur {self.device}")

    def transcribe(self, audio_path: str, target_language: str = None) -> TranscriptionResult:
        """Transcrit une vidéo avec Whisper"""
        try:
            # Chargement et préparation de l'audio
            audio = whisper.load_audio(audio_path)
            audio = whisper.pad_or_trim(audio)

            # Création du spectrogramme
            mel = whisper.log_mel_spectrogram(audio).to(self.device)

            # Détection de la langue si non spécifiée
            if target_language is None:
                _, probs = self.model.detect_language(mel)
                detected_language = max(probs, key=probs.get)
            else:
                detected_language = target_language
            logger.info(f"Langue détectée: {detected_language}")

            # Options de décodage
            options = whisper.DecodingOptions(
                language=detected_language,
                fp16=False if self.device == "cpu" else True,
                beam_size=5,
                best_of=5,
                temperature=0.0
            )

            # Transcription
            result = self.model.transcribe(
                audio_path,
                verbose=False,
                language=detected_language,
                task="transcribe",
                fp16=False if self.device == "cpu" else True,
                beam_size=5,
                best_of=5,
                temperature=0.0
            )

            return TranscriptionResult(
                text=result["text"],
                segments=result["segments"],
                timestamps=[{
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"],
                    "confidence": seg.get("confidence", 0.0)
                } for seg in result["segments"]],
                language=detected_language
            )
        except Exception as e:
            logger.error(f"Erreur lors de la transcription: {e}")
            raise 