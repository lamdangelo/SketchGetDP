"""
Main SVG Parser orchestrator that coordinates the parsing pipeline.
Implements the SVGParserInterface and delegates to specialized processors.
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple

from svgpathtools import svg2paths, Path

from svg_to_getdp.core.entities.point import Point
from svg_to_getdp.core.entities.color import Color
from svg_to_getdp.core.entities.raw_outline import RawOutline
from svg_to_getdp.interfaces.abstractions.svg_parser_interface import SVGParserInterface

from svg_to_getdp.infrastructure.svg_processing.raw_outline_assembler import RawOutline
from svg_to_getdp.infrastructure.svg_processing.svg_color_classifier import SvgColorClassifier
from svg_to_getdp.infrastructure.svg_processing.svg_transform_applier import SvgTransformApplier
from svg_to_getdp.infrastructure.svg_processing.svg_path_refiner import SvgPathRefiner
from svg_to_getdp.infrastructure.svg_processing.svg_coordinate_converter import SvgCoordinateConverter


class SvgParser(SVGParserInterface):
    """
    Main SVG parser that orchestrates the parsing pipeline.
    Delegates specific responsibilities to specialized processors.
    """
    
    def __init__(self, samples_per_segment: int = 20, points_per_unit_length: int = 1000):
        self.namespace = '{http://www.w3.org/2000/svg}'
        self.samples_per_segment = samples_per_segment
        self.points_per_unit_length = points_per_unit_length
        
        # Initialize specialized processors
        self.color_classifier = SvgColorClassifier()
        self.transform_applier = SvgTransformApplier()
        self.path_refiner = SvgPathRefiner(points_per_unit_length)
        self.coordinate_converter = SvgCoordinateConverter()
    
    def extract_raw_outlines_by_color(self, svg_file_path: str) -> Dict[Color, List[RawOutline]]:
        """
        Parse SVG file and extract raw_outlines grouped by color.
        
        Strategy:
        1. Use svg2paths for all non-red paths (green, blue, black)
        2. Parse circle/ellipse elements directly from XML for red structures
        """
        try:
            # Parse the XML tree to access all elements
            tree = ET.parse(svg_file_path)
            root = tree.getroot()
            
            # Parse paths with svgpathtools
            paths, attributes = svg2paths(svg_file_path)
            
        except Exception as e:
            raise ValueError(f"Invalid SVG file: {e}")
        
        viewbox = self._parse_viewbox(root.get('viewBox'))
        svg_width, svg_height = self._get_svg_dimensions(root)
        
        # Parse paths from svgpathtools
        # Skip red paths here - handled separately
        path_raw_outlines = self._convert_paths_to_raw_outlines(
            paths, attributes, viewbox, svg_width, svg_height
        )
        
        red_dots_raw_outlines = self._extract_red_dots_from_xml(
            root, viewbox, svg_width, svg_height
        )
        
        # Merge both results - path raw_outlines (green, blue, black) and red dots
        raw_outlines_by_color = self._merge_raw_outlines(path_raw_outlines, red_dots_raw_outlines)
        
        # Apply post-processing resampling to ensure even point distribution
        resampled_raw_outlines = self.path_refiner.resample_all_raw_outlines(raw_outlines_by_color)
        
        # Remove duplicate points from all raw_outlines after resampling
        clean_raw_outlines = self.path_refiner.remove_duplicates_from_all_raw_outlines(resampled_raw_outlines)
        
        # Merge nearby raw_outlines of the same color
        merged_raw_outlines = self.path_refiner.merge_nearby_raw_outlines(
            clean_raw_outlines, distance_threshold=0.02
        )
        
        return merged_raw_outlines
    
    def _convert_paths_to_raw_outlines(self, paths: List[Path], attributes: List[dict],
                                viewbox: Optional[Tuple[float, float, float, float]],
                                svg_width: float, svg_height: float) -> Dict[Color, List[RawOutline]]:
        """
        Convert all SVG paths to raw_outline objects grouped by color. Red paths are skipped here.
        """
        raw_outlines_by_color = {}
        
        for path_index, (path, attr) in enumerate(zip(paths, attributes)):
            try:
                color = self.color_classifier.extract_color_from_attributes(attr)
                
                # SKIP RED PATHS - these are typically converted circles/ellipses
                # that we'll handle separately via XML parsing for more flexibility
                if color == Color.RED:
                    continue
                    
                # Convert path to points
                points = self._convert_path_to_points(path, viewbox, svg_width, svg_height)
                
                if not points:
                    raise ValueError("Path contains no valid points")
                
                # Check if path is closed
                is_closed = self._is_path_closed(path)
                
                # Create RawOutline using the assembler (to be implemented separately)
                raw_outline = RawOutline(
                    points=points,
                    color=color,
                    is_closed=is_closed
                )
                
                if raw_outline.color not in raw_outlines_by_color:
                    raw_outlines_by_color[raw_outline.color] = []
                raw_outlines_by_color[raw_outline.color].append(raw_outline)
                
            except Exception as e:
                print(f"WARNING: Failed to process path {path_index}: {e}")
                continue
        
        return raw_outlines_by_color
    
    def _extract_red_dots_from_xml(self, root: ET.Element,
                                   viewbox: Optional[Tuple[float, float, float, float]],
                                   svg_width: float, svg_height: float) -> Dict[Color, List[RawOutline]]:
        """
        Extract red dots (circles and ellipses) directly from XML.
        """
        red_dots_raw_outlines = {}
        
        # Find all circle and ellipse elements
        for element_name in ['circle', 'ellipse']:
            for elem in root.iter(f'{self.namespace}{element_name}'):
                try:
                    color = self._extract_color_from_xml_element(elem)
                    
                    # Only process red circles/ellipses - skip other colors
                    if color != Color.RED:
                        continue
                    
                    # Get center coordinates
                    cx = float(elem.get('cx', '0'))
                    cy = float(elem.get('cy', '0'))
                    
                    # Apply transform if present
                    transform = elem.get('transform', '')
                    if transform:
                        transformed_point = self.transform_applier.apply_transform_to_point(cx, cy, transform)
                        cx, cy = transformed_point
                    
                    # Scale to unit coordinates
                    point = Point(cx, cy)
                    scaled_point = self.coordinate_converter.scale_to_unit_coordinates(
                        point, viewbox, svg_width, svg_height
                    )
                    
                    # For red dots, we just want the center point
                    raw_outline = RawOutline(
                        points=[scaled_point],
                        color=color,
                        is_closed=True
                    )
                    
                    if color not in red_dots_raw_outlines:
                        red_dots_raw_outlines[color] = []
                    red_dots_raw_outlines[color].append(raw_outline)
                    
                except Exception as e:
                    print(f"WARNING: Failed to process {element_name} element: {e}")
                    continue
        
        return red_dots_raw_outlines
    
    def _extract_color_from_xml_element(self, elem: ET.Element) -> Color:
        """
        Extract color from XML element attributes.
        """
        # Get color from multiple possible attributes
        style = elem.get('style', '')
        stroke = elem.get('stroke', '')
        fill = elem.get('fill', '')
        
        color = None
        
        # Try to extract color from different sources
        # Priority: stroke attribute -> fill attribute -> style attribute
        if stroke and stroke != 'none':
            color = self.color_classifier.parse_color_string(stroke)
        elif fill and fill != 'none':
            color = self.color_classifier.parse_color_string(fill)
        elif style:
            color = self.color_classifier.extract_color_from_style(style)
        
        if not color:
            raise ValueError(f"No valid color found for element")
        
        return color
    
    def _convert_path_to_points(self, path: Path, viewbox: Optional[Tuple[float, float, float, float]],
                              svg_width: float, svg_height: float) -> List[Point]:
        """
        Convert svgpathtools Path object to list of scaled points.
        """
        points = []
        
        for segment in path:
            segment_points = self._sample_segment_points(segment, self.samples_per_segment)
            points.extend(segment_points)
        
        points = self.path_refiner.remove_consecutive_duplicate_points(points)
        return [
            self.coordinate_converter.scale_to_unit_coordinates(p, viewbox, svg_width, svg_height) 
            for p in points
        ]
    
    def _sample_segment_points(self, segment, samples_per_segment: int) -> List[Point]:
        """
        Sample multiple points from a path segment.
        """
        from svgpathtools import Line, CubicBezier, QuadraticBezier, Arc
        
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
    
    def _merge_raw_outlines(self, raw_outlines1: Dict[Color, List[RawOutline]], 
                        raw_outlines2: Dict[Color, List[RawOutline]]) -> Dict[Color, List[RawOutline]]:
        """
        Merge two dictionaries of raw_outlines.
        """
        merged = {}
        all_colors = set(raw_outlines1.keys()) | set(raw_outlines2.keys())
        
        for color in all_colors:
            merged[color] = []
            if color in raw_outlines1:
                merged[color].extend(raw_outlines1[color])
            if color in raw_outlines2:
                merged[color].extend(raw_outlines2[color])
        
        return merged
    
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
        import re
        
        try:
            width_string = root_element.get('width', '100')
            height_string = root_element.get('height', '100')
            
            width = float(re.sub(r'[^\d.]', '', width_string))
            height = float(re.sub(r'[^\d.]', '', height_string))
            return width, height
        except (ValueError, TypeError):
            return 100.0, 100.0
        