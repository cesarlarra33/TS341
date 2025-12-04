import cv2
import numpy as np

from ts341_project.pipeline.image_block.ProcessingBlock import ProcessingBlock
from ts341_project.ProcessingResult import ProcessingResult


class MetadataOverlayBlock(ProcessingBlock):
    """Affiche les métadonnées de détection sur la frame en tant que texte d'overlay.
    
    S'attend à trouver dans result.metadata :
    - num_detections: nombre total de détections
    - num_confirmed_drones: nombre de drones confirmés
    - drone_center: (x, y) du centre détecté ou None
    - confidence: pourcentage de confiance ou None
    - coord_display: texte de description des coordonnées
    """

    def __init__(self, font_scale: float = 0.7, thickness: int = 2, bg_color=(0, 0, 0), text_color=(255, 255, 255)):
        """
        Args:
            font_scale: Taille du texte (1.0 = taille standard)
            thickness: Épaisseur du texte
            bg_color: Couleur du fond (BGR)
            text_color: Couleur du texte (BGR)
        """
        self.font_scale = font_scale
        self.thickness = thickness
        self.bg_color = bg_color
        self.text_color = text_color
        self.font = cv2.FONT_HERSHEY_SIMPLEX

    def _draw_text_with_bg(self, frame, text, org, font_scale, thickness, text_color, bg_color):
        """Dessine du texte avec un fond semi-transparent."""
        (text_width, text_height), baseline = cv2.getTextSize(text, self.font, font_scale, thickness)
        x, y = org
        
        # Rectangle de fond
        cv2.rectangle(frame, (x - 5, y - text_height - 5), (x + text_width + 5, y + baseline + 5), bg_color, -1)
        
        # Texte
        cv2.putText(frame, text, org, self.font, font_scale, text_color, thickness)

    def process(self, frame: np.ndarray, result: ProcessingResult = None) -> ProcessingResult:
        if result is None:
            result = ProcessingResult(frame=frame)

        # Copier la frame pour éviter les modifications accidentelles
        frame = result.frame.copy()

        h, _ = frame.shape[:2]
        y_offset = 30
        line_height = 30

        # 1. Nombre total de détections
        num_det = result.metadata.get("num_detections", 0)
        num_conf = result.metadata.get("num_confirmed_drones", 0)
        text_det = f"Détections: {num_det} (Confirmés: {num_conf})"
        self._draw_text_with_bg(frame, text_det, (10, y_offset), self.font_scale, self.thickness, self.text_color, self.bg_color)
        y_offset += line_height

        # 2. Confiance et coordonnées si disponible
        confidence = result.metadata.get("confidence")
        coord_display = result.metadata.get("coord_display", "")
        
        if confidence is not None and coord_display:
            text_conf = f"Confiance: {confidence}% | {coord_display}"
            self._draw_text_with_bg(frame, text_conf, (10, y_offset), self.font_scale, self.thickness, self.text_color, self.bg_color)
            y_offset += line_height

        # 3. Afficher la liste des détections (drone_detections)
        detections = result.metadata.get("drone_detections", [])
        if detections:
            text_list = f"Liste ({len(detections)} détections):"
            self._draw_text_with_bg(frame, text_list, (10, y_offset), self.font_scale, self.thickness, self.text_color, self.bg_color)
            y_offset += line_height

            for i, det in enumerate(detections):
                bbox = det.get("bbox", (0, 0, 0, 0))
                is_drone = det.get("is_drone", False)
                num_matches = det.get("num_matches", 0)
                
                # Abréger le label pour l'affichage
                status = "✓ Drone" if is_drone else "○ Mouv"
                text_item = f"  [{i+1}] {status} | Box: ({bbox[0]}, {bbox[1]}, {bbox[2]}, {bbox[3]}) | Matches: {num_matches}"
                self._draw_text_with_bg(frame, text_item, (10, y_offset), self.font_scale * 0.8, self.thickness - 1, self.text_color, self.bg_color)
                y_offset += line_height - 3

        # 4. Afficher les coordonnées brutes en bas à gauche
        drone_center = result.metadata.get("drone_center")
        if drone_center is not None:
            cx, cy = drone_center
            text_center = f"Centre détecté: ({cx}, {cy})"
            self._draw_text_with_bg(frame, text_center, (10, h - 10), self.font_scale, self.thickness, self.text_color, self.bg_color)

        result.frame = frame
        return result
