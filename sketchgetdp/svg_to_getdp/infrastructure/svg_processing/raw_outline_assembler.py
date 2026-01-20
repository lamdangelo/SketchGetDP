"""
Assembles RawOutline objects from processed SVG data.
Handles creation and validation of RawOutline instances.
"""

from typing import List
from svg_to_getdp.core.entities.point import Point
from svg_to_getdp.core.entities.color import Color
from svg_to_getdp.core.entities.raw_outline import RawOutline


class RawOutlineAssembler:
    """
    Assembles RawOutline objects from processed components.
    Provides factory methods for creating validated RawOutline instances.
    """
    
    @staticmethod
    def create_raw_outline(points: List[Point], color: Color, is_closed: bool = True) -> RawOutline:
        """
        Create and validate a RawOutline instance.
        """
        raw_outline = RawOutline(points=points, color=color, is_closed=is_closed)

        return raw_outline
    
    @staticmethod
    def create_red_dot(point: Point) -> RawOutline:
        """
        Create a RawOutline for a red dot (single point).
        """
        return RawOutline(points=[point], color=Color.RED, is_closed=True)
    
    @staticmethod
    def create_polyline(points: List[Point], color: Color, is_closed: bool = False) -> RawOutline:
        """
        Create a RawOutline for a polyline (open or closed).
        """
        if color != Color.RED and len(points) < 3:
            raise ValueError(f"Polyline must have at least 3 points for color {color.name}, got {len(points)}")
        
        return RawOutline(points=points, color=color, is_closed=is_closed)
    