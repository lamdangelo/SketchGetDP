"""
Unit tests for ConvertSVGToGeometry use case.

Tests the conversion of SVG files to geometric boundary curves and wires,
including handling of different colors, corner detection, and Bézier fitting.
"""

import pytest
from unittest.mock import Mock

from svg_to_getdp.core.entities.point import Point
from svg_to_getdp.core.entities.bezier_segment import BezierSegment
from svg_to_getdp.core.entities.boundary_curve import BoundaryCurve
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
    def mock_raw_boundary_class(self):
        """Create a mock RawBoundary class for testing."""
        class RawBoundary:
            def __init__(self, points, color, is_closed):
                self.points = points
                self.color = color
                self.is_closed = is_closed
        return RawBoundary
    
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

    # ==================== Basic Conversion Tests ====================

    def test_convert_simple_svg(self, converter, svg_parser, corner_detector, 
                               bezier_fitter, triangle_points, mock_raw_boundary_class):
        """Test converting a simple SVG with one RED curve (should become a wire)."""
        test_svg_path = "test_simple.svg"
        
        mock_raw_boundary = mock_raw_boundary_class(
            points=triangle_points,
            color=Color.RED,
            is_closed=True
        )
        
        svg_parser.extract_boundaries_by_color.return_value = {Color.RED: [mock_raw_boundary]}
        
        result = converter.execute(test_svg_path)
        boundary_curves, wires, colored_boundaries, corner_debug_data = result
        
        svg_parser.extract_boundaries_by_color.assert_called_once_with(test_svg_path)
        
        # RED elements should be converted to wires, not boundary curves
        assert len(boundary_curves) == 0
        assert len(wires) == 1
        
        wire_point, wire_color = wires[0]
        assert wire_color == Color.RED
        
        # Corner detector and Bézier fitter should NOT be called for RED elements
        corner_detector.detect_corners.assert_not_called()
        bezier_fitter.fit_boundary_curve.assert_not_called()
    
    def test_convert_svg_with_corners(self, converter, svg_parser, corner_detector, 
                                     bezier_fitter, triangle_points, mock_raw_boundary_class):
        """Test converting an SVG with corners (GREEN color)."""
        test_svg_path = "test_triangle.svg"
        
        mock_raw_boundary = mock_raw_boundary_class(
            points=triangle_points,
            color=Color.GREEN,
            is_closed=True
        )
        
        svg_parser.extract_boundaries_by_color.return_value = {Color.GREEN: [mock_raw_boundary]}
        
        mock_corner_indices = [0, 3, 6]
        mock_debug_data = {'some': 'debug'}
        corner_detector.detect_corners.return_value = (mock_corner_indices, mock_debug_data)
        
        mock_bezier_segment1 = Mock(spec=BezierSegment)
        mock_bezier_segment1.control_points = [Point(0.0, 0.0), Point(0.3, 0.1), Point(0.5, 0.2)]
        
        mock_bezier_segment2 = Mock(spec=BezierSegment)
        mock_bezier_segment2.control_points = [Point(0.5, 0.2), Point(0.7, 0.1), Point(1.0, 0.0)]
        
        mock_boundary_curve = Mock(spec=BoundaryCurve)
        mock_boundary_curve.color = Color.GREEN
        mock_boundary_curve.is_closed = True
        mock_boundary_curve.bezier_segments = [mock_bezier_segment1, mock_bezier_segment2]
        mock_boundary_curve.corners = mock_corner_indices
        
        bezier_fitter.fit_boundary_curve.return_value = mock_boundary_curve
        
        result = converter.execute(test_svg_path)
        boundary_curves, wires, colored_boundaries, corner_debug_data = result
        
        corner_detector.detect_corners.assert_called_once()
        bezier_fitter.fit_boundary_curve.assert_called_once()
        
        assert len(boundary_curves) == 1
        assert boundary_curves[0].color == Color.GREEN
        
        assert 'green_boundary_0' in corner_debug_data
        assert corner_debug_data['green_boundary_0']['color'] == 'green'
        assert corner_debug_data['green_boundary_0']['corner_indices'] == mock_corner_indices
    
    def test_convert_multiple_curves(self, converter, svg_parser, corner_detector, 
                                    bezier_fitter, triangle_points, square_points, 
                                    mock_raw_boundary_class, mock_bezier_segment):
        """Test converting SVG with multiple colored curves."""
        test_svg_path = "test_multiple.svg"
        
        mock_raw_boundary1 = mock_raw_boundary_class(
            points=triangle_points, 
            color=Color.GREEN, 
            is_closed=True
        )
        mock_raw_boundary2 = mock_raw_boundary_class(
            points=square_points, 
            color=Color.BLUE, 
            is_closed=True
        )
        
        mock_red_points = [Point(0.5, 0.5)]
        mock_raw_boundary_red = mock_raw_boundary_class(
            points=mock_red_points, 
            color=Color.RED, 
            is_closed=True
        )
        
        svg_parser.extract_boundaries_by_color.return_value = {
            Color.GREEN: [mock_raw_boundary1],
            Color.BLUE: [mock_raw_boundary2],
            Color.RED: [mock_raw_boundary_red]
        }
        
        corners1 = ([0, 3, 6], {'debug': 'data1'})
        corners2 = ([0, 1, 2, 3], {'debug': 'data2'})
        corner_detector.detect_corners.side_effect = [corners1, corners2]
        
        mock_boundary_curve1 = Mock(spec=BoundaryCurve)
        mock_boundary_curve1.color = Color.GREEN
        mock_boundary_curve1.is_closed = True
        mock_boundary_curve1.bezier_segments = [mock_bezier_segment, mock_bezier_segment]
        mock_boundary_curve1.corners = corners1[0]
        
        mock_boundary_curve2 = Mock(spec=BoundaryCurve)
        mock_boundary_curve2.color = Color.BLUE
        mock_boundary_curve2.is_closed = True
        mock_boundary_curve2.bezier_segments = [mock_bezier_segment, mock_bezier_segment]
        mock_boundary_curve2.corners = corners2[0]
        
        bezier_fitter.fit_boundary_curve.side_effect = [mock_boundary_curve1, mock_boundary_curve2]
        
        result = converter.execute(test_svg_path)
        boundary_curves, wires, colored_boundaries, corner_debug_data = result
        
        assert len(boundary_curves) == 2
        assert len(wires) == 1
        
        assert boundary_curves[0].color == Color.GREEN
        assert boundary_curves[0].corners == corners1[0]
        
        assert boundary_curves[1].color == Color.BLUE
        assert boundary_curves[1].corners == corners2[0]
        
        assert wires[0][1] == Color.RED
        assert wires[0][0] == mock_red_points[0]
        
        assert corner_detector.detect_corners.call_count == 2
        assert bezier_fitter.fit_boundary_curve.call_count == 2
        
        assert 'green_boundary_0' in corner_debug_data
        assert 'blue_boundary_0' in corner_debug_data

    # ==================== Edge Case Tests ====================

    def test_empty_svg(self, converter, svg_parser):
        """Test converting an empty SVG."""
        test_svg_path = "test_empty.svg"
        svg_parser.extract_boundaries_by_color.return_value = {}
        
        result = converter.execute(test_svg_path)
        boundary_curves, wires, colored_boundaries, corner_debug_data = result
        
        assert len(boundary_curves) == 0
        assert len(wires) == 0
        svg_parser.extract_boundaries_by_color.assert_called_once_with(test_svg_path)
    
    def test_invalid_svg_path(self, converter, svg_parser):
        """Test handling of invalid SVG file path."""
        test_svg_path = "nonexistent.svg"
        svg_parser.extract_boundaries_by_color.side_effect = ValueError("SVG file not found")
        
        with pytest.raises(ValueError, match="SVG file not found"):
            converter.execute(test_svg_path)
        
        svg_parser.extract_boundaries_by_color.assert_called_once_with(test_svg_path)
    
    def test_open_curves(self, converter, svg_parser, corner_detector, 
                        bezier_fitter, mock_raw_boundary_class):
        """Test converting SVG with open curves."""
        test_svg_path = "test_open.svg"
        
        mock_points = [
            Point(0.0, 0.0), Point(0.3, 0.4), Point(0.7, 0.3), Point(1.0, 0.0)
        ]
        
        mock_raw_boundary = mock_raw_boundary_class(
            points=mock_points,
            color=Color.GREEN,
            is_closed=False
        )
        
        svg_parser.extract_boundaries_by_color.return_value = {Color.GREEN: [mock_raw_boundary]}
        corner_detector.detect_corners.return_value = ([], {})
        
        mock_bezier_segment = Mock(spec=BezierSegment)
        mock_bezier_segment.control_points = [Point(0.0, 0.0), Point(0.3, 0.1), Point(0.5, 0.2)]
        
        mock_boundary_curve = Mock(spec=BoundaryCurve)
        mock_boundary_curve.color = Color.GREEN
        mock_boundary_curve.is_closed = False
        mock_boundary_curve.bezier_segments = [mock_bezier_segment, mock_bezier_segment]
        mock_boundary_curve.corners = []
        
        bezier_fitter.fit_boundary_curve.return_value = mock_boundary_curve
        
        result = converter.execute(test_svg_path)
        boundary_curves, wires, colored_boundaries, corner_debug_data = result
        
        bezier_fitter.fit_boundary_curve.assert_called_once()
        
        assert len(boundary_curves) == 1
        assert not boundary_curves[0].is_closed

    # ==================== Error Handling Tests ====================

    def test_error_handling_in_corner_detection(self, converter, svg_parser, corner_detector,
                                               bezier_fitter, triangle_points, mock_raw_boundary_class):
        """Test error handling when corner detection fails."""
        test_svg_path = "test_error.svg"
        
        mock_raw_boundary = mock_raw_boundary_class(
            points=triangle_points,
            color=Color.GREEN,
            is_closed=True
        )
        
        svg_parser.extract_boundaries_by_color.return_value = {Color.GREEN: [mock_raw_boundary]}
        corner_detector.detect_corners.side_effect = ValueError("Corner detection failed")
        
        with pytest.raises(ValueError, match="Corner detection failed"):
            converter.execute(test_svg_path)
    
    def test_error_handling_in_bezier_fitting(self, converter, svg_parser, corner_detector,
                                             bezier_fitter, triangle_points, mock_raw_boundary_class):
        """Test error handling when Bézier fitting fails."""
        test_svg_path = "test_error.svg"
        
        mock_raw_boundary = mock_raw_boundary_class(
            points=triangle_points,
            color=Color.GREEN,
            is_closed=True
        )
        
        svg_parser.extract_boundaries_by_color.return_value = {Color.GREEN: [mock_raw_boundary]}
        corner_detector.detect_corners.return_value = ([], {})
        bezier_fitter.fit_boundary_curve.side_effect = ValueError("Bézier fitting failed")
        
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
    
    def test_force_curve_closure(self, converter):
        """Test the _force_curve_closure method."""
        mock_segment1 = Mock()
        mock_segment1.control_points = [Point(0, 0), Point(0.5, 0)]
        
        mock_segment2 = Mock()
        mock_segment2.control_points = [Point(0.5, 0), Point(1, 1)]
        
        mock_boundary_curve = Mock(spec=BoundaryCurve)
        mock_boundary_curve.bezier_segments = [mock_segment1, mock_segment2]
        
        converter._force_curve_closure(mock_boundary_curve)
        
        assert mock_segment2.control_points[-1] == mock_segment1.control_points[0]
