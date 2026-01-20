"""
Refinement, clustering, and filtering of corner candidates.
"""

import numpy as np
from typing import List, Dict, Optional
from svg_to_getdp.core.entities.point import Point
from svg_to_getdp.infrastructure.corner_detection.geometric_calculator import GeometricCalculator


class CandidateRefiner:
    """Refines, clusters, and filters corner candidates."""
    
    def __init__(
        self,
        minimum_corner_distance: int = 5,
        corner_strength_threshold: float = 0.45,
        angle_threshold: float = np.pi / 6
    ):
        self.minimum_corner_distance = minimum_corner_distance
        self.corner_strength_threshold = corner_strength_threshold
        self.angle_threshold = angle_threshold
    
    def cluster_nearby_candidates(
        self, 
        outline_points: List[Point], 
        candidates: List[int], 
        debug_data: Dict
    ) -> List[List[int]]:
        """Group nearby candidate corners to avoid duplicates."""
        if not candidates or len(candidates) == 1:
            return [candidates] if candidates else []
        
        # Cluster candidates that are close to each other
        clusters = self._form_candidate_clusters(outline_points, candidates)
        
        debug_data['clustering']['clusters'] = clusters
        
        return clusters
    
    def refine_corner_positions(
        self, 
        outline_points: List[Point], 
        clustered_corners: List[List[int]], 
        debug_data: Dict
    ) -> List[int]:
        """Refine corner positions within each cluster."""
        refined_corners = []
        
        for cluster_index, cluster in enumerate(clustered_corners):
            if not cluster:
                continue
                
            # Select the strongest candidate from the cluster
            candidate_strengths = self._calculate_candidate_strengths(outline_points, cluster)
            best_candidate = max(cluster, key=lambda idx: candidate_strengths.get(idx, 0))
            
            # Refine the corner position
            refined_candidate = self._refine_corner_position(outline_points, best_candidate)
            
            # Record refinement details for debugging
            refinement_detail = self._record_refinement_details(
                cluster, best_candidate, refined_candidate, outline_points, debug_data
            )
            
            if refined_candidate is not None and refinement_detail.get('accepted', False):
                refined_corners.append(refined_candidate)
        
        return refined_corners
    
    def filter_corners_by_strength(self, outline_points: List[Point], corners: List[int]) -> List[int]:
        """Filter out corners that don't meet the strength threshold."""
        candidate_strengths = self._calculate_candidate_strengths(outline_points, corners)
        return [
            idx for idx in corners
            if candidate_strengths.get(idx, 0) >= self.corner_strength_threshold
        ]
    
    def enforce_minimum_corner_spacing(
        self, 
        outline_points: List[Point], 
        corners: List[int], 
        debug_data: Dict
    ) -> List[int]:
        """Ensure corners are spaced at least minimum_corner_distance apart."""
        if len(corners) <= 1:
            return corners
        
        point_count = len(outline_points)
        candidate_strengths = self._calculate_candidate_strengths(outline_points, corners)
        
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
    
    def _form_candidate_clusters(self, outline_points: List[Point], candidates: List[int]) -> List[List[int]]:
        """Group candidates that are within minimum distance of each other."""
        point_count = len(outline_points)
        sorted_candidates = sorted(candidates)
        clusters = []
        current_cluster = [sorted_candidates[0]]
        
        for i in range(1, len(sorted_candidates)):
            previous_idx = sorted_candidates[i-1]
            current_idx = sorted_candidates[i]
            
            # Calculate circular distance along the outline
            distance = min(abs(current_idx - previous_idx), point_count - abs(current_idx - previous_idx))
            
            if distance < self.minimum_corner_distance * 3:
                current_cluster.append(current_idx)
            else:
                clusters.append(current_cluster)
                current_cluster = [current_idx]
        
        if current_cluster:
            clusters.append(current_cluster)
        
        return clusters
    
    def _refine_corner_position(self, outline_points: List[Point], coarse_index: int) -> Optional[int]:
        """
        Refine a corner position by searching locally for the point with maximum interior angle.
        
        Args:
            outline_points: List of outline points
            coarse_index: Initial estimate of corner location
            
        Returns:
            Refined corner index, or None if no good corner found nearby
        """
        point_count = len(outline_points)
        search_radius = min(10, point_count // 20)
        
        best_index = coarse_index
        best_angle = 0.0
        
        # Search within radius for point with maximum interior angle
        for offset in range(-search_radius, search_radius + 1):
            test_index = (coarse_index + offset) % point_count
            angle = GeometricCalculator.calculate_point_angle(outline_points, test_index, 5)
            
            if angle > best_angle:
                best_angle = angle
                best_index = test_index
        
        # Only return if the refined point has a sufficiently large angle
        return best_index if best_angle > self.angle_threshold * 0.5 else None
    
    def _record_refinement_details(
        self,
        cluster: List[int],
        best_candidate: int,
        refined_candidate: Optional[int],
        outline_points: List[Point],
        debug_data: Dict
    ) -> Dict:
        """Record details of the refinement process for debugging."""
        refinement_detail = {
            'cluster': cluster,
            'best_candidate': best_candidate,
            'refined_candidate': refined_candidate
        }
        
        if refined_candidate is not None:
            refined_strength = self._calculate_corner_strength(outline_points, refined_candidate)
            refinement_detail['refined_strength'] = refined_strength
            
            if refined_strength >= self.corner_strength_threshold * 0.8:
                refinement_detail['accepted'] = True
            else:
                refinement_detail['accepted'] = False
        else:
            refinement_detail['accepted'] = False
        
        debug_data['refinement_details'].append(refinement_detail)
        return refinement_detail
    
    def _calculate_corner_strength(self, outline_points: List[Point], point_index: int) -> float:
        """Calculate corner strength (delegates to geometric calculator)."""
        point_count = len(outline_points)
        
        # Angle component
        angle = GeometricCalculator.calculate_point_angle(outline_points, point_index, 7)
        angle_score = min(angle / (np.pi * 0.8), 1.0)
        
        # Curvature contrast component
        x_coordinates = np.array([point.x for point in outline_points])
        y_coordinates = np.array([point.y for point in outline_points])
        
        local_curvature = GeometricCalculator.calculate_local_curvature(
            x_coordinates, y_coordinates, point_index, 5
        )
        
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
        