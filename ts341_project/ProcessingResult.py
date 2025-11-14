import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any


@dataclass
class ProcessingResult:
    """
    Résultat d'un traitement contenant l'image et des métadonnées.
    """

    frame: np.ndarray
    coordinates: List[Tuple[int, int, int, int]] = field(
        default_factory=list
    )  # [(x, y, w, h), ...]
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time: float = 0.0

    def add_box(self, x: int, y: int, w: int, h: int):
        """Ajoute des coordonnées de boîte englobante"""
        self.coordinates.append((x, y, w, h))

    def add_point(self, x: int, y: int):
        """Ajoute un point (stocké comme boîte 1x1)"""
        self.coordinates.append((x, y, 1, 1))
