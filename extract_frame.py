import cv2
import os

# Créer le dossier output s'il n'existe pas
os.makedirs('output', exist_ok=True)

# Lire la vidéo
cap = cv2.VideoCapture('input/video_test.webm')

# Lire la première image
ret, frame = cap.read()

if ret:
    # Sauvegarder l'image
    cv2.imwrite('output/first_frame.jpg', frame)
    print('Première image extraite avec succès')
else:
    print('Erreur lors de la lecture de la vidéo')

# Libérer les ressources
cap.release() 