import pytest
import math

from core.entities.point import Point

class TestPoint:
    """Test suite for the minimal Point entity with Euclidean distance"""
    
    def test_point_creation(self):
        """Test that a point can be created with coordinates"""
        point = Point(3, 4)
        assert point.x == 3
        assert point.y == 4
    
    def test_point_default_origin(self):
        """Test that point defaults to origin (0,0)"""
        point = Point()
        assert point.x == 0
        assert point.y == 0
    
    def test_point_immutability(self):
        """Test that Point is immutable"""
        point = Point(1, 2)
        
        with pytest.raises(AttributeError):
            point.x = 5
        with pytest.raises(AttributeError):
            point.y = 5
    
    def test_point_equality(self):
        """Test that points with same coordinates are equal"""
        point1 = Point(3, 4)
        point2 = Point(3, 4)
        point3 = Point(3, 5)
        
        assert point1 == point2
        assert point1 != point3
    
    def test_point_hash(self):
        """Test that points are hashable"""
        point1 = Point(1, 2)
        point2 = Point(1, 2)
        point3 = Point(3, 4)
        
        point_set = {point1, point2, point3}
        assert len(point_set) == 2  # point1 and point2 are duplicates
        assert point1 in point_set
        assert point2 in point_set
        assert point3 in point_set
    
    def test_point_repr(self):
        """Test the string representation of Point"""
        point = Point(5, 6)
        repr_str = repr(point)
        
        assert "Point" in repr_str
        assert "5" in repr_str
        assert "6" in repr_str
    
    def test_point_str(self):
        """Test the human-readable string representation"""
        point = Point(7, 8)
        str_repr = str(point)
        
        assert "7" in str_repr
        assert "8" in str_repr
    
    def test_distance_to_origin(self):
        """Test distance calculation from origin"""
        point = Point(3, 4)
        distance = point.distance_to_origin()
        
        assert distance == 5.0  # 3-4-5 triangle
    
    def test_distance_to_origin_zero(self):
        """Test distance from origin for origin point"""
        point = Point(0, 0)
        distance = point.distance_to_origin()
        
        assert distance == 0.0
    
    def test_distance_to_other_point(self):
        """Test distance calculation between two points"""
        point1 = Point(1, 1)
        point2 = Point(4, 5)
        
        distance = point1.distance_to(point2)
        expected_distance = math.sqrt((4-1)**2 + (5-1)**2)
        
        assert distance == pytest.approx(expected_distance)
    
    def test_distance_to_same_point(self):
        """Test distance from point to itself"""
        point = Point(3, 4)
        distance = point.distance_to(point)
        
        assert distance == 0.0
    
    def test_invalid_coordinate_types(self):
        """Test that point rejects non-numeric coordinates"""
        with pytest.raises(TypeError):
            Point("1", 2)
        with pytest.raises(TypeError):
            Point(1, "2")
        with pytest.raises(TypeError):
            Point(None, 2)
        with pytest.raises(TypeError):
            Point(1, [2])
    
    def test_nan_coordinates(self):
        """Test that point rejects NaN values"""
        with pytest.raises(ValueError):
            Point(float('nan'), 1)
        with pytest.raises(ValueError):
            Point(1, float('nan'))
    
    def test_integer_coordinates(self):
        """Test that point accepts integer coordinates"""
        point = Point(1, 2)  # integers
        assert point.x == 1
        assert point.y == 2
        
        # Should work with float operations
        distance = point.distance_to_origin()
        assert isinstance(distance, float)
    
    def test_float_coordinates(self):
        """Test that point accepts float coordinates"""
        point = Point(1.5, 2.5)
        assert point.x == 1.5
        assert point.y == 2.5
    
    def test_large_coordinates(self):
        """Test with large coordinate values"""
        point1 = Point(1e6, 2e6)
        point2 = Point(3e6, 4e6)
        
        distance = point1.distance_to(point2)
        expected = math.sqrt((2e6)**2 + (2e6)**2)
        
        assert distance == pytest.approx(expected)
    
    @pytest.mark.parametrize("x1,y1,x2,y2,expected_distance", [
        (0, 0, 3, 4, 5.0),           # 3-4-5 triangle
        (1, 1, 1, 1, 0.0),           # Same point
        (-1, -1, 2, 3, 5.0),         # Negative coordinates
        (0, 0, 0, 0, 0.0),           # Both at origin
        (1.5, 2.5, 4.5, 6.5, 5.0),   # Float coordinates
    ])
    def test_distance_combinations(self, x1, y1, x2, y2, expected_distance):
        """Test various distance calculation scenarios"""
        point1 = Point(x1, y1)
        point2 = Point(x2, y2)
        
        assert point1.distance_to(point2) == pytest.approx(expected_distance)