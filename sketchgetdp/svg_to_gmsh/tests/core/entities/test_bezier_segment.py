import pytest
from core.entities.point import Point
from core.entities.bezier_segment import BezierSegment


class TestBezierSegment:
    """Test suite for the Bézier segment entity"""
    
    def test_bezier_segment_creation_linear(self):
        """Test creation of linear Bézier segment (degree 1)"""
        p0 = Point(0, 0)
        p1 = Point(1, 1)
        segment = BezierSegment([p0, p1], degree=1)
        
        assert segment.degree == 1
        assert segment.control_points == [p0, p1]
        assert segment.start_point == p0
        assert segment.end_point == p1
    
    def test_bezier_segment_creation_quadratic(self):
        """Test creation of quadratic Bézier segment (degree 2)"""
        p0 = Point(0, 0)
        p1 = Point(0.5, 1)
        p2 = Point(1, 0)
        segment = BezierSegment([p0, p1, p2], degree=2)
        
        assert segment.degree == 2
        assert segment.control_points == [p0, p1, p2]
    
    def test_bezier_segment_creation_cubic(self):
        """Test creation of cubic Bézier segment (degree 3)"""
        p0 = Point(0, 0)
        p1 = Point(0.33, 1)
        p2 = Point(0.66, 1)
        p3 = Point(1, 0)
        segment = BezierSegment([p0, p1, p2, p3], degree=3)
        
        assert segment.degree == 3
        assert segment.control_points == [p0, p1, p2, p3]
    
    def test_invalid_control_points_count(self):
        """Test that invalid control point count raises error"""
        p0 = Point(0, 0)
        p1 = Point(1, 1)
        
        with pytest.raises(ValueError, match="Degree 2 requires 3 control points"):
            BezierSegment([p0, p1], degree=2)
        
        with pytest.raises(ValueError, match="Degree 1 requires 2 control points"):
            BezierSegment([p0], degree=1)
    
    def test_linear_bezier_evaluation(self):
        """Test evaluation of linear Bézier curve"""
        p0 = Point(0, 0)
        p1 = Point(2, 2)
        segment = BezierSegment([p0, p1], degree=1)
        
        # Test start point
        assert segment.evaluate(0.0) == p0
        # Test end point
        assert segment.evaluate(1.0) == p1
        # Test midpoint
        midpoint = segment.evaluate(0.5)
        assert midpoint == Point(1, 1)
    
    def test_quadratic_bezier_evaluation(self):
        """Test evaluation of quadratic Bézier curve"""
        p0 = Point(0, 0)
        p1 = Point(0.5, 1)
        p2 = Point(1, 0)
        segment = BezierSegment([p0, p1, p2], degree=2)
        
        # Test start and end points
        assert segment.evaluate(0.0) == p0
        assert segment.evaluate(1.0) == p2
        
        # Test midpoint (should be at p1's y-coordinate but interpolated x)
        midpoint = segment.evaluate(0.5)
        assert midpoint.x == pytest.approx(0.5)
        assert midpoint.y == pytest.approx(0.5)
    
    def test_evaluation_parameter_range(self):
        """Test that evaluation only works for t in [0,1]"""
        p0 = Point(0, 0)
        p1 = Point(1, 1)
        segment = BezierSegment([p0, p1], degree=1)
        
        with pytest.raises(ValueError, match="Parameter t must be in \\[0, 1\\]"):
            segment.evaluate(-0.1)
        
        with pytest.raises(ValueError, match="Parameter t must be in \\[0, 1\\]"):
            segment.evaluate(1.1)
    
    def test_bernstein_basis_calculation(self):
        """Test Bernstein basis polynomial calculation"""
        segment = BezierSegment([Point(0, 0), Point(1, 1)], degree=1)
        
        # For degree 1, Bernstein basis should be linear
        assert segment.bernstein_basis(0, 0.0) == 1.0
        assert segment.bernstein_basis(0, 1.0) == 0.0
        assert segment.bernstein_basis(1, 0.0) == 0.0
        assert segment.bernstein_basis(1, 1.0) == 1.0
        assert segment.bernstein_basis(0, 0.5) == pytest.approx(0.5)
        assert segment.bernstein_basis(1, 0.5) == pytest.approx(0.5)
    
    def test_bernstein_basis_invalid_index(self):
        """Test that invalid Bernstein basis index raises error"""
        segment = BezierSegment([Point(0, 0), Point(1, 1)], degree=1)
        
        with pytest.raises(ValueError, match="Index i must be between 0 and 1"):
            segment.bernstein_basis(2, 0.5)
        
        with pytest.raises(ValueError, match="Index i must be between 0 and 1"):
            segment.bernstein_basis(-1, 0.5)
    
    def test_linear_bezier_derivative(self):
        """Test derivative calculation for linear Bézier"""
        p0 = Point(0, 0)
        p1 = Point(2, 2)
        segment = BezierSegment([p0, p1], degree=1)
        
        # Derivative of linear Bézier is constant
        derivative = segment.derivative(0.5)
        expected = Point(2, 2)  # p1 - p0
        
        assert derivative == expected
        
        # Should be same at all points
        assert segment.derivative(0.0) == expected
        assert segment.derivative(1.0) == expected
    
    def test_quadratic_bezier_derivative(self):
        """Test derivative calculation for quadratic Bézier"""
        p0 = Point(0, 0)
        p1 = Point(0.5, 1)
        p2 = Point(1, 0)
        segment = BezierSegment([p0, p1, p2], degree=2)
        
        # Test derivative at start
        deriv_start = segment.derivative(0.0)
        expected_start = Point(1, 2)  # 2*(p1 - p0)
        assert deriv_start == expected_start
        
        # Test derivative at end
        deriv_end = segment.derivative(1.0)
        expected_end = Point(1, -2)  # 2*(p2 - p1)
        assert deriv_end == expected_end
    
    def test_degree_zero_bezier_derivative(self):
        """Test derivative of degree 0 Bézier (constant point)"""
        p0 = Point(1, 2)
        segment = BezierSegment([p0], degree=0)
        
        # Derivative of constant should be zero
        assert segment.derivative(0.5) == Point(0, 0)
    
    def test_derivative_parameter_range(self):
        """Test that derivative only works for t in [0,1]"""
        p0 = Point(0, 0)
        p1 = Point(1, 1)
        segment = BezierSegment([p0, p1], degree=1)
        
        with pytest.raises(ValueError, match="Parameter t must be in \\[0, 1\\]"):
            segment.derivative(-0.1)
        
        with pytest.raises(ValueError, match="Parameter t must be in \\[0, 1\\]"):
            segment.derivative(1.1)
    
    def test_get_curve_points(self):
        """Test sampling multiple points along the curve"""
        p0 = Point(0, 0)
        p1 = Point(1, 1)
        segment = BezierSegment([p0, p1], degree=1)
        
        points = segment.get_curve_points(num_points=3)
        
        assert len(points) == 3
        assert points[0] == p0
        assert points[1] == Point(0.5, 0.5)
        assert points[2] == p1
    
    def test_get_curve_points_invalid_count(self):
        """Test that invalid point count raises error"""
        p0 = Point(0, 0)
        p1 = Point(1, 1)
        segment = BezierSegment([p0, p1], degree=1)
        
        with pytest.raises(ValueError, match="Number of points must be at least 2"):
            segment.get_curve_points(num_points=1)
        
        with pytest.raises(ValueError, match="Number of points must be at least 2"):
            segment.get_curve_points(num_points=0)
    
    def test_bezier_segment_equality(self):
        """Test equality comparison between Bézier segments"""
        p0, p1 = Point(0, 0), Point(1, 1)
        p2, p3 = Point(0, 0), Point(2, 2)
        
        segment1 = BezierSegment([p0, p1], degree=1)
        segment2 = BezierSegment([p0, p1], degree=1)
        segment3 = BezierSegment([p0, p3], degree=1)
        segment4 = BezierSegment([p0, p1, p2], degree=2)
        
        assert segment1 == segment2
        assert segment1 != segment3
        assert segment1 != segment4
        assert segment1 != "not a segment"
    
    def test_bezier_segment_repr(self):
        """Test string representation of Bézier segment"""
        p0 = Point(0, 0)
        p1 = Point(1, 1)
        segment = BezierSegment([p0, p1], degree=1)
        
        repr_str = repr(segment)
        assert "BezierSegment" in repr_str
        assert "degree=1" in repr_str
        assert "control_points=2" in repr_str
    
    def test_straight_line_property(self):
        """Test that linear Bézier creates straight lines"""
        p0 = Point(0, 0)
        p1 = Point(10, 5)
        segment = BezierSegment([p0, p1], degree=1)
        
        # All points should lie on the straight line between p0 and p1
        for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
            point = segment.evaluate(t)
            expected_x = t * 10
            expected_y = t * 5
            assert point.x == pytest.approx(expected_x)
            assert point.y == pytest.approx(expected_y)
    
    def test_convex_hull_property(self):
        """Test that Bézier curve lies within convex hull of control points"""
        p0 = Point(0, 0)
        p1 = Point(2, 3)
        p2 = Point(4, 0)
        segment = BezierSegment([p0, p1, p2], degree=2)
        
        # Sample multiple points and verify they're within the triangle
        for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
            point = segment.evaluate(t)
            assert 0 <= point.x <= 4
            assert 0 <= point.y <= 1.5  # Maximum y should be at p1
    
    def test_endpoint_interpolation(self):
        """Test that curve interpolates first and last control points"""
        p0 = Point(1, 2)
        p1 = Point(3, 4)
        p2 = Point(5, 6)
        segment = BezierSegment([p0, p1, p2], degree=2)
        
        assert segment.evaluate(0.0) == p0
        assert segment.evaluate(1.0) == p2
    
    @pytest.mark.parametrize("degree,control_points,t,expected_point", [
        # Linear cases
        (1, [Point(0,0), Point(2,2)], 0.5, Point(1,1)),
        (1, [Point(1,1), Point(3,3)], 0.25, Point(1.5,1.5)),
        # Quadratic cases
        (2, [Point(0,0), Point(1,1), Point(2,0)], 0.5, Point(1,0.5)),
        (2, [Point(0,0), Point(2,2), Point(4,0)], 0.5, Point(2,1)),
    ])
    def test_parametrized_evaluation(self, degree, control_points, t, expected_point):
        """Test various Bézier curve evaluations with parameters"""
        segment = BezierSegment(control_points, degree)
        result = segment.evaluate(t)
        
        assert result.x == pytest.approx(expected_point.x)
        assert result.y == pytest.approx(expected_point.y)