import pytest
from unittest.mock import patch, MagicMock, PropertyMock
import math

from svg_to_getdp.core.entities.point import Point
from svg_to_getdp.core.entities.color import Color
from svg_to_getdp.core.entities.bezier_segment import BezierSegment
from sketchgetdp.svg_to_getdp.core.entities.outline import Outline
from svg_to_getdp.core.entities.physical_group import (
    DOMAIN_VA, 
    DOMAIN_VI_IRON, 
    DOMAIN_VI_AIR, 
    BOUNDARY_GAMMA, 
    BOUNDARY_OUT
)
from sketchgetdp.svg_to_getdp.infrastructure.outline_grouper import OutlineGrouper


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
def create_square_outline():
    """Create a simple square outline."""
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
        
        return Outline(
            bezier_segments=segments,
            corners=corners,
            color=color,
            is_closed=closed
        )
    return _create


@pytest.fixture
def sample_outlines(create_square_outline):
    """Create a set of sample outlines for testing."""
    # Outer green square (Vi air domain)
    outer = create_square_outline(center_x=0.0, center_y=0.0, size=10.0, color=Color.GREEN)
    
    # Inner blue square (Vi iron domain)
    inner1 = create_square_outline(center_x=0.0, center_y=0.0, size=6.0, color=Color.BLUE)
    
    # Even inner green square (Vi air domain)
    inner2 = create_square_outline(center_x=0.0, center_y=0.0, size=3.0, color=Color.GREEN)
    
    # Black square inside the green one
    inner3 = create_square_outline(center_x=0.0, center_y=0.0, size=1.0, color=Color.BLACK)

    return [outer, inner1, inner2, inner3]


# ============================================================================
# Test Cases for OutlineGrouper
# ============================================================================

