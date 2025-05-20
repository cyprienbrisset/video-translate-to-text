import cv2
import numpy as np

# Lire l'image
image = cv2.imread('output/first_frame.jpg')

# Initialiser le détecteur de visage d'OpenCV
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Convertir l'image en niveaux de gris
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Détecter les visages
faces = face_cascade.detectMultiScale(gray, 1.3, 5)

if len(faces) > 0:
    # Prendre le plus grand visage détecté
    face = max(faces, key=lambda x: x[2] * x[3])
    x, y, w, h = face
    
    # Ajouter des marges
    height, width = image.shape[:2]
    pad_top = 40
    pad_bottom = 40
    pad_left = 20
    pad_right = 20
    
    y1 = max(0, y - pad_top)
    y2 = min(height, y + h + pad_bottom)
    x1 = max(0, x - pad_left)
    x2 = min(width, x + w + pad_right)
    
    # Dessiner le rectangle autour du visage
    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
    
    # Sauvegarder l'image avec le rectangle
    cv2.imwrite('output/face_detected.jpg', image)
    
    print(f'Visage détecté aux coordonnées :')
    print(f'x1: {x1}, y1: {y1}, x2: {x2}, y2: {y2}')
else:
    print('Aucun visage détecté dans l\'image') 