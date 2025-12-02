import cv2
import numpy as np
from pathlib import Path

from ts341_project.pipeline.image_block.ProcessingBlock import ProcessingBlock
from ts341_project.ProcessingResult import ProcessingResult
from ts341_project.pipeline.image_block.ORBMatchingBlock import ORBMatchingBlock


class ContourMatchingBlock(ProcessingBlock):
    """Détecte les contours sur un masque fourni dans `result.metadata['fg_mask']`,
    réalise le matching ORB avec des patterns et dessine les boîtes/labels sur la frame.

    Ce bloc attend que `result.frame` soit la frame couleur (BGR) sur laquelle dessiner
    et que `result.metadata['fg_mask']` contienne le masque binaire des régions en mouvement.
    """

    def __init__(
        self,
        pattern_dir: str = None,
        min_matches: int = 2,
        orb_n_features: int = 300,
        min_contour_size: int = 5,
        roi_size: tuple = (128, 128),
    ):
        self.min_matches = min_matches
        self.min_contour_size = min_contour_size
        self.roi_size = tuple(roi_size)

        # Bloc ORB dédié
        self.orb_block = ORBMatchingBlock(pattern_dir=pattern_dir, min_matches=min_matches, orb_n_features=orb_n_features, roi_size=self.roi_size)

    # pattern loading and ORB matching are delegated to ORBMatchingBlock

    def process(self, frame: np.ndarray, result: ProcessingResult = None) -> ProcessingResult:
        if result is None:
            result = ProcessingResult(frame=frame)

        # On s'attend à trouver le masque dans result.metadata
        fg_mask = result.metadata.get("fg_mask")
        if fg_mask is None:
            # Rien à faire
            result.metadata.setdefault("drone_detections", [])
            return result

        # Trouver les contours sur le masque
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detections = []

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)

            if w < self.min_contour_size or h < self.min_contour_size:
                continue

            roi = frame[y : y + h, x : x + w]
            roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi
            roi_small = cv2.resize(roi_gray, self.roi_size)

            # Use ORBMatchingBlock to test the ROI
            orb_result = self.orb_block.process(roi_small)
            orb_meta = orb_result.metadata.get("orb_match", {"match_found": False, "num_matches": 0})
            match_found = orb_meta.get("match_found", False)
            num_matches = orb_meta.get("num_matches", 0)

            color = (0, 0, 255) if match_found else (0, 255, 0)
            label = f"Drone détecté ({num_matches})" if match_found else "Poss. Drone"

            cv2.rectangle(result.frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(result.frame, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

            detections.append({
                "bbox": (x, y, w, h),
                "is_drone": match_found,
                "num_matches": num_matches,
                "label": label,
            })

        result.metadata["drone_detections"] = detections
        result.metadata["num_detections"] = len(detections)
        result.metadata["num_confirmed_drones"] = sum(1 for d in detections if d["is_drone"])

        # Reprendre la logique d'affichage des coordonnées (même heuristique qu'avant)
        num_boxes = len(detections)
        result.metadata["drone_center"] = None
        result.metadata["confidence"] = None
        result.metadata["coord_display"] = ""

        if num_boxes > 5:
            result.metadata["coord_display"] = "Trop de détections : 0% fiable"
        elif num_boxes == 1:
            det = detections[0]
            x, y, w, h = det["bbox"]
            cx = x + w // 2
            cy = y + h // 2
            result.metadata["drone_center"] = (cx, cy)
            result.metadata["confidence"] = 90
            result.metadata["coord_display"] = f"Centre: ({cx}, {cy}) — 90% fiable"
            cv2.circle(result.frame, (cx, cy), 5, (255, 255, 0), -1)
            cv2.putText(result.frame, "90% fiable", (cx + 10, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        elif 2 <= num_boxes <= 5:
            biggest = max(detections, key=lambda d: d["bbox"][2] * d["bbox"][3])
            x, y, w, h = biggest["bbox"]
            cx = x + w // 2
            cy = y + h // 2
            confidence = round((1 / num_boxes) * 100, 1)
            result.metadata["drone_center"] = (cx, cy)
            result.metadata["confidence"] = confidence
            result.metadata["coord_display"] = f"Centre: ({cx}, {cy}) — {confidence}% fiable"
            cv2.circle(result.frame, (cx, cy), 5, (255, 255, 0), -1)
            cv2.putText(result.frame, f"{confidence}% fiable", (cx + 10, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        # Affichage des coordonnées en bas à gauche si présent
        if result.metadata.get("drone_center") is not None:
            cx, cy = result.metadata["drone_center"]
            text = f"Coordonnées : X={cx}, Y={cy}"
            h = result.frame.shape[0]
            cv2.putText(result.frame, text, (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        return result
