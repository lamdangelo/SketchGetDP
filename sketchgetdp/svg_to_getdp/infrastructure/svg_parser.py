"""
SVG Parser for converting SVG sketches to internal geometry representation.
"""

import xml.etree.ElementTree as ET
import math
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from svgpathtools import svg2paths, Path, Line, CubicBezier, QuadraticBezier, Arc

from ..core.entities.point import Point
from ..core.entities.color import Color
from ..interfaces.abstractions.svg_parser_interface import SVGParserInterface


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
        # Allow single points for red dots, but require >=3 points for other colors
        if self.color != Color.RED and len(self.points) < 3:
            raise ValueError(f"Raw boundary must have at least 3 points for color {self.color.name}, got {len(self.points)}")
        elif self.color == Color.RED and len(self.points) < 1:
            raise ValueError("Red dot must have at least 1 point")


class SVGParser(SVGParserInterface):
    """
    SVG parser that uses svgpathtools for all path parsing
    while adding custom logic for color extraction, scaling, and shape handling.
    """
    
    def __init__(self, samples_per_segment: int = 20, points_per_unit_length: int = 1000):
        self.namespace = '{http://www.w3.org/2000/svg}'
        self.samples_per_segment = samples_per_segment
        self.points_per_unit_length = points_per_unit_length
    
    def extract_boundaries_by_color(self, svg_file_path: str) -> Dict[Color, List[RawBoundary]]:
        """
        Parse SVG file and extract boundary curves grouped by color.
        
        Strategy:
        1. Use svg2paths for all non-red paths (green, blue, black)
        2. Parse circle/ellipse elements directly from XML for red structures
           (more flexible approach that works with arbitrary red structures)
        """
        try:
            # Parse the XML tree to access all elements
            tree = ET.parse(svg_file_path)
            root = tree.getroot()
            
            # Parse paths with svgpathtools (will skip red paths in _convert_paths_to_boundaries)
            paths, attributes = svg2paths(svg_file_path)
            
        except Exception as e:
            raise ValueError(f"Invalid SVG file: {e}")
        
        viewbox = self._parse_viewbox(root.get('viewBox'))
        svg_width, svg_height = self._get_svg_dimensions(root)
        
        # Parse paths from svgpathtools
        # Red paths will be handled separately via XML parsing for more flexibility
        path_boundaries = self._convert_paths_to_boundaries(
            paths, attributes, viewbox, svg_width, svg_height
        )
        
        # Parse circle AND ellipse elements separately - ONLY FOR RED
        # This gives us more flexibility to handle arbitrary red structures
        red_dots_boundaries = {}
        
        # Find all circle and ellipse elements
        for element_name in ['circle', 'ellipse']:
            for elem in root.iter(f'{self.namespace}{element_name}'):
                try:
                    style = elem.get('style', '')
                    color = self._extract_color_from_style(style)
                    
                    # Only process red circles/ellipses - skip other colors
                    if color != Color.RED:
                        continue
                        
                    transform = elem.get('transform', '')
                    cx = float(elem.get('cx', '0'))
                    cy = float(elem.get('cy', '0'))
                    
                    # Apply transform if present
                    if transform:
                        transformed_point = self._apply_transform_to_point(cx, cy, transform)
                        cx, cy = transformed_point
                    
                    # Scale to unit coordinates
                    point = Point(cx, cy)
                    scaled_point = self._scale_to_unit_coordinates(point, viewbox, svg_width, svg_height)
                    
                    # For red dots, we just want the center point
                    boundary = RawBoundary(
                        points=[scaled_point],
                        color=color,
                        is_closed=True
                    )
                    
                    if color not in red_dots_boundaries:
                        red_dots_boundaries[color] = []
                    red_dots_boundaries[color].append(boundary)
                    
                except Exception as e:
                    print(f"WARNING: Failed to process {element_name} element: {e}")
                    continue
        
        # Merge both results - path boundaries (green, blue, black) and red dots
        boundaries_by_color = self._merge_boundaries(path_boundaries, red_dots_boundaries)
        
        # Apply post-processing resampling to ensure even point distribution
        resampled_boundaries = self._resample_all_boundaries(boundaries_by_color)
        
        # Remove duplicate points from all boundaries after resampling
        clean_boundaries = self._remove_duplicates_from_all_boundaries(resampled_boundaries)
        
        # Merge nearby boundaries of the same color
        merged_boundaries = self._merge_nearby_boundaries(clean_boundaries, distance_threshold=0.02)
        
        return merged_boundaries

    def _process_all_svg_elements(self, root: ET.Element, 
                                viewbox: Optional[Tuple[float, float, float, float]],
                                svg_width: float, svg_height: float) -> Dict[Color, List[RawBoundary]]:
        """
        Process all SVG elements to extract boundaries by color.
        Handles paths, circles, ellipses, rectangles, lines, polygons, and polylines.
        """
        boundaries_by_color = {}
        
        # Element types to process
        element_types = [
            'path', 'circle', 'ellipse', 'rect', 
            'line', 'polygon', 'polyline'
        ]
        
        for element_name in element_types:
            for elem in root.iter(f'{self.namespace}{element_name}'):
                try:
                    # Skip elements with no style or display:none
                    style = elem.get('style', '')
                    if 'display:none' in style:
                        continue
                        
                    # Extract color from the element
                    color = self._extract_color_from_element(elem)
                    
                    # Process the element based on its type
                    if element_name == 'path':
                        boundaries = self._process_path_element(elem, viewbox, svg_width, svg_height)
                    elif element_name == 'circle':
                        boundaries = self._process_circle_element(elem, viewbox, svg_width, svg_height)
                    elif element_name == 'ellipse':
                        boundaries = self._process_ellipse_element(elem, viewbox, svg_width, svg_height)
                    elif element_name == 'rect':
                        boundaries = self._process_rect_element(elem, viewbox, svg_width, svg_height)
                    elif element_name == 'line':
                        boundaries = self._process_line_element(elem, viewbox, svg_width, svg_height)
                    elif element_name == 'polygon':
                        boundaries = self._process_polygon_element(elem, viewbox, svg_width, svg_height)
                    elif element_name == 'polyline':
                        boundaries = self._process_polyline_element(elem, viewbox, svg_width, svg_height)
                    else:
                        continue
                    
                    # Add boundaries with their color
                    for boundary in boundaries:
                        boundary_with_color = RawBoundary(
                            points=boundary['points'],
                            color=color,
                            is_closed=boundary['is_closed']
                        )
                        
                        if color not in boundaries_by_color:
                            boundaries_by_color[color] = []
                        boundaries_by_color[color].append(boundary_with_color)
                    
                except Exception as e:
                    print(f"WARNING: Failed to process {element_name} element: {e}")
                    continue
        
        return boundaries_by_color

    def _extract_color_from_element(self, elem: ET.Element) -> Color:
        """
        Extract color from an SVG element.
        Checks style, fill, and stroke attributes.
        """
        # Get style attribute
        style = elem.get('style', '')
        if style:
            try:
                return self._extract_color_from_style(style)
            except:
                pass
        
        # Check fill attribute directly
        fill = elem.get('fill', '')
        if fill and fill != 'none':
            return self._parse_color_string(fill)
        
        # Check stroke attribute directly
        stroke = elem.get('stroke', '')
        if stroke and stroke != 'none':
            return self._parse_color_string(stroke)
        
        # Raise error if no color found
        raise ValueError(f"No color found in element: {elem.tag}")

    def _process_circle_element(self, elem: ET.Element, viewbox, svg_width, svg_height) -> List[Dict]:
        """Process a circle element."""
        cx = float(elem.get('cx', '0'))
        cy = float(elem.get('cy', '0'))
        r = float(elem.get('r', '0'))
        
        # Get transform
        transform = elem.get('transform', '')
        
        # Sample points around the circle
        points = []
        num_samples = 32  # Number of points to sample around the circle
        
        for i in range(num_samples):
            angle = 2 * math.pi * i / num_samples
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            
            # Apply transform if present
            if transform:
                x, y = self._apply_transform_to_point(x, y, transform)
            
            point = Point(x, y)
            scaled_point = self._scale_to_unit_coordinates(point, viewbox, svg_width, svg_height)
            points.append(scaled_point)
        
        # Close the circle
        if points and points[0] != points[-1]:
            points.append(points[0])
        
        return [{'points': points, 'is_closed': True}]

    def _process_ellipse_element(self, elem: ET.Element, viewbox, svg_width, svg_height) -> List[Dict]:
        """Process an ellipse element."""
        cx = float(elem.get('cx', '0'))
        cy = float(elem.get('cy', '0'))
        rx = float(elem.get('rx', '0'))
        ry = float(elem.get('ry', '0'))
        
        # Get transform
        transform = elem.get('transform', '')
        
        # Sample points around the ellipse
        points = []
        num_samples = 32  # Number of points to sample around the ellipse
        
        for i in range(num_samples):
            angle = 2 * math.pi * i / num_samples
            x = cx + rx * math.cos(angle)
            y = cy + ry * math.sin(angle)
            
            # Apply transform if present
            if transform:
                x, y = self._apply_transform_to_point(x, y, transform)
            
            point = Point(x, y)
            scaled_point = self._scale_to_unit_coordinates(point, viewbox, svg_width, svg_height)
            points.append(scaled_point)
        
        # Close the ellipse
        if points and points[0] != points[-1]:
            points.append(points[0])
        
        return [{'points': points, 'is_closed': True}]

    def _process_path_element(self, elem: ET.Element, viewbox, svg_width, svg_height) -> List[Dict]:
        """Process a path element using svgpathtools."""
        # Extract path data
        d = elem.get('d', '')
        if not d:
            return []
        
        # Get transform
        transform = elem.get('transform', '')
        
        try:
            # Create a simple path from the d attribute
            from svgpathtools import parse_path
            path = parse_path(d)
            
            # Apply transform if present
            if transform:
                # Note: svgpathtools has transform methods, but for simplicity
                # we'll apply to sampled points
                pass
            
            # Convert path to points
            points = []
            for segment in path:
                segment_points = self._sample_segment_points(segment, self.samples_per_segment)
                points.extend(segment_points)
            
            points = self._remove_consecutive_duplicate_points(points)
            
            # Scale points
            scaled_points = [self._scale_to_unit_coordinates(p, viewbox, svg_width, svg_height) for p in points]
            
            # Apply transform to scaled points
            if transform:
                transformed_points = []
                for point in scaled_points:
                    x, y = self._apply_transform_to_point(point.x, point.y, transform)
                    transformed_points.append(Point(x, y))
                scaled_points = transformed_points
            
            # Check if path is closed
            is_closed = self._is_path_closed(path)
            
            return [{'points': scaled_points, 'is_closed': is_closed}]
            
        except Exception as e:
            print(f"WARNING: Failed to parse path: {e}")
            return []

    def _process_rect_element(self, elem: ET.Element, viewbox, svg_width, svg_height) -> List[Dict]:
        """Process a rectangle element."""
        x = float(elem.get('x', '0'))
        y = float(elem.get('y', '0'))
        width = float(elem.get('width', '0'))
        height = float(elem.get('height', '0'))
        
        # Get transform
        transform = elem.get('transform', '')
        
        # Create rectangle points
        points_data = [
            (x, y),
            (x + width, y),
            (x + width, y + height),
            (x, y + height)
        ]
        
        points = []
        for px, py in points_data:
            # Apply transform if present
            if transform:
                px, py = self._apply_transform_to_point(px, py, transform)
            
            point = Point(px, py)
            scaled_point = self._scale_to_unit_coordinates(point, viewbox, svg_width, svg_height)
            points.append(scaled_point)
        
        # Close the rectangle
        if points and points[0] != points[-1]:
            points.append(points[0])
        
        return [{'points': points, 'is_closed': True}]

    def _process_line_element(self, elem: ET.Element, viewbox, svg_width, svg_height) -> List[Dict]:
        """Process a line element."""
        x1 = float(elem.get('x1', '0'))
        y1 = float(elem.get('y1', '0'))
        x2 = float(elem.get('x2', '0'))
        y2 = float(elem.get('y2', '0'))
        
        # Get transform
        transform = elem.get('transform', '')
        
        points_data = [(x1, y1), (x2, y2)]
        
        points = []
        for px, py in points_data:
            # Apply transform if present
            if transform:
                px, py = self._apply_transform_to_point(px, py, transform)
            
            point = Point(px, py)
            scaled_point = self._scale_to_unit_coordinates(point, viewbox, svg_width, svg_height)
            points.append(scaled_point)
        
        return [{'points': points, 'is_closed': False}]

    def _process_polygon_element(self, elem: ET.Element, viewbox, svg_width, svg_height) -> List[Dict]:
        """Process a polygon element."""
        points_str = elem.get('points', '')
        if not points_str:
            return []
        
        # Parse points string (format: "x1,y1 x2,y2 x3,y3 ...")
        points_data = []
        for coord_pair in points_str.strip().split():
            if ',' in coord_pair:
                x, y = map(float, coord_pair.split(','))
                points_data.append((x, y))
        
        # Get transform
        transform = elem.get('transform', '')
        
        points = []
        for px, py in points_data:
            # Apply transform if present
            if transform:
                px, py = self._apply_transform_to_point(px, py, transform)
            
            point = Point(px, py)
            scaled_point = self._scale_to_unit_coordinates(point, viewbox, svg_width, svg_height)
            points.append(scaled_point)
        
        # Close the polygon (already closed by definition)
        if points and points[0] != points[-1]:
            points.append(points[0])
        
        return [{'points': points, 'is_closed': True}]

    def _process_polyline_element(self, elem: ET.Element, viewbox, svg_width, svg_height) -> List[Dict]:
        """Process a polyline element."""
        points_str = elem.get('points', '')
        if not points_str:
            return []
        
        # Parse points string (format: "x1,y1 x2,y2 x3,y3 ...")
        points_data = []
        for coord_pair in points_str.strip().split():
            if ',' in coord_pair:
                x, y = map(float, coord_pair.split(','))
                points_data.append((x, y))
        
        # Get transform
        transform = elem.get('transform', '')
        
        points = []
        for px, py in points_data:
            # Apply transform if present
            if transform:
                px, py = self._apply_transform_to_point(px, py, transform)
            
            point = Point(px, py)
            scaled_point = self._scale_to_unit_coordinates(point, viewbox, svg_width, svg_height)
            points.append(scaled_point)
        
        return [{'points': points, 'is_closed': False}]
    
    def _convert_paths_to_boundaries(self, paths: List[Path], attributes: List[dict],
                                viewbox: Optional[Tuple[float, float, float, float]],
                                svg_width: float, svg_height: float) -> Dict[Color, List[RawBoundary]]:
        """
        Convert all SVG paths to boundary objects grouped by color.
        svg2paths converts circles/ellipses to paths, but we handle red ones separately.
        """
        boundaries_by_color = {}
        
        for path_index, (path, attr) in enumerate(zip(paths, attributes)):
            try:
                color = self._extract_color_from_attributes(attr)
                
                # SKIP RED PATHS - these are typically converted circles/ellipses
                # that we'll handle separately via XML parsing for more flexibility
                if color == Color.RED:
                    continue
                    
                points = self._convert_path_to_points(path, viewbox, svg_width, svg_height)
                
                if not points:
                    raise ValueError("Path contains no valid points")
                
                is_closed = self._is_path_closed(path)
                
                boundary = RawBoundary(
                    points=points,
                    color=color,
                    is_closed=is_closed
                )
                
                if boundary.color not in boundaries_by_color:
                    boundaries_by_color[boundary.color] = []
                boundaries_by_color[boundary.color].append(boundary)
                
            except Exception as e:
                print(f"WARNING: Failed to process path {path_index}: {e}")
                continue
        
        return boundaries_by_color
    
    def _extract_color_from_style(self, style_string: str) -> Color:
        """
        Extract color from SVG style attribute.
        """
        if not style_string:
            raise ValueError("No style attribute found")
        
        # Parse style string
        style_parts = [part.strip() for part in style_string.split(';')]
        color_str = None
        
        for part in style_parts:
            if part.startswith('fill:'):
                color_parts = part.split(':', 1)
                if len(color_parts) == 2:
                    color_str = color_parts[1].strip()
                    break
        
        if not color_str or color_str == 'none':
            raise ValueError(f"No valid fill color found in style: {style_string}")
        
        return self._parse_color_string(color_str)
    
    def _apply_transform_to_point(self, x: float, y: float, transform_str: str) -> Tuple[float, float]:
        """
        Apply SVG transform to a point.
        Handles matrix(), rotate(), scale(), and translate() transforms.
        """
        if not transform_str:
            return x, y
        
        # Parse matrix transform: matrix(a,b,c,d,e,f)
        matrix_match = re.match(r'matrix\s*\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)', transform_str)
        
        if matrix_match:
            a, b, c, d, e, f = map(float, matrix_match.groups())
            # Apply matrix transformation
            new_x = a * x + c * y + e
            new_y = b * x + d * y + f
            return new_x, new_y
        
        # Parse rotate transform: rotate(angle, cx, cy) or rotate(angle)
        rotate_match = re.match(r'rotate\s*\(\s*([-\d.]+)\s*(?:,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*)?\)', transform_str)
        
        if rotate_match:
            angle = float(rotate_match.group(1))
            # Convert to radians
            angle_rad = math.radians(angle)
            
            if rotate_match.group(2) and rotate_match.group(3):
                # Has center point
                cx = float(rotate_match.group(2))
                cy = float(rotate_match.group(3))
                # Translate to origin, rotate, translate back
                x_translated = x - cx
                y_translated = y - cy
                new_x = x_translated * math.cos(angle_rad) - y_translated * math.sin(angle_rad) + cx
                new_y = x_translated * math.sin(angle_rad) + y_translated * math.cos(angle_rad) + cy
            else:
                # No center point, rotate around origin (0,0)
                new_x = x * math.cos(angle_rad) - y * math.sin(angle_rad)
                new_y = x * math.sin(angle_rad) + y * math.cos(angle_rad)
            
            return new_x, new_y
        
        # Handle translate transforms
        translate_match = re.match(r'translate\s*\(\s*([-\d.]+)\s*(?:,\s*([-\d.]+)\s*)?\)', transform_str)
        if translate_match:
            tx = float(translate_match.group(1))
            ty = float(translate_match.group(2)) if translate_match.group(2) else 0
            return x + tx, y + ty
        
        # Handle scale transforms: scale(sx, sy) or scale(s)
        scale_match = re.match(r'scale\s*\(\s*([-\d.]+)\s*(?:,\s*([-\d.]+)\s*)?\)', transform_str)
        if scale_match:
            sx = float(scale_match.group(1))
            sy = float(scale_match.group(2)) if scale_match.group(2) else sx
            return x * sx, y * sy
        
        # Return original point if transform not recognized
        print(f"WARNING: Unsupported transform format: {transform_str}")
        return x, y
    
    def _merge_boundaries(self, boundaries1: Dict[Color, List[RawBoundary]], 
                        boundaries2: Dict[Color, List[RawBoundary]]) -> Dict[Color, List[RawBoundary]]:
        """
        Merge two dictionaries of boundaries.
        """
        merged = {}
        all_colors = set(boundaries1.keys()) | set(boundaries2.keys())
        
        for color in all_colors:
            merged[color] = []
            if color in boundaries1:
                merged[color].extend(boundaries1[color])
            if color in boundaries2:
                merged[color].extend(boundaries2[color])
        
        return merged
    
    def _resample_all_boundaries(self, boundaries_by_color: Dict[Color, List[RawBoundary]]) -> Dict[Color, List[RawBoundary]]:
        """
        Apply uniform resampling to all boundaries except red dots.
        """
        resampled_boundaries = {}
        
        for color, boundaries in boundaries_by_color.items():
            resampled_boundaries[color] = []
            for boundary in boundaries:
                if color == Color.RED:
                    # Don't resample red dots (single points)
                    resampled_boundaries[color].append(boundary)
                else:
                    # Resample polylines for even point distribution
                    resampled_points = self._resample_polyline_uniform(boundary.points)
                    resampled_boundary = RawBoundary(
                        points=resampled_points,
                        color=boundary.color,
                        is_closed=boundary.is_closed
                    )
                    resampled_boundaries[color].append(resampled_boundary)
        
        return resampled_boundaries
    
    def _resample_polyline_uniform(self, points: List[Point]) -> List[Point]:
        """
        Resample polyline to have evenly spaced points.
        
        Args:
            points: Original unevenly distributed points
            
        Returns:
            List of evenly spaced points
        """
        if len(points) < 2:
            return points
        
        # Calculate total length and segment lengths
        total_length = 0.0
        segment_lengths = []
        for i in range(len(points) - 1):
            segment_length = math.sqrt(
                (points[i+1].x - points[i].x)**2 + 
                (points[i+1].y - points[i].y)**2
            )
            segment_lengths.append(segment_length)
            total_length += segment_length
        
        if total_length <= 0:
            return points
        
        spacing = 1.0 / self.points_per_unit_length
        
        # Calculate how many points we need for each segment
        resampled_points = [points[0]]
        
        for segment_idx in range(len(segment_lengths)):
            segment_length = segment_lengths[segment_idx]
            segment_start = points[segment_idx]
            segment_end = points[segment_idx + 1]
            
            # Calculate how many points to place on this segment (excluding the start point)
            num_points_on_segment = max(1, int(segment_length / spacing))
            actual_spacing = segment_length / num_points_on_segment
            
            # Add points along this segment
            for i in range(1, num_points_on_segment):
                t = i * actual_spacing / segment_length
                new_x = segment_start.x + t * (segment_end.x - segment_start.x)
                new_y = segment_start.y + t * (segment_end.y - segment_start.y)
                resampled_points.append(Point(new_x, new_y))
            
            # Add the segment end point (unless it's the very last point of the polyline)
            if segment_idx < len(segment_lengths) - 1:
                resampled_points.append(segment_end)
        
        # Always include the very last point of the polyline
        if resampled_points[-1] != points[-1]:
            resampled_points.append(points[-1])
        
        return resampled_points
    
    def _convert_path_to_points(self, path: Path, viewbox: Optional[Tuple[float, float, float, float]],
                              svg_width: float, svg_height: float) -> List[Point]:
        """
        Convert svgpathtools Path object to list of scaled points.
        """
        points = []
        
        for segment in path:
            segment_points = self._sample_segment_points(segment, self.samples_per_segment)
            points.extend(segment_points)
        
        points = self._remove_consecutive_duplicate_points(points)
        return [self._scale_to_unit_coordinates(p, viewbox, svg_width, svg_height) for p in points]
    
    def _sample_segment_points(self, segment, samples_per_segment: int) -> List[Point]:
        """
        Sample multiple points from a path segment.
        """
        points = []
        
        if isinstance(segment, (Line, CubicBezier, QuadraticBezier, Arc)):
            for sample_index in range(samples_per_segment + 1):
                parameter = sample_index / samples_per_segment
                try:
                    complex_point = segment.point(parameter)
                    points.append(Point(complex_point.real, complex_point.imag))
                except Exception as e:
                    print(f"WARNING: Failed to sample segment at parameter={parameter}: {e}")
                    continue
        
        return points
    
    def _remove_consecutive_duplicate_points(self, points: List[Point]) -> List[Point]:
        """Remove consecutive duplicate points while preserving order."""
        if not points:
            return points
        
        unique_points = [points[0]]
        for current_point in points[1:]:
            if current_point != unique_points[-1]:
                unique_points.append(current_point)
        
        return unique_points
    
    def _remove_duplicate_end_point(self, points: List[Point]) -> List[Point]:
        """Remove closing duplicate point for closed paths."""
        if not points:
            return points

        # Check if path is closed (first and last points are the same)
        if len(points) > 1 and points[0] == points[-1]:
            # Remove the last point since it's a duplicate of the first
            points = points[:-1]
        
        return points
    
    def _is_path_closed(self, path: Path) -> bool:
        """
        Determine if a path forms a closed shape.
        """
        if len(path) == 0:
            return False
        
        try:
            start_point = path[0].point(0)
            end_point = path[-1].point(1)
            
            tolerance = 1e-6
            distance = abs(start_point - end_point)
            return distance < tolerance
        except:
            return False
    
    def _extract_color_from_attributes(self, attributes: dict) -> Color:
        """
        Extract color from svgpathtools attributes dictionary.
        """
        # Check stroke, fill, and style attributes
        stroke = attributes.get('stroke')
        fill = attributes.get('fill')
        style = attributes.get('style')
        
        color_str = None
        
        # Priority: stroke -> fill -> style attribute
        if stroke and stroke != 'none':
            color_str = stroke
        elif fill and fill != 'none':
            color_str = fill
        elif style:
            # Parse style attribute
            style_parts = [part.strip() for part in style.split(';')]
            for part in style_parts:
                if part.startswith('stroke:'):
                    color_parts = part.split(':', 1)
                    if len(color_parts) == 2:
                        potential_color = color_parts[1].strip()
                        if potential_color and potential_color != 'none':
                            color_str = potential_color
                            break
                elif part.startswith('fill:'):
                    color_parts = part.split(':', 1)
                    if len(color_parts) == 2:
                        potential_color = color_parts[1].strip()
                        if potential_color and potential_color != 'none':
                            color_str = potential_color
                            break
        
        if not color_str or color_str == 'none':
            raise ValueError(f"No valid color found in attributes: {attributes}")
        
        return self._parse_color_string(color_str)
    
    def _parse_color_string(self, color_string: str) -> Color:
        """Convert color string to Color enum."""
        normalized_color = color_string.lower().strip()
        
        if self._is_red_color(normalized_color):
            return Color.RED
        elif self._is_green_color(normalized_color):
            return Color.GREEN
        elif self._is_blue_color(normalized_color):
            return Color.BLUE
        elif self._is_black_color(normalized_color):
            return Color.BLACK
        elif normalized_color.startswith('#'):
            return self._convert_hex_to_primary_color(normalized_color)
        elif normalized_color.startswith('rgb'):
            return self._parse_rgb_color_string(normalized_color)
        else:
            return self._infer_color_from_name(normalized_color)
    
    def _is_red_color(self, color_string: str) -> bool:
        """Check if color string represents a red color."""
        red_representations = {
            '#ff0000', 'red', '#f00', '#ff0000ff',
            'rgb(255,0,0)', 'rgb(255, 0, 0)',
            '#fa0000'  # Added for your SVG
        }
        return color_string in red_representations
    
    def _is_green_color(self, color_string: str) -> bool:
        """Check if color string represents a green color."""
        green_representations = {
            '#00ff00', 'green', '#0f0', '#00ff00ff',
            'rgb(0,255,0)', 'rgb(0, 255, 0)',
            '#00f700'  # Added for your SVG
        }
        return color_string in green_representations
    
    def _is_blue_color(self, color_string: str) -> bool:
        """Check if color string represents a blue color."""
        blue_representations = {
            '#0000ff', 'blue', '#00f', '#0000ffff',
            'rgb(0,0,255)', 'rgb(0, 0, 255)',
            '#0000fb'  # Added for your SVG
        }
        return color_string in blue_representations
    
    def _is_black_color(self, color_string: str) -> bool:
        """Check if color string represents a black color."""
        black_representations = {
            '#000000', 'black', '#000', '#000000ff',
            'rgb(0,0,0)', 'rgb(0, 0, 0)'
        }
        return color_string in black_representations
    
    def _infer_color_from_name(self, color_name: str) -> Color:
        """Infer color from color name containing color hint."""
        if 'red' in color_name:
            return Color.RED
        elif 'green' in color_name:
            return Color.GREEN
        elif 'blue' in color_name:
            return Color.BLUE
        else:
            raise ValueError(f"Unknown color format: '{color_name}'")
    
    def _parse_rgb_color_string(self, rgb_string: str) -> Color:
        """Parse RGB color string and find closest primary color."""
        match = re.match(r'rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*[\d.]+\s*)?\)', rgb_string)
        if not match:
            raise ValueError(f"Invalid RGB color format: '{rgb_string}'")
        
        red, green, blue = map(int, match.groups())
        return self._find_closest_primary_color(red, green, blue)
    
    def _convert_hex_to_primary_color(self, hex_string: str) -> Color:
        """Convert hex color to closest primary color."""
        hex_digits = hex_string.lstrip('#')
        
        try:
            if len(hex_digits) == 6:
                red = int(hex_digits[0:2], 16)
                green = int(hex_digits[2:4], 16)
                blue = int(hex_digits[4:6], 16)
            elif len(hex_digits) == 3:
                red = int(hex_digits[0] * 2, 16)
                green = int(hex_digits[1] * 2, 16)
                blue = int(hex_digits[2] * 2, 16)
            else:
                raise ValueError(f"Invalid hex color length: {len(hex_digits)}")
            
            return self._find_closest_primary_color(red, green, blue)
            
        except ValueError as e:
            raise ValueError(f"Invalid hex color format '#{hex_digits}': {e}")

    def _find_closest_primary_color(self, red: int, green: int, blue: int) -> Color:
        """Find the closest primary color using Euclidean distance in RGB space."""
        primary_colors = {
            Color.RED: (255, 0, 0),
            Color.GREEN: (0, 255, 0),
            Color.BLUE: (0, 0, 255),
            Color.BLACK: (0, 0, 0)
        }
        
        min_distance = float('inf')
        closest_color = None
        
        for color, (target_red, target_green, target_blue) in primary_colors.items():
            distance = math.sqrt(
                (red - target_red)**2 + 
                (green - target_green)**2 + 
                (blue - target_blue)**2
            )
            if distance < min_distance:
                min_distance = distance
                closest_color = color
        
        if closest_color is None:
            raise ValueError(f"Could not determine closest primary color for RGB({red},{green},{blue})")
        
        return closest_color

    def _parse_viewbox(self, viewbox_string: str) -> Optional[Tuple[float, float, float, float]]:
        """Parse SVG viewBox attribute."""
        if not viewbox_string:
            return None
        
        try:
            coordinates = [float(coord) for coord in viewbox_string.split()]
            return tuple(coordinates) if len(coordinates) == 4 else None
        except ValueError:
            return None
    
    def _get_svg_dimensions(self, root_element: ET.Element) -> Tuple[float, float]:
        """Extract SVG width and height as fallback for scaling."""
        try:
            width_string = root_element.get('width', '100')
            height_string = root_element.get('height', '100')
            
            width = float(re.sub(r'[^\d.]', '', width_string))
            height = float(re.sub(r'[^\d.]', '', height_string))
            return width, height
        except (ValueError, TypeError):
            return 100.0, 100.0
    
    def _scale_to_unit_coordinates(self, point: Point, viewbox: Optional[Tuple[float, float, float, float]], 
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

    def _remove_duplicates_from_all_boundaries(self, boundaries_by_color: Dict[Color, List[RawBoundary]]) -> Dict[Color, List[RawBoundary]]:
        """
        Remove duplicate points from all boundaries after resampling.
        """
        cleaned_boundaries = {}
        
        for color, boundaries in boundaries_by_color.items():
            cleaned_boundaries[color] = []
            for boundary in boundaries:
                if color == Color.RED:
                    # For red dots (single points), no need to remove duplicates
                    cleaned_boundaries[color].append(boundary)
                else:
                    # Remove duplicate points from polyline boundaries
                    no_consecutive_duplicate_points = self._remove_consecutive_duplicate_points(boundary.points)
                    cleaned_points = self._remove_duplicate_end_point(no_consecutive_duplicate_points)
                    cleaned_boundary = RawBoundary(
                        points=cleaned_points,
                        color=boundary.color,
                        is_closed=boundary.is_closed
                    )
                    cleaned_boundaries[color].append(cleaned_boundary)
        
        return cleaned_boundaries

    def _merge_nearby_boundaries(self, boundaries_by_color: Dict[Color, List[RawBoundary]], 
                                distance_threshold: float = 0.02) -> Dict[Color, List[RawBoundary]]:
        """
        Merge boundaries of the same color that are close to each other and not already closed.
        
        Args:
            boundaries_by_color: Dictionary of boundaries grouped by color
            distance_threshold: Maximum distance between endpoints to consider for merging (in unit coordinates)
            
        Returns:
            Dictionary with merged boundaries
        """
        merged_boundaries = {}
        
        for color, boundaries in boundaries_by_color.items():
            if color == Color.RED:
                # Don't merge red dots (they're single points)
                merged_boundaries[color] = boundaries
                continue
            
            # Skip if only one boundary or all boundaries are already closed
            if len(boundaries) <= 1 or all(b.is_closed for b in boundaries):
                merged_boundaries[color] = boundaries
                continue
            
            # Create a list of open boundaries to process
            open_boundaries = [b for b in boundaries if not b.is_closed]
            closed_boundaries = [b for b in boundaries if b.is_closed]
            
            # Try to merge open boundaries
            merged = self._merge_open_boundaries(open_boundaries, distance_threshold)
            
            # Combine merged boundaries with closed ones
            merged_boundaries[color] = closed_boundaries + merged
        
        return merged_boundaries
    
    def _merge_open_boundaries(self, open_boundaries: List[RawBoundary], 
                              distance_threshold: float) -> List[RawBoundary]:
        """
        Merge open boundaries by connecting endpoints that are close together.
        """
        if not open_boundaries:
            return []
        
        merged_boundaries = []
        processed = [False] * len(open_boundaries)
        
        for i, boundary in enumerate(open_boundaries):
            if processed[i]:
                continue
            
            # Start a new merged boundary with this one
            current_points = boundary.points.copy()
            start_point = current_points[0]
            end_point = current_points[-1]
            
            processed[i] = True
            merged_with_something = True
            
            # Keep trying to merge until no more merges are possible
            while merged_with_something:
                merged_with_something = False
                
                for j, other_boundary in enumerate(open_boundaries):
                    if processed[j]:
                        continue
                    
                    other_start = other_boundary.points[0]
                    other_end = other_boundary.points[-1]
                    
                    # Check for possible connections
                    start_to_start = self._distance_between_points(start_point, other_start)
                    start_to_end = self._distance_between_points(start_point, other_end)
                    end_to_start = self._distance_between_points(end_point, other_start)
                    end_to_end = self._distance_between_points(end_point, other_end)
                    
                    min_distance = min(start_to_start, start_to_end, end_to_start, end_to_end)
                    
                    if min_distance <= distance_threshold:
                        # Merge the boundaries
                        if min_distance == start_to_start:
                            # Reverse other boundary and prepend to current
                            other_points_reversed = other_boundary.points[::-1]
                            current_points = other_points_reversed + current_points[1:]
                            start_point = other_end  # After reversal, start becomes end
                        elif min_distance == start_to_end:
                            # Prepend other boundary to current
                            current_points = other_boundary.points[:-1] + current_points
                            start_point = other_start
                        elif min_distance == end_to_start:
                            # Append other boundary to current
                            current_points = current_points[:-1] + other_boundary.points
                            end_point = other_end
                        elif min_distance == end_to_end:
                            # Reverse other boundary and append to current
                            other_points_reversed = other_boundary.points[::-1]
                            current_points = current_points[:-1] + other_points_reversed
                            end_point = other_start  # After reversal, end becomes start
                        
                        processed[j] = True
                        merged_with_something = True
                        break
            
            # Check if the merged boundary is now closed
            is_closed = self._distance_between_points(start_point, end_point) <= distance_threshold
            
            if is_closed:
                # Ensure proper closure
                if self._distance_between_points(current_points[0], current_points[-1]) > distance_threshold:
                    current_points.append(current_points[0])
            
            merged_boundary = RawBoundary(
                points=current_points,
                color=boundary.color,
                is_closed=is_closed
            )
            merged_boundaries.append(merged_boundary)
        
        return merged_boundaries
    
    def _distance_between_points(self, p1: Point, p2: Point) -> float:
        """Calculate Euclidean distance between two points."""
        return math.sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2)