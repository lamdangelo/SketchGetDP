import numpy as np
from typing import List
from ..core.entities.point import Point


class CornerDetector:
    """
    Identifies corner points in boundary point sequences by analyzing changes
    in direction vectors across sliding windows.
    """
    
    def __init__(self, window_size: int = 3, direction_change_threshold: float = 1.0):
        self.window_size = window_size
        self.direction_change_threshold = direction_change_threshold
    
    def detect_corners(self, boundary_points: List[Point]) -> List[int]:
        """
        Identifies indices of corner points in the boundary point sequence.
        
        Corner points are detected where the average direction of consecutive
        point windows changes significantly, indicating sharp turns.
        """
        if len(boundary_points) < self.window_size * 2:
            return []
        
        x_coordinates = np.array([point.x for point in boundary_points])
        y_coordinates = np.array([point.y for point in boundary_points])
        
        window_directions = self._calculate_window_directions(x_coordinates, y_coordinates)
        
        if len(window_directions) < 2:
            return []
        
        corner_indices = self._find_corner_indices(window_directions, len(boundary_points))
        return sorted(set(corner_indices))
    
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
                corner_index = window_index * self.window_size
                corner_indices.append(corner_index)
        
        # Check for closure in circular boundaries (last window to first window)
        if len(window_directions) >= 2:
            closure_direction_change = window_directions[-1] - window_directions[0]
            closure_change_magnitude = np.linalg.norm(closure_direction_change)
            
            if closure_change_magnitude > self.direction_change_threshold:
                closure_corner_index = total_points - self.window_size
                corner_indices.append(closure_corner_index)
        
        return corner_indices