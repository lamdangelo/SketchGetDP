from dataclasses import dataclass
from typing import List, Optional
import numpy as np
import cv2

from .point import Point


@dataclass
class Contour:
    """
    A closed shape detected in the bitmap image.
    The closure status is critical for proper SVG path generation.
    """
    points: List[Point]
    is_closed: bool
    closure_gap: float
    
    def __post_init__(self):
        """Make a defensive copy of the points list to prevent external mutation."""
        self.points = self.points.copy()
    
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
    def from_numpy_contour(cls, contour: np.ndarray, tolerance: float = 5.0) -> 'Contour':
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
        
        # KEY FIX: Check if the contour was explicitly closed by the closure service
        # If the first and last points are identical, it's definitely closed
        points_are_identical = (start_point.x == end_point.x and start_point.y == end_point.y)
        
        # Consider contour closed if either:
        # 1. Points are within tolerance (natural closure)
        # 2. Points are identical (explicit closure by closure service)
        is_closed = closure_gap <= tolerance or points_are_identical
        
        # If points are identical but gap > tolerance, use 0 gap (it's perfectly closed)
        actual_closure_gap = 0.0 if points_are_identical else closure_gap
        
        # Debug output to verify closure detection
        closure_type = "explicit" if points_are_identical else "natural" if is_closed else "open"
        print(f"    🔍 Contour closure: {closure_type}, gap: {actual_closure_gap:.2f}px, points: {len(points)}")
        
        return cls(points=points, is_closed=is_closed, closure_gap=actual_closure_gap)
    
    def to_numpy(self) -> np.ndarray:
        """
        Convert contour points to OpenCV numpy format.
        
        Returns:
            Numpy array in format [[[x, y]], [[x, y]], ...] for OpenCV compatibility
        """
        points_array = np.array([[point.x, point.y] for point in self.points], dtype=np.float32)
        return points_array.reshape(-1, 1, 2)

    def is_empty(self) -> bool:
        """
        Check if contour has no points.
        
        Returns:
            True if contour has no points, False otherwise
        """
        return len(self.points) == 0
    
    def get_bounding_box(self) -> Optional[tuple]:
        """
        Calculate the axis-aligned bounding box of the contour.
        
        Returns:
            Tuple (min_x, min_y, max_x, max_y) or None if contour is empty
        """
        if not self.points:
            return None
        
        x_coords = [point.x for point in self.points]
        y_coords = [point.y for point in self.points]
        
        return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))
    
    def simplify(self, epsilon: float = 1.0) -> 'Contour':
        """
        Simplify the contour using Douglas-Peucker algorithm.
        
        Args:
            epsilon: Approximation accuracy parameter
            
        Returns:
            New simplified Contour instance
        """
        if len(self.points) < 3:
            return self
        
        # Convert to numpy for OpenCV processing
        numpy_contour = self.to_numpy()
        
        # Apply Douglas-Peucker simplification
        simplified_numpy = cv2.approxPolyDP(numpy_contour, epsilon, self.is_closed)
        
        # Convert back to domain entity
        return Contour.from_numpy_contour(simplified_numpy)
    
    def __len__(self) -> int:
        """Return the number of points in the contour."""
        return len(self.points)
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        status = "CLOSED" if self.is_closed else "OPEN"
        return f"Contour(points={len(self.points)}, {status}, area={self.area:.1f}, gap={self.closure_gap:.2f}px)"