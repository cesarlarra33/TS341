# en utilisant l'algo de Farneback pour le calcul du flux optique
import cv2
import numpy as np

directory = "video_drone1"
file = "foreground_masks_double_threshold.avi"
cap = cv2.VideoCapture(directory + "/" + file)
if not cap.isOpened():
    raise RuntimeError("Impossible d'ouvrir la vidéo")

# lire une frame pour récupérer la taille et la fps
ret, frame1 = cap.read()
if not ret:
    raise RuntimeError("La vidéo ne contient aucune frame")
height, width = frame1.shape[:2]
fps = cap.get(cv2.CAP_PROP_FPS)
if fps is None or fps <= 0 or np.isnan(fps):
    fps = 20.0
# Use a codec/container that is widely supported for debugging (MJPG + .avi)
fourcc = cv2.VideoWriter_fourcc(*"MJPG")
out_file = directory + "/optical_flow.avi"
# We will write 3-channel BGR frames to be compatible with most codecs/players
out = cv2.VideoWriter(out_file, fourcc, fps, (width, height), True)
if not out.isOpened():
    raise RuntimeError(f"Impossible d'ouvrir le VideoWriter pour '{out_file}'")
prvs = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
hsv = np.zeros_like(frame1)
hsv[..., 1] = 255

while True:
    ret, frame2 = cap.read()
    if not ret:
        break
    next = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    flow = cv2.calcOpticalFlowFarneback(prvs, next, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
    hsv[..., 0] = ang * 180 / np.pi / 2
    hsv[..., 2] = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX)
    bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    out.write(bgr)
    prvs = next

cap.release()
out.release()
