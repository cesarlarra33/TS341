#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import numpy as np
import argparse
import os

# ================================
# Filtre Alpha-Beta
# ================================
class AlphaBetaFilter:
    def __init__(self, alpha=0.3, beta=0.05, dt=1/30):
        self.alpha = alpha
        self.beta = beta
        self.dt = dt
        self.initialized = False
        
        # États
        self.x = 0.0  
        self.y = 0.0
        self.vx = 0.0 
        self.vy = 0.0

    def reset(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.initialized = True

    def predict(self):
        # modèle mouvement uniforme
        self.x_pred = self.x + self.vx * self.dt
        self.y_pred = self.y + self.vy * self.dt
        return self.x_pred, self.y_pred

    def update(self, mx, my):
        # erreur de mesure vs prédiction
        rx = mx - self.x_pred
        ry = my - self.y_pred

        # correction position
        self.x = self.x_pred + self.alpha * rx
        self.y = self.y_pred + self.alpha * ry

        # correction vitesse
        self.vx = self.vx + self.beta * (rx / self.dt)
        self.vy = self.vy + self.beta * (ry / self.dt)


# ================================
# ARGS
# ================================
def parse_args():
    p = argparse.ArgumentParser(description="Suivi d'objet avec MOG2 + Alpha-Beta Filter")
    p.add_argument("--input", "-i", required=True, help="Vidéo d'entrée")
    p.add_argument("--output", "-o", default="output_alpha_beta.mp4")
    p.add_argument("--display", "-d", action="store_true")
    p.add_argument("--resize-width", type=int, default=1280)
    p.add_argument("--min-area", type=int, default=100)
    p.add_argument("--max-gate", type=float, default=200.0)
    p.add_argument("--max-lost", type=int, default=15)
    return p.parse_args()


# ================================
# MAIN
# ================================
def main():
    args = parse_args()
    if not os.path.exists(args.input):
        print("❌ Fichier introuvable :", args.input)
        return

    cap = cv2.VideoCapture(args.input)
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        fps = 25.0

    w_in = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h_in = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    target_w = args.resize_width
    target_h = int(h_in * target_w / w_in)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(args.output, fourcc, fps, (target_w, target_h))

    # Background subtractor
    backSub = cv2.createBackgroundSubtractorMOG2(
        history=500,
        varThreshold=16,
        detectShadows=False
    )
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))

    # Filtre alpha-beta
    dt = 1.0 / fps
    ab = AlphaBetaFilter(alpha=0.3, beta=0.05, dt=dt)

    has_track = False
    lost_frames = 0

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1

        frame_resized = cv2.resize(frame, (target_w, target_h))

        # Prediction alpha-beta
        if has_track:
            px, py = ab.predict()
            px_i, py_i = int(px), int(py)
        else:
            px_i, py_i = -100, -100

        # MOG2
        fg_mask = backSub.apply(frame_resized)
        _, fg_mask = cv2.threshold(fg_mask, 254, 255, cv2.THRESH_BINARY)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        fg_mask = cv2.dilate(fg_mask, kernel, iterations=1)

        # Contours
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        best_detection = None
        best_distance = float("inf")

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = w * h
            if area < args.min_area:
                continue

            cx = x + w / 2
            cy = y + h / 2

            if has_track:
                dist = np.hypot(cx - px, cy - py)
            else:
                dist = 0  # si aucune piste, on prend le plus gros blob

            if dist < best_distance:
                best_distance = dist
                best_detection = (x,y,w,h,cx,cy,area)

        accepted = False

        if best_detection is not None:
            x, y, w, h, cx, cy, area = best_detection

            if has_track:
                if best_distance <= args.max_gate:
                    accepted = True
            else:
                accepted = True

        if accepted:
            if not has_track:
                ab.reset(cx, cy)
                has_track = True
                lost_frames = 0
            else:
                ab.update(cx, cy)
                lost_frames = 0

            # dessiner bounding box
            cv2.rectangle(frame_resized, (int(x), int(y)), (int(x+w), int(y+h)), (0,0,255), 2)
        else:
            if has_track:
                lost_frames += 1
                ab.predict()  # continue mouvement

                if lost_frames > args.max_lost:
                    has_track = False
                    lost_frames = 0

        # Dessiner point prédit
        if has_track:
            cv2.circle(frame_resized, (int(ab.x), int(ab.y)), 5, (255,0,0), -1)

        cv2.putText(frame_resized, f"Frame:{frame_idx}", (10,20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

        out.write(frame_resized)

        if args.display:
            cv2.imshow("AlphaBeta Tracking", frame_resized)
            cv2.imshow("Mask", fg_mask)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    out.release()
    cv2.destroyAllWindows()

    print("✅ Vidéo générée :", args.output)


if __name__ == "__main__":
    main()
