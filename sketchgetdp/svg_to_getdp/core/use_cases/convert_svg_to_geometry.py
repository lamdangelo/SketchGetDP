"""
Core use case: Convert SVG to Geometry
"""

from typing import List, Tuple
from svg_to_getdp.core.entities.outline import Outline
from svg_to_getdp.core.entities.point import Point
from svg_to_getdp.core.entities.color import Color

class ConvertSVGToGeometry:
    """
    Use case for converting SVG sketches to outlines with Bézier representations.
    """
    
    def __init__(self):
        """
        Initialize the converter using factories internally.
        """
        from svg_to_getdp.infrastructure.factories.svg_parser_factory import SvgParserFactory
        from svg_to_getdp.infrastructure.factories.corner_detector_factory import CornerDetectorFactory
        from svg_to_getdp.infrastructure.factories.bezier_fitter_factory import BezierFitterFactory
        
        self.svg_parser = SvgParserFactory.create_default()
        self.corner_detector = CornerDetectorFactory.create_default()
        self.bezier_fitter = BezierFitterFactory.create_default()
    
    def execute(self, svg_file_path: str) -> Tuple[List[Outline], List[Tuple[Point, Color]], dict, dict]:
        """
        Convert SVG file to outlines with Bézier representations and wires.
        Returns: (outlines, wires, colored_raw_outlines, corner_debug_data)
        """
        # Step 1: Parse SVG to get raw outlines grouped by color
        colored_raw_outlines = self.svg_parser.extract_raw_outlines_by_color(svg_file_path)
        
        outlines = []
        wires = []
        corner_debug_data = {}
        
        # Process each color group
        for color, raw_outlines in colored_raw_outlines.items():
            for outline_idx, raw_outline in enumerate(raw_outlines):
                if color == Color.RED:
                    # For red elements: treat as wires
                    if len(raw_outline.points) == 1:
                        wires.append((raw_outline.points[0], color))
                    else:
                        center = raw_outline.points[0]
                        wires.append((center, color))
                else:
                    # For green/blue elements: process as outlines
                    
                    # Step 1: Ensure proper closure for closed outlines
                    points = self._ensure_proper_closure(raw_outline.points, raw_outline.is_closed)
                    
                    # Step 2: Detect corners in the outline with debug data
                    corner_indices, raw_outline_debug = self.corner_detector.detect_corners(points)
                    
                    # Store debug data with unique key
                    key = f"{color.name}_raw_outline_{outline_idx}"
                    corner_debug_data[key] = {
                        'color': color.name,
                        'outline_index': outline_idx,
                        'points_count': len(points),
                        'is_closed': raw_outline.is_closed,
                        'corner_indices': corner_indices,
                        'debug': raw_outline_debug
                    }
                    
                    # Step 3: Fit piecewise Bézier curves
                    outline = self.bezier_fitter.fit_outline(
                        points=points,
                        corner_indices=corner_indices,
                        color=color,
                        is_closed=raw_outline.is_closed
                    )
                    
                    # Step 4: Ensure closure if needed
                    if outline.is_closed and outline.bezier_segments:
                        self._force_outline_closure(outline)
                    
                    outlines.append(outline)
        
        return outlines, wires, colored_raw_outlines, corner_debug_data
    
    def _ensure_proper_closure(self, points: List[Point], is_closed: bool) -> List[Point]:
        """
        Ensure that closed outlines properly connect first and last points.
        """
        if not is_closed or len(points) < 3:
            return points
        
        # Check if first and last points are already close
        first_point = points[0]
        last_point = points[-1]
        closure_distance = first_point.distance_to(last_point)
        
        if closure_distance > 1e-6:  # If not properly closed
            # Add first point at the end to close the outline
            return points + [first_point]
        else:
            return points
    
    def _force_outline_closure(self, outline: Outline):
        """
        Force an outline to be properly closed by ensuring first and last control points match.
        """
        if not outline.bezier_segments:
            return
        
        first_segment = outline.bezier_segments[0]
        last_segment = outline.bezier_segments[-1]
        
        if (first_segment.control_points and last_segment.control_points and
            first_segment.control_points[0] != last_segment.control_points[-1]):
            
            # Make last control point of last segment match first control point of first segment
            last_segment.control_points[-1] = first_segment.control_points[0]
            