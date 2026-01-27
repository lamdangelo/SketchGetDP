"""
Multi-method corner candidate detection.
"""

import numpy as np
from typing import List, Dict
from svg_to_getdp.core.entities.point import Point
from svg_to_getdp.infrastructure.corner_detection.geometric_calculator import GeometricCalculator


class CandidateDetector:
    """Detects corner candidates using multiple complementary methods."""
    
    def __init__(
        self,
        window_size: int = 15,
        direction_change_threshold: float = 0.8,
        angle_threshold: float = np.pi / 6,
        corner_strength_threshold: float = 0.45
    ):
        self.window_size = window_size
        self.direction_change_threshold = direction_change_threshold
        self.angle_threshold = angle_threshold
        self.corner_strength_threshold = corner_strength_threshold
    
    def detect_candidate_corners(
        self, 
        outline_points: List[Point], 
        x_coordinates: np.ndarray, 
        y_coordinates: np.ndarray,
        debug_data: Dict
    ) -> List[int]:
        """
        Detect candidate corners using multiple complementary methods.
        
        Combines results from:
        1. Local angle analysis
        2. Direction change detection
        3. Curvature peak analysis
        """
        # Apply each detection method independently
        angle_based_corners = self._detect_corners_by_local_angle(outline_points)
        direction_based_corners = self._detect_corners_by_direction_change(x_coordinates, y_coordinates)
        curvature_based_corners = self._detect_corners_by_curvature_peaks(x_coordinates, y_coordinates)
        
        # Record detection results for debugging
        debug_data['candidate_detection'] = {
            'angle_method': angle_based_corners,
            'direction_method': direction_based_corners,
            'curvature_method': curvature_based_corners,
            'all_candidates': list(set(angle_based_corners + direction_based_corners + curvature_based_corners))
        }
        
        # Calculate strength for all candidates
        all_candidates = debug_data['candidate_detection']['all_candidates']
        candidate_strengths = self._calculate_candidate_strengths(outline_points, all_candidates)
        debug_data['strength_calculations'] = candidate_strengths
        
        # Combine results with method-specific weights
        weighted_candidates = self._combine_candidate_methods(
            angle_based_corners, 
            direction_based_corners, 
            curvature_based_corners, 
            candidate_strengths
        )
        debug_data['candidate_detection']['combined_votes'] = weighted_candidates
        
        # Filter weak candidates based on votes and strength
        strong_candidates = self._filter_weak_candidates(weighted_candidates, candidate_strengths)
        debug_data['candidate_detection']['coarse_corners'] = strong_candidates
        
        return strong_candidates
    
    def _detect_corners_by_local_angle(self, outline_points: List[Point]) -> List[int]:
        """Detect corners by analyzing local interior angles at each point."""
        point_count = len(outline_points)
        if point_count < 10:
            return []
        
        angle_window = max(3, min(10, point_count // 50))
        angle_threshold = self.angle_threshold * 0.8
        
        corners = []
        
        for i in range(point_count):
            angle = GeometricCalculator.calculate_point_angle(outline_points, i, angle_window)
            if angle > angle_threshold:
                corners.append(i)
        
        return corners
    
    def _detect_corners_by_direction_change(
        self, 
        x_coordinates: np.ndarray, 
        y_coordinates: np.ndarray
    ) -> List[int]:
        """Detect corners by analyzing changes in direction along the outline."""
        point_count = len(x_coordinates)
        if point_count < self.window_size * 2:
            return []
        
        corners = []
        
        for i in range(point_count):
            # Compute direction vectors before and after the point
            previous_direction = GeometricCalculator.compute_direction_vector(
                x_coordinates, y_coordinates, i, self.window_size, backward=True
            )
            next_direction = GeometricCalculator.compute_direction_vector(
                x_coordinates, y_coordinates, i, self.window_size, backward=False
            )
            
            previous_direction_norm = np.linalg.norm(previous_direction)
            next_direction_norm = np.linalg.norm(next_direction)
            
            if previous_direction_norm > 1e-8 and next_direction_norm > 1e-8:
                previous_direction_normalized = previous_direction / previous_direction_norm
                next_direction_normalized = next_direction / next_direction_norm
                
                dot_product = np.clip(np.dot(previous_direction_normalized, next_direction_normalized), -1.0, 1.0)
                angle_change = np.arccos(dot_product)
                
                if angle_change > self.direction_change_threshold:
                    corners.append(i)
        
        return corners
    
    def _detect_corners_by_curvature_peaks(
        self, 
        x_coordinates: np.ndarray, 
        y_coordinates: np.ndarray
    ) -> List[int]:
        """Detect corners as local peaks in the curvature profile."""
        point_count = len(x_coordinates)
        if point_count < 20:
            return []
        
        curvature_window = max(3, point_count // 100)
        curvatures = []
        
        # Calculate curvature at each point
        for i in range(point_count):
            curvature = GeometricCalculator.calculate_local_curvature(
                x_coordinates, y_coordinates, i, curvature_window
            )
            curvatures.append(curvature)
        
        # Find local peaks above threshold
        average_curvature = np.mean(curvatures)
        curvature_std = np.std(curvatures)
        curvature_threshold = average_curvature + curvature_std * 1.0
        
        corners = []
        
        for i in range(point_count):
            previous_index = (i - 1) % point_count
            next_index = (i + 1) % point_count
            
            is_local_peak = (
                curvatures[i] > curvatures[previous_index] and 
                curvatures[i] > curvatures[next_index] and
                curvatures[i] > curvature_threshold
            )
            
            if is_local_peak:
                corners.append(i)
        
        return corners
    
    def _calculate_corner_strength(self, outline_points: List[Point], point_index: int) -> float:
        """
        Calculate a strength score (0-1) for a potential corner.
        
        Combines:
        1. Interior angle (larger angles are stronger corners)
        2. Local curvature contrast (corners should stand out from neighbors)
        """
        point_count = len(outline_points)
        
        # Angle component: corners have larger interior angles
        angle = GeometricCalculator.calculate_point_angle(outline_points, point_index, 7)
        angle_score = min(angle / (np.pi * 0.8), 1.0)
        
        # Curvature contrast component: corners should have higher curvature than neighbors
        x_coordinates = np.array([point.x for point in outline_points])
        y_coordinates = np.array([point.y for point in outline_points])
        
        local_curvature = GeometricCalculator.calculate_local_curvature(
            x_coordinates, y_coordinates, point_index, 5
        )
        
        # Compare with neighboring curvatures
        neighbor_window = min(10, point_count // 20)
        neighbor_curvatures = []
        
        for offset in range(-neighbor_window, neighbor_window + 1):
            if offset != 0:
                neighbor_index = (point_index + offset) % point_count
                curvature = GeometricCalculator.calculate_local_curvature(
                    x_coordinates, y_coordinates, neighbor_index, 5
                )
                neighbor_curvatures.append(curvature)
        
        if neighbor_curvatures:
            average_neighbor_curvature = np.mean(neighbor_curvatures)
            if average_neighbor_curvature > 1e-8:
                curvature_contrast = local_curvature / average_neighbor_curvature
                contrast_score = min(curvature_contrast / 3.0, 1.0)
            else:
                contrast_score = 1.0
        else:
            contrast_score = 0.5
        
        # Weighted combination: angle is more important than contrast
        return angle_score * 0.7 + contrast_score * 0.3
    
    def _calculate_candidate_strengths(
        self, 
        outline_points: List[Point], 
        candidate_indices: List[int]
    ) -> Dict[int, float]:
        """Calculate strength scores for multiple candidate corners."""
        return {
            idx: self._calculate_corner_strength(outline_points, idx)
            for idx in candidate_indices
        }
    
    def _combine_candidate_methods(
        self,
        angle_corners: List[int],
        direction_corners: List[int],
        curvature_corners: List[int],
        candidate_strengths: Dict[int, float]
    ) -> Dict[int, float]:
        """Combine results from multiple detection methods with weights."""
        weighted_candidates = {}
        
        # Method weights reflect confidence in each detection approach
        method_weights = {
            'angle': 1.0,      # Most reliable for clear corners
            'direction': 0.8,  # Good for gradual direction changes
            'curvature': 0.6   # Sensitive to local shape changes
        }
        
        # Add candidates from each method with their respective weights
        for idx in angle_corners:
            if candidate_strengths.get(idx, 0) >= self.corner_strength_threshold * 0.5:
                weighted_candidates[idx] = weighted_candidates.get(idx, 0) + method_weights['angle']
        
        for idx in direction_corners:
            if candidate_strengths.get(idx, 0) >= self.corner_strength_threshold * 0.5:
                weighted_candidates[idx] = weighted_candidates.get(idx, 0) + method_weights['direction']
        
        for idx in curvature_corners:
            if candidate_strengths.get(idx, 0) >= self.corner_strength_threshold * 0.5:
                weighted_candidates[idx] = weighted_candidates.get(idx, 0) + method_weights['curvature']
        
        return weighted_candidates
    
    def _filter_weak_candidates(
        self, 
        weighted_candidates: Dict[int, float], 
        candidate_strengths: Dict[int, float]
    ) -> List[int]:
        """Filter out candidates with insufficient votes or low strength."""
        minimum_votes = 1.0
        strong_candidates = []
        
        for idx, votes in weighted_candidates.items():
            strength = candidate_strengths.get(idx, 0)
            if votes >= minimum_votes and strength >= self.corner_strength_threshold:
                strong_candidates.append(idx)
        
        return strong_candidates
    