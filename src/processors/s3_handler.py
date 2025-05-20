import logging
from typing import Dict, List
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class S3Handler:
    """Gestionnaire des opérations S3"""
    def __init__(self, config: Dict):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=config['aws_access_key_id'],
            aws_secret_access_key=config['aws_secret_access_key'],
            region_name=config['region_name']
        )
        self.bucket_name = config['bucket_name']

    def list_video_files(self) -> List[str]:
        """Liste tous les fichiers vidéo dans le bucket"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix='videos/'
            )
            return [
                obj['Key'] for obj in response.get('Contents', [])
                if obj['Key'].lower().endswith(('.mp4', '.avi', '.mov'))
            ]
        except ClientError as e:
            logger.error(f"Erreur lors de la liste des fichiers: {e}")
            raise

    def download_file(self, key: str, local_path: str) -> None:
        """Télécharge un fichier depuis S3"""
        try:
            self.s3_client.download_file(self.bucket_name, key, local_path)
        except ClientError as e:
            logger.error(f"Erreur lors du téléchargement de {key}: {e}")
            raise 