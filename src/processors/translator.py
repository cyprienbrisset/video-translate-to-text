from transformers import MBartForConditionalGeneration, MBart50TokenizerFast
import logging

class Translator:
    def __init__(self, model_name="facebook/mbart-large-50-many-to-many-mmt"):
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initialisation du traducteur avec le modèle {model_name}")
        self.tokenizer = MBart50TokenizerFast.from_pretrained(model_name)
        self.model = MBartForConditionalGeneration.from_pretrained(model_name)
        
    def translate(self, text: str) -> str:
        """
        Traduit le texte en utilisant le modèle mBART.
        
        Args:
            text (str): Le texte à traduire
            
        Returns:
            str: Le texte traduit
        """
        try:
            # Tokenisation du texte
            self.tokenizer.src_lang = "en_XX"
            encoded = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            
            # Génération de la traduction
            generated_tokens = self.model.generate(
                **encoded,
                forced_bos_token_id=self.tokenizer.lang_code_to_id["fr_XX"]
            )
            
            # Décodage de la traduction
            translated_text = self.tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]
            
            return translated_text
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la traduction : {str(e)}")
            raise 