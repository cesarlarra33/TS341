"""
Pipelines.py - Définition des pipelines de traitement pré-configurés

Utilise les blocks existants dans image_block/ et video_block/
Toutes les pipelines héritent de ProcessingPipeline.
"""

import cv2
import numpy as np

from ts341_project.ProcessingResult import ProcessingResult
from ts341_project.pipeline.video_block.CustomDroneBlock import CustomDroneBlock
from ts341_project.pipeline.ProcessingPipeline import ProcessingPipeline
from ts341_project.pipeline.image_block import *
from ts341_project.pipeline.video_block import *
import os
from pathlib import Path

# ============================================================================
# PIPELINES SIMPLES
# ============================================================================


class PassthroughPipeline(ProcessingPipeline):
    """Pipeline passthrough - aucun traitement"""

    def __init__(self):
        super().__init__(blocks=[])
        self.name = "Passthrough"


class DroneDetectionPipeline(ProcessingPipeline):
    """Pipeline de détection de drone utilisant CustomDroneBlock"""

    def __init__(self, pattern_dir: str = None):
        super().__init__(
            blocks=[
                CustomDroneBlock(pattern_dir=pattern_dir),
            ]
        )
        self.name = "Drone Detection"


class GrayscalePipeline(ProcessingPipeline):
    """Pipeline de conversion en niveaux de gris avec affichage couleur"""

    def __init__(self):
        super().__init__(
            blocks=[
                GrayscaleBlock(),
                ColorScaleBlock(),  # Conversion BGR pour affichage
            ]
        )
        self.name = "Grayscale"


class EdgeDetectionPipeline(ProcessingPipeline):
    """Pipeline de détection de contours (Canny)"""

    def __init__(self, threshold1=50, threshold2=150):
        super().__init__(
            blocks=[
                CannyEdgeBlock(threshold1, threshold2),
                ColorScaleBlock(),  # Conversion BGR pour affichage
            ]
        )
        self.name = "Edge Detection (Canny)"


class BlurPipeline(ProcessingPipeline):
    """Pipeline de flou gaussien"""

    def __init__(self, kernel_size=15, sigma=0):
        # GaussianBlurBlock attend un tuple (kernel_size, kernel_size)
        kernel = (
            (kernel_size, kernel_size) if isinstance(kernel_size, int) else kernel_size
        )
        super().__init__(
            blocks=[
                GaussianBlurBlock(kernel, sigma),
            ]
        )
        self.name = f"Gaussian Blur (kernel={kernel_size})"


class ThresholdPipeline(ProcessingPipeline):
    """Pipeline de seuillage"""

    def __init__(self, threshold=127, threshold_type="binary"):
        super().__init__(
            blocks=[
                GrayscaleBlock(),
                ThresholdBlock(threshold, 255, threshold_type),
                ColorScaleBlock(),  # Conversion BGR pour affichage
            ]
        )
        self.name = f"Threshold ({threshold_type})"


class HistogramEqualizationPipeline(ProcessingPipeline):
    """Pipeline d'égalisation d'histogramme"""

    def __init__(self):
        super().__init__(
            blocks=[
                GrayscaleBlock(),
                HistogramEqualizationBlock(),
                ColorScaleBlock(),  # Conversion BGR pour affichage
            ]
        )
        self.name = "Histogram Equalization"


# ============================================================================
# PIPELINES COMPOSÉS
# ============================================================================


class EdgeEnhancementPipeline(ProcessingPipeline):
    """Pipeline avancé: Flou + Détection de contours"""

    def __init__(self, blur_kernel=5, canny_low=50, canny_high=150):
        # GaussianBlurBlock attend un tuple
        kernel = (
            (blur_kernel, blur_kernel) if isinstance(blur_kernel, int) else blur_kernel
        )
        super().__init__(
            blocks=[
                GaussianBlurBlock(kernel, 0),
                CannyEdgeBlock(canny_low, canny_high),
                ColorScaleBlock(),  # Conversion BGR pour affichage
            ]
        )
        self.name = "Edge Enhancement (Blur + Canny)"


class MorphologyPipeline(ProcessingPipeline):
    """Pipeline de morphologie mathématique"""

    def __init__(self, operation="opening", kernel_size=5):
        super().__init__(
            blocks=[
                GrayscaleBlock(),
                ThresholdBlock(127, 255, "binary"),
                MorphologyBlock(operation, kernel_size),
                ColorScaleBlock(),  # Conversion BGR pour affichage
            ]
        )
        self.name = f"Morphology ({operation})"


