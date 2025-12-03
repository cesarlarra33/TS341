"""Bloc de seuillage d'image."""

import cv2
import numpy as np

from ts341_project.pipeline.image_block.ProcessingBlock import ProcessingBlock
from ts341_project.ProcessingResult import ProcessingResult


class ThresholdBlock(ProcessingBlock):
    """Seuillage d'image."""

    def __init__(
        self,
        threshold: int = 127,
        max_value: int = 255,
        threshold_type: str = "binary",
    ):
        """
        Initialise le bloc de seuillage.

        Args:
            threshold: Valeur de seuil
            max_value: Valeur maximale
            threshold_type: 'binary', 'binary_inv',
            'trunc', 'tozero', 'tozero_inv'
        """
        self.threshold = threshold
        self.max_value = max_value

        threshold_types = {
            "binary": cv2.THRESH_BINARY,
            "binary_inv": cv2.THRESH_BINARY_INV,
            "trunc": cv2.THRESH_TRUNC,
            "tozero": cv2.THRESH_TOZERO,
            "tozero_inv": cv2.THRESH_TOZERO_INV,
        }
        self.threshold_type = threshold_types.get(
            threshold_type.lower(), cv2.THRESH_BINARY
        )

    def process(
        self, frame: np.ndarray, result: ProcessingResult | None = None
    ) -> ProcessingResult:
        """Applique un seuillage à l'image."""
        if result is None:
            result = ProcessingResult(frame=frame)

        # Convertir en grayscale si nécessaire
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        _, result.frame = cv2.threshold(
            gray, self.threshold, self.max_value, self.threshold_type
        )
        return result
