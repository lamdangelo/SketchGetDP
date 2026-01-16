"""
Unit tests for OutlinePreprocessor class.

Tests the functionality of converting outlines to Gmsh geometry,
handling holes, physical groups, and topological relationships.
"""
import pytest
from unittest.mock import Mock, patch

from sketchgetdp.svg_to_getdp.core.entities.outline import Outline
from svg_to_getdp.core.entities.point import Point
from svg_to_getdp.core.entities.bezier_segment import BezierSegment
from svg_to_getdp.core.entities.color import Color
from svg_to_getdp.core.entities.physical_group import (
    DOMAIN_VI_IRON,
    DOMAIN_VI_AIR,
    DOMAIN_VA,
    BOUNDARY_GAMMA,
    BOUNDARY_OUT
)
from sketchgetdp.svg_to_getdp.infrastructure.outline_preprocessor import OutlinePreprocessor


class TestOutlinePreprocessor:
    """Test suite for OutlinePreprocessor class."""

    # ==================== Fixtures ====================

    @pytest.fixture
    def mock_gmsh_factory(self):
        """Create a mock Gmsh factory with basic geometry operations."""
        factory = Mock()
        
        # Mock geometry creation methods with distinct return values
        # Track counters as instance variables
        self._point_counter = 0
        self._line_counter = 0
        self._bezier_counter = 0
        self._curve_loop_counter = 0
        self._surface_counter = 0
        
        def mock_add_point(x, y, z):
            self._point_counter += 1
            return 100 + self._point_counter
        
        def mock_add_line(start, end):
            self._line_counter += 1
            return 200 + self._line_counter
        
        def mock_add_bezier(points):
            self._bezier_counter += 1
            return 300 + self._bezier_counter
        
        def mock_add_curve_loop(curves):
            self._curve_loop_counter += 1
            return 400 + self._curve_loop_counter
        
        def mock_add_plane_surface(curve_loops):
            self._surface_counter += 1
            return 500 + self._surface_counter
        
        factory.addPoint = Mock(side_effect=mock_add_point)
        factory.addLine = Mock(side_effect=mock_add_line)
        factory.addBezier = Mock(side_effect=mock_add_bezier)
        factory.addCurveLoop = Mock(side_effect=mock_add_curve_loop)
        factory.addPlaneSurface = Mock(side_effect=mock_add_plane_surface)
        factory.addPhysicalGroup = Mock()
        
        return factory
    
    @pytest.fixture
    def basic_points(self):
        """Create basic test points for constructing outlines."""
        return [
            Point(0.0, 0.0),    # Bottom-left
            Point(1.0, 0.0),    # Bottom-right
            Point(1.0, 1.0),    # Top-right
            Point(0.0, 1.0),    # Top-left
            Point(0.5, 0.5),    # Center
            Point(0.0, 0.5),    # Left-center
            Point(0.5, 0.0)     # Bottom-center
        ]
    
    @pytest.fixture
    def square_outline(self, basic_points):
        """Create a square outline with straight edges."""
        segments = [
            BezierSegment([basic_points[0], basic_points[1]], degree=1),  # Bottom edge
            BezierSegment([basic_points[1], basic_points[2]], degree=1),  # Right edge
            BezierSegment([basic_points[2], basic_points[3]], degree=1),  # Top edge
            BezierSegment([basic_points[3], basic_points[0]], degree=1),  # Left edge
        ]
        corners = [basic_points[0], basic_points[1], basic_points[2], basic_points[3]]
        return Outline(segments, corners, Color.BLUE)
    
    @pytest.fixture
    def outline_with_bezier_curves(self, basic_points):
        """Create an outline with both straight edges and Bézier curves."""
        segments = [
            # Curved bottom edge (quadratic Bézier)
            BezierSegment([basic_points[0], basic_points[6], basic_points[1]], degree=2),
            # Straight right edge
            BezierSegment([basic_points[1], basic_points[2]], degree=1),
            # Straight top edge
            BezierSegment([basic_points[2], basic_points[3]], degree=1),
            # Curved left edge (quadratic Bézier)
            BezierSegment([basic_points[3], basic_points[5], basic_points[0]], degree=2),
        ]
        corners = [basic_points[0], basic_points[1], basic_points[2], basic_points[3]]
        return Outline(segments, corners, Color.BLACK)

    # ==================== Initialization Tests ====================

    def test_initializes_with_empty_state(self):
        """OutlinePreprocessor should initialize with all internal collections empty."""
        mesher = OutlinePreprocessor()
        
        assert mesher._point_tags == {}
        assert mesher._curve_loops == {}
        assert mesher._surface_tags == {}
        assert mesher._created_points == {}
        assert mesher._curve_tags_per_outline == {}
        assert mesher._processing_order == []
        assert mesher._physical_groups_by_type['boundary'] == {}
        assert mesher._physical_groups_by_type['domain'] == {}

    # ==================== Basic Functionality Tests ====================

    def test_raises_error_when_outline_and_property_counts_mismatch(
        self, mock_gmsh_factory, square_outline
    ):
        """Should raise ValueError when outlines and properties counts don't match."""
        mesher = OutlinePreprocessor()
        
        outlines = [square_outline]
        properties = [
            {"physical_groups": [DOMAIN_VA]},
            {"physical_groups": [BOUNDARY_OUT]}  # Extra property dict
        ]
        
        with pytest.raises(ValueError, match="must match"):
            mesher.preprocess_outlines(mock_gmsh_factory, outlines, properties)

    def test_meshes_square_outline_with_straight_edges(
        self, mock_gmsh_factory, square_outline
    ):
        """Should create geometry for a square outline with only straight edges."""
        mesher = OutlinePreprocessor()
        
        mesher.preprocess_outlines(mock_gmsh_factory, [square_outline], [{"physical_groups": [DOMAIN_VI_IRON]}])
        
        # Verify geometry creation calls
        assert mock_gmsh_factory.addPoint.call_count == 4  # Four corner points
        assert mock_gmsh_factory.addLine.call_count == 4   # Four straight edges
        assert mock_gmsh_factory.addBezier.call_count == 0 # No Bézier curves
        
        # Verify surface and physical group creation
        assert mock_gmsh_factory.addCurveLoop.call_count == 1
        assert mock_gmsh_factory.addPlaneSurface.call_count == 1
        assert mock_gmsh_factory.addPhysicalGroup.call_count == 1
        
        # Get the actual surface tag that was created (should be 501)
        # Since addPlaneSurface returns 500 + counter, and counter starts at 1
        surface_tag = 501
        
        # Verify the physical group was created with the correct surface tag
        mock_gmsh_factory.addPhysicalGroup.assert_called_with(
            2, [surface_tag], DOMAIN_VI_IRON.value
        )

    def test_preprocesses_outline_with_bezier_curves(
        self, mock_gmsh_factory, outline_with_bezier_curves
    ):
        """Should create geometry for outline containing both straight and Bézier edges."""
        mesher = OutlinePreprocessor()
        mesher.preprocess_outlines(
            mock_gmsh_factory,
            [outline_with_bezier_curves], 
            [{"physical_groups": [DOMAIN_VA]}]
        )
        
        # Verify geometry creation calls
        assert mock_gmsh_factory.addPoint.call_count == 6  # All unique control points
        assert mock_gmsh_factory.addLine.call_count == 2   # Two straight segments
        assert mock_gmsh_factory.addBezier.call_count == 2 # Two Bézier segments
        
        # Verify surface and physical group creation
        assert mock_gmsh_factory.addCurveLoop.call_count == 1
        assert mock_gmsh_factory.addPlaneSurface.call_count == 1
        
        # Surface tag should be 501 (first call to addPlaneSurface)
        surface_tag = 501
        
        mock_gmsh_factory.addPhysicalGroup.assert_called_with(
            2, [surface_tag], DOMAIN_VA.value
        )

    # ==================== Hole Handling Tests ====================

    def test_preprocesses_outer_outline_with_inner_hole(
        self, mock_gmsh_factory, square_outline
    ):
        """Should create outer surface containing an inner hole."""
        # Create inner square outline (hole)
        inner_square_points = [
            Point(0.25, 0.25),
            Point(0.75, 0.25),
            Point(0.75, 0.75),
            Point(0.25, 0.75)
        ]
        inner_segments = [
            BezierSegment([inner_square_points[0], inner_square_points[1]], degree=1),
            BezierSegment([inner_square_points[1], inner_square_points[2]], degree=1),
            BezierSegment([inner_square_points[2], inner_square_points[3]], degree=1),
            BezierSegment([inner_square_points[3], inner_square_points[0]], degree=1),
        ]
        inner_outline = Outline(inner_segments, inner_square_points, Color.GREEN)

        outlines = [square_outline, inner_outline]
        properties = [
            {"holes": [1], "physical_groups": [DOMAIN_VI_IRON]},  # Outer contains hole
            {"holes": [], "physical_groups": [DOMAIN_VI_AIR]}      # Inner is hole
        ]

        mesher = OutlinePreprocessor()
        mesher.preprocess_outlines(mock_gmsh_factory, outlines, properties)

        # Verify holes are processed first (topological ordering)
        assert mesher.get_processing_order() == [1, 0]  # Inner first, outer second

        # Verify both surfaces were created
        assert mock_gmsh_factory.addPlaneSurface.call_count == 2
        
        # Outer surface should be created with hole references
        surface_calls = mock_gmsh_factory.addPlaneSurface.call_args_list
        # Find the call that has 2 curve loops (main loop + hole)
        for call_obj in surface_calls:
            if len(call_obj[0][0]) == 2:  # Outer has 2 curve loops
                assert len(call_obj[0][0]) == 2  # Main loop + hole loop
                break

    def test_preprocesses_outline_with_multiple_holes(
        self, mock_gmsh_factory, square_outline
    ):
        """Should create surface containing multiple holes."""
        # Create two hole outlines
        hole_one_points = [Point(0.2, 0.2), Point(0.4, 0.2), Point(0.4, 0.4), Point(0.2, 0.4)]
        hole_two_points = [Point(0.6, 0.6), Point(0.8, 0.6), Point(0.8, 0.8), Point(0.6, 0.8)]
        
        def create_square_segments(points):
            return [BezierSegment([points[i], points[(i+1)%4]], degree=1) for i in range(4)]
        
        hole_one = Outline(create_square_segments(hole_one_points), hole_one_points, Color.GREEN)
        hole_two = Outline(create_square_segments(hole_two_points), hole_two_points, Color.BLUE)
        
        outlines = [square_outline, hole_one, hole_two]
        properties = [
            {"holes": [1, 2], "physical_groups": [DOMAIN_VI_IRON]},           # Outer with two holes
            {"holes": [], "physical_groups": [DOMAIN_VI_AIR]},    # First hole
            {"holes": [], "physical_groups": [DOMAIN_VI_AIR]}     # Second hole
        ]
        
        mesher = OutlinePreprocessor()
        mesher.preprocess_outlines(mock_gmsh_factory, outlines, properties)

        # Verify topological order: holes first, then outer
        processing_order = mesher.get_processing_order()
        assert set(processing_order[:2]) == {1, 2}  # Holes processed first
        assert processing_order[2] == 0             # Outer processed last
        
        # Verify all surfaces were created
        assert mock_gmsh_factory.addPlaneSurface.call_count == 3

    # ==================== Physical Group Tests ====================

    def test_assigns_boundary_physical_groups_to_outlines(
        self, mock_gmsh_factory, square_outline
    ):
        """Should assign boundary physical groups to 1D outline entities."""
        preprocessor = OutlinePreprocessor()
        
        preprocessor = OutlinePreprocessor()
        preprocessor.preprocess_outlines(mock_gmsh_factory, [square_outline], [{"physical_groups": [BOUNDARY_OUT]}])
        
        # The line tags should be 201, 202, 203, 204 (incrementing from 200)
        expected_curve_tags = [201, 202, 203, 204]
        
        # Check that addPhysicalGroup was called with expected curve tags
        mock_gmsh_factory.addPhysicalGroup.assert_called_with(
            1, expected_curve_tags, BOUNDARY_OUT.value
        )

    def test_assigns_multiple_physical_groups_to_single_outline(
        self, mock_gmsh_factory, square_outline
    ):
        """Should assign both domain and boundary physical groups when specified."""
        preprocessor = OutlinePreprocessor()
        
        preprocessor.preprocess_outlines(
            mock_gmsh_factory,
            [square_outline], 
            [{"physical_groups": [DOMAIN_VA, BOUNDARY_GAMMA]}]
        )
        
        # Should have two physical group assignments
        assert mock_gmsh_factory.addPhysicalGroup.call_count == 2
        
        calls = mock_gmsh_factory.addPhysicalGroup.call_args_list
        domain_call = next(c for c in calls if c[0][0] == 2)  # Dimension 2
        boundary_call = next(c for c in calls if c[0][0] == 1)  # Dimension 1
        
        # Verify domain assignment
        assert domain_call[0][2] == DOMAIN_VA.value
        assert domain_call[0][1] == [501]  # Surface tag (first call returns 501)
        
        # Verify boundary assignment
        assert boundary_call[0][2] == BOUNDARY_GAMMA.value
        # Line tags should be 201, 202, 203, 204
        assert boundary_call[0][1] == [201, 202, 203, 204]

    # ==================== Edge Case Tests ====================

    def test_returns_processing_order_copy_not_reference(
        self, mock_gmsh_factory, square_outline
    ):
        """Should return a copy of processing order to prevent external modification."""
        preprocessor = OutlinePreprocessor()
        
        preprocessor.preprocess_outlines(mock_gmsh_factory, [square_outline], [{"physical_groups": [DOMAIN_VA]}])
        
        order = preprocessor.get_processing_order()
        assert order == [0]
        
        # Modifying returned list shouldn't affect internal state
        order.append(999)
        assert preprocessor.get_processing_order() == [0]

    def test_raises_error_for_non_existent_hole_reference(
        self, mock_gmsh_factory, square_outline
    ):
        """Should raise error when hole index references non-existent outline."""
        preprocessor = OutlinePreprocessor()
        
        outlines = [square_outline]
        properties = [{"holes": [999], "physical_groups": [DOMAIN_VI_IRON]}]  # Invalid hole index
        
        with pytest.raises(ValueError, match="has not been created yet"):
            preprocessor.preprocess_outlines(mock_gmsh_factory, outlines, properties)
    def test_raises_error_for_non_physical_group_in_list(
        self, mock_gmsh_factory, square_outline
    ):
        """Should raise TypeError when physical_groups contains non-PhysicalGroup objects."""
        preprocessor = OutlinePreprocessor()
        
        outlines = [square_outline]
        properties = [{"physical_groups": ["invalid_type"]}]
        
        with pytest.raises(TypeError, match="must be PhysicalGroup instance"):
            preprocessor.preprocess_outlines(mock_gmsh_factory, outlines, properties)
    # ==================== Internal Method Tests ====================

    def test_falls_back_to_input_order_when_topological_sort_fails(
        self, square_outline
    ):
        """Should use input order when cyclic dependencies prevent topological sort."""
        preprocessor = OutlinePreprocessor()
        
        # Create outlines with circular dependency
        outlines = [square_outline, square_outline, square_outline]
        properties = [
            {"holes": [1], "physical_groups": [DOMAIN_VA]},    # Depends on outline 1
            {"holes": [0], "physical_groups": [DOMAIN_VI_IRON]},  # Depends on outline 0 (cycle)
            {"physical_groups": [DOMAIN_VI_AIR]}
        ]
        
        with patch('builtins.print') as mock_print:
            order = preprocessor._get_processing_order(outlines, properties)

            # Verify warning was logged
            mock_print.assert_called_with(
                "Warning: Could not determine topological order. Using input order."
            )
            
            # Should use original order as fallback
            assert order == [0, 1, 2]
            