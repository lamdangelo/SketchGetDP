import math
from typing import List, Tuple, Optional
from svg_to_getdp.core.entities.point import Point


class BezierCalculator:
    """
    Mathematical calculator for Bézier curve fitting and geometric calculations.
    """
    
    def remove_consecutive_duplicate_points(self, points: List[Point]) -> List[Point]:
        """Remove consecutive duplicate points from the input list."""
        if not points:
            return []
        
        unique_points = [points[0]]
        for i in range(1, len(points)):
            if points[i] != points[i-1]:
                unique_points.append(points[i])
        
        return unique_points
    
    def calculate_optimal_segment_count(self, points: List[Point], 
                                      corner_indices: List[int],
                                      minimum_points_per_segment: int = 15) -> int:
        """Calculate appropriate number of segments based on corners and point density."""
        point_count = len(points)
        
        if corner_indices:
            base_segments = max(len(corner_indices), 100)
        else:
            base_segments = max(200, point_count // 10)
            
        minimum_segments = 100
        maximum_segments = min(200, max(1, point_count // 10))
        
        return min(maximum_segments, max(minimum_segments, base_segments))
    
    def calculate_segment_interfaces(self, points: List[Point], corner_indices: List[int],
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
    
    def compute_bernstein_basis(self, basis_index: int, degree: int, parameter: float) -> float:
        """Compute Bernstein basis polynomial value."""
        return math.comb(degree, basis_index) * (parameter ** basis_index) * ((1 - parameter) ** (degree - basis_index))
    
    def are_points_geometrically_straight(self, points: List[Point], 
                                        relative_tolerance: float = 0.005,
                                        absolute_tolerance: float = 1e-6) -> Tuple[bool, float]:
        """
        Determine if points form a straight line within specified tolerances.
        
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
        passes_simplified_check = self.are_points_approximately_linear(points, relative_tolerance)
        
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
    
    def are_points_approximately_linear(self, points: List[Point], max_deviation_ratio: float = 0.01) -> bool:
        """Check if points form an approximately straight line."""
        if len(points) < 3:
            return True
        
        start_point = points[0]
        end_point = points[-1]
        
        max_absolute_deviation = 0
        for point in points:
            deviation = self.calculate_distance_from_line(start_point, end_point, point)
            max_absolute_deviation = max(max_absolute_deviation, deviation)
        
        segment_length = start_point.distance_to(end_point)
        if segment_length == 0:
            return True
        
        normalized_deviation = max_absolute_deviation / segment_length
        return normalized_deviation < max_deviation_ratio
    
    def find_point_with_max_deviation(self, points: List[Point], line_start: Point, line_end: Point) -> Point:
        """Find the point that deviates most from the line between start and end points."""
        max_deviation = -1
        most_deviant_point = points[len(points) // 2]
        
        for point in points:
            deviation = self.calculate_distance_from_line(line_start, line_end, point)
            if deviation > max_deviation:
                max_deviation = deviation
                most_deviant_point = point
        
        return most_deviant_point
    
    def project_point_to_line(self, line_start: Point, line_end: Point, point: Point) -> Point:
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
    
    def calculate_distance_from_line(self, line_point1: Point, line_point2: Point, test_point: Point) -> float:
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
    
    def _calculate_max_deviation_from_line(self, points: List[Point]) -> float:
        """Find maximum perpendicular distance of any point from the line between endpoints."""
        start_point, end_point = points[0], points[-1]
        max_deviation = 0.0
        
        for point in points:
            deviation = self.calculate_distance_from_line(start_point, end_point, point)
            max_deviation = max(max_deviation, deviation)
        
        return max_deviation
    
    def _calculate_straightness_confidence(self, normalized_deviation: float, 
                                         max_deviation: float, angle_variance: float,
                                         relative_tolerance: float, 
                                         absolute_tolerance: float) -> float:
        """
        Calculate confidence score (0-1) for straightness assessment.
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
    