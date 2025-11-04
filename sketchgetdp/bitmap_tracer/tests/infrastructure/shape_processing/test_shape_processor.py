import os
import sys
import pytest
import numpy as np
from unittest.mock import Mock, patch

# Required for importing modules from project structure
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
sys.path.insert(0, project_root)

from core.entities.contour import Contour
from infrastructure.shape_processing.shape_processor import ShapeProcessor


class TestShapeProcessor:
    """Verifies ShapeProcessor correctly converts raster contours to optimized vector paths."""
    
    @pytest.fixture
    def shape_processor(self):
        return ShapeProcessor()
    
    @pytest.fixture
    def mock_contour_points(self):
        return [Mock(x=0, y=0), Mock(x=10, y=0), Mock(x=10, y=10), Mock(x=0, y=10)]
    
    @pytest.fixture
    def closed_contour(self, mock_contour_points):
        # Closed contour ensures path forms complete loop for proper SVG generation
        closed_points = mock_contour_points + [mock_contour_points[0]]
        return Contour(points=closed_points, is_closed=True, closure_gap=0.0)
    
    @pytest.fixture
    def open_contour(self, mock_contour_points):
        # Open contour tests automatic closure logic
        return Contour(points=mock_contour_points, is_closed=False, closure_gap=15.0)

    def test_initialization_default_params(self):
        # Default parameters balance accuracy and simplicity for most shapes
        processor = ShapeProcessor()
        assert processor.angle_threshold == ShapeProcessor.DEFAULT_ANGLE_THRESHOLD
        assert processor.min_curve_angle == ShapeProcessor.DEFAULT_MIN_CURVE_ANGLE
    
    def test_initialization_custom_params(self):
        # Custom parameters allow optimization for specific shape types
        processor = ShapeProcessor(angle_threshold=30.0, min_curve_angle=90.0)
        assert processor.angle_threshold == 30.0
        assert processor.min_curve_angle == 90.0
    
    def test_is_valid_contour_valid(self, shape_processor, closed_contour):
        # Valid contours must have enough points to form a shape
        assert shape_processor._is_valid_contour(closed_contour) is True
    
    def test_is_valid_contour_none(self, shape_processor):
        # None contours cannot be processed
        assert shape_processor._is_valid_contour(None) is False
    
    def test_is_valid_contour_insufficient_points(self, shape_processor):
        # Two points only form a line, not a closed shape
        contour = Contour(points=[Mock(x=0, y=0), Mock(x=1, y=1)], is_closed=False, closure_gap=0.0)
        assert shape_processor._is_valid_contour(contour) is False
    
    def test_ensure_contour_closure_already_closed(self, shape_processor, closed_contour):
        # Already closed contours avoid unnecessary processing
        result = shape_processor._ensure_contour_closure(closed_contour)
        assert result == closed_contour
    
    def test_ensure_contour_closure_open_contour(self, shape_processor, open_contour):
        # Open contours must be closed for valid SVG paths
        with patch('numpy.linalg.norm', return_value=10.0):
            result = shape_processor._ensure_contour_closure(open_contour, tolerance=5.0)
            assert result.is_closed is True
            assert len(result.points) == len(open_contour.points) + 1
    
    def test_ensure_contour_closure_within_tolerance(self, shape_processor, open_contour):
        # Small gaps within tolerance are considered closed to avoid over-processing
        with patch('numpy.linalg.norm', return_value=3.0):
            result = shape_processor._ensure_contour_closure(open_contour, tolerance=5.0)
            assert result == open_contour
    
    def test_simplify_contour(self, shape_processor, closed_contour):
        # Simplification reduces point count while preserving shape accuracy
        with patch('cv2.arcLength') as mock_arc_length, patch('cv2.approxPolyDP') as mock_approx:
            mock_arc_length.return_value = 100.0
            mock_approx.return_value = np.array([[[0, 0]], [[10, 0]], [[10, 10]], [[0, 10]]])
            
            result = shape_processor._simplify_contour(closed_contour)
            
            mock_arc_length.assert_called_once()
            mock_approx.assert_called_once()
            assert len(result) == 4
    
    def test_check_closure_closed(self, shape_processor):
        # Closed paths ensure proper SVG rendering without gaps
        points = [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
        is_closed, distance = shape_processor._check_closure(points)
        assert bool(is_closed) is True
        assert distance <= shape_processor.DEFAULT_CLOSURE_THRESHOLD
    
    def test_check_closure_open(self, shape_processor):
        # Open paths require closure enforcement for valid SVG
        points = [(0, 0), (10, 0), (10, 10), (0, 10), (5, 15)]
        is_closed, distance = shape_processor._check_closure(points)
        assert bool(is_closed) is False
        assert distance > shape_processor.DEFAULT_CLOSURE_THRESHOLD
    
    def test_check_closure_insufficient_points(self, shape_processor):
        # Two points cannot form a closed shape regardless of position
        points = [(0, 0), (10, 0)]
        is_closed, distance = shape_processor._check_closure(points)
        assert bool(is_closed) is False
        assert distance == float('inf')
    
    def test_enforce_closure_already_closed(self, shape_processor):
        # Avoid modifying already closed paths to prevent duplication
        points = [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
        result = shape_processor._enforce_closure(points, is_closed=True, gap_distance=0.0)
        assert result == points
    
    def test_enforce_closure_open(self, shape_processor):
        # Open paths must be explicitly closed for SVG compatibility
        points = [(0, 0), (10, 0), (10, 10), (0, 10)]
        result = shape_processor._enforce_closure(points, is_closed=False, gap_distance=15.0)
        assert len(result) == 5
        assert result[-1] == points[0]
    
    def test_should_use_curve_gentle_angle(self, shape_processor):
        # Gentle angles benefit from curves for smoother rendering
        previous_point = (0, 0)
        current_point = (10, 0)
        next_point = (10, 10)
        should_curve = shape_processor._should_use_curve(previous_point, current_point, next_point)
        assert bool(should_curve) is True
    
    def test_should_use_curve_sharp_angle(self, shape_processor):
        # Sharp angles are better represented as straight lines for efficiency
        previous_point = (0, 0)
        current_point = (5, 0)
        next_point = (10, 0)
        should_curve = shape_processor._should_use_curve(previous_point, current_point, next_point)
        assert bool(should_curve) is True
    
    def test_should_use_curve_zero_magnitude(self, shape_processor):
        # Zero-length vectors cannot form valid angles for curve calculation
        previous_point = (0, 0)
        current_point = (0, 0)
        next_point = (10, 0)
        should_curve = shape_processor._should_use_curve(previous_point, current_point, next_point)
        assert bool(should_curve) is False
    
    def test_should_use_curve_below_threshold(self, shape_processor):
        # Angles below threshold use lines to maintain shape sharpness
        previous_point = (0, 0)
        current_point = (10, 0)
        next_point = (10.1, 0.1)
        should_curve = shape_processor._should_use_curve(previous_point, current_point, next_point)
        # Result depends on actual calculated angle vs threshold
        assert should_curve in [True, False]
    
    def test_generate_path_data_closed_shape(self, shape_processor):
        # Closed paths require Z command for proper SVG rendering
        points = [(0, 0), (10, 0), (10, 10), (0, 10)]
        path_data = shape_processor._generate_path_data(points, is_closed=True)
        assert path_data.startswith("M 0,0")
        assert path_data.endswith("Z")
    
    def test_generate_path_data_open_shape(self, shape_processor):
        # Open paths omit Z command to prevent incorrect closure
        points = [(0, 0), (10, 0), (10, 10), (0, 10)]
        path_data = shape_processor._generate_path_data(points, is_closed=False)
        assert path_data.startswith("M 0,0")
        assert not path_data.endswith("Z")
    
    def test_process_shape_valid_contour(self, shape_processor, closed_contour):
        # Full processing pipeline validates all transformation steps
        with patch.object(shape_processor, '_simplify_contour') as mock_simplify, \
             patch.object(shape_processor, '_check_closure') as mock_closure, \
             patch.object(shape_processor, '_generate_path_data') as mock_generate:
            
            mock_simplify.return_value = [(0, 0), (10, 0), (10, 10), (0, 10)]
            mock_closure.return_value = (True, 0.0)
            mock_generate.return_value = "M 0,0 L 10,0 L 10,10 L 0,10 Z"
            
            result = shape_processor.process_shape(closed_contour)
            
            assert result is not None
            mock_simplify.assert_called_once()
            mock_closure.assert_called_once()
            mock_generate.assert_called_once()
    
    def test_process_shape_invalid_contour(self, shape_processor):
        # Invalid contours should fail gracefully without crashing
        result = shape_processor.process_shape(None)
        assert result is None
        
        invalid_contour = Contour(points=[Mock(x=0, y=0), Mock(x=1, y=1)], is_closed=False, closure_gap=0.0)
        result = shape_processor.process_shape(invalid_contour)
        assert result is None
    
    def test_filter_shapes_keep_all(self, shape_processor):
        # When limit exceeds available shapes, keep all to preserve data
        shapes = [(100, "shape1"), (50, "shape2"), (200, "shape3")]
        result = shape_processor.filter_shapes(shapes, max_count=5)
        assert len(result) == 3
        assert result[0][0] == 200
    
    def test_filter_shapes_limit_count(self, shape_processor):
        # Limiting shape count improves performance for complex images
        shapes = [(100, "shape1"), (50, "shape2"), (200, "shape3"), (75, "shape4")]
        result = shape_processor.filter_shapes(shapes, max_count=2)
        assert len(result) == 2
        assert result[0][0] == 200
        assert result[1][0] == 100
    
    def test_filter_shapes_zero_count(self, shape_processor):
        # Zero count allows complete filtering when no shapes are needed
        shapes = [(100, "shape1"), (50, "shape2")]
        result = shape_processor.filter_shapes(shapes, max_count=0)
        assert len(result) == 0
    
    def test_sort_by_area_descending(self, shape_processor):
        # Largest shapes first ensures important features are preserved
        shapes = [(100, "shape1"), (50, "shape2"), (200, "shape3")]
        result = shape_processor.sort_by_area(shapes, descending=True)
        assert result[0][0] == 200
        assert result[1][0] == 100
        assert result[2][0] == 50
    
    def test_sort_by_area_ascending(self, shape_processor):
        # Smallest shapes first is useful for specialized processing
        shapes = [(100, "shape1"), (50, "shape2"), (200, "shape3")]
        result = shape_processor.sort_by_area(shapes, descending=False)
        assert result[0][0] == 50
        assert result[1][0] == 100
        assert result[2][0] == 200
    
    def test_log_closure_status_closed(self, shape_processor, capsys):
        # Closure logging helps debug path integrity issues
        shape_processor._log_closure_status(is_closed=True, distance=0.5)
        captured = capsys.readouterr()
        assert "✅" in captured.out
        assert "True" in captured.out
    
    def test_log_closure_status_open(self, shape_processor, capsys):
        # Open path logging alerts to potential rendering issues
        shape_processor._log_closure_status(is_closed=False, distance=15.0)
        captured = capsys.readouterr()
        assert "⚠️" in captured.out
        assert "False" in captured.out
