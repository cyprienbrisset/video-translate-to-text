import os
import logging
import argostranslate.package

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def install_model(model_path):
    """Installe un modèle Argos Translate."""
    if not os.path.exists(model_path):
        logger.error(f"Le fichier {model_path} n'existe pas.")
        return False
    
    try:
        argostranslate.package.install_from_path(model_path)
        logger.info(f"Modèle installé avec succès depuis {model_path}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de l'installation du modèle : {e}")
        return False

if __name__ == "__main__":
    # Chemin vers le modèle téléchargé
    model_path = "models/en_fr.argosmodel"
    
    if install_model(model_path):
        logger.info("Le modèle a été installé avec succès.")
        logger.info("Vous pouvez maintenant exécuter le script principal.")
    else:
        logger.error("L'installation du modèle a échoué.")
        logger.error("Veuillez télécharger le modèle depuis https://www.argosopentech.com/argospm/index/")
        logger.error("et le placer dans le dossier 'models/' avec le nom 'en_fr.argosmodel'") 