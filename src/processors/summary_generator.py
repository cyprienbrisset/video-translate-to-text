import logging
from transformers import pipeline
from src.utils.types import SummaryResult

logger = logging.getLogger(__name__)

class SummaryGenerator:
    """Générateur de résumés"""
    def __init__(self):
        self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

    def generate_summaries(self, text: str) -> SummaryResult:
        """Génère trois résumés de différentes longueurs"""
        try:
            # Résumé court (100 mots)
            short_summary = self.summarizer(text, max_length=100, min_length=50, do_sample=False)[0]['summary_text']
            
            # Résumé moyen (200 mots)
            medium_summary = self.summarizer(text, max_length=200, min_length=100, do_sample=False)[0]['summary_text']
            
            # Résumé long (500 mots)
            long_summary = self.summarizer(text, max_length=500, min_length=300, do_sample=False)[0]['summary_text']

            return SummaryResult(
                short=short_summary,
                medium=medium_summary,
                long=long_summary
            )
        except Exception as e:
            logger.error(f"Erreur lors de la génération des résumés: {e}")
            raise 