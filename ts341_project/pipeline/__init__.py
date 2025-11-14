"""
Module pipeline pour le traitement de flux vidéo
"""

from .ProcessingPipeline import ProcessingPipeline
from .Pipelines import (
    create_pipeline,
    list_pipelines,
    AVAILABLE_PIPELINES,
    PassthroughPipeline,
    GrayscalePipeline,
    EdgeDetectionPipeline,
    BlurPipeline,
    ThresholdPipeline,
    HistogramEqualizationPipeline,
    EdgeEnhancementPipeline,
    MorphologyPipeline,
    DualDisplayPipeline,
)

__all__ = [
    "ProcessingPipeline",
    "create_pipeline",
    "list_pipelines",
    "AVAILABLE_PIPELINES",
    "PassthroughPipeline",
    "GrayscalePipeline",
    "EdgeDetectionPipeline",
    "BlurPipeline",
    "ThresholdPipeline",
    "HistogramEqualizationPipeline",
    "EdgeEnhancementPipeline",
    "MorphologyPipeline",
    "DualDisplayPipeline",
]
