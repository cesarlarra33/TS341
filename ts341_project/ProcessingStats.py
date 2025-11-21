"""
ProcessingStats - Collecte et calcul des statistiques de traitement
"""

import numpy as np
import logging
from typing import List, Optional
from dataclasses import dataclass, field


@dataclass
class ProcessingStats:
    """
    Collecte et analyse les temps de traitement.
    """

    processing_times: List[float] = field(default_factory=list)
    frame_count: int = 0

    def add_time(self, processing_time: float):
        """Ajoute un temps de traitement"""
        self.processing_times.append(processing_time)
        self.frame_count += 1

    def get_mean(self) -> float:
        """Retourne le temps moyen de traitement"""
        if not self.processing_times:
            return 0.0
        return float(np.mean(self.processing_times))

    def get_median(self) -> float:
        """Retourne le temps médian de traitement"""
        if not self.processing_times:
            return 0.0
        return float(np.median(self.processing_times))

    def get_max(self) -> float:
        """Retourne le temps maximum de traitement"""
        if not self.processing_times:
            return 0.0
        return float(np.max(self.processing_times))

    def get_min(self) -> float:
        """Retourne le temps minimum de traitement"""
        if not self.processing_times:
            return 0.0
        return float(np.min(self.processing_times))

    def get_std(self) -> float:
        """Retourne l'écart-type des temps de traitement"""
        if not self.processing_times:
            return 0.0
        return float(np.std(self.processing_times))

    def get_fps(self) -> float:
        """Retourne les FPS moyens basés sur les temps de traitement"""
        mean_time = self.get_mean()
        if mean_time == 0:
            return 0.0
        return 1.0 / mean_time

    def get_summary(self) -> dict:
        """Retourne un résumé complet des statistiques"""
        return {
            "frame_count": self.frame_count,
            "mean_time_ms": self.get_mean() * 1000,
            "median_time_ms": self.get_median() * 1000,
            "min_time_ms": self.get_min() * 1000,
            "max_time_ms": self.get_max() * 1000,
            "std_time_ms": self.get_std() * 1000,
            "avg_fps": self.get_fps(),
        }

    def print_summary(self, title: str = "Statistics de traitement"):
        """Affiche un résumé formaté des statistiques (deprecated, use log_summary)"""
        logger = logging.getLogger(__name__)
        self.log_summary(logger, title)

    def log_summary(
        self,
        logger: Optional[logging.Logger] = None,
        title: str = "Statistics de traitement",
    ):
        """Affiche un résumé formaté des statistiques via logging"""
        if logger is None:
            logger = logging.getLogger(__name__)

        if not self.processing_times:
            logger.info("")
            logger.info("=" * 60)
            logger.info(title)
            logger.info("=" * 60)
            logger.info("Aucune donnée de traitement")
            logger.info("=" * 60)
            logger.info("")
            return

        summary = self.get_summary()

        logger.info("")
        logger.info("=" * 60)
        logger.info(title)
        logger.info("=" * 60)
        logger.info("Frames traitées      : %d", summary["frame_count"])
        logger.info("Temps moyen          : %.2f ms", summary["mean_time_ms"])
        logger.info("Temps médian         : %.2f ms", summary["median_time_ms"])
        logger.info("Temps minimum        : %.2f ms", summary["min_time_ms"])
        logger.info("Temps maximum        : %.2f ms", summary["max_time_ms"])
        logger.info("Écart-type           : %.2f ms", summary["std_time_ms"])
        logger.info("FPS moyen            : %.1f FPS", summary["avg_fps"])
        logger.info("=" * 60)
        logger.info("")

    def reset(self):
        """Réinitialise les statistiques"""
        self.processing_times.clear()
        self.frame_count = 0
