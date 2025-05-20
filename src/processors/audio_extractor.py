import logging
import ffmpeg

logger = logging.getLogger(__name__)

class AudioExtractor:
    """Gestionnaire de l'extraction audio"""
    def __init__(self):
        self.sample_rate = 16000  # Taux d'échantillonnage standard pour Whisper

    def extract_audio(self, video_path: str, output_path: str) -> None:
        """Extrait l'audio d'une vidéo en WAV"""
        try:
            logger.info(f"Extraction de l'audio de {video_path}")
            stream = ffmpeg.input(video_path)
            stream = ffmpeg.output(
                stream,
                output_path,
                acodec='pcm_s16le',  # Codec PCM 16-bit
                ac=1,  # Mono audio
                ar=self.sample_rate  # Taux d'échantillonnage
            )
            ffmpeg.run(stream, capture_stdout=True, capture_stderr=True, overwrite_output=True)
            logger.info(f"Audio extrait avec succès vers {output_path}")
        except ffmpeg.Error as e:
            logger.error(f"Erreur lors de l'extraction audio: {e.stderr.decode()}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'extraction audio: {e}")
            raise 