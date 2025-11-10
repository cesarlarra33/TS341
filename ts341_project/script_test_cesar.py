# detect_drone.py
import cv2
import numpy as np
import argparse
import os

def parse_args():
    p = argparse.ArgumentParser(description="Détection de drone sur vidéo (soustraction de fond + contours)")
    p.add_argument("--input", "-i", required=True, help="Chemin vers la vidéo d'entrée")
    p.add_argument("--output", "-o", default="output.mp4", help="Chemin vers la vidéo de sortie")
    p.add_argument("--display", "-d", action="store_true", help="Afficher la vidéo en temps réel (fenêtre)")
    p.add_argument("--min-area", type=int, default=50, help="Surface minimale du contour pour être considéré")
    p.add_argument("--max-area", type=int, default=600, help="Surface maximale du contour pour être considéré")
    p.add_argument("--resize-width", type=int, default=1280, help="Largeur redimensionnée pour l'enregistrement/affichage")
    return p.parse_args()

def main():
    args = parse_args()

    if not os.path.exists(args.input):
        print("Fichier d'entrée introuvable :", args.input)
        return

    cap = cv2.VideoCapture(args.input)
    if not cap.isOpened():
        print("Impossible d'ouvrir la vidéo :", args.input)
        return

    # récupère infos vidéo pour l'enregistrement (fps, taille)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    w_in = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h_in = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    # On redimensionne la sortie pour uniformiser (garde aspect ratio)
    target_w = args.resize_width
    scale = target_w / float(w_in)
    target_h = int(h_in * scale)

    # VideoWriter (codec MP4V pour .mp4)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(args.output, fourcc, fps, (target_w, target_h))

    # Soustracteur de fond : MOG2 (adaptatif)
    backSub = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=40, detectShadows=True)

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1

        # redimensionne pour accélérer et standardiser
        frame_resized = cv2.resize(frame, (target_w, target_h))

        # Appliquer la soustraction de fond
        fg_mask = backSub.apply(frame_resized)

        # Supprimer les ombres (si detectShadows=True, les ombres ont valeur 127)
        _, fg_mask = cv2.threshold(fg_mask, 250, 255, cv2.THRESH_BINARY)

        # Morphologie pour enlever le bruit et combler les trous
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel, iterations=1)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_DILATE, kernel, iterations=2)

        # Optionnel : filtrer par couleur sombre (utile si le drone apparaît sombre sur fond clair)
        # Convertir en HSV et créer un masque pour les pixels sombres (ajustable)
        hsv = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2HSV)
        v_channel = hsv[:,:,2]
        _, dark_mask = cv2.threshold(v_channel, 160, 255, cv2.THRESH_BINARY_INV)  # 160 = seuil de luminosité
        # Combine masques : mouvement ET potentiellement sombre
        combined_mask = cv2.bitwise_and(fg_mask, dark_mask)

        # Si tu veux être moins strict (p.ex. drone clair), tu peux revenir à fg_mask seul:
        mask_to_use = combined_mask  # ou fg_mask

        # Trouver contours
        contours, _ = cv2.findContours(mask_to_use, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detections = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < args.min_area or area > args.max_area:
                continue
            x, y, w, h = cv2.boundingRect(cnt)

            # Filtrer rapports d'aspect extrêmes (optionnel)
            aspect = w / float(h + 1e-6)
            if aspect < 0.2 or aspect > 5.0:
                # prob. pas un drone si trop allongé ou trop fin
                continue

            # On peut calculer la "solidité" pour éviter contours creux (optionnel)
            hull_area = cv2.contourArea(cv2.convexHull(cnt))
            solidity = area / float(hull_area + 1e-6)
            if solidity < 0.3:
                continue

            detections.append((x, y, w, h, area))

        # Dessiner les détections sur la frame
        for (x, y, w, h, area) in detections:
            # Boîte rouge épaisse
            cv2.rectangle(frame_resized, (x, y), (x+w, y+h), (0, 0, 255), 2)
            label = f"Drone? area={int(area)}"
            cv2.putText(frame_resized, label, (x, y-8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)

        # Écrire la frame dans le fichier de sortie
        out.write(frame_resized)

        # Afficher si demandé
        if args.display:
            cv2.imshow("Drone Detection", frame_resized)
            # q pour quitter
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    print("Traitement terminé. Vidéo sortie :", args.output)
    cap.release()
    out.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
