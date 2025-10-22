import cv2
import numpy as np
from typing import Optional
from ...core.entities.contour import Contour


class CurveFitter:
    """
    Converts raster contours into smooth vector paths using adaptive fitting.
    
    This class implements a hybrid curve fitting approach that intelligently
    switches between straight lines and curved segments based on local
    contour geometry. It preserves sharp corners while smoothing gentle curves.
    """
    
    def __init__(self, angle_threshold: float = 25, min_curve_angle: float = 120):
        """
        Initialize curve fitter with geometric thresholds.
        
        Args:
            angle_threshold: Minimum angle (degrees) for curve segment classification
            min_curve_angle: Minimum angle (degrees) for considering curve fitting
        """
        self.angle_threshold = angle_threshold
        self.min_curve_angle = min_curve_angle
    
    def fit_curve(self, contour: np.ndarray, epsilon_factor: float = 0.0015) -> Optional[str]:
        """
        Convert contour to SVG path data using adaptive line/curve fitting.
        
        The algorithm:
        1. Simplifies contour to remove noise while preserving structure
        2. Ensures path closure for valid SVG rendering
        3. Analyzes angles between segments to determine fitting strategy
        4. Uses lines for sharp corners and quadratic bezier for gentle curves
        
        Args:
            contour: OpenCV contour array to convert
            epsilon_factor: Douglas-Peucker simplification tolerance factor
            
        Returns:
            SVG path data string, or None if conversion fails
        """
        if len(contour) < 3:
            return None
        
        # Simplify contour to reduce noise while preserving important features
        simplified_contour = self._simplify_contour(contour, epsilon_factor)
        if simplified_contour is None:
            return None
        
        points = [point[0] for point in simplified_contour]
        
        # Ensure path forms closed loop for valid SVG rendering
        points, is_closed = self._ensure_closure(points)
        
        # Generate SVG path data using adaptive segment fitting
        path_data = self._generate_svg_path(points, is_closed)
        
        return path_data
    
    def simplify(self, contour: np.ndarray, epsilon_factor: float = 0.0015) -> Optional[np.ndarray]:
        """
        Reduce contour complexity using Douglas-Peucker algorithm.
        
        Contour simplification removes redundant points while preserving
        the essential shape structure. This improves rendering performance
        and reduces file size without significant quality loss.
        
        Args:
            contour: OpenCV contour array to simplify
            epsilon_factor: Simplification tolerance relative to contour length
            
        Returns:
            Simplified contour array, or None if simplification fails
        """
        if len(contour) < 3:
            return None
        
        contour_length = cv2.arcLength(contour, True)
        epsilon = epsilon_factor * contour_length
        simplified_contour = cv2.approxPolyDP(contour, epsilon, True)
        
        return simplified_contour if len(simplified_contour) >= 3 else None
    
    def _simplify_contour(self, contour: np.ndarray, epsilon_factor: float) -> Optional[np.ndarray]:
        """
        Apply contour simplification with length-adaptive tolerance.
        
        Args:
            contour: Raw contour array to simplify
            epsilon_factor: Tolerance factor relative to contour perimeter
            
        Returns:
            Simplified contour array meeting minimum point requirements
        """
        contour_length = cv2.arcLength(contour, True)
        epsilon = epsilon_factor * contour_length
        simplified_contour = cv2.approxPolyDP(contour, epsilon, True)
        
        return simplified_contour if len(simplified_contour) >= 3 else None
    
    def _ensure_closure(self, points: list) -> tuple:
        """
        Verify and enforce contour closure for valid SVG path generation.
        
        Checks distance between start and end points. If beyond threshold,
        appends start point to end to force closure. This ensures all
        generated paths form complete, renderable shapes.
        
        Args:
            points: List of contour points as [x, y] coordinates
            
        Returns:
            Tuple of (closed_points, closure_status)
        """
        start_point = points[0]
        end_point = points[-1]
        closure_distance = np.linalg.norm(np.array(start_point) - np.array(end_point))
        
        closure_threshold = 10.0  # pixels
        is_naturally_closed = closure_distance <= closure_threshold
        
        if not is_naturally_closed:
            print(f"  ⚠️  Simplified contour not closed, distance: {closure_distance:.2f}")
            points.append(points[0])
            print("  🔒 Forced closure on simplified points")
            is_naturally_closed = True
        
        return points, is_naturally_closed
    
    def _generate_svg_path(self, points: list, is_closed: bool) -> str:
        """
        Convert point sequence to SVG path data using adaptive fitting.
        
        Analyzes angles between consecutive segments to determine optimal
        path commands. Sharp angles use straight lines, while gentle curves
        use quadratic bezier segments for smooth rendering.
        
        Args:
            points: List of contour points as [x, y] coordinates
            is_closed: Boolean indicating if path forms closed loop
            
        Returns:
            SVG path data string with move, line, and curve commands
        """
        path_data = f"M {points[0][0]},{points[0][1]}"
        point_count = len(points)
        current_index = 1
        
        while current_index < point_count:
            current_point = points[current_index]
            previous_point = points[current_index - 1]
            next_point = points[(current_index + 1) % point_count]
            
            # Handle final segment connection for closed paths
            if current_index == point_count - 1 and is_closed:
                path_data += f" L {points[0][0]},{points[0][1]}"
                break
            
            # Analyze segment geometry for curve fitting decisions
            if self._should_use_curve_fitting(current_index, point_count, is_closed):
                segment_angle = self._calculate_segment_angle(previous_point, current_point, next_point)
                
                if segment_angle is not None and segment_angle < self.angle_threshold:
                    # Sharp corner - use straight line segment
                    path_data += f" L {current_point[0]},{current_point[1]}"
                    current_index += 1
                else:
                    # Gentle curve - use quadratic bezier
                    path_data += f" Q {current_point[0]},{current_point[1]} {next_point[0]},{next_point[1]}"
                    current_index += 2  # Skip next point as it's used in curve
            else:
                # Default to straight line segment
                path_data += f" L {current_point[0]},{current_point[1]}"
                current_index += 1
        
        # Ensure path termination for closed shapes
        path_data += " Z"
        print(f"  {'✅' if is_closed else '⚠️'} Path closure: {is_closed}")
        
        return path_data
    
    def _should_use_curve_fitting(self, current_index: int, total_points: int, is_closed: bool) -> bool:
        """
        Determine if current segment is suitable for curve analysis.
        
        Curve fitting requires sufficient surrounding points for
        angle calculation. This prevents errors at path boundaries.
        
        Args:
            current_index: Current position in point sequence
            total_points: Total number of points in contour
            is_closed: Whether path forms closed loop
            
        Returns:
            True if segment can be evaluated for curve fitting
        """
        return current_index < total_points - 1 or (is_closed and total_points > 3)
    
    def _calculate_segment_angle(self, previous_point: list, current_point: list, next_point: list) -> Optional[float]:
        """
        Calculate angle between consecutive contour segments.
        
        Uses vector analysis to determine the turning angle at each
        contour vertex. This angle guides the line vs curve decision.
        
        Args:
            previous_point: Point before current vertex
            current_point: Current vertex position
            next_point: Point after current vertex
            
        Returns:
            Angle in degrees between segments, or None if calculation fails
        """
        vector_to_previous = np.array([previous_point[0] - current_point[0], 
                                     previous_point[1] - current_point[1]])
        vector_to_next = np.array([next_point[0] - current_point[0], 
                                 next_point[1] - current_point[1]])
        
        previous_magnitude = np.linalg.norm(vector_to_previous)
        next_magnitude = np.linalg.norm(vector_to_next)
        
        if previous_magnitude > 0 and next_magnitude > 0:
            normalized_previous = vector_to_previous / previous_magnitude
            normalized_next = vector_to_next / next_magnitude
            
            dot_product = np.clip(np.dot(normalized_previous, normalized_next), -1.0, 1.0)
            angle_radians = np.arccos(dot_product)
            return np.degrees(angle_radians)
        
        return None