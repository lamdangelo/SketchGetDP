import numpy as np
from typing import List, Tuple
import math

from ..core.entities.bezier_segment import BezierSegment
from ..core.entities.boundary_curve import BoundaryCurve
from ..core.entities.point import Point
from ..interfaces.abstractions.bezier_fitter_interface import BezierFitterInterface

class BezierFitter(BezierFitterInterface):
    """
    Fits piecewise Bézier curves to boundary points using optimized global least-squares.
    Handles corners as sharp discontinuities and curved regions with smooth continuity.
    """
    
    def __init__(self, bezier_degree: int = 2, minimum_points_per_segment: int = 15):
        self.bezier_degree = bezier_degree
        self.minimum_points_per_segment = minimum_points_per_segment
        
    def fit_boundary_curve(self, points: List[Point], corner_indices: List[int], 
                          color, is_closed: bool = True) -> BoundaryCurve:
        """
        Fit piecewise Bézier curves to boundary points, treating corners as segment boundaries.
        
        Args:
            points: Raw boundary points to fit curves to
            corner_indices: Indices of corner points that should be segment boundaries
            color: Color for the resulting boundary curve
            is_closed: Whether the curve forms a closed loop
            
        Returns:
            BoundaryCurve with fitted Bézier segments and corner information
            
        Raises:
            ValueError: When insufficient points are provided
        """
        cleaned_points = self._remove_consecutive_duplicate_points(points)
        if len(cleaned_points) < 3:
            raise ValueError(f"Need at least 3 non-duplicate points for boundary curve, got {len(cleaned_points)}")
            
        optimal_segment_count = self._calculate_optimal_segment_count(cleaned_points, corner_indices)
        bezier_segments = self._fit_piecewise_bezier_curves(
            cleaned_points, corner_indices, optimal_segment_count, is_closed
        )
        
        corner_points = [cleaned_points[idx] for idx in corner_indices] if corner_indices else []
        
        return BoundaryCurve(
            bezier_segments=bezier_segments,
            corners=corner_points,
            color=color,
            is_closed=is_closed
        )
    
    def _calculate_optimal_segment_count(self, points: List[Point], corner_indices: List[int]) -> int:
        """Calculate appropriate number of segments based on corners and point density."""
        point_count = len(points)
        
        if corner_indices:
            base_segments = max(len(corner_indices), 20)
        else:
            base_segments = max(100, point_count // 30)
            
        minimum_segments = 20
        maximum_segments = min(100, point_count // 10)
        
        return min(maximum_segments, max(minimum_segments, base_segments))
    
    def _fit_piecewise_bezier_curves(self, points: List[Point], corner_indices: List[int], 
                                   segment_count: int, is_closed: bool) -> List[BezierSegment]:
        """
        Fit Bézier curves with special handling for corner regions and straight edges.
        """
        if not corner_indices:
            return self._fit_continuous_curves_without_corners(points, segment_count, is_closed)
        
        corner_regions = self._identify_corner_regions(points, corner_indices)
        segment_boundaries = self._calculate_segment_boundaries(points, corner_indices, segment_count, is_closed)
        
        fitted_segments = []
        for segment_index in range(len(segment_boundaries) - 1):
            start_index = segment_boundaries[segment_index]
            end_index = segment_boundaries[segment_index + 1]
            segment_points = points[start_index:end_index + 1]
            
            if len(segment_points) < 2:
                continue
                
            segment_type = self._classify_segment_type(start_index, end_index, corner_regions, corner_indices)
            
            if segment_type == "corner_region":
                fitted_segment = self._fit_constrained_corner_segment(segment_points)
            elif segment_type == "straight_edge":
                fitted_segment = self._fit_straight_edge_segment(segment_points)
            else:
                fitted_segment = self._fit_single_bezier_curve(segment_points)
            
            fitted_segments.append(fitted_segment)
        
        self._enforce_segment_continuity(fitted_segments, segment_boundaries, corner_indices, is_closed)
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

    def _calculate_segment_boundaries(self, points: List[Point], corner_indices: List[int],
                                   target_segment_count: int, is_closed: bool) -> List[int]:
        """Calculate segment boundaries prioritizing corners while ensuring sufficient segmentation."""
        point_count = len(points)
        
        if point_count < 2:
            return [0]
        
        # Start with corners as primary boundaries
        boundaries = sorted(set(corner_indices))
        
        # Always include the start point
        if 0 not in boundaries:
            boundaries.insert(0, 0)
        
        if is_closed:
            if not boundaries:
                boundaries = [0]
            
            current_segment_count = len(boundaries)
            
            if current_segment_count < target_segment_count:
                additional_boundaries_needed = target_segment_count - current_segment_count
                new_boundaries = set(boundaries)
                
                for i in range(1, additional_boundaries_needed + 1):
                    new_boundary_index = int((i * point_count) / (additional_boundaries_needed + 1))
                    # Avoid boundaries too close to existing ones
                    is_too_close = any(abs(new_boundary_index - existing) < 5 for existing in new_boundaries)
                    if not is_too_close and new_boundary_index < point_count:
                        new_boundaries.add(new_boundary_index)
                
                boundaries = sorted(new_boundaries)
        
        else:
            # For open curves, include the end point
            if (point_count - 1) not in boundaries:
                boundaries.append(point_count - 1)
            
            current_segment_count = len(boundaries) - 1
            
            if current_segment_count < target_segment_count:
                additional_boundaries_needed = target_segment_count - current_segment_count
                
                # Find segments with largest gaps
                segment_gaps = []
                for i in range(len(boundaries) - 1):
                    gap_size = boundaries[i + 1] - boundaries[i]
                    segment_gaps.append((gap_size, i))
                
                segment_gaps.sort(reverse=True)
                
                # Split largest gaps
                for gap_size, gap_index in segment_gaps[:additional_boundaries_needed]:
                    if gap_size > 20:  # Only split substantial gaps
                        midpoint = boundaries[gap_index] + gap_size // 2
                        boundaries.insert(gap_index + 1, midpoint)
        
        # Clean up boundaries
        boundaries = [index for index in boundaries if 0 <= index < point_count]
        boundaries = sorted(set(boundaries))
        
        # Ensure minimum of 2 boundaries for segment creation
        if len(boundaries) < 2:
            if point_count > 1:
                midpoint = point_count // 2
                boundaries = [0, midpoint, point_count - 1] if not is_closed else [0, midpoint]
            else:
                boundaries = [0]
        
        return boundaries

    def _enforce_segment_continuity(self, segments: List[BezierSegment], 
                                  boundaries: List[int], corner_indices: List[int],
                                  is_closed: bool):
        """Enforce C0 continuity at all junctions and C1 continuity only at non-corner junctions."""
        if len(segments) < 2:
            return
        
        for segment_index in range(len(segments) - 1):
            current_segment = segments[segment_index]
            next_segment = segments[segment_index + 1]
            junction_index = boundaries[segment_index + 1]
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
        
        # Handle closure for closed curves
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
                            corner_regions: List[Tuple[int, int]], corner_indices: List[int]) -> str:
        """Classify segment based on its relationship to corner regions."""
        # Check if segment falls entirely within a corner region
        for region_start, region_end in corner_regions:
            if start_index >= region_start and end_index <= region_end:
                return "corner_region"
        
        # Check if segment contains any corner
        for corner_index in corner_indices:
            if start_index <= corner_index <= end_index:
                return "corner_region"
        
        # Check if segment connects two consecutive corners (likely straight)
        if self._is_segment_connecting_corners(start_index, end_index, corner_indices):
            return "straight_edge"
        
        return "curved"
        
    def _is_segment_connecting_corners(self, start_index: int, end_index: int, corner_indices: List[int]) -> bool:
        """Check if segment directly connects two consecutive corner points."""
        sorted_corners = sorted(corner_indices)
        
        # Check consecutive corners in open chain
        for i in range(len(sorted_corners) - 1):
            if start_index == sorted_corners[i] and end_index == sorted_corners[i + 1]:
                return True
        
        # Check closure for closed curves
        if len(sorted_corners) > 1:
            if start_index == sorted_corners[-1] and end_index == sorted_corners[0]:
                return True
        
        return False
    
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
            # Find point with maximum deviation but constrain it near the line
            max_deviation_point = self._find_point_with_max_deviation(points, start_point, end_point)
            line_projection = self._project_point_to_line(start_point, end_point, max_deviation_point)
            
            # Keep deviation point close to the line to prevent distortion
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
        
        # Create evenly distributed segment boundaries
        points_per_segment = max(1, point_count // segment_count)
        boundaries = [i * points_per_segment for i in range(segment_count)]
        boundaries.append(point_count - 1)
        
        # Fit each segment independently
        for segment_index in range(segment_count):
            start_index = boundaries[segment_index]
            end_index = boundaries[segment_index + 1]
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
        
        # Handle closure for closed curves
        if is_closed and len(segments) > 1:
            self._ensure_curve_closure(segments)
            
            # Enforce C1 continuity between last and first segment
            if self.bezier_degree == 2 and len(segments) > 1:
                self._enforce_tangent_continuity(segments[-1], segments[0])
        
        return segments

    def _ensure_curve_closure(self, segments: List[BezierSegment]):
        """Ensure the first and last points of a closed curve match exactly."""
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