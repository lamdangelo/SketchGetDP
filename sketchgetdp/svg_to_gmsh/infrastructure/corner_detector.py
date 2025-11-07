"""
Detects corners by analyzing direction changes in batches of boundary points.
"""

from typing import List
import math
from core.entities.point import Point


class CornerDetector:
    """
    Detects corners in boundary curves by analyzing local direction changes.
    
    The algorithm works by:
    1. Dividing the boundary points into sequential batches
    2. Calculating the average direction vector for each batch
    3. Comparing direction vectors between adjacent batches
    4. Identifying corners where direction changes exceed a threshold
    
    This approach is robust against drawing inaccuracies while detecting
    true geometric corners in hand-drawn shapes.
    """
    
    def __init__(self, num_batches: int = 8, threshold: float = 0.5, window_size: int = 5, min_corner_distance: int = 10):
        """
        Initialize the corner detector with heuristic parameters.
        
        Args:
            num_batches: Number of batches to divide the curve into (heuristically determined)
            threshold: Threshold for direction vector difference to identify corners
            window_size: Size of the sliding window for direction calculation
            min_corner_distance: Minimum distance between detected corners (in points)
        """
        self.num_batches = num_batches
        self.threshold = threshold
        self.window_size = window_size
        self.min_corner_distance = min_corner_distance
    
    def detect_corners(self, boundary_points: List[Point]) -> List[Point]:
        """
        Detect corners in a boundary curve.
        
        Args:
            boundary_points: Ordered list of points representing the boundary curve
            
        Returns:
            List of detected corner points
        """
        if len(boundary_points) < 3:
            raise ValueError("Need at least 3 points to detect corners")
        
        # Validate all points
        for point in boundary_points:
            if math.isnan(point.x) or math.isnan(point.y):
                raise ValueError("Points cannot contain NaN values")
        
        # Remove consecutive duplicate points
        cleaned_points = self._remove_duplicate_points(boundary_points)
        if len(cleaned_points) < 3:
            return []
        
        # Use sliding window approach for more robust corner detection
        corners = self._detect_corners_sliding_window(cleaned_points)
        
        return corners
    
    def _detect_corners_sliding_window(self, points: List[Point]) -> List[Point]:
        """
        Detect corners using a sliding window approach.
        This is more robust than the batch-based approach for detecting geometric corners.
        """
        if len(points) < self.window_size * 2:
            return []
        
        corners = []
        n = len(points)
        
        # Calculate direction changes for each point using sliding windows
        direction_changes = []
        for i in range(n):
            # Get left and right windows
            left_start = max(0, i - self.window_size)
            left_end = i
            right_start = i
            right_end = min(n, i + self.window_size + 1)
            
            # Calculate average directions for left and right windows
            left_direction = self._calculate_window_direction(points, left_start, left_end)
            right_direction = self._calculate_window_direction(points, right_start, right_end)
            
            # Calculate direction change
            if left_direction.norm() > 1e-10 and right_direction.norm() > 1e-10:
                change = self._direction_difference(left_direction, right_direction)
                direction_changes.append(change)
            else:
                direction_changes.append(0.0)
        
        # Find local maxima in direction changes that exceed threshold
        candidate_indices = []
        for i in range(self.window_size, n - self.window_size):
            if (direction_changes[i] > self.threshold and
                direction_changes[i] >= direction_changes[i-1] and
                direction_changes[i] >= direction_changes[i+1]):
                candidate_indices.append(i)
        
        # Filter candidates to ensure minimum distance between corners
        filtered_indices = self._filter_corner_candidates(candidate_indices, direction_changes)
        
        # Convert indices to points
        for idx in filtered_indices:
            corners.append(points[idx])
        
        return corners
    
    def _filter_corner_candidates(self, candidate_indices: List[int], direction_changes: List[float]) -> List[int]:
        """Filter corner candidates to ensure minimum distance between corners."""
        if not candidate_indices:
            return []
        
        # Sort candidates by direction change magnitude (descending)
        candidates_with_scores = [(idx, direction_changes[idx]) for idx in candidate_indices]
        candidates_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        filtered_indices = []
        for idx, score in candidates_with_scores:
            # Check if this candidate is too close to any already selected corner
            too_close = False
            for selected_idx in filtered_indices:
                if abs(idx - selected_idx) < self.min_corner_distance:
                    too_close = True
                    break
            
            if not too_close:
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
    
    def _divide_into_batches(self, points: List[Point]) -> List[List[Point]]:
        """
        Divide the boundary points into approximately equal batches.
        
        Args:
            points: Ordered list of boundary points
            
        Returns:
            List of batches, each containing a subset of points
        """
        n_points = len(points)
        
        # Adjust number of batches if we have fewer points than requested batches
        actual_batches = min(self.num_batches, n_points)
        if actual_batches < 1:
            return [points]  # Fallback: all points in one batch
        
        # Calculate batch sizes
        base_batch_size = n_points // actual_batches
        remainder = n_points % actual_batches
        
        batches = []
        start_index = 0
        
        for i in range(actual_batches):
            # Distribute remainder among first few batches
            batch_size = base_batch_size + (1 if i < remainder else 0)
            end_index = start_index + batch_size
            
            # Ensure we don't go beyond the points list
            if end_index > n_points:
                end_index = n_points
            
            batch = points[start_index:end_index]
            if batch:  # Only add non-empty batches
                batches.append(batch)
            start_index = end_index
            
            # Stop if we've processed all points
            if start_index >= n_points:
                break
        
        return batches
    
    def _compute_direction_vectors(self, batches: List[List[Point]]) -> List[Point]:
        """
        Compute normalized average direction vectors for each batch.
        
        Args:
            batches: List of point batches
            
        Returns:
            List of normalized direction vectors (one per batch)
        """
        direction_vectors = []
        
        for batch in batches:
            if len(batch) < 2:
                # For single-point batches, use zero vector
                direction_vectors.append(Point(0, 0))
                continue
            
            # Calculate average direction within the batch
            total_direction = Point(0, 0)
            segment_count = 0
            
            for i in range(len(batch) - 1):
                current_point = batch[i]
                next_point = batch[i + 1]
                
                # Direction vector between consecutive points
                direction_vec = next_point - current_point
                
                # Normalize the direction vector
                norm = direction_vec.norm()
                if norm > 1e-10:  # Avoid division by zero
                    normalized_direction = direction_vec / norm
                    total_direction = total_direction + normalized_direction
                    segment_count += 1
            
            if segment_count > 0:
                # Average direction
                average_direction = total_direction / segment_count
                
                # Normalize the average direction
                avg_norm = average_direction.norm()
                if avg_norm > 1e-10:
                    direction = average_direction / avg_norm
                else:
                    direction = Point(0, 0)
            else:
                direction = Point(0, 0)
            
            direction_vectors.append(direction)
        
        return direction_vectors
    
    def _detect_corner_indices(self, direction_vectors: List[Point]) -> List[int]:
        """
        Detect corner indices based on direction vector differences.
        
        Args:
            direction_vectors: List of normalized direction vectors
            
        Returns:
            List of indices where corners are detected
        """
        corner_indices = []
        n_vectors = len(direction_vectors)
        
        if n_vectors < 2:
            return corner_indices  # Need at least 2 batches to detect corners
        
        # Check differences between adjacent direction vectors
        for i in range(n_vectors - 1):
            current_vector = direction_vectors[i]
            next_vector = direction_vectors[i + 1]
            
            # Skip if either vector is zero (degenerate case)
            if current_vector.norm() < 1e-10 or next_vector.norm() < 1e-10:
                continue
            
            # Calculate the difference between direction vectors
            difference = self._direction_difference(current_vector, next_vector)
            
            # If difference exceeds threshold, mark as corner
            if difference > self.threshold:
                corner_indices.append(i + 1)  # Corner at start of next batch
        
        return corner_indices
    
    def _direction_difference(self, vec1: Point, vec2: Point) -> float:
        """
        Calculate the difference between two direction vectors.
        
        Args:
            vec1: First direction vector (normalized)
            vec2: Second direction vector (normalized)
            
        Returns:
            Euclidean distance between the two vectors
        """
        # Since vectors are normalized, the Euclidean distance represents
        # the angular difference (0 = same direction, √2 = opposite directions)
        diff_x = vec1.x - vec2.x
        diff_y = vec1.y - vec2.y
        return math.sqrt(diff_x * diff_x + diff_y * diff_y)
    
    def _map_corner_indices_to_points(self, batches: List[List[Point]], corner_indices: List[int]) -> List[Point]:
        """
        Map corner batch indices back to actual boundary points.
        
        Args:
            batches: List of point batches
            corner_indices: List of batch indices where corners were detected
            
        Returns:
            List of corner points
        """
        corner_points = []
        
        for batch_index in corner_indices:
            if 0 <= batch_index < len(batches):
                batch = batches[batch_index]
                if batch:  # Ensure batch is not empty
                    # Use the first point of the batch as the corner location
                    corner_points.append(batch[0])
        
        return corner_points
    
    def _calculate_batch_direction(self, points: List[Point], start_idx: int, end_idx: int) -> Point:
        """
        Calculate the normalized average direction for a specific range of points.
        This is a helper method used by tests.
        
        Args:
            points: Complete list of boundary points
            start_idx: Start index of the range
            end_idx: End index of the range (exclusive)
            
        Returns:
            Normalized direction vector
        """
        batch = points[start_idx:end_idx]
        direction_vectors = self._compute_direction_vectors([batch])
        return direction_vectors[0] if direction_vectors else Point(0, 0)