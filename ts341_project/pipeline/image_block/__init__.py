"""Blocs de traitement pour images uniques (sans mémoire)."""

from .CannyEdgeBlock import CannyEdgeBlock
from .ColorFilterBlock import ColorFilterBlock
from .ColorScaleBlock import ColorScaleBlock
from .GaussianBlurBlock import GaussianBlurBlock
from .GrayscaleBlock import GrayscaleBlock
from .HistogramEqualizationBlock import HistogramEqualizationBlock
from .MorphologyBlock import MorphologyBlock
from .ProcessingBlock import ProcessingBlock
from .ThresholdBlock import ThresholdBlock

__all__ = [
    "ProcessingBlock",
    "GrayscaleBlock",
    "GaussianBlurBlock",
    "HistogramEqualizationBlock",
    "CannyEdgeBlock",
    "ColorFilterBlock",
    "ColorScaleBlock",
    "MorphologyBlock",
    "ThresholdBlock",
]
