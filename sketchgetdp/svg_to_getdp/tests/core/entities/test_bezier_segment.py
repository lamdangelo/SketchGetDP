"""
Unit tests for BezierSegment class.

Tests Bézier segment functionality including creation, evaluation,
derivative calculation, and geometric properties.
"""
import pytest
from core.entities.point import Point
from core.entities.bezier_segment import BezierSegment


class TestBezierSegment:
    """Test suite for BezierSegment class."""
    
    # ==================== Initialization Tests ====================
    
    def test_bezier_segment_creation_linear(self):
        """Test creation of linear Bézier segment (degree 1)."""
        p0 = Point(0.0, 0.0)
        p1 = Point(1.0, 1.0)
        segment = BezierSegment([p0, p1], degree=1)
        
        assert segment.degree == 1
        assert segment.control_points == [p0, p1]
        assert segment.start_point == p0
        assert segment.end_point == p1
    
    def test_bezier_segment_creation_quadratic(self):
        """Test creation of quadratic Bézier segment (degree 2)."""
        p0 = Point(0.0, 0.0)
        p1 = Point(0.5, 1.0)
        p2 = Point(1.0, 0.0)
        segment = BezierSegment([p0, p1, p2], degree=2)
        
        assert segment.degree == 2
        assert segment.control_points == [p0, p1, p2]
    
    def test_bezier_segment_creation_cubic(self):
        """Test creation of cubic Bézier segment (degree 3)."""
        p0 = Point(0.0, 0.0)
        p1 = Point(0.33, 1.0)
        p2 = Point(0.66, 1.0)
        p3 = Point(1.0, 0.0)
        segment = BezierSegment([p0, p1, p2, p3], degree=3)
        
        assert segment.degree == 3
        assert segment.control_points == [p0, p1, p2, p3]
    
    def test_invalid_control_points_count(self):
        """Test that invalid control point count raises error."""
        p0 = Point(0.0, 0.0)
        p1 = Point(1.0, 1.0)
        
        with pytest.raises(ValueError, match="Degree 2 requires 3 control points"):
            BezierSegment([p0, p1], degree=2)
        
        with pytest.raises(ValueError, match="Degree 1 requires 2 control points"):
            BezierSegment([p0], degree=1)

    # ==================== Evaluation Tests ====================
    
    def test_linear_bezier_evaluation(self):
        """Test evaluation of linear Bézier curve."""
        p0 = Point(0.0, 0.0)
        p1 = Point(2.0, 2.0)
        segment = BezierSegment([p0, p1], degree=1)
        
        # Test start point
        result_start = segment.evaluate(0.0)
        assert result_start.x == pytest.approx(p0.x)
        assert result_start.y == pytest.approx(p0.y)
        
        # Test end point
        result_end = segment.evaluate(1.0)
        assert result_end.x == pytest.approx(p1.x)
        assert result_end.y == pytest.approx(p1.y)
        
        # Test midpoint
        midpoint = segment.evaluate(0.5)
        assert midpoint.x == pytest.approx(1.0)
        assert midpoint.y == pytest.approx(1.0)
    
    def test_quadratic_bezier_evaluation(self):
        """Test evaluation of quadratic Bézier curve."""
        p0 = Point(0.0, 0.0)
        p1 = Point(0.5, 1.0)
        p2 = Point(1.0, 0.0)
        segment = BezierSegment([p0, p1, p2], degree=2)
        
        # Test start and end points
        result_start = segment.evaluate(0.0)
        assert result_start.x == pytest.approx(p0.x)
        assert result_start.y == pytest.approx(p0.y)
        
        result_end = segment.evaluate(1.0)
        assert result_end.x == pytest.approx(p2.x)
        assert result_end.y == pytest.approx(p2.y)
        
        # Test midpoint
        midpoint = segment.evaluate(0.5)
        assert midpoint.x == pytest.approx(0.5)
        assert midpoint.y == pytest.approx(0.5)
    
    def test_evaluation_parameter_range(self):
        """Test that evaluation only works for t in [0,1]."""
        p0 = Point(0.0, 0.0)
        p1 = Point(1.0, 1.0)
        segment = BezierSegment([p0, p1], degree=1)
        
        with pytest.raises(ValueError, match="Parameter t must be in \\[0, 1\\]"):
            segment.evaluate(-0.1)
        
        with pytest.raises(ValueError, match="Parameter t must be in \\[0, 1\\]"):
            segment.evaluate(1.1)

    # ==================== Bernstein Basis Tests ====================
    
    def test_bernstein_basis_calculation(self):
        """Test Bernstein basis polynomial calculation."""
        segment = BezierSegment([Point(0.0, 0.0), Point(1.0, 1.0)], degree=1)
        
        # For degree 1, Bernstein basis should be linear
        assert segment.bernstein_basis(0, 0.0) == 1.0
        assert segment.bernstein_basis(0, 1.0) == 0.0
        assert segment.bernstein_basis(1, 0.0) == 0.0
        assert segment.bernstein_basis(1, 1.0) == 1.0
        assert segment.bernstein_basis(0, 0.5) == pytest.approx(0.5)
        assert segment.bernstein_basis(1, 0.5) == pytest.approx(0.5)
    
    def test_bernstein_basis_invalid_index(self):
        """Test that invalid Bernstein basis index raises error."""
        segment = BezierSegment([Point(0.0, 0.0), Point(1.0, 1.0)], degree=1)
        
        with pytest.raises(ValueError, match="Index i must be between 0 and 1"):
            segment.bernstein_basis(2, 0.5)
        
        with pytest.raises(ValueError, match="Index i must be between 0 and 1"):
            segment.bernstein_basis(-1, 0.5)

    # ==================== Derivative Tests ====================
    
    def test_linear_bezier_derivative(self):
        """Test derivative calculation for linear Bézier."""
        p0 = Point(0.0, 0.0)
        p1 = Point(2.0, 2.0)
        segment = BezierSegment([p0, p1], degree=1)
        
        # Derivative of linear Bézier is constant
        derivative = segment.derivative(0.5)
        expected_x = 2.0  # p1.x - p0.x
        expected_y = 2.0  # p1.y - p0.y
        
        assert derivative.x == pytest.approx(expected_x)
        assert derivative.y == pytest.approx(expected_y)
        
        # Should be same at all points
        deriv_start = segment.derivative(0.0)
        assert deriv_start.x == pytest.approx(expected_x)
        assert deriv_start.y == pytest.approx(expected_y)
        
        deriv_end = segment.derivative(1.0)
        assert deriv_end.x == pytest.approx(expected_x)
        assert deriv_end.y == pytest.approx(expected_y)
    
    def test_quadratic_bezier_derivative(self):
        """Test derivative calculation for quadratic Bézier."""
        p0 = Point(0.0, 0.0)
        p1 = Point(0.5, 1.0)
        p2 = Point(1.0, 0.0)
        segment = BezierSegment([p0, p1, p2], degree=2)
        
        # Test derivative at start
        deriv_start = segment.derivative(0.0)
        # For quadratic: 2 * (p1 - p0) at t=0
        expected_start_x = 1.0  # 2 * (0.5 - 0)
        expected_start_y = 2.0  # 2 * (1 - 0)
        assert deriv_start.x == pytest.approx(expected_start_x)
        assert deriv_start.y == pytest.approx(expected_start_y)
        
        # Test derivative at end
        deriv_end = segment.derivative(1.0)
        # For quadratic: 2 * (p2 - p1) at t=1
        expected_end_x = 1.0   # 2 * (1 - 0.5)
        expected_end_y = -2.0  # 2 * (0 - 1)
        assert deriv_end.x == pytest.approx(expected_end_x)
        assert deriv_end.y == pytest.approx(expected_end_y)
        
        # Test derivative at midpoint
        deriv_mid = segment.derivative(0.5)
        # For quadratic: 2 * ((1-t)*(p1-p0) + t*(p2-p1)) at t=0.5
        expected_mid_x = 1.0
        expected_mid_y = 0.0
        assert deriv_mid.x == pytest.approx(expected_mid_x)
        assert deriv_mid.y == pytest.approx(expected_mid_y)
    
    def test_degree_zero_bezier_derivative(self):
        """Test derivative of degree 0 Bézier (constant point)."""
        p0 = Point(1.0, 2.0)
        segment = BezierSegment([p0], degree=0)
        
        # Derivative of constant should be zero
        derivative = segment.derivative(0.5)
        assert derivative.x == pytest.approx(0.0)
        assert derivative.y == pytest.approx(0.0)
    
    def test_derivative_parameter_range(self):
        """Test that derivative only works for t in [0,1]."""
        p0 = Point(0.0, 0.0)
        p1 = Point(1.0, 1.0)
        segment = BezierSegment([p0, p1], degree=1)
        
        with pytest.raises(ValueError, match="Parameter t must be in \\[0, 1\\]"):
            segment.derivative(-0.1)
        
        with pytest.raises(ValueError, match="Parameter t must be in \\[0, 1\\]"):
            segment.derivative(1.1)

    # ==================== Sampling Tests ====================
    
    def test_get_curve_points(self):
        """Test sampling multiple points along the curve."""
        p0 = Point(0.0, 0.0)
        p1 = Point(1.0, 1.0)
        segment = BezierSegment([p0, p1], degree=1)
        
        points = segment.get_curve_points(num_points=3)
        
        assert len(points) == 3
        assert points[0].x == pytest.approx(p0.x)
        assert points[0].y == pytest.approx(p0.y)
        assert points[1].x == pytest.approx(0.5)
        assert points[1].y == pytest.approx(0.5)
        assert points[2].x == pytest.approx(p1.x)
        assert points[2].y == pytest.approx(p1.y)
    
    def test_get_curve_points_invalid_count(self):
        """Test that invalid point count raises error."""
        p0 = Point(0.0, 0.0)
        p1 = Point(1.0, 1.0)
        segment = BezierSegment([p0, p1], degree=1)
        
        with pytest.raises(ValueError, match="Number of points must be at least 2"):
            segment.get_curve_points(num_points=1)
        
        with pytest.raises(ValueError, match="Number of points must be at least 2"):
            segment.get_curve_points(num_points=0)

    # ==================== Property Tests ====================
    
    def test_straight_line_property(self):
        """Test that linear Bézier creates straight lines."""
        p0 = Point(0.0, 0.0)
        p1 = Point(10.0, 5.0)
        segment = BezierSegment([p0, p1], degree=1)
        
        # All points should lie on the straight line between p0 and p1
        for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
            point = segment.evaluate(t)
            expected_x = t * 10.0
            expected_y = t * 5.0
            assert point.x == pytest.approx(expected_x)
            assert point.y == pytest.approx(expected_y)
    
    def test_convex_hull_property(self):
        """Test that Bézier curve lies within convex hull of control points."""
        p0 = Point(0.0, 0.0)
        p1 = Point(2.0, 3.0)
        p2 = Point(4.0, 0.0)
        segment = BezierSegment([p0, p1, p2], degree=2)
        
        # Sample multiple points and verify they're within the triangle
        for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
            point = segment.evaluate(t)
            assert 0.0 <= point.x <= 4.0
            assert 0.0 <= point.y <= 1.5

    # ==================== Interface Tests ====================
    
    def test_bezier_segment_equality(self):
        """Test equality comparison between Bézier segments."""
        p0, p1 = Point(0.0, 0.0), Point(1.0, 1.0)
        p2, p3 = Point(0.0, 0.0), Point(2.0, 2.0)
        
        segment1 = BezierSegment([p0, p1], degree=1)
        segment2 = BezierSegment([p0, p1], degree=1)
        segment3 = BezierSegment([p0, p3], degree=1)
        segment4 = BezierSegment([p0, p1, p2], degree=2)
        
        assert segment1 == segment2
        assert segment1 != segment3
        assert segment1 != segment4
        assert segment1 != "not a segment"
    
    def test_bezier_segment_repr(self):
        """Test string representation of Bézier segment."""
        p0 = Point(0.0, 0.0)
        p1 = Point(1.0, 1.0)
        segment = BezierSegment([p0, p1], degree=1)
        
        repr_str = repr(segment)
        assert "BezierSegment" in repr_str
        assert "degree=1" in repr_str
        assert "control_points=2" in repr_str