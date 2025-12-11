import numpy as np
from typing import List, Tuple
from ..core.entities.point import Point
from ..interfaces.abstractions.corner_detector_interface import CornerDetectorInterface


class CornerDetector(CornerDetectorInterface):
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
            # Special handling for small shapes (like small ellipses)
            if len(boundary_points) < 30:
                if self._is_likely_small_ellipse(boundary_points):
                    return []
            return []
        
        x_coordinates = np.array([point.x for point in boundary_points])
        y_coordinates = np.array([point.y for point in boundary_points])
        
        window_directions = self._calculate_window_directions(x_coordinates, y_coordinates)
        
        if len(window_directions) < 2:
            return []
        
        # Step 1: coarse detection
        coarse_corner_indices = self._find_corner_indices_with_adaptive_threshold(
            window_directions, x_coordinates, y_coordinates, len(boundary_points)
        )
        
        # Step 2: refine locally using *both* adjacent windows
        refined_corner_indices = []
        for coarse_index in coarse_corner_indices:
            # refine at coarse_index
            refined_index = self._refine_corner(boundary_points, coarse_index, self.window_size)
            if refined_index is not None:
                refined_corner_indices.append(refined_index)
        
        # Step 3: Post-process to remove false positives while preserving true corners
        final_corners = self._post_process_corners(boundary_points, refined_corner_indices)
            
        return sorted(set(final_corners))
    
    def _is_likely_small_ellipse(self, points: List[Point]) -> bool:
        """Check if a small point set is likely an ellipse."""
        n = len(points)
        if n < 10:
            return True  # Very small sets are usually smooth
        
        # Calculate compactness (area/perimeter^2)
        # Ellipses have higher compactness than polygons with corners
        area = self._calculate_polygon_area(points)
        perimeter = self._calculate_polygon_perimeter(points)
        
        if perimeter > 0:
            compactness = 4 * np.pi * area / (perimeter * perimeter)
            # Ellipses have compactness close to 1, polygons with corners have lower compactness
            return compactness > 0.7
        
        return True
    
    def _calculate_polygon_area(self, points: List[Point]) -> float:
        """Calculate area of polygon using shoelace formula."""
        n = len(points)
        if n < 3:
            return 0.0
        
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += points[i].x * points[j].y
            area -= points[j].x * points[i].y
        
        return abs(area) / 2.0
    
    def _calculate_polygon_perimeter(self, points: List[Point]) -> float:
        """Calculate perimeter of polygon."""
        n = len(points)
        if n < 2:
            return 0.0
        
        perimeter = 0.0
        for i in range(n):
            j = (i + 1) % n
            dx = points[j].x - points[i].x
            dy = points[j].y - points[i].y
            perimeter += np.sqrt(dx*dx + dy*dy)
        
        return perimeter
    
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
    
    def _find_corner_indices_with_adaptive_threshold(self, window_directions: List[np.ndarray], 
                                                    x_coords: np.ndarray, y_coords: np.ndarray, 
                                                    total_points: int) -> List[int]:
        """Improved corner detection with curvature awareness."""
        corner_indices = []
        
        if len(window_directions) < 2:
            return corner_indices
        
        # Calculate local curvature for each window transition
        curvature_scores = []
        
        for window_index in range(len(window_directions) - 1):
            direction_change = window_directions[window_index] - window_directions[window_index + 1]
            change_magnitude = np.linalg.norm(direction_change)
            
            # Calculate local curvature at the transition point
            transition_idx = window_index * self.window_size + self.window_size // 2
            curvature = self._calculate_local_curvature(x_coords, y_coords, transition_idx)
            
            curvature_scores.append((change_magnitude, curvature))
        
        if not curvature_scores:
            return corner_indices
        
        # Find peaks in direction change that are NOT in high-curvature smooth regions
        changes = [score[0] for score in curvature_scores]
        curvatures = [score[1] for score in curvature_scores]
        
        mean_change = np.mean(changes)
        std_change = np.std(changes)
        mean_curvature = np.mean(curvatures)
        
        # Adjust thresholds for small shapes
        if total_points < 50:
            direction_threshold = max(self.direction_change_threshold * 1.5, mean_change + std_change)
        else:
            direction_threshold = max(self.direction_change_threshold, mean_change + 0.5 * std_change)
        
        for window_index, (change_magnitude, curvature) in enumerate(curvature_scores):
            # Only detect corners when:
            # 1. Direction change is significantly above average AND
            # 2. Not in a uniformly high-curvature region (like an ellipse)
            is_significant_change = change_magnitude > direction_threshold
            
            # Ellipses have uniformly high curvature, real corners have localized high curvature
            is_localized_corner = curvature > 2 * mean_curvature or change_magnitude > mean_change + 1.5 * std_change
            
            if is_significant_change and is_localized_corner:
                corner_index = window_index * self.window_size + self.window_size // 2
                corner_indices.append(corner_index)
        
        # Check closure point
        if len(window_directions) >= 2:
            closure_direction_change = window_directions[-1] - window_directions[0]
            closure_change_magnitude = np.linalg.norm(closure_direction_change)
            
            # Calculate the actual angle at point 0 to see if it's a real corner
            closure_angle = self._calculate_point_angle(x_coords, y_coords, 0, total_points)
            
            # For polygons, closure should be a corner with sharp angle
            # For ellipses, closure should be smooth (small angle)
            if (closure_change_magnitude > direction_threshold and 
                closure_angle > self.angle_threshold):
                closure_corner_index = 0
                corner_indices.append(closure_corner_index)
        
        return corner_indices
    
    def _calculate_point_angle(self, x_coords: np.ndarray, y_coords: np.ndarray, 
                             point_idx: int, total_points: int, window_size: int = 10) -> float:
        """Calculate the angle at a specific point."""
        n = total_points
        
        prev_idx = (point_idx - window_size) % n
        next_idx = (point_idx + window_size) % n
        
        v1 = np.array([x_coords[point_idx] - x_coords[prev_idx], 
                      y_coords[point_idx] - y_coords[prev_idx]])
        v2 = np.array([x_coords[next_idx] - x_coords[point_idx], 
                      y_coords[next_idx] - y_coords[point_idx]])
        
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        
        if norm_v1 < 1e-8 or norm_v2 < 1e-8:
            return 0.0
        
        cos_angle = np.dot(v1, v2) / (norm_v1 * norm_v2)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        return np.arccos(cos_angle)
    
    def _calculate_local_curvature(self, x_coords: np.ndarray, y_coords: np.ndarray, center_idx: int, radius: int = 10) -> float:
        """Calculate local curvature around a point."""
        n = len(x_coords)
        curvatures = []
        
        # Sample curvature at different scales
        for r in [radius // 2, radius]:
            start_idx = max(0, center_idx - r)
            end_idx = min(n - 1, center_idx + r)
            
            if end_idx - start_idx < 4:
                continue
            
            # Use a small window for curvature estimation
            window_x = x_coords[start_idx:end_idx + 1]
            window_y = y_coords[start_idx:end_idx + 1]
            
            # Simple curvature approximation: change in angle per unit length
            angles = []
            for i in range(1, len(window_x) - 1):
                v1 = np.array([window_x[i] - window_x[i-1], window_y[i] - window_y[i-1]])
                v2 = np.array([window_x[i+1] - window_x[i], window_y[i+1] - window_y[i]])
                
                norm_v1 = np.linalg.norm(v1)
                norm_v2 = np.linalg.norm(v2)
                
                if norm_v1 > 1e-8 and norm_v2 > 1e-8:
                    cos_angle = np.dot(v1, v2) / (norm_v1 * norm_v2)
                    cos_angle = np.clip(cos_angle, -1.0, 1.0)
                    angle = np.arccos(cos_angle)
                    angles.append(angle)
            
            if angles:
                avg_angle = np.mean(angles)
                # Convert to curvature (angle per unit length approximation)
                segment_length = np.sqrt((window_x[-1] - window_x[0])**2 + (window_y[-1] - window_y[0])**2)
                if segment_length > 1e-8:
                    curvature = avg_angle / segment_length
                    curvatures.append(curvature)
        
        return np.mean(curvatures) if curvatures else 0.0
    
    def _post_process_corners(self, points: List[Point], corner_indices: List[int]) -> List[int]:
        """Post-process corners to remove false positives while keeping true corners."""
        if len(corner_indices) <= 1:
            # Special case: check if single corner is legitimate
            if len(corner_indices) == 1:
                idx = corner_indices[0]
                # Check compactness - ellipses are more compact
                if len(points) < 100:  # Only for smaller shapes
                    compactness = self._calculate_compactness(points)
                    if compactness > 0.8:  # Very compact = likely ellipse
                        return []
            return corner_indices
        
        n = len(points)
        filtered_corners = []
        
        for i, idx in enumerate(corner_indices):
            # Check if this is a real corner by examining its neighborhood
            is_real_corner = self._is_real_corner(points, idx, corner_indices)
            
            if is_real_corner:
                filtered_corners.append(idx)
        
        # Ensure corners are not too close to each other
        merged_corners = self._merge_close_corners(points, filtered_corners)
        
        return merged_corners
    
    def _calculate_compactness(self, points: List[Point]) -> float:
        """Calculate shape compactness (4πA/P²). Higher = more circle-like."""
        area = self._calculate_polygon_area(points)
        perimeter = self._calculate_polygon_perimeter(points)
        
        if perimeter > 0:
            return 4 * np.pi * area / (perimeter * perimeter)
        return 0.0
    
    def _is_likely_ellipse(self, points: List[Point]) -> bool:
        """Check if shape is likely an ellipse/oval."""
        n = len(points)
        if n < 20:
            return True  # Small shapes are usually smooth
        
        # Use compactness as primary indicator
        compactness = self._calculate_compactness(points)
        if compactness > 0.85:
            return True
        
        # Also check curvature uniformity
        curvature_samples = []
        sample_step = max(1, n // 20)
        x_coords = np.array([p.x for p in points])
        y_coords = np.array([p.y for p in points])
        
        for i in range(0, n, sample_step):
            curvature = self._calculate_local_curvature(x_coords, y_coords, i, radius=min(10, n // 10))
            curvature_samples.append(curvature)
        
        if curvature_samples:
            curv_array = np.array(curvature_samples)
            mean_curv = np.mean(curv_array)
            std_curv = np.std(curv_array)
            
            # Ellipses have moderate, relatively uniform curvature
            if mean_curv > 0 and std_curv / mean_curv < 0.6:
                return True
        
        return False
    
    def _has_sharp_corners(self, points: List[Point], corner_indices: List[int]) -> bool:
        """Check if shape has genuinely sharp corners."""
        if not corner_indices:
            return False
        
        # Calculate angles at detected corners
        sharp_corner_count = 0
        for idx in corner_indices:
            angle = self._calculate_corner_angle(points, idx)
            if angle > np.pi / 3:  # 60 degrees or more
                sharp_corner_count += 1
        
        # Need at least 2 sharp corners for a polygonal shape
        return sharp_corner_count >= 2
    
    def _is_real_corner(self, points: List[Point], corner_idx: int, all_corners: List[int]) -> bool:
        """Determine if a detected corner is a real corner or a false positive."""
        n = len(points)
        
        # Find the angle at this point
        window_size = min(10, n // 20)
        angle = self._calculate_corner_angle(points, corner_idx, window_size)
        
        # Real corners should have significant angles
        if angle < self.angle_threshold:
            return False
        
        # For small shapes, be more careful
        if n < 100:
            # Check if this "corner" has neighbors with similar angles
            # (ellipses have many similar moderate angles, real corners stand out)
            similar_angle_count = 0
            test_points = [corner_idx - 10, corner_idx - 5, corner_idx + 5, corner_idx + 10]
            
            for test_idx in test_points:
                if 0 <= test_idx < n:
                    test_angle = self._calculate_corner_angle(points, test_idx, window_size=5)
                    if abs(test_angle - angle) < np.pi / 6:  # Within 30 degrees
                        similar_angle_count += 1
            
            # If many nearby points have similar angles, it's likely an ellipse
            if similar_angle_count >= 2:
                return False
        
        # Check if this corner is part of a smooth curve by looking at neighbors
        corner_positions = np.array(all_corners)
        distances = np.abs(corner_positions - corner_idx)
        distances = distances[distances > 0]  # Remove self
        
        if len(distances) > 0:
            min_distance = np.min(distances)
            
            # If corners are too regularly spaced, might be on an ellipse
            if min_distance < n // 6:  # More than 6 corners in total circumference
                # Check if this is part of a regularly spaced pattern
                regularity_score = self._check_regularity(points, all_corners)
                if regularity_score > 0.7:  # Moderately regular pattern
                    # But if angles are very sharp, keep them (could be a polygon)
                    if angle < np.pi / 2:  # Less than 90 degrees
                        return False
        
        return True
    
    def _check_regularity(self, points: List[Point], corner_indices: List[int]) -> float:
        """Check if corners are regularly spaced (indicative of ellipse false positives)."""
        if len(corner_indices) < 4:
            return 0.0
        
        # Calculate distances between consecutive corners
        sorted_indices = sorted(corner_indices)
        n = len(points)
        
        distances = []
        for i in range(len(sorted_indices)):
            next_idx = sorted_indices[(i + 1) % len(sorted_indices)]
            current_idx = sorted_indices[i]
            
            if next_idx >= current_idx:
                distance = next_idx - current_idx
            else:
                distance = (n - current_idx) + next_idx
            
            distances.append(distance)
        
        # Calculate coefficient of variation (regularity metric)
        mean_dist = np.mean(distances)
        std_dist = np.std(distances)
        
        if mean_dist > 0:
            cv = std_dist / mean_dist
            # Low CV indicates regular spacing
            regularity = 1.0 - min(cv, 1.0)
            return regularity
        
        return 0.0
    
    def _merge_close_corners(self, points: List[Point], corner_indices: List[int], min_distance: int = 15) -> List[int]:
        """Merge corners that are too close to each other."""
        if len(corner_indices) <= 1:
            return corner_indices
        
        sorted_corners = sorted(corner_indices)
        n = len(points)
        merged = []
        i = 0
        
        while i < len(sorted_corners):
            current = sorted_corners[i]
            
            # Look ahead to find close corners
            j = i + 1
            close_corners = [current]
            
            while j < len(sorted_corners):
                next_corner = sorted_corners[j]
                # Handle circular boundary
                distance = min(abs(next_corner - current), 
                              n - abs(next_corner - current))
                
                if distance < min_distance:
                    close_corners.append(next_corner)
                    j += 1
                else:
                    break
            
            # Merge close corners by taking the one with the sharpest angle
            if len(close_corners) > 1:
                best_corner = self._select_best_corner(points, close_corners)
                merged.append(best_corner)
            else:
                merged.append(current)
            
            i = j
        
        return merged
    
    def _select_best_corner(self, points: List[Point], corner_candidates: List[int]) -> int:
        """Select the best corner from a set of close candidates."""
        best_idx = corner_candidates[0]
        best_angle = 0.0
        
        for idx in corner_candidates:
            angle = self._calculate_corner_angle(points, idx)
            if angle > best_angle:
                best_angle = angle
                best_idx = idx
        
        return best_idx
    
    def _calculate_corner_angle(self, points: List[Point], corner_idx: int, window_size: int = 10) -> float:
        """Calculate the angle at a corner point."""
        n = len(points)
        
        prev_idx = (corner_idx - window_size) % n
        next_idx = (corner_idx + window_size) % n
        
        v1 = np.array([
            points[corner_idx].x - points[prev_idx].x,
            points[corner_idx].y - points[prev_idx].y
        ])
        v2 = np.array([
            points[next_idx].x - points[corner_idx].x,
            points[next_idx].y - points[corner_idx].y
        ])
        
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        
        if norm_v1 < 1e-8 or norm_v2 < 1e-8:
            return 0.0
        
        cos_angle = np.dot(v1, v2) / (norm_v1 * norm_v2)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        return np.arccos(cos_angle)
    
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