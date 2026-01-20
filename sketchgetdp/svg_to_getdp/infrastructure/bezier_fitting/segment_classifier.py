from typing import List, Tuple
from svg_to_getdp.core.entities.point import Point


class SegmentClassifier:
    """
    Classifies segments into corner regions, straight edges, or curved segments.
    """
    
    def __init__(self, relative_tolerance: float = 0.005, absolute_tolerance: float = 1e-6):
        self.relative_tolerance = relative_tolerance
        self.absolute_tolerance = absolute_tolerance
    
    def classify_segment_type(self, start_index: int, end_index: int, 
                            corner_regions: List[Tuple[int, int]], 
                            corner_indices: List[int],
                            points: List[Point]) -> str:
        """
        Classify a segment into one of three types: corner region, straight edge, or curved.
        """
        segment_points = self._extract_segment_points(points, start_index, end_index)
        
        if self._is_within_corner_region(start_index, end_index, corner_regions):
            return "corner_region"
        
        if self._contains_interior_corner(start_index, end_index, corner_indices):
            return "corner_region"
        
        is_connecting_corners = self._is_segment_connecting_corners(start_index, end_index, corner_indices)
        
        return self._determine_segment_type_by_geometry(segment_points, is_connecting_corners)
    
    def identify_corner_regions(self, points: List[Point], corner_indices: List[int]) -> List[Tuple[int, int]]:
        """Identify regions around corners that require special constrained fitting."""
        corner_regions = []
        region_radius = min(20, len(points) // 20)
        
        for corner_index in corner_indices:
            region_start = max(0, corner_index - region_radius)
            region_end = min(len(points) - 1, corner_index + region_radius)
            corner_regions.append((region_start, region_end))
        
        return corner_regions
    
    def _extract_segment_points(self, points: List[Point], start_index: int, end_index: int) -> List[Point]:
        """Extract points belonging to a segment from the complete point list."""
        return points[start_index:end_index + 1]
    
    def _is_within_corner_region(self, start_index: int, end_index: int, 
                                corner_regions: List[Tuple[int, int]]) -> bool:
        """Check if segment lies completely within any corner region."""
        for region_start, region_end in corner_regions:
            if start_index >= region_start and end_index <= region_end:
                return True
        return False
    
    def _contains_interior_corner(self, start_index: int, end_index: int, 
                                 corner_indices: List[int]) -> bool:
        """
        Check if segment contains a corner point that is not at its outline.
        """
        for corner_index in corner_indices:
            if start_index < corner_index < end_index:
                return True
        return False
    
    def _determine_segment_type_by_geometry(self, segment_points: List[Point], 
                                          is_connecting_corners: bool) -> str:
        """
        Classify segment based on geometric analysis.
        """
        if len(segment_points) < 3:
            return self._classify_short_segment(segment_points, is_connecting_corners)
        
        # Import here to avoid circular imports
        from svg_to_getdp.infrastructure.bezier_fitting.bezier_calculator import BezierCalculator
        bezier_calculator = BezierCalculator()
        
        straight, _ = bezier_calculator.are_points_geometrically_straight(
            segment_points, self.relative_tolerance, self.absolute_tolerance
        )
        
        if straight:
            return "straight_edge" if is_connecting_corners else "curved"
        
        return "curved"
    
    def _classify_short_segment(self, segment_points: List[Point], 
                              is_connecting_corners: bool) -> str:
        """Handle classification for segments with fewer than 3 points."""
        if is_connecting_corners:
            return "straight_edge"
        return "curved"
    
    def _is_segment_connecting_corners(self, start_index: int, end_index: int, 
                                     corner_indices: List[int]) -> bool:
        """Check if segment endpoints are consecutive corner points."""
        sorted_corners = sorted(corner_indices)
        
        # Check for consecutive corners in sequence
        for i in range(len(sorted_corners) - 1):
            if start_index == sorted_corners[i] and end_index == sorted_corners[i + 1]:
                return True
        
        # Check for closure connection (last to first corner)
        if len(sorted_corners) > 1:
            if start_index == sorted_corners[-1] and end_index == sorted_corners[0]:
                return True
        
        return False
    