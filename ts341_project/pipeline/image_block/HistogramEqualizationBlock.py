import cv2
import numpy as np

from ts341_project.pipeline.image_block.ProcessingBlock import ProcessingBlock
from ts341_project.ProcessingResult import ProcessingResult


class HistogramEqualizationBlock(ProcessingBlock):
    """Égalisation d'histogramme pour améliorer le contraste"""

    def process(
        self, frame: np.ndarray, result: ProcessingResult = None
    ) -> ProcessingResult:
        if result is None:
            result = ProcessingResult(frame=frame)

        if len(frame.shape) == 2:  # Grayscale
            result.frame = cv2.equalizeHist(frame)
        else:  # Color - égalisation sur le canal V (HSV)
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            hsv[:, :, 2] = cv2.equalizeHist(hsv[:, :, 2])
            result.frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        return result
