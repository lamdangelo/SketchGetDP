"""
Test suite for the Bézier Fitter infrastructure component.
"""

import pytest
import math
import numpy as np
from unittest.mock import patch

from sketchgetdp.svg_to_getdp.core.entities import color
from svg_to_getdp.infrastructure.bezier_fitter import BezierFitter
from svg_to_getdp.core.entities.bezier_segment import BezierSegment
from svg_to_getdp.core.entities.point import Point
from svg_to_getdp.core.entities.color import Color


class TestBezierFitter:
    """Test suite for the BezierFitter class"""
    
    # ==================== Fixtures ====================
    
    @pytest.fixture
    def fitter(self):
        """Create a Bézier fitter instance for testing."""
        return BezierFitter(bezier_degree=2, minimum_points_per_segment=15)
    
    # ==================== Initialization Tests ====================
    
    def test_fitter_initialization(self, fitter):
        """Test that fitter initializes with correct parameters"""
        assert fitter.bezier_degree == 2
        assert fitter.minimum_points_per_segment == 15
        
        # Test with custom parameters
        custom_fitter = BezierFitter(bezier_degree=3, minimum_points_per_segment=10)
        assert custom_fitter.bezier_degree == 3
        assert custom_fitter.minimum_points_per_segment == 10
    
    # ==================== Basic Functionality Tests ====================
    
    def test_fit_outline_insufficient_points(self, fitter):
        """Test that fitter raises error for insufficient points"""
        points = [Point(0, 0), Point(1, 0)]  # Only 2 points
        corner_indices = []
        color = Color.BLACK
        
        with pytest.raises(ValueError, match="Need at least 3 non-duplicate points for outline"):
            fitter.fit_outline(points, corner_indices, color)

    def test_fit_outline_simple_triangle(self, fitter):
        """Test fitting Bézier curves to a simple triangle"""
        # Create a triangle
        points = [
            Point(0, 0), Point(1, 0), Point(0.5, 1), Point(0, 0)  # Closed triangle
        ]
        corner_indices = [0, 1, 2]  # All vertices are corners
        color = Color.BLUE

        outline = fitter.fit_outline(points, corner_indices, color)
        # Validate the result - use hasattr to check if it's a Outline-like object
        assert hasattr(outline, 'bezier_segments')
        assert hasattr(outline, 'corners')
        assert hasattr(outline, 'color')
        assert hasattr(outline, 'is_closed')
        
        # Check attributes directly
        assert outline.color == color
        assert outline.is_closed == True
        assert len(outline.corners) == 3

        # Should have at least 1 Bézier segment
        assert len(outline.bezier_segments) >= 1

        # Each segment should be valid
        for segment in outline.bezier_segments:
            assert hasattr(segment, 'control_points')
            assert hasattr(segment, 'degree')
            # Each Bézier segment should have degree + 1 control points
            assert len(segment.control_points) == segment.degree + 1
            # Control points should not be NaN or infinite
            for control_point in segment.control_points:
                assert math.isfinite(control_point.x)
                assert math.isfinite(control_point.y)

        # Check segment connections
        if len(outline.bezier_segments) > 1:
            for i in range(len(outline.bezier_segments)):
                current_segment = outline.bezier_segments[i]
                next_segment = outline.bezier_segments[(i + 1) % len(outline.bezier_segments)]
                
                # Check C0 continuity (position continuity at segment interfaces)
                # The end point of current segment should match start point of next segment
                distance = current_segment.end_point.distance_to(next_segment.start_point)
                assert distance < 1e-10, f"Segment {i} end point doesn't connect to segment {(i + 1) % len(outline.bezier_segments)} start point. Distance: {distance}"
        
        # Additional check: verify the outline is properly closed
        first_segment = outline.bezier_segments[0]
        last_segment = outline.bezier_segments[-1]
        closure_distance = last_segment.end_point.distance_to(first_segment.start_point)
        assert closure_distance < 1e-10, f"Outline is not properly closed. Gap: {closure_distance}"
    
    def test_fit_outline_no_corners(self, fitter):
        """Test fitting Bézier curves to a smooth curve without corners"""
        # Create a circle-like shape (approximated)
        points = []
        for i in range(20):
            angle = 2 * math.pi * i / 20
            x = 0.5 + 0.4 * math.cos(angle)
            y = 0.5 + 0.4 * math.sin(angle)
            points.append(Point(x, y))
        points.append(points[0])  # Close the curve
        
        corner_indices = []  # No corners for smooth curve
        color = Color.GREEN

        outline = fitter.fit_outline(points, corner_indices, color)

        # Check attributes
        assert hasattr(outline, 'bezier_segments')
        assert len(outline.bezier_segments) > 0
        
        # Verify there are no corners after fitting (since none were provided)
        assert hasattr(outline, 'corners')
        assert len(outline.corners) == 0
        
        # Ensure all segments are properly connected
        if len(outline.bezier_segments) > 1:
            for i in range(len(outline.bezier_segments) - 1):
                current = outline.bezier_segments[i]
                next_seg = outline.bezier_segments[i + 1]
                # Check C0 continuity (end point matches next start point)
                assert current.end_point.distance_to(next_seg.start_point) < 1e-10
        
        # Check closure for closed Outline
        if outline.is_closed and len(outline.bezier_segments) > 1:
            first = outline.bezier_segments[0]
            last = outline.bezier_segments[-1]
            assert last.end_point.distance_to(first.start_point) < 1e-10
    
    def test_fit_outline_mixed_corners(self, fitter):
        """Test fitting with some corners and some smooth sections"""
        points = [
            Point(0, 0),  # Corner
            Point(0.2, 0.1), Point(0.4, 0.15), Point(0.6, 0.1),  # Smooth section
            Point(0.8, 0),  # Corner
            Point(0.8, 0.5),  # Corner  
            Point(0.6, 0.6), Point(0.4, 0.65), Point(0.2, 0.6),  # Smooth section
            Point(0, 0.5),  # Corner
            Point(0, 0)  # Back to start
        ]
        corner_indices = [0, 4, 5, 8]  # Indices of corners
        color = Color.BLACK
        
        outline = fitter.fit_outline(points, corner_indices, color)
        
        # Should create valid outline
        assert hasattr(outline, 'bezier_segments')
        assert len(outline.bezier_segments) >= 1
        
        # Check attributes
        assert hasattr(outline, 'corners')
        assert hasattr(outline, 'color')
        assert hasattr(outline, 'is_closed')
        
        # Check attribute values
        assert outline.color == color
        assert outline.is_closed == True
        assert len(outline.corners) == 4  # Should have 4 corners
        
        # Each segment should be valid
        for segment in outline.bezier_segments:
            assert hasattr(segment, 'control_points')
            assert hasattr(segment, 'degree')
            # Each Bézier segment should have degree + 1 control points
            assert len(segment.control_points) == segment.degree + 1
            # Control points should not be NaN or infinite
            for control_point in segment.control_points:
                assert math.isfinite(control_point.x)
                assert math.isfinite(control_point.y)
        
        # Check segment connections (C0 continuity)
        if len(outline.bezier_segments) > 1:
            for i in range(len(outline.bezier_segments)):
                current_segment = outline.bezier_segments[i]
                next_segment = outline.bezier_segments[(i + 1) % len(outline.bezier_segments)]
                
                # Check C0 continuity (position continuity at segment interfaces)
                distance = current_segment.end_point.distance_to(next_segment.start_point)
                assert distance < 1e-10, f"Segment {i} end point doesn't connect to segment {(i + 1) % len(outline.bezier_segments)} start point. Distance: {distance}"
        
        # Verify the outline is properly closed
        if len(outline.bezier_segments) > 1:
            first_segment = outline.bezier_segments[0]
            last_segment = outline.bezier_segments[-1]
            closure_distance = last_segment.end_point.distance_to(first_segment.start_point)
            assert closure_distance < 1e-10, f"Outline is not properly closed. Gap: {closure_distance}"
    
    # ==================== Internal Method Tests ====================
    
    def test_remove_consecutive_duplicate_points(self, fitter):
        """Test removal of consecutive duplicate points"""
        points = [
            Point(0, 0),
            Point(0, 0),  # Duplicate
            Point(1, 0),
            Point(1, 0),  # Duplicate
            Point(1, 1),
            Point(0, 0)  # Not consecutive duplicate
        ]
        
        cleaned = fitter._remove_consecutive_duplicate_points(points)
        assert len(cleaned) == 4  # Should have 4 unique consecutive points
    
    def test_calculate_segment_interfaces(self, fitter):
        """Test segment interface determination with corners"""
        points = [Point(i * 0.1, 0) for i in range(11)]  # 11 points along x-axis
        corner_indices = [0, 5, 10]  # Corners at start, middle, end
        
        interfaces = fitter._calculate_segment_interfaces(
            points, corner_indices, target_segment_count=3, is_closed=False
        )
        
        # Should include all corner indices plus start and end
        assert 0 in interfaces
        assert 5 in interfaces
        assert 10 in interfaces
    
    def test_bernstein_basis_computation(self, fitter):
        """Test Bernstein basis computation"""
        basis_val = fitter._compute_bernstein_basis(1, 2, 0.5)  # B_{1,2}(0.5)
        expected = math.comb(2, 1) * (0.5 ** 1) * ((1 - 0.5) ** (2 - 1))
        assert abs(basis_val - expected) < 1e-10
        
        # Test that basis polynomials sum to 1
        total = 0
        for i in range(3):  # degree 2 has 3 basis functions
            total += fitter._compute_bernstein_basis(i, 2, 0.3)
        assert abs(total - 1.0) < 1e-10
    
    def test_fit_simple_bezier_curve(self, fitter):
        """Test simple Bézier fitting for small point sets"""
        # Single point
        points = [Point(5, 5)]
        segment = fitter._fit_simple_bezier_curve(points)
        # Check attributes instead of isinstance
        assert hasattr(segment, 'control_points')
        assert hasattr(segment, 'degree')
        assert len(segment.control_points) == 3  # degree 2 + 1
        
        # Two points
        points = [Point(0, 0), Point(1, 1)]
        segment = fitter._fit_simple_bezier_curve(points)
        assert hasattr(segment, 'start_point')
        assert hasattr(segment, 'end_point')
        # Access attributes directly
        assert segment.control_points[0] == points[0]
        assert segment.control_points[-1] == points[1]
    
    def test_enforce_segment_continuity(self, fitter):
        """Test that piecewise Bézier curves maintain continuity"""
        # Create two simple segments using BezierSegment constructor
        segment1 = BezierSegment(
            control_points=[Point(0, 0), Point(0.3, 0.1), Point(0.5, 0)],
            degree=2
        )
        segment2 = BezierSegment(
            control_points=[Point(0.5, 0), Point(0.7, -0.1), Point(1, 0)],
            degree=2
        )
        
        segments = [segment1, segment2]
        interfaces = [0, 5, 10]  # Mock interfaces
        corner_indices = []  # No corners for smooth junction
        
        # Test C0 continuity enforcement
        fitter._enforce_segment_continuity(
            segments, interfaces, corner_indices, is_closed=False
        )
        
        # End point of first should match start point of second (C0 continuity)
        assert segment1.control_points[-1] == segment2.control_points[0]
    
    def test_classify_segment_type(self, fitter):
        """Test segment type classification for all three types"""
        points = [Point(i * 0.1, 0) for i in range(11)]
        corner_regions = [(0, 2), (8, 10)]
        corner_indices = [0, 5, 10]
        
        # Track which tests pass/fail
        test_results = {}
        
        # Test 1: corner_region - segment within corner region
        try:
            segment_type = fitter._classify_segment_type(
                start_index=1,
                end_index=2,
                corner_regions=corner_regions,
                corner_indices=corner_indices,
                points=points
            )
            test_results["corner_region_within"] = (segment_type == "corner_region", segment_type)
        except Exception as e:
            test_results["corner_region_within"] = (False, f"Exception: {e}")
        
        # Test 2: corner_region - segment contains interior corner
        try:
            segment_type = fitter._classify_segment_type(
                start_index=4,
                end_index=6,
                corner_regions=[],
                corner_indices=corner_indices,
                points=points
            )
            test_results["corner_region_interior"] = (segment_type == "corner_region", segment_type)
        except Exception as e:
            test_results["corner_region_interior"] = (False, f"Exception: {e}")
        
        # Test 3: straight_edge - segment connecting corners with straight geometry
        try:
            # Create points for a straight line connecting corners
            straight_points = [Point(0, 0), Point(0.5, 0), Point(1, 0)]
            all_points = points + straight_points
            segment_type = fitter._classify_segment_type(
                start_index=11,  # Start at the first straight point
                end_index=13,    # End at the last straight point
                corner_regions=[],
                corner_indices=[11, 13],  # Treat endpoints as corners
                points=all_points
            )
            test_results["straight_edge"] = (segment_type == "straight_edge", segment_type)
        except Exception as e:
            test_results["straight_edge"] = (False, f"Exception: {e}")
        
        # Test 4: curved - segment not connecting corners and not straight
        try:
            # Create curved points (a slight arc)
            curved_points = [Point(0, 0), Point(0.3, 0.1), Point(0.7, 0.1), Point(1, 0)]
            all_points = points + curved_points
            segment_type = fitter._classify_segment_type(
                start_index=11,  # Start at the first curved point
                end_index=14,    # End at the last curved point
                corner_regions=[],
                corner_indices=[],  # No corners involved
                points=all_points
            )
            test_results["curved"] = (segment_type == "curved", segment_type)
        except Exception as e:
            test_results["curved"] = (False, f"Exception: {e}")
        
        # Check all results and print failures
        all_passed = True
        failed_tests = []
        
        for test_name, (passed, result) in test_results.items():
            if not passed:
                all_passed = False
                failed_tests.append((test_name, result))
        
        if not all_passed:
            # Print detailed failure information
            print(f"Segment classification test failed for {len(failed_tests)} case(s):")
            for test_name, result in failed_tests:
                print(f"  - {test_name}: expected specific type, got '{result}'")
            
            raise AssertionError(f"Segment classification tests failed: {[name for name, _ in failed_tests]}")
    
    def test_are_points_approximately_linear(self, fitter):
        """Test linear approximation check"""
        # Linear points
        linear_points = [Point(0, 0), Point(0.5, 0.5), Point(1, 1)]
        assert fitter._are_points_approximately_linear(linear_points)
        
        # Non-linear points
        non_linear_points = [Point(0, 0), Point(0.5, 0), Point(1, 1)]
        assert not fitter._are_points_approximately_linear(non_linear_points)
    
    def test_calculate_distance_from_line(self, fitter):
        """Test distance calculation from point to line"""
        line_start = Point(0, 0)
        line_end = Point(1, 0)
        test_point = Point(0.5, 1)
        
        distance = fitter._calculate_distance_from_line(line_start, line_end, test_point)
        assert abs(distance - 1.0) < 1e-10
    
    # ==================== Error Handling Tests ====================
    
    @patch('numpy.linalg.lstsq')
    def test_least_squares_fallback(self, mock_lstsq, fitter):
        """Test fallback when least squares fails"""
        # Mock numpy.linalg.lstsq to raise LinAlgError
        mock_lstsq.side_effect = np.linalg.LinAlgError("Matrix is singular")
        
        points = [Point(0, 0), Point(0.5, 0.5), Point(1, 1), Point(0, 0)]
        
        # Provide at least one corner to avoid the no-corners path
        corner_indices = [0]
        
        # Should use fallback but still work
        outline = fitter.fit_outline(points, corner_indices=corner_indices, color=Color.BLUE)
        
        # Check attributes
        assert hasattr(outline, 'bezier_segments')
        assert len(outline.bezier_segments) >= 1
    
    # ==================== Performance Tests ====================
    
    def test_performance_large_dataset(self, fitter):
        """Test performance with larger datasets"""
        # Create a larger point set
        n_points = 100
        points = [Point(math.cos(2 * math.pi * i / n_points), 
                        math.sin(2 * math.pi * i / n_points)) 
                 for i in range(n_points)]
        corner_indices = [0, 25, 50, 75]  # Approximate corner indices
        color = Color.GREEN
        
        import time
        start_time = time.time()
        
        outline = fitter.fit_outline(points, corner_indices, color)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete in reasonable time
        assert duration < 5.0  # 5 seconds should be plenty
        
        # Result should be valid
        assert hasattr(outline, 'bezier_segments')
        assert len(outline.bezier_segments) > 0
        