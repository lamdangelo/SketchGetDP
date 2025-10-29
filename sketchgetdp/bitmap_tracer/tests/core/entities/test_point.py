import pytest
import math
from typing import Tuple
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
sys.path.insert(0, project_root)

from bitmap_tracer.core.entities.point import Point, PointData

class TestPoint:
    """Test suite for Point value object"""
    
    def test_point_creation(self):
        """Test basic Point creation with x and y coordinates"""
        point = Point(3.5, 7.2)
        assert point.x == 3.5
        assert point.y == 7.2
    
    def test_point_immutability(self):
        """Test that Point objects are immutable (dataclass frozen behavior)"""
        point = Point(1.0, 2.0)
        
        # Verify attributes cannot be modified directly
        with pytest.raises(AttributeError):
            point.x = 5.0
        with pytest.raises(AttributeError):
            point.y = 5.0
    
    def test_to_tuple(self):
        """Test conversion to tuple format"""
        point = Point(3.14, 2.71)
        result = point.to_tuple()
        
        assert isinstance(result, Tuple)
        assert result == (3.14, 2.71)
        assert result[0] == 3.14
        assert result[1] == 2.71
    
    def test_distance_to_same_point(self):
        """Test distance calculation to the same point"""
        point1 = Point(5.0, 5.0)
        point2 = Point(5.0, 5.0)
        
        distance = point1.distance_to(point2)
        assert distance == 0.0
    
    def test_distance_to_different_points(self):
        """Test distance calculation to different points"""
        point1 = Point(0.0, 0.0)
        point2 = Point(3.0, 4.0)  # 3-4-5 triangle
        
        distance = point1.distance_to(point2)
        assert distance == 5.0
    
    def test_distance_to_negative_coordinates(self):
        """Test distance calculation with negative coordinates"""
        point1 = Point(-1.0, -1.0)
        point2 = Point(2.0, 3.0)
        
        distance = point1.distance_to(point2)
        expected_distance = math.sqrt((3.0 ** 2) + (4.0 ** 2))  # 5.0
        assert distance == expected_distance
    
    def test_from_tuple_creation(self):
        """Test factory method creating Point from tuple"""
        input_tuple = (10.5, 20.7)
        point = Point.from_tuple(input_tuple)
        
        assert point.x == 10.5
        assert point.y == 20.7
        assert isinstance(point, Point)
    
    def test_from_tuple_with_negative_values(self):
        """Test factory method with negative tuple values"""
        input_tuple = (-5.5, -10.2)
        point = Point.from_tuple(input_tuple)
        
        assert point.x == -5.5
        assert point.y == -10.2
    
    def test_equality_comparison(self):
        """Test that Points with same coordinates are equal"""
        point1 = Point(1.0, 2.0)
        point2 = Point(1.0, 2.0)
        
        assert point1 == point2
    
    def test_inequality_comparison(self):
        """Test that Points with different coordinates are not equal"""
        point1 = Point(1.0, 2.0)
        point2 = Point(1.0, 3.0)
        point3 = Point(2.0, 2.0)
        
        assert point1 != point2
        assert point1 != point3
    
    def test_hashability(self):
        """Test that Point objects are hashable (required for value objects)"""
        point1 = Point(1.0, 2.0)
        point2 = Point(1.0, 2.0)
        
        # Should be able to create sets and use as dict keys
        point_set = {point1, point2}
        assert len(point_set) == 1  # Duplicates should be removed
        
        point_dict = {point1: "value"}
        assert point_dict[point2] == "value"  # Same coordinates should access same key


