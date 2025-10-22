import cv2
import numpy as np
from typing import List, Optional, Tuple
from ...core.entities.contour import Contour
from ...core.entities.point import Point


class ShapeProcessor:
    """
    Transforms raster contours into optimized vector paths.
    
    Uses hybrid approach with lines for straight segments and curves
    for curved segments to balance accuracy and simplicity.
    """
    
    # Default thresholds for curve fitting decisions
    DEFAULT_ANGLE_THRESHOLD = 25      # Degrees - below this use lines
    DEFAULT_MIN_CURVE_ANGLE = 120     # Degrees - minimum for curve consideration
    DEFAULT_CLOSURE_THRESHOLD = 10.0  # Pixels - maximum gap to consider closed
    DEFAULT_SIMPLIFICATION_EPSILON = 0.0015  # Contour length multiplier
    
    def __init__(self, angle_threshold: float = DEFAULT_ANGLE_THRESHOLD,
                 min_curve_angle: float = DEFAULT_MIN_CURVE_ANGLE):
        """
        Initialize with curve fitting parameters.
        
        Args:
            angle_threshold: Angles below this use straight lines (degrees)
            min_curve_angle: Minimum angle to consider for curves (degrees)
        """
        self.angle_threshold = angle_threshold
        self.min_curve_angle = min_curve_angle
    
    def process_shape(self, contour: Contour) -> Optional[str]:
        """
        Convert contour to optimized SVG path data.
        
        Applies simplification, closure enforcement, and smart curve fitting
        to create efficient vector representation.
        
        Args:
            contour: The raster contour to process
            
        Returns:
            SVG path data string, or None if contour is invalid
            
        Example:
            Returns: "M 10,20 L 30,40 Q 50,60 70,80 Z"
        """
        if not self._is_valid_contour(contour):
            return None
        
        closed_contour = self._ensure_contour_closure(contour)
        simplified_points = self._simplify_contour(closed_contour)
        
        if len(simplified_points) < 3:
            return None
        
        is_closed, closure_distance = self._check_closure(simplified_points)
        enforced_points = self._enforce_closure(simplified_points, is_closed, closure_distance)
        path_data = self._generate_path_data(enforced_points, is_closed)
        
        self._log_closure_status(is_closed, closure_distance)
        return path_data
    
    def filter_shapes(self, shapes: List[Tuple[float, Any]], max_count: int) -> List[Tuple[float, Any]]:
        """
        Retain only the largest shapes by area.
        
        Used to limit output complexity based on configuration.
        
        Args:
            shapes: List of (area, shape_data) tuples
            max_count: Maximum number of shapes to keep
            
        Returns:
            Filtered list containing largest shapes
            
        Example:
            Input: [(100, contour1), (50, contour2), (200, contour3)]
            Output with max_count=2: [(200, contour3), (100, contour1)]
        """
        if max_count <= 0:
            return []
        
        sorted_shapes = self.sort_by_area(shapes, descending=True)
        
        if max_count < len(sorted_shapes):
            discarded_count = len(sorted_shapes) - max_count
            print(f"Keeping {max_count} largest shapes, discarding {discarded_count}")
            return sorted_shapes[:max_count]
        else:
            print(f"Keeping all {len(sorted_shapes)} shapes")
            return sorted_shapes
    
    def sort_by_area(self, shapes: List[Tuple[float, Any]], descending: bool = True) -> List[Tuple[float, Any]]:
        """
        Sort shapes by their area.
        
        Args:
            shapes: List of (area, shape_data) tuples
            descending: True for largest first, False for smallest first
            
        Returns:
            Shapes sorted by area
        """
        return sorted(shapes, key=lambda shape: shape[0], reverse=descending)
    
    def _is_valid_contour(self, contour: Contour) -> bool:
        """Check if contour has enough points for processing."""
        return len(contour.points) >= 3
    
    def _ensure_contour_closure(self, contour: Contour, tolerance: float = 5.0) -> Contour:
        """
        Ensure contour forms a closed loop.
        
        Adds start point to end if gap exceeds tolerance.
        
        Args:
            contour: Contour to check
            tolerance: Maximum allowed gap between start and end (pixels)
            
        Returns:
            Guaranteed closed contour
        """
        start_point = contour.points[0]
        end_point = contour.points[-1]
        
        start_end_distance = np.linalg.norm(
            np.array([start_point.x, start_point.y]) - 
            np.array([end_point.x, end_point.y])
        )
        
        if start_end_distance > tolerance:
            closed_points = contour.points + [start_point]
            closed_contour = Contour(closed_points)
            print(f"Closed contour gap: {start_end_distance:.2f} pixels")
            return closed_contour
        
        return contour
    
    def _simplify_contour(self, contour: Contour) -> List:
        """
        Reduce contour complexity while preserving shape.
        
        Uses Douglas-Peucker algorithm to remove redundant points.
        
        Args:
            contour: Contour to simplify
            
        Returns:
            List of simplified points
        """
        contour_length = cv2.arcLength(contour.to_numpy(), True)
        epsilon = self.DEFAULT_SIMPLIFICATION_EPSILON * contour_length
        approximated = cv2.approxPolyDP(contour.to_numpy(), epsilon, True)
        
        return [point[0] for point in approximated]
    
    def _check_closure(self, points: List) -> Tuple[bool, float]:
        """
        Determine if points form a closed contour.
        
        Args:
            points: List of (x, y) coordinate tuples
            
        Returns:
            Tuple of (is_closed, gap_distance)
        """
        if len(points) < 3:
            return False, float('inf')
        
        start_x, start_y = points[0]
        end_x, end_y = points[-1]
        gap_distance = np.linalg.norm(np.array([start_x, start_y]) - np.array([end_x, end_y]))
        
        is_closed = gap_distance <= self.DEFAULT_CLOSURE_THRESHOLD
        return is_closed, gap_distance
    
    def _enforce_closure(self, points: List, is_closed: bool, gap_distance: float) -> List:
        """
        Force closure if needed by adding start point to end.
        
        Args:
            points: List of points
            is_closed: Current closure status
            gap_distance: Distance between start and end
            
        Returns:
            Points with guaranteed closure
        """
        if not is_closed:
            print(f"Enforcing closure on gap: {gap_distance:.2f} pixels")
            points.append(points[0])
        return points
    
    def _generate_path_data(self, points: List, is_closed: bool) -> str:
        """
        Create SVG path data using hybrid line/curve approach.
        
        Analyzes angles between segments to decide between straight lines
        and quadratic bezier curves for optimal results.
        
        Args:
            points: List of (x, y) coordinate tuples
            is_closed: Whether path should be explicitly closed
            
        Returns:
            SVG path data string
        """
        start_x, start_y = points[0]
        path_commands = [f"M {start_x},{start_y}"]
        point_count = len(points)
        current_index = 1
        
        while current_index < point_count:
            current_point = points[current_index]
            previous_point = points[current_index - 1]
            
            # For closed paths, wrap around to start for next point
            next_index = (current_index + 1) % point_count
            next_point = points[next_index] if is_closed else (
                points[current_index + 1] if current_index < point_count - 1 else None
            )
            
            # Handle final segment of closed path
            if current_index == point_count - 1 and is_closed:
                path_commands.append(f"L {points[0][0]},{points[0][1]}")
                break
            
            # Use curve if gentle angle, line if sharp angle
            if next_point and self._should_use_curve(previous_point, current_point, next_point):
                path_commands.append(f"Q {current_point[0]},{current_point[1]} {next_point[0]},{next_point[1]}")
                current_index += 2  # Skip next point since used in curve
            else:
                path_commands.append(f"L {current_point[0]},{current_point[1]}")
                current_index += 1
        
        if is_closed:
            path_commands.append("Z")
        
        return " ".join(path_commands)
    
    def _should_use_curve(self, previous_point: Tuple, current_point: Tuple, next_point: Tuple) -> bool:
        """
        Decide whether to use curve based on angle between segments.
        
        Args:
            previous_point: Point before current
            current_point: Current vertex point  
            next_point: Point after current
            
        Returns:
            True if curve should be used, False for straight line
        """
        vector_to_previous = np.array([
            previous_point[0] - current_point[0],
            previous_point[1] - current_point[1]
        ])
        vector_to_next = np.array([
            next_point[0] - current_point[0], 
            next_point[1] - current_point[1]
        ])
        
        previous_magnitude = np.linalg.norm(vector_to_previous)
        next_magnitude = np.linalg.norm(vector_to_next)
        
        if previous_magnitude == 0 or next_magnitude == 0:
            return False
        
        # Calculate angle between segments
        normalized_previous = vector_to_previous / previous_magnitude
        normalized_next = vector_to_next / next_magnitude
        dot_product = np.clip(np.dot(normalized_previous, normalized_next), -1.0, 1.0)
        angle = np.degrees(np.arccos(dot_product))
        
        # Use curve for gentle angles, line for sharp angles
        return angle >= self.angle_threshold
    
    def _log_closure_status(self, is_closed: bool, distance: float) -> None:
        """Output closure status for debugging."""
        status_icon = "✅" if is_closed else "⚠️"
        print(f"{status_icon} Path closure: {is_closed} (gap: {distance:.2f}px)")