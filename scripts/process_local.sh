#!/bin/bash

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérification des arguments
if [ "$#" -lt 1 ]; then
    print_error "Usage: $0 <chemin_vers_video> [chemin_vers_config] [dossier_sortie]"
    print_error "Exemple: $0 ./videos/ma_video.mp4 ./config.yaml ./output"
    exit 1
fi

# Récupération des arguments
VIDEO_PATH="$1"
CONFIG_PATH="${2:-config.yaml}"
OUTPUT_DIR="${3:-./output}"

# Vérification de l'existence de la vidéo
if [ ! -f "$VIDEO_PATH" ]; then
    print_error "La vidéo n'existe pas : $VIDEO_PATH"
    exit 1
fi

# Vérification de l'existence du fichier de configuration
if [ ! -f "$CONFIG_PATH" ]; then
    print_warning "Le fichier de configuration n'existe pas : $CONFIG_PATH"
    print_warning "Création d'un fichier de configuration par défaut..."
    
    # Création du fichier de configuration par défaut
    cat > "$CONFIG_PATH" << EOL
whisper:
  model_name: "base"
  beam_size: 5
  best_of: 5
  temperature: 0.0
  fp16: true
  task: "transcribe"

output:
  base_dir: "$OUTPUT_DIR"
  temp_dir: "$OUTPUT_DIR/temp"
EOL
    print_message "Fichier de configuration créé : $CONFIG_PATH"
fi

# Activation de l'environnement virtuel si présent
if [ -d "venv" ]; then
    print_message "Activation de l'environnement virtuel..."
    source venv/bin/activate
fi

# Exécution du script Python
print_message "Traitement de la vidéo : $VIDEO_PATH"
export PYTHONPATH=src
python3 -m process_local_video --video "$VIDEO_PATH" --config "$CONFIG_PATH" --output-dir "$OUTPUT_DIR"

# Vérification du résultat
if [ $? -eq 0 ]; then
    print_message "Traitement terminé avec succès !"
    print_message "Les résultats sont disponibles dans : $OUTPUT_DIR"
else
    print_error "Une erreur s'est produite lors du traitement"
    exit 1
fi 