class TestOutlineGrouper:
    """Test suite for OutlineGrouper class."""
    
    def test_should_return_true_when_point_is_inside_closed_square_outline(self, create_square_outline):
        """Test point inside/outside detection for square outline."""
        outline = create_square_outline(center_x=0.0, center_y=0.0, size=4.0)
        
        # Points inside
        assert OutlineGrouper.is_point_inside_outline(Point(0.0, 0.0), outline)
        assert OutlineGrouper.is_point_inside_outline(Point(0.5, 0.5), outline)
        assert OutlineGrouper.is_point_inside_outline(Point(-0.5, -0.5), outline)
        
        # Points outside
        assert not OutlineGrouper.is_point_inside_outline(Point(2.0, 2.0), outline)
        assert not OutlineGrouper.is_point_inside_outline(Point(-2.0, -2.0), outline)
        assert not OutlineGrouper.is_point_inside_outline(Point(0.0, 2.0), outline)  # on edge

    def test_should_return_false_when_point_is_inside_open_outline(self, create_square_outline):
        """Test that open outlines always return False."""
        open_outline = create_square_outline(center_x=0.0, center_y=0.0, size=4.0, closed=False)

        # Even points that would be inside a closed outline should return False
        assert not OutlineGrouper.is_point_inside_outline(Point(0.0, 0.0), open_outline)

    def test_should_raise_value_error_when_getting_bounding_box_for_empty_outline(self):
        """Test bounding box with empty outline."""
        mock_outline = MagicMock()
        type(mock_outline).control_points = PropertyMock(return_value=[])
        
        with pytest.raises(ValueError, match="must have at least one control point"):
            OutlineGrouper.get_outline_bounding_box(mock_outline)
    
    def test_should_detect_when_one_outline_is_inside_another(self, create_square_outline):
        """Test outline containment detection."""
        outer = create_square_outline(center_x=0.0, center_y=0.0, size=10.0)
        inner = create_square_outline(center_x=0.0, center_y=0.0, size=5.0)
        separate = create_square_outline(center_x=20.0, center_y=20.0, size=5.0)
        
        # Inner is inside outer
        assert OutlineGrouper.is_outline_inside_other(inner, outer)
        
        # Outer is not inside inner
        assert not OutlineGrouper.is_outline_inside_other(outer, inner)

        # Separate is not inside outer
        assert not OutlineGrouper.is_outline_inside_other(separate, outer)
    
    def test_should_correctly_identify_containment_hierarchy_for_nested_squares(self, create_square_outline):
        """Test containment hierarchy detection."""
        # Create nested squares
        outlines = [
            create_square_outline(center_x=0.0, center_y=0.0, size=10.0, color=Color.BLACK),    # 0
            create_square_outline(center_x=0.0, center_y=0.0, size=6.0, color=Color.BLUE),      # 1
            create_square_outline(center_x=0.0, center_y=0.0, size=3.0, color=Color.GREEN),     # 2
            create_square_outline(center_x=0.0, center_y=0.0, size=1.0, color=Color.BLACK),     # 3
            create_square_outline(center_x=20.0, center_y=20.0, size=5.0, color=Color.BLACK),   # 4
        ]

        hierarchy = OutlineGrouper.get_containment_hierarchy(outlines)

        # Expected hierarchy (only immediate children):
        # Outline 0 contains 1 (outline 1 is inside outline 0)
        # Outline 1 contains 2 (outline 2 is inside outline 1)
        # Outline 2 contains 3 (outline 3 is inside outline 2)

        assert hierarchy[0] == [1]
        assert hierarchy[1] == [2]
        assert hierarchy[2] == [3]
        assert hierarchy[3] == []

    def test_should_classify_outline_colors_correctly(self, create_square_outline):
        """Test outline color classification."""
        black_outline = create_square_outline(color=Color.BLACK)
        blue_outline = create_square_outline(color=Color.BLUE)
        green_outline = create_square_outline(color=Color.GREEN)

        assert OutlineGrouper.classify_outline_color(black_outline) == "va"
        assert OutlineGrouper.classify_outline_color(blue_outline) == "vi_iron"
        assert OutlineGrouper.classify_outline_color(green_outline) == "vi_air"

    def test_should_raise_value_error_when_classifying_outline_with_invalid_color(self):
        """Test outline color classification with invalid color."""
        red_outline = Outline(
            bezier_segments=[BezierSegment([Point(0,0), Point(1,0)], degree=1)],
            corners=[Point(0,0), Point(1,0)],
            color=Color.RED,
            is_closed=True
        )
        
        with pytest.raises(ValueError, match="Unknown outline color"):
            OutlineGrouper.classify_outline_color(red_outline)

    def test_should_assign_correct_physical_groups_based_on_outline_classification(self, create_square_outline):
        """Test physical group assignment for outlines."""
        # Test Va outline
        groups = OutlineGrouper.get_physical_groups_for_outline(
            classification="va",
            is_outermost=False,
            is_va_in_vi=False
        )
        assert len(groups) == 1
        assert groups[0] == DOMAIN_VA

        # Test Va outline inside Vi (should get BOUNDARY_GAMMA too)
        groups = OutlineGrouper.get_physical_groups_for_outline(
            classification="va",
            is_outermost=False,
            is_va_in_vi=True
        )
        assert len(groups) == 2
        assert BOUNDARY_GAMMA in groups
        assert DOMAIN_VA in groups

        # Test outermost outline (should get BOUNDARY_OUT)
        groups = OutlineGrouper.get_physical_groups_for_outline(
            classification="va",
            is_outermost=True,
            is_va_in_vi=False
        )
        assert len(groups) == 2
        assert DOMAIN_VA in groups
        assert BOUNDARY_OUT in groups

    def test_should_group_single_outline_as_outermost(self, create_square_outline):
        """Test basic grouping of outlines."""
        # Simple case: one outer Va outline
        outlines = [create_square_outline(color=Color.BLACK)]

        result = OutlineGrouper.group_outlines(outlines)
        
        assert len(result) == 1
        assert result[0]["holes"] == []
        assert len(result[0]["physical_groups"]) == 2  # DOMAIN_VA + BOUNDARY_OUT
        assert DOMAIN_VA in result[0]["physical_groups"]
        assert BOUNDARY_OUT in result[0]["physical_groups"]
    
    def test_should_correctly_group_nested_outlines_with_varying_colors(self, sample_outlines):
        """Test grouping of nested outlines."""
        result = OutlineGrouper.group_outlines(sample_outlines)
        
        assert len(result) == 4
        
        # Check outline 0 (outermost green - Vi air)
        assert result[0]["holes"] == [1]  # Contains only the immediate child (inner1 - blue)
        assert DOMAIN_VI_AIR in result[0]["physical_groups"]
        assert BOUNDARY_OUT in result[0]["physical_groups"]
        
        # Check outline 1 (blue inner1 - Vi iron)
        assert result[1]["holes"] == [2]  # Contains only the immediate child (inner2 - green)
        assert DOMAIN_VI_IRON in result[1]["physical_groups"]
        
        # Check outline 2 (green inner2 - Vi air)
        assert result[2]["holes"] == [3]  # Contains only the immediate child (inner3 - black)
        assert DOMAIN_VI_AIR in result[2]["physical_groups"]
        
        # Check outline 3 (innermost black - Va)
        assert result[3]["holes"] == []  # Contains nothing
        assert DOMAIN_VA in result[3]["physical_groups"]
        assert BOUNDARY_GAMMA in result[3]["physical_groups"]  # Inside Vi
    
    def test_should_return_empty_list_when_grouping_empty_outlines(self):
        """Test grouping with empty input."""
        result = OutlineGrouper.group_outlines([])
        assert result == []
    
    @patch('sketchgetdp.svg_to_getdp.infrastructure.outline_grouper.OutlineGrouper.classify_outline_color')
    @patch('sketchgetdp.svg_to_getdp.infrastructure.outline_grouper.OutlineGrouper.is_outline_inside_other')
    def test_should_detect_va_outlines_inside_vi_outlines_and_assign_boundary_gamma(
        self, mock_is_inside, mock_classify, create_square_outline
    ):
        """Test detection of Va outlines inside Vi outlines."""
        # Setup mock to simulate Va inside Vi
        def side_effect(outline, other):
            # Simple mock: return True if outline is black and other is blue or green
            if outline.color == Color.BLACK and other.color in [Color.BLUE, Color.GREEN]:
                return True
            return False
        
        mock_is_inside.side_effect = side_effect
        
        # Mock color classification
        def classify_side_effect(outline):
            if outline.color == Color.BLACK:
                return "va"
            elif outline.color == Color.BLUE:
                return "vi_iron"
            return "va"  # default
        
        mock_classify.side_effect = classify_side_effect
        
        # Create outlines
        vi_outline = create_square_outline(color=Color.BLUE)
        va_outline = create_square_outline(color=Color.BLACK)
        outlines = [vi_outline, va_outline]
        
        # Mock the containment hierarchy to show Va is inside Vi
        with patch('sketchgetdp.svg_to_getdp.infrastructure.outline_grouper.OutlineGrouper.get_containment_hierarchy') as mock_hierarchy:
            mock_hierarchy.return_value = {0: [1], 1: []}  # Vi contains Va
            
            result = OutlineGrouper.group_outlines(outlines)
            
            # Check that Va outline got BOUNDARY_GAMMA
            assert BOUNDARY_GAMMA in result[1]["physical_groups"]
    
    def test_should_raise_error_when_no_outermost_candidate_can_be_determined(self, create_square_outline):
        """Test error when no outermost candidate is found."""
        # Create a circular dependency scenario
        outline1 = create_square_outline(color=Color.BLACK)
        outline2 = create_square_outline(color=Color.BLUE)
        
        # Mock containment hierarchy to create circular reference
        # Use the correct module path based on import
        with patch('sketchgetdp.svg_to_getdp.infrastructure.outline_grouper.OutlineGrouper.get_containment_hierarchy') as mock_hierarchy:
            mock_hierarchy.return_value = {0: [1], 1: [0]}  # Each contains the other
            
            with pytest.raises(ValueError, match="No outermost candidates found"):
                OutlineGrouper.group_outlines([outline1, outline2])


