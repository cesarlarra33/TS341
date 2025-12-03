"""
Module StatefulProcessingBlock.

Ce module définit la classe abstraite StatefulProcessingBlock pour
les blocs de traitement vidéo
avec mémoire, supportant le pré- et post-traitement.
"""

from abc import abstractmethod
from typing import List

import numpy as np

from ts341_project.pipeline.image_block import ProcessingBlock
from ts341_project.ProcessingResult import ProcessingResult


class StatefulProcessingBlock(ProcessingBlock):
    """Classe abstraite pour les briques avec mémoire (traitement vidéo).

    Supporte des pipelines de pré-traitement et post-traitement. Si
    aucun preprocessing n'est fourni, utilise un pipeline par défaut.
    """

    def __init__(
        self,
        preprocessing: List[ProcessingBlock] | None = None,
        postprocessing: List[ProcessingBlock] | None = None,
        use_default_preprocessing: bool = True,
    ):
        """Initialise le bloc de traitement vidéo avec mémoire.

        Args:
            preprocessing: Liste de briques à appliquer AVANT la logique
            avec mémoire.
            Si None et use_default_preprocessing=True, utilise le
            preprocessing par défaut.
            postprocessing: Liste de briques à appliquer APRÈS
            la logique avec mémoire.
            use_default_preprocessing: Si True et preprocessing=None, utilise l
            e preprocessing par défaut.
        """
        # Si preprocessing est explicitement fourni, on l'utilise
        if preprocessing is not None:
            self.preprocessing = preprocessing
        # Sinon, on utilise le preprocessing par défaut si demandé
        elif use_default_preprocessing:
            self.preprocessing = self._get_default_preprocessing()
        # Sinon, pas de preprocessing
        else:
            self.preprocessing = []

        self.postprocessing = postprocessing or []

    def _get_default_preprocessing(self) -> list:
        """Retourne le pré-traitement par défaut pour.

        la détection de mouvement.

        Par défaut : Flou gaussien léger + conversion en niveaux de gris.
        Optimisé pour temps réel : noyau réduit à 5x5 au lieu de 21x21.
        """
        from ts341_project.pipeline.image_block.GaussianBlurBlock import (
            GaussianBlurBlock,
        )
        from ts341_project.pipeline.image_block.GrayscaleBlock import (
            GrayscaleBlock,
        )

        # OPTIMISATION: noyau 5x5 au lieu de 21x21 pour la webcam temps réel
        return [GaussianBlurBlock(kernel_size=(5, 5)), GrayscaleBlock()]

    def _apply_pipeline(
        self, frame: np.ndarray, blocks: List[ProcessingBlock]
    ) -> np.ndarray:
        """Applique une liste de briques sur une frame.

        Args:
            frame: Image d'entrée
            blocks: Liste de briques à appliquer
        Returns:
            Image transformée
        """
        result_frame = frame
        for block in blocks:
            temp_result = block.process(result_frame)
            result_frame = temp_result.frame
        return result_frame

    @abstractmethod
    def process_with_memory(
        self, frame: np.ndarray, result: ProcessingResult
    ) -> ProcessingResult:
        """Logique principale avec mémoire (à implémenter.

        par les sous-classes).

        Args:
            frame: Image après pré-traitement.
            result: Résultat à enrichir.
        Returns:
            ProcessingResult mis à jour.
        """

    def process(
        self, frame: np.ndarray, result: ProcessingResult | None = None
    ) -> ProcessingResult:
        """Traite une frame avec pré/post-traitement automatique.

        Args:
            frame: Image d'entrée.
            result: Résultat existant ou None.
        Returns:
            ProcessingResult mis à jour.
        """
        if result is None:
            result = ProcessingResult(frame=frame.copy())

        # 1. PRÉ-TRAITEMENT
        preprocessed = self._apply_pipeline(frame, self.preprocessing)

        # 2. TRAITEMENT AVEC MÉMOIRE (logique spécifique)
        result = self.process_with_memory(preprocessed, result)

        # 3. POST-TRAITEMENT (sur le résultat)
        if self.postprocessing:
            result.frame = self._apply_pipeline(
                result.frame, self.postprocessing
            )

        return result
