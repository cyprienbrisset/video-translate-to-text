import cv2
import os

# Paramètres
video_path = 'input/video_test.webm'
output_dir = 'output'
os.makedirs(output_dir, exist_ok=True)

# Initialiser le détecteur de visage d'OpenCV
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Ouvrir la vidéo
cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
duration = total_frames / fps

found = False
for sec in range(15, int(duration)):
    frame_id = int(sec * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
    ret, frame = cap.read()
    if not ret:
        continue
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    if len(faces) > 0:
        face = max(faces, key=lambda x: x[2] * x[3])
        x, y, w, h = face
        # Ajouter des marges
        height, width = frame.shape[:2]
        pad_top = 40
        pad_bottom = 40
        pad_left = 20
        pad_right = 20
        y1 = max(0, y - pad_top)
        y2 = min(height, y + h + pad_bottom)
        x1 = max(0, x - pad_left)
        x2 = min(width, x + w + pad_right)
        # Dessiner le rectangle
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        # Sauvegarder l'image
        out_img = os.path.join(output_dir, f'first_face_after_15s_at_{sec}s.jpg')
        cv2.imwrite(out_img, frame)
        print(f'Visage détecté à {sec} secondes (frame {frame_id}) :')
        print(f'x1: {x1}, y1: {y1}, x2: {x2}, y2: {y2}')
        print(f'Image sauvegardée : {out_img}')
        found = True
        break

cap.release()
if not found:
    print('Aucun visage détecté après la 15e seconde dans la vidéo.') 