# tests/core/entities/test_line.py
import pytest
import math
from typing import List, Tuple

from core.entities.line import Line
from core.entities.point import Point


class TestLine:
    """Test suite for the Line entity representing a line segment between two points."""
    
    def test_line_creation(self):
        """Test that a line can be created with start and end points"""
        start = Point(0, 0)
        end = Point(3, 4)
        line = Line(start, end)
        
        assert line.start == start
        assert line.end == end
    
    def test_line_immutability(self):
        """Test that Line is immutable"""
        start = Point(1, 2)
        end = Point(3, 4)
        line = Line(start, end)
        
        with pytest.raises(AttributeError):
            line.start = Point(5, 6)
        with pytest.raises(AttributeError):
            line.end = Point(7, 8)
    
    def test_line_equality(self):
        """Test that lines with same start and end points are equal"""
        line1 = Line(Point(1, 2), Point(3, 4))
        line2 = Line(Point(1, 2), Point(3, 4))
        line3 = Line(Point(1, 2), Point(5, 6))
        
        assert line1 == line2
        assert line1 != line3
    
    def test_line_hash(self):
        """Test that lines are hashable"""
        line1 = Line(Point(1, 2), Point(3, 4))
        line2 = Line(Point(1, 2), Point(3, 4))
        line3 = Line(Point(5, 6), Point(7, 8))
        
        line_set = {line1, line2, line3}
        assert len(line_set) == 2  # line1 and line2 are duplicates
        assert line1 in line_set
        assert line2 in line_set
        assert line3 in line_set
    
    def test_line_length(self):
        """Test length calculation for line segment"""
        line = Line(Point(0, 0), Point(3, 4))
        length = line.length
        
        assert length == 5.0  # 3-4-5 triangle
    
    def test_line_length_zero(self):
        """Test length calculation for zero-length line"""
        line = Line(Point(1, 1), Point(1, 1))
        length = line.length
        
        assert length == 0.0
    
    def test_line_length_negative_coordinates(self):
        """Test length calculation with negative coordinates"""
        line = Line(Point(-1, -1), Point(2, 3))
        length = line.length
        
        expected = math.sqrt((2 - (-1))**2 + (3 - (-1))**2)
        assert length == pytest.approx(expected)
    
    def test_line_midpoint(self):
        """Test midpoint calculation"""
        line = Line(Point(0, 0), Point(4, 6))
        midpoint = line.midpoint
        
        assert midpoint == Point(2, 3)
    
    def test_line_slope(self):
        """Test slope calculation"""
        line = Line(Point(1, 1), Point(4, 5))
        slope = line.slope
        
        assert slope == pytest.approx(4/3)
    
    def test_line_slope_vertical(self):
        """Test slope calculation for vertical line"""
        line = Line(Point(1, 1), Point(1, 5))
        
        with pytest.raises(ValueError, match="Vertical line has undefined slope"):
            _ = line.slope
    
    def test_line_slope_horizontal(self):
        """Test slope calculation for horizontal line"""
        line = Line(Point(1, 2), Point(5, 2))
        slope = line.slope
        
        assert slope == 0.0
    
    def test_line_is_vertical(self):
        """Test vertical line detection"""
        vertical_line = Line(Point(1, 1), Point(1, 5))
        non_vertical_line = Line(Point(1, 1), Point(3, 5))
        
        assert vertical_line.is_vertical is True
        assert non_vertical_line.is_vertical is False
    
    def test_line_is_horizontal(self):
        """Test horizontal line detection"""
        horizontal_line = Line(Point(1, 2), Point(5, 2))
        non_horizontal_line = Line(Point(1, 1), Point(3, 5))
        
        assert horizontal_line.is_horizontal is True
        assert non_horizontal_line.is_horizontal is False
    
    def test_line_contains_point(self):
        """Test if line contains a point"""
        line = Line(Point(0, 0), Point(4, 4))
        
        # Points on the line
        assert line.contains_point(Point(1, 1)) is True
        assert line.contains_point(Point(2, 2)) is True
        assert line.contains_point(Point(4, 4)) is True
        
        # Points not on the line
        assert line.contains_point(Point(1, 2)) is False
        assert line.contains_point(Point(5, 5)) is False
    
    def test_line_parallel_to(self):
        """Test parallel line detection"""
        line1 = Line(Point(0, 0), Point(4, 4))
        line2 = Line(Point(1, 0), Point(5, 4))  # Parallel
        line3 = Line(Point(0, 0), Point(4, 5))  # Not parallel
        
        assert line1.is_parallel_to(line2) is True
        assert line1.is_parallel_to(line3) is False
    
    def test_line_reversed(self):
        """Test line reversal"""
        line = Line(Point(1, 2), Point(3, 4))
        reversed_line = line.reversed()
        
        assert reversed_line.start == Point(3, 4)
        assert reversed_line.end == Point(1, 2)
        assert line.length == reversed_line.length
    
    def test_line_repr(self):
        """Test the string representation of Line"""
        line = Line(Point(1, 2), Point(3, 4))
        repr_str = repr(line)
        
        assert "Line" in repr_str
        assert "Point(x=1, y=2)" in repr_str  # Fixed: match actual Point repr
        assert "Point(x=3, y=4)" in repr_str  # Fixed: match actual Point repr
    
    def test_line_str(self):
        """Test the human-readable string representation"""
        line = Line(Point(1, 2), Point(3, 4))
        str_repr = str(line)
        
        assert "Line" in str_repr
        assert "Point(x=1, y=2)" in str_repr  # Fixed: match actual Point str
        assert "Point(x=3, y=4)" in str_repr  # Fixed: match actual Point str
    
    @pytest.mark.parametrize("start_x,start_y,end_x,end_y,expected_length", [
        (0, 0, 3, 4, 5.0),           # 3-4-5 triangle
        (1, 1, 1, 1, 0.0),           # Zero length
        (-1, -1, 2, 3, 5.0),         # Negative coordinates
        (0, 0, 0, 0, 0.0),           # Both at origin
        (1.5, 2.5, 4.5, 6.5, 5.0),   # Float coordinates
    ])
    def test_length_combinations(self, start_x, start_y, end_x, end_y, expected_length):
        """Test various length calculation scenarios"""
        start = Point(start_x, start_y)
        end = Point(end_x, end_y)
        line = Line(start, end)
        
        assert line.length == pytest.approx(expected_length)
    
    @pytest.mark.parametrize("start_x,start_y,end_x,end_y,point_x,point_y,expected", [
        (0, 0, 4, 4, 2, 2, True),    # Point on line
        (0, 0, 4, 4, 1, 2, False),   # Point off line
        (0, 0, 4, 4, 5, 5, False),   # Point beyond end
        (0, 0, 4, 4, 0, 0, True),    # Point at start
        (0, 0, 4, 4, 4, 4, True),    # Point at end
    ])
    def test_contains_point_combinations(self, start_x, start_y, end_x, end_y, point_x, point_y, expected):
        """Test various point containment scenarios"""
        line = Line(Point(start_x, start_y), Point(end_x, end_y))
        point = Point(point_x, point_y)
        
        assert line.contains_point(point) == expected