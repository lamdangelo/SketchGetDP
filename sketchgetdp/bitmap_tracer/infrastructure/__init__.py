"""
Infrastructure Layer - Frameworks & Drivers

Contains concrete implementations of technical concerns and external interfaces.
This layer is the outermost in Clean Architecture and depends inward toward the core.

Responsibilities:
- Image processing with OpenCV
- Shape processing  
- Configuration file management
- Point detection and curve fitting algorithms

Dependencies:
- Can depend on core entities and use cases
- Must not contain business logic
- Implements interfaces defined in the interfaces layer
"""

from .image_processing import *
from .shape_processing import *
from .configuration import *
from .point_detection import *

__all__ = [
    # Image processing components
    "ContourDetector",
    "ColorAnalyzer", 
    "ContourClosureService",
    
    # Shape processing components
    "ShapeProcessor",
    
    # Configuration components
    "ConfigLoader",
    
    # Point detection components
    "PointDetector",
    "CurveFitter",
]