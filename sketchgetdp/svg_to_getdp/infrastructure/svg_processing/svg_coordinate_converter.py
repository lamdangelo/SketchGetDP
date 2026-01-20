"""
Converts SVG coordinates to the application's unit coordinate system.
Handles viewbox scaling, dimension fallbacks, and Y-axis flipping.
"""

import re
from typing import Optional, Tuple
from svg_to_getdp.core.entities.point import Point


class SvgCoordinateConverter:
    """
    Converts SVG coordinates to normalized unit coordinates [0,1]×[0,1].
    Handles viewbox parsing, dimension extraction, and coordinate transformation.
    """
    
    def scale_to_unit_coordinates(self, point: Point, 
                                viewbox: Optional[Tuple[float, float, float, float]], 
                                svg_width: float, svg_height: float) -> Point:
        """
        Scale point to unit square [0,1]×[0,1] and flip Y-axis.
        """
        if viewbox:
            viewbox_x, viewbox_y, viewbox_width, viewbox_height = viewbox
            if viewbox_width > 0 and viewbox_height > 0:
                normalized_x = (point.x - viewbox_x) / viewbox_width
                normalized_y = (point.y - viewbox_y) / viewbox_height
                flipped_y = 1.0 - normalized_y
                return Point(normalized_x, flipped_y)
        
        if svg_width > 0 and svg_height > 0:
            normalized_x = point.x / svg_width
            normalized_y = point.y / svg_height
            flipped_y = 1.0 - normalized_y
            return Point(normalized_x, flipped_y)
        
        # Fallback to default scaling
        normalized_x = point.x / 100.0
        normalized_y = point.y / 100.0
        flipped_y = 1.0 - normalized_y
        return Point(normalized_x, flipped_y)
    
    def parse_viewbox(self, viewbox_string: str) -> Optional[Tuple[float, float, float, float]]:
        """Parse SVG viewBox attribute."""
        if not viewbox_string:
            return None
        
        try:
            coordinates = [float(coord) for coord in viewbox_string.split()]
            return tuple(coordinates) if len(coordinates) == 4 else None
        except ValueError:
            return None
    
    def get_svg_dimensions(self, root_element) -> Tuple[float, float]:
        """Extract SVG width and height as fallback for scaling."""
        try:
            width_string = root_element.get('width', '100')
            height_string = root_element.get('height', '100')
            
            width = float(re.sub(r'[^\d.]', '', width_string))
            height = float(re.sub(r'[^\d.]', '', height_string))
            return width, height
        except (ValueError, TypeError):
            return 100.0, 100.0
        