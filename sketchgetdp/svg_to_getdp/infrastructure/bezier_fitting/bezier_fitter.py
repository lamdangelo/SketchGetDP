from typing import List
from svg_to_getdp.core.entities.outline import Outline
from svg_to_getdp.core.entities.point import Point
from svg_to_getdp.interfaces.abstractions.bezier_fitter_interface import BezierFitterInterface

from svg_to_getdp.infrastructure.bezier_fitting.segment_classifier import SegmentClassifier
from svg_to_getdp.infrastructure.bezier_fitting.segment_fitter import SegmentFitter
from svg_to_getdp.infrastructure.bezier_fitting.continuity_enforcer import ContinuityEnforcer
from svg_to_getdp.infrastructure.bezier_fitting.bezier_calculator import BezierCalculator


class BezierFitter(BezierFitterInterface):
    """
    Main orchestrator for fitting piecewise Bézier curves to outline points.
    Coordinates the workflow between specialized components.
    """
    
    def __init__(self, bezier_degree: int = 2, minimum_points_per_segment: int = 15):
        self.bezier_degree = bezier_degree
        self.minimum_points_per_segment = minimum_points_per_segment
        
        # Initialize components
        self.segment_classifier = SegmentClassifier()
        self.segment_fitter = SegmentFitter(bezier_degree)
        self.continuity_enforcer = ContinuityEnforcer(bezier_degree)
        self.bezier_calculator = BezierCalculator()
        
    def fit_outline(self, points: List[Point], corner_indices: List[int], 
                    color, is_closed: bool = True) -> Outline:
        """
        Fit piecewise Bézier curves to outline points, treating corners as segment interfaces.
        
        Args:
            points: Raw outline points to fit curves to
            corner_indices: Indices of corner points that should be segment interfaces
            color: Color for the resulting outline
            is_closed: Whether the outline forms a closed loop
            
        Returns:
            Outline with fitted Bézier segments and corner information
            
        Raises:
            ValueError: When insufficient points are provided
        """
        # Step 1: Clean input points
        cleaned_points = self.bezier_calculator.remove_consecutive_duplicate_points(points)
        if len(cleaned_points) < 3:
            raise ValueError(f"Need at least 3 non-duplicate points for outline, got {len(cleaned_points)}")
        
        # Step 2: Calculate optimal segment count
        optimal_segment_count = self.bezier_calculator.calculate_optimal_segment_count(
            cleaned_points, corner_indices, self.minimum_points_per_segment
        )
        
        # Step 3: Fit piecewise Bézier curves
        bezier_segments = self.segment_fitter.fit_piecewise_bezier_curves(
            cleaned_points, 
            corner_indices, 
            optimal_segment_count, 
            is_closed,
            self.segment_classifier,
            self.bezier_calculator
        )
        
        # Step 4: Enforce continuity
        if bezier_segments:
            segment_interfaces = self.bezier_calculator.calculate_segment_interfaces(
                cleaned_points, corner_indices, optimal_segment_count, is_closed
            )
            self.continuity_enforcer.enforce_segment_continuity(
                bezier_segments, segment_interfaces, corner_indices, is_closed
            )
        
        # Step 5: Extract corner points
        corner_points = [cleaned_points[idx] for idx in corner_indices] if corner_indices else []
        
        return Outline(
            bezier_segments=bezier_segments,
            corners=corner_points,
            color=color,
            is_closed=is_closed
        )
        