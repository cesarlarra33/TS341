import cv2
import numpy as np

from ts341_project.pipeline.image_block.ProcessingBlock import ProcessingBlock
from ts341_project.ProcessingResult import ProcessingResult


class GrayscaleBlock(ProcessingBlock):
    """Convertit l'image en niveaux de gris"""

    def process(
        self, frame: np.ndarray, result: ProcessingResult = None
    ) -> ProcessingResult:
        if result is None:
            result = ProcessingResult(frame=frame)

        if len(frame.shape) == 3:
            result.frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            result.frame = frame
        return result
