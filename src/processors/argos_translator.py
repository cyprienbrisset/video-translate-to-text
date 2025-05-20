import argostranslate.package
import argostranslate.translate
import logging
import os
import time
from typing import Optional, List
import gc
import re

logger = logging.getLogger(__name__)

class TranslationError(Exception):
    """Exception personnalisée pour les erreurs de traduction"""
    pass

class ArgosTranslator:
    def __init__(self, from_code="en", to_code="fr", max_retries=3, timeout=30, max_chunk_size=100):
        self.from_code = from_code
        self.to_code = to_code
        self.max_retries = max_retries
        self.timeout = timeout
        self.max_chunk_size = max_chunk_size
        self.translation = None
        self._ensure_installed()
        self._load_languages()

    def _ensure_installed(self):
        """Vérifie si le modèle de traduction est installé."""
        try:
            logger.info("Vérification des modèles de traduction installés...")
            installed_languages = argostranslate.translate.get_installed_languages()
            from_lang = next((lang for lang in installed_languages if lang.code == self.from_code), None)
            to_lang = next((lang for lang in installed_languages if lang.code == self.to_code), None)

            if not from_lang or not to_lang:
                logger.error(f"Modèle de traduction {self.from_code}->{self.to_code} non trouvé.")
                logger.error("Veuillez télécharger le modèle depuis https://www.argosopentech.com/argospm/index/")
                logger.error("Puis installez-le avec la commande :")
                logger.error(f"argostranslate.package.install_from_path('chemin/vers/{self.from_code}_{self.to_code}.argosmodel')")
                raise TranslationError("Modèle de traduction non installé")
            
            logger.info(f"Modèles de traduction {self.from_code}->{self.to_code} trouvés")
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des modèles : {str(e)}")
            raise TranslationError(f"Erreur lors de la vérification des modèles : {str(e)}")

    def _load_languages(self):
        """Charge les langues pour la traduction."""
        try:
            logger.info("Chargement des langues pour la traduction...")
            installed_languages = argostranslate.translate.get_installed_languages()
            self.from_lang = next(lang for lang in installed_languages if lang.code == self.from_code)
            self.to_lang = next(lang for lang in installed_languages if lang.code == self.to_code)
            self.translation = self.from_lang.get_translation(self.to_lang)
            logger.info("Langues chargées avec succès")
        except Exception as e:
            logger.error(f"Erreur lors du chargement des langues : {str(e)}")
            raise TranslationError(f"Erreur lors du chargement des langues : {str(e)}")

    def reset(self):
        """Réinitialise le traducteur."""
        try:
            logger.info("Réinitialisation du traducteur...")
            self.translation = None
            gc.collect()  # Force le nettoyage de la mémoire
            self._load_languages()
            logger.info("Traducteur réinitialisé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de la réinitialisation du traducteur : {str(e)}")
            raise TranslationError(f"Erreur lors de la réinitialisation du traducteur : {str(e)}")

    def _split_text(self, text: str) -> List[str]:
        """
        Divise le texte en morceaux plus petits en respectant la ponctuation.
        
        Args:
            text (str): Le texte à diviser
            
        Returns:
            List[str]: Liste des morceaux de texte
        """
        if len(text) <= self.max_chunk_size:
            return [text]

        # Points de séparation possibles
        separators = ['. ', '? ', '! ', '; ', ', ']
        chunks = []
        current_chunk = ""
        
        # Diviser le texte en phrases
        sentences = re.split(r'([.!?;]\s+)', text)
        
        for i in range(0, len(sentences), 2):
            sentence = sentences[i]
            if i + 1 < len(sentences):
                sentence += sentences[i + 1]  # Ajouter le séparateur
            
            if len(current_chunk) + len(sentence) <= self.max_chunk_size:
                current_chunk += sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        logger.info(f"Texte divisé en {len(chunks)} morceaux")
        return chunks

    def translate(self, text: str) -> Optional[str]:
        """
        Traduit le texte de la langue source vers la langue cible.
        
        Args:
            text (str): Le texte à traduire
            
        Returns:
            Optional[str]: Le texte traduit ou None en cas d'échec
            
        Raises:
            TranslationError: Si la traduction échoue après tous les essais
        """
        if not text or not text.strip():
            logger.warning("Texte vide reçu pour la traduction")
            return text

        # Diviser le texte en morceaux plus petits si nécessaire
        chunks = self._split_text(text)
        if len(chunks) > 1:
            logger.info(f"Texte trop long ({len(text)} caractères), divisé en {len(chunks)} morceaux")
        
        translated_chunks = []
        for i, chunk in enumerate(chunks):
            start_time = time.time()
            last_error = None

            for attempt in range(self.max_retries):
                try:
                    if time.time() - start_time > self.timeout:
                        raise TranslationError("Timeout de la traduction")

                    logger.info(f"Tentative de traduction {attempt + 1}/{self.max_retries} pour le morceau {i + 1}/{len(chunks)}")
                    
                    # Réinitialiser le traducteur à chaque tentative
                    if attempt > 0:
                        self.reset()
                    
                    translated = self.translation.translate(chunk)

                    if not translated or not translated.strip():
                        raise TranslationError("La traduction est vide")

                    logger.info(f"Traduction réussie du morceau {i + 1}/{len(chunks)} : {chunk[:50]}... -> {translated[:50]}...")
                    translated_chunks.append(translated)
                    break

                except Exception as e:
                    last_error = e
                    logger.warning(f"Échec de la traduction du morceau {i + 1}/{len(chunks)} (tentative {attempt + 1}/{self.max_retries}) : {str(e)}")
                    if attempt < self.max_retries - 1:
                        logger.info(f"Attente de 1 seconde avant la prochaine tentative...")
                        time.sleep(1)  # Attente entre les tentatives
            else:
                error_msg = f"Échec de la traduction du morceau {i + 1}/{len(chunks)} après {self.max_retries} tentatives : {str(last_error)}"
                logger.error(error_msg)
                raise TranslationError(error_msg)

        # Recombiner les morceaux traduits
        final_translation = " ".join(translated_chunks)
        logger.info(f"Traduction complète réussie : {text[:50]}... -> {final_translation[:50]}...")
        return final_translation 