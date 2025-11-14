import cv2
import numpy as np

from ts341_project.ProcessingResult import ProcessingResult
from ts341_project.pipeline.image_block.ProcessingBlock import ProcessingBlock


class ColorScaleBlock(ProcessingBlock):
    """Convertit une image grayscale en BGR (fausse couleur pour affichage)"""

    def __init__(self):
        """Initialise le bloc de conversion colorscale."""
        self.name = "ColorScale"

    def process(
        self, frame: np.ndarray, result: ProcessingResult = None
    ) -> ProcessingResult:
        """
        Convertit l'image de 1 canal vers 3 canaux BGR si nécessaire.

        Args:
            frame: Image à convertir (np.ndarray)
            result: ProcessingResult (optionnel)

        Returns:
            ProcessingResult avec l'image en 3 canaux BGR
        """
        if result is None:
            result = ProcessingResult(frame=frame)

        # Si l'image est déjà en couleur (3 canaux), on ne fait rien
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            result.frame = frame
            return result

        # Si l'image est en niveaux de gris (1 ou 2 dimensions), on convertit en BGR
        if len(frame.shape) == 2 or (len(frame.shape) == 3 and frame.shape[2] == 1):
            result.frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        return result

    def __repr__(self):
        """Représentation textuelle du bloc."""
        return "ColorScaleBlock()"
