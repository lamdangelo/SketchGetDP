"""
Unit tests for BoundaryCurveMesher class.

Tests the functionality of converting boundary curves to Gmsh geometry,
handling holes, physical groups, and topological relationships.
"""
import pytest
from unittest.mock import Mock, patch

import gmsh

from svg_to_getdp.core.entities.boundary_curve import BoundaryCurve
from svg_to_getdp.core.entities.point import Point
from svg_to_getdp.core.entities.bezier_segment import BezierSegment
from svg_to_getdp.core.entities.color import Color
from svg_to_getdp.core.entities.physical_group import (
    PhysicalGroup,
    DOMAIN_VI_IRON,
    DOMAIN_VI_AIR,
    DOMAIN_VA,
    DOMAIN_COIL_POSITIVE,
    DOMAIN_COIL_NEGATIVE,
    BOUNDARY_GAMMA,
    BOUNDARY_OUT
)
from svg_to_getdp.infrastructure.boundary_curve_mesher import BoundaryCurveMesher


class TestBoundaryCurveMesher:
    """Test suite for BoundaryCurveMesher class."""

    @pytest.fixture
    def mock_gmsh_factory(self):
        """Create a mock Gmsh factory with basic geometry operations."""
        factory = Mock()
        factory.synchronize = Mock()
        
        # Mock geometry creation methods with distinct return values
        factory.addPoint = Mock(return_value=100)
        factory.addLine = Mock(return_value=200)
        factory.addBezier = Mock(return_value=300)
        factory.addCurveLoop = Mock(return_value=400)
        factory.addPlaneSurface = Mock(return_value=500)
        factory.addPhysicalGroup = Mock()
        
        return factory
    
    @pytest.fixture
    def basic_points(self):
        """Create basic test points for constructing boundaries."""
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
    def square_boundary(self, basic_points):
        """Create a square boundary with straight edges."""
        segments = [
            BezierSegment([basic_points[0], basic_points[1]], degree=1),  # Bottom edge
            BezierSegment([basic_points[1], basic_points[2]], degree=1),  # Right edge
            BezierSegment([basic_points[2], basic_points[3]], degree=1),  # Top edge
            BezierSegment([basic_points[3], basic_points[0]], degree=1),  # Left edge
        ]
        corners = [basic_points[0], basic_points[1], basic_points[2], basic_points[3]]
        return BoundaryCurve(segments, corners, Color.BLACK)
    
    @pytest.fixture
    def boundary_with_bezier_curves(self, basic_points):
        """Create a boundary with both straight edges and Bézier curves."""
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
        return BoundaryCurve(segments, corners, Color.RED)

    def test_initializes_with_empty_state(self, mock_gmsh_factory):
        """BoundaryCurveMesher should initialize with all internal collections empty."""
        mesher = BoundaryCurveMesher(mock_gmsh_factory)
        
        assert mesher.factory == mock_gmsh_factory
        assert mesher._point_tags == {}
        assert mesher._curve_loops == {}
        assert mesher._surface_tags == {}
        assert mesher._created_points == {}
        assert mesher._curve_tags_per_boundary == {}
        assert mesher._processing_order == []

    def test_raises_error_when_boundary_and_property_counts_mismatch(
        self, mock_gmsh_factory, square_boundary
    ):
        """Should raise ValueError when boundary curves and properties counts don't match."""
        mesher = BoundaryCurveMesher(mock_gmsh_factory)
        
        boundary_curves = [square_boundary]
        properties = [
            {"physical_groups": [DOMAIN_VA]},
            {"physical_groups": [BOUNDARY_OUT]}  # Extra property dict
        ]
        
        with pytest.raises(ValueError, match="must match"):
            mesher.mesh_boundary_curves(boundary_curves, properties)

    def test_meshes_square_boundary_with_straight_edges(
        self, mock_gmsh_factory, square_boundary
    ):
        """Should create geometry for a square boundary with only straight edges."""
        mesher = BoundaryCurveMesher(mock_gmsh_factory)
        
        mesher.mesh_boundary_curves([square_boundary], [{"physical_groups": [DOMAIN_VA]}])
        
        # Verify geometry creation calls
        assert mock_gmsh_factory.synchronize.called
        assert mock_gmsh_factory.addPoint.call_count == 4  # Four corner points
        assert mock_gmsh_factory.addLine.call_count == 4   # Four straight edges
        assert mock_gmsh_factory.addBezier.call_count == 0 # No Bézier curves
        
        # Verify surface and physical group creation
        assert mock_gmsh_factory.addCurveLoop.call_count == 1
        assert mock_gmsh_factory.addPlaneSurface.call_count == 1
        assert mock_gmsh_factory.addPhysicalGroup.call_count == 1
        
        expected_surface_tag = mock_gmsh_factory.addPlaneSurface.return_value
        mock_gmsh_factory.addPhysicalGroup.assert_called_with(
            2, [expected_surface_tag], DOMAIN_VA.value
        )

    def test_meshes_boundary_with_bezier_curves(
        self, mock_gmsh_factory, boundary_with_bezier_curves
    ):
        """Should create geometry for boundary containing both straight and Bézier edges."""
        mesher = BoundaryCurveMesher(mock_gmsh_factory)
        
        mesher.mesh_boundary_curves(
            [boundary_with_bezier_curves], 
            [{"physical_groups": [DOMAIN_VI_IRON]}]
        )
        
        # Verify geometry creation calls
        assert mock_gmsh_factory.synchronize.called
        assert mock_gmsh_factory.addPoint.call_count == 6  # All unique control points
        assert mock_gmsh_factory.addLine.call_count == 2   # Two straight segments
        assert mock_gmsh_factory.addBezier.call_count == 2 # Two Bézier segments
        
        # Verify surface and physical group creation
        assert mock_gmsh_factory.addCurveLoop.call_count == 1
        assert mock_gmsh_factory.addPlaneSurface.call_count == 1
        
        expected_surface_tag = mock_gmsh_factory.addPlaneSurface.return_value
        mock_gmsh_factory.addPhysicalGroup.assert_called_with(
            2, [expected_surface_tag], DOMAIN_VI_IRON.value
        )

    def test_meshes_outer_boundary_with_inner_hole(
        self, mock_gmsh_factory, square_boundary, basic_points
    ):
        """Should create outer surface containing an inner hole."""
        # Create inner square boundary (hole)
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
        inner_boundary = BoundaryCurve(inner_segments, inner_square_points, Color.GREEN)

        boundary_curves = [square_boundary, inner_boundary]
        properties = [
            {"holes": [1], "physical_groups": [DOMAIN_VI_IRON]},  # Outer contains hole
            {"holes": [], "physical_groups": [DOMAIN_VI_AIR]}      # Inner is hole
        ]

        mesher = BoundaryCurveMesher(mock_gmsh_factory)
        mesher.mesh_boundary_curves(boundary_curves, properties)

        # Verify holes are processed first (topological ordering)
        assert mesher.get_processing_order() == [1, 0]  # Inner first, outer second

        # Verify both surfaces were created
        assert mock_gmsh_factory.addPlaneSurface.call_count == 2
        
        # Outer surface should be created with hole references
        surface_calls = mock_gmsh_factory.addPlaneSurface.call_args_list
        outer_surface_call = next(
            call for call in surface_calls if len(call[0][0]) == 2  # Outer has 2 curve loops
        )
        assert len(outer_surface_call[0][0]) == 2  # Main loop + hole loop

    def test_meshes_boundary_with_multiple_holes(
        self, mock_gmsh_factory, square_boundary
    ):
        """Should create surface containing multiple holes."""
        # Create two hole boundaries
        hole_one_points = [Point(0.2, 0.2), Point(0.4, 0.2), Point(0.4, 0.4), Point(0.2, 0.4)]
        hole_two_points = [Point(0.6, 0.6), Point(0.8, 0.6), Point(0.8, 0.8), Point(0.6, 0.8)]
        
        def create_square_segments(points):
            return [BezierSegment([points[i], points[(i+1)%4]], degree=1) for i in range(4)]
        
        hole_one = BoundaryCurve(create_square_segments(hole_one_points), hole_one_points, Color.RED)
        hole_two = BoundaryCurve(create_square_segments(hole_two_points), hole_two_points, Color.BLUE)
        
        boundary_curves = [square_boundary, hole_one, hole_two]
        properties = [
            {"holes": [1, 2], "physical_groups": [DOMAIN_VA]},           # Outer with two holes
            {"holes": [], "physical_groups": [DOMAIN_COIL_POSITIVE]},    # First hole
            {"holes": [], "physical_groups": [DOMAIN_COIL_NEGATIVE]}     # Second hole
        ]
        
        mesher = BoundaryCurveMesher(mock_gmsh_factory)
        mesher.mesh_boundary_curves(boundary_curves, properties)
        
        # Verify topological order: holes first, then outer
        processing_order = mesher.get_processing_order()
        assert set(processing_order[:2]) == {1, 2}  # Holes processed first
        assert processing_order[2] == 0             # Outer processed last
        
        # Verify all surfaces were created
        assert mock_gmsh_factory.addPlaneSurface.call_count == 3

    def test_assigns_boundary_physical_groups_to_curves(
        self, mock_gmsh_factory, square_boundary
    ):
        """Should assign boundary physical groups to 1D curve entities."""
        mesher = BoundaryCurveMesher(mock_gmsh_factory)
        
        mesher.mesh_boundary_curves([square_boundary], [{"physical_groups": [BOUNDARY_OUT]}])
        
        # Verify boundary physical group assigned to curves
        expected_curve_tags = [200, 200, 200, 200]  # Four line segments
        mock_gmsh_factory.addPhysicalGroup.assert_called_with(
            1, expected_curve_tags, BOUNDARY_OUT.value
        )

    def test_assigns_multiple_physical_groups_to_single_boundary(
        self, mock_gmsh_factory, square_boundary
    ):
        """Should assign both domain and boundary physical groups when specified."""
        mesher = BoundaryCurveMesher(mock_gmsh_factory)
        
        mesher.mesh_boundary_curves(
            [square_boundary], 
            [{"physical_groups": [DOMAIN_VA, BOUNDARY_GAMMA]}]
        )
        
        # Should have two physical group assignments
        assert mock_gmsh_factory.addPhysicalGroup.call_count == 2
        
        calls = mock_gmsh_factory.addPhysicalGroup.call_args_list
        domain_call = next(call for call in calls if call[0][0] == 2)  # Dimension 2
        boundary_call = next(call for call in calls if call[0][0] == 1)  # Dimension 1
        
        # Verify domain assignment
        assert domain_call[0][2] == DOMAIN_VA.value
        assert domain_call[0][1] == [500]  # Surface tag
        
        # Verify boundary assignment
        assert boundary_call[0][2] == BOUNDARY_GAMMA.value
        assert boundary_call[0][1] == [200, 200, 200, 200]  # Curve tags

    def test_reuses_existing_points_instead_of_creating_duplicates(
        self, mock_gmsh_factory
    ):
        """Should return cached point tag for duplicate coordinates."""
        mesher = BoundaryCurveMesher(mock_gmsh_factory)
        
        # Configure mock to return incrementing values
        point_counter = 0
        def mock_add_point(x, y, z):
            nonlocal point_counter
            point_counter += 1
            return 100 + point_counter
        
        mock_gmsh_factory.addPoint.side_effect = mock_add_point
        
        first_point = Point(1.0, 2.0)
        second_point = Point(3.0, 4.0)
        
        # First call creates point
        first_tag = mesher._create_or_get_point(first_point)
        assert first_tag == 101
        
        # Same point returns cached tag
        cached_tag = mesher._create_or_get_point(first_point)
        assert cached_tag == first_tag == 101
        
        # Different point creates new point
        new_tag = mesher._create_or_get_point(second_point)
        assert new_tag == 102
        assert new_tag != first_tag

    def test_returns_processing_order_copy_not_reference(
        self, mock_gmsh_factory, square_boundary
    ):
        """Should return a copy of processing order to prevent external modification."""
        mesher = BoundaryCurveMesher(mock_gmsh_factory)
        
        mesher.mesh_boundary_curves([square_boundary], [{"physical_groups": [DOMAIN_VA]}])
        
        order = mesher.get_processing_order()
        assert order == [0]
        
        # Modifying returned list shouldn't affect internal state
        order.append(999)
        assert mesher.get_processing_order() == [0]

    def test_retrieves_curve_loop_tag_by_boundary_index(
        self, mock_gmsh_factory, square_boundary
    ):
        """Should retrieve curve loop tag for existing boundary index."""
        mesher = BoundaryCurveMesher(mock_gmsh_factory)
        
        mesher.mesh_boundary_curves([square_boundary], [{"physical_groups": [DOMAIN_VA]}])
        
        tag = mesher.get_curve_loop_tag(0)
        assert tag == mock_gmsh_factory.addCurveLoop.return_value
        
        with pytest.raises(KeyError):
            mesher.get_curve_loop_tag(999)  # Non-existent index

    def test_retrieves_surface_tag_by_boundary_index(
        self, mock_gmsh_factory, square_boundary
    ):
        """Should retrieve surface tag for existing boundary index."""
        mesher = BoundaryCurveMesher(mock_gmsh_factory)
        
        mesher.mesh_boundary_curves([square_boundary], [{"physical_groups": [DOMAIN_VA]}])
        
        tag = mesher.get_surface_tag(0)
        assert tag == mock_gmsh_factory.addPlaneSurface.return_value
        
        with pytest.raises(KeyError):
            mesher.get_surface_tag(999)  # Non-existent index

    def test_retrieves_curve_tags_by_boundary_index(
        self, mock_gmsh_factory, square_boundary
    ):
        """Should retrieve all curve tags for existing boundary."""
        mesher = BoundaryCurveMesher(mock_gmsh_factory)
        
        mesher.mesh_boundary_curves([square_boundary], [{"physical_groups": [DOMAIN_VA]}])
        
        tags = mesher.get_curve_tags(0)
        assert len(tags) == 4  # Four edges
        
        with pytest.raises(KeyError):
            mesher.get_curve_tags(999)  # Non-existent index

    def test_clears_all_internal_state(self, mock_gmsh_factory, square_boundary):
        """Should reset all internal collections to empty state."""
        mesher = BoundaryCurveMesher(mock_gmsh_factory)
        
        mesher.mesh_boundary_curves([square_boundary], [{"physical_groups": [DOMAIN_VA]}])
        
        # Verify state is populated
        assert len(mesher._curve_loops) > 0
        assert len(mesher._surface_tags) > 0
        assert len(mesher._created_points) > 0
        assert len(mesher._curve_tags_per_boundary) > 0
        assert len(mesher._processing_order) > 0
        
        # Clear and verify empty state
        mesher.clear()
        assert mesher._curve_loops == {}
        assert mesher._surface_tags == {}
        assert mesher._created_points == {}
        assert mesher._curve_tags_per_boundary == {}
        assert mesher._processing_order == []

    def test_raises_error_for_non_existent_hole_reference(
        self, mock_gmsh_factory, square_boundary
    ):
        """Should raise error when hole index references non-existent boundary."""
        mesher = BoundaryCurveMesher(mock_gmsh_factory)
        
        boundary_curves = [square_boundary]
        properties = [{"holes": [999], "physical_groups": [DOMAIN_VA]}]  # Invalid hole index
        
        with pytest.raises(ValueError, match="has not been created yet"):
            mesher.mesh_boundary_curves(boundary_curves, properties)

    def test_raises_error_for_non_physical_group_in_list(
        self, mock_gmsh_factory, square_boundary
    ):
        """Should raise TypeError when physical_groups contains non-PhysicalGroup objects."""
        mesher = BoundaryCurveMesher(mock_gmsh_factory)
        
        boundary_curves = [square_boundary]
        properties = [{"physical_groups": ["invalid_type"]}]
        
        with pytest.raises(TypeError, match="must be PhysicalGroup instance"):
            mesher.mesh_boundary_curves(boundary_curves, properties)

    def test_falls_back_to_input_order_when_topological_sort_fails(
        self, mock_gmsh_factory, square_boundary
    ):
        """Should use input order when cyclic dependencies prevent topological sort."""
        mesher = BoundaryCurveMesher(mock_gmsh_factory)
        
        # Create boundaries with circular dependency
        boundaries = [square_boundary, square_boundary, square_boundary]
        properties = [
            {"holes": [1], "physical_groups": [DOMAIN_VA]},    # Depends on boundary 1
            {"holes": [0], "physical_groups": [DOMAIN_VI_IRON]},  # Depends on boundary 0 (cycle)
            {"physical_groups": [DOMAIN_VI_AIR]}
        ]
        
        with patch('builtins.print') as mock_print:
            order = mesher._get_processing_order(boundaries, properties)
            
            # Verify warning was logged
            mock_print.assert_called_with(
                "Warning: Could not determine topological order. Using input order."
            )
            
            # Should use original order as fallback
            assert order == [0, 1, 2]