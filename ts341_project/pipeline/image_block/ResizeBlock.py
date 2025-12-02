import cv2
import numpy as np

from ts341_project.pipeline.image_block.ProcessingBlock import ProcessingBlock
from ts341_project.ProcessingResult import ProcessingResult


class ResizeBlock(ProcessingBlock):
    """Redimensionne l'image à une largeur donnée (conserve le ratio).

    Si `target_width` est None, ne fait rien.
    """

    def __init__(self, target_width: int = None, target_height: int = None):
        self.target_width = target_width
        self.target_height = target_height

    def process(self, frame: np.ndarray, result: ProcessingResult = None) -> ProcessingResult:
        if result is None:
            result = ProcessingResult(frame=frame)

        if self.target_width is None and self.target_height is None:
            result.frame = frame
            return result

        h, w = frame.shape[:2]

        if self.target_width is not None and self.target_height is None:
            scale = self.target_width / float(w)
            new_w = self.target_width
            new_h = int(h * scale)
        elif self.target_height is not None and self.target_width is None:
            scale = self.target_height / float(h)
            new_h = self.target_height
            new_w = int(w * scale)
        else:
            new_w = int(self.target_width)
            new_h = int(self.target_height)

        # éviter de redimensionner si la taille est déjà correcte
        if (w, h) == (new_w, new_h):
            result.frame = frame
            return result

        result.frame = cv2.resize(frame, (new_w, new_h))
        return result
