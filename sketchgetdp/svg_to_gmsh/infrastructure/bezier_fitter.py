import numpy as np
from typing import List, Tuple
import math

from ..core.entities.bezier_segment import BezierSegment
from ..core.entities.boundary_curve import BoundaryCurve
from ..core.entities.point import Point

class BezierFitter:
    """
    Fits piecewise Bézier curves to boundary points using optimized global least-squares.
    """
    
    def __init__(self, degree: int = 2, min_points_per_segment: int = 15):
        self.degree = degree
        self.min_points_per_segment = min_points_per_segment
        
    def fit_boundary_curve(self, points: List[Point], corner_indices: List[int], color, is_closed: bool = True) -> BoundaryCurve:
        """
        Fit piecewise Bézier curves with optimized continuity and accuracy.
        """
        if len(points) < 3:
            raise ValueError(f"Need at least 3 points for boundary curve, got {len(points)}")
        
        # Remove duplicate consecutive points
        cleaned_points = self._remove_duplicate_points(points)
        if len(cleaned_points) < 3:
            cleaned_points = points[:3]
            
        # Use moderate number of segments
        n_segments = self._determine_optimal_segments(cleaned_points, corner_indices)
        
        # Use optimized fitting
        bezier_segments = self._fit_optimized_bezier(
            cleaned_points, corner_indices, n_segments, is_closed
        )
        
        # Convert corner indices to corner points for the boundary curve
        corner_points = [cleaned_points[idx] for idx in corner_indices] if corner_indices else []
        
        return BoundaryCurve(
            bezier_segments=bezier_segments,
            corners=corner_points,
            color=color,
            is_closed=is_closed
        )
    
    def _determine_optimal_segments(self, points: List[Point], corner_indices: List[int]) -> int:
        """Determine optimal number of segments."""
        n_points = len(points)
        
        # Increase base segments significantly
        if corner_indices:
            base_segments = max(8, len(corner_indices) * 3)  # More segments for corners
        else:
            base_segments = max(12, n_points // 20)  # More segments in general
            
        min_segments = 8
        max_segments = min(20, n_points // 10)  # Increased maximum
        
        return min(max_segments, max(min_segments, base_segments))
    
    def _fit_optimized_bezier(self, points: List[Point], corner_indices: List[int], 
                            n_segments: int, is_closed: bool) -> List[BezierSegment]:
        """
        Optimized fitting with strong continuity but good shape preservation.
        """
        n_points = len(points)
        t_global = np.linspace(0, 1, n_points)
        
        # Build system with optimized constraints
        A, b_x, b_y = self._build_optimized_system(
            points, t_global, n_segments, corner_indices, is_closed
        )
        
        try:
            # Optimized weights - strong enough for continuity but not too strong
            data_weight = 1.0
            constraint_weight = 1000.0  # Balanced weight
            
            W = np.eye(A.shape[0])
            for i in range(n_points):
                W[i, i] = data_weight
            for i in range(n_points, A.shape[0]):
                W[i, i] = constraint_weight
            
            # Solve with optimized regularization
            ATWA = A.T @ W @ A
            ATWb_x = A.T @ W @ b_x
            ATWb_y = A.T @ W @ b_y
            
            # Optimized regularization
            regularization = np.eye(ATWA.shape[0]) * 1e-12
            ATWA_reg = ATWA + regularization
            
            control_x = np.linalg.solve(ATWA_reg, ATWb_x)
            control_y = np.linalg.solve(ATWA_reg, ATWb_y)
            
        except np.linalg.LinAlgError:
            # Use continuity-enforced independent fitting
            return self._fit_continuous_independent(points, n_segments, is_closed)
        
        # Create segments and ensure exact continuity
        segments = self._create_bezier_segments_from_solution(control_x, control_y, n_segments)
        self._enforce_exact_continuity(segments, is_closed)
        
        return segments
    
    def _build_optimized_system(self, points: List[Point], t_global: np.ndarray, 
                              n_segments: int, corner_indices: List[int], 
                              is_closed: bool) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Build optimized system with proper continuity enforcement.
        """
        n_points = len(points)
        control_points_per_segment = self.degree + 1
        total_control_points = n_segments * control_points_per_segment
        
        # Count constraints
        n_constraints = self._count_optimized_constraints(n_segments, corner_indices, is_closed)
        
        # Initialize matrices
        A = np.zeros((n_points + n_constraints, total_control_points))
        b_x = np.zeros(n_points + n_constraints)
        b_y = np.zeros(n_points + n_constraints)
        
        # Build Bernstein basis - this is the data fitting part
        for point_idx, t in enumerate(t_global):
            segment_idx, local_t = self._global_to_local_parameter(t, n_segments)
            
            segment_start = segment_idx * control_points_per_segment
            for basis_idx in range(control_points_per_segment):
                basis_val = self._bernstein_basis(basis_idx, self.degree, local_t)
                A[point_idx, segment_start + basis_idx] = basis_val
            
            b_x[point_idx] = points[point_idx].x
            b_y[point_idx] = points[point_idx].y
        
        # Add optimized constraints
        constraint_row = n_points
        
        # STRONG C0 continuity - these must be exact
        for seg_idx in range(n_segments - 1):
            current_start = seg_idx * control_points_per_segment
            next_start = (seg_idx + 1) * control_points_per_segment
            
            # Positional continuity: b_n^(current) = b_0^(next)
            A[constraint_row, current_start + self.degree] = 1.0
            A[constraint_row, next_start] = -1.0
            b_x[constraint_row] = 0
            b_y[constraint_row] = 0
            constraint_row += 1
        
        # Moderate C1 continuity
        for seg_idx in range(n_segments - 1):
            if self.degree == 2:
                current_start = seg_idx * control_points_per_segment
                next_start = (seg_idx + 1) * control_points_per_segment
                
                # Derivative continuity: 2*b_2^(current) - b_1^(current) - b_1^(next) = 0
                A[constraint_row, current_start + 1] = -1.0
                A[constraint_row, current_start + 2] = 2.0
                A[constraint_row, next_start + 1] = -1.0
                b_x[constraint_row] = 0
                b_y[constraint_row] = 0
                constraint_row += 1
        
        # Closure constraints
        if is_closed and n_segments > 1:
            last_start = (n_segments - 1) * control_points_per_segment
            first_start = 0
            
            # C0 closure
            A[constraint_row, last_start + self.degree] = 1.0
            A[constraint_row, first_start] = -1.0
            b_x[constraint_row] = 0
            b_y[constraint_row] = 0
            constraint_row += 1
            
            # C1 closure for quadratic
            if self.degree == 2:
                A[constraint_row, last_start + 1] = -1.0
                A[constraint_row, last_start + 2] = 2.0
                A[constraint_row, first_start + 1] = -1.0
                b_x[constraint_row] = 0
                b_y[constraint_row] = 0
        
        return A, b_x, b_y
    
    def _enforce_exact_continuity(self, segments: List[BezierSegment], is_closed: bool):
        """Enforce exact continuity by adjusting control points."""
        if len(segments) < 2:
            return
        
        # Ensure C0 continuity between segments
        for i in range(len(segments) - 1):
            current_segment = segments[i]
            next_segment = segments[i + 1]
            
            # Check and fix positional continuity
            gap = current_segment.end_point.distance_to(next_segment.start_point)
            if gap > 1e-10:
                # Adjust next segment's first control point to match current segment's last
                new_control_points = next_segment.control_points.copy()
                new_control_points[0] = current_segment.end_point
                segments[i + 1] = BezierSegment(
                    control_points=new_control_points,
                    degree=next_segment.degree
                )
        
        # Ensure closure
        if is_closed and len(segments) > 1:
            first_start = segments[0].start_point
            last_segment = segments[-1]
            
            closure_gap = last_segment.end_point.distance_to(first_start)
            if closure_gap > 1e-10:
                new_control_points = last_segment.control_points.copy()
                new_control_points[-1] = first_start
                segments[-1] = BezierSegment(
                    control_points=new_control_points,
                    degree=last_segment.degree
                )
    
    def _fit_continuous_independent(self, points: List[Point], n_segments: int, is_closed: bool) -> List[BezierSegment]:
        """
        Independent fitting with explicit continuity enforcement.
        """
        n_points = len(points)
        segments = []
        
        # Create segment boundaries
        segment_size = max(1, n_points // n_segments)
        boundaries = [i * segment_size for i in range(n_segments)]
        boundaries.append(n_points - 1)
        
        # Fit segments with enforced continuity
        previous_end = None
        for seg_idx in range(n_segments):
            start_idx = boundaries[seg_idx]
            end_idx = boundaries[seg_idx + 1]
            segment_points = points[start_idx:end_idx + 1]
            
            if len(segment_points) >= 2:
                # Enforce continuity with previous segment
                if previous_end is not None:
                    segment_points[0] = previous_end
                
                segment = self._fit_single_bezier_accurate(segment_points)
                segments.append(segment)
                previous_end = segment.end_point
        
        # Ensure exact closure
        if is_closed and len(segments) > 1:
            self._enforce_exact_closure(segments)
        
        return segments
    
    def _fit_single_bezier_accurate(self, points: List[Point]) -> BezierSegment:
        """Accurately fit a single Bézier curve."""
        n_points = len(points)
        
        if n_points <= 3:
            return self._fit_direct_bezier(points)
        
        t_values = np.linspace(0, 1, n_points)
        
        A = np.zeros((n_points, self.degree + 1))
        for i, t in enumerate(t_values):
            for j in range(self.degree + 1):
                A[i, j] = self._bernstein_basis(j, self.degree, t)
        
        x_coords = np.array([p.x for p in points])
        y_coords = np.array([p.y for p in points])
        
        try:
            # Use robust least squares
            control_x, residuals_x, rank_x, _ = np.linalg.lstsq(A, x_coords, rcond=None)
            control_y, residuals_y, rank_y, _ = np.linalg.lstsq(A, y_coords, rcond=None)
            
            control_points = []
            for i in range(self.degree + 1):
                control_points.append(Point(float(control_x[i]), float(control_y[i])))
            
            return BezierSegment(control_points=control_points, degree=self.degree)
            
        except np.linalg.LinAlgError:
            return self._fit_direct_bezier(points)
    
    def _enforce_exact_closure(self, segments: List[BezierSegment]):
        """Enforce exact closure."""
        if not segments:
            return
        
        first_start = segments[0].start_point
        last_segment = segments[-1]
        
        closure_gap = last_segment.end_point.distance_to(first_start)
        if closure_gap > 1e-10:
            new_control_points = last_segment.control_points.copy()
            new_control_points[-1] = first_start
            segments[-1] = BezierSegment(
                control_points=new_control_points,
                degree=last_segment.degree
            )
    
    def _count_optimized_constraints(self, n_segments: int, corner_indices: List[int], is_closed: bool) -> int:
        """Count optimized constraints."""
        n_constraints = 0
        
        # C0 constraints (always enforced)
        n_constraints += (n_segments - 1)
        
        # C1 constraints for quadratic
        if self.degree == 2:
            n_constraints += (n_segments - 1)
        
        # Closure constraints
        if is_closed and n_segments > 1:
            n_constraints += 1  # C0
            if self.degree == 2:
                n_constraints += 1  # C1
        
        return n_constraints
    
    def _global_to_local_parameter(self, t: float, n_segments: int) -> Tuple[int, float]:
        """Convert global parameter to segment index and local parameter."""
        segment_idx = int(t * n_segments)
        segment_idx = min(segment_idx, n_segments - 1)
        local_t = (t * n_segments) - segment_idx
        return segment_idx, local_t
    
    def _create_bezier_segments_from_solution(self, control_x: np.ndarray, control_y: np.ndarray, 
                                            n_segments: int) -> List[BezierSegment]:
        """Create Bézier segments from solution vectors."""
        control_points_per_segment = self.degree + 1
        segments = []
        
        for seg_idx in range(n_segments):
            start_idx = seg_idx * control_points_per_segment
            control_points = []
            
            for i in range(control_points_per_segment):
                idx = start_idx + i
                control_points.append(Point(float(control_x[idx]), float(control_y[idx])))
            
            segments.append(BezierSegment(
                control_points=control_points,
                degree=self.degree
            ))
        
        return segments
    
    def _fit_direct_bezier(self, points: List[Point]) -> BezierSegment:
        """Direct Bézier fitting."""
        n_points = len(points)
        
        if n_points == 1:
            control_points = [points[0]] * (self.degree + 1)
        elif n_points == 2:
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
            if self.degree == 2:
                start = points[0]
                end = points[-1]
                middle_idx = len(points) // 2
                middle = points[middle_idx]
                control_points = [start, middle, end]
            else:
                control_points = [points[0]]
                for i in range(1, self.degree):
                    idx = int((i / self.degree) * (n_points - 1))
                    control_points.append(points[idx])
                control_points.append(points[-1])
        
        return BezierSegment(control_points=control_points, degree=self.degree)
    
    def _bernstein_basis(self, i: int, n: int, t: float) -> float:
        """Bernstein basis polynomial."""
        return math.comb(n, i) * (t ** i) * ((1 - t) ** (n - i))
    
    def _remove_duplicate_points(self, points: List[Point]) -> List[Point]:
        """Remove consecutive duplicate points."""
        if not points:
            return []
        
        cleaned = [points[0]]
        for i in range(1, len(points)):
            if points[i] != points[i-1]:
                cleaned.append(points[i])
        
        return cleaned