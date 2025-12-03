"""
Module ProcessingResult.

Ce module définit la classe ProcessingResult, qui encapsule
le résultat d'un traitement d'image
avec la frame, les coordonnées des objets détectés,
les métadonnées et le temps de traitement.
Utilisé pour transmettre les résultats entre les différents
blocs du pipeline vidéo.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

import numpy as np


@dataclass
class ProcessingResult:
    """Résultat d'un traitement contenant l'image et des métadonnées."""

    frame: np.ndarray
    coordinates: List[Tuple[int, int, int, int]] = field(
        default_factory=list
    )  # [(x, y, w, h), ...]
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time: float = 0.0

    def add_box(self, x: int, y: int, w: int, h: int):
        """Ajoute des coordonnées de boîte englobante."""
        self.coordinates.append((x, y, w, h))

    def add_point(self, x: int, y: int):
        """Ajoute un point (stocké comme boîte 1x1)."""
        self.coordinates.append((x, y, 1, 1))
