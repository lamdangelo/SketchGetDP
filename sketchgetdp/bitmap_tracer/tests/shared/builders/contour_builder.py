"""
Test fixture builder for ClosedContour domain objects.
Provides a fluent interface for creating contour test data with various shapes and properties.
"""

from typing import List
import math
from ....core.entities.contour import ClosedContour
from ....core.entities.point import Point


class ContourBuilder:
    """
    Constructs ClosedContour objects for testing contour processing algorithms.
    Follows the builder pattern to enable fluent configuration of contour properties.
    """
    
    def __init__(self) -> None:
        self._points: List[Point] = []
        self._is_closed: bool = True
        self._closure_gap: float = 0.0

    def with_points(self, points: List[Point]) -> 'ContourBuilder':
        """Sets the contour points from a provided list."""
        self._points = points.copy()
        return self

    def with_simple_rectangle(self, x: float = 0.0, y: float = 0.0, 
                            width: float = 100.0, height: float = 50.0) -> 'ContourBuilder':
        """Creates a rectangular contour with specified position and dimensions."""
        if width <= 0 or height <= 0:
            raise ValueError("Width and height must be positive")
            
        points = [
            Point(x, y),
            Point(x + width, y),
            Point(x + width, y + height),
            Point(x, y + height)
        ]
        return self.with_points(points)

    def with_triangle(self, x1: float = 0.0, y1: float = 0.0,
                     x2: float = 100.0, y2: float = 0.0,
                     x3: float = 50.0, y3: float = 86.6) -> 'ContourBuilder':
        """Creates a triangular contour from three vertex coordinates."""
        points = [
            Point(x1, y1),
            Point(x2, y2),
            Point(x3, y3)
        ]
        return self.with_points(points)

    def with_complex_shape(self, center_x: float = 50.0, center_y: float = 50.0, 
                          size: float = 40.0) -> 'ContourBuilder':
        """Creates a complex star-like shape with varying radius."""
        if size <= 0:
            raise ValueError("Size must be positive")
            
        points = []
        segments = 16
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            radius = size * (0.8 + 0.2 * math.cos(2 * angle))
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            points.append(Point(x, y))
        return self.with_points(points)

    def with_circle(self, center_x: float = 50.0, center_y: float = 50.0,
                   radius: float = 30.0, segments: int = 12) -> 'ContourBuilder':
        """Creates a circular contour approximated by the specified number of segments."""
        if radius <= 0:
            raise ValueError("Radius must be positive")
        if segments < 3:
            raise ValueError("Segments must be at least 3")
            
        points = []
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            points.append(Point(x, y))
        return self.with_points(points)

    def with_teardrop(self, tip_x: float = 50.0, tip_y: float = 20.0,
                     width: float = 30.0, height: float = 60.0) -> 'ContourBuilder':
        """Creates a teardrop-shaped contour expanding from the tip point."""
        if width <= 0 or height <= 0:
            raise ValueError("Width and height must be positive")
            
        points = []
        segments = 12
        for i in range(segments):
            angle = math.pi * i / (segments - 1)
            if angle <= math.pi / 2:
                x = tip_x - width * math.sin(angle)
                y = tip_y + height * (1 - math.cos(angle))
            else:
                x = tip_x + width * math.sin(angle)
                y = tip_y + height * (1 - math.cos(angle))
            points.append(Point(x, y))
        return self.with_points(points)

    def with_open_contour(self, points: List[Point] = None) -> 'ContourBuilder':
        """Configures the contour as open with optional custom points."""
        if points is None:
            points = [
                Point(0, 0),
                Point(50, 25),
                Point(100, 0),
                Point(150, 25)
            ]
        self._points = points
        self._is_closed = False
        return self

    def with_closure_gap(self, gap: float) -> 'ContourBuilder':
        """Sets the maximum allowed gap for considering the contour closed."""
        if gap < 0:
            raise ValueError("Closure gap cannot be negative")
        self._closure_gap = gap
        return self

    def with_random_points(self, count: int = 10, min_x: float = 0.0, max_x: float = 100.0,
                          min_y: float = 0.0, max_y: float = 100.0) -> 'ContourBuilder':
        """Generates a contour with randomly placed points within the specified bounds."""
        if count < 2:
            raise ValueError("Count must be at least 2")
        if min_x >= max_x or min_y >= max_y:
            raise ValueError("Invalid coordinate ranges")
            
        import random
        points = []
        for _ in range(count):
            x = random.uniform(min_x, max_x)
            y = random.uniform(min_y, max_y)
            points.append(Point(x, y))
        
        return self.with_points(points)

    def with_degenerate_case(self, case_type: str = "line") -> 'ContourBuilder':
        """Creates degenerate contours for testing edge cases and error conditions."""
        if case_type == "line":
            points = [Point(0, 0), Point(50, 50), Point(100, 100)]
        elif case_type == "point":
            points = [Point(50, 50), Point(50, 50), Point(50, 50)]
        elif case_type == "duplicate":
            points = [Point(0, 0), Point(100, 0), Point(100, 100), Point(0, 100), Point(0, 0)]
        else:
            raise ValueError(f"Unknown degenerate case type: {case_type}")
            
        return self.with_points(points)

    def build(self) -> ClosedContour:
        """Constructs and returns the configured ClosedContour instance."""
        if not self._points:
            raise ValueError("Cannot build contour: no points configured")
        
        return ClosedContour(
            points=self._points,
            is_closed=self._is_closed,
            closure_gap=self._closure_gap
        )


def create_simple_rectangle() -> ClosedContour:
    """Factory function for a standard rectangular contour."""
    return ContourBuilder().with_simple_rectangle().build()

def create_triangle() -> ClosedContour:
    """Factory function for a standard triangular contour."""
    return ContourBuilder().with_triangle().build()

def create_complex_shape() -> ClosedContour:
    """Factory function for a complex star-shaped contour."""
    return ContourBuilder().with_complex_shape().build()

def create_circle() -> ClosedContour:
    """Factory function for a standard circular contour."""
    return ContourBuilder().with_circle().build()

def create_teardrop() -> ClosedContour:
    """Factory function for a teardrop-shaped contour."""
    return ContourBuilder().with_teardrop().build()

def create_open_contour() -> ClosedContour:
    """Factory function for an open contour."""
    return ContourBuilder().with_open_contour().build()

def create_contour_with_closure_gap(gap: float = 5.0) -> ClosedContour:
    """Factory function for a rectangular contour with specified closure gap tolerance."""
    return ContourBuilder().with_simple_rectangle().with_closure_gap(gap).build()

def create_random_contour(count: int = 10) -> ClosedContour:
    """Factory function for a contour with randomly generated points."""
    return ContourBuilder().with_random_points(count=count).build()

def create_degenerate_contour(case_type: str = "line") -> ClosedContour:
    """Factory function for degenerate contour cases."""
    return ContourBuilder().with_degenerate_case(case_type).build()