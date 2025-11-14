import cv2
import numpy as np
from typing import List

from pipeline.image_block.GaussianBlurBlock import GaussianBlurBlock
from pipeline.image_block.GrayscaleBlock import GrayscaleBlock
from pipeline.image_block import ProcessingBlock
from pipeline.video_block.StatefulProcessingBlock import StatefulProcessingBlock
from ProcessingResult import ProcessingResult


class MotionDetectionBlock(StatefulProcessingBlock):
    """Détection de mouvement par différence entre frames avec coordonnées"""

    def __init__(
        self,
        threshold: int = 25,
        min_area: int = 500,
        draw_boxes: bool = True,
        preprocessing: List[ProcessingBlock] = None,
        postprocessing: List[ProcessingBlock] = None,
    ):
        default_preprocessing = [
            GaussianBlurBlock(kernel_size=(9, 9)),  # Flou plus léger que le défaut
            GrayscaleBlock(),
        ]
        super().__init__(
            preprocessing=preprocessing or default_preprocessing,
            postprocessing=postprocessing,
        )
        self.previous_frame = None
        self.threshold = threshold
        self.min_area = min_area
        self.draw_boxes = draw_boxes

    def process_with_memory(
        self, frame: np.ndarray, result: ProcessingResult
    ) -> ProcessingResult:
        """
        Détection de mouvement sur la frame pré-traitée.
        frame est déjà pré-traité (grayscale + blur par défaut, ou preprocessing personnalisé).
        """
        # La frame reçue ici est déjà pré-traitée (grayscale et blur par défaut)
        # On s'assure qu'elle est en grayscale au cas où preprocessing personnalisé
        if len(frame.shape) == 3:
            print("Converting frame to grayscale")
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        # Mettre à jour result.frame avec l'image en grayscale
        result.frame = gray

        if self.previous_frame is None:
            self.previous_frame = gray
            return result

        # Différence entre frames
        frame_delta = cv2.absdiff(self.previous_frame, gray)
        thresh = cv2.threshold(frame_delta, self.threshold, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)

        # Trouver les contours
        contours, _ = cv2.findContours(
            thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        motion_count = 0

        # Si on veut dessiner les boxes, convertir en BGR pour avoir les couleurs
        if self.draw_boxes and len(result.frame.shape) == 2:
            result.frame = cv2.cvtColor(result.frame, cv2.COLOR_GRAY2BGR)

        for contour in contours:
            if cv2.contourArea(contour) < self.min_area:
                continue

            x, y, w, h = cv2.boundingRect(contour)
            result.add_box(x, y, w, h)
            motion_count += 1

            if self.draw_boxes:
                cv2.rectangle(result.frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(
                    result.frame,
                    f"#{motion_count}",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    2,
                )

        result.metadata["motion_count"] = motion_count
        self.previous_frame = gray
        return result
