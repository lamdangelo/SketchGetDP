import numpy as np
from typing import List, Tuple, Optional
import math

from svg_to_getdp.core.entities.bezier_segment import BezierSegment
from sketchgetdp.svg_to_getdp.core.entities.outline import Outline
from svg_to_getdp.core.entities.point import Point
from svg_to_getdp.interfaces.abstractions.bezier_fitter_interface import BezierFitterInterface

class BezierFitter(BezierFitterInterface):
    """
    Fits piecewise Bézier curves to outline points using optimized global least-squares.
    Handles corners as sharp discontinuities and curved regions with smooth continuity.
    """
    
    def __init__(self, bezier_degree: int = 2, minimum_points_per_segment: int = 15):
        self.bezier_degree = bezier_degree
        self.minimum_points_per_segment = minimum_points_per_segment
        
    def fit_outline(self, points: List[Point], corner_indices: List[int], 
                          color, is_closed: bool = True) -> Outline:
        """
        Fit piecewise Bézier curves to outline points, treating corners as segment interfaces.
        
        Args:
            points: Raw outline points to fit curves to
            corner_indices: Indices of corner points that should be segment interfaces
            color: Color for the resulting outline
            is_closed: Whether the outline forms a closed loop
            
        Returns:
            Outline with fitted Bézier segments and corner information
            
        Raises:
            ValueError: When insufficient points are provided
        """
        cleaned_points = self._remove_consecutive_duplicate_points(points)
        if len(cleaned_points) < 3:
            raise ValueError(f"Need at least 3 non-duplicate points for outline, got {len(cleaned_points)}")
            
        optimal_segment_count = self._calculate_optimal_segment_count(cleaned_points, corner_indices)
        bezier_segments = self._fit_piecewise_bezier_curves(
            cleaned_points, corner_indices, optimal_segment_count, is_closed
        )
        
        corner_points = [cleaned_points[idx] for idx in corner_indices] if corner_indices else []
        
        return Outline(
            bezier_segments=bezier_segments,
            corners=corner_points,
            color=color,
            is_closed=is_closed
        )
    
    def _calculate_optimal_segment_count(self, points: List[Point], corner_indices: List[int]) -> int:
        """Calculate appropriate number of segments based on corners and point density."""
        point_count = len(points)
        
        if corner_indices:
            base_segments = max(len(corner_indices), 100)
        else:
            base_segments = max(200, point_count // 10)
            
        minimum_segments = 100
        maximum_segments = min(200, max(1, point_count // 10))
        
        return min(maximum_segments, max(minimum_segments, base_segments))
    
    def _fit_piecewise_bezier_curves(self, points: List[Point], corner_indices: List[int], 
                                   segment_count: int, is_closed: bool) -> List[BezierSegment]:
        """
        Fit Bézier curves with special handling for corner regions and straight edges.
        """
        if not corner_indices:
            return self._fit_continuous_curves_without_corners(points, segment_count, is_closed)
        
        corner_regions = self._identify_corner_regions(points, corner_indices)
        segment_interfaces = self._calculate_segment_interfaces(points, corner_indices, segment_count, is_closed)
        
        fitted_segments = []
        for segment_index in range(len(segment_interfaces) - 1):
            start_index = segment_interfaces[segment_index]
            end_index = segment_interfaces[segment_index + 1]
            segment_points = points[start_index:end_index + 1]
            
            if len(segment_points) < 2:
                continue
                
            segment_type = self._classify_segment_type(
                start_index, end_index, corner_regions, corner_indices, points
            )
            
            if segment_type == "corner_region":
                fitted_segment = self._fit_constrained_corner_segment(segment_points)
            elif segment_type == "straight_edge":
                fitted_segment = self._fit_straight_edge_segment(segment_points)
            else:
                fitted_segment = self._fit_single_bezier_curve(segment_points)
            
            fitted_segments.append(fitted_segment)
        
        self._enforce_segment_continuity(fitted_segments, segment_interfaces, corner_indices, is_closed)
        return fitted_segments
    
    def _fit_single_bezier_curve(self, points: List[Point]) -> BezierSegment:
        """Fit a single Bézier curve to points using least-squares optimization."""
        point_count = len(points)
        
        if point_count <= 3:
            return self._fit_simple_bezier_curve(points)
        
        parameter_values = np.linspace(0, 1, point_count)
        
        # Build Bernstein basis matrix
        basis_matrix = np.zeros((point_count, self.bezier_degree + 1))
        for row, t in enumerate(parameter_values):
            for col in range(self.bezier_degree + 1):
                basis_matrix[row, col] = self._compute_bernstein_basis(col, self.bezier_degree, t)
        
        x_coordinates = np.array([point.x for point in points])
        y_coordinates = np.array([point.y for point in points])
        
        try:
            control_x, _, _, _ = np.linalg.lstsq(basis_matrix, x_coordinates, rcond=None)
            control_y, _, _, _ = np.linalg.lstsq(basis_matrix, y_coordinates, rcond=None)
            
            control_points = [
                Point(float(control_x[i]), float(control_y[i])) 
                for i in range(self.bezier_degree + 1)
            ]
            
            return BezierSegment(control_points=control_points, degree=self.bezier_degree)
            
        except np.linalg.LinAlgError:
            return self._fit_simple_bezier_curve(points)
    
    def _fit_simple_bezier_curve(self, points: List[Point]) -> BezierSegment:
        """Direct Bézier fitting for small point sets or when least-squares fails."""
        point_count = len(points)
        
        if point_count == 1:
            control_points = [points[0]] * (self.bezier_degree + 1)
        elif point_count == 2:
            start_point, end_point = points[0], points[-1]
            control_points = [start_point]
            for i in range(1, self.bezier_degree):
                interpolation_ratio = i / self.bezier_degree
                control_points.append(Point(
                    start_point.x * (1 - interpolation_ratio) + end_point.x * interpolation_ratio,
                    start_point.y * (1 - interpolation_ratio) + end_point.y * interpolation_ratio
                ))
            control_points.append(end_point)
        else:
            if self.bezier_degree == 2:
                start_point, end_point = points[0], points[-1]
                middle_index = len(points) // 2
                middle_point = points[middle_index]
                control_points = [start_point, middle_point, end_point]
            else:
                control_points = [points[0]]
                for i in range(1, self.bezier_degree):
                    index = int((i / self.bezier_degree) * (point_count - 1))
                    control_points.append(points[index])
                control_points.append(points[-1])
        
        return BezierSegment(control_points=control_points, degree=self.bezier_degree)
    
    def _compute_bernstein_basis(self, basis_index: int, degree: int, parameter: float) -> float:
        """Compute Bernstein basis polynomial value."""
        return math.comb(degree, basis_index) * (parameter ** basis_index) * ((1 - parameter) ** (degree - basis_index))
    
    def _remove_consecutive_duplicate_points(self, points: List[Point]) -> List[Point]:
        """Remove consecutive duplicate points from the input list."""
        if not points:
            return []
        
        unique_points = [points[0]]
        for i in range(1, len(points)):
            if points[i] != points[i-1]:
                unique_points.append(points[i])
        
        return unique_points

    def _calculate_segment_interfaces(self, points: List[Point], corner_indices: List[int],
                                   target_segment_count: int, is_closed: bool) -> List[int]:
        """Calculate bezier segment interfaces prioritizing corners while ensuring sufficient segmentation."""
        point_count = len(points)
        
        if point_count < 2:
            return [0]
        
        # Start with corners as primary interfaces
        interfaces = sorted(set(corner_indices))
        
        # Always include the start point
        if 0 not in interfaces:
            interfaces.insert(0, 0)
        
        if is_closed:
            if not interfaces:
                interfaces = [0]
            
            current_segment_count = len(interfaces)
            
            if current_segment_count < target_segment_count:
                additional_interfaces_needed = target_segment_count - current_segment_count
                new_interfaces = set(interfaces)
                
                for i in range(1, additional_interfaces_needed + 1):
                    new_interface_index = int((i * point_count) / (additional_interfaces_needed + 1))
                    # Avoid interfaces too close to existing ones
                    is_too_close = any(abs(new_interface_index - existing) < 5 for existing in new_interfaces)
                    if not is_too_close and new_interface_index < point_count:
                        new_interfaces.add(new_interface_index)
                
                interfaces = sorted(new_interfaces)
        
        else:
            # For open outlines, include the end point
            if (point_count - 1) not in interfaces:
                interfaces.append(point_count - 1)
            
            current_segment_count = len(interfaces) - 1
            
            if current_segment_count < target_segment_count:
                additional_interfaces_needed = target_segment_count - current_segment_count
                
                # Find segments with largest gaps
                segment_gaps = []
                for i in range(len(interfaces) - 1):
                    gap_size = interfaces[i + 1] - interfaces[i]
                    segment_gaps.append((gap_size, i))
                
                segment_gaps.sort(reverse=True)
                
                # Split largest gaps
                for gap_size, gap_index in segment_gaps[:additional_interfaces_needed]:
                    if gap_size > 20:  # Only split substantial gaps
                        midpoint = interfaces[gap_index] + gap_size // 2
                        interfaces.insert(gap_index + 1, midpoint)
        
        # Clean up interfaces
        interfaces = [index for index in interfaces if 0 <= index < point_count]
        interfaces = sorted(set(interfaces))
        
        # Ensure minimum of 2 interfaces for segment creation
        if len(interfaces) < 2:
            if point_count > 1:
                midpoint = point_count // 2
                interfaces = [0, midpoint, point_count - 1] if not is_closed else [0, midpoint]
            else:
                interfaces = [0]
        
        return interfaces

    def _enforce_segment_continuity(self, segments: List[BezierSegment], 
                                  outlines: List[int], corner_indices: List[int],
                                  is_closed: bool):
        """Enforce C0 continuity at all junctions and C1 continuity only at non-corner junctions."""
        if len(segments) < 2:
            return
        
        for segment_index in range(len(segments) - 1):
            current_segment = segments[segment_index]
            next_segment = segments[segment_index + 1]
            junction_index = outlines[segment_index + 1]
            is_corner_junction = junction_index in corner_indices
            
            # Always enforce C0 continuity (position continuity)
            endpoint_gap = current_segment.end_point.distance_to(next_segment.start_point)
            if endpoint_gap > 1e-10:
                adjusted_control_points = next_segment.control_points.copy()
                adjusted_control_points[0] = current_segment.end_point
                segments[segment_index + 1] = BezierSegment(
                    control_points=adjusted_control_points,
                    degree=next_segment.degree
                )
            
            # Only enforce C1 continuity (tangent continuity) at smooth junctions
            if not is_corner_junction and self.bezier_degree == 2:
                self._enforce_tangent_continuity(current_segment, next_segment)
        
        # Handle closure for closed outlines
        if is_closed and len(segments) > 1:
            first_segment_start = segments[0].start_point
            last_segment_end = segments[-1].end_point
            
            closure_gap = last_segment_end.distance_to(first_segment_start)
            if closure_gap > 1e-10:
                adjusted_control_points = segments[-1].control_points.copy()
                adjusted_control_points[-1] = first_segment_start
                segments[-1] = BezierSegment(
                    control_points=adjusted_control_points,
                    degree=segments[-1].degree
                )
                
    def _enforce_tangent_continuity(self, first_segment: BezierSegment, second_segment: BezierSegment):
        """Enforce C1 continuity between two quadratic Bézier segments."""
        if self.bezier_degree != 2:
            return
        
        # For quadratic Bézier curves, C1 continuity requires:
        # first_segment.control_points[2] - first_segment.control_points[1] = 
        # second_segment.control_points[1] - second_segment.control_points[0]
        p0, p1, p2 = first_segment.control_points
        q0, q1, q2 = second_segment.control_points
        
        # Calculate ideal midpoint that satisfies C1 continuity
        ideal_midpoint_x = (p2.x + q0.x) / 2
        ideal_midpoint_y = (p2.y + q0.y) / 2
        
        # Adjust control points toward ideal midpoint
        adjustment_strength = 0.3
        
        adjusted_p1 = Point(
            p1.x * (1 - adjustment_strength) + ideal_midpoint_x * adjustment_strength,
            p1.y * (1 - adjustment_strength) + ideal_midpoint_y * adjustment_strength
        )
        
        adjusted_q1 = Point(
            q1.x * (1 - adjustment_strength) + ideal_midpoint_x * adjustment_strength,
            q1.y * (1 - adjustment_strength) + ideal_midpoint_y * adjustment_strength
        )
        
        first_segment.control_points[1] = adjusted_p1
        second_segment.control_points[1] = adjusted_q1

    def _identify_corner_regions(self, points: List[Point], corner_indices: List[int]) -> List[Tuple[int, int]]:
        """Identify regions around corners that require special constrained fitting."""
        corner_regions = []
        region_radius = min(20, len(points) // 20)
        
        for corner_index in corner_indices:
            region_start = max(0, corner_index - region_radius)
            region_end = min(len(points) - 1, corner_index + region_radius)
            corner_regions.append((region_start, region_end))
        
        return corner_regions
    
    def _classify_segment_type(self, start_index: int, end_index: int, 
                             corner_regions: List[Tuple[int, int]], corner_indices: List[int],
                             points: List[Point]) -> str:
        """
        Classify a segment into one of three types: corner region, straight edge, or curved.
        
        Classification is performed through a multi-stage process:
        1. Check if segment lies entirely within a corner region
        2. Check if segment contains a corner point in its interior
        3. Analyze geometric straightness for final classification
        """
        segment_points = self._extract_segment_points(points, start_index, end_index)
        
        if self._is_within_corner_region(start_index, end_index, corner_regions):
            return "corner_region"
        
        if self._contains_interior_corner(start_index, end_index, corner_indices):
            return "corner_region"
        
        is_connecting_corners = self._is_segment_connecting_corners(start_index, end_index, corner_indices)
        
        return self._determine_segment_type_by_geometry(segment_points, is_connecting_corners)
    
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
        
        Corner points at segment interfaces don't automatically make the segment
        a corner region - they may be part of straight edges.
        """
        for corner_index in corner_indices:
            if start_index < corner_index < end_index:
                return True
        return False
    
    def _determine_segment_type_by_geometry(self, segment_points: List[Point], 
                                          is_connecting_corners: bool) -> str:
        """
        Classify segment based on geometric analysis.
        
        Segments connecting corners are classified as straight edges if geometrically straight.
        Other straight segments are treated as curved for fitting consistency.
        """
        if len(segment_points) < 3:
            return self._classify_short_segment(segment_points, is_connecting_corners)
        
        if self._are_points_geometrically_straight(segment_points):
            return "straight_edge" if is_connecting_corners else "curved"
        
        return "curved"
    
    def _classify_short_segment(self, segment_points: List[Point], 
                              is_connecting_corners: bool) -> str:
        """Handle classification for segments with fewer than 3 points."""
        if is_connecting_corners:
            return "straight_edge"
        return "curved"  # Treat as curved for consistency
    
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
    
    def _are_points_geometrically_straight(self, points: List[Point], 
                                         relative_tolerance: float = 0.005,
                                         absolute_tolerance: float = 1e-6) -> Tuple[bool, float]:
        """
        Determine if points form a straight line within specified tolerances.
        
        Uses multiple geometric checks:
        1. Maximum deviation from ideal line
        2. Angle consistency between consecutive segments
        3. Simplified linear approximation check
        
        Returns both boolean result and confidence score (0-1).
        """
        if len(points) < 3:
            return True, 1.0
        
        max_deviation = self._calculate_max_deviation_from_line(points)
        segment_length = points[0].distance_to(points[-1])
        
        if segment_length == 0:
            return True, 1.0
        
        normalized_deviation = max_deviation / segment_length
        angle_variance = self._calculate_angle_variance(points)
        passes_simplified_check = self._are_points_approximately_linear(points, relative_tolerance)
        
        meets_all_criteria = (
            normalized_deviation < relative_tolerance and
            max_deviation < absolute_tolerance and
            angle_variance < 0.01 and
            passes_simplified_check
        )
        
        confidence = self._calculate_straightness_confidence(
            normalized_deviation, max_deviation, angle_variance, 
            relative_tolerance, absolute_tolerance
        )
        
        return meets_all_criteria, confidence
    
    def _calculate_max_deviation_from_line(self, points: List[Point]) -> float:
        """Find maximum perpendicular distance of any point from the line between endpoints."""
        start_point, end_point = points[0], points[-1]
        max_deviation = 0.0
        
        for point in points:
            deviation = self._calculate_distance_from_line(start_point, end_point, point)
            max_deviation = max(max_deviation, deviation)
        
        return max_deviation
    
    def _calculate_straightness_confidence(self, normalized_deviation: float, 
                                         max_deviation: float, angle_variance: float,
                                         relative_tolerance: float, 
                                         absolute_tolerance: float) -> float:
        """
        Calculate confidence score (0-1) for straightness assessment.
        
        Combines multiple metrics with weighted contributions:
        - 40%: Normalized deviation score
        - 30%: Absolute deviation score  
        - 30%: Angle variance score
        """
        deviation_score = 1.0 - normalized_deviation / max(relative_tolerance, 1e-10)
        absolute_score = 1.0 - max_deviation / max(absolute_tolerance, 1e-10)
        angle_score = 1.0 - angle_variance / 0.01
        
        confidence = (
            deviation_score * 0.4 +
            absolute_score * 0.3 + 
            angle_score * 0.3
        )
        
        return min(1.0, confidence)
    
    def _calculate_angle_variance(self, points: List[Point]) -> float:
        """Calculate variance of angles between consecutive line segments."""
        if len(points) < 3:
            return 0.0
        
        angles = self._collect_segment_angles(points)
        
        if not angles:
            return 0.0
        
        mean_angle = sum(angles) / len(angles)
        variance = sum((angle - mean_angle) ** 2 for angle in angles) / len(angles)
        return variance
    
    def _collect_segment_angles(self, points: List[Point]) -> List[float]:
        """Collect angles between consecutive segments formed by three adjacent points."""
        angles = []
        
        for i in range(1, len(points) - 1):
            angle = self._calculate_angle_at_point(points[i-1], points[i], points[i+1])
            if angle is not None:
                angles.append(angle)
        
        return angles
    
    def _calculate_angle_at_point(self, previous_point: Point, current_point: Point, 
                                next_point: Point) -> Optional[float]:
        """Calculate angle formed by three consecutive points at the middle point."""
        vector_to_previous = Point(current_point.x - previous_point.x, 
                                 current_point.y - previous_point.y)
        vector_to_next = Point(next_point.x - current_point.x, 
                             next_point.y - current_point.y)
        
        dot_product = vector_to_previous.x * vector_to_next.x + vector_to_previous.y * vector_to_next.y
        previous_length = math.sqrt(vector_to_previous.x**2 + vector_to_previous.y**2)
        next_length = math.sqrt(vector_to_next.x**2 + vector_to_next.y**2)
        
        if previous_length < 1e-10 or next_length < 1e-10:
            return None
        
        cosine = max(-1.0, min(1.0, dot_product / (previous_length * next_length)))
        return math.acos(cosine)
    
    def _fit_constrained_corner_segment(self, points: List[Point]) -> BezierSegment:
        """Fit segments in corner regions with heavy constraints to prevent overshooting."""
        if len(points) <= 2:
            return self._fit_simple_bezier_curve(points)
        
        start_point = points[0]
        end_point = points[-1]
        
        if self._are_points_approximately_linear(points):
            # Use midpoint for nearly linear segments
            midpoint = Point((start_point.x + end_point.x) / 2, (start_point.y + end_point.y) / 2)
        else:
            # Find point with maximum deviation and its projection onto the line
            max_deviation_point = self._find_point_with_max_deviation(points, start_point, end_point)
            line_projection = self._project_point_to_line(start_point, end_point, max_deviation_point)
            
            # Blend between actual deviation point and its projection (70% actual, 30% projected) to prevent distortion
            constraint_strength = 0.7
            midpoint = Point(
                max_deviation_point.x * constraint_strength + line_projection.x * (1 - constraint_strength),
                max_deviation_point.y * constraint_strength + line_projection.y * (1 - constraint_strength)
            )
        
        return BezierSegment(control_points=[start_point, midpoint, end_point], degree=2)
    
    def _fit_straight_edge_segment(self, points: List[Point]) -> BezierSegment:
        """Fit segments that are known to be straight edges between corners."""
        start_point = points[0]
        end_point = points[-1]
        midpoint = Point((start_point.x + end_point.x) / 2, (start_point.y + end_point.y) / 2)
        
        return BezierSegment(control_points=[start_point, midpoint, end_point], degree=2)
    
    def _are_points_approximately_linear(self, points: List[Point], max_deviation_ratio: float = 0.01) -> bool:
        """Check if points form an approximately straight line."""
        if len(points) < 3:
            return True
        
        start_point = points[0]
        end_point = points[-1]
        
        max_absolute_deviation = 0
        for point in points:
            deviation = self._calculate_distance_from_line(start_point, end_point, point)
            max_absolute_deviation = max(max_absolute_deviation, deviation)
        
        segment_length = start_point.distance_to(end_point)
        if segment_length == 0:
            return True
        
        normalized_deviation = max_absolute_deviation / segment_length
        return normalized_deviation < max_deviation_ratio
        
    def _find_point_with_max_deviation(self, points: List[Point], line_start: Point, line_end: Point) -> Point:
        """Find the point that deviates most from the line between start and end points."""
        max_deviation = -1
        most_deviant_point = points[len(points) // 2]
        
        for point in points:
            deviation = self._calculate_distance_from_line(line_start, line_end, point)
            if deviation > max_deviation:
                max_deviation = deviation
                most_deviant_point = point
        
        return most_deviant_point

    def _project_point_to_line(self, line_start: Point, line_end: Point, point: Point) -> Point:
        """Project a point onto the line defined by start and end points."""
        line_vector = Point(line_end.x - line_start.x, line_end.y - line_start.y)
        point_vector = Point(point.x - line_start.x, point.y - line_start.y)
        
        line_length_squared = line_vector.x ** 2 + line_vector.y ** 2
        if line_length_squared == 0:
            return line_start
        
        projection_parameter = (point_vector.x * line_vector.x + point_vector.y * line_vector.y) / line_length_squared
        projection_parameter = max(0, min(1, projection_parameter))  # Clamp to segment
        
        return Point(
            line_start.x + projection_parameter * line_vector.x,
            line_start.y + projection_parameter * line_vector.y
        )

    def _calculate_distance_from_line(self, line_point1: Point, line_point2: Point, test_point: Point) -> float:
        """Calculate perpendicular distance from a point to a line."""
        if line_point1 == line_point2:
            return line_point1.distance_to(test_point)
        
        # Using cross product formula: |(p2 - p1) × (p - p1)| / |p2 - p1|
        cross_product = abs(
            (line_point2.x - line_point1.x) * (test_point.y - line_point1.y) - 
            (line_point2.y - line_point1.y) * (test_point.x - line_point1.x)
        )
        line_length = line_point1.distance_to(line_point2)
        
        return cross_product / line_length if line_length > 0 else 0

    def _fit_continuous_curves_without_corners(self, points: List[Point], segment_count: int, 
                                             is_closed: bool) -> List[BezierSegment]:
        """Fallback method for fitting curves when no corner points are provided."""
        point_count = len(points)
        segments = []
        
        # Create evenly distributed segment interfaces
        points_per_segment = max(1, point_count // segment_count)
        outlines = [i * points_per_segment for i in range(segment_count)]
        outlines.append(point_count - 1)
        
        # Fit each segment independently
        for segment_index in range(segment_count):
            start_index = outlines[segment_index]
            end_index = outlines[segment_index + 1]
            segment_points = points[start_index:end_index + 1]
            
            if len(segment_points) >= 2:
                segment = self._fit_single_bezier_curve(segment_points)
                segments.append(segment)
        
        # Enforce continuity between segments
        for i in range(len(segments) - 1):
            current_segment = segments[i]
            next_segment = segments[i + 1]
            
            # Ensure C0 continuity
            endpoint_gap = current_segment.end_point.distance_to(next_segment.start_point)
            if endpoint_gap > 1e-10:
                adjusted_control_points = next_segment.control_points.copy()
                adjusted_control_points[0] = current_segment.end_point
                segments[i + 1] = BezierSegment(
                    control_points=adjusted_control_points,
                    degree=next_segment.degree
                )
            
            # Enforce C1 continuity for quadratic curves
            if self.bezier_degree == 2:
                self._enforce_tangent_continuity(segments[i], segments[i + 1])
        
        # Handle closure for closed outlines
        if is_closed and len(segments) > 1:
            self._ensure_outline_closure(segments)
            
            # Enforce C1 continuity between last and first segment
            if self.bezier_degree == 2 and len(segments) > 1:
                self._enforce_tangent_continuity(segments[-1], segments[0])
        
        return segments

    def _ensure_outline_closure(self, segments: List[BezierSegment]):
        """Ensure the first and last points of a closed outline match exactly."""
        if not segments:
            return
        
        first_segment_start = segments[0].start_point
        last_segment = segments[-1]
        
        closure_gap = last_segment.end_point.distance_to(first_segment_start)
        if closure_gap > 1e-10:
            adjusted_control_points = last_segment.control_points.copy()
            adjusted_control_points[-1] = first_segment_start
            segments[-1] = BezierSegment(
                control_points=adjusted_control_points,
                degree=last_segment.degree
            )