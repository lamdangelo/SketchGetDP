"""
Pure geometric calculations for corner detection.
Stateless utility functions.
"""

import numpy as np
from typing import List
from svg_to_getdp.core.entities.point import Point


class GeometricCalculator:
    """Stateless geometric calculations for corner detection."""
    
    @staticmethod
    def calculate_point_angle(outline_points: List[Point], point_index: int, window_size: int) -> float:
        """
        Calculate the interior angle at a specific outline point.
        
        Uses vectors to previous and next points to compute the angle.
        """
        point_count = len(outline_points)
        
        previous_index = (point_index - window_size) % point_count
        next_index = (point_index + window_size) % point_count
        
        # Vector from previous point to current point
        vector_to_current = np.array([
            outline_points[point_index].x - outline_points[previous_index].x,
            outline_points[point_index].y - outline_points[previous_index].y
        ])
        
        # Vector from current point to next point
        vector_from_current = np.array([
            outline_points[next_index].x - outline_points[point_index].x,
            outline_points[next_index].y - outline_points[point_index].y
        ])
        
        vector_to_current_norm = np.linalg.norm(vector_to_current)
        vector_from_current_norm = np.linalg.norm(vector_from_current)
        
        if vector_to_current_norm > 1e-8 and vector_from_current_norm > 1e-8:
            cosine_angle = np.dot(vector_to_current, vector_from_current) / (vector_to_current_norm * vector_from_current_norm)
            cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
            return np.arccos(cosine_angle)
        
        return 0.0
    
    @staticmethod
    def calculate_local_curvature(
        x_coordinates: np.ndarray, 
        y_coordinates: np.ndarray, 
        point_index: int, 
        window_size: int
    ) -> float:
        """
        Calculate the curvature at a specific point along the outline.
        
        Curvature is defined as the rate of change of direction per unit arc length.
        """
        point_count = len(x_coordinates)
        
        previous_index = (point_index - window_size) % point_count
        next_index = (point_index + window_size) % point_count
        
        # Vectors from previous to current and current to next
        vector_to_current = np.array([
            x_coordinates[point_index] - x_coordinates[previous_index],
            y_coordinates[point_index] - y_coordinates[previous_index]
        ])
        
        vector_from_current = np.array([
            x_coordinates[next_index] - x_coordinates[point_index],
            y_coordinates[next_index] - y_coordinates[point_index]
        ])
        
        vector_to_current_norm = np.linalg.norm(vector_to_current)
        vector_from_current_norm = np.linalg.norm(vector_from_current)
        
        if vector_to_current_norm < 1e-8 or vector_from_current_norm < 1e-8:
            return 0.0
        
        # Calculate angle between vectors
        cosine_angle = np.dot(vector_to_current, vector_from_current) / (vector_to_current_norm * vector_from_current_norm)
        cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
        angle = np.arccos(cosine_angle)
        
        # Calculate average arc length
        arc_length = (vector_to_current_norm + vector_from_current_norm) / 2
        
        return angle / arc_length if arc_length > 0 else 0.0
    
    @staticmethod
    def compute_direction_vector(
        x_coordinates: np.ndarray, 
        y_coordinates: np.ndarray,
        point_index: int, 
        window_size: int, 
        backward: bool
    ) -> np.ndarray:
        """Compute the average direction vector over a window of points."""
        point_count = len(x_coordinates)
        
        if backward:
            start_index = (point_index - window_size) % point_count
            end_index = point_index
        else:
            start_index = point_index
            end_index = (point_index + window_size) % point_count
        
        # Extract coordinates from the window (handling circular outline)
        if start_index < end_index:
            x_window = x_coordinates[start_index:end_index]
            y_window = y_coordinates[start_index:end_index]
        else:
            x_window = np.concatenate([x_coordinates[start_index:], x_coordinates[:end_index]])
            y_window = np.concatenate([y_coordinates[start_index:], y_coordinates[:end_index]])
        
        if len(x_window) < 2:
            return np.array([0.0, 0.0])
        
        # Direction vector from first to last point in the window
        return np.array([
            x_window[-1] - x_window[0],
            y_window[-1] - y_window[0]
        ])
    
    @staticmethod
    def calculate_sampled_curvatures(
        x_coordinates: np.ndarray, 
        y_coordinates: np.ndarray, 
        point_count: int
    ) -> List[float]:
        """Calculate curvatures at regularly sampled points along the outline."""
        sample_step = max(1, point_count // 50)
        curvatures = []
        
        for i in range(0, point_count, sample_step):
            curvature = GeometricCalculator.calculate_local_curvature(x_coordinates, y_coordinates, i, 5)
            curvatures.append(curvature)
        
        return curvatures
    
    @staticmethod
    def calculate_sampled_angles(outline_points: List[Point], point_count: int) -> List[float]:
        """Calculate angles at regularly sampled points along the outline."""
        sample_step = max(1, point_count // 50)
        angles = []
        
        for i in range(0, point_count, sample_step):
            angle = GeometricCalculator.calculate_point_angle(outline_points, i, 7)
            angles.append(angle)
        
        return angles
    
    @staticmethod
    def compute_smoothness_score(angles: List[float], curvatures: List[float]) -> float:
        """Compute a combined smoothness score from angle and curvature statistics."""
        if not angles:
            return 1.0
        
        # Angle-based smoothness: shapes with smaller maximum angles are smoother
        max_angle = max(angles)
        angle_score = 1.0 - min(max_angle / (np.pi * 0.5), 1.0)
        
        # Curvature-based smoothness: shapes with consistent curvature are smoother
        if curvatures:
            curvature_std = np.std(curvatures)
            curvature_mean = np.mean(curvatures)
            
            if curvature_mean > 1e-8:
                curvature_variation = curvature_std / curvature_mean
                curvature_score = 1.0 / (1.0 + curvature_variation)
            else:
                curvature_score = 1.0
        else:
            curvature_score = 1.0
        
        # Weighted combination of angle and curvature smoothness
        return angle_score * 0.6 + curvature_score * 0.4
    