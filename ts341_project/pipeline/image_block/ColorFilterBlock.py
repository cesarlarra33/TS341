"""Bloc de filtrage de couleur en espace HSV."""

import cv2
import numpy as np

from ts341_project.pipeline.image_block.ProcessingBlock import ProcessingBlock
from ts341_project.ProcessingResult import ProcessingResult


class ColorFilterBlock(ProcessingBlock):
    """Filtre une plage de couleurs (HSV)."""

    def __init__(self, lower_hsv: tuple, upper_hsv: tuple):
        """Initialise le bloc de filtrage de couleur."""
        self.lower = np.array(lower_hsv)
        self.upper = np.array(upper_hsv)

    def process(
        self, frame: np.ndarray, result: ProcessingResult | None = None
    ) -> ProcessingResult:
        """Applique le filtre de couleur à l'image."""
        if result is None:
            result = ProcessingResult(frame=frame)

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower, self.upper)
        result.frame = cv2.bitwise_and(frame, frame, mask=mask)
        return result
