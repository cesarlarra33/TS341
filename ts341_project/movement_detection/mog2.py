import cv2
import numpy as np

directory = "video_drone2"
file = "input_video.mp4"
varThreshold = 64
cap = cv2.VideoCapture(directory + "/" + file)
if not cap.isOpened():
    raise RuntimeError("Impossible d'ouvrir la vidéo")

backSub = cv2.createBackgroundSubtractorMOG2(varThreshold=varThreshold)

# lire une frame pour récupérer la taille et la fps
ret, frame = cap.read()
if not ret:
    raise RuntimeError("La vidéo ne contient aucune frame")
height, width = frame.shape[:2]
fps = cap.get(cv2.CAP_PROP_FPS)
if fps is None or fps <= 0 or np.isnan(fps):
    fps = 20.0

# Use a codec/container that is widely supported for debugging (MJPG + .avi)
fourcc = cv2.VideoWriter_fourcc(*"MJPG")
out_file = directory + "/foreground_masks_threshold" + str(varThreshold) + ".avi"
# We will write 3-channel BGR frames to be compatible with most codecs/players
out = cv2.VideoWriter(out_file, fourcc, fps, (width, height), True)
if not out.isOpened():
    raise RuntimeError(f"Impossible d'ouvrir le VideoWriter pour '{out_file}'")

# traiter la première frame lue puis continuer la lecture en streaming
fg_mask = backSub.apply(frame)
# garantir uint8
fg_mask = fg_mask.astype(np.uint8)
# si le masque est 2D (gris), convertir en BGR pour l'écriture
if fg_mask.ndim == 2:
    write_frame = cv2.cvtColor(fg_mask, cv2.COLOR_GRAY2BGR)
else:
    write_frame = fg_mask
out.write(write_frame)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    fg_mask = backSub.apply(frame)
    fg_mask = fg_mask.astype(np.uint8)
    if fg_mask.ndim == 2:
        write_frame = cv2.cvtColor(fg_mask, cv2.COLOR_GRAY2BGR)
    else:
        write_frame = fg_mask
    out.write(write_frame)

cap.release()
out.release()
