import cv2
import numpy as np
import logging
from pathlib import Path

from ts341_project.ProcessingResult import ProcessingResult
from ts341_project.pipeline.video_block.StatefulProcessingBlock import (
    StatefulProcessingBlock,
)

logger = logging.getLogger(__name__)


class CustomDroneBlock(StatefulProcessingBlock):
    """
    Block de détection de drone utilisant MOG2 pour la détection de mouvement
    et ORB pour le matching de patterns.

    Adapté de script_test1_pauline.py pour l'architecture de pipeline.
    """

    def __init__(
        self,
        pattern_dir: str = None,
        min_matches: int = 2,
        mog2_history: int = 300,
        mog2_var_threshold: int = 20,
        orb_n_features: int = 300,  # OPTI: moins de keypoints
        min_contour_size: int = 5,  # OPTI: ignorer petits objets
        resize_width: int = 1280,  # Frame traitée forcée à largeur 1280
    ):
        """
        Args:
            pattern_dir: Chemin vers le dossier contenant les images de patterns du drone
            min_matches: Nombre minimum de matches ORB pour confirmer un drone
            mog2_history: Nombre de frames d'historique pour MOG2
            mog2_var_threshold: Seuil de variance pour MOG2
            orb_n_features: Nombre de features ORB à détecter
            min_contour_size: Taille minimale des contours à analyser
        """
        # IMPORTANT: désactiver le preprocessing par défaut car on a besoin de BGR
        super().__init__(use_default_preprocessing=False)
        self.name = "CustomDroneBlock"

        # Paramètres
        self.min_matches = min_matches
        self.min_contour_size = min_contour_size
        self.resize_width = resize_width

        # Initialisation MOG2
        self.back_sub = cv2.createBackgroundSubtractorMOG2(
            history=mog2_history, varThreshold=mog2_var_threshold, detectShadows=False
        )

        # Kernel pour opérations morphologiques (plus petit = plus rapide)
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

        # Initialisation ORB (moins de keypoints)
        self.orb = cv2.ORB_create(nfeatures=orb_n_features)
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING)

        # Charger les patterns
        self.patterns = []
        if pattern_dir:
            self._load_patterns(pattern_dir)

    def _load_patterns(self, pattern_dir: str):
        """Charge les patterns de drone pour le matching ORB (lecture en gray, resize 128x128)"""
        pattern_path = Path(pattern_dir)
        if not pattern_path.exists():
            print(f"Dossier patterns introuvable: {pattern_dir}")
            return

        for file_path in pattern_path.glob("*"):
            if file_path.suffix.lower() not in [".jpg", ".png", ".jpeg"]:
                continue

            img = cv2.imread(str(file_path), cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue
            img_small = cv2.resize(img, (128, 128))
            kp, des = self.orb.detectAndCompute(img_small, None)
            if des is not None:
                self.patterns.append((kp, des))
                print(f"Pattern chargé: {file_path.name} ({len(kp)} keypoints)")

    def process_with_memory(
        self, frame: np.ndarray, result: ProcessingResult
    ) -> ProcessingResult:
        """
        Traite une frame avec détection de mouvement MOG2 et matching ORB.

        Args:
            frame: Frame à traiter (BGR ou grayscale)
            result: Résultat de traitement (contient les métadonnées)

        Returns:
            ProcessingResult avec les détections dessinées
        """
        # Forcer la frame traitée à 1280x720
        if self.resize_width is not None:
            target_w = self.resize_width
            target_h = 720
            if (frame.shape[1], frame.shape[0]) != (target_w, target_h):
                frame = cv2.resize(frame, (target_w, target_h))

        # S'assurer qu'on a une image BGR pour MOG2
        if len(frame.shape) == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        # Convertir en niveaux de gris pour ORB
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # --- Détection de mouvement avec MOG2 ---
        fg_mask = self.back_sub.apply(frame)

        # Seuillage pour garder uniquement les pixels très probables
        _, fg_mask = cv2.threshold(fg_mask, 250, 255, cv2.THRESH_BINARY)

        # Opérations morphologiques pour nettoyer le masque
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, self.kernel, iterations=1)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, self.kernel, iterations=1)

        # --- Détection des contours des zones en mouvement ---
        contours, _ = cv2.findContours(
            fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        detections = []

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)

            # Filtrer les contours trop petits
            if w < self.min_contour_size or h < self.min_contour_size:
                continue

            # Extraire la ROI, convertir en gray puis resize 128x128
            roi = frame[y : y + h, x : x + w]
            roi_gray = (
                cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi
            )
            roi_small = cv2.resize(roi_gray, (128, 128))

            match_found = False
            num_matches = 0

            # --- Matching ORB avec les patterns ---
            if self.patterns:
                _, des_roi = self.orb.detectAndCompute(roi_small, None)

                if des_roi is not None:
                    for kp_pat, des_pat in self.patterns:
                        matches = self.bf.knnMatch(des_pat, des_roi, k=2)

                        # Appliquer le ratio test de Lowe
                        good_matches = []
                        for m_n in matches:
                            if len(m_n) == 2:
                                m, n = m_n
                                if m.distance < 0.75 * n.distance:
                                    good_matches.append(m)

                        # Si suffisamment de matches, c'est un drone
                        if len(good_matches) >= self.min_matches:
                            match_found = True
                            num_matches = len(good_matches)
                            break

            # Dessiner les détections
            color = (0, 0, 255) if match_found else (0, 255, 0)
            label = f"Drone détecté ({num_matches})" if match_found else "Poss. Drone"

            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(
                frame, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1
            )

            # Stocker les détections dans les métadonnées
            detections.append(
                {
                    "bbox": (x, y, w, h),
                    "is_drone": match_found,
                    "num_matches": num_matches,
                    "label": label,
                }
            )

        # Mettre à jour le résultat
        result.frame = frame
        result.metadata["drone_detections"] = detections
        result.metadata["num_detections"] = len(detections)
        result.metadata["num_confirmed_drones"] = sum(
            1 for d in detections if d["is_drone"]
        )

        # -------------------------------
        # LOGIQUE D’AFFICHAGE DES COORDONNÉES
        # -------------------------------

        num_boxes = len(detections)

        # Reset des données
        result.metadata["drone_center"] = None
        result.metadata["confidence"] = None
        result.metadata["coord_display"] = ""

        # Cas 1 : Trop de détections → rien
        if num_boxes > 5:
            result.metadata["coord_display"] = "Trop de détections : 0% fiable"

        # Cas 2 : Une seule box → 90% fiable
        elif num_boxes == 1:
            det = detections[0]
            x, y, w, h = det["bbox"]
            cx = x + w // 2
            cy = y + h // 2

            result.metadata["drone_center"] = (cx, cy)
            result.metadata["confidence"] = 90
            result.metadata["coord_display"] = f"Centre: ({cx}, {cy}) — 90% fiable"

            # Dessin
            cv2.circle(frame, (cx, cy), 5, (255, 255, 0), -1)
            cv2.putText(
                frame,
                "90% fiable",
                (cx + 10, cy),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 0),
                2,
            )

        # Cas 3 : 2, 3, 4 ou 5 boxes → centre de la plus grande box + fiabilité = 1/nb
        elif 2 <= num_boxes <= 5:

            # Trouver la plus grande box (aire = w*h)
            biggest = max(detections, key=lambda d: d["bbox"][2] * d["bbox"][3])

            x, y, w, h = biggest["bbox"]
            cx = x + w // 2
            cy = y + h // 2

            confidence = round((1 / num_boxes) * 100, 1)

            result.metadata["drone_center"] = (cx, cy)
            result.metadata["confidence"] = confidence
            result.metadata["coord_display"] = (
                f"Centre: ({cx}, {cy}) — {confidence}% fiable"
            )

            # Dessin
            cv2.circle(frame, (cx, cy), 5, (255, 255, 0), -1)
            cv2.putText(
                frame,
                f"{confidence}% fiable",
                (cx + 10, cy),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 0),
                2,
            )

        # --- Affichage des coordonnées en bas à gauche ---
        if result.metadata["drone_center"] is not None:
            cx, cy = result.metadata["drone_center"]
            text = f"Coordonnées : X={cx}, Y={cy}"

            h = frame.shape[0]
            cv2.putText(
                frame,
                text,
                (10, h - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )

        return result
