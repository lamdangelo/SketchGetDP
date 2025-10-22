"""
Core business entities for bitmap tracing.
These objects represent the fundamental concepts that drive the tracing algorithm:
- Spatial coordinates and relationships
- Shape boundaries and properties  
- Color classification and standardization

The entities contain the business rules that determine how bitmap features
are interpreted and converted to vector graphics.
"""

from .point import Point, PointData
from .contour import ClosedContour
from .color import Color, ColorCategory

__all__ = [
    'Point',
    'PointData', 
    'ClosedContour',
    'Color',
    'ColorCategory'
]