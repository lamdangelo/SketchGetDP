"""
Builder for creating Point and PointData test objects.
Follows the Test Data Builder pattern to create complex test objects
with clear, readable configuration.
"""

import math
from typing import List, Tuple
from core.entities.point import Point, PointData


class PointBuilder:
    """
    Constructs Point objects for testing spatial relationships and algorithms.
    
    This builder provides a fluent interface to create points with specific
    coordinates, enabling tests to clearly express their intent without
    being cluttered with object creation details.
    """
    
    def __init__(self):
        self._x = 0.0
        self._y = 0.0
        self._radius = 0.0
        self._is_small_point = False
    
    def with_coordinates(self, x: float, y: float) -> 'PointBuilder':
        """Sets the spatial coordinates for the point."""
        self._x = x
        self._y = y
        return self
    
    def with_x(self, x: float) -> 'PointBuilder':
        """Sets only the x-coordinate, leaving y at its current value."""
        self._x = x
        return self
    
    def with_y(self, y: float) -> 'PointBuilder':
        """Sets only the y-coordinate, leaving x at its current value."""
        self._y = y
        return self
    
    def with_radius(self, radius: float) -> 'PointBuilder':
        """Sets the detection radius for PointData objects."""
        self._radius = radius
        return self
    
    def as_small_point(self, is_small: bool = True) -> 'PointBuilder':
        """Marks the point as small for point detection algorithms."""
        self._is_small_point = is_small
        return self
    
    def build_point(self) -> Point:
        """Constructs a basic Point with the configured coordinates."""
        return Point(x=self._x, y=self._y)
    
    def build_point_data(self) -> PointData:
        """Constructs a PointData object with spatial and detection metadata."""
        return PointData(
            x=self._x, 
            y=self._y, 
            radius=self._radius, 
            is_small_point=self._is_small_point
        )
    
    # Factory methods for common test scenarios
    # These methods provide meaningful names that reveal test intent
    
    @classmethod
    def create_default_point(cls) -> Point:
        """Creates a point at the origin for basic existence tests."""
        return cls().build_point()
    
    @classmethod
    def create_point(cls, x: float, y: float) -> Point:
        """Creates a point at specified coordinates for spatial tests."""
        return cls().with_coordinates(x, y).build_point()
    
    @classmethod
    def create_point_data(cls, x: float, y: float, radius: float = 0.0, 
                         is_small_point: bool = False) -> PointData:
        """Creates a PointData with detection parameters for algorithm tests."""
        return (cls()
                .with_coordinates(x, y)
                .with_radius(radius)
                .as_small_point(is_small_point)
                .build_point_data())
    
    @classmethod
    def create_point_from_tuple(cls, point_tuple: Tuple[float, float]) -> Point:
        """Creates a Point from tuple data for external format compatibility tests."""
        return Point.from_tuple(point_tuple)
    
    @classmethod
    def create_points_sequence(cls, coordinates: List[Tuple[float, float]]) -> List[Point]:
        """Creates a sequence of points for contour and path testing."""
        return [cls.create_point_from_tuple(coord) for coord in coordinates]
    
    @classmethod
    def create_grid_points(cls, rows: int, cols: int, 
                          spacing: float = 10.0) -> List[Point]:
        """
        Creates a grid of points for testing spatial relationships and algorithms.
        
        Args:
            rows: Number of rows in the grid
            cols: Number of columns in the grid  
            spacing: Distance between adjacent points
            
        Returns:
            List of points arranged in row-major order
        """
        points = []
        for row in range(rows):
            for col in range(cols):
                x = col * spacing
                y = row * spacing
                points.append(cls.create_point(x, y))
        return points
    
    @classmethod
    def create_circle_points(cls, center_x: float, center_y: float, 
                            radius: float, num_points: int = 8) -> List[Point]:
        """
        Creates points arranged in a circle for testing contour detection.
        
        Args:
            center_x: X coordinate of circle center
            center_y: Y coordinate of circle center
            radius: Radius of the circle
            num_points: Number of points to generate around the circumference
            
        Returns:
            List of points forming a circular contour
        """
        points = []
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            points.append(cls.create_point(x, y))
        return points


class PointDataBuilder(PointBuilder):
    """
    Specialized builder for PointData objects with detection-specific parameters.
    
    This builder extends PointBuilder to focus on creating PointData objects
    with realistic detection metadata for testing point detection algorithms.
    """
    
    def __init__(self):
        super().__init__()
        self._radius = 1.0  # Reasonable default for detection scenarios
    
    def with_detection_parameters(self, radius: float, is_small_point: bool) -> 'PointDataBuilder':
        """Configures both radius and size classification together."""
        self._radius = radius
        self._is_small_point = is_small_point
        return self
    
    def as_detected_point(self, confidence_radius: float = 2.0) -> 'PointDataBuilder':
        """Configures as a typical point detected by the point detection algorithm."""
        self._radius = confidence_radius
        self._is_small_point = confidence_radius < 3.0
        return self
    
    def as_large_feature(self, feature_radius: float = 5.0) -> 'PointDataBuilder':
        """Configures as a large feature point that should not be filtered out."""
        self._radius = feature_radius
        self._is_small_point = False
        return self


# Intention-revealing convenience functions
# These functions have names that clearly state what kind of test object they create

def create_test_point(x: float = 0.0, y: float = 0.0) -> Point:
    """Creates a basic point for general testing purposes."""
    return PointBuilder().with_coordinates(x, y).build_point()

def create_test_point_data(x: float = 0.0, y: float = 0.0, 
                          radius: float = 1.0, 
                          is_small_point: bool = False) -> PointData:
    """Creates PointData with typical detection parameters for algorithm testing."""
    return PointDataBuilder().with_coordinates(x, y).with_radius(radius).as_small_point(is_small_point).build_point_data()

def create_contour_points() -> List[Point]:
    """Creates a simple rectangular contour for contour processing tests."""
    return PointBuilder().create_points_sequence([
        (0, 0), (10, 0), (10, 10), (0, 10)
    ])