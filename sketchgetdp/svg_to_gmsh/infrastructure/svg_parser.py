"""
SVG Parser for converting SVG sketches to internal geometry representation.
"""

import xml.etree.ElementTree as ET
import math
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from core.entities.point import Point
from core.entities.color import Color


@dataclass
class RawBoundary:
    """
    Temporary data structure for raw boundary data extracted from SVG.
    This will be converted to BoundaryCurve later after Bezier fitting.
    """
    points: List[Point]
    color: Color
    is_closed: bool = True
    
    def __post_init__(self):
        """Validate the raw boundary data."""
        if len(self.points) < 3:
            raise ValueError("Raw boundary must have at least 3 points")


class SVGParser:
    """
    Parses SVG files to extract colored boundary curves as ordered point sets.
    """
    
    def __init__(self):
        self.namespace = '{http://www.w3.org/2000/svg}'
    
    def parse(self, svg_file_path: str) -> Dict[Color, List[RawBoundary]]:
        """
        Parse SVG file and extract boundary curves grouped by color.
        
        Args:
            svg_file_path: Path to the SVG file
            
        Returns:
            Dictionary mapping colors to lists of RawBoundary objects containing raw points.
            
        Raises:
            ValueError: If the SVG file is invalid or cannot be parsed
        """
        try:
            tree = ET.parse(svg_file_path)
            root = tree.getroot()
        except ET.ParseError as e:
            raise ValueError(f"Invalid SVG file: {e}")
        except FileNotFoundError:
            raise ValueError(f"SVG file not found: {svg_file_path}")
        
        # Extract viewBox for scaling to unit square
        # Also get width/height as fallback
        viewbox = self._parse_viewbox(root.get('viewBox'))
        svg_width, svg_height = self._parse_svg_dimensions(root)
        
        # Group elements by color
        colored_elements = self._group_elements_by_color(root)
        
        # Convert elements to raw boundaries
        colored_boundaries = {}
        for color, elements in colored_elements.items():
            boundaries = []
            for element in elements:
                points = self._element_to_points(element, viewbox, svg_width, svg_height)
                if len(points) >= 3:  # Need at least 3 points for a meaningful boundary
                    raw_boundary = RawBoundary(
                        points=points,
                        color=color,
                        is_closed=self._is_element_closed(element)
                    )
                    boundaries.append(raw_boundary)
            
            if boundaries:
                colored_boundaries[color] = boundaries
        
        return colored_boundaries
    
    def _parse_viewbox(self, viewbox_str: str) -> Optional[Tuple[float, float, float, float]]:
        """
        Parse SVG viewBox attribute to get scaling parameters.
        Returns (min_x, min_y, width, height)
        """
        if not viewbox_str:
            return None
        
        try:
            coords = [float(x) for x in viewbox_str.split()]
            if len(coords) == 4:
                return tuple(coords)
            else:
                return None
        except ValueError:
            return None
    
    def _parse_svg_dimensions(self, root: ET.Element) -> Tuple[float, float]:
        """Parse SVG width and height attributes as fallback for scaling."""
        try:
            # Remove units if present (e.g., "100px" -> 100.0)
            width_str = root.get('width', '100')
            height_str = root.get('height', '100')
            
            width = float(re.sub(r'[^\d.]', '', width_str))
            height = float(re.sub(r'[^\d.]', '', height_str))
            return width, height
        except (ValueError, TypeError):
            return 100.0, 100.0  # Default fallback
    
    def _group_elements_by_color(self, root: ET.Element) -> Dict[Color, List[ET.Element]]:
        """
        Group SVG elements by their stroke color
        """
        colored_elements = {}
        
        # Find all path and basic shape elements that represent boundaries
        elements = []
        for tag in ['path', 'rect', 'circle', 'ellipse', 'polygon', 'polyline']:
            # Search at all levels
            found_elements = root.findall(f'.//{self.namespace}{tag}')
            elements.extend(found_elements)
        
        for element in elements:
            color = self._extract_color(element)
            if color not in colored_elements:
                colored_elements[color] = []
            colored_elements[color].append(element)
        
        return colored_elements
    
    def _extract_color(self, element: ET.Element) -> Color:
        """
        Extract color from SVG element's stroke attribute.
        """
        stroke = element.get('stroke')
        
        if not stroke or stroke == 'none':
            return Color.RED  # Default color
        
        # Handle different color formats
        stroke_lower = stroke.lower().strip()
        
        # Map common colors to our three electrode colors
        if (stroke_lower == '#ff0000' or stroke_lower == 'red' or 
            stroke_lower == 'rgb(255,0,0)' or stroke_lower == 'rgb(255, 0, 0)'):
            return Color.RED
        elif (stroke_lower == '#00ff00' or stroke_lower == 'green' or 
              stroke_lower == 'rgb(0,255,0)' or stroke_lower == 'rgb(0, 255, 0)'):
            return Color.GREEN
        elif (stroke_lower == '#0000ff' or stroke_lower == 'blue' or 
              stroke_lower == 'rgb(0,0,255)' or stroke_lower == 'rgb(0, 0, 255)'):
            return Color.BLUE
        elif stroke_lower.startswith('#'):
            # For other hex colors, map to closest primary color
            return self._hex_to_primary_color(stroke_lower)
        elif stroke_lower.startswith('rgb'):
            # Handle rgb format with spaces
            return self._parse_rgb_color(stroke_lower)
        else:
            # Try to match color names more broadly
            if 'red' in stroke_lower:
                return Color.RED
            elif 'green' in stroke_lower:
                return Color.GREEN
            elif 'blue' in stroke_lower:
                return Color.BLUE
            else:
                return Color.RED  # Default
    
    def _parse_rgb_color(self, rgb_str: str) -> Color:
        """Parse rgb color string with various formats."""
        # Match rgb(r, g, b) with optional spaces
        match = re.match(r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', rgb_str)
        if match:
            r, g, b = map(int, match.groups())
            if r == 255 and g == 0 and b == 0:
                return Color.RED
            elif r == 0 and g == 255 and b == 0:
                return Color.GREEN
            elif r == 0 and g == 0 and b == 255:
                return Color.BLUE
        return Color.RED  # Default
    
    def _hex_to_primary_color(self, hex_str: str) -> Color:
        """Convert arbitrary hex color to closest primary color."""
        hex_str = hex_str.lstrip('#')
        
        if len(hex_str) == 6:
            r = int(hex_str[0:2], 16)
            g = int(hex_str[2:4], 16)
            b = int(hex_str[4:6], 16)
        elif len(hex_str) == 3:
            r = int(hex_str[0] * 2, 16)
            g = int(hex_str[1] * 2, 16)
            b = int(hex_str[2] * 2, 16)
        else:
            return Color.RED
        
        # Find closest primary color by Euclidean distance in RGB space
        colors = {
            Color.RED: (255, 0, 0),
            Color.GREEN: (0, 255, 0),
            Color.BLUE: (0, 0, 255)
        }
        
        min_distance = float('inf')
        closest_color = Color.RED
        
        for color, (cr, cg, cb) in colors.items():
            distance = math.sqrt((r - cr)**2 + (g - cg)**2 + (b - cb)**2)
            if distance < min_distance:
                min_distance = distance
                closest_color = color
        
        return closest_color
    
    def _is_element_closed(self, element: ET.Element) -> bool:
        """Determine if an SVG element represents a closed shape."""
        tag = element.tag.replace(self.namespace, '')
        if tag == 'path':
            # Check if path has 'z' or 'Z' command
            path_data = element.get('d', '')
            return 'z' in path_data.lower()
        return tag in ['rect', 'circle', 'ellipse', 'polygon']
    
    def _element_to_points(self, element: ET.Element, viewbox: Optional[Tuple[float, float, float, float]], 
                          svg_width: float, svg_height: float) -> List[Point]:
        """
        Convert SVG element to ordered list of points.
        """
        tag = element.tag.replace(self.namespace, '')
        
        if tag == 'path':
            return self._parse_path(element.get('d', ''), viewbox, svg_width, svg_height)
        elif tag == 'rect':
            return self._parse_rect(element, viewbox, svg_width, svg_height)
        elif tag == 'circle':
            return self._parse_circle(element, viewbox, svg_width, svg_height)
        elif tag == 'ellipse':
            return self._parse_ellipse(element, viewbox, svg_width, svg_height)
        elif tag == 'polygon':
            return self._parse_polygon(element.get('points', ''), viewbox, svg_width, svg_height)
        elif tag == 'polyline':
            return self._parse_polyline(element.get('points', ''), viewbox, svg_width, svg_height)
        else:
            return []
    
    def _parse_path(self, path_data: str, viewbox: Optional[Tuple[float, float, float, float]], 
                   svg_width: float, svg_height: float) -> List[Point]:
        """
        Parse SVG path data into points.
        For simple paths with only 2 points, we'll create a triangle to make it a valid boundary.
        """
        points = []
        
        # Extract move-to (M) and line-to (L) commands with coordinates
        commands = re.findall(r'([ML])\s*([-\d.]+)\s*([-\d.]+)', path_data, re.IGNORECASE)
        
        for cmd, x_str, y_str in commands:
            try:
                x = float(x_str)
                y = float(y_str)
                points.append(self._scale_point(Point(x, y), viewbox, svg_width, svg_height))
            except ValueError:
                continue
        
        # If we only have 2 points, create a third point to make a triangle
        if len(points) == 2:
            # Create a third point to form a triangle
            p1, p2 = points[0], points[1]
            # Calculate midpoint and offset perpendicularly
            mid_x = (p1.x + p2.x) / 2
            mid_y = (p1.y + p2.y) / 2
            # Calculate perpendicular vector
            dx = p2.x - p1.x
            dy = p2.y - p1.y
            # Rotate 90 degrees and scale
            perp_x = -dy * 0.1  # Small offset
            perp_y = dx * 0.1
            # Add the third point
            points.append(Point(mid_x + perp_x, mid_y + perp_y))
            # Close the triangle
            points.append(points[0])
        
        # If path is closed (z command), ensure last point connects to first
        elif 'z' in path_data.lower() and len(points) > 1:
            points.append(points[0])
        
        return points
    
    def _parse_rect(self, element: ET.Element, viewbox: Optional[Tuple[float, float, float, float]], 
                   svg_width: float, svg_height: float) -> List[Point]:
        """Convert rectangle to boundary points."""
        try:
            x = float(element.get('x', 0))
            y = float(element.get('y', 0))
            width = float(element.get('width', 0))
            height = float(element.get('height', 0))
            
            points = [
                Point(x, y),
                Point(x + width, y),
                Point(x + width, y + height),
                Point(x, y + height),
                Point(x, y)  # Close the rectangle
            ]
            
            return [self._scale_point(p, viewbox, svg_width, svg_height) for p in points]
        except (ValueError, TypeError):
            return []
    
    def _parse_circle(self, element: ET.Element, viewbox: Optional[Tuple[float, float, float, float]], 
                     svg_width: float, svg_height: float) -> List[Point]:
        """Convert circle to boundary points (approximated as polygon)."""
        try:
            cx = float(element.get('cx', 0))
            cy = float(element.get('cy', 0))
            r = float(element.get('r', 0))
            
            return self._approximate_circle(cx, cy, r, viewbox, svg_width, svg_height)
        except (ValueError, TypeError):
            return []
    
    def _parse_ellipse(self, element: ET.Element, viewbox: Optional[Tuple[float, float, float, float]], 
                      svg_width: float, svg_height: float) -> List[Point]:
        """Convert ellipse to boundary points (approximated as polygon)."""
        try:
            cx = float(element.get('cx', 0))
            cy = float(element.get('cy', 0))
            rx = float(element.get('rx', 0))
            ry = float(element.get('ry', 0))
            
            return self._approximate_ellipse(cx, cy, rx, ry, viewbox, svg_width, svg_height)
        except (ValueError, TypeError):
            return []
    
    def _parse_polygon(self, points_str: str, viewbox: Optional[Tuple[float, float, float, float]], 
                      svg_width: float, svg_height: float) -> List[Point]:
        """Parse polygon points string (automatically closed)."""
        points = self._parse_poly_points(points_str, viewbox, svg_width, svg_height)
        if points and len(points) > 2:
            # Ensure polygon is closed by adding first point at the end
            # Only if it's not already closed
            if points[0] != points[-1]:
                points.append(points[0])
        return points
    
    def _parse_polyline(self, points_str: str, viewbox: Optional[Tuple[float, float, float, float]], 
                       svg_width: float, svg_height: float) -> List[Point]:
        """Parse polyline points string (not automatically closed)."""
        points = self._parse_poly_points(points_str, viewbox, svg_width, svg_height)
        # For polylines with only 2 points, create a third point
        if len(points) == 2:
            p1, p2 = points[0], points[1]
            mid_x = (p1.x + p2.x) / 2
            mid_y = (p1.y + p2.y) / 2
            dx = p2.x - p1.x
            dy = p2.y - p1.y
            perp_x = -dy * 0.1
            perp_y = dx * 0.1
            points.append(Point(mid_x + perp_x, mid_y + perp_y))
        return points
    
    def _parse_poly_points(self, points_str: str, viewbox: Optional[Tuple[float, float, float, float]], 
                          svg_width: float, svg_height: float) -> List[Point]:
        """Parse points string for polygon/polyline."""
        points = []
        coords = re.findall(r'[-\d.]+', points_str)
        
        for i in range(0, len(coords) - 1, 2):
            try:
                x = float(coords[i])
                y = float(coords[i + 1])
                points.append(self._scale_point(Point(x, y), viewbox, svg_width, svg_height))
            except (ValueError, IndexError):
                continue
        
        return points
    
    def _approximate_circle(self, cx: float, cy: float, r: float, 
                           viewbox: Optional[Tuple[float, float, float, float]], 
                           svg_width: float, svg_height: float) -> List[Point]:
        """Approximate circle as polygon with 32 segments."""
        points = []
        num_segments = 32
        
        for i in range(num_segments + 1):
            angle = 2 * math.pi * i / num_segments
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            points.append(self._scale_point(Point(x, y), viewbox, svg_width, svg_height))
        
        return points
    
    def _approximate_ellipse(self, cx: float, cy: float, rx: float, ry: float, 
                            viewbox: Optional[Tuple[float, float, float, float]], 
                            svg_width: float, svg_height: float) -> List[Point]:
        """Approximate ellipse as polygon with 32 segments."""
        points = []
        num_segments = 32
        
        for i in range(num_segments + 1):
            angle = 2 * math.pi * i / num_segments
            x = cx + rx * math.cos(angle)
            y = cy + ry * math.sin(angle)
            points.append(self._scale_point(Point(x, y), viewbox, svg_width, svg_height))
        
        return points
    
    def _scale_point(self, point: Point, viewbox: Optional[Tuple[float, float, float, float]], 
                    svg_width: float, svg_height: float) -> Point:
        """
        Scale point to unit square [0,1]×[0,1].
        This ensures diam(Ω) < 1 condition for BEM functionality.
        """
        if viewbox:
            vx, vy, vw, vh = viewbox
            if vw > 0 and vh > 0:
                # Normalize to [0,1] range using viewBox
                x_norm = (point.x - vx) / vw
                y_norm = (point.y - vy) / vh
                return Point(x_norm, y_norm)
        
        # Fallback: use SVG dimensions or default scaling
        if svg_width > 0 and svg_height > 0:
            x_norm = point.x / svg_width
            y_norm = point.y / svg_height
            return Point(x_norm, y_norm)
        
        # Final fallback: assume reasonable default bounds
        return Point(point.x / 100.0, point.y / 100.0)