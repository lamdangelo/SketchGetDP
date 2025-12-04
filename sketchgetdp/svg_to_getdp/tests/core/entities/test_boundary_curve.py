import pytest
from core.entities.point import Point
from core.entities.bezier_segment import BezierSegment
from core.entities.color import Color
from core.entities.boundary_curve import BoundaryCurve


class TestBoundaryCurve:
    """Test suite for the BoundaryCurve entity"""
    
    def create_sample_bezier_segments(self):
        """Helper to create sample Bézier segments for testing"""
        # Create three connected quadratic Bézier segments
        p0, p1, p2 = Point(0, 0), Point(0.5, 1), Point(1, 0)
        p3, p4 = Point(1.5, 1), Point(2, 0)
        
        segment1 = BezierSegment([p0, p1, p2], degree=2)
        segment2 = BezierSegment([p2, p3, p4], degree=2)  # p2 is shared
        
        return [segment1, segment2]
    
    def test_boundary_curve_creation(self):
        """Test basic creation of BoundaryCurve"""
        segments = self.create_sample_bezier_segments()
        corners = [Point(1, 0)]  # p2 is a corner
        color = Color.RED
        
        curve = BoundaryCurve(
            bezier_segments=segments,
            corners=corners,
            color=color
        )
        
        assert len(curve.bezier_segments) == 2
        assert len(curve.corners) == 1
        assert curve.color == color
        assert curve.is_closed == True
    
    def test_boundary_curve_creation_open(self):
        """Test creation of open BoundaryCurve"""
        segments = self.create_sample_bezier_segments()
        curve = BoundaryCurve(
            bezier_segments=segments,
            corners=[],
            color=Color.BLUE,
            is_closed=False
        )
        
        assert curve.is_closed == False
    
    def test_empty_segments_raises_error(self):
        """Test that empty segments list raises error"""
        with pytest.raises(ValueError, match="Boundary curve must have at least one Bézier segment"):
            BoundaryCurve(
                bezier_segments=[],
                corners=[],
                color=Color.RED
            )
    
    def test_discontinuous_segments_raises_error(self):
        """Test that discontinuous segments raise error"""
        p0, p1, p2 = Point(0, 0), Point(0.5, 1), Point(1, 0)
        p3, p4, p5 = Point(1.1, 1), Point(1.6, 1), Point(2, 0)  # p5 doesn't match p2
        
        segment1 = BezierSegment([p0, p1, p2], degree=2)
        segment2 = BezierSegment([p3, p4, p5], degree=2)  # Not connected to segment1
        
        with pytest.raises(ValueError, match="Discontinuity between segments 0 and 1"):
            BoundaryCurve(
                bezier_segments=[segment1, segment2],
                corners=[],
                color=Color.GREEN
            )
    
    def test_control_points_property(self):
        """Test control_points property aggregates all segment control points"""
        segments = self.create_sample_bezier_segments()
        curve = BoundaryCurve(segments, corners=[], color=Color.RED)

        control_points = curve.control_points
        unique_control_points = curve.unique_control_points
        
        # control_points includes duplicates at interfaces
        assert len(control_points) == 6  # 3 from seg1 + 3 from seg2 (including duplicate interface)
        
        # unique_control_points removes duplicates
        assert len(unique_control_points) == 5  # 3 from seg1 + 2 from seg2 (excluding duplicate interface)
        
        # Verify the points are in the correct order
        assert control_points[0] == segments[0].control_points[0]  # p0
        assert control_points[1] == segments[0].control_points[1]  # p1
        assert control_points[2] == segments[0].control_points[2]  # p2 (interface)
        assert control_points[3] == segments[1].control_points[0]  # p2 (interface - duplicate)
        assert control_points[4] == segments[1].control_points[1]  # p3
        assert control_points[5] == segments[1].control_points[2]  # p4
        
        # Verify unique points
        assert unique_control_points[0] == segments[0].control_points[0]  # p0
        assert unique_control_points[1] == segments[0].control_points[1]  # p1
        assert unique_control_points[2] == segments[0].control_points[2]  # p2 (interface)
        assert unique_control_points[3] == segments[1].control_points[1]  # p3
        assert unique_control_points[4] == segments[1].control_points[2]  # p4
    
    def test_evaluate_single_segment(self):
        """Test evaluation with single Bézier segment"""
        p0, p1 = Point(0, 0), Point(1, 1)
        segment = BezierSegment([p0, p1], degree=1)
        curve = BoundaryCurve([segment], corners=[], color=Color.RED)
        
        # Test start, middle, end
        assert curve.evaluate(0.0) == p0
        assert curve.evaluate(0.5) == Point(0.5, 0.5)
        assert curve.evaluate(1.0) == p1
    
    def test_evaluate_multiple_segments(self):
        """Test evaluation with multiple Bézier segments"""
        segments = self.create_sample_bezier_segments()
        curve = BoundaryCurve(segments, corners=[], color=Color.BLUE)
        
        # Test segment boundaries
        assert curve.evaluate(0.0) == segments[0].start_point
        assert curve.evaluate(0.5) == segments[1].start_point  # Interface at t=0.5
        assert curve.evaluate(1.0) == segments[1].end_point
        
        # Test within first segment
        point1 = curve.evaluate(0.25)
        expected1 = segments[0].evaluate(0.5)  # t=0.25 global = t=0.5 local in first segment
        assert point1 == expected1
        
        # Test within second segment
        point2 = curve.evaluate(0.75)
        expected2 = segments[1].evaluate(0.5)  # t=0.75 global = t=0.5 local in second segment
        assert point2 == expected2
    
    def test_evaluate_parameter_range(self):
        """Test that evaluation only works for t in [0,1]"""
        segments = self.create_sample_bezier_segments()
        curve = BoundaryCurve(segments, corners=[], color=Color.RED)
        
        with pytest.raises(ValueError, match="Parameter t must be in \\[0,1\\]"):
            curve.evaluate(-0.1)
        
        with pytest.raises(ValueError, match="Parameter t must be in \\[0,1\\]"):
            curve.evaluate(1.1)
    
    def test_derivative_single_segment(self):
        """Test derivative calculation with single segment"""
        p0, p1 = Point(0, 0), Point(2, 2)
        segment = BezierSegment([p0, p1], degree=1)
        curve = BoundaryCurve([segment], corners=[], color=Color.RED)
        
        # Derivative should be scaled by number of segments (1 in this case)
        derivative = curve.derivative(0.5)
        expected = Point(2, 2)  # Same as segment derivative since N_C=1
        
        assert derivative == expected
    
    def test_derivative_multiple_segments(self):
        """Test derivative calculation with multiple segments"""
        segments = self.create_sample_bezier_segments()
        curve = BoundaryCurve(segments, corners=[], color=Color.BLUE)
        
        # Test derivative in first segment (should be scaled by N_C=2)
        derivative1 = curve.derivative(0.25)
        segment_deriv1 = segments[0].derivative(0.5)  # Local t=0.5 for global t=0.25
        expected1 = Point(segment_deriv1.x * 2, segment_deriv1.y * 2)
        assert derivative1 == expected1
        
        # Test derivative in second segment
        derivative2 = curve.derivative(0.75)
        segment_deriv2 = segments[1].derivative(0.5)  # Local t=0.5 for global t=0.75
        expected2 = Point(segment_deriv2.x * 2, segment_deriv2.y * 2)
        assert derivative2 == expected2
    
    def test_derivative_parameter_range(self):
        """Test that derivative only works for t in [0,1]"""
        segments = self.create_sample_bezier_segments()
        curve = BoundaryCurve(segments, corners=[], color=Color.RED)
        
        with pytest.raises(ValueError, match="Parameter t must be in \\[0,1\\]"):
            curve.derivative(-0.1)
        
        with pytest.raises(ValueError, match="Parameter t must be in \\[0,1\\]"):
            curve.derivative(1.1)
    
    def test_is_corner_at_parameter(self):
        """Test corner detection at parameter values"""
        segments = self.create_sample_bezier_segments()
        corner_point = segments[0].end_point  # p2
        curve = BoundaryCurve(segments, corners=[corner_point], color=Color.RED)
        
        # Should detect corner at t=0.5 (interface between segments)
        assert curve.is_corner_at_parameter(0.5) == True
        
        # Should not detect corner at other parameters
        assert curve.is_corner_at_parameter(0.0) == False
        assert curve.is_corner_at_parameter(0.25) == False
        assert curve.is_corner_at_parameter(0.75) == False
        assert curve.is_corner_at_parameter(1.0) == False
    
    def test_is_corner_at_segment_interface(self):
        """Test corner detection at segment interfaces"""
        segments = self.create_sample_bezier_segments()
        corner_point = segments[0].end_point  # p2
        curve = BoundaryCurve(segments, corners=[corner_point], color=Color.RED)
        
        # Interface 0 (between segment 0 and 1) should be a corner
        assert curve.is_corner_at_segment_interface(0) == True
        
        # Test invalid interface indices
        with pytest.raises(ValueError, match="Invalid segment index for interface check"):
            curve.is_corner_at_segment_interface(-1)
        
        with pytest.raises(ValueError, match="Invalid segment index for interface check"):
            curve.is_corner_at_segment_interface(1)  # Only interfaces 0 to N-2
    
    def test_get_segment_at_parameter(self):
        """Test getting segment and local parameter for global parameter"""
        segments = self.create_sample_bezier_segments()
        curve = BoundaryCurve(segments, corners=[], color=Color.RED)
        
        # Test first segment
        segment1, local_t1 = curve.get_segment_at_parameter(0.25)
        assert segment1 == segments[0]
        assert local_t1 == pytest.approx(0.5)
        
        # Test second segment
        segment2, local_t2 = curve.get_segment_at_parameter(0.75)
        assert segment2 == segments[1]
        assert local_t2 == pytest.approx(0.5)
        
        # Test boundaries
        segment_start, local_t_start = curve.get_segment_at_parameter(0.0)
        assert segment_start == segments[0]
        assert local_t_start == pytest.approx(0.0)
        
        segment_end, local_t_end = curve.get_segment_at_parameter(1.0)
        assert segment_end == segments[1]
        assert local_t_end == pytest.approx(1.0)
    
    def test_get_curve_points(self):
        """Test sampling points along entire boundary curve"""
        segments = self.create_sample_bezier_segments()
        curve = BoundaryCurve(segments, corners=[], color=Color.RED)
        
        points = curve.get_curve_points(num_points=5)
        
        assert len(points) == 5
        assert points[0] == segments[0].start_point
        assert points[2] == segments[0].end_point  # Interface point
        assert points[4] == segments[1].end_point
    
    def test_get_curve_points_invalid_count(self):
        """Test that invalid point count raises error"""
        segments = self.create_sample_bezier_segments()
        curve = BoundaryCurve(segments, corners=[], color=Color.RED)
        
        with pytest.raises(ValueError, match="Number of points must be at least 2"):
            curve.get_curve_points(num_points=1)
    
    def test_get_boundary_length_approximation(self):
        """Test boundary length approximation"""
        p0, p1 = Point(0, 0), Point(1, 0)
        segment = BezierSegment([p0, p1], degree=1)
        curve = BoundaryCurve([segment], corners=[], color=Color.RED)
        
        length = curve.get_boundary_length_approximation(num_samples=10)
        
        # Straight line from (0,0) to (1,0) should have length 1.0
        assert length == pytest.approx(1.0, rel=1e-2)
    
    def test_len_operator(self):
        """Test len() operator returns number of segments"""
        segments = self.create_sample_bezier_segments()
        curve = BoundaryCurve(segments, corners=[], color=Color.RED)
        
        assert len(curve) == 2
    
    def test_iteration(self):
        """Test iteration over Bézier segments"""
        segments = self.create_sample_bezier_segments()
        curve = BoundaryCurve(segments, corners=[], color=Color.RED)
        
        segment_list = list(curve)
        assert segment_list == segments
    
    def test_repr(self):
        """Test string representation"""
        segments = self.create_sample_bezier_segments()
        curve = BoundaryCurve(segments, corners=[Point(1, 0)], color=Color.GREEN)
        
        repr_str = repr(curve)
        assert "BoundaryCurve" in repr_str
        assert "segments=2" in repr_str
        assert "corners=1" in repr_str
        assert "color=green" in repr_str
        assert "closed=True" in repr_str
    
    @pytest.mark.parametrize("t,expected_segment_idx,expected_local_t", [
        (0.0, 0, 0.0),
        (0.25, 0, 0.5),
        (0.5, 1, 0.0),
        (0.75, 1, 0.5),
        (1.0, 1, 1.0),
    ])
    def test_parametrized_segment_mapping(self, t, expected_segment_idx, expected_local_t):
        """Test parameter mapping with various inputs"""
        segments = self.create_sample_bezier_segments()
        curve = BoundaryCurve(segments, corners=[], color=Color.RED)
        
        segment, local_t = curve.get_segment_at_parameter(t)
        
        assert segment == segments[expected_segment_idx]
        assert local_t == pytest.approx(expected_local_t)
    
    def test_color_persistence(self):
        """Test that color property is properly maintained"""
        segments = self.create_sample_bezier_segments()
        
        for color in [Color.RED, Color.GREEN, Color.BLUE]:
            curve = BoundaryCurve(segments, corners=[], color=color)
            assert curve.color == color
            assert curve.color.name == color.name