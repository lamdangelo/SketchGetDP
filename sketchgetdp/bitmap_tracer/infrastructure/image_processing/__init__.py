"""
Image processing infrastructure layer for the bitmap tracing system.

This package provides the core image analysis capabilities including contour detection,
color analysis, and geometric processing. These components implement the framework-side
concerns of the Clean Architecture, handling OpenCV interactions and image processing
algorithms while exposing clean interfaces to the domain layer.
"""

from .contour_detector import ContourDetector
from .color_analyzer import ColorAnalyzer
from .contour_closure_service import ContourClosureService, ClosedContour

__all__ = [
    'ContourDetector',
    'ColorAnalyzer', 
    'ContourClosureService',
    'ClosedContour'
]