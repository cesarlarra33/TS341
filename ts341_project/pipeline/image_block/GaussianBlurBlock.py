"""Applique un flou gaussien à une image."""

import cv2
import numpy as np

from ts341_project.pipeline.image_block.ProcessingBlock import ProcessingBlock
from ts341_project.ProcessingResult import ProcessingResult


class GaussianBlurBlock(ProcessingBlock):
    """Applique un flou gaussien."""

    def __init__(self, kernel_size: tuple = (5, 5), sigma: float = 0):
        """Initialise le bloc de flou gaussien."""
        self.kernel_size = kernel_size
        self.sigma = sigma

    def process(
        self, frame: np.ndarray, result: ProcessingResult | None = None
    ) -> ProcessingResult:
        """Applique un flou gaussien à l'image."""
        if result is None:
            result = ProcessingResult(frame=frame)

        result.frame = cv2.GaussianBlur(frame, self.kernel_size, self.sigma)
        return result
