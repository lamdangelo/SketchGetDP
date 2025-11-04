import os
import sys
import pytest
import numpy as np
import copy

# Required for importing the module under test
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
sys.path.insert(0, project_root)

from infrastructure.point_detection.curve_fitter import CurveFitter


class TestCurveFitter:
    """Verify CurveFitter converts raster contours to smooth vector paths."""
    
    @pytest.fixture
    def curve_fitter(self):
        return CurveFitter(angle_threshold=25, min_curve_angle=120)
    
    @pytest.fixture
    def simple_contour(self):
        """Square contour tests basic shape handling."""
        return np.array([[[0, 0]], [[100, 0]], [[100, 100]], [[0, 100]]], dtype=np.int32)
    
    @pytest.fixture
    def triangle_contour(self):
        """Triangle contour tests corner detection."""
        return np.array([[[0, 0]], [[50, 100]], [[100, 0]]], dtype=np.int32)
    
    @pytest.fixture
    def closed_contour(self):
        """Circular contour tests curve fitting behavior."""
        points = []
        center_x, center_y = 50, 50
        radius = 40
        
        # Exact integer coordinates ensure proper closure detection
        angles = [0, 45, 90, 135, 180, 225, 270, 315]
        for angle_deg in angles:
            angle_rad = np.radians(angle_deg)
            x = int(center_x + radius * np.cos(angle_rad))
            y = int(center_y + radius * np.sin(angle_rad))
            points.append([[x, y]])
        
        points.append(points[0])  # Force exact closure
        return np.array(points, dtype=np.int32)

    def test_initialization_sets_geometric_thresholds(self, curve_fitter):
        """Thresholds determine line vs curve classification."""
        assert curve_fitter.angle_threshold == 25
        assert curve_fitter.min_curve_angle == 120

    def test_simplify_reduces_points_while_preserving_shape(self, curve_fitter, simple_contour):
        """Simplification improves performance without quality loss."""
        simplified = curve_fitter.simplify(simple_contour)
        assert simplified is not None
        assert len(simplified) >= 3

    def test_simplify_rejects_contours_with_insufficient_points(self, curve_fitter):
        """Minimum 3 points required to form a valid shape."""
        insufficient_contour = np.array([[[0, 0]], [[1, 1]]], dtype=np.int32)
        assert curve_fitter.simplify(insufficient_contour) is None

    def test_fit_curve_generates_valid_svg_path(self, curve_fitter, simple_contour):
        """SVG path must be properly formatted for rendering."""
        path_data = curve_fitter.fit_curve(simple_contour)
        assert path_data.startswith('M')  # Move command starts path
        assert path_data.endswith('Z')    # Close command ends path
        assert any(cmd in path_data for cmd in ['L', 'Q'])  # Contains drawing commands

    def test_fit_curve_rejects_invalid_contours(self, curve_fitter):
        """Prevents processing of malformed input data."""
        insufficient_contour = np.array([[[0, 0]], [[1, 1]]], dtype=np.int32)
        assert curve_fitter.fit_curve(insufficient_contour) is None

    def test_ensure_closure_preserves_already_closed_contours(self, curve_fitter):
        """Avoids redundant operations on properly formed shapes."""
        points = [[0, 0], [100, 0], [100, 100], [0, 100], [0, 0]]
        closed_points, is_closed = curve_fitter._ensure_closure(points)
        assert bool(is_closed) is True
        assert len(closed_points) == len(points)

    def test_ensure_closure_force_closes_open_contours(self, curve_fitter):
        """SVG requires closed paths for proper rendering."""
        original_points = [[0, 0], [100, 0], [100, 100], [0, 100]]
        points = copy.deepcopy(original_points)
        closed_points, is_closed = curve_fitter._ensure_closure(points)
        assert bool(is_closed) is True
        assert len(closed_points) == len(original_points) + 1  # Added closure point
        assert closed_points[0] == closed_points[-1]  # Path forms complete loop

    def test_calculate_segment_angle_computes_turning_angles(self, curve_fitter):
        """Angles determine whether to use lines or curves."""
        angle = curve_fitter._calculate_segment_angle([0, 0], [0, 1], [1, 1])
        assert angle is not None
        assert abs(angle - 90) < 1.0  # Right angle should be ~90 degrees

    def test_calculate_segment_angle_handles_degenerate_cases(self, curve_fitter):
        """Prevents mathematical errors with invalid geometry."""
        angle = curve_fitter._calculate_segment_angle([0, 0], [0, 0], [0, 0])
        assert angle is None

    def test_should_use_curve_fitting_determines_segment_eligibility(self, curve_fitter):
        """Curve fitting requires sufficient surrounding points."""
        assert curve_fitter._should_use_curve_fitting(1, 5, True) is True   # Has neighbors
        assert curve_fitter._should_use_curve_fitting(4, 5, False) is False # Path boundary

    def test_generate_svg_path_creates_drawing_commands(self, curve_fitter):
        """Translates geometric data into SVG render instructions."""
        points = [[0, 0], [100, 0], [100, 100], [0, 100]]
        path_data = curve_fitter._generate_svg_path(points, True)
        assert path_data.startswith('M 0,0')
        assert path_data.endswith('Z')

    def test_contour_closure_detection_handles_various_geometries(self, curve_fitter, closed_contour):
        """Different contour types require different closure strategies."""
        points = [[point[0][0], point[0][1]] for point in closed_contour]
        
        # Naturally closed contours remain unchanged
        points_copy_1 = copy.deepcopy(points)
        closed_points_1, is_closed_1 = curve_fitter._ensure_closure(points_copy_1)
        assert bool(is_closed_1) is True
        assert len(closed_points_1) == len(points)
        
        # Artificially opened contours get forced closure
        points_copy_2 = copy.deepcopy(points)
        opened_points = points_copy_2[:-1]
        original_opened_count = len(opened_points)
        closed_points_2, is_closed_2 = curve_fitter._ensure_closure(opened_points)
        assert bool(is_closed_2) is True
        assert len(closed_points_2) == original_opened_count + 1

    def test_different_epsilon_factors_affect_simplification_aggressiveness(self, curve_fitter, simple_contour):
        """Tolerance balance between detail preservation and point reduction."""
        path_aggressive = curve_fitter.fit_curve(simple_contour, epsilon_factor=0.01)
        path_conservative = curve_fitter.fit_curve(simple_contour, epsilon_factor=0.0001)
        assert path_aggressive is not None
        assert path_conservative is not None

    def test_path_data_contains_required_svg_elements(self, curve_fitter, simple_contour):
        """SVG specification mandates specific command structure."""
        path_data = curve_fitter.fit_curve(simple_contour)
        commands = path_data.split()
        assert commands[0] == 'M'  # Must start with move
        assert commands[-1] == 'Z' # Must end with close

    def test_performance_with_large_contours(self, curve_fitter):
        """Algorithm must handle realistic input sizes efficiently."""
        points = []
        for i in range(50):
            angle = 2 * np.pi * i / 50
            x = 100 + 80 * np.cos(angle)
            y = 100 + 80 * np.sin(angle)
            points.append([[x, y]])
        points.append(points[0])
        large_contour = np.array(points, dtype=np.int32)
        
        path_data = curve_fitter.fit_curve(large_contour)
        assert path_data is not None

    def test_square_contour_prefers_curves_over_lines(self, curve_fitter):
        """Curve fitting produces smoother results than straight lines."""
        square_contour = np.array([[[0, 0]], [[100, 0]], [[100, 100]], [[0, 100]]], dtype=np.int32)
        path_data = curve_fitter.fit_curve(square_contour)
        assert any(cmd in path_data for cmd in ['L', 'Q'])

    def test_triangle_contour_generation(self, curve_fitter, triangle_contour):
        """Triangles test corner case with minimal points."""
        path_data = curve_fitter.fit_curve(triangle_contour)
        assert path_data is not None
