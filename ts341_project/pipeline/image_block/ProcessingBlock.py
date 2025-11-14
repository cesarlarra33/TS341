import numpy as np
from abc import ABC, abstractmethod

from ts341_project.ProcessingResult import ProcessingResult


class ProcessingBlock(ABC):
    """
    Classe abstraite pour définir une brique de traitement.
    Retourne maintenant un ProcessingResult avec l'image et les métadonnées.
    """

    @abstractmethod
    def process(
        self, frame: np.ndarray, result: ProcessingResult = None
    ) -> ProcessingResult:
        """
        Traite une frame.
        Args:
            frame: Image d'entrée (numpy array)
            result: Résultat précédent (optionnel, pour chaînage)
        Returns:
            ProcessingResult avec l'image traitée et les métadonnées
        """
        pass

    def __call__(
        self, frame: np.ndarray, result: ProcessingResult = None
    ) -> ProcessingResult:
        """Permet d'appeler l'objet comme une fonction"""
        return self.process(frame, result)
