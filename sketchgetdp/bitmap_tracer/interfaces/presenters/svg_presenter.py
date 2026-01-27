"""
SVG format presenter for bitmap tracing results.
Converts contours and points into SVG vector graphics elements.
"""

from svgwrite import Drawing
from typing import List
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
