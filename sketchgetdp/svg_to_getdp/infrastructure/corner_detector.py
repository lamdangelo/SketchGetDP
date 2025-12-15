import numpy as np
from typing import List, Optional, Tuple, Dict
from ..core.entities.point import Point
from ..interfaces.abstractions.corner_detector_interface import CornerDetectorInterface


class CornerDetector(CornerDetectorInterface):
    """
    Enhanced corner detector with improved handling for complex shapes like crosses.
    Returns structured debug data along with corner indices.
    
    The detector uses multiple complementary methods to identify corners:
    1. Local angle analysis
    2. Direction change detection
    3. Curvature peak analysis
    
    Results are combined, clustered, refined, and filtered to produce final corner points.
    """
    
    def __init__(
        self, 
        window_size: int = 15, 
        direction_change_threshold: float = 0.8, 
        angle_threshold: float = np.pi / 6,
        minimum_corner_distance: int = 5,
        smoothness_threshold: float = 0.72,
        corner_strength_threshold: float = 0.45,
        ellipse_aspect_ratio_threshold: float = 1.2,
        debug_enabled: bool = True
    ):
        """
        Initialize the corner detector with configurable parameters.
        
        Args:
            window_size: Size of the analysis window for direction vectors
            direction_change_threshold: Minimum angle change (radians) to consider a direction change
            angle_threshold: Minimum interior angle (radians) to qualify as a corner
            minimum_corner_distance: Minimum distance between detected corners (pixels)
            smoothness_threshold: Threshold for detecting smooth/elliptical shapes
            corner_strength_threshold: Minimum strength score for a valid corner
            ellipse_aspect_ratio_threshold: Maximum aspect ratio for ellipse detection
            debug_enabled: Whether to collect and return debug information
        """
        self.window_size = window_size
        self.direction_change_threshold = direction_change_threshold
        self.angle_threshold = angle_threshold
        self.minimum_corner_distance = minimum_corner_distance
        self.smoothness_threshold = smoothness_threshold
        self.corner_strength_threshold = corner_strength_threshold
        self.ellipse_aspect_ratio_threshold = ellipse_aspect_ratio_threshold
        self.debug_enabled = debug_enabled
    
    def detect_corners(self, boundary_points: List[Point]) -> Tuple[List[int], Dict]:
        """
        Identifies indices of corner points in the boundary point sequence.
        
        The detection process involves:
        1. Early shape analysis (ellipse/smooth shape detection)
        2. Candidate detection using multiple methods
        3. Strength calculation for each candidate
        4. Clustering of nearby candidates
        5. Refinement of corner positions
        6. Final filtering and spacing enforcement
        
        Args:
            boundary_points: List of ordered points representing a closed boundary
            
        Returns:
            Tuple containing:
                - List of corner indices in the boundary_points list
                - Dictionary containing debug information if debug_enabled is True
        """
        debug_data = self._initialize_debug_data()
        self._record_debug_step(debug_data, f"Starting corner detection for {len(boundary_points)} boundary points")
        
        # Early return for shapes that are likely ellipses or too smooth
        if self._should_skip_corner_detection(boundary_points, debug_data):
            return [], debug_data
        
        # Convert points to coordinate arrays for efficient computation
        x_coordinates = np.array([point.x for point in boundary_points])
        y_coordinates = np.array([point.y for point in boundary_points])
        
        self._record_bounding_box_info(x_coordinates, y_coordinates, debug_data)
        
        # Step 1: Detect candidate corners using multiple complementary methods
        candidate_corners = self._detect_candidate_corners(boundary_points, x_coordinates, y_coordinates, debug_data)
        
        if not candidate_corners:
            self._record_debug_step(debug_data, "No strong corners found: returning empty list")
            return [], debug_data
        
        # Step 2: Cluster nearby candidates to avoid duplicates
        clustered_corners = self._cluster_nearby_candidates(boundary_points, candidate_corners, debug_data)
        
        # Step 3: Refine corner positions within each cluster
        refined_corners = self._refine_corner_positions(boundary_points, clustered_corners, debug_data)
        
        # Step 4: Filter corners by strength
        strong_corners = self._filter_corners_by_strength(boundary_points, refined_corners)
        
        # Step 5: Ensure minimum spacing between corners
        final_corners = self._enforce_minimum_corner_spacing(boundary_points, strong_corners, debug_data)
        
        self._record_final_results(boundary_points, final_corners, debug_data)
        self._record_debug_step(debug_data, f"Final result: {len(final_corners)} corners detected")
        
        return sorted(final_corners), debug_data
    
    # ==================== Helper Methods ====================
    
    def _initialize_debug_data(self) -> Dict:
        """Initialize the debug data structure."""
        return {
            'shape_analysis': {},
            'candidate_detection': {},
            'strength_calculations': {},
            'clustering': {},
            'refinement_details': [],
            'final_decisions': {},
            'all_steps': []
        }
    
    def _record_debug_step(self, debug_data: Dict, message: str) -> None:
        """Record a debug step if debugging is enabled."""
        if self.debug_enabled:
            debug_data['all_steps'].append(message)
    
    def _should_skip_corner_detection(self, boundary_points: List[Point], debug_data: Dict) -> bool:
        """
        Check if the shape is likely an ellipse or too smooth for corner detection.
        
        Returns True if corner detection should be skipped for this shape.
        """
        point_count = len(boundary_points)
        
        # Early ellipse detection for small shapes
        if point_count < 100 and self._is_likely_small_ellipse(boundary_points):
            debug_data['shape_analysis']['early_ellipse_detection'] = True
            debug_data['shape_analysis']['ellipse_reason'] = "Small shape with ellipse-like properties"
            self._record_debug_step(debug_data, "Early ellipse detection: returning no corners")
            return True
        
        # Enhanced smoothness check for larger shapes
        if point_count > 30:
            smoothness_score, is_ellipse = self._calculate_shape_smoothness(boundary_points)
            
            debug_data['shape_analysis']['smoothness_score'] = smoothness_score
            debug_data['shape_analysis']['is_ellipse'] = is_ellipse
            
            if is_ellipse:
                debug_data['shape_analysis']['ellipse_reason'] = "Enhanced smoothness detection"
                self._record_debug_step(debug_data, 
                    f"Ellipse detection (smoothness={smoothness_score:.3f}): returning no corners")
                return True
            
            if smoothness_score > self.smoothness_threshold:
                debug_data['shape_analysis']['too_smooth'] = True
                self._record_debug_step(debug_data,
                    f"Too smooth (score={smoothness_score:.3f} > threshold={self.smoothness_threshold}): returning no corners")
                return True
        
        # Check if shape is too small for reliable corner detection
        if point_count < self.window_size * 2:
            debug_data['shape_analysis']['too_small'] = True
            self._record_debug_step(debug_data, f"Shape too small: {point_count} points")
            
            if point_count < 30 and self._is_likely_small_ellipse(boundary_points):
                debug_data['shape_analysis']['small_ellipse'] = True
                self._record_debug_step(debug_data, "Small shape detected as ellipse: returning no corners")
                return True
            
            return True
        
        return False
    
    def _record_bounding_box_info(self, x_coordinates: np.ndarray, y_coordinates: np.ndarray, debug_data: Dict) -> None:
        """Record bounding box information for debugging."""
        debug_data['shape_analysis']['bounding_box'] = {
            'x_min': float(np.min(x_coordinates)),
            'x_max': float(np.max(x_coordinates)),
            'y_min': float(np.min(y_coordinates)),
            'y_max': float(np.max(y_coordinates)),
            'width': float(np.max(x_coordinates) - np.min(x_coordinates)),
            'height': float(np.max(y_coordinates) - np.min(y_coordinates))
        }
    
    def _detect_candidate_corners(
        self, 
        boundary_points: List[Point], 
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
        angle_based_corners = self._detect_corners_by_local_angle(boundary_points)
        direction_based_corners = self._detect_corners_by_direction_change(x_coordinates, y_coordinates)
        curvature_based_corners = self._detect_corners_by_curvature_peaks(x_coordinates, y_coordinates)
        
        # Record detection results for debugging
        debug_data['candidate_detection'] = {
            'angle_method': angle_based_corners,
            'direction_method': direction_based_corners,
            'curvature_method': curvature_based_corners,
            'all_candidates': list(set(angle_based_corners + direction_based_corners + curvature_based_corners))
        }
        
        self._record_debug_step(debug_data, f"Angle method found {len(angle_based_corners)} corners")
        self._record_debug_step(debug_data, f"Direction method found {len(direction_based_corners)} corners")
        self._record_debug_step(debug_data, f"Curvature method found {len(curvature_based_corners)} corners")
        
        # Calculate strength for all candidates
        all_candidates = debug_data['candidate_detection']['all_candidates']
        candidate_strengths = self._calculate_candidate_strengths(boundary_points, all_candidates)
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
        self._record_debug_step(debug_data, f"After filtering: {len(strong_candidates)} strong candidates")
        
        return strong_candidates
    
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
    
    def _cluster_nearby_candidates(
        self, 
        boundary_points: List[Point], 
        candidates: List[int], 
        debug_data: Dict
    ) -> List[List[int]]:
        """Group nearby candidate corners to avoid duplicates."""
        if not candidates or len(candidates) == 1:
            return [candidates] if candidates else []
        
        # Calculate candidate strengths for clustering decisions
        candidate_strengths = self._calculate_candidate_strengths(boundary_points, candidates)
        
        # Cluster candidates that are close to each other
        clusters = self._form_candidate_clusters(boundary_points, candidates)
        
        debug_data['clustering']['clusters'] = clusters
        self._record_debug_step(debug_data, f"Clustering created {len(clusters)} candidate clusters")
        
        return clusters
    
    def _form_candidate_clusters(self, boundary_points: List[Point], candidates: List[int]) -> List[List[int]]:
        """Group candidates that are within minimum distance of each other."""
        point_count = len(boundary_points)
        sorted_candidates = sorted(candidates)
        clusters = []
        current_cluster = [sorted_candidates[0]]
        
        for i in range(1, len(sorted_candidates)):
            previous_idx = sorted_candidates[i-1]
            current_idx = sorted_candidates[i]
            
            # Calculate circular distance along the boundary
            distance = min(abs(current_idx - previous_idx), point_count - abs(current_idx - previous_idx))
            
            if distance < self.minimum_corner_distance * 3:
                current_cluster.append(current_idx)
            else:
                clusters.append(current_cluster)
                current_cluster = [current_idx]
        
        if current_cluster:
            clusters.append(current_cluster)
        
        return clusters
    
    def _refine_corner_positions(
        self, 
        boundary_points: List[Point], 
        clustered_corners: List[List[int]], 
        debug_data: Dict
    ) -> List[int]:
        """Refine corner positions within each cluster."""
        refined_corners = []
        
        for cluster_index, cluster in enumerate(clustered_corners):
            if not cluster:
                continue
                
            # Select the strongest candidate from the cluster
            candidate_strengths = self._calculate_candidate_strengths(boundary_points, cluster)
            best_candidate = max(cluster, key=lambda idx: candidate_strengths.get(idx, 0))
            
            # Refine the corner position
            refined_candidate = self._refine_corner_position(boundary_points, best_candidate)
            
            # Record refinement details for debugging
            refinement_detail = self._record_refinement_details(
                cluster, best_candidate, refined_candidate, boundary_points, debug_data
            )
            
            if refined_candidate is not None and refinement_detail.get('accepted', False):
                refined_corners.append(refined_candidate)
        
        return refined_corners
    
    def _record_refinement_details(
        self,
        cluster: List[int],
        best_candidate: int,
        refined_candidate: Optional[int],
        boundary_points: List[Point],
        debug_data: Dict
    ) -> Dict:
        """Record details of the refinement process for debugging."""
        refinement_detail = {
            'cluster': cluster,
            'best_candidate': best_candidate,
            'refined_candidate': refined_candidate
        }
        
        if refined_candidate is not None:
            refined_strength = self._calculate_corner_strength(boundary_points, refined_candidate)
            refinement_detail['refined_strength'] = refined_strength
            
            if refined_strength >= self.corner_strength_threshold * 0.8:
                refinement_detail['accepted'] = True
                self._record_debug_step(debug_data,
                    f"Cluster accepted: refined {best_candidate} → {refined_candidate} (strength={refined_strength:.3f})")
            else:
                refinement_detail['accepted'] = False
                self._record_debug_step(debug_data,
                    f"Cluster rejected: refined {best_candidate} → {refined_candidate} (strength={refined_strength:.3f} < threshold)")
        else:
            refinement_detail['accepted'] = False
            self._record_debug_step(debug_data, f"Cluster: candidate {best_candidate} could not be refined")
        
        debug_data['refinement_details'].append(refinement_detail)
        return refinement_detail
    
    def _filter_corners_by_strength(self, boundary_points: List[Point], corners: List[int]) -> List[int]:
        """Filter out corners that don't meet the strength threshold."""
        return [
            idx for idx in corners
            if self._calculate_corner_strength(boundary_points, idx) >= self.corner_strength_threshold
        ]
    
    def _enforce_minimum_corner_spacing(
        self, 
        boundary_points: List[Point], 
        corners: List[int], 
        debug_data: Dict
    ) -> List[int]:
        """Ensure corners are spaced at least minimum_corner_distance apart."""
        if len(corners) <= 1:
            return corners
        
        point_count = len(boundary_points)
        candidate_strengths = self._calculate_candidate_strengths(boundary_points, corners)
        
        sorted_corners = sorted(corners)
        well_spaced_corners = []
        
        i = 0
        while i < len(sorted_corners):
            current_corner = sorted_corners[i]
            well_spaced_corners.append(current_corner)
            
            # Skip any corners that are too close to the current one
            j = i + 1
            while j < len(sorted_corners):
                next_corner = sorted_corners[j]
                distance = min(abs(next_corner - current_corner),
                             point_count - abs(next_corner - current_corner))
                
                if distance < self.minimum_corner_distance:
                    # Keep the stronger corner when two are too close
                    current_strength = candidate_strengths.get(current_corner, 0)
                    next_strength = candidate_strengths.get(next_corner, 0)
                    
                    if next_strength > current_strength * 1.1:
                        well_spaced_corners[-1] = next_corner
                        current_corner = next_corner
                    
                    j += 1
                else:
                    break
            
            i = j
        
        debug_data['clustering']['refined_corners'] = corners
        debug_data['clustering']['quality_corners'] = well_spaced_corners
        
        return sorted(well_spaced_corners)
    
    def _record_final_results(
        self, 
        boundary_points: List[Point], 
        final_corners: List[int], 
        debug_data: Dict
    ) -> None:
        """Record final corner detection results for debugging."""
        candidate_strengths = self._calculate_candidate_strengths(boundary_points, final_corners)
        
        debug_data['final_decisions']['final_corners'] = final_corners
        debug_data['final_decisions']['corner_coordinates'] = {
            idx: boundary_points[idx] for idx in final_corners
        }
        debug_data['final_decisions']['corner_strengths'] = {
            idx: candidate_strengths.get(idx, 0) for idx in final_corners
        }
    
    # ==================== Geometric Calculations ====================
    
    def _calculate_shape_smoothness(self, boundary_points: List[Point]) -> Tuple[float, bool]:
        """
        Calculate a smoothness score for the shape and detect if it's ellipse-like.
        
        Returns:
            Tuple containing:
                - Smoothness score (higher = smoother)
                - Boolean indicating if shape is likely an ellipse
        """
        point_count = len(boundary_points)
        
        x_coordinates = np.array([point.x for point in boundary_points])
        y_coordinates = np.array([point.y for point in boundary_points])
        
        # Calculate curvatures at sample points
        curvatures = self._calculate_sampled_curvatures(x_coordinates, y_coordinates, point_count)
        
        # Check if shape is ellipse-like
        is_ellipse = self._is_shape_ellipse_like(boundary_points, curvatures)
        
        # Calculate angles at sample points
        angles = self._calculate_sampled_angles(boundary_points, point_count)
        
        # Compute smoothness score from angle and curvature statistics
        smoothness_score = self._compute_smoothness_score(angles, curvatures)
        
        return smoothness_score, is_ellipse
    
    def _calculate_sampled_curvatures(
        self, 
        x_coordinates: np.ndarray, 
        y_coordinates: np.ndarray, 
        point_count: int
    ) -> List[float]:
        """Calculate curvatures at regularly sampled points along the boundary."""
        sample_step = max(1, point_count // 50)
        curvatures = []
        
        for i in range(0, point_count, sample_step):
            curvature = self._calculate_local_curvature(x_coordinates, y_coordinates, i, 5)
            curvatures.append(curvature)
        
        return curvatures
    
    def _calculate_sampled_angles(self, boundary_points: List[Point], point_count: int) -> List[float]:
        """Calculate angles at regularly sampled points along the boundary."""
        sample_step = max(1, point_count // 50)
        angles = []
        
        for i in range(0, point_count, sample_step):
            angle = self._calculate_point_angle(boundary_points, i, 7)
            angles.append(angle)
        
        return angles
    
    def _compute_smoothness_score(self, angles: List[float], curvatures: List[float]) -> float:
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
    
    def _is_shape_ellipse_like(self, boundary_points: List[Point], curvatures: List[float]) -> bool:
        """Determine if the shape is likely an ellipse based on curvature consistency."""
        point_count = len(boundary_points)
        
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
        x_coordinates = np.array([point.x for point in boundary_points])
        y_coordinates = np.array([point.y for point in boundary_points])
        
        center_x = np.mean(x_coordinates)
        center_y = np.mean(y_coordinates)
        
        distances = np.sqrt((x_coordinates - center_x)**2 + (y_coordinates - center_y)**2)
        distance_mean = np.mean(distances)
        
        if distance_mean > 0:
            distance_variation = np.std(distances) / distance_mean
            if distance_variation < 0.2:
                return True
        
        return False
    
    def _is_likely_small_ellipse(self, boundary_points: List[Point]) -> bool:
        """Check if a small shape is likely an ellipse."""
        point_count = len(boundary_points)
        
        if point_count < 10:
            return False
        
        x_coordinates = np.array([point.x for point in boundary_points])
        y_coordinates = np.array([point.y for point in boundary_points])
        
        width = np.max(x_coordinates) - np.min(x_coordinates)
        height = np.max(y_coordinates) - np.min(y_coordinates)
        
        # Check curvature consistency
        curvatures = []
        sample_step = max(1, point_count // 20)
        for i in range(0, point_count, sample_step):
            curvature = self._calculate_local_curvature(x_coordinates, y_coordinates, i, 3)
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
    
    def _calculate_point_angle(self, boundary_points: List[Point], point_index: int, window_size: int) -> float:
        """
        Calculate the interior angle at a specific boundary point.
        
        Uses vectors to previous and next points to compute the angle.
        """
        point_count = len(boundary_points)
        
        previous_index = (point_index - window_size) % point_count
        next_index = (point_index + window_size) % point_count
        
        # Vector from previous point to current point
        vector_to_current = np.array([
            boundary_points[point_index].x - boundary_points[previous_index].x,
            boundary_points[point_index].y - boundary_points[previous_index].y
        ])
        
        # Vector from current point to next point
        vector_from_current = np.array([
            boundary_points[next_index].x - boundary_points[point_index].x,
            boundary_points[next_index].y - boundary_points[point_index].y
        ])
        
        vector_to_current_norm = np.linalg.norm(vector_to_current)
        vector_from_current_norm = np.linalg.norm(vector_from_current)
        
        if vector_to_current_norm > 1e-8 and vector_from_current_norm > 1e-8:
            cosine_angle = np.dot(vector_to_current, vector_from_current) / (vector_to_current_norm * vector_from_current_norm)
            cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
            return np.arccos(cosine_angle)
        
        return 0.0
    
    def _calculate_local_curvature(
        self, 
        x_coordinates: np.ndarray, 
        y_coordinates: np.ndarray, 
        point_index: int, 
        window_size: int
    ) -> float:
        """
        Calculate the curvature at a specific point along the boundary.
        
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
    
    def _detect_corners_by_local_angle(self, boundary_points: List[Point]) -> List[int]:
        """Detect corners by analyzing local interior angles at each point."""
        point_count = len(boundary_points)
        if point_count < 10:
            return []
        
        angle_window = max(3, min(10, point_count // 50))
        angle_threshold = self.angle_threshold * 0.8
        
        corners = []
        
        for i in range(point_count):
            angle = self._calculate_point_angle(boundary_points, i, angle_window)
            if angle > angle_threshold:
                corners.append(i)
        
        return corners
    
    def _detect_corners_by_direction_change(
        self, 
        x_coordinates: np.ndarray, 
        y_coordinates: np.ndarray
    ) -> List[int]:
        """Detect corners by analyzing changes in direction along the boundary."""
        point_count = len(x_coordinates)
        if point_count < self.window_size * 2:
            return []
        
        corners = []
        
        for i in range(point_count):
            # Compute direction vectors before and after the point
            previous_direction = self._compute_direction_vector(
                x_coordinates, y_coordinates, i, self.window_size, backward=True
            )
            next_direction = self._compute_direction_vector(
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
    
    def _compute_direction_vector(
        self, 
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
        
        # Extract coordinates from the window (handling circular boundary)
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
            curvature = self._calculate_local_curvature(x_coordinates, y_coordinates, i, curvature_window)
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
    
    def _calculate_corner_strength(self, boundary_points: List[Point], point_index: int) -> float:
        """
        Calculate a strength score (0-1) for a potential corner.
        
        Combines:
        1. Interior angle (larger angles are stronger corners)
        2. Local curvature contrast (corners should stand out from neighbors)
        """
        point_count = len(boundary_points)
        
        # Angle component: corners have larger interior angles
        angle = self._calculate_point_angle(boundary_points, point_index, 7)
        angle_score = min(angle / (np.pi * 0.8), 1.0)
        
        # Curvature contrast component: corners should have higher curvature than neighbors
        x_coordinates = np.array([point.x for point in boundary_points])
        y_coordinates = np.array([point.y for point in boundary_points])
        
        local_curvature = self._calculate_local_curvature(x_coordinates, y_coordinates, point_index, 5)
        
        # Compare with neighboring curvatures
        neighbor_window = min(10, point_count // 20)
        neighbor_curvatures = []
        
        for offset in range(-neighbor_window, neighbor_window + 1):
            if offset != 0:
                neighbor_index = (point_index + offset) % point_count
                curvature = self._calculate_local_curvature(x_coordinates, y_coordinates, neighbor_index, 5)
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
        boundary_points: List[Point], 
        candidate_indices: List[int]
    ) -> Dict[int, float]:
        """Calculate strength scores for multiple candidate corners."""
        return {
            idx: self._calculate_corner_strength(boundary_points, idx)
            for idx in candidate_indices
        }
    
    def _refine_corner_position(self, boundary_points: List[Point], coarse_index: int) -> Optional[int]:
        """
        Refine a corner position by searching locally for the point with maximum interior angle.
        
        Args:
            boundary_points: List of boundary points
            coarse_index: Initial estimate of corner location
            
        Returns:
            Refined corner index, or None if no good corner found nearby
        """
        point_count = len(boundary_points)
        search_radius = min(10, point_count // 20)
        
        best_index = coarse_index
        best_angle = 0.0
        
        # Search within radius for point with maximum interior angle
        for offset in range(-search_radius, search_radius + 1):
            test_index = (coarse_index + offset) % point_count
            angle = self._calculate_point_angle(boundary_points, test_index, 5)
            
            if angle > best_angle:
                best_angle = angle
                best_index = test_index
        
        # Only return if the refined point has a sufficiently large angle
        return best_index if best_angle > self.angle_threshold * 0.5 else None