class TestPointData:
    """Test suite for PointData enhanced point information"""
    
    def test_point_data_creation_defaults(self):
        """Test PointData creation with default values"""
        point_data = PointData(1.0, 2.0)
        
        assert point_data.x == 1.0
        assert point_data.y == 2.0
        assert point_data.radius == 0.0
        assert point_data.is_small_point is False
    
    def test_point_data_creation_custom_values(self):
        """Test PointData creation with custom radius and small point flag"""
        point_data = PointData(1.0, 2.0, radius=5.5, is_small_point=True)
        
        assert point_data.x == 1.0
        assert point_data.y == 2.0
        assert point_data.radius == 5.5
        assert point_data.is_small_point is True
    
    def test_point_data_immutability(self):
        """Test that PointData objects are immutable"""
        point_data = PointData(1.0, 2.0, radius=3.0, is_small_point=True)
        
        # Verify attributes cannot be modified directly
        with pytest.raises(AttributeError):
            point_data.x = 5.0
        with pytest.raises(AttributeError):
            point_data.y = 5.0
        with pytest.raises(AttributeError):
            point_data.radius = 10.0
        with pytest.raises(AttributeError):
            point_data.is_small_point = False
    
    def test_center_property(self):
        """Test center property returns correct Point"""
        point_data = PointData(3.5, 7.2, radius=2.0)
        center = point_data.center
        
        assert isinstance(center, Point)
        assert center.x == 3.5
        assert center.y == 7.2
    
    def test_to_point_conversion(self):
        """Test conversion to basic Point object"""
        point_data = PointData(4.5, 6.7, radius=1.5, is_small_point=True)
        point = point_data.to_point()
        
        assert isinstance(point, Point)
        assert point.x == 4.5
        assert point.y == 6.7
        # Should not include radius or is_small_point in basic Point
    
    def test_equality_comparison_point_data(self):
        """Test that PointData objects with same attributes are equal"""
        point_data1 = PointData(1.0, 2.0, radius=3.0, is_small_point=True)
        point_data2 = PointData(1.0, 2.0, radius=3.0, is_small_point=True)
        
        assert point_data1 == point_data2
    
    def test_inequality_comparison_point_data(self):
        """Test that PointData objects with different attributes are not equal"""
        point_data1 = PointData(1.0, 2.0, radius=3.0, is_small_point=True)
        point_data2 = PointData(1.0, 2.0, radius=4.0, is_small_point=True)  # Different radius
        point_data3 = PointData(1.0, 2.0, radius=3.0, is_small_point=False)  # Different flag
        
        assert point_data1 != point_data2
        assert point_data1 != point_data3
    
    def test_hashability_point_data(self):
        """Test that PointData objects are hashable"""
        point_data1 = PointData(1.0, 2.0, radius=3.0, is_small_point=True)
        point_data2 = PointData(1.0, 2.0, radius=3.0, is_small_point=True)
        
        # Should be able to create sets and use as dict keys
        point_data_set = {point_data1, point_data2}
        assert len(point_data_set) == 1  # Duplicates should be removed
        
        point_data_dict = {point_data1: "value"}
        assert point_data_dict[point_data2] == "value"


class TestPointAndPointDataIntegration:
    """Test integration between Point and PointData classes"""
    
    def test_point_data_center_returns_point(self):
        """Test that PointData.center returns a proper Point object"""
        point_data = PointData(10.0, 20.0, radius=5.0)
        center_point = point_data.center
        
        # Verify it's a Point with correct coordinates
        assert isinstance(center_point, Point)
        assert center_point.x == 10.0
        assert center_point.y == 20.0
        
        # Verify Point methods work on the returned center
        distance = center_point.distance_to(Point(13.0, 24.0))
        expected_distance = math.sqrt(3.0**2 + 4.0**2)  # 5.0
        assert distance == expected_distance
    
    def test_point_data_to_point_conversion(self):
        """Test that to_point() returns a proper Point object"""
        point_data = PointData(15.0, 25.0, radius=10.0, is_small_point=False)
        basic_point = point_data.to_point()
        
        assert isinstance(basic_point, Point)
        assert basic_point.x == 15.0
        assert basic_point.y == 25.0
        
        # Verify the converted Point has all Point functionality
        tuple_result = basic_point.to_tuple()
        assert tuple_result == (15.0, 25.0)
    
    def test_interoperability_between_point_and_point_data(self):
        """Test that Point and PointData can work together seamlessly"""
        point_data = PointData(5.0, 5.0, radius=2.0)
        regular_point = Point(8.0, 9.0)
        
        # PointData.center should work with Point.distance_to
        distance = point_data.center.distance_to(regular_point)
        expected_distance = math.sqrt(3.0**2 + 4.0**2)  # 5.0
        assert distance == expected_distance
        
        # PointData.to_point() should create compatible Point objects
        converted_point = point_data.to_point()
        assert converted_point.distance_to(regular_point) == distance