import pytest
from unittest.mock import patch, MagicMock, PropertyMock
import math

from svg_to_gmsh.core.entities.point import Point
from svg_to_gmsh.core.entities.color import Color
from svg_to_gmsh.core.entities.bezier_segment import BezierSegment
from svg_to_gmsh.core.entities.boundary_curve import BoundaryCurve
from svg_to_gmsh.core.entities.physical_group import (
    DOMAIN_VA, 
    DOMAIN_VI_IRON, 
    DOMAIN_VI_AIR, 
    BOUNDARY_GAMMA, 
    BOUNDARY_OUT
)
from svg_to_gmsh.infrastructure.boundary_curve_grouper import BoundaryCurveGrouper


# ============================================================================
# Fixtures and Helper Functions
# ============================================================================

@pytest.fixture
def sample_points():
    """Create sample points for testing."""
    return [
        Point(0.0, 0.0),
        Point(1.0, 0.0),
        Point(2.0, 0.0),
        Point(3.0, 1.0),
        Point(0.0, 2.0),
        Point(1.0, 2.0),
        Point(2.0, 2.0),
    ]


@pytest.fixture
def create_square_boundary():
    """Create a simple square boundary curve."""
    def _create(center_x=0.0, center_y=0.0, size=1.0, color=Color.BLACK, closed=True):
        half = size / 2.0
        # Create 4 line segments for a square
        segments = []
        corners = []
        
        # Define the 4 corners
        corners.append(Point(center_x - half, center_y - half))  # bottom-left
        corners.append(Point(center_x + half, center_y - half))  # bottom-right
        corners.append(Point(center_x + half, center_y + half))  # top-right
        corners.append(Point(center_x - half, center_y + half))  # top-left
        
        # Create segments connecting the corners
        for i in range(4):
            start = corners[i]
            end = corners[(i + 1) % 4]
            # Linear Bézier (degree 1) - just a line
            segment = BezierSegment([start, end], degree=1)
            segments.append(segment)
        
        return BoundaryCurve(
            bezier_segments=segments,
            corners=corners,
            color=color,
            is_closed=closed
        )
    return _create


@pytest.fixture
def sample_boundary_curves(create_square_boundary):
    """Create a set of sample boundary curves for testing."""
    # Outer green square (Vi air domain)
    outer = create_square_boundary(center_x=0.0, center_y=0.0, size=10.0, color=Color.GREEN)
    
    # Inner blue square (Vi iron domain)
    inner1 = create_square_boundary(center_x=0.0, center_y=0.0, size=6.0, color=Color.BLUE)
    
    # Even inner green square (Vi air domain)
    inner2 = create_square_boundary(center_x=0.0, center_y=0.0, size=3.0, color=Color.GREEN)
    
    # Black square inside the green one
    inner3 = create_square_boundary(center_x=0.0, center_y=0.0, size=1.0, color=Color.BLACK)
    
    return [outer, inner1, inner2, inner3]


# ============================================================================
# Test Cases for BoundaryCurveGrouper
# ============================================================================

