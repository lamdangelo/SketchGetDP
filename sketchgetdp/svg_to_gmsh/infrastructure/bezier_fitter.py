import numpy as np
from typing import List, Tuple
import math

from ..core.entities.bezier_segment import BezierSegment
from ..core.entities.boundary_curve import BoundaryCurve
from ..core.entities.point import Point


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
        
        Args:
            points: Ordered set of boundary points (from image processing/SVG parsing)
            corners: List of corner points detected by corner_detector
            color: Color entity for the boundary curve
            is_closed: Whether the curve forms a closed loop
            
        Returns:
            Boundary curve with fitted Bézier segments
        """
        if len(points) < 3:
            raise ValueError(f"Need at least 3 points for boundary curve, got {len(points)}")
        
        # Remove duplicate consecutive points but ensure we keep enough points
        cleaned_points = self._remove_duplicate_points(points)
        if len(cleaned_points) < 3:
            # If we removed too many duplicates, use original points
            cleaned_points = points[:3]  # Use first 3 points
        
        # Scale points to unit square
        scaled_points, scale_info = self._scale_to_unit_square(cleaned_points)
        
        # Convert corners to scaled coordinates
        scaled_corners = self._find_scaled_corners(cleaned_points, corners, scaled_points)
        
        # Determine segment boundaries based on corners
        segment_boundaries = self._determine_segment_boundaries(scaled_points, scaled_corners)
        
        # Fit Bézier segments to each segment with continuity constraints
        bezier_segments = self._fit_piecewise_bezier_with_continuity(
            scaled_points, segment_boundaries, scaled_corners, is_closed
        )
        
        # Create and return the boundary curve
        return BoundaryCurve(
            bezier_segments=bezier_segments,
            corners=corners,  # Return original corners, not scaled
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
    
    def _scale_to_unit_square(self, points: List[Point]) -> Tuple[List[Point], dict]:
        """Scale points to unit square [0,1]×[0,1] as described in Section II."""
        if not points:
            return [], {}
        
        # Find bounding box
        x_coords = [p.x for p in points]
        y_coords = [p.y for p in points]
        
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        
        width = max_x - min_x
        height = max_y - min_y
        
        # Handle degenerate cases by adding padding
        if width == 0:
            width = 1.0
            min_x -= 0.5
            max_x += 0.5
            
        if height == 0:
            height = 1.0
            min_y -= 0.5
            max_y += 0.5
        
        # Scale points
        scaled_points = []
        for point in points:
            scaled_x = (point.x - min_x) / width
            scaled_y = (point.y - min_y) / height
            scaled_points.append(Point(scaled_x, scaled_y))
        
        scale_info = {
            'min_x': min_x, 'max_x': max_x, 'min_y': min_y, 'max_y': max_y,
            'width': width, 'height': height
        }
            
        return scaled_points, scale_info
    
    def _find_scaled_corners(self, original_points: List[Point], original_corners: List[Point], 
                           scaled_points: List[Point]) -> List[Point]:
        """Find the scaled coordinates of corner points."""
        if not original_corners:
            return []
        
        scaled_corners = []
        tolerance = 1e-6
        
        for corner in original_corners:
            # Find the index of the corner in the original points
            found = False
            for i, point in enumerate(original_points):
                if (abs(point.x - corner.x) < tolerance and 
                    abs(point.y - corner.y) < tolerance):
                    # Use the corresponding scaled point
                    if i < len(scaled_points):
                        scaled_corners.append(scaled_points[i])
                        found = True
                    break
            if not found:
                # If corner not found in points, scale it directly
                # This is a fallback for edge cases
                x_coords = [p.x for p in original_points]
                y_coords = [p.y for p in original_points]
                min_x, max_x = min(x_coords), max(x_coords)
                min_y, max_y = min(y_coords), max(y_coords)
                width = max_x - min_x if max_x > min_x else 1.0
                height = max_y - min_y if max_y > min_y else 1.0
                
                scaled_x = (corner.x - min_x) / width
                scaled_y = (corner.y - min_y) / height
                scaled_corners.append(Point(scaled_x, scaled_y))
        
        return scaled_corners
    
    def _determine_segment_boundaries(self, points: List[Point], corners: List[Point]) -> List[int]:
        """Determine segment boundaries based on corners and curve characteristics."""
        n_points = len(points)
        
        if not corners:
            # No corners: divide curve into segments based on curvature
            return self._segment_by_curvature(points)
        
        # Use corners as primary segment boundaries
        corner_indices = []
        tolerance = 1e-6
        
        for corner in corners:
            for i, point in enumerate(points):
                if (abs(point.x - corner.x) < tolerance and 
                    abs(point.y - corner.y) < tolerance):
                    corner_indices.append(i)
                    break
        
        # Remove duplicates and sort
        corner_indices = sorted(set(corner_indices))
        
        # Ensure we have proper segment boundaries from start to end
        segment_boundaries = []
        
        if corner_indices[0] != 0:
            segment_boundaries.append(0)
        
        segment_boundaries.extend(corner_indices)
        
        if segment_boundaries[-1] != n_points - 1:
            segment_boundaries.append(n_points - 1)
            
        return segment_boundaries
    
    def _segment_by_curvature(self, points: List[Point]) -> List[int]:
        """Segment curve based on curvature when no corners are detected."""
        n_points = len(points)
        
        # For very short curves, use a single segment
        if n_points <= self.min_points_per_segment * 2:
            return [0, n_points - 1]
        
        # Simple heuristic: segment every N points, but ensure minimum points per segment
        max_segments = max(1, n_points // self.min_points_per_segment)
        segment_size = max(self.min_points_per_segment, n_points // max_segments)
        
        boundaries = list(range(0, n_points, segment_size))
        if boundaries[-1] != n_points - 1:
            boundaries.append(n_points - 1)
            
        return boundaries
    
    def _fit_piecewise_bezier_with_continuity(self, points: List[Point], segment_boundaries: List[int], 
                                            corners: List[Point], is_closed: bool) -> List[BezierSegment]:
        """Fit Bézier segments to each segment ensuring continuity between segments."""
        n_segments = len(segment_boundaries) - 1
        bezier_segments = []
        
        # First, fit all segments independently
        independent_segments = []
        for seg_idx in range(n_segments):
            start_idx = segment_boundaries[seg_idx]
            end_idx = segment_boundaries[seg_idx + 1]
            
            # Extract segment points
            segment_points = points[start_idx:end_idx + 1]
            
            # Fit Bézier curve to this segment
            bezier_segment = self._fit_single_bezier_independent(segment_points)
            independent_segments.append(bezier_segment)
        
        # Now adjust segments for continuity
        for seg_idx in range(n_segments):
            current_segment = independent_segments[seg_idx]
            
            if seg_idx == 0:
                # First segment - keep as is
                adjusted_segment = current_segment
            else:
                # Adjust current segment to start at the end of previous segment
                previous_segment = bezier_segments[seg_idx - 1]
                required_start = previous_segment.end_point
                
                # Create new control points that maintain the shape but start at required point
                adjusted_control_points = self._adjust_bezier_start(
                    current_segment.control_points, required_start
                )
                adjusted_segment = BezierSegment(
                    control_points=adjusted_control_points, 
                    degree=current_segment.degree
                )
            
            bezier_segments.append(adjusted_segment)
        
        return bezier_segments
    
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