from typing import List
import math
from ..core.entities.point import Point

class CornerDetector:
    """
    Detects meaningful corner points in a polyline for Bézier curve fitting.
    Uses a balanced approach combining turning angles and curvature analysis
    to avoid over-detection while capturing significant shape features.
    """
    
    def __init__(self, neighborhood_size: int = 7, min_turning_angle: float = 45.0, 
                 min_curvature_sharpness: float = 0.8, min_corner_distance: int = 8, 
                 max_corners_to_detect: int = 12):
        """
        Initialize corner detector with balanced parameters.
        
        Args:
            neighborhood_size: Number of points to consider for local curvature calculation
            min_turning_angle: Minimum angle (degrees) to consider a point as a corner
            min_curvature_sharpness: Minimum sharpness value for curvature-based detection
            min_corner_distance: Minimum pixel distance between detected corners
            max_corners_to_detect: Maximum number of corners to return
        """
        self.neighborhood_size = neighborhood_size
        self.min_turning_angle = min_turning_angle
        self.min_curvature_sharpness = min_curvature_sharpness
        self.min_corner_distance = min_corner_distance
        self.max_corners_to_detect = max_corners_to_detect
    
    def detect_corners(self, points: List[Point]) -> List[int]:
        """
        Detect meaningful corners for Bézier fitting.
        
        Args:
            points: List of points representing the polyline
            
        Returns:
            List of indices where corners are detected
        """
        if len(points) < 2 * self.neighborhood_size + 1:
            return self._fallback_detection_for_small_curves(points)
        
        turning_angles = self._calculate_turning_angles(points)
        curvature_sharpness_values = self._calculate_curvature_sharpness(points)
        corner_scores = self._calculate_combined_corner_scores(points, turning_angles, curvature_sharpness_values)
        
        corners_from_angles = self._find_corners_by_turning_angle(turning_angles)
        corners_from_curvature = self._find_corners_by_curvature_sharpness(curvature_sharpness_values)
        
        all_candidate_indices = set(corners_from_angles + corners_from_curvature)
        
        filtered_corners = self._filter_corners_by_score_and_distance(
            list(all_candidate_indices), corner_scores, points)
        
        final_corners = self._ensure_reasonable_corner_distribution(filtered_corners, points)
        final_corners.sort()
        
        return final_corners
    
    def _calculate_turning_angles(self, points: List[Point]) -> List[float]:
        """Calculate the turning angle at each point in degrees."""
        turning_angles = [0.0] * len(points)
        
        for current_index in range(1, len(points) - 1):
            vector_to_previous = points[current_index - 1] - points[current_index]
            vector_to_next = points[current_index + 1] - points[current_index]
            
            dot_product = vector_to_previous.x * vector_to_next.x + vector_to_previous.y * vector_to_next.y
            magnitude_product = vector_to_previous.norm() * vector_to_next.norm()
            
            if magnitude_product > 1e-10:
                cosine_value = max(-1.0, min(1.0, dot_product / magnitude_product))
                angle_radians = math.acos(cosine_value)
                # Convert internal angle to turning angle (180° - internal angle)
                turning_angle = 180.0 - math.degrees(angle_radians)
                turning_angles[current_index] = abs(turning_angle)
        
        return turning_angles
    
    def _calculate_curvature_sharpness(self, points: List[Point]) -> List[float]:
        """Calculate curvature sharpness using k-cosine method."""
        curvature_sharpness_values = []
        
        for center_index in range(len(points)):
            left_neighbor_index = max(0, center_index - self.neighborhood_size)
            right_neighbor_index = min(len(points) - 1, center_index + self.neighborhood_size)
            
            if right_neighbor_index - left_neighbor_index < 2:
                curvature_sharpness_values.append(1.0)
                continue
            
            left_vector = points[left_neighbor_index] - points[center_index]
            right_vector = points[right_neighbor_index] - points[center_index]
            
            dot_product = left_vector.x * right_vector.x + left_vector.y * right_vector.y
            magnitude_product = left_vector.norm() * right_vector.norm()
            
            if magnitude_product > 1e-10:
                cosine_similarity = dot_product / magnitude_product
                # Convert to sharpness measure (1.0 = maximum sharpness, 0.0 = flat)
                sharpness = 1.0 - abs(cosine_similarity)
                curvature_sharpness_values.append(sharpness)
            else:
                curvature_sharpness_values.append(0.0)
        
        return curvature_sharpness_values
    
    def _calculate_combined_corner_scores(self, points: List[Point], 
                                        turning_angles: List[float], 
                                        curvature_sharpness_values: List[float]) -> List[float]:
        """Calculate combined corner scores from turning angles and curvature."""
        corner_scores = [0.0] * len(points)
        
        for i in range(len(points)):
            # Normalize angle score (0-1 range, 90° = maximum score)
            normalized_angle_score = min(turning_angles[i] / 90.0, 1.0)
            
            # Curvature score is already normalized (0-1)
            curvature_score = curvature_sharpness_values[i]
            
            # Weighted combination favoring turning angles (60%) over curvature (40%)
            corner_scores[i] = 0.6 * normalized_angle_score + 0.4 * curvature_score
        
        return corner_scores
    
    def _find_corners_by_turning_angle(self, turning_angles: List[float]) -> List[int]:
        """Find corner candidates where turning angle exceeds threshold and is locally maximal."""
        corner_indices = []
        
        for center_index in range(2, len(turning_angles) - 2):
            current_angle = turning_angles[center_index]
            is_local_maximum = (current_angle > turning_angles[center_index-1] and 
                              current_angle > turning_angles[center_index-2] and
                              current_angle > turning_angles[center_index+1] and 
                              current_angle > turning_angles[center_index+2])
            
            if current_angle > self.min_turning_angle and is_local_maximum:
                corner_indices.append(center_index)
        
        return corner_indices
    
    def _find_corners_by_curvature_sharpness(self, curvature_sharpness_values: List[float]) -> List[int]:
        """Find corner candidates where curvature sharpness exceeds threshold and is locally maximal."""
        corner_indices = []
        
        for center_index in range(2, len(curvature_sharpness_values) - 2):
            current_sharpness = curvature_sharpness_values[center_index]
            is_local_maximum = (current_sharpness > curvature_sharpness_values[center_index-1] and 
                              current_sharpness > curvature_sharpness_values[center_index-2] and
                              current_sharpness > curvature_sharpness_values[center_index+1] and 
                              current_sharpness > curvature_sharpness_values[center_index+2])
            
            if current_sharpness > self.min_curvature_sharpness and is_local_maximum:
                corner_indices.append(center_index)
        
        return corner_indices
    
    def _filter_corners_by_score_and_distance(self, candidate_indices: List[int], 
                                            corner_scores: List[float], 
                                            points: List[Point]) -> List[int]:
        """Filter corners by score ranking and minimum distance constraints."""
        if not candidate_indices:
            return []
        
        candidates_with_scores = [(index, corner_scores[index]) for index in candidate_indices]
        candidates_with_scores.sort(key=lambda candidate: candidate[1], reverse=True)
        
        top_candidates_by_score = candidates_with_scores[:self.max_corners_to_detect]
        
        filtered_corners = []
        for candidate_index, score in top_candidates_by_score:
            if not filtered_corners:
                filtered_corners.append(candidate_index)
                continue
            
            # Check if this candidate is too close to any already selected corner
            is_too_close_to_existing = any(
                points[candidate_index].distance_to(points[existing_index]) < self.min_corner_distance
                for existing_index in filtered_corners
            )
            
            if not is_too_close_to_existing:
                filtered_corners.append(candidate_index)
        
        return filtered_corners
    
    def _ensure_reasonable_corner_distribution(self, corner_indices: List[int], 
                                             points: List[Point]) -> List[int]:
        """
        Ensure corners are reasonably distributed, especially for simple shapes.
        Adds start/end points and quarter points if too few corners are detected.
        """
        if len(corner_indices) >= 4:
            return corner_indices
        
        total_points = len(points)
        if total_points < 10:
            return corner_indices
        
        distributed_corners = corner_indices.copy()
        
        # Always include start and end points for open curves
        start_point_index = 0
        end_point_index = total_points - 1
        if start_point_index not in distributed_corners:
            distributed_corners.append(start_point_index)
        if end_point_index not in distributed_corners:
            distributed_corners.append(end_point_index)
        
        # Add quarter points if still insufficient
        if len(distributed_corners) < 4:
            first_quarter_index = total_points // 4
            midpoint_index = total_points // 2
            third_quarter_index = 3 * total_points // 4
            
            for quarter_point_index in [first_quarter_index, midpoint_index, third_quarter_index]:
                if quarter_point_index not in distributed_corners:
                    distributed_corners.append(quarter_point_index)
        
        return distributed_corners[:self.max_corners_to_detect]
    
    def _fallback_detection_for_small_curves(self, points: List[Point]) -> List[int]:
        """Simple corner detection for curves with too few points for full analysis."""
        point_count = len(points)
        
        if point_count <= 10:
            return list(range(point_count))
        
        else:
            # Simple segmentation for medium-sized curves
            return [0, point_count // 3, 2 * point_count // 3, point_count - 1]
    
    def _log_detection_statistics(self, points: List[Point], corners_from_angles: List[int],
                                corners_from_curvature: List[int], final_corners: List[int]) -> None:
        """Log debugging information about the corner detection process."""
        print(f"\n=== CORNER DETECTOR DEBUG OUTPUT ===")
        print(f"Total points: {len(points)}")
        print(f"Angle-based corners: {len(corners_from_angles)}")
        print(f"Curvature-based corners: {len(corners_from_curvature)}")
        print(f"Final corner indices: {final_corners}")
        print(f"Detected corner count: {len(final_corners)}")
        
        if final_corners:
            print("Corner point coordinates:")
            for index in final_corners:
                if index < len(points):
                    point = points[index]
                    print(f"  Index {index}: ({point.x:.2f}, {point.y:.2f})")
        else:
            print("No corners detected!")
        print("=== END CORNER DETECTOR DEBUG ===\n")