class TestBoundaryCurveGrouper:
    """Test suite for BoundaryCurveGrouper class."""
    
    def test_should_return_true_when_point_is_inside_closed_square_boundary(self, create_square_boundary):
        """Test point inside/outside detection for square boundary."""
        square = create_square_boundary(center_x=0.0, center_y=0.0, size=4.0)
        
        # Points inside
        assert BoundaryCurveGrouper.is_point_inside_boundary(Point(0.0, 0.0), square)
        assert BoundaryCurveGrouper.is_point_inside_boundary(Point(0.5, 0.5), square)
        assert BoundaryCurveGrouper.is_point_inside_boundary(Point(-0.5, -0.5), square)
        
        # Points outside
        assert not BoundaryCurveGrouper.is_point_inside_boundary(Point(2.0, 2.0), square)
        assert not BoundaryCurveGrouper.is_point_inside_boundary(Point(-2.0, -2.0), square)
        assert not BoundaryCurveGrouper.is_point_inside_boundary(Point(0.0, 2.0), square)  # on edge
    
    def test_should_return_false_when_point_is_inside_open_curve(self, create_square_boundary):
        """Test that open curves always return False."""
        open_square = create_square_boundary(center_x=0.0, center_y=0.0, size=4.0, closed=False)
        
        # Even points that would be inside a closed curve should return False
        assert not BoundaryCurveGrouper.is_point_inside_boundary(Point(0.0, 0.0), open_square)
    
    def test_should_raise_value_error_when_getting_bounding_box_for_empty_curve(self):
        """Test bounding box with empty curve."""
        mock_curve = MagicMock()
        type(mock_curve).control_points = PropertyMock(return_value=[])
        
        with pytest.raises(ValueError, match="must have at least one control point"):
            BoundaryCurveGrouper.get_curve_bounding_box(mock_curve)
    
    def test_should_detect_when_one_curve_is_inside_another(self, create_square_boundary):
        """Test curve containment detection."""
        outer = create_square_boundary(center_x=0.0, center_y=0.0, size=10.0)
        inner = create_square_boundary(center_x=0.0, center_y=0.0, size=5.0)
        separate = create_square_boundary(center_x=20.0, center_y=20.0, size=5.0)
        
        # Inner is inside outer
        assert BoundaryCurveGrouper.is_curve_inside_other(inner, outer)
        
        # Outer is not inside inner
        assert not BoundaryCurveGrouper.is_curve_inside_other(outer, inner)
        
        # Separate is not inside outer
        assert not BoundaryCurveGrouper.is_curve_inside_other(separate, outer)
    
    def test_should_correctly_identify_containment_hierarchy_for_nested_squares(self, create_square_boundary):
        """Test containment hierarchy detection."""
        # Create nested squares
        curves = [
            create_square_boundary(center_x=0.0, center_y=0.0, size=10.0, color=Color.BLACK),    # 0
            create_square_boundary(center_x=0.0, center_y=0.0, size=6.0, color=Color.BLUE),      # 1
            create_square_boundary(center_x=0.0, center_y=0.0, size=3.0, color=Color.GREEN),     # 2
            create_square_boundary(center_x=0.0, center_y=0.0, size=1.0, color=Color.BLACK),     # 3
            create_square_boundary(center_x=20.0, center_y=20.0, size=5.0, color=Color.BLACK),   # 4
        ]

        hierarchy = BoundaryCurveGrouper.get_containment_hierarchy(curves)

        # Expected hierarchy (only immediate children):
        # Curve 0 contains 1 (curve 1 is inside curve 0)
        # Curve 1 contains 2 (curve 2 is inside curve 1)
        # Curve 2 contains 3 (curve 3 is inside curve 2)

        assert hierarchy[0] == [1]
        assert hierarchy[1] == [2]
        assert hierarchy[2] == [3]
        assert hierarchy[3] == []
    
    def test_should_classify_curve_colors_correctly(self, create_square_boundary):
        """Test curve color classification."""
        black_curve = create_square_boundary(color=Color.BLACK)
        blue_curve = create_square_boundary(color=Color.BLUE)
        green_curve = create_square_boundary(color=Color.GREEN)
        
        assert BoundaryCurveGrouper.classify_curve_color(black_curve) == "va"
        assert BoundaryCurveGrouper.classify_curve_color(blue_curve) == "vi_iron"
        assert BoundaryCurveGrouper.classify_curve_color(green_curve) == "vi_air"
    
    def test_should_raise_value_error_when_classifying_curve_with_invalid_color(self):
        """Test curve color classification with invalid color."""
        red_curve = BoundaryCurve(
            bezier_segments=[BezierSegment([Point(0,0), Point(1,0)], degree=1)],
            corners=[Point(0,0), Point(1,0)],
            color=Color.RED,
            is_closed=True
        )
        
        with pytest.raises(ValueError, match="Unknown curve color"):
            BoundaryCurveGrouper.classify_curve_color(red_curve)
    
    def test_should_assign_correct_physical_groups_based_on_curve_classification(self, create_square_boundary):
        """Test physical group assignment for curves."""
        # Test Va curve
        va_curve = create_square_boundary(color=Color.BLACK)
        groups = BoundaryCurveGrouper.get_physical_groups_for_curve(
            curve=va_curve,
            classification="va",
            is_outermost=False,
            is_va_in_vi=False
        )
        assert len(groups) == 1
        assert groups[0] == DOMAIN_VA
        
        # Test Va curve inside Vi (should get BOUNDARY_GAMMA too)
        groups = BoundaryCurveGrouper.get_physical_groups_for_curve(
            curve=va_curve,
            classification="va",
            is_outermost=False,
            is_va_in_vi=True
        )
        assert len(groups) == 2
        assert BOUNDARY_GAMMA in groups
        assert DOMAIN_VA in groups
        
        # Test outermost curve (should get BOUNDARY_OUT)
        groups = BoundaryCurveGrouper.get_physical_groups_for_curve(
            curve=va_curve,
            classification="va",
            is_outermost=True,
            is_va_in_vi=False
        )
        assert len(groups) == 2
        assert DOMAIN_VA in groups
        assert BOUNDARY_OUT in groups
    
    def test_should_group_single_boundary_curve_as_outermost(self, create_square_boundary):
        """Test basic grouping of boundary curves."""
        # Simple case: one outer Va curve
        curves = [create_square_boundary(color=Color.BLACK)]
        
        result = BoundaryCurveGrouper.group_boundary_curves(curves)
        
        assert len(result) == 1
        assert result[0]["holes"] == []
        assert len(result[0]["physical_groups"]) == 2  # DOMAIN_VA + BOUNDARY_OUT
        assert DOMAIN_VA in result[0]["physical_groups"]
        assert BOUNDARY_OUT in result[0]["physical_groups"]
    
    def test_should_correctly_group_nested_boundary_curves_with_varying_colors(self, sample_boundary_curves):
        """Test grouping of nested boundary curves."""
        result = BoundaryCurveGrouper.group_boundary_curves(sample_boundary_curves)
        
        assert len(result) == 4
        
        # Check curve 0 (outermost green - Vi air)
        assert result[0]["holes"] == [1]  # Contains only the immediate child (inner1 - blue)
        assert DOMAIN_VI_AIR in result[0]["physical_groups"]
        assert BOUNDARY_OUT in result[0]["physical_groups"]
        
        # Check curve 1 (blue inner1 - Vi iron)
        assert result[1]["holes"] == [2]  # Contains only the immediate child (inner2 - green)
        assert DOMAIN_VI_IRON in result[1]["physical_groups"]
        
        # Check curve 2 (green inner2 - Vi air)
        assert result[2]["holes"] == [3]  # Contains only the immediate child (inner3 - black)
        assert DOMAIN_VI_AIR in result[2]["physical_groups"]
        
        # Check curve 3 (innermost black - Va)
        assert result[3]["holes"] == []  # Contains nothing
        assert DOMAIN_VA in result[3]["physical_groups"]
        assert BOUNDARY_GAMMA in result[3]["physical_groups"]  # Inside Vi
    
    def test_should_return_empty_list_when_grouping_empty_boundary_curves(self):
        """Test grouping with empty input."""
        result = BoundaryCurveGrouper.group_boundary_curves([])
        assert result == []
    
    def test_should_always_consider_single_curve_as_outermost(self, create_square_boundary):
        """Test that a single curve is always considered outermost."""
        curve = create_square_boundary(color=Color.BLACK)
        result = BoundaryCurveGrouper.group_boundary_curves([curve])
        
        assert len(result) == 1
        assert BOUNDARY_OUT in result[0]["physical_groups"]
    
    @patch('svg_to_gmsh.infrastructure.boundary_curve_grouper.BoundaryCurveGrouper.is_curve_inside_other')
    def test_should_detect_va_curves_inside_vi_curves_and_assign_boundary_gamma(self, mock_is_inside, create_square_boundary):
        """Test detection of Va curves inside Vi curves."""
        # Setup mock to simulate Va inside Vi
        def side_effect(curve, other):
            # Simple mock: return True if curve is black and other is blue or green
            if curve.color == Color.BLACK and other.color in [Color.BLUE, Color.GREEN]:
                return True
            return False
        
        mock_is_inside.side_effect = side_effect
        
        # Create curves
        vi_curve = create_square_boundary(color=Color.BLUE)
        va_curve = create_square_boundary(color=Color.BLACK)
        
        curves = [vi_curve, va_curve]
        
        # Mock the containment hierarchy to show Va is inside Vi
        with patch('svg_to_gmsh.infrastructure.boundary_curve_grouper.BoundaryCurveGrouper.get_containment_hierarchy') as mock_hierarchy:
            mock_hierarchy.return_value = {0: [1], 1: []}  # Vi contains Va
            
            result = BoundaryCurveGrouper.group_boundary_curves(curves)
            
            # Check that Va curve got BOUNDARY_GAMMA
            assert BOUNDARY_GAMMA in result[1]["physical_groups"]
    
    def test_should_raise_error_when_no_outermost_candidate_can_be_determined(self, create_square_boundary):
        """Test error when no outermost candidate is found."""
        # Create a circular dependency scenario (shouldn't happen in practice)
        curve1 = create_square_boundary(color=Color.BLACK)
        curve2 = create_square_boundary(color=Color.BLUE)
        
        # Mock containment hierarchy to create circular reference
        # Use the full module path for patching
        with patch('svg_to_gmsh.infrastructure.boundary_curve_grouper.BoundaryCurveGrouper.get_containment_hierarchy') as mock_hierarchy:
            mock_hierarchy.return_value = {0: [1], 1: [0]}  # Each contains the other
            
            with pytest.raises(ValueError, match="No outermost candidates found"):
                BoundaryCurveGrouper.group_boundary_curves([curve1, curve2])
    
    def test_should_print_comprehensive_grouping_summary_to_stdout(self, sample_boundary_curves, capsys):
        """Test the summary printing function."""
        result = BoundaryCurveGrouper.group_boundary_curves(sample_boundary_curves)
        
        # Call the summary function
        BoundaryCurveGrouper.print_grouping_summary(sample_boundary_curves, result)
        
        # Capture the output
        captured = capsys.readouterr()
        
        # Check that expected text appears in output
        assert "BOUNDARY CURVE GROUPING SUMMARY" in captured.out
        assert "Curve 0:" in captured.out
        assert "Color: black" in captured.out
        # Check for actual physical group names from the output
        assert any("domain_Va" in line or "boundary_out" in line or "boundary_gamma" in line or 
                   "domain_Vi_iron" in line or "domain_Vi_air" in line 
                   for line in captured.out.split('\n'))
        assert "CONTAINMENT HIERARCHY" in captured.out


