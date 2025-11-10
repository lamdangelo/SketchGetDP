"""
Robust corner detection for freehand drawings.
"""

from typing import List, Tuple
import math
from ..core.entities.point import Point


class CornerDetector:
    """
    Detects corners in freehand boundary curves using multi-scale curvature analysis.
    """
    
    def __init__(self, primary_threshold: float = 0.12, secondary_threshold: float = 0.08, 
                 min_corner_angle: float = 100.0, min_distance: int = 15):
        """
        Initialize with robust parameters for freehand drawings.
        
        Args:
            primary_threshold: Main threshold for strong corners (0-1 scale)
            secondary_threshold: Lower threshold for weaker but still significant corners
            min_corner_angle: Minimum angle (degrees) to consider as a corner
            min_distance: Minimum distance between detected corners (in point indices)
        """
        self.primary_threshold = primary_threshold
        self.secondary_threshold = secondary_threshold
        self.min_corner_angle_rad = math.radians(min_corner_angle)
        self.min_distance = min_distance
    
    def detect_corners(self, boundary_points: List[Point]) -> List[Point]:
        """
        Detect corners in freehand boundary curves using robust multi-scale approach.
        """
        if len(boundary_points) < 10:
            return []
        
        # Remove duplicates and smooth slightly
        cleaned_points = self._preprocess_points(boundary_points)
        if len(cleaned_points) < 10:
            return []
        
        # Multi-scale curvature analysis
        curvature_maps = self._multi_scale_curvature_analysis(cleaned_points)
        
        # Combine curvature maps and find significant corners
        combined_curvature = self._combine_curvature_maps(curvature_maps)
        corner_indices = self._find_significant_corners(combined_curvature, cleaned_points)
        
        return [cleaned_points[i] for i in corner_indices]
    
    def _preprocess_points(self, points: List[Point]) -> List[Point]:
        """Remove duplicates and apply light smoothing."""
        # Remove duplicates
        cleaned = []
        for i, point in enumerate(points):
            if i == 0 or point != points[i-1]:
                cleaned.append(point)
        
        # Light smoothing to reduce noise (3-point moving average)
        if len(cleaned) >= 5:
            smoothed = []
            for i in range(len(cleaned)):
                if i == 0 or i == len(cleaned) - 1:
                    smoothed.append(cleaned[i])
                else:
                    # Simple 3-point average
                    prev = cleaned[i-1]
                    curr = cleaned[i]
                    next_p = cleaned[i+1]
                    avg_x = (prev.x + curr.x + next_p.x) / 3.0
                    avg_y = (prev.y + curr.y + next_p.y) / 3.0
                    smoothed.append(Point(avg_x, avg_y))
            return smoothed
        
        return cleaned
    
    def _multi_scale_curvature_analysis(self, points: List[Point]) -> List[List[float]]:
        """Calculate curvature at multiple scales."""
        scales = [3, 5, 7, 9]  # Different window sizes
        curvature_maps = []
        
        for scale in scales:
            curvature_map = self._calculate_curvature_map(points, scale)
            curvature_maps.append(curvature_map)
        
        return curvature_maps
    
    def _calculate_curvature_map(self, points: List[Point], window_size: int) -> List[float]:
        """Calculate curvature using a specific window size."""
        n = len(points)
        curvature = [0.0] * n
        
        for i in range(window_size, n - window_size):
            # Calculate vectors before and after current point
            left_vector = self._get_direction_vector(points, i - window_size, i)
            right_vector = self._get_direction_vector(points, i, i + window_size)
            
            if left_vector.norm() > 1e-10 and right_vector.norm() > 1e-10:
                angle = self._angle_between_vectors(left_vector, right_vector)
                # Normalize curvature to [0,1] where 1 = 180 degree turn
                curvature[i] = angle / math.pi
            else:
                curvature[i] = 0.0
        
        return curvature
    
    def _get_direction_vector(self, points: List[Point], start: int, end: int) -> Point:
        """Calculate average direction vector over a range of points."""
        if end <= start:
            return Point(0, 0)
        
        # Use start and end points to get overall direction
        start_point = points[start]
        end_point = points[end]
        return end_point - start_point
    
    def _angle_between_vectors(self, v1: Point, v2: Point) -> float:
        """Calculate angle between two vectors in radians."""
        if v1.norm() < 1e-10 or v2.norm() < 1e-10:
            return 0.0
        
        dot_product = (v1.x * v2.x + v1.y * v2.y) / (v1.norm() * v2.norm())
        dot_product = max(-1.0, min(1.0, dot_product))
        return math.acos(dot_product)
    
    def _combine_curvature_maps(self, curvature_maps: List[List[float]]) -> List[float]:
        """Combine curvature maps from different scales."""
        n = len(curvature_maps[0])
        combined = [0.0] * n
        
        for i in range(n):
            # Take maximum curvature across scales (sharp corners appear at multiple scales)
            max_curvature = max(curvature_map[i] for curvature_map in curvature_maps)
            combined[i] = max_curvature
        
        return combined
    
    def _find_significant_corners(self, combined_curvature: List[float], points: List[Point]) -> List[int]:
        """Find significant corners using adaptive thresholding."""
        n = len(combined_curvature)
        
        # Find local maxima
        local_maxima = []
        for i in range(5, n - 5):
            if (combined_curvature[i] > self.primary_threshold and
                combined_curvature[i] == max(combined_curvature[i-2:i+3])):
                local_maxima.append(i)
        
        # Filter by actual angle and significance
        filtered_corners = []
        for idx in local_maxima:
            if self._is_valid_corner(points, idx, combined_curvature):
                # Check distance from existing corners
                if not any(abs(idx - corner) < self.min_distance for corner in filtered_corners):
                    filtered_corners.append(idx)
        
        # If we found too few corners, use secondary threshold
        if len(filtered_corners) < 2 and len(local_maxima) > 0:
            secondary_candidates = [idx for idx in local_maxima 
                                 if combined_curvature[idx] > self.secondary_threshold 
                                 and idx not in filtered_corners]
            
            for idx in secondary_candidates:
                if self._is_valid_corner(points, idx, combined_curvature):
                    if not any(abs(idx - corner) < self.min_distance for corner in filtered_corners):
                        filtered_corners.append(idx)
                        if len(filtered_corners) >= 3:  # Reasonable limit
                            break
        
        # Sort by index
        filtered_corners.sort()
        return filtered_corners
    
    def _is_valid_corner(self, points: List[Point], index: int, combined_curvature: List[float]) -> bool:
        """Validate if a point is a true corner."""
        n = len(points)
        if index < 5 or index > n - 6:
            return False
        
        # Calculate actual angle using a larger window for more reliable measurement
        left_vec = points[index] - points[index - 4]
        right_vec = points[index + 4] - points[index]
        
        if left_vec.norm() < 1e-10 or right_vec.norm() < 1e-10:
            return False
        
        angle = self._angle_between_vectors(left_vec, right_vec)
        
        # Check if this is a sharp enough corner
        is_sharp = angle < (math.pi - self.min_corner_angle_rad)
        
        # Additional check: curvature should be significantly higher than neighbors
        neighbor_indices = [
            max(0, index-3), max(0, index-2), max(0, index-1),
            min(n-1, index+1), min(n-1, index+2), min(n-1, index+3)
        ]
        neighbor_curvatures = [combined_curvature[i] for i in neighbor_indices]
        neighbor_avg = sum(neighbor_curvatures) / len(neighbor_curvatures)
        
        is_significant = combined_curvature[index] > neighbor_avg * 1.5
        
        return is_sharp and is_significant
    
    def debug_corner_detection(self, boundary_points: List[Point]):
        """Debug corner detection process."""
        if len(boundary_points) < 10:
            print("Not enough points for meaningful corner detection")
            return
        
        cleaned_points = self._preprocess_points(boundary_points)
        print(f"Processing {len(cleaned_points)} points for corner detection")
        
        # Multi-scale analysis
        curvature_maps = self._multi_scale_curvature_analysis(cleaned_points)
        combined_curvature = self._combine_curvature_maps(curvature_maps)
        
        # Find and show top curvature points
        top_indices = sorted(range(len(combined_curvature)), 
                           key=lambda i: combined_curvature[i], reverse=True)[:10]
        
        print("Top curvature points:")
        for idx in top_indices:
            if combined_curvature[idx] > 0.05:  # Only show significant ones
                point = cleaned_points[idx]
                curvature_val = combined_curvature[idx]
                angle_deg = curvature_val * 180  # Convert to degrees for readability
                print(f"  Point {idx}: ({point.x:.3f}, {point.y:.3f}) - curvature: {curvature_val:.3f} ({angle_deg:.1f}°)")
        
        # Show detected corners
        corners = self.detect_corners(boundary_points)
        print(f"Detected {len(corners)} corners:")
        for i, corner in enumerate(corners):
            print(f"  Corner {i}: ({corner.x:.3f}, {corner.y:.3f})")