"""
Core use case: Convert SVG to Geometry
"""

from typing import List
from core.entities.boundary_curve import BoundaryCurve
from infrastructure.svg_parser import SVGParser, RawBoundary
from infrastructure.corner_detector import CornerDetector
from infrastructure.bezier_fitter import BezierFitter


class ConvertSVGToGeometry:
    """
    Use case for converting SVG sketches to boundary curves with Bézier representations.
    
    This implements the following workflow:
    1. Parse SVG to extract colored boundaries as point sets
    2. Detect corners in each boundary
    3. Fit piecewise Bézier curves to each boundary
    4. Return BoundaryCurve objects ready for simulation
    
    The use case follows the dependency inversion principle by accepting
    infrastructure services as dependencies.
    """
    
    def __init__(self, svg_parser: SVGParser, corner_detector: CornerDetector, bezier_fitter: BezierFitter):
        """
        Initialize the use case with required infrastructure services.
        
        Args:
            svg_parser: Service for parsing SVG files
            corner_detector: Service for detecting corners in boundary curves
            bezier_fitter: Service for fitting Bézier curves to boundary points
        """
        self.svg_parser = svg_parser
        self.corner_detector = corner_detector
        self.bezier_fitter = bezier_fitter
    
    def execute(self, svg_file_path: str) -> List[BoundaryCurve]:
        """
        Convert SVG file to boundary curves with Bézier representations.
        
        Args:
            svg_file_path: Path to the SVG file to convert
            
        Returns:
            List of BoundaryCurve objects representing the geometry
            
        Raises:
            ValueError: If the SVG file cannot be parsed or is invalid
        """
        # Step 1: Parse SVG to get raw boundaries grouped by color
        colored_boundaries = self.svg_parser.parse(svg_file_path)
        
        boundary_curves = []
        
        # Process each color group
        for color, raw_boundaries in colored_boundaries.items():
            for raw_boundary in raw_boundaries:
                # Step 2: Detect corners in the boundary
                corners = self.corner_detector.detect_corners(raw_boundary.points)
                
                # Step 3: Fit piecewise Bézier curves
                boundary_curve = self.bezier_fitter.fit_boundary_curve(
                    points=raw_boundary.points,
                    corners=corners,
                    color=color,
                    is_closed=raw_boundary.is_closed
                )
                
                boundary_curves.append(boundary_curve)
        
        return boundary_curves