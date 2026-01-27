"""
Detection of ellipses and smooth shapes to skip unnecessary corner detection.
"""

import numpy as np
from typing import List, Tuple, Dict
from svg_to_getdp.core.entities.point import Point
from svg_to_getdp.infrastructure.corner_detection.geometric_calculator import GeometricCalculator


class SmoothShapeDetector:
    """Detects ellipses and smooth shapes to avoid unnecessary corner detection."""
    
    def __init__(
        self,
        smoothness_threshold: float = 0.72,
        ellipse_aspect_ratio_threshold: float = 1.2,
        window_size: int = 15
    ):
        self.smoothness_threshold = smoothness_threshold
        self.ellipse_aspect_ratio_threshold = ellipse_aspect_ratio_threshold
        self.window_size = window_size
    
    def should_skip_corner_detection(self, outline_points: List[Point], debug_data: Dict) -> bool:
        """
        Check if the shape is likely an ellipse or too smooth for corner detection.
        
        Returns True if corner detection should be skipped for this shape.
        """
        point_count = len(outline_points)
        
        # Early ellipse detection for small shapes
        if point_count < 100 and self._is_likely_small_ellipse(outline_points):
            debug_data['shape_analysis']['early_ellipse_detection'] = True
            debug_data['shape_analysis']['ellipse_reason'] = "Small shape with ellipse-like properties"
            return True
        
        # Smoothness check for larger shapes
        if point_count > 30:
            smoothness_score, is_ellipse = self.calculate_shape_smoothness(outline_points)
            
            debug_data['shape_analysis']['smoothness_score'] = smoothness_score
            debug_data['shape_analysis']['is_ellipse'] = is_ellipse
            
            if is_ellipse:
                debug_data['shape_analysis']['ellipse_reason'] = "Smoothness detection"
                return True
            
            if smoothness_score > self.smoothness_threshold:
                debug_data['shape_analysis']['too_smooth'] = True
                return True
        
        # Check if shape is too small for reliable corner detection
        if point_count < self.window_size * 2:
            debug_data['shape_analysis']['too_small'] = True
            return True
        
        return False
    
    def calculate_shape_smoothness(self, outline_points: List[Point]) -> Tuple[float, bool]:
        """
        Calculate a smoothness score for the shape and detect if it's ellipse-like.
        
        Returns:
            Tuple containing:
                - Smoothness score (higher = smoother)
                - Boolean indicating if shape is likely an ellipse
        """
        point_count = len(outline_points)
        x_coordinates = np.array([point.x for point in outline_points])
        y_coordinates = np.array([point.y for point in outline_points])
        
        # Calculate curvatures at sample points
        curvatures = GeometricCalculator.calculate_sampled_curvatures(x_coordinates, y_coordinates, point_count)
        
        # Check if shape is ellipse-like
        is_ellipse = self._is_shape_ellipse_like(outline_points, curvatures)
        
        # Calculate angles at sample points
        angles = GeometricCalculator.calculate_sampled_angles(outline_points, point_count)
        
        # Compute smoothness score from angle and curvature statistics
        smoothness_score = GeometricCalculator.compute_smoothness_score(angles, curvatures)
        
        return smoothness_score, is_ellipse
    
    def _is_shape_ellipse_like(self, outline_points: List[Point], curvatures: List[float]) -> bool:
        """Determine if the shape is likely an ellipse based on curvature consistency."""
        point_count = len(outline_points)
        
        # Large shapes are less likely to be simple ellipses
        if point_count > 200:
            return False
        
        # Check curvature consistency
        if curvatures:
            curvature_std = np.std(curvatures)
            curvature_mean = np.mean(curvatures)
            
            if curvature_mean > 1e-8:
                coefficient_of_variation = curvature_std / curvature_mean
                if coefficient_of_variation < 0.3:
                    return True
        
        # Check distance to center consistency
        x_coordinates = np.array([point.x for point in outline_points])
        y_coordinates = np.array([point.y for point in outline_points])

        center_x = np.mean(x_coordinates)
        center_y = np.mean(y_coordinates)
        
        distances = np.sqrt((x_coordinates - center_x)**2 + (y_coordinates - center_y)**2)
        distance_mean = np.mean(distances)
        
        if distance_mean > 0:
            distance_variation = np.std(distances) / distance_mean
            if distance_variation < 0.2:
                return True
        
        return False
    
    def _is_likely_small_ellipse(self, outline_points: List[Point]) -> bool:
        """Check if a small shape is likely an ellipse."""
        point_count = len(outline_points)

        if point_count < 10:
            return False
        
        x_coordinates = np.array([point.x for point in outline_points])
        y_coordinates = np.array([point.y for point in outline_points])
        
        width = np.max(x_coordinates) - np.min(x_coordinates)
        height = np.max(y_coordinates) - np.min(y_coordinates)
        
        # Check curvature consistency
        curvatures = []
        sample_step = max(1, point_count // 20)
        for i in range(0, point_count, sample_step):
            curvature = GeometricCalculator.calculate_local_curvature(x_coordinates, y_coordinates, i, 3)
            curvatures.append(curvature)
        
        if curvatures:
            curvature_std = np.std(curvatures)
            curvature_mean = np.mean(curvatures)
            if curvature_mean > 1e-8:
                coefficient_of_variation = curvature_std / curvature_mean
                if coefficient_of_variation < 0.25:
                    return True
        
        # Check aspect ratio and closure
        if width > 0 and height > 0:
            aspect_ratio = max(width, height) / min(width, height)
            if aspect_ratio < self.ellipse_aspect_ratio_threshold:
                start_end_distance = np.sqrt(
                    (x_coordinates[0] - x_coordinates[-1])**2 + 
                    (y_coordinates[0] - y_coordinates[-1])**2
                )
                if start_end_distance < min(width, height) * 0.1:
                    return True
        
        return False
    