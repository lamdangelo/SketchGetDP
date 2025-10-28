"""
SVG format presenter for bitmap tracing results.
Converts contours and points into SVG vector graphics elements.
"""

from svgwrite import Drawing
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from core.entities.contour import Contour
from core.entities.point import Point
from core.entities.color import Color
from core.entities.color import ColorCategory


class SVGPresenter:
    """Converts traced shapes and points into SVG vector graphics."""
    
    def __init__(self, output_path: str, width: int, height: int):
        """Initializes SVG presenter with output specifications.
        
        Args:
            output_path: File path for SVG output
            width: Canvas width in pixels
            height: Canvas height in pixels
        """
        self.output_path = output_path
        self.width = width
        self.height = height
        self.dwg = Drawing(output_path, size=(width, height))
        self._initialize_element_counters()
    
    def _initialize_element_counters(self) -> None:
        """Sets up counters for tracking different SVG element types."""
        self.elements_count = {
            'points': 0,
            'paths': 0,
            'blue_paths': 0,
            'green_paths': 0,
            'red_points': 0
        }
    
    def add_point(self, point: Point, color: Color, radius: int = 4) -> None:
        """Adds a point marker as SVG circle element.
        
        Red points are filled circles, other colors use standard styling.
        
        Args:
            point: Point coordinates to render
            color: Color classification for styling
            radius: Circle radius in pixels
        """
        category, _ = color.categorize()
        if category == ColorCategory.RED:
            fill_color = "#FF0000"
            self.elements_count['red_points'] += 1
        else:
            fill_color = color.to_hex()
        
        self.dwg.add(self.dwg.circle(
            center=(point.x, point.y),
            r=radius,
            fill=fill_color,
            stroke="none"
        ))
        self.elements_count['points'] += 1
    
    def add_path(self, path_data: str, color: Color, stroke_width: int = 2) -> None:
        """Adds SVG path element with specified color styling.
        
        Args:
            path_data: SVG path commands string
            color: Determines stroke color (blue/green)
            stroke_width: Path line thickness
        """
        stroke_color = self._get_path_stroke_color(color)
        self._increment_path_counter(color)
        
        self.dwg.add(self.dwg.path(
            d=path_data,
            fill="none",
            stroke=stroke_color,
            stroke_width=stroke_width,
            stroke_linecap="round",
            stroke_linejoin="round"
        ))
        self.elements_count['paths'] += 1
    
    def _get_path_stroke_color(self, color: Color) -> str:
        """Determines SVG stroke color from color classification.
        
        Args:
            color: Color classification
            
        Returns:
            Hex color code for SVG stroke
        """
        category, hex_color = color.categorize()
        if category == ColorCategory.BLUE:
            return "#0000FF"
        elif category == ColorCategory.GREEN:
            return "#00FF00"
        elif category == ColorCategory.RED:
            return "#FF0000"
        return color.to_hex()
    
    def _increment_path_counter(self, color: Color) -> None:
        """Updates path counters based on color type.
        
        Args:
            color: Color classification for counter selection
        """
        category, _ = color.categorize()
        if category == ColorCategory.BLUE:
            self.elements_count['blue_paths'] += 1
        elif category == ColorCategory.GREEN:
            self.elements_count['green_paths'] += 1
    
    def add_contour_as_path(self, contour: Contour, color: Color, stroke_width: int = 2) -> None:
        """Converts contour to SVG path and adds to drawing.
        
        Args:
            contour: Shape contour to convert
            color: Path stroke color
            stroke_width: Line thickness
        """
        if contour.is_empty():
            return
        
        path_data = self._convert_contour_to_path_data(contour)
        self.add_path(path_data, color, stroke_width)
    
    def _convert_contour_to_path_data(self, contour: Contour) -> str:
        """Generates SVG path data from contour points.
        
        Args:
            contour: Contains ordered points defining shape boundary
            
        Returns:
            SVG path data string with move-to and line-to commands
        """
        if len(contour.points) < 1:
            return ""
        
        path_commands = self._build_path_commands_from_contour(contour)
        return " ".join(path_commands)
    
    def _build_path_commands_from_contour(self, contour: Contour) -> List[str]:
        """Constructs SVG path commands from contour point sequence.
        
        Args:
            contour: Ordered points defining shape
            
        Returns:
            List of SVG path commands
        """
        first_point = contour.points[0]
        commands = [f"M {first_point.x},{first_point.y}"]
        
        for point in contour.points[1:]:
            commands.append(f"L {point.x},{point.y}")
        
        if contour.is_closed and len(contour.points) > 2:
            commands.append("Z")
        
        return commands
    
    def save(self) -> bool:
        """Saves SVG file to disk and prints creation summary.
        
        Returns:
            True if save successful, False on error
        """
        try:
            self.dwg.save()
            self._report_save_success()
            return True
        except Exception as error:
            self._report_save_error(error)
            return False
    
    def _report_save_success(self) -> None:
        """Prints success message and element summary."""
        print(f"✅ SVG saved: {self.output_path}")
        self._print_creation_summary()
    
    def _report_save_error(self, error: Exception) -> None:
        """Prints error message when save fails."""
        print(f"❌ Error saving SVG: {error}")
    
    def _print_creation_summary(self) -> None:
        """Outputs formatted summary of created SVG elements."""
        print(f"🎨 SVG Creation Summary:")
        print(f"   Canvas size: {self.width}x{self.height}")
        print(f"   Total paths: {self.elements_count['paths']}")
        print(f"   - Blue paths: {self.elements_count['blue_paths']}")
        print(f"   - Green paths: {self.elements_count['green_paths']}")
        print(f"   Total points: {self.elements_count['points']}")
        print(f"   - Red points: {self.elements_count['red_points']}")
    
    def get_elements_count(self) -> Dict[str, int]:
        """Provides copy of element counts for reporting.
        
        Returns:
            Dictionary with counts for each element type
        """
        return self.elements_count.copy()
    
    def create_point_marker(self, center_x: int, center_y: int, radius: int = 3) -> Dict[str, Any]:
        """Defines point marker properties for rendering.
        
        Args:
            center_x: Horizontal center position
            center_y: Vertical center position  
            radius: Circle radius
            
        Returns:
            Dictionary with circle element properties
        """
        return {
            'type': 'circle',
            'cx': center_x,
            'cy': center_y,
            'r': radius
        }
    
    def add_smart_curve_path(self, points: List[Tuple[int, int]], color: Color, 
                           is_closed: bool = True, stroke_width: int = 2) -> Optional[str]:
        """Adds path with hybrid line/curve fitting for optimal smoothness.
        
        Uses lines for straight segments and curves for curved segments.
        
        Args:
            points: Ordered sequence of (x,y) coordinates
            color: Path stroke color
            is_closed: Whether to connect last point to first
            stroke_width: Line thickness
            
        Returns:
            Generated path data string if successful, None otherwise
        """
        if len(points) < 3:
            return None
        
        path_data = self._generate_hybrid_curve_path(points, is_closed)
        if path_data:
            self.add_path(path_data, color, stroke_width)
            return path_data
        return None
    
    def _generate_hybrid_curve_path(self, points: List[Tuple[int, int]], is_closed: bool, 
                                  angle_threshold: int = 25) -> str:
        """Generates path data using angle-based line/curve selection.
        
        Args:
            points: Coordinate sequence defining path
            is_closed: Whether path forms closed loop
            angle_threshold: Minimum angle for using curves vs lines
            
        Returns:
            SVG path data with optimized line and curve segments
        """
        if len(points) < 3:
            return ""
        
        path_start = self._create_path_start_command(points[0])
        segment_commands = self._generate_segment_commands(points, is_closed, angle_threshold)
        
        return path_start + " " + " ".join(segment_commands)
    
    def _create_path_start_command(self, start_point: Tuple[int, int]) -> str:
        """Creates SVG move-to command for path start.
        
        Args:
            start_point: Starting coordinate
            
        Returns:
            SVG M command string
        """
        return f"M {start_point[0]},{start_point[1]}"
    
    def _generate_segment_commands(self, points: List[Tuple[int, int]], 
                                 is_closed: bool, angle_threshold: int) -> List[str]:
        """Generates line and curve commands for path segments.
        
        Args:
            points: All path coordinates
            is_closed: Whether path should loop back to start
            angle_threshold: Angle limit for curve selection
            
        Returns:
            List of SVG path commands for segments
        """
        commands = []
        point_count = len(points)
        current_index = 1
        
        while current_index < point_count:
            command, index_increment = self._generate_segment_command(
                points, current_index, is_closed, angle_threshold
            )
            commands.append(command)
            current_index += index_increment
        
        if is_closed:
            commands.append(self._create_closure_command(points))
        
        return commands
    
    def _generate_segment_command(self, points: List[Tuple[int, int]], current_index: int,
                                is_closed: bool, angle_threshold: int) -> Tuple[str, int]:
        """Generates appropriate command for current path segment.
        
        Args:
            points: All path coordinates
            current_index: Index of current processing position
            is_closed: Whether path forms closed shape
            angle_threshold: Angle limit for curve usage
            
        Returns:
            Tuple of (SVG command string, number of points consumed)
        """
        if self._should_use_closure_line(points, current_index, is_closed):
            return self._create_closure_line_command(points), 1
        
        if self._can_analyze_curvature(points, current_index, is_closed):
            return self._analyze_segment_curvature(points, current_index, angle_threshold)
        
        return self._create_line_command(points[current_index]), 1
    
    def _should_use_closure_line(self, points: List[Tuple[int, int]], 
                               current_index: int, is_closed: bool) -> bool:
        """Determines if current segment should close the path.
        
        Args:
            points: All path coordinates
            current_index: Current processing position
            is_closed: Whether path should be closed
            
        Returns:
            True if this segment should connect back to start
        """
        return current_index == len(points) - 1 and is_closed
    
    def _create_closure_line_command(self, points: List[Tuple[int, int]]) -> str:
        """Creates line command connecting last point to first.
        
        Args:
            points: All path coordinates
            
        Returns:
            SVG L command to path start
        """
        return f"L {points[0][0]},{points[0][1]}"
    
    def _create_closure_command(self, points: List[Tuple[int, int]]) -> str:
        """Creates path closure command.
        
        Args:
            points: Path coordinates (used for start point)
            
        Returns:
            SVG Z closure command
        """
        return "Z"
    
    def _can_analyze_curvature(self, points: List[Tuple[int, int]], 
                             current_index: int, is_closed: bool) -> bool:
        """Checks if sufficient points remain for curvature analysis.
        
        Args:
            points: All path coordinates
            current_index: Current processing position
            is_closed: Whether path forms closed loop
            
        Returns:
            True if curvature analysis is possible
        """
        point_count = len(points)
        has_next_point = current_index < point_count - 1
        has_wrap_around = is_closed and point_count > 3
        return has_next_point or has_wrap_around
    
    def _analyze_segment_curvature(self, points: List[Tuple[int, int]], 
                                 current_index: int, angle_threshold: int) -> Tuple[str, int]:
        """Analyzes segment angle to choose between line or curve.
        
        Args:
            points: All path coordinates
            current_index: Current processing position
            angle_threshold: Minimum angle for curve selection
            
        Returns:
            Tuple of (SVG command, points consumed)
        """
        current_point = points[current_index]
        previous_point = points[current_index - 1]
        next_point = self._get_next_point(points, current_index)
        
        segment_angle = self._calculate_segment_angle(previous_point, current_point, next_point)
        
        if segment_angle < angle_threshold:
            return self._create_line_command(current_point), 1
        else:
            return self._create_curve_command(current_point, next_point), 2
    
    def _get_next_point(self, points: List[Tuple[int, int]], current_index: int) -> Tuple[int, int]:
        """Gets next point with wrap-around for closed paths.
        
        Args:
            points: All path coordinates
            current_index: Current processing position
            
        Returns:
            Next point coordinates
        """
        next_index = (current_index + 1) % len(points)
        return points[next_index]
    
    def _calculate_segment_angle(self, previous_point: Tuple[int, int],
                               current_point: Tuple[int, int],
                               next_point: Tuple[int, int]) -> float:
        """Calculates angle between incoming and outgoing segments.
        
        Args:
            previous_point: Point before current
            current_point: Current vertex
            next_point: Point after current
            
        Returns:
            Angle in degrees between segments
        """
        incoming_vector = self._create_vector(previous_point, current_point)
        outgoing_vector = self._create_vector(current_point, next_point)
        
        incoming_magnitude = self._calculate_vector_magnitude(incoming_vector)
        outgoing_magnitude = self._calculate_vector_magnitude(outgoing_vector)
        
        if incoming_magnitude == 0 or outgoing_magnitude == 0:
            return 0.0
        
        normalized_incoming = self._normalize_vector(incoming_vector, incoming_magnitude)
        normalized_outgoing = self._normalize_vector(outgoing_vector, outgoing_magnitude)
        
        dot_product = self._calculate_dot_product(normalized_incoming, normalized_outgoing)
        return np.degrees(np.arccos(dot_product))
    
    def _create_vector(self, from_point: Tuple[int, int], to_point: Tuple[int, int]) -> Tuple[float, float]:
        """Creates vector between two points.
        
        Args:
            from_point: Vector origin
            to_point: Vector destination
            
        Returns:
            (x, y) vector components
        """
        return (
            to_point[0] - from_point[0],
            to_point[1] - from_point[1]
        )
    
    def _calculate_vector_magnitude(self, vector: Tuple[float, float]) -> float:
        """Calculates Euclidean length of vector.
        
        Args:
            vector: (x, y) components
            
        Returns:
            Vector magnitude
        """
        return (vector[0]**2 + vector[1]**2) ** 0.5
    
    def _normalize_vector(self, vector: Tuple[float, float], magnitude: float) -> Tuple[float, float]:
        """Scales vector to unit length.
        
        Args:
            vector: (x, y) components
            magnitude: Current vector length
            
        Returns:
            Normalized unit vector
        """
        return (vector[0] / magnitude, vector[1] / magnitude)
    
    def _calculate_dot_product(self, vector1: Tuple[float, float], 
                             vector2: Tuple[float, float]) -> float:
        """Calculates dot product of two vectors.
        
        Args:
            vector1: First vector
            vector2: Second vector
            
        Returns:
            Dot product value clamped to [-1, 1]
        """
        dot = vector1[0] * vector2[0] + vector1[1] * vector2[1]
        return max(min(dot, 1.0), -1.0)
    
    def _create_line_command(self, point: Tuple[int, int]) -> str:
        """Creates SVG line-to command.
        
        Args:
            point: Line destination
            
        Returns:
            SVG L command string
        """
        return f"L {point[0]},{point[1]}"
    
    def _create_curve_command(self, control_point: Tuple[int, int], 
                            end_point: Tuple[int, int]) -> str:
        """Creates SVG quadratic curve command.
        
        Args:
            control_point: Curve control point
            end_point: Curve end point
            
        Returns:
            SVG Q command string
        """
        return f"Q {control_point[0]},{control_point[1]} {end_point[0]},{end_point[1]}"