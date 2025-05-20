# Workflow N8N pour la Transcription et Traduction de Vidéos

Ce workflow N8N permet de :
1. Recevoir une vidéo via un webhook
2. Extraire l'audio en WAV (16kHz, mono)
3. Transmettre l'audio à une API Whisper pour la transcription
4. Traduire le texte via une API de traduction
5. Sauvegarder les résultats dans un fichier JSON

## Prérequis

1. N8N installé et configuré
2. FFmpeg installé sur le système
3. API Whisper accessible sur `http://localhost:9000`
4. API de traduction accessible sur `http://localhost:5000`

## Installation

1. Importer le fichier `video-transcription-workflow.json` dans N8N
2. Configurer les endpoints des APIs si nécessaire
3. Activer le workflow

## Utilisation

1. Envoyer une requête POST au webhook avec un fichier vidéo
2. Le workflow traitera automatiquement la vidéo
3. Les résultats seront sauvegardés dans un fichier JSON avec le format :
   ```json
   {
     "original_text": "Texte original",
     "translated_text": "Texte traduit",
     "segments": [
       {
         "start": 0.0,
         "end": 2.5,
         "text": "Segment de texte",
         "words": [
           {
             "word": "mot",
             "start": 0.0,
             "end": 0.5
           }
         ]
       }
     ],
     "language": "langue détectée"
   }
   ```

## Configuration des APIs

### API Whisper
- Endpoint : `http://localhost:9000/asr`
- Paramètres :
  - `audio_file` : Chemin du fichier audio
  - `model` : Modèle Whisper (medium)
  - `language` : Langue (auto)
  - `word_timestamps` : true

### API de Traduction
- Endpoint : `http://localhost:5000/translate`
- Paramètres :
  - `text` : Texte à traduire
  - `source_lang` : Langue source (auto)
  - `target_lang` : Langue cible (fr)

## Notes

- Le workflow utilise FFmpeg pour extraire l'audio en WAV 16kHz mono
- Les timestamps sont générés au niveau des mots pour une meilleure précision
- Le fichier de sortie est nommé selon le nom du fichier vidéo d'entrée 