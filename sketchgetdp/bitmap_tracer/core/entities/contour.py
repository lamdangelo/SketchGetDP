from dataclasses import dataclass
from typing import List, Optional
import numpy as np

from .point import Point


@dataclass
class ClosedContour:
    """
    A closed shape detected in the bitmap image.
    The closure status is critical for proper SVG path generation.
    """
    points: List[Point]
    is_closed: bool
    closure_gap: float
    
    @property
    def area(self) -> float:
        """
        Calculates area using the shoelace formula.
        Used for filtering out noise and prioritizing larger structures.
        """
        if len(self.points) < 3:
            return 0.0
        
        x_coordinates = [point.x for point in self.points]
        y_coordinates = [point.y for point in self.points]
        
        # Shoelace formula: ∑(x_i * y_i+1 - x_i+1 * y_i) / 2
        area = 0.5 * abs(sum(
            x_coordinates[i] * y_coordinates[i + 1] - x_coordinates[i + 1] * y_coordinates[i] 
            for i in range(len(x_coordinates) - 1)
        ) + (x_coordinates[-1] * y_coordinates[0] - x_coordinates[0] * y_coordinates[-1]))
        
        return area
    
    @property
    def perimeter(self) -> float:
        """Total boundary length, used for circularity calculation and simplification thresholds."""
        if len(self.points) < 2:
            return 0.0
        
        perimeter = 0.0
        for i in range(len(self.points)):
            current_point = self.points[i]
            next_point = self.points[(i + 1) % len(self.points)]  # Wrap for closed contour
            perimeter += current_point.distance_to(next_point)
        
        return perimeter
    
    @property
    def circularity(self) -> float:
        """
        Measures how circular the shape is (4πA/P²).
        Perfect circle = 1.0, other shapes < 1.0.
        Used to filter out irregular noise artifacts.
        """
        area = self.area
        perimeter = self.perimeter
        
        if perimeter == 0:
            return 0.0
        
        return (4 * np.pi * area) / (perimeter * perimeter)
    
    def get_center(self) -> Optional[Point]:
        """Centroid calculation for point marker placement and spatial analysis."""
        if not self.points:
            return None
        
        sum_x = sum(point.x for point in self.points)
        sum_y = sum(point.y for point in self.points)
        
        return Point(sum_x / len(self.points), sum_y / len(self.points))
    
    @classmethod
    def from_numpy_contour(cls, contour: np.ndarray, tolerance: float = 5.0) -> 'ClosedContour':
        """
        Converts OpenCV contour format to our domain representation.
        The tolerance parameter controls how close endpoints must be to consider the contour closed.
        """
        if len(contour) == 0:
            return cls(points=[], is_closed=True, closure_gap=0.0)
        
        # OpenCV contours are nested arrays: [[[x, y]]], [[[x, y]]], ...
        points = [Point(float(point[0][0]), float(point[0][1])) for point in contour]
        
        if len(points) < 3:
            return cls(points=points, is_closed=False, closure_gap=0.0)
        
        # Closure detection: if start and end points are within tolerance, contour is closed
        start_point = points[0]
        end_point = points[-1]
        closure_gap = start_point.distance_to(end_point)
        is_closed = closure_gap <= tolerance
        
        return cls(points=points, is_closed=is_closed, closure_gap=closure_gap)