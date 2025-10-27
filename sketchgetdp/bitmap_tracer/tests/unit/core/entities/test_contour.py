import pytest
import numpy as np
import sys
import os

# Add the root project directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../..'))

from core.entities.point import Point
from core.entities.contour import ClosedContour


class TestClosedContour:
    """Unit tests for ClosedContour entity."""
    
    @pytest.fixture
    def square_points(self):
        return [Point(0, 0), Point(2, 0), Point(2, 2), Point(0, 2)]
    
    @pytest.fixture
    def triangle_points(self):
        # Right triangle: base=3, height=4
        return [Point(0, 0), Point(3, 0), Point(3, 4)]
    
    @pytest.fixture
    def empty_contour(self):
        return ClosedContour(points=[], is_closed=True, closure_gap=0.0)

    def test_initialization(self, square_points):
        contour = ClosedContour(points=square_points, is_closed=True, closure_gap=0.5)
        
        assert contour.points == square_points
        assert contour.is_closed is True
        assert contour.closure_gap == 0.5

    def test_area_triangle(self, triangle_points):
        contour = ClosedContour(points=triangle_points, is_closed=True, closure_gap=0.0)
        
        # 3*4/2 = 6.0
        expected_area = 6.0
        assert contour.area == expected_area

    def test_area_square(self, square_points):
        contour = ClosedContour(points=square_points, is_closed=True, closure_gap=0.0)
        
        assert contour.area == 4.0

    @pytest.mark.parametrize("points,expected_area", [
        ([], 0.0),
        ([Point(0, 0)], 0.0),
        ([Point(0, 0), Point(1, 1)], 0.0),
    ])
    def test_area_insufficient_points(self, points, expected_area):
        contour = ClosedContour(points=points, is_closed=True, closure_gap=0.0)
        assert contour.area == expected_area

    def test_perimeter_square(self, square_points):
        contour = ClosedContour(points=square_points, is_closed=True, closure_gap=0.0)
        
        assert contour.perimeter == 8.0

    @pytest.mark.parametrize("points,expected_perimeter", [
        ([], 0.0),
        ([Point(0, 0)], 0.0),
    ])
    def test_perimeter_insufficient_points(self, points, expected_perimeter):
        contour = ClosedContour(points=points, is_closed=True, closure_gap=0.0)
        assert contour.perimeter == expected_perimeter

    def test_circularity_perfect_circle_approximation(self):
        # Create a rough circle approximation to test circularity calculation
        points = []
        radius = 5.0
        num_points = 36
        
        for i in range(num_points):
            angle = 2 * np.pi * i / num_points
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            points.append(Point(x, y))
        
        contour = ClosedContour(points=points, is_closed=True, closure_gap=0.0)
        
        # Should be close to 1.0 for a circle
        assert 0.9 < contour.circularity < 1.1

    def test_circularity_square(self, square_points):
        contour = ClosedContour(points=square_points, is_closed=True, closure_gap=0.0)
        
        # 4πA/P² = 4π*4/64 = π/4 ≈ 0.785
        expected_circularity = np.pi / 4
        assert contour.circularity == pytest.approx(expected_circularity, abs=0.01)

    def test_circularity_zero_perimeter(self, empty_contour):
        assert empty_contour.circularity == 0.0

    def test_get_center(self, square_points):
        contour = ClosedContour(points=square_points, is_closed=True, closure_gap=0.0)
        
        # Centroid of square from (0,0) to (2,2) is at (1.0, 1.0)
        assert contour.get_center() == Point(1.0, 1.0)

    def test_get_center_empty_contour(self, empty_contour):
        assert empty_contour.get_center() is None

    def test_from_numpy_contour_empty(self):
        result = ClosedContour.from_numpy_contour(np.array([]))
        
        assert result.points == []
        assert result.is_closed is True
        assert result.closure_gap == 0.0

    def test_from_numpy_contour_single_point(self):
        result = ClosedContour.from_numpy_contour(np.array([[[0, 0]]]))
        
        assert len(result.points) == 1
        assert result.points[0] == Point(0, 0)
        assert result.is_closed is False
        assert result.closure_gap == 0.0

    def test_from_numpy_contour_closed_shape(self):
        # Closing point matches start - should be detected as closed
        triangle_contour = np.array([[[0, 0]], [[4, 0]], [[0, 3]], [[0, 0]]])
        
        result = ClosedContour.from_numpy_contour(triangle_contour, tolerance=1.0)
        
        assert len(result.points) == 4
        assert result.is_closed is True
        assert result.closure_gap == 0.0

    def test_from_numpy_contour_open_shape(self):
        # Ends far from start point - should be detected as open
        open_contour = np.array([[[0, 0]], [[4, 0]], [[4, 3]], [[8, 3]]])
        
        result = ClosedContour.from_numpy_contour(open_contour, tolerance=1.0)
        
        assert len(result.points) == 4
        assert result.is_closed is False
        assert result.closure_gap > 1.0

    @pytest.mark.parametrize("tolerance,expected_closed", [
        (0.05, False),  # Strict tolerance - not closed
        (1.0, True),    # Lenient tolerance - closed
    ])
    def test_from_numpy_contour_tolerance(self, tolerance, expected_closed):
        # Slightly off from start - tolerance affects closure detection
        almost_closed_contour = np.array([
            [[0, 0]], [[2, 0]], [[2, 2]], [[0, 2]], [[0.1, 0.1]]
        ])
        
        result = ClosedContour.from_numpy_contour(almost_closed_contour, tolerance=tolerance)
        assert result.is_closed is expected_closed

    def test_property_consistency(self, triangle_points):
        contour = ClosedContour(points=triangle_points, is_closed=True, closure_gap=0.0)
        
        # For triangle with points (0,0), (3,0), (3,4)
        expected_area = 6.0      # 3*4/2
        expected_perimeter = 12.0  # 3 + 4 + 5
        expected_circularity = (4 * np.pi * expected_area) / (expected_perimeter ** 2)
        expected_center = Point(2.0, 1.3333333333333333)  # (0+3+3)/3, (0+0+4)/3
        
        assert contour.area == expected_area
        assert contour.perimeter == expected_perimeter
        assert contour.circularity == pytest.approx(expected_circularity, abs=0.001)
        assert contour.get_center() == expected_center

    def test_immutability_of_points(self):
        """Test that external changes to points list don't affect the contour."""
        original_points = [Point(0, 0), Point(1, 0), Point(1, 1)]
        contour = ClosedContour(points=original_points, is_closed=True, closure_gap=0.0)
        
        original_point_count = len(contour.points)
        original_area = contour.area
        
        # Modify external list - contour should be unaffected
        original_points.append(Point(0, 1))
        
        assert len(contour.points) == original_point_count
        assert contour.area == original_area
        
        # New contour with modified list should be different
        new_contour = ClosedContour(points=original_points, is_closed=True, closure_gap=0.0)
        assert len(new_contour.points) == 4
        assert new_contour.area != original_area

    @pytest.mark.parametrize("points,expected_closed,expected_gap", [
        ([Point(0, 0), Point(1, 0), Point(1, 1), Point(0, 1)], True, 0.0),
        ([Point(0, 0), Point(1, 0), Point(1, 1)], False, 0.0),
    ])
    def test_closure_properties(self, points, expected_closed, expected_gap):
        contour = ClosedContour(points=points, is_closed=expected_closed, closure_gap=expected_gap)
        
        assert contour.is_closed == expected_closed
        assert contour.closure_gap == expected_gap