# ============================================================================
# Integration Tests
# ============================================================================

class TestOutlineGrouperIntegration:
    """Integration tests for OutlineGrouper with real outline data."""

    def test_should_process_triangle_outline_and_correctly_determine_containment(self):
        """Test complete workflow with actual Bézier segments."""
        # Create a simple triangle using linear Bézier segments
        p1 = Point(0, 0)
        p2 = Point(4, 0)
        p3 = Point(2, 3)
        
        segment1 = BezierSegment([p1, p2], degree=1)
        segment2 = BezierSegment([p2, p3], degree=1)
        segment3 = BezierSegment([p3, p1], degree=1)
        
        triangle = Outline(
            bezier_segments=[segment1, segment2, segment3],
            corners=[p1, p2, p3],
            color=Color.BLACK,
            is_closed=True
        )
        
        # Test point inside triangle
        point_inside = Point(2, 1)
        point_outside = Point(2, -1)
        
        assert OutlineGrouper.is_point_inside_outline(point_inside, triangle)
        assert not OutlineGrouper.is_point_inside_outline(point_outside, triangle)
        
        # Test bounding box
        min_x, max_x, min_y, max_y = OutlineGrouper.get_outline_bounding_box(triangle)
        assert math.isclose(min_x, 0.0)
        assert math.isclose(max_x, 4.0)
        assert math.isclose(min_y, 0.0)
        assert math.isclose(max_y, 3.0)
        
        # Test grouping (just this one outline)
        result = OutlineGrouper.group_outlines([triangle])
        assert len(result) == 1
        assert result[0]["holes"] == []
        assert len(result[0]["physical_groups"]) == 2  # DOMAIN_VA + BOUNDARY_OUT
