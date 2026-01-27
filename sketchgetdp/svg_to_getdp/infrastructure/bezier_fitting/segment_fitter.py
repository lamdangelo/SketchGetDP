import numpy as np
from typing import List
from svg_to_getdp.core.entities.bezier_segment import BezierSegment
from svg_to_getdp.core.entities.point import Point


class SegmentFitter:
    """
    Fits Bézier segments to point data using various fitting strategies.
    """
    
    def __init__(self, bezier_degree: int = 2):
        self.bezier_degree = bezier_degree
    
    def fit_piecewise_bezier_curves(self, points: List[Point], corner_indices: List[int], 
                                   segment_count: int, is_closed: bool,
                                   segment_classifier, bezier_calculator) -> List[BezierSegment]:
        """
        Fit Bézier curves with special handling for corner regions and straight edges.
        """
        if not corner_indices:
            return self._fit_continuous_curves_without_corners(points, segment_count, is_closed, bezier_calculator)
        
        corner_regions = segment_classifier.identify_corner_regions(points, corner_indices)
        segment_interfaces = bezier_calculator.calculate_segment_interfaces(
            points, corner_indices, segment_count, is_closed
        )
        
        fitted_segments = []
        for segment_index in range(len(segment_interfaces) - 1):
            start_index = segment_interfaces[segment_index]
            end_index = segment_interfaces[segment_index + 1]
            segment_points = points[start_index:end_index + 1]
            
            if len(segment_points) < 2:
                continue
                
            segment_type = segment_classifier.classify_segment_type(
                start_index, end_index, corner_regions, corner_indices, points
            )
            
            if segment_type == "corner_region":
                fitted_segment = self._fit_constrained_corner_segment(segment_points, bezier_calculator)
            elif segment_type == "straight_edge":
                fitted_segment = self._fit_straight_edge_segment(segment_points)
            else:
                fitted_segment = self.fit_single_bezier_curve(segment_points)
            
            fitted_segments.append(fitted_segment)
        
        return fitted_segments
    
    def fit_single_bezier_curve(self, points: List[Point]) -> BezierSegment:
        """Fit a single Bézier curve to points using least-squares optimization."""
        point_count = len(points)
        
        if point_count <= 3:
            return self._fit_simple_bezier_curve(points)
        
        # Import here to avoid circular imports
        from svg_to_getdp.infrastructure.bezier_fitting.bezier_calculator import BezierCalculator
        bezier_calculator = BezierCalculator()
        
        parameter_values = np.linspace(0, 1, point_count)
        
        # Build Bernstein basis matrix
        basis_matrix = np.zeros((point_count, self.bezier_degree + 1))
        for row, t in enumerate(parameter_values):
            for col in range(self.bezier_degree + 1):
                basis_matrix[row, col] = bezier_calculator.compute_bernstein_basis(col, self.bezier_degree, t)
        
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
    
    def _fit_constrained_corner_segment(self, points: List[Point], bezier_calculator) -> BezierSegment:
        """Fit segments in corner regions with heavy constraints to prevent overshooting."""
        if len(points) <= 2:
            return self._fit_simple_bezier_curve(points)
        
        start_point = points[0]
        end_point = points[-1]
        
        if bezier_calculator.are_points_approximately_linear(points):
            # Use midpoint for nearly linear segments
            midpoint = Point((start_point.x + end_point.x) / 2, (start_point.y + end_point.y) / 2)
        else:
            # Find point with maximum deviation and its projection onto the line
            max_deviation_point = bezier_calculator.find_point_with_max_deviation(points, start_point, end_point)
            line_projection = bezier_calculator.project_point_to_line(start_point, end_point, max_deviation_point)
            
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
    
    def _fit_continuous_curves_without_corners(self, points: List[Point], segment_count: int, 
                                             is_closed: bool, bezier_calculator) -> List[BezierSegment]:
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
                segment = self.fit_single_bezier_curve(segment_points)
                segments.append(segment)
        
        return segments
    