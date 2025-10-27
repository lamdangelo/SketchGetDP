"""
Test fixtures for bitmap tracer contour detection and analysis.
Provides geometric shapes for testing contour processing algorithms.
"""

from typing import List, Tuple
import pytest
import numpy as np

from core.entities.contour import ClosedContour
from core.entities.point import Point


class ContourFixtures:
    """
    Geometric contour test data for bitmap tracer shape detection.
    Includes closed shapes, open paths, and edge cases for contour processing.
    """
    
    # Geometric shape generators
    @classmethod
    def create_square(cls, center_x: float = 100, center_y: float = 100, size: float = 50) -> ClosedContour:
        """Square contour for testing right-angle detection and area calculation."""
        half_size = size / 2
        points = [
            Point(center_x - half_size, center_y - half_size),
            Point(center_x + half_size, center_y - half_size),
            Point(center_x + half_size, center_y + half_size),
            Point(center_x - half_size, center_y + half_size)
        ]
        return ClosedContour(points=points, is_closed=True, closure_gap=0.0)
    
    @classmethod
    def create_triangle(cls, center_x: float = 100, center_y: float = 100, size: float = 50) -> ClosedContour:
        """Triangle contour for testing three-point geometry and angle calculations."""
        height = size * (3 ** 0.5) / 2
        points = [
            Point(center_x, center_y - height / 2),
            Point(center_x - size / 2, center_y + height / 2),
            Point(center_x + size / 2, center_y + height / 2)
        ]
        return ClosedContour(points=points, is_closed=True, closure_gap=0.0)
    
    @classmethod
    def create_circle(cls, center_x: float = 100, center_y: float = 100, 
                     radius: float = 40, num_points: int = 16) -> ClosedContour:
        """Circular contour for testing circularity detection and smooth curves."""
        points = []
        for i in range(num_points):
            angle = 2 * np.pi * i / num_points
            x = center_x + radius * np.cos(angle)
            y = center_y + radius * np.sin(angle)
            points.append(Point(x, y))
        return ClosedContour(points=points, is_closed=True, closure_gap=0.0)
    
    @classmethod
    def create_rectangle(cls, x: float = 50, y: float = 50, 
                        width: float = 100, height: float = 60) -> ClosedContour:
        """Rectangular contour for testing aspect ratio detection."""
        points = [
            Point(x, y),
            Point(x + width, y),
            Point(x + width, y + height),
            Point(x, y + height)
        ]
        return ClosedContour(points=points, is_closed=True, closure_gap=0.0)
    
    @classmethod
    def create_open_path(cls, gap_distance: float = 10.0) -> ClosedContour:
        """Open path contour for testing closure detection algorithms."""
        points = [
            Point(0, 0),
            Point(50, 0),
            Point(50, 50),
            Point(0, 50 + gap_distance)
        ]
        closure_gap = points[0].distance_to(points[-1])
        return ClosedContour(points=points, is_closed=False, closure_gap=closure_gap)
    
    @classmethod
    def create_near_closed_path(cls, gap_tolerance: float = 4.0) -> ClosedContour:
        """Nearly closed path for testing closure tolerance thresholds."""
        points = [
            Point(0, 0),
            Point(50, 0),
            Point(50, 50),
            Point(0, 50),
            Point(gap_tolerance / 2, 0)
        ]
        closure_gap = points[0].distance_to(points[-1])
        return ClosedContour(points=points, is_closed=False, closure_gap=closure_gap)
    
    @classmethod
    def create_irregular_polygon(cls) -> ClosedContour:
        """Complex polygon for testing vertex count and shape complexity."""
        points = [
            Point(0, 0),
            Point(30, 10),
            Point(50, 0),
            Point(70, 20),
            Point(60, 50),
            Point(30, 60),
            Point(10, 40),
            Point(0, 30)
        ]
        return ClosedContour(points=points, is_closed=True, closure_gap=0.0)
    
    @classmethod
    def create_tiny_contour(cls) -> ClosedContour:
        """Minimal contour for testing area threshold detection."""
        points = [
            Point(0, 0),
            Point(5, 0),
            Point(5, 5),
            Point(0, 5)
        ]
        return ClosedContour(points=points, is_closed=True, closure_gap=0.0)
    
    @classmethod
    def create_huge_contour(cls) -> ClosedContour:
        """Large contour for testing maximum size handling."""
        points = [
            Point(0, 0),
            Point(500, 0),
            Point(500, 500),
            Point(0, 500)
        ]
        return ClosedContour(points=points, is_closed=True, closure_gap=0.0)
    
    @classmethod
    def create_invalid_contour(cls, num_points: int = 2) -> ClosedContour:
        """Degenerate contour for testing validation edge cases."""
        points = [Point(i * 10, i * 10) for i in range(num_points)]
        return ClosedContour(points=points, is_closed=False, closure_gap=0.0)
    
    @classmethod
    def create_empty_contour(cls) -> ClosedContour:
        """Empty contour for testing boundary conditions."""
        return ClosedContour(points=[], is_closed=True, closure_gap=0.0)
    
    @classmethod
    def convert_to_numpy_format(cls, contour: ClosedContour) -> np.ndarray:
        """Convert contour to OpenCV numpy array format for interoperability tests."""
        numpy_data = np.array([[[point.x, point.y]] for point in contour.points], dtype=np.float32)
        return numpy_data
    
    # Predefined contour instances for consistent testing
    SQUARE = create_square.__func__()
    TRIANGLE = create_triangle.__func__()
    CIRCLE = create_circle.__func__(num_points=32)
    RECTANGLE = create_rectangle.__func__()
    OPEN_PATH = create_open_path.__func__(gap_distance=15.0)
    NEAR_CLOSED = create_near_closed_path.__func__(gap_tolerance=3.0)
    IRREGULAR_POLYGON = create_irregular_polygon.__func__()
    TINY = create_tiny_contour.__func__()
    HUGE = create_huge_contour.__func__()
    LINE = create_invalid_contour.__func__(num_points=2)
    SINGLE_POINT = create_invalid_contour.__func__(num_points=1)
    EMPTY = create_empty_contour.__func__()

    @classmethod
    def get_predefined_contours(cls) -> List[ClosedContour]:
        """All predefined contour instances for comprehensive testing."""
        return [
            cls.SQUARE,
            cls.TRIANGLE,
            cls.CIRCLE,
            cls.RECTANGLE,
            cls.OPEN_PATH,
            cls.NEAR_CLOSED,
            cls.IRREGULAR_POLYGON,
            cls.TINY,
            cls.HUGE,
            cls.LINE,
            cls.SINGLE_POINT,
            cls.EMPTY
        ]
    
    @classmethod
    def get_well_formed_contours(cls) -> List[ClosedContour]:
        """Contours that meet minimum requirements for bitmap tracer processing."""
        return [contour for contour in cls.get_predefined_contours() 
                if contour.is_closed and len(contour.points) >= 3]
    
    @classmethod
    def get_malformed_contours(cls) -> List[ClosedContour]:
        """Contours that should be rejected by validation checks."""
        return [contour for contour in cls.get_predefined_contours() 
                if not contour.is_closed or len(contour.points) < 3]
    
    @classmethod
    def get_closure_test_cases(cls) -> List[ClosedContour]:
        """Contours specifically for testing closure detection logic."""
        return [cls.SQUARE, cls.OPEN_PATH, cls.NEAR_CLOSED, cls.CIRCLE, cls.LINE]
    
    @classmethod
    def get_size_test_cases(cls) -> List[ClosedContour]:
        """Contours for testing area-based filtering."""
        return [cls.TINY, cls.SQUARE, cls.HUGE, cls.IRREGULAR_POLYGON]
    
    @classmethod
    def get_shape_complexity_cases(cls) -> List[Tuple[ClosedContour, str]]:
        """Contours organized by geometric complexity for algorithm testing."""
        return [
            (cls.SQUARE, "simple_polygon"),
            (cls.TRIANGLE, "simple_polygon"),
            (cls.CIRCLE, "smooth_curve"),
            (cls.RECTANGLE, "simple_polygon"),
            (cls.IRREGULAR_POLYGON, "complex_polygon"),
            (cls.OPEN_PATH, "open_path"),
            (cls.NEAR_CLOSED, "nearly_closed")
        ]


