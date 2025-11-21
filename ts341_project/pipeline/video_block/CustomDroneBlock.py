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
        min_matches: int = 10,
        resize_width: int = 1024,
        mog2_history: int = 500,
        mog2_var_threshold: int = 20,
        orb_n_features: int = 500,
        min_contour_size: int = 5,
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

        # Kernel pour opérations morphologiques
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

        # Initialisation ORB
        self.orb = cv2.ORB_create(nfeatures=orb_n_features)
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING)

        # Charger les patterns
        self.patterns = []
        if pattern_dir:
            self._load_patterns(pattern_dir)

    def _load_patterns(self, pattern_dir: str):
        """Charge les patterns de drone pour le matching ORB"""
        pattern_path = Path(pattern_dir)
        if not pattern_path.exists():
            logger.warning(f"Dossier patterns introuvable: {pattern_dir}")
            return

        for file_path in pattern_path.glob("*"):
            if file_path.suffix.lower() not in [".jpg", ".png", ".jpeg"]:
                continue

            img = cv2.imread(str(file_path), cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue

            # Redimensionner pour optimisation
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

        # S'assurer qu'on a une image BGR pour MOG2
        if len(frame.shape) == 2:
            # Frame en grayscale, convertir en BGR
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        # Convertir en niveaux de gris pour ORB
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        w_in = gray.shape[1]
        h_in = gray.shape[0]
        target_w = self.resize_width
        target_h = int(h_in * target_w / w_in)

        frame = cv2.resize(frame, (target_w, target_h))
        # gray = cv2.resize(gray, (target_w, target_h))

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

            # Extraire la ROI
            roi = gray[y : y + h, x : x + w]
            roi_small = cv2.resize(roi, (128, 128))  # Optimisation

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

        return result