# ============================================================================
# Integration Tests
# ============================================================================

class TestBoundaryCurveGrouperIntegration:
    """Integration tests for BoundaryCurveGrouper with real curve data."""
    
    def test_should_process_triangle_boundary_curve_and_correctly_determine_containment(self):
        """Test complete workflow with actual Bézier segments."""
        # Create a simple triangle using linear Bézier segments
        p1 = Point(0, 0)
        p2 = Point(4, 0)
        p3 = Point(2, 3)
        
        segment1 = BezierSegment([p1, p2], degree=1)
        segment2 = BezierSegment([p2, p3], degree=1)
        segment3 = BezierSegment([p3, p1], degree=1)
        
        triangle = BoundaryCurve(
            bezier_segments=[segment1, segment2, segment3],
            corners=[p1, p2, p3],
            color=Color.BLACK,
            is_closed=True
        )
        
        # Test point inside triangle
        point_inside = Point(2, 1)
        point_outside = Point(2, -1)
        
        assert BoundaryCurveGrouper.is_point_inside_boundary(point_inside, triangle)
        assert not BoundaryCurveGrouper.is_point_inside_boundary(point_outside, triangle)
        
        # Test bounding box
        min_x, max_x, min_y, max_y = BoundaryCurveGrouper.get_curve_bounding_box(triangle)
        assert math.isclose(min_x, 0.0)
        assert math.isclose(max_x, 4.0)
        assert math.isclose(min_y, 0.0)
        assert math.isclose(max_y, 3.0)
        
        # Test grouping (just this one curve)
        result = BoundaryCurveGrouper.group_boundary_curves([triangle])
        assert len(result) == 1
        assert result[0]["holes"] == []
        assert len(result[0]["physical_groups"]) == 2  # DOMAIN_VA + BOUNDARY_OUT
