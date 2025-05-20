import yaml
import logging
from typing import Dict

logger = logging.getLogger(__name__)

def load_config(config_path: str) -> Dict:
    """Charge la configuration depuis un fichier YAML"""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la configuration: {e}")
        raise 