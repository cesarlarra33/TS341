#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import numpy as np
import argparse
import os

def parse_args():
    p = argparse.ArgumentParser(description="Suivi d'objet avec MOG2 + Kalman (un seul objet)")
    p.add_argument("--input", "-i", required=True, help="Chemin vers la vidéo d'entrée")
    p.add_argument("--output", "-o", default="output_kalman_mog2.mp4", help="Chemin vers la vidéo de sortie")
    p.add_argument("--display", "-d", action="store_true", help="Afficher la vidéo en temps réel")
    p.add_argument("--resize-width", type=int, default=1280, help="Largeur redimensionnée pour la sortie")
    p.add_argument("--min-area", type=int, default=100, help="Aire minimale d'un blob (à ignorer si plus petit)")
    p.add_argument("--max-gate", type=float, default=200.0, help="Distance max (pixels) entre prédiction Kalman et blob pour accepter")
    p.add_argument("--max-lost", type=int, default=15, help="Nombre de frames sans détection avant ré-initialisation")
    return p.parse_args()

def init_kalman(dt):
    # état: [x, y, vx, vy], mesure: [x, y]
    kf = cv2.KalmanFilter(4, 2)
    kf.transitionMatrix = np.array([
        [1, 0, dt, 0],
        [0, 1, 0, dt],
        [0, 0, 1, 0 ],
        [0, 0, 0, 1 ]
    ], dtype=np.float32)
    kf.measurementMatrix = np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0]
    ], dtype=np.float32)
    # Process noise: small -> plus de confiance dans modèle
    kf.processNoiseCov = np.eye(4, dtype=np.float32) * 1e-2
    # Measurement noise: adapter si détecteur noisy
    kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * 1e-1
    # Initial state/cov
    kf.statePre = np.zeros((4,1), dtype=np.float32)
    kf.statePost = np.zeros((4,1), dtype=np.float32)
    return kf

def main():
    args = parse_args()

    if not os.path.exists(args.input):
        print("Fichier vidéo introuvable :", args.input)
        return

    cap = cv2.VideoCapture(args.input)
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        fps = 25.0
    w_in = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
    h_in = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
    target_w = args.resize_width
    target_h = int(h_in * target_w / w_in)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(args.output, fourcc, fps, (target_w, target_h))

    # --- Background subtractor ---
    backSub = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=16, detectShadows=False)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))

    # --- Kalman ---
    dt = 1.0 / fps
    kalman = init_kalman(dt)
    measurement = np.zeros((2,1), dtype=np.float32)

    has_track = False
    lost_frames = 0

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1

        frame_resized = cv2.resize(frame, (target_w, target_h))
        gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)

        # --- Kalman prediction ---
        pred = kalman.predict()  # shape (4,1)
        px, py = float(pred[0]), float(pred[1])
        px_i, py_i = int(px), int(py)

        # --- MOG2 -> mask mouvement ---
        fg_mask = backSub.apply(frame_resized)
        _, fg_mask = cv2.threshold(fg_mask, 254, 255, cv2.THRESH_BINARY)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel, iterations=1)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel, iterations=1)
        # Optionnel: petite dilatation pour fusionner fragments
        fg_mask = cv2.dilate(fg_mask, kernel, iterations=1)

        # --- Contours blobs en mouvement ---
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        best_detection = None
        best_distance = float("inf")

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = w * h
            if area < args.min_area:
                continue

            cx = x + w / 2.0
            cy = y + h / 2.0

            # distance euclidienne à la prédiction
            dist = np.hypot(cx - px, cy - py)

            # privilégier blob le plus proche de la prédiction
            if dist < best_distance:
                best_distance = dist
                best_detection = (x, y, w, h, cx, cy, area)

        # --- Gating : n'accepte que si proche de la prédiction (ou si pas de track) ---
        accepted = False
        if best_detection is not None:
            x, y, w, h, cx, cy, area = best_detection
            # si on a déjà un track, appliquer gate
            if has_track:
                if best_distance <= args.max_gate:
                    accepted = True
            else:
                # si pas de track, accepter le plus gros blob (heuristique)
                accepted = True

        if accepted:
            # Mise à jour Kalman
            measurement[0,0] = float(cx)
            measurement[1,0] = float(cy)

            if not has_track:
                # initialisation de l'état (position + vitesse nulle)
                kalman.statePre = np.array([[cx],[cy],[0.0],[0.0]], dtype=np.float32)
                kalman.statePost = np.array([[cx],[cy],[0.0],[0.0]], dtype=np.float32)
                has_track = True
                lost_frames = 0
            else:
                kalman.correct(measurement)
                lost_frames = 0

            # dessiner la bbox choisie
            cv2.rectangle(frame_resized, (int(x), int(y)), (int(x+w), int(y+h)), (0,0,255), 2)
            cv2.putText(frame_resized, "Cible (Kalman)", (int(x), int(y)-6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1)
        else:
            # pas de mesure valide -> on considère que la cible est momentanément perdue
            if has_track:
                lost_frames += 1
                if lost_frames > args.max_lost:
                    # réinitialiser le track si perdu trop longtemps
                    has_track = False
                    lost_frames = 0

        # --- Visualisation prédiction et mask ---
        # point prédit (bleu)
        if has_track:
            # mise à jour prédiction après correction déjà faite ci-dessus
            pred_post = kalman.statePost
            ppx, ppy = int(pred_post[0]), int(pred_post[1])
            cv2.circle(frame_resized, (ppx, ppy), 6, (255,0,0), -1)
            cv2.putText(frame_resized, f"Pred: {ppx},{ppy}", (ppx+8, ppy+8), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,0,0), 1)
        else:
            # prédiction brute (sans track)
            cv2.circle(frame_resized, (px_i, py_i), 4, (200,200,200), 1)

        # mini HUD
        cv2.putText(frame_resized, f"Frame: {frame_idx}", (10,20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1)
        cv2.putText(frame_resized, f"Track: {'ON' if has_track else 'OFF'}  Lost:{lost_frames}", (10,40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

        out.write(frame_resized)

        if args.display:
            cv2.imshow("Tracking (Kalman+MOG2)", frame_resized)
            cv2.imshow("Mouvement mask", fg_mask)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

    cap.release()
    out.release()
    cv2.destroyAllWindows()
    print("✅ Traitement terminé. Vidéo sortie :", args.output)

if __name__ == "__main__":
    main()
