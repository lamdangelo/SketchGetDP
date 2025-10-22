"""
Infrastructure Layer - Frameworks & Drivers

Contains concrete implementations of technical concerns and external interfaces.
This layer is the outermost in Clean Architecture and depends inward toward the core.

Responsibilities:
- Image processing with OpenCV
- SVG document generation  
- Configuration file management
- Point detection and curve fitting algorithms

Dependencies:
- Can depend on core entities and use cases
- Must not contain business logic
- Implements interfaces defined in the interfaces layer
"""

from .image_processing import *
from .svg_generation import *
from .configuration import *
from .point_detection import *

__all__ = [
    # Image processing components
    "ContourDetector",
    "ColorAnalyzer", 
    "ContourClosureService",
    
    # SVG generation components
    "SVGGenerator",
    "ShapeProcessor",
    
    # Configuration components
    "ConfigLoader",
    
    # Point detection components
    "PointDetector",
    "CurveFitter",
]