class CustomPipeline(ProcessingPipeline):
    """Pipeline personnalisée avec des blocks définis par l'utilisateur"""

    def __init__(self):
        # Obtenir le répertoire patterns
        patterns_dir = Path(__file__).parent.parent / "patterns"

        # Prétraiter les images de référence avec Canny
        preprocessed_references = {}
        references = {}
        if patterns_dir.exists():
            # Créer une instance temporaire de CannyEdgeBlock pour le prétraitement
            canny_preprocessor = CannyEdgeBlock(threshold1=100, threshold2=200)

            for idx, file_path in enumerate(
                sorted(patterns_dir.glob("*.png")), start=1
            ):
                # Charger l'image de référence
                ref_image = cv2.imread(str(file_path))
                references[f"ref{idx}"] = str(file_path)
                if ref_image is not None:
                    # Appliquer Canny à l'image de référence
                    result = canny_preprocessor.process(ref_image)
                    # Sauvegarder l'image prétraitée temporairement
                    temp_path = patterns_dir / f"preprocessed_{file_path.name}"
                    cv2.imwrite(str(temp_path), result.frame)
                    preprocessed_references[f"ref{idx}"] = str(temp_path)

        super().__init__(
            blocks=[
                # Ajouter ici les blocks personnalisés
                # BackgroundSubtractorBlock(
                #     history=250, varThreshold=20, detectShadows=False
                # ),
                # CannyEdgeBlock(threshold1=100, threshold2=200),
                # OrbBlock(
                #     draw_results=True,
                #     references=references,
                # ),
            ]
        )
        self.name = "Custom Pipeline"


class DronePipeline(ProcessingPipeline):
    """Pipeline de détection de drone avec MOG2 + ORB matching"""

    def __init__(self, pattern_dir: str = None):
        """
        Args:
            pattern_dir: Chemin vers le dossier contenant les patterns de drone
            min_matches: Nombre minimum de matches ORB pour confirmer un drone
        """
        # Si pas de pattern_dir fourni, utiliser le dossier patterns par défaut
        if pattern_dir is None:
            pattern_dir = str(Path(__file__).parent / "patterns")

        super().__init__(
            blocks=[
                CustomDroneBlock(
                    pattern_dir=pattern_dir,
                    min_matches=5,
                    resize_width=2048,
                    mog2_history=500,
                    mog2_var_threshold=20,
                    orb_n_features=500,
                    min_contour_size=30,
                ),
            ]
        )
        self.name = "Drone Detection (MOG2 + ORB)"


# ============================================================================
# FACTORY DE PIPELINES
# ============================================================================

AVAILABLE_PIPELINES = {
    "passthrough": PassthroughPipeline,
    "grayscale": GrayscalePipeline,
    "edges": EdgeDetectionPipeline,
    "blur": BlurPipeline,
    "threshold": ThresholdPipeline,
    "histogram": HistogramEqualizationPipeline,
    "edge-enhance": EdgeEnhancementPipeline,
    "morphology": MorphologyPipeline,
    # "custom": CustomPipeline,
    "drone": DronePipeline,
    "drone-detection": DroneDetectionPipeline,
}


def create_pipeline(pipeline_name, **kwargs):
    """
    Crée un pipeline selon le nom ou retourne la pipeline si c'est déjà une instance.

    Args:
        pipeline_name: Nom du pipeline (str), instance de ProcessingPipeline,
                      ou classe de pipeline
        **kwargs: Arguments spécifiques au pipeline

    Returns:
        Instance du pipeline

    Exemples:
        >>> create_pipeline("grayscale")
        >>> create_pipeline("edges", threshold1=100, threshold2=200)
        >>> create_pipeline(EdgeDetectionPipeline(100, 200))
        >>> create_pipeline(EdgeDetectionPipeline, threshold1=100, threshold2=200)
    """
    # Si c'est déjà une instance de ProcessingPipeline, la retourner
    if isinstance(pipeline_name, ProcessingPipeline):
        return pipeline_name

    # Si c'est une classe, l'instancier
    if isinstance(pipeline_name, type) and issubclass(
        pipeline_name, ProcessingPipeline
    ):
        return pipeline_name(**kwargs)

    # Si c'est un string, créer depuis AVAILABLE_PIPELINES
    if isinstance(pipeline_name, str):
        if pipeline_name not in AVAILABLE_PIPELINES:
            available = ", ".join(AVAILABLE_PIPELINES.keys())
            raise ValueError(
                f"Pipeline '{pipeline_name}' inconnu. "
                f"Pipelines disponibles: {available}"
            )

        pipeline_class = AVAILABLE_PIPELINES[pipeline_name]
        return pipeline_class(**kwargs)

    # Sinon erreur
    raise TypeError(
        f"pipeline_name doit être un str, une classe ou une instance de ProcessingPipeline, "
        f"pas {type(pipeline_name)}"
    )


def list_pipelines():
    """Retourne la liste des pipelines disponibles avec leurs descriptions"""
    pipelines_info = []
    for name, pipeline_class in AVAILABLE_PIPELINES.items():
        # Créer une instance temporaire pour obtenir le nom
        try:
            instance = pipeline_class()
            description = instance.name
        except Exception:
            description = pipeline_class.__doc__ or "No description"

        pipelines_info.append((name, description))

    return pipelines_info
