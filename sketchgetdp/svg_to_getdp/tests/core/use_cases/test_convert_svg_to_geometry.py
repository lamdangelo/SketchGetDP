"""
Unit tests for ConvertSVGToGeometry use case.

Tests the conversion of SVG files to geometric outlines and wires,
including handling of different colors, corner detection, and Bézier fitting.
"""

import pytest
from unittest.mock import Mock

from svg_to_getdp.core.entities.point import Point
from svg_to_getdp.core.entities.bezier_segment import BezierSegment
from sketchgetdp.svg_to_getdp.core.entities.outline import Outline
from svg_to_getdp.core.entities.color import Color

from svg_to_getdp.interfaces.abstractions.svg_parser_interface import SVGParserInterface
from svg_to_getdp.interfaces.abstractions.corner_detector_interface import CornerDetectorInterface
from svg_to_getdp.interfaces.abstractions.bezier_fitter_interface import BezierFitterInterface

from svg_to_getdp.core.use_cases.convert_svg_to_geometry import ConvertSVGToGeometry


class TestConvertSVGToGeometry:
    """Test suite for ConvertSVGToGeometry class."""

    # ==================== Fixtures ====================

    @pytest.fixture
    def svg_parser(self):
        """Create a mock SVG parser."""
        return Mock(spec=SVGParserInterface)
    
    @pytest.fixture
    def corner_detector(self):
        """Create a mock corner detector."""
        return Mock(spec=CornerDetectorInterface)
    
    @pytest.fixture
    def bezier_fitter(self):
        """Create a mock Bézier fitter."""
        return Mock(spec=BezierFitterInterface)
    
    @pytest.fixture
    def converter(self, svg_parser, corner_detector, bezier_fitter):
        """Create a converter instance for testing."""
        return ConvertSVGToGeometry(svg_parser, corner_detector, bezier_fitter)
    
    @pytest.fixture
    def triangle_points(self):
        """Create sample points for a triangle shape."""
        return [
            Point(0.0, 0.0), Point(0.5, 0.0), Point(1.0, 0.0),
            Point(0.9, 0.1), Point(0.8, 0.2), Point(0.7, 0.3),
            Point(0.5, 1.0), Point(0.3, 0.7), Point(0.2, 0.5),
            Point(0.1, 0.3), Point(0.0, 0.1), Point(0.0, 0.0)
        ]
    
    @pytest.fixture
    def square_points(self):
        """Create sample points for a square shape."""
        return [
            Point(0.2, 0.2), Point(0.8, 0.2), Point(0.8, 0.8),
            Point(0.2, 0.8), Point(0.2, 0.2)
        ]
    
    @pytest.fixture
    def mock_raw_outline_class(self):
        """Create a mock RawOutline class for testing."""
        class RawOutline:
            def __init__(self, points, is_closed):
                self.points = points
                self.is_closed = is_closed
        return RawOutline
    
    @pytest.fixture
    def mock_bezier_segment(self):
        """Create a mock Bézier segment for testing."""
        segment = Mock(spec=BezierSegment)
        segment.control_points = [Point(0.0, 0.0), Point(0.3, 0.1), Point(0.5, 0.2)]
        return segment

    # ==================== Initialization Tests ====================

    def test_initialization(self, svg_parser, corner_detector, bezier_fitter):
        """Test that the use case initializes correctly with dependencies."""
        converter = ConvertSVGToGeometry(svg_parser, corner_detector, bezier_fitter)
        
        assert converter.svg_parser == svg_parser
        assert converter.corner_detector == corner_detector
        assert converter.bezier_fitter == bezier_fitter

    # ==================== Color Differentiation Tests ====================

    def test_red_single_point_wire(self, converter, svg_parser, mock_raw_outline_class):
        """Test RED elements with single point become wires."""
        test_svg_path = "test_red_single.svg"
        
        single_point = [Point(0.5, 0.5)]
        mock_raw_outline = mock_raw_outline_class(
            points=single_point,
            is_closed=True
        )
        
        svg_parser.extract_raw_outlines_by_color.return_value = {
            Color.RED: [mock_raw_outline]
        }
        
        result = converter.execute(test_svg_path)
        outlines, wires, colored_outlines, corner_debug_data = result

        assert len(outlines) == 0
        assert len(wires) == 1
        assert wires[0][1] == Color.RED
        assert wires[0][0] == single_point[0]

    def test_red_multiple_points_wire(self, converter, svg_parser, mock_raw_outline_class):
        """Test RED elements with multiple points become wires using first point."""
        test_svg_path = "test_red_multiple.svg"
        
        multiple_points = [Point(0.5, 0.5), Point(0.6, 0.6), Point(0.7, 0.7)]
        mock_raw_outline = mock_raw_outline_class(
            points=multiple_points,
            is_closed=True
        )
        
        svg_parser.extract_raw_outlines_by_color.return_value = {
            Color.RED: [mock_raw_outline]
        }
        
        result = converter.execute(test_svg_path)
        outlines, wires, colored_outlines, corner_debug_data = result

        assert len(outlines) == 0
        assert len(wires) == 1
        assert wires[0][1] == Color.RED
        assert wires[0][0] == multiple_points[0]  # First point used for wire

    def test_green_outline_processing(self, converter, svg_parser, corner_detector, 
                                     bezier_fitter, triangle_points, mock_raw_outline_class):
        """Test GREEN elements become outlines with Bézier fitting."""
        test_svg_path = "test_green.svg"
        
        mock_raw_outline = mock_raw_outline_class(
            points=triangle_points,
            is_closed=True
        )

        svg_parser.extract_raw_outlines_by_color.return_value = {
            Color.GREEN: [mock_raw_outline]
        }
        
        mock_corner_indices = [0, 3, 6]
        mock_debug_data = {'some': 'debug'}
        corner_detector.detect_corners.return_value = (mock_corner_indices, mock_debug_data)
        
        mock_outline = Mock(spec=Outline)
        mock_outline.color = Color.GREEN
        mock_outline.is_closed = True
        mock_outline.bezier_segments = []
        mock_outline.corners = mock_corner_indices
        
        bezier_fitter.fit_outline.return_value = mock_outline
        
        result = converter.execute(test_svg_path)
        outlines, wires, colored_outlines, corner_debug_data = result
        
        assert len(outlines) == 1
        assert len(wires) == 0
        assert outlines[0].color == Color.GREEN
        
        # Debug data key uses lowercase color name
        assert 'green_raw_outline_0' in corner_debug_data
        debug_data = corner_debug_data['green_raw_outline_0']
        assert debug_data['color'] == 'green'  # lowercase
        assert debug_data['corner_indices'] == mock_corner_indices

    def test_blue_outline_processing(self, converter, svg_parser, corner_detector,
                                    bezier_fitter, square_points, mock_raw_outline_class):
        """Test BLUE elements become outlines with Bézier fitting."""
        test_svg_path = "test_blue.svg"
        
        mock_raw_outline = mock_raw_outline_class(
            points=square_points,
            is_closed=True
        )

        svg_parser.extract_raw_outlines_by_color.return_value = {
            Color.BLUE: [mock_raw_outline]
        }
        
        mock_corner_indices = [0, 1, 2, 3]
        mock_debug_data = {'some': 'debug'}
        corner_detector.detect_corners.return_value = (mock_corner_indices, mock_debug_data)
        
        mock_outline = Mock(spec=Outline)
        mock_outline.color = Color.BLUE
        mock_outline.is_closed = True
        mock_outline.bezier_segments = []
        mock_outline.corners = mock_corner_indices
        
        bezier_fitter.fit_outline.return_value = mock_outline
        
        result = converter.execute(test_svg_path)
        outlines, wires, colored_outlines, corner_debug_data = result
        
        assert len(outlines) == 1
        assert len(wires) == 0
        assert outlines[0].color == Color.BLUE
        
        # Debug data key uses lowercase color name
        assert 'blue_raw_outline_0' in corner_debug_data
        debug_data = corner_debug_data['blue_raw_outline_0']
        assert debug_data['color'] == 'blue'  # lowercase
        assert debug_data['corner_indices'] == mock_corner_indices

    def test_black_outline_processing(self, converter, svg_parser, corner_detector,
                                     bezier_fitter, triangle_points, mock_raw_outline_class):
        """Test BLACK elements become outlines with Bézier fitting."""
        test_svg_path = "test_black.svg"
        
        mock_raw_outline = mock_raw_outline_class(
            points=triangle_points,
            is_closed=True
        )

        svg_parser.extract_raw_outlines_by_color.return_value = {
            Color.BLACK: [mock_raw_outline]
        }
        
        mock_corner_indices = [0, 3, 6]
        mock_debug_data = {'some': 'debug'}
        corner_detector.detect_corners.return_value = (mock_corner_indices, mock_debug_data)
        
        mock_outline = Mock(spec=Outline)
        mock_outline.color = Color.BLACK
        mock_outline.is_closed = True
        mock_outline.bezier_segments = []
        mock_outline.corners = mock_corner_indices
        
        bezier_fitter.fit_outline.return_value = mock_outline
        
        result = converter.execute(test_svg_path)
        outlines, wires, colored_outlines, corner_debug_data = result
        
        assert len(outlines) == 1
        assert len(wires) == 0
        assert outlines[0].color == Color.BLACK
        
        # Debug data key uses lowercase color name
        assert 'black_raw_outline_0' in corner_debug_data
        debug_data = corner_debug_data['black_raw_outline_0']
        assert debug_data['color'] == 'black'  # lowercase
        assert debug_data['corner_indices'] == mock_corner_indices

    def test_mixed_colors_processing(self, converter, svg_parser, corner_detector,
                                    bezier_fitter, triangle_points, square_points, 
                                    mock_raw_outline_class):
        """Test processing of SVG with mixed colors."""
        test_svg_path = "test_mixed.svg"
        
        # Create outlines for different colors
        mock_green_outline = mock_raw_outline_class(
            points=triangle_points,
            is_closed=True
        )
        mock_blue_outline = mock_raw_outline_class(
            points=square_points,
            is_closed=True
        )
        mock_black_outline = mock_raw_outline_class(
            points=triangle_points,
            is_closed=False  # Open curve
        )
        mock_red_wire = mock_raw_outline_class(
            points=[Point(0.5, 0.5)],
            is_closed=True
        )
        mock_red_outline = mock_raw_outline_class(
            points=[Point(0.2, 0.2), Point(0.8, 0.2), Point(0.5, 0.8)],  # Multiple points
            is_closed=True
        )
        
        svg_parser.extract_raw_outlines_by_color.return_value = {
            Color.GREEN: [mock_green_outline],
            Color.BLUE: [mock_blue_outline],
            Color.BLACK: [mock_black_outline],
            Color.RED: [mock_red_wire, mock_red_outline]  # Multiple RED elements
        }
        
        # Setup corner detection responses
        corners_green = ([0, 3, 6], {'debug': 'green'})
        corners_blue = ([0, 1, 2, 3], {'debug': 'blue'})
        corners_black = ([], {'debug': 'black'})
        corner_detector.detect_corners.side_effect = [corners_green, corners_blue, corners_black]
        
        # Setup Bézier fitting responses
        mock_green_result = Mock(spec=Outline)
        mock_green_result.color = Color.GREEN
        mock_green_result.is_closed = True
        mock_green_result.bezier_segments = []
        mock_green_result.corners = corners_green[0]
        
        mock_blue_result = Mock(spec=Outline)
        mock_blue_result.color = Color.BLUE
        mock_blue_result.is_closed = True
        mock_blue_result.bezier_segments = []
        mock_blue_result.corners = corners_blue[0]
        
        mock_black_result = Mock(spec=Outline)
        mock_black_result.color = Color.BLACK
        mock_black_result.is_closed = False
        mock_black_result.bezier_segments = []
        mock_black_result.corners = corners_black[0]
        
        bezier_fitter.fit_outline.side_effect = [mock_green_result, mock_blue_result, mock_black_result]
        
        result = converter.execute(test_svg_path)
        outlines, wires, colored_outlines, corner_debug_data = result
        
        # Verify results
        assert len(outlines) == 3  # GREEN, BLUE, BLACK
        assert len(wires) == 2  # Two RED elements
        
        # Verify wires (RED elements)
        assert wires[0][1] == Color.RED  # Single point wire
        assert wires[0][0] == Point(0.5, 0.5)
        
        assert wires[1][1] == Color.RED  # Multi-point wire (uses first point)
        assert wires[1][0] == Point(0.2, 0.2)
        
        # Verify debug data keys (all lowercase)
        assert 'green_raw_outline_0' in corner_debug_data
        assert 'blue_raw_outline_0' in corner_debug_data
        assert 'black_raw_outline_0' in corner_debug_data
        
        # Corner detector should be called for GREEN, BLUE, BLACK but not RED
        assert corner_detector.detect_corners.call_count == 3
        
        # Bézier fitter should be called for GREEN, BLUE, BLACK but not RED
        assert bezier_fitter.fit_outline.call_count == 3

    # ==================== Edge Case Tests ====================

    def test_empty_svg(self, converter, svg_parser):
        """Test converting an empty SVG."""
        test_svg_path = "test_empty.svg"
        svg_parser.extract_raw_outlines_by_color.return_value = {}
        
        result = converter.execute(test_svg_path)
        outlines, wires, colored_outlines, corner_debug_data = result
        
        assert len(outlines) == 0
        assert len(wires) == 0
        svg_parser.extract_raw_outlines_by_color.assert_called_once_with(test_svg_path)

    def test_invalid_svg_path(self, converter, svg_parser):
        """Test handling of invalid SVG file path."""
        test_svg_path = "nonexistent.svg"
        svg_parser.extract_raw_outlines_by_color.side_effect = ValueError("SVG file not found")
        
        with pytest.raises(ValueError, match="SVG file not found"):
            converter.execute(test_svg_path)
        
        svg_parser.extract_raw_outlines_by_color.assert_called_once_with(test_svg_path)

    # ==================== Open Curve Tests ====================

    def test_open_curves(self, converter, svg_parser, corner_detector,
                        bezier_fitter, mock_raw_outline_class):
        """Test converting SVG with open curves."""
        test_svg_path = "test_open.svg"
        
        mock_points = [
            Point(0.0, 0.0), Point(0.3, 0.4), Point(0.7, 0.3), Point(1.0, 0.0)
        ]
        
        mock_raw_outline = mock_raw_outline_class(
            points=mock_points,
            is_closed=False
        )
        
        svg_parser.extract_raw_outlines_by_color.return_value = {Color.GREEN: [mock_raw_outline]}
        corner_detector.detect_corners.return_value = ([], {})
        
        mock_bezier_segment = Mock(spec=BezierSegment)
        mock_bezier_segment.control_points = [Point(0.0, 0.0), Point(0.3, 0.1), Point(0.5, 0.2)]
        
        mock_outline = Mock(spec=Outline)
        mock_outline.color = Color.GREEN
        mock_outline.is_closed = False
        mock_outline.bezier_segments = [mock_bezier_segment, mock_bezier_segment]
        mock_outline.corners = []
        
        bezier_fitter.fit_outline.return_value = mock_outline
        
        result = converter.execute(test_svg_path)
        outlines, wires, colored_outlines, corner_debug_data = result
        
        bezier_fitter.fit_outline.assert_called_once()
        
        assert len(outlines) == 1
        assert not outlines[0].is_closed

    # ==================== Error Handling Tests ====================

    def test_error_handling_in_corner_detection(self, converter, svg_parser, corner_detector,
                                               bezier_fitter, triangle_points, mock_raw_outline_class):
        """Test error handling when corner detection fails."""
        test_svg_path = "test_error.svg"

        mock_raw_outline = mock_raw_outline_class(
            points=triangle_points,
            is_closed=True
        )

        svg_parser.extract_raw_outlines_by_color.return_value = {Color.GREEN: [mock_raw_outline]}
        corner_detector.detect_corners.side_effect = ValueError("Corner detection failed")
        
        with pytest.raises(ValueError, match="Corner detection failed"):
            converter.execute(test_svg_path)
    
    def test_error_handling_in_bezier_fitting(self, converter, svg_parser, corner_detector,
                                             bezier_fitter, triangle_points, mock_raw_outline_class):
        """Test error handling when Bézier fitting fails."""
        test_svg_path = "test_error.svg"
        
        mock_raw_outline = mock_raw_outline_class(
            points=triangle_points,
            is_closed=True
        )

        svg_parser.extract_raw_outlines_by_color.return_value = {Color.GREEN: [mock_raw_outline]}
        corner_detector.detect_corners.return_value = ([], {})
        bezier_fitter.fit_outline.side_effect = ValueError("Bézier fitting failed")

        with pytest.raises(ValueError, match="Bézier fitting failed"):
            converter.execute(test_svg_path)

    # ==================== Internal Method Tests ====================

    def test_ensure_proper_closure_open_curve(self, converter):
        """Test the _ensure_proper_closure method with open curve."""
        points_open = [Point(0, 0), Point(1, 0), Point(1, 1)]
        result_open = converter._ensure_proper_closure(points_open, False)
        assert result_open == points_open
        assert len(result_open) == 3
    
    def test_ensure_proper_closure_closed_curve_with_gap(self, converter):
        """Test the _ensure_proper_closure method with closed curve with gap."""
        points_closed_gap = [Point(0, 0), Point(1, 0), Point(1, 1), Point(0, 1)]
        result_closed_gap = converter._ensure_proper_closure(points_closed_gap, True)
        assert len(result_closed_gap) == 5
        assert result_closed_gap[-1] == points_closed_gap[0]
    
    def test_ensure_proper_closure_already_closed(self, converter):
        """Test the _ensure_proper_closure method with already closed curve."""
        points_already_closed = [Point(0, 0), Point(1, 0), Point(1, 1), Point(0, 1), Point(0, 0)]
        result_already_closed = converter._ensure_proper_closure(points_already_closed, True)
        assert result_already_closed == points_already_closed
    
    def test_ensure_proper_closure_too_few_points(self, converter):
        """Test the _ensure_proper_closure method with too few points."""
        points_few = [Point(0, 0), Point(1, 0)]
        result_few = converter._ensure_proper_closure(points_few, True)
        assert result_few == points_few
    
    def test_force_outline_closure(self, converter):
        """Test the _force_outline_closure method."""
        mock_segment1 = Mock()
        mock_segment1.control_points = [Point(0, 0), Point(0.5, 0)]
        
        mock_segment2 = Mock()
        mock_segment2.control_points = [Point(0.5, 0), Point(1, 1)]
        
        mock_outline = Mock(spec=Outline)
        mock_outline.bezier_segments = [mock_segment1, mock_segment2]
        
        converter._force_outline_closure(mock_outline)
        
        assert mock_segment2.control_points[-1] == mock_segment1.control_points[0]
