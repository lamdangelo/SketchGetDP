"""
Core use case: Convert SVG to Geometry
"""

from typing import List, Tuple
from ...core.entities.boundary_curve import BoundaryCurve
from ...core.entities.point import Point
from ...core.entities.color import Color
from ...infrastructure.svg_parser import SVGParser, RawBoundary
from ...infrastructure.corner_detector import CornerDetector
from ...infrastructure.bezier_fitter import BezierFitter


class ConvertSVGToGeometry:
    """
    Use case for converting SVG sketches to boundary curves with Bézier representations.
    """
    
    def __init__(self, svg_parser: SVGParser, corner_detector: CornerDetector, bezier_fitter: BezierFitter):
        self.svg_parser = svg_parser
        self.corner_detector = corner_detector
        self.bezier_fitter = bezier_fitter
    
    def execute(self, svg_file_path: str) -> Tuple[List[BoundaryCurve], List[Tuple[Point, Color]]]:
        """
        Convert SVG file to boundary curves with Bézier representations and point electrodes.
        """
        # Step 1: Parse SVG to get raw boundaries grouped by color
        colored_boundaries = self.svg_parser.parse(svg_file_path)
        
        boundary_curves = []
        point_electrodes = []
        
        # Process each color group
        for color, raw_boundaries in colored_boundaries.items():
            for raw_boundary in raw_boundaries:
                if color == Color.RED:
                    # For red elements: treat as point electrodes
                    if len(raw_boundary.points) == 1:
                        point_electrodes.append((raw_boundary.points[0], color))
                    else:
                        center = raw_boundary.points[0]
                        point_electrodes.append((center, color))
                else:
                    # For green/blue elements: process as boundary curves
                    
                    # Step 1: Ensure proper closure for closed curves
                    points = self._ensure_proper_closure(raw_boundary.points, raw_boundary.is_closed)
                    
                    # Step 2: Detect corners in the boundary
                    corners = self.corner_detector.detect_corners(points)
                    
                    # Step 3: Fit piecewise Bézier curves
                    boundary_curve = self.bezier_fitter.fit_boundary_curve(
                        points=points,
                        corners=corners,
                        color=color,
                        is_closed=raw_boundary.is_closed
                    )
                    
                    # Step 4: Ensure closure if needed
                    if raw_boundary.is_closed and boundary_curve.bezier_segments:
                        self._force_curve_closure(boundary_curve)
                    
                    boundary_curves.append(boundary_curve)
        
        return boundary_curves, point_electrodes
    
    def _ensure_proper_closure(self, points: List[Point], is_closed: bool) -> List[Point]:
        """
        Ensure that closed curves properly connect first and last points.
        """
        if not is_closed or len(points) < 3:
            return points
        
        # Check if first and last points are already close
        first_point = points[0]
        last_point = points[-1]
        closure_distance = first_point.distance_to(last_point)
        
        if closure_distance > 1e-6:  # If not properly closed
            # Add first point at the end to close the curve
            return points + [first_point]
        else:
            return points
    
    def _force_curve_closure(self, boundary_curve: BoundaryCurve):
        """
        Force a boundary curve to be properly closed by ensuring first and last control points match.
        """
        if not boundary_curve.bezier_segments:
            return
        
        first_segment = boundary_curve.bezier_segments[0]
        last_segment = boundary_curve.bezier_segments[-1]
        
        if (first_segment.control_points and last_segment.control_points and
            first_segment.control_points[0] != last_segment.control_points[-1]):
            
            # Make last control point of last segment match first control point of first segment
            last_segment.control_points[-1] = first_segment.control_points[0]