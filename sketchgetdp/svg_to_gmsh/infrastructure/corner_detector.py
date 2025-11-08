"""
Detects corners by analyzing direction changes in batches of boundary points.
"""

from typing import List
import math
from ..core.entities.point import Point


class CornerDetector:
    """
    Detects corners in boundary curves by analyzing local direction changes.
    """
    
    def __init__(self, num_batches: int = 12, threshold: float = 0.3, window_size: int = 8, min_corner_distance: int = 20):
        """
        Initialize with more sensitive parameters to detect actual corners.
        """
        self.num_batches = num_batches
        self.threshold = threshold  # Lower threshold = more corners
        self.window_size = window_size
        self.min_corner_distance = min_corner_distance
    
    def detect_corners(self, boundary_points: List[Point]) -> List[Point]:
        """
        Detect corners in a boundary curve with conservative settings.
        """
        if len(boundary_points) < 3:
            raise ValueError("Need at least 3 points to detect corners")
        
        # Remove consecutive duplicate points
        cleaned_points = self._remove_duplicate_points(boundary_points)
        if len(cleaned_points) < 3:
            return []
        
        # Use conservative sliding window approach
        corners = self._detect_corners_conservative(cleaned_points)
        
        return corners
    
    def _detect_corners_conservative(self, points: List[Point]) -> List[Point]:
        """
        Conservative corner detection with higher thresholds.
        """
        if len(points) < self.window_size * 2:
            return []
        
        corners = []
        n = len(points)
        
        # Calculate direction changes for each point
        direction_changes = []
        for i in range(n):
            # Get left and right windows
            left_start = max(0, i - self.window_size)
            left_end = i
            right_start = i
            right_end = min(n, i + self.window_size + 1)
            
            # Calculate average directions
            left_direction = self._calculate_window_direction(points, left_start, left_end)
            right_direction = self._calculate_window_direction(points, right_start, right_end)
            
            # Calculate direction change
            if left_direction.norm() > 1e-10 and right_direction.norm() > 1e-10:
                change = self._direction_difference(left_direction, right_direction)
                direction_changes.append(change)
            else:
                direction_changes.append(0.0)
        
        # Find local maxima with higher threshold
        candidate_indices = []
        for i in range(self.window_size, n - self.window_size):
            if (direction_changes[i] > self.threshold and  # Higher threshold
                direction_changes[i] >= direction_changes[i-1] and
                direction_changes[i] >= direction_changes[i+1] and
                direction_changes[i] > 0.8):  # Additional absolute threshold
                candidate_indices.append(i)
        
        # Filter candidates aggressively
        filtered_indices = self._filter_corner_candidates_conservative(candidate_indices, direction_changes, n)
        
        # Convert indices to points
        for idx in filtered_indices:
            corners.append(points[idx])
        
        return corners
    
    def _filter_corner_candidates_conservative(self, candidate_indices: List[int], direction_changes: List[float], total_points: int) -> List[int]:
        """Filter corner candidates aggressively to avoid over-detection."""
        if not candidate_indices:
            return []
        
        # Sort candidates by direction change magnitude (descending)
        candidates_with_scores = [(idx, direction_changes[idx]) for idx in candidate_indices]
        candidates_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Limit maximum corners based on curve length
        max_corners = max(3, total_points // 80)  # Very conservative: ~1 corner per 80 points
        filtered_indices = []
        
        for idx, score in candidates_with_scores:
            # Check if this candidate is too close to any already selected corner
            too_close = False
            for selected_idx in filtered_indices:
                if abs(idx - selected_idx) < self.min_corner_distance:
                    too_close = True
                    break
            
            if not too_close and len(filtered_indices) < max_corners:
                filtered_indices.append(idx)
        
        # Sort by index to maintain order along the curve
        filtered_indices.sort()
        return filtered_indices
    
    def _calculate_window_direction(self, points: List[Point], start: int, end: int) -> Point:
        """Calculate average direction for a window of points."""
        if end - start < 2:
            return Point(0, 0)
        
        total_direction = Point(0, 0)
        segment_count = 0
        
        for i in range(start, end - 1):
            current_point = points[i]
            next_point = points[i + 1]
            
            direction_vec = next_point - current_point
            norm = direction_vec.norm()
            
            if norm > 1e-10:
                normalized_direction = direction_vec / norm
                total_direction = total_direction + normalized_direction
                segment_count += 1
        
        if segment_count > 0:
            average_direction = total_direction / segment_count
            avg_norm = average_direction.norm()
            if avg_norm > 1e-10:
                return average_direction / avg_norm
        
        return Point(0, 0)
    
    def _remove_duplicate_points(self, points: List[Point]) -> List[Point]:
        """Remove consecutive duplicate points."""
        if not points:
            return []
        
        cleaned = [points[0]]
        for i in range(1, len(points)):
            if (abs(points[i].x - points[i-1].x) > 1e-10 or 
                abs(points[i].y - points[i-1].y) > 1e-10):
                cleaned.append(points[i])
        
        return cleaned
    
    def _direction_difference(self, vec1: Point, vec2: Point) -> float:
        """Calculate the difference between two direction vectors."""
        diff_x = vec1.x - vec2.x
        diff_y = vec1.y - vec2.y
        return math.sqrt(diff_x * diff_x + diff_y * diff_y)