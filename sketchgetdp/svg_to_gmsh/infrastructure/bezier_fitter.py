import numpy as np
from typing import List, Tuple
import math

from ..core.entities.bezier_segment import BezierSegment
from ..core.entities.boundary_curve import BoundaryCurve
from ..core.entities.point import Point

#TODO: Avoid discontinuities by implementing global least-squares fitting with continuity constraints
class BezierFitter:
    """
    Fits piecewise Bézier curves to boundary points using least-squares approach.
    Based on the methodology from "Simulating on Sketches: Uniting Numerics & Design"
    
    This infrastructure service implements the curve fitting algorithm converting ordered point sets into smooth
    piecewise Bézier representations.
    """
    
    def __init__(self, degree: int = 2, min_points_per_segment: int = 5):
        """
        Args:
            degree: Degree of Bézier curves (typically 2 for stability)
            min_points_per_segment: Minimum number of boundary points per Bézier segment
        """
        self.degree = degree
        self.min_points_per_segment = min_points_per_segment
        
    def fit_boundary_curve(self, points: List[Point], corners: List[Point], color, is_closed: bool = True) -> BoundaryCurve:
        """
        Fit piecewise Bézier curves to boundary points with continuity constraints.
        """
        if len(points) < 3:
            raise ValueError(f"Need at least 3 points for boundary curve, got {len(points)}")
        
        # Remove duplicate consecutive points but ensure we keep enough points
        cleaned_points = self._remove_duplicate_points(points)
        if len(cleaned_points) < 3:
            # If we removed too many duplicates, use original points
            cleaned_points = points[:3]  # Use first 3 points
            
        scaled_points = cleaned_points
        
        # Convert corners to match the points (they should already be scaled)
        scaled_corners = corners  # Use corners directly since they're already scaled
        
        # Determine segment boundaries based on corners
        segment_boundaries = self._determine_segment_boundaries(scaled_points, scaled_corners)
        
        # Fit Bézier segments to each segment with continuity constraints
        bezier_segments = self._fit_piecewise_bezier_with_continuity(
            scaled_points, segment_boundaries, scaled_corners, is_closed
        )
        
        # Create and return the boundary curve
        return BoundaryCurve(
            bezier_segments=bezier_segments,
            corners=corners,  # Return original corners
            color=color,
            is_closed=is_closed
        )
    
    def _remove_duplicate_points(self, points: List[Point]) -> List[Point]:
        """Remove consecutive duplicate points."""
        if not points:
            return []
        
        cleaned = [points[0]]
        for i in range(1, len(points)):
            if points[i] != points[i-1]:
                cleaned.append(points[i])
        
        return cleaned
    
    def _determine_segment_boundaries(self, points: List[Point], corners: List[Point]) -> List[int]:
        """Determine segment boundaries based on corners and curve characteristics."""
        n_points = len(points)
        
        if not corners:
            # Use curvature-based segmentation with more segments
            return self._segment_by_curvature_sensitive(points)
        
        # Use corners as primary segment boundaries
        corner_indices = []
        tolerance = 1e-4  # Increased tolerance
        
        for corner in corners:
            # Find the closest point to the corner
            min_distance = float('inf')
            best_index = -1
            
            for i, point in enumerate(points):
                distance = point.distance_to(corner)
                if distance < min_distance and distance < tolerance:
                    min_distance = distance
                    best_index = i
            
            if best_index != -1:
                corner_indices.append(best_index)
        
        # Remove duplicates and sort
        corner_indices = sorted(set(corner_indices))
        
        # Ensure we have proper segment boundaries from start to end
        segment_boundaries = []
        
        if not corner_indices or corner_indices[0] != 0:
            segment_boundaries.append(0)
        
        segment_boundaries.extend(corner_indices)
        
        if segment_boundaries[-1] != n_points - 1:
            segment_boundaries.append(n_points - 1)
            
        return segment_boundaries

    def _segment_by_curvature_sensitive(self, points: List[Point]) -> List[int]:
        """More sensitive curvature-based segmentation."""
        n_points = len(points)
        
        if n_points <= self.min_points_per_segment * 2:
            return [0, n_points - 1]
        
        # Create more segments for better fitting
        target_segments = max(4, n_points // 15)  # More segments
        segment_size = max(self.min_points_per_segment, n_points // target_segments)
        
        boundaries = list(range(0, n_points, segment_size))
        if boundaries[-1] != n_points - 1:
            boundaries.append(n_points - 1)
            
        return boundaries
    
    def _fit_piecewise_bezier_with_continuity(self, points: List[Point], segment_boundaries: List[int], 
                                            corners: List[Point], is_closed: bool) -> List[BezierSegment]:
        """Fit Bézier segments ensuring proper continuity and closure."""
        n_segments = len(segment_boundaries) - 1
        bezier_segments = []
        
        # Limit maximum segments to avoid over-segmentation
        max_reasonable_segments = min(15, len(points) // 10)
        if n_segments > max_reasonable_segments:
            segment_boundaries = self._create_reasonable_segments(points, max_reasonable_segments)
            n_segments = len(segment_boundaries) - 1
        
        # For closed curves, ensure we wrap around properly
        if is_closed and n_segments > 0:
            # Add the first point to the end to ensure proper closure
            if points[0] != points[-1]:
                points.append(points[0])
                # Update segment boundaries if needed
                if segment_boundaries[-1] != len(points) - 1:
                    segment_boundaries[-1] = len(points) - 1
        
        # Fit each segment
        for seg_idx in range(n_segments):
            start_idx = segment_boundaries[seg_idx]
            end_idx = segment_boundaries[seg_idx + 1]
            
            # Extract segment points
            segment_points = points[start_idx:end_idx + 1]
            
            if len(segment_points) < 2:
                continue
                
            # Fit the segment
            bezier_segment = self._fit_single_bezier_independent(segment_points)
            bezier_segments.append(bezier_segment)
        
        # CRITICAL: Ensure proper closure for closed curves
        if is_closed and len(bezier_segments) > 1:
            self._ensure_curve_closure(bezier_segments, points[0])
        
        return bezier_segments

    def _ensure_curve_closure(self, segments: List[BezierSegment], first_point: Point):
        """Ensure the curve properly closes by adjusting the last segment."""
        if not segments:
            return
        
        first_segment = segments[0]
        last_segment = segments[-1]
        
        # Check closure distance
        closure_distance = first_segment.start_point.distance_to(last_segment.end_point)
        
        if closure_distance > 1e-4:  # More tolerant threshold
            
            # Strategy 1: Simple translation of last segment
            adjusted_control_points = self._adjust_bezier_end(
                last_segment.control_points, first_segment.start_point
            )
            segments[-1] = BezierSegment(
                control_points=adjusted_control_points,
                degree=last_segment.degree
            )
            
            # Verify the fix
            new_closure_distance = first_segment.start_point.distance_to(segments[-1].end_point)
            
            if new_closure_distance > 1e-4:
                # Strategy 2: Re-fit the last segment with enforced start/end points
                self._refit_last_segment_with_closure(segments, first_point)

    def _create_reasonable_segments(self, points: List[Point], max_segments: int) -> List[int]:
        """Create reasonable segment boundaries to avoid over-segmentation."""
        n_points = len(points)
        segment_size = max(5, n_points // max_segments)
        
        boundaries = list(range(0, n_points, segment_size))
        if boundaries[-1] != n_points - 1:
            boundaries.append(n_points - 1)
        
        return boundaries

    def _adjust_bezier_end(self, control_points: List[Point], required_end: Point) -> List[Point]:
        """Adjust Bézier control points to end at a specific point."""
        if not control_points:
            return control_points
        
        # Calculate the translation needed
        current_end = control_points[-1]
        translation_x = required_end.x - current_end.x
        translation_y = required_end.y - current_end.y
        
        # Apply translation to all control points
        adjusted_points = []
        for point in control_points:
            adjusted_points.append(Point(
                point.x + translation_x,
                point.y + translation_y
            ))
        
        return adjusted_points
    
    def _refit_last_segment_with_closure(self, segments: List[BezierSegment], closure_point: Point):
        """Re-fit the last segment with enforced closure constraint."""
        if len(segments) < 2:
            return
        
        last_segment = segments[-1]
        prev_segment = segments[-2]
        
        # Get the required start point (end of previous segment)
        required_start = prev_segment.end_point
        required_end = closure_point
        
        # For quadratic Bézier, we have 3 control points: [p0, p1, p2]
        # p0 = required_start, p2 = required_end
        # We only need to find p1 that minimizes the fitting error
        
        # Simple approach: use the middle control point from the original fit
        # but adjust it to maintain reasonable curvature
        original_p1 = last_segment.control_points[1]
        
        # Calculate a reasonable middle point that maintains shape
        mid_x = (required_start.x + required_end.x) / 2
        mid_y = (required_start.y + required_end.y) / 2
        
        # Blend with original middle point
        blend_factor = 0.7
        new_p1_x = mid_x * blend_factor + original_p1.x * (1 - blend_factor)
        new_p1_y = mid_y * blend_factor + original_p1.y * (1 - blend_factor)
        
        adjusted_control_points = [
            required_start,
            Point(new_p1_x, new_p1_y),
            required_end
        ]
        
        segments[-1] = BezierSegment(
            control_points=adjusted_control_points,
            degree=last_segment.degree
        )
    
    def _fit_single_bezier_independent(self, points: List[Point]) -> BezierSegment:
        """
        Fit a single Bézier curve to points without considering continuity.
        """
        n_points = len(points)
        
        # For very short segments or simple cases, use direct fitting
        if n_points <= 3:
            return self._fit_direct_bezier(points)
        
        # For longer segments, use least squares fitting
        # Create parameter values for all points
        t_values = np.linspace(0, 1, n_points)
        
        # Build design matrix for all control points
        A = np.zeros((n_points, self.degree + 1))
        for i, t in enumerate(t_values):
            for j in range(self.degree + 1):
                A[i, j] = self._bernstein_basis(j, self.degree, t)
        
        # Extract coordinates
        x_coords = np.array([p.x for p in points])
        y_coords = np.array([p.y for p in points])
        
        try:
            # Solve for control points using least squares with regularization
            # Add small regularization to avoid numerical issues
            ATA = A.T @ A
            regularization = np.eye(ATA.shape[0]) * 1e-8
            ATA_reg = ATA + regularization
            
            control_x = np.linalg.solve(ATA_reg, A.T @ x_coords)
            control_y = np.linalg.solve(ATA_reg, A.T @ y_coords)
            
            # Create control points
            control_points = []
            for i in range(self.degree + 1):
                control_points.append(Point(float(control_x[i]), float(control_y[i])))
            
            return BezierSegment(control_points=control_points, degree=self.degree)
            
        except np.linalg.LinAlgError:
            # Fallback if least squares fails
            return self._fit_direct_bezier(points)
    
    def _adjust_bezier_start(self, control_points: List[Point], required_start: Point) -> List[Point]:
        """
        Adjust Bézier control points to start at a specific point while maintaining shape.
        This preserves the curve shape but translates it to start at the required point.
        """
        if not control_points:
            return control_points
        
        # Calculate the translation needed
        current_start = control_points[0]
        translation_x = required_start.x - current_start.x
        translation_y = required_start.y - current_start.y
        
        # Apply translation to all control points
        adjusted_points = []
        for point in control_points:
            adjusted_points.append(Point(
                point.x + translation_x,
                point.y + translation_y
            ))
        
        return adjusted_points
    
    def _fit_direct_bezier(self, points: List[Point]) -> BezierSegment:
        """Fit Bézier curve using direct method (for simple cases)."""
        n_points = len(points)
        
        if n_points == 1:
            # Single point - create degenerate curve
            control_points = [points[0]] * (self.degree + 1)
        elif n_points == 2:
            # Two points - distribute control points along the line
            start, end = points[0], points[-1]
            control_points = [start]
            for i in range(1, self.degree):
                alpha = i / self.degree
                control_points.append(Point(
                    start.x * (1 - alpha) + end.x * alpha,
                    start.y * (1 - alpha) + end.y * alpha
                ))
            control_points.append(end)
        else:
            # Multiple points - use interpolation approach
            if self.degree == 2:
                # For quadratic Bézier, use start, middle, and end points
                start = points[0]
                end = points[-1]
                middle_idx = len(points) // 2
                middle = points[middle_idx]
                control_points = [start, middle, end]
            else:
                # For higher degrees, sample points along the curve
                control_points = [points[0]]
                for i in range(1, self.degree):
                    idx = int((i / self.degree) * (n_points - 1))
                    control_points.append(points[idx])
                control_points.append(points[-1])
        
        return BezierSegment(control_points=control_points, degree=self.degree)
    
    def _bernstein_basis(self, i: int, n: int, t: float) -> float:
        """Compute the i-th Bernstein basis polynomial of degree n at parameter t."""
        return math.comb(n, i) * (t ** i) * ((1 - t) ** (n - i))
    
    def _is_point_corner(self, point: Point, corners: List[Point]) -> bool:
        """Check if a point is a corner."""
        tolerance = 1e-6
        for corner in corners:
            if (abs(point.x - corner.x) < tolerance and 
                abs(point.y - corner.y) < tolerance):
                return True
        return False
    
    def compute_fitting_error(self, boundary_curve: BoundaryCurve, original_points: List[Point]) -> float:
        """
        Compute the RMS error between the fitted Bézier curve and original points.
        
        Args:
            boundary_curve: The fitted boundary curve
            original_points: Original boundary points
            
        Returns:
            Root mean square error
        """
        if not original_points:
            return 0.0
        
        total_error = 0.0
        n_points = len(original_points)
        
        for i, point in enumerate(original_points):
            # Map point index to curve parameter
            t = i / (n_points - 1) if n_points > 1 else 0.0
            fitted_point = boundary_curve.evaluate(t)
            
            error = point.distance_to(fitted_point)
            total_error += error * error
        
        return math.sqrt(total_error / n_points)
    
    