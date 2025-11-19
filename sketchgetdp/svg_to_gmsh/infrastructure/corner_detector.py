import numpy as np
from typing import List
from ..core.entities.point import Point


class CornerDetector:
    """
    Identifies corner points in boundary point sequences by analyzing changes
    in direction vectors across sliding windows, then refines them locally
    using angle-based detection.
    """
    
    def __init__(self, window_size: int = 20, direction_change_threshold: float = 1.0, angle_threshold: float = np.pi/4):
        self.window_size = window_size
        self.direction_change_threshold = direction_change_threshold
        self.angle_threshold = angle_threshold
    
    def detect_corners(self, boundary_points: List[Point]) -> List[int]:
        """
        Identifies indices of corner points in the boundary point sequence.
        """
        if len(boundary_points) < self.window_size * 2:
            return []
        
        x_coordinates = np.array([point.x for point in boundary_points])
        y_coordinates = np.array([point.y for point in boundary_points])
        
        window_directions = self._calculate_window_directions(x_coordinates, y_coordinates)
        
        if len(window_directions) < 2:
            return []
        
        # Step 1: coarse detection
        coarse_corner_indices = self._find_corner_indices(window_directions, len(boundary_points))
        
        # Step 2: refine locally using *both* adjacent windows
        refined_corner_indices = []
        for coarse_index in coarse_corner_indices:
            # refine at coarse_index
            refined_index = self._refine_corner(boundary_points, coarse_index, self.window_size)
            if refined_index is not None:
                refined_corner_indices.append(refined_index)
            
        return sorted(set(refined_corner_indices))
    
    def _calculate_window_directions(self, x_coordinates: np.ndarray, y_coordinates: np.ndarray) -> List[np.ndarray]:
        """Calculates normalized direction vectors for each sliding window."""
        total_windows = len(x_coordinates) // self.window_size
        window_directions = []
        
        for window_index in range(total_windows):
            window_start = window_index * self.window_size
            window_end = window_start + self.window_size
            
            if window_end >= len(x_coordinates):
                continue
                
            direction_vector = self._compute_window_direction(
                x_coordinates, y_coordinates, window_start, window_end
            )
            window_directions.append(direction_vector)
        
        return window_directions
    
    def _compute_window_direction(self, x_coordinates: np.ndarray, y_coordinates: np.ndarray, 
                                start_index: int, end_index: int) -> np.ndarray:
        """Computes the average direction vector for a specific window of points."""
        vector_sum_x = 0.0
        vector_sum_y = 0.0
        
        for point_index in range(start_index, end_index - 1):
            delta_x = x_coordinates[point_index + 1] - x_coordinates[point_index]
            delta_y = y_coordinates[point_index + 1] - y_coordinates[point_index]
            
            vector_sum_x += delta_x
            vector_sum_y += delta_y
        
        direction_vector = np.array([vector_sum_x, vector_sum_y])
        vector_magnitude = np.linalg.norm(direction_vector)
        
        if vector_magnitude > 1e-10:
            return direction_vector / vector_magnitude
        else:
            return np.array([0.0, 0.0])
    
    def _find_corner_indices(self, window_directions: List[np.ndarray], total_points: int) -> List[int]:
        """Identifies corner indices by detecting significant direction changes between windows."""
        corner_indices = []
        
        # Check direction changes between consecutive windows
        for window_index in range(len(window_directions) - 1):
            direction_change = window_directions[window_index] - window_directions[window_index + 1]
            change_magnitude = np.linalg.norm(direction_change)
            
            if change_magnitude > self.direction_change_threshold:
                corner_index = window_index * self.window_size + self.window_size // 2
                corner_indices.append(corner_index)
        
        # Check for closure in circular boundaries (last window to first window)
        if len(window_directions) >= 2:
            closure_direction_change = window_directions[-1] - window_directions[0]
            closure_change_magnitude = np.linalg.norm(closure_direction_change)
            
            if closure_change_magnitude > self.direction_change_threshold:
                closure_corner_index = 0
                corner_indices.append(closure_corner_index)
        
        return corner_indices
    
    def _refine_corner(self, boundary_points: List[Point], coarse_index: int, search_radius: int) -> int:
        """
        Refines a coarse corner using adaptive vector method to handle oversampled corners.
        """
        best_index = None
        max_angle = 0.0
        n = len(boundary_points)
        coarse_index = coarse_index % n

        start = coarse_index - search_radius
        end = coarse_index + search_radius

        for offset in range(start, end + 1):
            i = offset % n
            
            # Skip if too close to boundaries for proper vector calculation
            if i < 1 or i >= n - 1:
                continue

            # Use adaptive window to find non-zero vectors
            window_size = self._find_minimal_window(boundary_points, i, max_window=min(10, n//4))
            
            if window_size == 0:
                continue

            prev_idx = (i - window_size) % n
            next_idx = (i + window_size) % n

            v1 = np.array([
                boundary_points[i].x - boundary_points[prev_idx].x,
                boundary_points[i].y - boundary_points[prev_idx].y
            ])
            v2 = np.array([
                boundary_points[next_idx].x - boundary_points[i].x,
                boundary_points[next_idx].y - boundary_points[i].y
            ])

            norm_v1 = np.linalg.norm(v1)
            norm_v2 = np.linalg.norm(v2)

            if norm_v1 < 1e-8 or norm_v2 < 1e-8:
                continue

            angle = self._angle_between_vectors(v1, v2)
            angle_deg = np.degrees(angle)

            if angle > self.angle_threshold and angle > max_angle:
                max_angle = angle
                best_index = i

        if best_index is None:
            best_index = coarse_index

        return best_index

    def _find_minimal_window(self, points: List[Point], center_idx: int, max_window: int = 10) -> int:
        """
        Find the smallest window size that gives non-zero vectors.
        Returns 0 if no valid window found.
        """
        n = len(points)
        
        for window in range(1, max_window + 1):
            prev_idx = (center_idx - window) % n
            next_idx = (center_idx + window) % n
            
            # Avoid using the same point (wrap-around edge case)
            if prev_idx == next_idx:
                continue
                
            v1 = np.array([
                points[center_idx].x - points[prev_idx].x,
                points[center_idx].y - points[prev_idx].y
            ])
            v2 = np.array([
                points[next_idx].x - points[center_idx].x,
                points[next_idx].y - points[center_idx].y
            ])
            
            norm1, norm2 = np.linalg.norm(v1), np.linalg.norm(v2)
            
            if norm1 > 1e-8 and norm2 > 1e-8:
                return window
        
        return 0

    def _angle_between_vectors(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """Calculate angle between two vectors in radians"""
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        return np.arccos(cos_angle)