@pytest.fixture
def contour_fixtures():
    return ContourFixtures

@pytest.fixture
def square_contour():
    return ContourFixtures.SQUARE

@pytest.fixture
def triangle_contour():
    return ContourFixtures.TRIANGLE

@pytest.fixture
def circle_contour():
    return ContourFixtures.CIRCLE

@pytest.fixture
def rectangle_contour():
    return ContourFixtures.RECTANGLE

@pytest.fixture
def open_path_contour():
    return ContourFixtures.OPEN_PATH

@pytest.fixture
def near_closed_contour():
    return ContourFixtures.NEAR_CLOSED

@pytest.fixture
def irregular_polygon_contour():
    return ContourFixtures.IRREGULAR_POLYGON

@pytest.fixture
def tiny_contour():
    return ContourFixtures.TINY

@pytest.fixture
def huge_contour():
    return ContourFixtures.HUGE

@pytest.fixture
def line_contour():
    return ContourFixtures.LINE

@pytest.fixture
def single_point_contour():
    return ContourFixtures.SINGLE_POINT

@pytest.fixture
def empty_contour():
    return ContourFixtures.EMPTY

@pytest.fixture
def well_formed_contours():
    return ContourFixtures.get_well_formed_contours()

@pytest.fixture
def malformed_contours():
    return ContourFixtures.get_malformed_contours()

