"""Module pipeline pour le traitement de flux vidéo."""

from .Pipelines import (
    AVAILABLE_PIPELINES,
    BlurPipeline,
    EdgeDetectionPipeline,
    EdgeEnhancementPipeline,
    GrayscalePipeline,
    HistogramEqualizationPipeline,
    MorphologyPipeline,
    PassthroughPipeline,
    ThresholdPipeline,
    create_pipeline,
    list_pipelines,
)
from .ProcessingPipeline import ProcessingPipeline

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
