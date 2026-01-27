"""
Main corner detector orchestrator implementing the CornerDetectorInterface.
"""

import numpy as np
from typing import List, Tuple, Dict
from svg_to_getdp.core.entities.point import Point
from svg_to_getdp.interfaces.abstractions.corner_detector_interface import CornerDetectorInterface

from svg_to_getdp.infrastructure.corner_detection.smooth_shape_detector import SmoothShapeDetector
from svg_to_getdp.infrastructure.corner_detection.candidate_detector import CandidateDetector
from svg_to_getdp.infrastructure.corner_detection.candidate_refiner import CandidateRefiner
from svg_to_getdp.infrastructure.corner_detection.debug_recorder import DebugRecorder


class CornerDetector(CornerDetectorInterface):
    """
    Corner detector with handling for complex shapes like crosses.
    Returns structured debug data along with corner indices.
    
    The detector uses multiple complementary methods to identify corners:
    1. Local angle analysis
    2. Direction change detection
    3. Curvature peak analysis
    
    Results are combined, clustered, refined, and filtered to produce final corner points.
    """
    
    def __init__(
        self, 
        window_size: int = 15, 
        direction_change_threshold: float = 0.8, 
        angle_threshold: float = np.pi / 6,
        minimum_corner_distance: int = 5,
        smoothness_threshold: float = 0.72,
        corner_strength_threshold: float = 0.45,
        ellipse_aspect_ratio_threshold: float = 1.2,
        debug_enabled: bool = True
    ):
        """
        Initialize the corner detector with configurable parameters.
        
        Args:
            window_size: Size of the analysis window for direction vectors
            direction_change_threshold: Minimum angle change (radians) to consider a direction change
            angle_threshold: Minimum interior angle (radians) to qualify as a corner
            minimum_corner_distance: Minimum distance between detected corners (pixels)
            smoothness_threshold: Threshold for detecting smooth/elliptical shapes
            corner_strength_threshold: Minimum strength score for a valid corner
            ellipse_aspect_ratio_threshold: Maximum aspect ratio for ellipse detection
            debug_enabled: Whether to collect and return debug information
        """
        self.window_size = window_size
        self.direction_change_threshold = direction_change_threshold
        self.angle_threshold = angle_threshold
        self.minimum_corner_distance = minimum_corner_distance
        self.smoothness_threshold = smoothness_threshold
        self.corner_strength_threshold = corner_strength_threshold
        self.ellipse_aspect_ratio_threshold = ellipse_aspect_ratio_threshold
        self.debug_enabled = debug_enabled
        
        # Initialize components
        self.debug_recorder = DebugRecorder(debug_enabled)
        self.smooth_shape_detector = SmoothShapeDetector(
            smoothness_threshold=smoothness_threshold,
            ellipse_aspect_ratio_threshold=ellipse_aspect_ratio_threshold,
            window_size=window_size
        )
        self.candidate_detector = CandidateDetector(
            window_size=window_size,
            direction_change_threshold=direction_change_threshold,
            angle_threshold=angle_threshold,
            corner_strength_threshold=corner_strength_threshold
        )
        self.candidate_refiner = CandidateRefiner(
            minimum_corner_distance=minimum_corner_distance,
            corner_strength_threshold=corner_strength_threshold,
            angle_threshold=angle_threshold
        )
    
    def detect_corners(self, outline_points: List[Point]) -> Tuple[List[int], Dict]:
        """
        Identifies indices of corner points in the outline point sequence.
        
        The detection process involves:
        1. Early shape analysis (ellipse/smooth shape detection)
        2. Candidate detection using multiple methods
        3. Strength calculation for each candidate
        4. Clustering of nearby candidates
        5. Refinement of corner positions
        6. Final filtering and spacing enforcement
        
        Args:
            outline_points: List of ordered points representing a closed outline
            
        Returns:
            Tuple containing:
                - List of corner indices in the outline_points list
                - Dictionary containing debug information if debug_enabled is True
        """
        debug_data = self.debug_recorder.initialize_debug_data()
        self.debug_recorder.record_debug_step(debug_data, f"Starting corner detection for {len(outline_points)} outline points")
        
        # Early return for shapes that are likely ellipses or too smooth
        if self.smooth_shape_detector.should_skip_corner_detection(outline_points, debug_data):
            self.debug_recorder.record_debug_step(debug_data, "Shape is ellipse or too smooth: returning no corners")
            return [], debug_data
        
        # Convert points to coordinate arrays for efficient computation
        x_coordinates = np.array([point.x for point in outline_points])
        y_coordinates = np.array([point.y for point in outline_points])
        
        self.debug_recorder.record_bounding_box_info(x_coordinates, y_coordinates, debug_data)
        
        # Step 1: Detect candidate corners using multiple complementary methods
        candidate_corners = self.candidate_detector.detect_candidate_corners(
            outline_points, x_coordinates, y_coordinates, debug_data
        )
        
        self.debug_recorder.record_debug_step(debug_data, f"Angle method found {len(debug_data['candidate_detection']['angle_method'])} corners")
        self.debug_recorder.record_debug_step(debug_data, f"Direction method found {len(debug_data['candidate_detection']['direction_method'])} corners")
        self.debug_recorder.record_debug_step(debug_data, f"Curvature method found {len(debug_data['candidate_detection']['curvature_method'])} corners")
        self.debug_recorder.record_debug_step(debug_data, f"After filtering: {len(candidate_corners)} strong candidates")
        
        if not candidate_corners:
            self.debug_recorder.record_debug_step(debug_data, "No strong corners found: returning empty list")
            return [], debug_data
        
        # Step 2: Cluster nearby candidates to avoid duplicates
        clustered_corners = self.candidate_refiner.cluster_nearby_candidates(
            outline_points, candidate_corners, debug_data
        )
        
        self.debug_recorder.record_debug_step(debug_data, f"Clustering created {len(clustered_corners)} candidate clusters")
        
        # Step 3: Refine corner positions within each cluster
        refined_corners = self.candidate_refiner.refine_corner_positions(
            outline_points, clustered_corners, debug_data
        )
        
        # Step 4: Filter corners by strength
        strong_corners = self.candidate_refiner.filter_corners_by_strength(outline_points, refined_corners)
        
        # Step 5: Ensure minimum spacing between corners
        final_corners = self.candidate_refiner.enforce_minimum_corner_spacing(
            outline_points, strong_corners, debug_data
        )
        
        # Record final results
        candidate_strengths = self.candidate_detector._calculate_candidate_strengths(outline_points, final_corners)
        self.debug_recorder.record_final_results(outline_points, final_corners, debug_data, candidate_strengths)
        
        self.debug_recorder.record_debug_step(debug_data, f"Final result: {len(final_corners)} corners detected")
        
        return sorted(final_corners), debug_data
    