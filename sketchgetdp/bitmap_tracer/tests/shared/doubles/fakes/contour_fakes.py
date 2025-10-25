import math
from typing import List
from dataclasses import dataclass
from .....core.entities.contour import Contour
from .....core.entities.point import Point


@dataclass
class FakeContour(Contour):
    """
    Fake contour implementation for testing purposes.
    
    Provides a test double that mimics Contour behavior while tracking
    method calls and state changes for verification in tests.
    """
    
    def __init__(self, points: List[Point] = None, is_closed: bool = True, closure_gap: float = 0.0):
        """
        Initialize a fake contour with optional custom points.
        
        Args:
            points: List of points defining the contour. Defaults to a unit square.
            is_closed: Whether the contour forms a closed shape.
            closure_gap: Maximum distance between start and end points to consider closed.
        """
        points = points or [Point(0, 0), Point(10, 0), Point(10, 10), Point(0, 10)]
        super().__init__(points, is_closed, closure_gap)
        self.was_processed = False
        self.simplification_called = False
    
    def simplify(self, tolerance: float) -> 'FakeContour':
        """
        Track simplification calls without performing actual simplification.
        
        Args:
            tolerance: Simplification tolerance value (ignored in fake implementation).
            
        Returns:
            Self reference to allow method chaining.
        """
        self.simplification_called = True
        return self


class FakeContourBuilder:
    """
    Test utility for creating standardized fake contour instances.
    
    Provides factory methods for common contour shapes used in testing scenarios.
    """
    
    @staticmethod
    def create_square_contour(x: float = 0, y: float = 0, size: float = 10) -> FakeContour:
        """
        Create a square-shaped contour for testing.
        
        Args:
            x: X-coordinate of the square's bottom-left corner.
            y: Y-coordinate of the square's bottom-left corner.
            size: Side length of the square.
            
        Returns:
            FakeContour instance representing a square.
        """
        points = [
            Point(x, y),
            Point(x + size, y),
            Point(x + size, y + size),
            Point(x, y + size)
        ]
        return FakeContour(points=points, is_closed=True)
    
    @staticmethod
    def create_open_contour() -> FakeContour:
        """
        Create an open contour for testing open path scenarios.
        
        Returns:
            FakeContour instance representing an open path.
        """
        points = [Point(0, 0), Point(5, 5), Point(10, 0)]
        return FakeContour(points=points, is_closed=False, closure_gap=2.5)
    
    @staticmethod
    def create_circle_contour(center_x: float = 0, center_y: float = 0, 
                            radius: float = 5, points: int = 8) -> FakeContour:
        """
        Create a circular contour approximation for testing.
        
        Args:
            center_x: X-coordinate of the circle center.
            center_y: Y-coordinate of the circle center.
            radius: Radius of the circle.
            points: Number of points to approximate the circle.
            
        Returns:
            FakeContour instance representing a circular shape.
        """
        contour_points = []
        for i in range(points):
            angle = 2 * 3.14159 * i / points
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            contour_points.append(Point(x, y))
        return FakeContour(points=contour_points, is_closed=True)