# 🎬 Video-to-Text-Translate

> Un outil puissant pour extraire, transcrire et traduire automatiquement le contenu audio des vidéos. Parfait pour l'analyse de contenu vidéo et la génération de sous-titres multilingues.

## ✨ Fonctionnalités

- 🎵 **Extraction Audio** : Conversion de vidéos en audio WAV optimisé
- 🗣️ **Transcription Intelligente** : Utilisation de Whisper pour une transcription précise
- 🌍 **Traduction Automatique** : Support multilingue avec mBART
- 📝 **Format JSON** : Export structuré avec timestamps et métadonnées
- ⚡ **Performance** : Optimisé pour Apple Silicon (M1/M2)
- 🔄 **Traitement Parallèle** : Support du traitement de plusieurs vidéos
- 🧹 **Nettoyage Automatique** : Gestion des fichiers temporaires
- 🎯 **Synchronisation Précise** : Maintien de la synchronisation audio-vidéo avec préservation des segments non vocaux
- 🎵 **Gestion Intelligente** : Conservation automatique de la musique et des effets sonores

## 🛠️ Prérequis

- 💻 macOS (testé sur Apple Silicon M1/M2)
- 🐍 Miniforge/Conda
- 🎥 FFmpeg
- 💾 4GB d'espace disque minimum
- 🧠 8GB de RAM recommandés

## 📥 Installation

### 1. Installation de Miniforge et des dépendances

Le projet utilise Miniforge pour gérer les dépendances Python et les packages natifs. Un script d'installation automatique est fourni :

```bash
# Rendre le script exécutable
chmod +x scripts/install_miniforge.sh

# Lancer l'installation
./scripts/install_miniforge.sh
```

Ce script va :
- 📦 Installer Miniforge
- 🐍 Créer un environnement Conda `video-to-text`
- 🔧 Installer toutes les dépendances nécessaires
- ✅ Vérifier l'installation

### 2. Configuration

Le fichier `config.yaml` permet de configurer :
- 🤖 Le modèle Whisper à utiliser
- 🌐 Les options de traduction
- 📂 Les chemins de sortie

Exemple de configuration :
```yaml
whisper:
  model: "base"  # Options: tiny, base, small, medium, large
  language: "auto"
  translate: true
  target_language: "fr"

translation:
  model: "facebook/mbart-large-50-many-to-many-mmt"
  max_length: 512

output:
  directory: "./output"
  temp_directory: "./output/temp"
  format: "json"
```

## 🚀 Utilisation

### Traitement d'une vidéo locale

```bash
# Activer l'environnement Conda
conda activate video-to-text

# Traiter une vidéo
python src/process_local_video.py chemin/vers/video.mp4
```

Options disponibles :
- `--config` : Chemin vers le fichier de configuration (par défaut : config.yaml)
- `--output` : Répertoire de sortie (par défaut : ./output)

### Format de sortie

Le résultat est sauvegardé dans un fichier JSON contenant :
- 📝 Le texte original
- 🌐 Le texte traduit (si la traduction est activée)
- ⏱️ Les segments avec timestamps
- 🌍 La langue détectée
- 📅 La date de traitement
- 🎵 Les segments non vocaux (musique, applaudissements, etc.)

Exemple de sortie JSON :
```json
{
  "original_text": "Hello, this is a test video.",
  "translated_text": "Bonjour, ceci est une vidéo test.",
  "segments": [
    {
      "start": 0.0,
      "end": 12.0,
      "text": "[Music]",
      "type": "non_vocal"
    },
    {
      "start": 12.0,
      "end": 16.0,
      "text": "[Applause]",
      "type": "non_vocal"
    },
    {
      "start": 16.0,
      "end": 20.0,
      "text": "Hello, this is a test video.",
      "type": "vocal"
    }
  ],
  "language": "en",
  "processing_date": "2024-05-20T12:00:00"
}
```

## 📁 Structure du projet

```
.
├── 📄 config.yaml           # Configuration du projet
├── 📂 scripts/
│   ├── 📄 install_miniforge.sh  # Script d'installation
│   └── 📄 process_local.sh      # Script de traitement
├── 📂 src/
│   ├── 📂 processors/      # Processeurs
│   │   ├── 📄 audio_extractor.py
│   │   ├── 📄 whisper_processor.py
│   │   └── 📄 translator.py
│   └── 📂 utils/          # Utilitaires
│       └── 📄 config.py
└── 📂 output/             # Résultats
```

## 💻 Développement

### Environnement de développement

```bash
# Activer l'environnement
conda activate video-to-text

# Vérifier l'installation
python -c "import sentencepiece; import whisper; print('OK')"
```

### Tests

Pour tester le traitement d'une vidéo :
```bash
python src/process_local_video.py ./scripts/video.webm
```

### Modèles Whisper Disponibles

| Modèle | Taille | VRAM Requise | Vitesse Relative |
|--------|---------|--------------|------------------|
| tiny   | 39M     | ~1GB         | ~10x            |
| base   | 74M     | ~1GB         | ~7x             |
| small  | 244M    | ~2GB         | ~4x             |
| medium | 769M    | ~5GB         | ~2x             |
| large  | 1550M   | ~10GB        | 1x              |

## 🤝 Contribution

Les contributions sont les bienvenues ! Voici comment contribuer :

1. Fork le projet
2. Créer une branche pour votre fonctionnalité (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## 🙏 Remerciements

- [OpenAI Whisper](https://github.com/openai/whisper) pour le modèle de transcription
- [Hugging Face](https://huggingface.co/) pour les modèles de traduction
- [FFmpeg](https://ffmpeg.org/) pour le traitement audio

### Traitement Audio

Le système gère intelligemment différents types de segments audio :

1. **Segments Vocaux** :
   - Transcription et traduction
   - Synchronisation précise avec l'audio original
   - Remplacement par l'audio TTS traduit

2. **Segments Non Vocaux** :
   - Détection automatique (musique, applaudissements, etc.)
   - Conservation de l'audio original
   - Maintien de la synchronisation

3. **Synchronisation** :
   - Préservation des timestamps originaux
   - Mélange intelligent de l'audio TTS et de l'audio original
   - Gestion des transitions entre segments 