@pytest.fixture
def closure_test_contours():
    return ContourFixtures.get_closure_test_cases()

@pytest.fixture
def size_test_contours():
    return ContourFixtures.get_size_test_cases()

@pytest.fixture
def numpy_contour_data(square_contour):
    return ContourFixtures.convert_to_numpy_format(square_contour)


# Test data generators with clear testing intent
def area_computation_test_cases():
    """Test cases for contour area calculation validation."""
    return [
        (ContourFixtures.SQUARE, 2500.0),
        (ContourFixtures.TRIANGLE, 1082.5),
        (ContourFixtures.RECTANGLE, 6000.0),
        (ContourFixtures.TINY, 25.0),
        (ContourFixtures.HUGE, 250000.0),
        (ContourFixtures.LINE, 0.0),
        (ContourFixtures.SINGLE_POINT, 0.0),
        (ContourFixtures.EMPTY, 0.0)
    ]


def perimeter_computation_test_cases():
    """Test cases for contour perimeter calculation validation."""
    return [
        (ContourFixtures.SQUARE, 200.0),
        (ContourFixtures.RECTANGLE, 320.0),
        (ContourFixtures.TINY, 20.0),
        (ContourFixtures.LINE, 14.14),
        (ContourFixtures.SINGLE_POINT, 0.0),
        (ContourFixtures.EMPTY, 0.0)
    ]


def circularity_measurement_test_cases():
    """Test cases for shape circularity detection algorithms."""
    return [
        (ContourFixtures.CIRCLE, 0.95),
        (ContourFixtures.SQUARE, 0.785),
        (ContourFixtures.TRIANGLE, 0.604),
        (ContourFixtures.IRREGULAR_POLYGON, 0.5),
        (ContourFixtures.LINE, 0.0),
        (ContourFixtures.SINGLE_POINT, 0.0),
        (ContourFixtures.EMPTY, 0.0)
    ]


def closure_detection_test_cases():
    """Test cases for path closure detection logic."""
    return [
        (ContourFixtures.SQUARE, True, 0.0),
        (ContourFixtures.OPEN_PATH, False, 15.0),
        (ContourFixtures.NEAR_CLOSED, False, 3.0),
        (ContourFixtures.CIRCLE, True, 0.0),
        (ContourFixtures.LINE, False, 0.0)
    ]


def centroid_computation_test_cases():
    """Test cases for contour center point calculation."""
    return [
        (ContourFixtures.SQUARE, Point(100, 100)),
        (ContourFixtures.RECTANGLE, Point(100, 80)),
        (ContourFixtures.TRIANGLE, Point(100, 100)),
        (ContourFixtures.TINY, Point(2.5, 2.5)),
        (ContourFixtures.LINE, Point(5, 5)),
        (ContourFixtures.SINGLE_POINT, Point(0, 0)),
        (ContourFixtures.EMPTY, None)
    ]


def format_conversion_test_cases():
    """Test cases for contour data format interoperability."""
    return [
        (ContourFixtures.SQUARE, 5.0),
        (ContourFixtures.OPEN_PATH, 5.0),
        (ContourFixtures.NEAR_CLOSED, 5.0),
        (ContourFixtures.CIRCLE, 5.0),
        (ContourFixtures.TRIANGLE, 5.0)
    ]