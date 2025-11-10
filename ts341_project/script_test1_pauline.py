import cv2
import numpy as np
import os
import argparse

def parse_args():
    p = argparse.ArgumentParser(description="Détection de drone avec MOG2 + ORB sans tracker")
    p.add_argument("--input", "-i", required=True, help="Chemin vers la vidéo d'entrée")
    p.add_argument("--patterns", "-p", required=True, help="Dossier contenant les images de pattern du drone")
    p.add_argument("--output", "-o", default="output_orb_no_tracker.mp4", help="Chemin vers la vidéo de sortie")
    p.add_argument("--display", "-d", action="store_true", help="Afficher la vidéo en temps réel")
    p.add_argument("--resize-width", type=int, default=1280, help="Largeur redimensionnée pour la sortie")
    p.add_argument("--min-matches", type=int, default=10, help="Nombre minimum de matches ORB pour confirmer un drone")
    return p.parse_args()

def load_patterns(pattern_dir, orb):
    pattern_features = []
    for fname in os.listdir(pattern_dir):
        if not fname.lower().endswith(('.jpg', '.png', '.jpeg')):
            continue
        path = os.path.join(pattern_dir, fname)
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        img_small = cv2.resize(img, (128,128))
        kp, des = orb.detectAndCompute(img_small, None)
        if des is not None:
            pattern_features.append((kp, des))
            print(f"✅ Pattern chargé : {fname} ({len(kp)} keypoints)")
    return pattern_features

def main():
    args = parse_args()

    if not os.path.exists(args.input) or not os.path.isdir(args.patterns):
        print("Fichier vidéo ou dossier patterns introuvable")
        return

    cap = cv2.VideoCapture(args.input)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    w_in = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h_in = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    target_w = args.resize_width
    target_h = int(h_in * target_w / w_in)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(args.output, fourcc, fps, (target_w, target_h))

    # --- Initialisation MOG2 + ORB ---
    backSub = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=20, detectShadows=False)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
    orb = cv2.ORB_create(nfeatures=500)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING)

    patterns = load_patterns(args.patterns, orb)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_resized = cv2.resize(frame, (target_w, target_h))
        gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)

        # --- Masque de mouvement (MOG2) ---
        fg_mask = backSub.apply(frame_resized)
        _, fg_mask = cv2.threshold(fg_mask, 250, 255, cv2.THRESH_BINARY)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel, iterations=1)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel, iterations=1)

        # --- Contours zones en mouvement ---
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w < 5 or h < 5:
                continue
            roi = gray[y:y+h, x:x+w]
            roi_small = cv2.resize(roi, (128,128))  # optimisation

            match_found = False
            if patterns:
                kp_roi, des_roi = orb.detectAndCompute(roi_small, None)
                if des_roi is not None:
                    for kp_pat, des_pat in patterns:
                        matches = bf.knnMatch(des_pat, des_roi, k=2)
                        good = []
                        for m_n in matches:
                            if len(m_n) == 2:
                                m, n = m_n
                                if m.distance < 0.75 * n.distance:
                                    good.append(m)
                        if len(good) >= args.min_matches:
                            match_found = True
                            break

            color = (0,0,255) if match_found else (0,255,0)
            label = "Drone détecté" if match_found else "Poss. Drone"
            cv2.rectangle(frame_resized, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame_resized, label, (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        out.write(frame_resized)
        if args.display:
            cv2.imshow("Détection", frame_resized)
            cv2.imshow("Mouvement", fg_mask)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    out.release()
    cv2.destroyAllWindows()
    print("✅ Traitement terminé. Vidéo sortie :", args.output)

if __name__ == "__main__":
    main()
