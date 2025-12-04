from ultralytics import YOLO
import cv2
import time

model = YOLO("best.pt")

cap = cv2.VideoCapture("dehaut_2.mp4")
if not cap.isOpened():
    raise Exception("Impossible d'ouvrir la vidéo")

TARGET_WIDTH = 1280
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
out = None

frame_count = 0
total_inference_time = 0.0
start_global = time.time()  # temps début du script

while True:
    ret, frame = cap.read()
    if not ret:
        break

    h, w = frame.shape[:2]
    new_height = int(h * (TARGET_WIDTH / w))
    frame = cv2.resize(frame, (TARGET_WIDTH, new_height))

    # --- Mesure du temps d'inférence ---
    t0 = time.time()
    results = model(frame)
    inference_time = time.time() - t0

    total_inference_time += inference_time
    frame_count += 1

    annotated = results[0].plot()

    if out is None:
        out = cv2.VideoWriter(
            "output.mp4",
            fourcc,
            cap.get(cv2.CAP_PROP_FPS),
            (annotated.shape[1], annotated.shape[0])
        )

    out.write(annotated)

cap.release()
if out is not None:
    out.release()

# --- Temps total ---
total_time = time.time() - start_global

# --- FPS moyen d'inférence ---
if frame_count > 0:
    avg_fps = frame_count / total_inference_time
else:
    avg_fps = 0

print("\n===== STATISTIQUES =====")
print(f"Frames traitées : {frame_count}")
print(f"Temps total : {total_time:.2f} sec")
print(f"FPS moyen d'inférence : {avg_fps:.2f} fps")
print("========================")
