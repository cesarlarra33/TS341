"""Bloc de soustraction de fond utilisant MOG2."""

from typing import List

import cv2
import numpy as np

from ts341_project.pipeline.image_block import ProcessingBlock
from ts341_project.pipeline.video_block.StatefulProcessingBlock import (
    StatefulProcessingBlock,
)
from ts341_project.ProcessingResult import ProcessingResult


class BackgroundSubtractorBlock(StatefulProcessingBlock):
    """Soustraction de fond avec MOG2."""

    def __init__(
        self,
        history: int = 500,
        var_threshold: int = 16,
        detect_shadows: bool = True,
        preprocessing: List[ProcessingBlock] | None = None,
        postprocessing: List[ProcessingBlock] | None = None,
    ):
        """
        Initialise le bloc de soustraction de fond.

        Args:
            history: Nombre de frames d'historique
            var_threshold: Seuil de variance
            detect_shadows: Détecter les ombres
            preprocessing: Pipeline de pré-traitement
            postprocessing: Pipeline de post-traitement (ex: morphologie)
        """
        super().__init__(
            preprocessing=preprocessing, postprocessing=postprocessing
        )

        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=history,
            varThreshold=var_threshold,
            detectShadows=detect_shadows,
        )

    def process_with_memory(
        self, frame: np.ndarray, result: ProcessingResult
    ) -> ProcessingResult:
        """Applique la soustraction de fond.

        frame est déjà pré-traité si un preprocessing est défini.
        """
        fg_mask = self.bg_subtractor.apply(frame)
        result.frame = fg_mask
        result.metadata["foreground_pixels"] = np.count_nonzero(fg_mask)
        return result
