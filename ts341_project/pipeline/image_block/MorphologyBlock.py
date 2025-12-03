"""Bloc d'opérations morphologiques sur les images."""

import cv2
import numpy as np

from ts341_project.pipeline.image_block.ProcessingBlock import ProcessingBlock
from ts341_project.ProcessingResult import ProcessingResult


class MorphologyBlock(ProcessingBlock):
    """Opérations morphologiques (erosion, dilatation, opening, closing)."""

    def __init__(
        self,
        operation: str = "closing",
        kernel_size: int = 5,
        iterations: int = 1,
    ):
        """
        Initialise le bloc d'opérations morphologiques.

        Args:
            operation: 'erode', 'dilate', 'opening', 'closing'
            kernel_size: Taille du kernel (kernel_size x kernel_size)
            iterations: Nombre d'itérations
        """
        self.operation = operation.lower()
        self.kernel = np.ones((kernel_size, kernel_size), np.uint8)
        self.iterations = iterations

    def process(
        self, frame: np.ndarray, result: ProcessingResult | None = None
    ) -> ProcessingResult:
        """Applique l'opération morphologique spécifiée à l'image."""
        if result is None:
            result = ProcessingResult(frame=frame)

        if self.operation == "erode":
            result.frame = cv2.erode(
                frame, self.kernel, iterations=self.iterations
            )
        elif self.operation == "dilate":
            result.frame = cv2.dilate(
                frame, self.kernel, iterations=self.iterations
            )

        elif self.operation == "opening":
            result.frame = cv2.morphologyEx(
                frame, cv2.MORPH_OPEN, self.kernel, iterations=self.iterations
            )
        elif self.operation == "closing":
            result.frame = cv2.morphologyEx(
                frame, cv2.MORPH_CLOSE, self.kernel, iterations=self.iterations
            )
        else:
            raise ValueError(
                f"Opération morphologique" f"inconnue: {self.operation}"
            )

        return result
