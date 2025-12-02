import cv2
import numpy as np
from pathlib import Path

from ts341_project.pipeline.image_block.ProcessingBlock import ProcessingBlock
from ts341_project.ProcessingResult import ProcessingResult


class ORBMatchingBlock(ProcessingBlock):
    """Bloc réutilisable qui réalise le matching ORB entre une petite ROI
    (grayscale, déjà redimensionnée) et un jeu de patterns chargés depuis un dossier.

    Le bloc écrit dans `result.metadata['orb_match']` un dict {match_found: bool, num_matches: int}.
    """

    def __init__(self, pattern_dir: str = None, min_matches: int = 2, orb_n_features: int = 300, roi_size=(128, 128)):
        self.min_matches = min_matches
        self.roi_size = tuple(roi_size)
        self.orb = cv2.ORB_create(nfeatures=orb_n_features)
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING)

        self.patterns = []
        if pattern_dir:
            self._load_patterns(pattern_dir)

    def _load_patterns(self, pattern_dir: str):
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
            img_small = cv2.resize(img, self.roi_size)
            kp, des = self.orb.detectAndCompute(img_small, None)
            if des is not None:
                self.patterns.append((kp, des))
                print(f"Pattern ORB chargé: {file_path.name} ({len(kp)} keypoints)")

    def process(self, frame: np.ndarray, result: ProcessingResult = None) -> ProcessingResult:
        # frame attendu: grayscale et de taille self.roi_size
        if result is None:
            result = ProcessingResult(frame=frame)

        match_found = False
        num_matches = 0

        if self.patterns:
            _, des_roi = self.orb.detectAndCompute(frame, None)
            if des_roi is not None:
                for kp_pat, des_pat in self.patterns:
                    matches = self.bf.knnMatch(des_pat, des_roi, k=2)
                    good_matches = []
                    for m_n in matches:
                        if len(m_n) == 2:
                            m, n = m_n
                            if m.distance < 0.75 * n.distance:
                                good_matches.append(m)
                    if len(good_matches) >= self.min_matches:
                        match_found = True
                        num_matches = len(good_matches)
                        break

        result.metadata["orb_match"] = {"match_found": match_found, "num_matches": num_matches}
        return result
