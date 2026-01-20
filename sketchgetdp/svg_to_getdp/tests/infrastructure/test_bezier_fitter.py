"""
Test suite for the Bézier Fitter infrastructure component.
Updated for modular bezier_fitting structure.
"""
import pytest
import math
import numpy as np
from unittest.mock import patch

from svg_to_getdp.infrastructure.bezier_fitting.bezier_fitter import BezierFitter
from svg_to_getdp.infrastructure.bezier_fitting.bezier_calculator import BezierCalculator
from svg_to_getdp.infrastructure.bezier_fitting.segment_classifier import SegmentClassifier
from svg_to_getdp.infrastructure.bezier_fitting.segment_fitter import SegmentFitter
from svg_to_getdp.infrastructure.bezier_fitting.continuity_enforcer import ContinuityEnforcer

from svg_to_getdp.core.entities.bezier_segment import BezierSegment
from svg_to_getdp.core.entities.point import Point
from svg_to_getdp.core.entities.color import Color


class TestBezierFitter:
    """Test suite for the main BezierFitter orchestrator"""
    
    # ==================== Fixtures ====================
    
    @pytest.fixture
    def fitter(self):
        """Set up a fresh fitter instance for each test"""
        return BezierFitter(bezier_degree=2, minimum_points_per_segment=15)
    
    @pytest.fixture
    def calculator(self):
        """Set up a bezier calculator for component testing"""
        return BezierCalculator()
    
    @pytest.fixture
    def classifier(self):
        """Set up a segment classifier for component testing"""
        return SegmentClassifier()
    
    @pytest.fixture
    def segment_fitter(self):
        """Set up a segment fitter for component testing"""
        return SegmentFitter(bezier_degree=2)
    
    @pytest.fixture
    def continuity_enforcer(self):
        """Set up a continuity enforcer for component testing"""
        return ContinuityEnforcer(bezier_degree=2)
    
    @pytest.fixture
    def triangle_points(self):
        """Create a triangle shape for testing"""
        return [
            Point(0, 0), 
            Point(1, 0), 
            Point(0.5, 1), 
            Point(0, 0)  # Closed triangle
        ]
    
    @pytest.fixture
    def circle_points(self):
        """Create a circle-like shape for testing"""
        points = []
        for i in range(20):
            angle = 2 * math.pi * i / 20
            x = 0.5 + 0.4 * math.cos(angle)
            y = 0.5 + 0.4 * math.sin(angle)
            points.append(Point(x, y))
        points.append(points[0])  # Close the curve
        return points
    
    @pytest.fixture
    def mixed_shape_points(self):
        """Create a shape with mixed corners and smooth sections"""
        return [
            Point(0, 0),  # Corner
            Point(0.2, 0.1), Point(0.4, 0.15), Point(0.6, 0.1),  # Smooth section
            Point(0.8, 0),  # Corner
            Point(0.8, 0.5),  # Corner  
            Point(0.6, 0.6), Point(0.4, 0.65), Point(0.2, 0.6),  # Smooth section
            Point(0, 0.5),  # Corner
            Point(0, 0)  # Back to start
        ]
    
    # ==================== Initialization and Configuration Tests ====================
    
    def test_fitter_initialization_default(self, fitter):
        """Test that fitter initializes with correct default parameters"""
        assert fitter.bezier_degree == 2
        assert fitter.minimum_points_per_segment == 15
        
        # Verify components are initialized
        assert hasattr(fitter, 'segment_classifier')
        assert hasattr(fitter, 'segment_fitter')
        assert hasattr(fitter, 'continuity_enforcer')
        assert hasattr(fitter, 'bezier_calculator')
    
    @pytest.mark.parametrize("degree,min_points", [
        (3, 10),
        (2, 5),
        (4, 20),
    ])
    def test_fitter_initialization_custom_parameters(self, degree, min_points):
        """Test fitter initialization with custom bezier degree and segment size"""
        custom_fitter = BezierFitter(
            bezier_degree=degree, 
            minimum_points_per_segment=min_points
        )
        assert custom_fitter.bezier_degree == degree
        assert custom_fitter.minimum_points_per_segment == min_points
    
    # ==================== Input Validation and Error Tests ====================
    
    def test_fit_outline_insufficient_points_raises_error(self, fitter):
        """Test that fitter raises ValueError for insufficient points"""
        points = [Point(0, 0), Point(1, 0)]  # Only 2 points
        corner_indices = []
        color = Color.BLACK
        
        with pytest.raises(ValueError, match="Need at least 3 non-duplicate points for outline"):
            fitter.fit_outline(points, corner_indices, color)
    
    def test_fit_outline_consecutive_duplicate_points_handling(self, fitter):
        """Test that consecutive duplicate points are automatically removed"""
        points = [
            Point(0, 0),
            Point(0, 0),  # Duplicate (will be removed)
            Point(1, 0),
            Point(1, 0),  # Duplicate (will be removed)
            Point(0.5, 1),
            Point(0, 0)
        ]
        # After removing duplicates at indices 1 and 3, the cleaned list will be:
        # [Point(0,0), Point(1,0), Point(0.5,1), Point(0,0)]
        corner_indices = [0, 1, 2]  # Indices in the CLEANED list
        
        # Should not raise error despite duplicates
        outline = fitter.fit_outline(points, corner_indices, Color.BLUE)
        assert hasattr(outline, 'bezier_segments')
        assert len(outline.bezier_segments) >= 1
        # Should have 3 corners in the outline
        assert len(outline.corners) == 3
    
    @patch('svg_to_getdp.infrastructure.bezier_fitting.segment_fitter.np.linalg.lstsq')
    def test_least_squares_fallback_on_singular_matrix(self, mock_lstsq, fitter):
        """Test fallback to simple fitting when least squares fails with singular matrix"""
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
    
    # ==================== Basic Shape Fitting Tests ====================
    
    def test_fit_outline_simple_triangle_with_corners(self, fitter, triangle_points):
        """Test fitting Bézier curves to a simple triangle with explicit corners"""
        corner_indices = [0, 1, 2]  # All vertices are corners
        color = Color.BLUE

        outline = fitter.fit_outline(triangle_points, corner_indices, color)
        
        # Validate the result structure
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

        # Check segment connections for continuity
        if len(outline.bezier_segments) > 1:
            for i in range(len(outline.bezier_segments)):
                current_segment = outline.bezier_segments[i]
                next_segment = outline.bezier_segments[(i + 1) % len(outline.bezier_segments)]
                
                # Check C0 continuity (position continuity at segment interfaces)
                distance = current_segment.end_point.distance_to(next_segment.start_point)
                assert distance < 1e-10, f"Segment {i} end point doesn't connect to segment {(i + 1) % len(outline.bezier_segments)} start point. Distance: {distance}"
        
        # Verify the outline is properly closed
        first_segment = outline.bezier_segments[0]
        last_segment = outline.bezier_segments[-1]
        closure_distance = last_segment.end_point.distance_to(first_segment.start_point)
        assert closure_distance < 1e-10, f"Outline is not properly closed. Gap: {closure_distance}"
    
    def test_fit_outline_smooth_circle_without_corners(self, fitter, circle_points):
        """Test fitting Bézier curves to a smooth circle-like shape without explicit corners"""
        corner_indices = []  # No corners for smooth curve
        color = Color.GREEN

        outline = fitter.fit_outline(circle_points, corner_indices, color)

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
    
    def test_fit_outline_mixed_corners_and_smooth_sections(self, fitter, mixed_shape_points):
        """Test fitting with combination of corner points and smooth sections"""
        corner_indices = [0, 4, 5, 8]  # Indices of corners
        color = Color.BLACK
        
        outline = fitter.fit_outline(mixed_shape_points, corner_indices, color)
        
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
    
    # ==================== BezierCalculator Component Tests ====================
    
    def test_bezier_calculator_remove_consecutive_duplicate_points(self, calculator):
        """Test that consecutive duplicate points are removed while preserving non-consecutive duplicates"""
        points = [
            Point(0, 0),
            Point(0, 0),  # Consecutive duplicate
            Point(1, 0),
            Point(1, 0),  # Consecutive duplicate
            Point(1, 1),
            Point(0, 0)  # Not consecutive duplicate (different from first)
        ]
        
        cleaned = calculator.remove_consecutive_duplicate_points(points)
        assert len(cleaned) == 4  # Should have 4 unique consecutive points
    
    def test_bezier_calculator_calculate_segment_interfaces_with_corners(self, calculator):
        """Test segment interface calculation prioritizing corner points"""
        points = [Point(i * 0.1, 0) for i in range(11)]  # 11 points along x-axis
        corner_indices = [0, 5, 10]  # Corners at start, middle, end
        
        interfaces = calculator.calculate_segment_interfaces(
            points, corner_indices, target_segment_count=3, is_closed=False
        )
        
        # Should include all corner indices plus start and end
        assert 0 in interfaces
        assert 5 in interfaces
        assert 10 in interfaces
    
    def test_bezier_calculator_compute_bernstein_basis(self, calculator):
        """Test Bernstein basis polynomial computation for Bézier curves"""
        basis_val = calculator.compute_bernstein_basis(1, 2, 0.5)  # B_{1,2}(0.5)
        expected = math.comb(2, 1) * (0.5 ** 1) * ((1 - 0.5) ** (2 - 1))
        assert abs(basis_val - expected) < 1e-10
        
        # Test that basis polynomials sum to 1 (partition of unity property)
        total = 0
        for i in range(3):  # degree 2 has 3 basis functions
            total += calculator.compute_bernstein_basis(i, 2, 0.3)
        assert abs(total - 1.0) < 1e-10
    
    def test_bezier_calculator_are_points_approximately_linear(self, calculator):
        """Test detection of approximately linear point sequences"""
        # Linear points
        linear_points = [Point(0, 0), Point(0.5, 0.5), Point(1, 1)]
        assert calculator.are_points_approximately_linear(linear_points)
        
        # Non-linear points
        non_linear_points = [Point(0, 0), Point(0.5, 0), Point(1, 1)]
        assert not calculator.are_points_approximately_linear(non_linear_points)
    
    def test_bezier_calculator_calculate_distance_from_line(self, calculator):
        """Test perpendicular distance calculation from point to line"""
        line_start = Point(0, 0)
        line_end = Point(1, 0)
        test_point = Point(0.5, 1)
        
        distance = calculator.calculate_distance_from_line(line_start, line_end, test_point)
        assert abs(distance - 1.0) < 1e-10
    
    def test_bezier_calculator_project_point_to_line(self, calculator):
        """Test orthogonal projection of point onto line segment"""
        line_start = Point(0, 0)
        line_end = Point(1, 0)
        test_point = Point(0.5, 1)
        
        projection = calculator.project_point_to_line(line_start, line_end, test_point)
        assert projection == Point(0.5, 0)  # Should project to (0.5, 0)
    
    def test_bezier_calculator_find_point_with_max_deviation(self, calculator):
        """Test identification of point with maximum deviation from line"""
        line_start = Point(0, 0)
        line_end = Point(1, 0)
        points = [
            Point(0.2, 0.1),
            Point(0.5, 0.5),  # Max deviation
            Point(0.8, 0.1)
        ]
        
        max_point = calculator.find_point_with_max_deviation(points, line_start, line_end)
        assert max_point == points[1]  # Point (0.5, 0.5) has max deviation
    
    # ==================== SegmentClassifier Component Tests ====================
    
    def test_segment_classifier_identify_corner_regions(self, classifier, calculator):
        """Test identification of regions around corners for special fitting"""
        points = [Point(i * 0.1, 0) for i in range(11)]
        corner_indices = [0, 5, 10]
        regions = classifier.identify_corner_regions(points, corner_indices)
        
        assert len(regions) == 3
        for region in regions:
            assert isinstance(region, tuple)
            assert len(region) == 2
            assert region[0] <= region[1]
    
    def test_segment_classifier_classify_segment_type_corner_regions(self, classifier):
        """Test segment classification for corner regions"""
        points = [Point(i * 0.1, 0) for i in range(11)]
        corner_regions = [(0, 2), (8, 10)]
        corner_indices = [0, 5, 10]
        
        # Test corner region (segment within corner region)
        segment_type = classifier.classify_segment_type(
            start_index=1,
            end_index=2,
            corner_regions=corner_regions,
            corner_indices=corner_indices,
            points=points
        )
        assert segment_type == "corner_region"
        
        # Test corner region (segment contains interior corner)
        segment_type = classifier.classify_segment_type(
            start_index=4,
            end_index=6,
            corner_regions=[],
            corner_indices=corner_indices,
            points=points
        )
        assert segment_type == "corner_region"
    
    def test_segment_classifier_classify_segment_type_straight_and_curved(self, classifier):
        """Test segment classification for straight edges and curved segments"""
        points = [Point(i * 0.1, 0) for i in range(11)]
        
        # Test straight_edge - segment connecting corners with straight geometry
        straight_points = [Point(0, 0), Point(0.5, 0), Point(1, 0)]
        all_points = points + straight_points
        segment_type = classifier.classify_segment_type(
            start_index=11,  # Start at the first straight point
            end_index=13,    # End at the last straight point
            corner_regions=[],
            corner_indices=[11, 13],  # Treat endpoints as corners
            points=all_points
        )
        assert segment_type == "straight_edge"
        
        # Test curved - segment not connecting corners and not straight
        curved_points = [Point(0, 0), Point(0.3, 0.1), Point(0.7, 0.1), Point(1, 0)]
        all_points = points + curved_points
        segment_type = classifier.classify_segment_type(
            start_index=11,  # Start at the first curved point
            end_index=14,    # End at the last curved point
            corner_regions=[],
            corner_indices=[],  # No corners involved
            points=all_points
        )
        assert segment_type == "curved"
    
    # ==================== SegmentFitter Component Tests ====================
    
    def test_segment_fitter_fit_simple_bezier_curve_small_point_sets(self, segment_fitter):
        """Test simple Bézier fitting for small point sets (fallback cases)"""
        # Single point
        points = [Point(5, 5)]
        segment = segment_fitter._fit_simple_bezier_curve(points)
        assert hasattr(segment, 'control_points')
        assert hasattr(segment, 'degree')
        assert len(segment.control_points) == 3  # degree 2 + 1
        
        # Two points
        points = [Point(0, 0), Point(1, 1)]
        segment = segment_fitter._fit_simple_bezier_curve(points)
        assert hasattr(segment, 'start_point')
        assert hasattr(segment, 'end_point')
        # Access attributes directly
        assert segment.control_points[0] == points[0]
        assert segment.control_points[-1] == points[1]
    
    def test_segment_fitter_fit_straight_edge_segment(self, segment_fitter):
        """Test fitting of straight edge segments between corners"""
        points = [Point(0, 0), Point(0.5, 0), Point(1, 0)]
        segment = segment_fitter._fit_straight_edge_segment(points)
        
        assert hasattr(segment, 'control_points')
        assert len(segment.control_points) == 3
        assert segment.control_points[0] == points[0]
        assert segment.control_points[-1] == points[-1]
        
        # Midpoint should be average of endpoints
        midpoint = segment.control_points[1]
        expected_midpoint = Point(
            (points[0].x + points[-1].x) / 2,
            (points[0].y + points[-1].y) / 2
        )
        assert midpoint.distance_to(expected_midpoint) < 1e-10
    
    # ==================== ContinuityEnforcer Component Tests ====================
    
    def test_continuity_enforcer_enforce_segment_continuity_c0(self, continuity_enforcer):
        """Test C0 continuity (position continuity) enforcement between segments"""
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
        continuity_enforcer.enforce_segment_continuity(
            segments, interfaces, corner_indices, is_closed=False
        )
        
        # End point of first should match start point of second (C0 continuity)
        assert segment1.control_points[-1] == segment2.control_points[0]
    
    def test_continuity_enforcer_enforce_tangent_continuity_c1(self, continuity_enforcer):
        """Test C1 continuity (tangent continuity) enforcement for smooth junctions"""
        segment1 = BezierSegment(
            control_points=[Point(0, 0), Point(0.3, 0.1), Point(0.5, 0)],
            degree=2
        )
        segment2 = BezierSegment(
            control_points=[Point(0.5, 0), Point(0.7, -0.1), Point(1, 0)],
            degree=2
        )
        
        original_p1 = segment1.control_points[1]
        original_q1 = segment2.control_points[1]
        
        continuity_enforcer._enforce_tangent_continuity(segment1, segment2)
        
        # Control points should be adjusted for tangent continuity
        assert segment1.control_points[1] != original_p1
        assert segment2.control_points[1] != original_q1
    
    def test_continuity_enforcer_ensure_outline_closure(self, continuity_enforcer):
        """Test enforcement of closure for closed outlines"""
        segment1 = BezierSegment(
            control_points=[Point(0, 0), Point(0.3, 0.1), Point(0.5, 0)],
            degree=2
        )
        segment2 = BezierSegment(
            control_points=[Point(0.6, 0), Point(0.7, -0.1), Point(1, 0)],  # Not connected to segment1
            degree=2
        )
        
        segments = [segment1, segment2]
        continuity_enforcer._ensure_outline_closure(segments)
        
        # Last point of last segment should match first point of first segment
        assert segments[-1].control_points[-1] == segments[0].control_points[0]
    
    # ==================== Regular Polygon Fitting Tests ====================
    
    @pytest.mark.parametrize("shape_type,corner_count", [
        ("triangle", 3),
        ("square", 4),
        ("pentagon", 5),
        ("hexagon", 6),
    ])
    def test_fit_regular_polygons_various_sizes(self, fitter, shape_type, corner_count):
        """Test fitting Bézier curves to regular polygons with different numbers of sides"""
        # Generate regular polygon points
        points = []
        for i in range(corner_count):
            angle = 2 * math.pi * i / corner_count
            x = 0.5 + 0.4 * math.cos(angle)
            y = 0.5 + 0.4 * math.sin(angle)
            points.append(Point(x, y))
        points.append(points[0])  # Close the polygon
        
        # All vertices are corners
        corner_indices = list(range(corner_count))
        
        outline = fitter.fit_outline(points, corner_indices, Color.GREEN)
        
        # Validate outline
        assert hasattr(outline, 'bezier_segments')
        assert hasattr(outline, 'corners')
        assert outline.color == Color.GREEN
        assert outline.is_closed == True
        assert len(outline.corners) == corner_count
        assert len(outline.bezier_segments) >= 1
        
        for segment in outline.bezier_segments:
            assert hasattr(segment, 'control_points')
            assert hasattr(segment, 'degree')
            assert len(segment.control_points) == segment.degree + 1
            for control_point in segment.control_points:
                assert math.isfinite(control_point.x)
                assert math.isfinite(control_point.y)
    
    # ==================== Performance and Scalability Tests ====================
    
    def test_performance_with_large_point_set(self, fitter):
        """Test fitting performance with larger point sets (100 points)"""
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
        assert duration < 5.0, f"Fitting 100 points took {duration:.2f} seconds (should be < 5s)"
        
        # Result should be valid
        assert hasattr(outline, 'bezier_segments')
        assert len(outline.bezier_segments) > 0
    
    # ==================== Edge Case and Robustness Tests ====================
    
    def test_fit_outline_open_curve_not_closed(self, fitter):
        """Test fitting Bézier curves to an open (non-closed) curve"""
        points = [
            Point(0, 0),
            Point(0.2, 0.1),
            Point(0.4, 0.2),
            Point(0.6, 0.1),
            Point(0.8, 0)
        ]
        corner_indices = [0, 4]
        
        outline = fitter.fit_outline(points, corner_indices, Color.BLUE, is_closed=False)
        
        # Validate outline structure (open)
        assert hasattr(outline, 'bezier_segments')
        assert hasattr(outline, 'corners')
        assert outline.color == Color.BLUE
        assert outline.is_closed == False
        assert len(outline.corners) == 2
        
        # Should create valid segments
        assert len(outline.bezier_segments) >= 1
        
        for segment in outline.bezier_segments:
            assert hasattr(segment, 'control_points')
            assert hasattr(segment, 'degree')
            assert len(segment.control_points) == segment.degree + 1
            for control_point in segment.control_points:
                assert math.isfinite(control_point.x)
                assert math.isfinite(control_point.y)
                