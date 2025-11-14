"""
Blocs de traitement pour images uniques (sans mémoire)
"""

from .ProcessingBlock import ProcessingBlock
from .GrayscaleBlock import GrayscaleBlock
from .GaussianBlurBlock import GaussianBlurBlock
from .HistogramEqualizationBlock import HistogramEqualizationBlock
from .CannyEdgeBlock import CannyEdgeBlock
from .ColorFilterBlock import ColorFilterBlock
from .ColorScaleBlock import ColorScaleBlock
from .MorphologyBlock import MorphologyBlock
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
