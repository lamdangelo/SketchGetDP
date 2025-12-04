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

    def test_vector_addition(self):
        """Test vector addition of two points"""
        point1 = Point(1, 2)
        point2 = Point(3, 4)
        result = point1 + point2
        
        assert result == Point(4, 6)
        assert isinstance(result, Point)
    
    def test_vector_subtraction(self):
        """Test vector subtraction of two points"""
        point1 = Point(5, 6)
        point2 = Point(2, 3)
        result = point1 - point2
        
        assert result == Point(3, 3)
        assert isinstance(result, Point)
    
    def test_scalar_multiplication(self):
        """Test scalar multiplication"""
        point = Point(2, 3)
        result = point * 2.5
        
        assert result == Point(5.0, 7.5)
        assert isinstance(result, Point)
    
    def test_reverse_scalar_multiplication(self):
        """Test reverse scalar multiplication"""
        point = Point(2, 3)
        result = 2.5 * point
        
        assert result == Point(5.0, 7.5)
        assert isinstance(result, Point)
    
    def test_scalar_division(self):
        """Test scalar division"""
        point = Point(6, 9)
        result = point / 3
        
        assert result == Point(2.0, 3.0)
        assert isinstance(result, Point)
    
    def test_scalar_division_by_zero(self):
        """Test that scalar division by zero raises ValueError"""
        point = Point(1, 2)
        
        with pytest.raises(ValueError, match="Division by zero"):
            point / 0
    
    def test_norm_calculation(self):
        """Test Euclidean norm calculation"""
        point = Point(3, 4)
        norm = point.norm()
        
        assert norm == 5.0
        assert isinstance(norm, float)
    
    def test_norm_zero(self):
        """Test norm calculation for zero vector"""
        point = Point(0, 0)
        norm = point.norm()
        
        assert norm == 0.0
    
    def test_equality_with_floating_point_precision(self):
        """Test equality comparison with floating point precision"""
        point1 = Point(1.0, 2.0)
        point2 = Point(1.0 + 1e-10, 2.0 - 1e-10)  # Very close values
        
        assert point1 == point2  # Should be equal due to math.isclose
    
    def test_equality_with_different_types(self):
        """Test equality comparison with non-Point types"""
        point = Point(1, 2)
        
        assert point != (1, 2)
        assert point != [1, 2]
        assert point != "Point(1, 2)"
        assert point != 1
    
    def test_vector_operations_chain(self):
        """Test chaining of vector operations"""
        point1 = Point(1, 2)
        point2 = Point(3, 4)
        point3 = Point(5, 6)
        
        result = point1 + point2 - point3
        expected = Point(-1, 0)
        
        assert result == expected
    
    def test_mixed_operations(self):
        """Test mixed scalar and vector operations"""
        point1 = Point(1, 2)
        point2 = Point(3, 4)
        
        result = 2 * point1 + point2 / 2
        expected = Point(3.5, 6.0)  # 2*(1,2) + (3,4)/2 = (2,4) + (1.5,2) = (3.5,6)
        
        assert result == expected
    
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
    
    @pytest.mark.parametrize("x,y,scalar,expected_mul_x,expected_mul_y,expected_div_x,expected_div_y", [
        (2, 3, 2, 4, 6, 1, 1.5),           # Integer multiplication and division
        (1, 2, 0.5, 0.5, 1.0, 2.0, 4.0),   # Float multiplication and division
        (4, 6, 2, 8, 12, 2, 3),            # Integer multiplication and division
        (5, 10, 2.5, 12.5, 25.0, 2.0, 4.0), # Float multiplication and division
    ])
    def test_scalar_operations(self, x, y, scalar, expected_mul_x, expected_mul_y, expected_div_x, expected_div_y):
        """Test various scalar multiplication and division scenarios"""
        point = Point(x, y)
        
        mul_result = point * scalar
        div_result = point / scalar
        
        assert mul_result == Point(expected_mul_x, expected_mul_y)
        assert div_result == Point(expected_div_x, expected_div_y)
    
    def test_commutative_property(self):
        """Test commutative property of addition"""
        point1 = Point(1, 2)
        point2 = Point(3, 4)
        
        assert point1 + point2 == point2 + point1
    
    def test_associative_property_addition(self):
        """Test associative property of addition"""
        point1 = Point(1, 2)
        point2 = Point(3, 4)
        point3 = Point(5, 6)
        
        result1 = (point1 + point2) + point3
        result2 = point1 + (point2 + point3)
        
        assert result1 == result2
    
    def test_distributive_property(self):
        """Test distributive property of scalar multiplication over addition"""
        point1 = Point(1, 2)
        point2 = Point(3, 4)
        scalar = 2
        
        result1 = scalar * (point1 + point2)
        result2 = (scalar * point1) + (scalar * point2)
        
        assert result1 == result2