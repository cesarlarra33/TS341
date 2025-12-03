"""Détection de contours avec Canny."""

import cv2
import numpy as np

from ts341_project.pipeline.image_block.ProcessingBlock import ProcessingBlock
from ts341_project.ProcessingResult import ProcessingResult


class CannyEdgeBlock(ProcessingBlock):
    """Détection de contours avec Canny."""

    def __init__(self, threshold1: int = 50, threshold2: int = 150):
        """Initialise le bloc de détection de contours avec Canny."""
        self.threshold1 = threshold1
        self.threshold2 = threshold2

    def process(
        self, frame: np.ndarray, result: ProcessingResult | None = None
    ) -> ProcessingResult:
        """Applique la détection de contours Canny à l'image."""
        if result is None:
            result = ProcessingResult(frame=frame)

        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
        result.frame = cv2.Canny(gray, self.threshold1, self.threshold2)
        return result
