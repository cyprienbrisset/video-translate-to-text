# Workflow N8N pour la Génération Audio

Ce workflow N8N permet de générer un fichier audio à partir d'un fichier JSON de transcription, en respectant les timestamps et en utilisant la synthèse vocale.

## Prérequis

1. N8N installé et configuré
2. FFmpeg installé sur le système
3. gTTS (Google Text-to-Speech) installé :
   ```bash
   pip install gTTS
   ```

## Installation

1. Importer le fichier `audio-generation-workflow.json` dans N8N
2. Activer le workflow

## Fonctionnement

Le workflow :
1. Reçoit le fichier JSON de transcription via un webhook
2. Lit le contenu du fichier JSON
3. Pour chaque segment :
   - Génère un fichier audio temporaire avec gTTS
   - Respecte les timestamps du segment
4. Combine tous les segments avec FFmpeg en respectant les timestamps
5. Nettoie les fichiers temporaires

## Utilisation

1. Envoyer une requête POST au webhook avec le fichier JSON de transcription
2. Le workflow générera automatiquement l'audio
3. Le fichier audio généré sera nommé `[nom_du_fichier_json]_generated.wav`

## Format du JSON d'entrée

Le fichier JSON doit contenir un tableau `segments` avec la structure suivante :
```json
{
  "segments": [
    {
      "start": 0.0,
      "end": 2.5,
      "text": "Texte original",
      "text_translated": "Texte traduit"  // Optionnel
    }
  ]
}
```

## Notes

- Le workflow utilise gTTS pour la synthèse vocale en français
- Les timestamps sont respectés grâce à FFmpeg
- Les fichiers temporaires sont automatiquement nettoyés
- L'audio final est en WAV 16kHz mono 