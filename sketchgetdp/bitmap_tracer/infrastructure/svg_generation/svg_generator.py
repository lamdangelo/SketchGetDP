import svgwrite
from typing import List, Dict, Any
from ...core.entities.point import Point


class SVGGenerator:
    """
    Creates and manages SVG drawings with paths and points.
    
    This class handles the low-level SVG generation operations including
    path creation, point rendering, and file output.
    """
    
    def __init__(self, width: int, height: int):
        """Initialize with canvas dimensions."""
        self.width = width
        self.height = height
        self.drawing = None
    
    def create_drawing(self, output_path: str) -> None:
        """
        Create a new SVG drawing canvas.
        
        Args:
            output_path: File path where SVG will be saved
            
        Raises:
            RuntimeError: If drawing creation fails
        """
        self.drawing = svgwrite.Drawing(output_path, size=(self.width, self.height))
    
    def add_path(self, path_data: str, stroke_color: str = "#000000", 
                 stroke_width: int = 2, fill: str = "none") -> None:
        """
        Add a vector path to the SVG drawing.
        
        Paths represent continuous shapes like contours and boundaries.
        
        Args:
            path_data: SVG path commands (M, L, Q, Z, etc.)
            stroke_color: Color of the path stroke in hex format
            stroke_width: Width of the stroke in pixels
            fill: Interior fill color, "none" for transparent
                
        Raises:
            RuntimeError: If no drawing has been created
        """
        self._ensure_drawing_exists()
        
        self.drawing.add(self.drawing.path(
            d=path_data,
            fill=fill,
            stroke=stroke_color,
            stroke_width=stroke_width,
            stroke_linecap="round",
            stroke_linejoin="round"
        ))
    
    def add_point(self, point: Point, color: str = "#FF0000", radius: int = 4) -> None:
        """
        Add a point marker as a filled circle.
        
        Points represent discrete locations like detected features or centers.
        
        Args:
            point: The point location to render
            color: Fill color for the point marker
            radius: Size of the point marker in pixels
            
        Raises:
            RuntimeError: If no drawing has been created
        """
        self._ensure_drawing_exists()
        
        self.drawing.add(self.drawing.circle(
            center=(point.x, point.y),
            r=radius,
            fill=color,
            stroke="none"
        ))
    
    def add_circle(self, center_x: int, center_y: int, radius: int, 
                   fill: str, stroke: str = "none") -> None:
        """
        Add a circle shape to the drawing.
        
        Used for point markers and other circular elements.
        
        Args:
            center_x: Horizontal center position
            center_y: Vertical center position  
            radius: Circle radius in pixels
            fill: Interior fill color
            stroke: Border stroke color
                
        Raises:
            RuntimeError: If no drawing has been created
        """
        self._ensure_drawing_exists()
        
        self.drawing.add(self.drawing.circle(
            center=(center_x, center_y),
            r=radius,
            fill=fill,
            stroke=stroke
        ))
    
    def save(self) -> None:
        """
        Write the SVG drawing to disk.
        
        Raises:
            RuntimeError: If no drawing has been created
        """
        self._ensure_drawing_exists()
        self.drawing.save()
    
    def generate(self, output_path: str, paths: List[Dict[str, Any]], 
                 points: List[Dict[str, Any]]) -> bool:
        """
        Generate complete SVG file with all paths and points.
        
        This is the main entry point for creating a complete SVG document
        from processed image data.
        
        Args:
            output_path: Destination file path for SVG output
            paths: List of path definitions with data and styling
            points: List of point definitions with positions and styling
            
        Returns:
            True if generation succeeded, False on error
            
        Example:
            paths = [{'data': 'M 10,20 L 30,40', 'color': '#0000FF'}]
            points = [{'x': 50, 'y': 60, 'color': '#FF0000'}]
        """
        try:
            self.create_drawing(output_path)
            self._add_all_paths(paths)
            self._add_all_points(points)
            self.save()
            return True
            
        except Exception as error:
            print(f"SVG generation failed: {error}")
            return False
    
    def _ensure_drawing_exists(self) -> None:
        """Verify drawing is initialized before operations."""
        if self.drawing is None:
            raise RuntimeError("SVG drawing not initialized")
    
    def _add_all_paths(self, paths: List[Dict[str, Any]]) -> None:
        """Add all paths from the provided list."""
        for path in paths:
            self.add_path(
                path_data=path['data'],
                stroke_color=path.get('color', '#000000'),
                stroke_width=path.get('stroke_width', 2),
                fill=path.get('fill', 'none')
            )
    
    def _add_all_points(self, points: List[Dict[str, Any]]) -> None:
        """Add all points from the provided list."""
        for point in points:
            self.add_point(
                point=Point(point['x'], point['y']),
                color=point.get('color', '#FF0000'),
                radius=point.get('radius', 4)
            )