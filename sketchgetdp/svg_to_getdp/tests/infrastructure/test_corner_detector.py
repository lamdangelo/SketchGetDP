"""
Unit tests for CornerDetector class.

Tests corner detection functionality on various geometric shapes,
including rectangles, circles, ellipses, and complex mixed shapes.
"""
import pytest
from math import cos, sin, pi

from svg_to_getdp.infrastructure.corner_detection.corner_detector import CornerDetector
from svg_to_getdp.core.entities.point import Point


class TestCornerDetector:
    """Test suite for CornerDetector class."""

    # ==================== Fixtures ====================

    @pytest.fixture
    def detector(self):
        """Create a corner detector instance for testing."""
        return CornerDetector(debug_enabled=False)
    
    @pytest.fixture
    def debug_detector(self):
        """Create a corner detector with debug enabled."""
        return CornerDetector(debug_enabled=True)
    
    @pytest.fixture
    def rectangle_points(self):
        """Create points for a rectangle shape."""
        return self.generate_rectangle_points(0, 0, 100, 50)
    
    @pytest.fixture
    def circle_points(self):
        """Create points for a circle shape."""
        return self.generate_circle_points(50, 50, 40)
    
    @pytest.fixture
    def ellipse_points(self):
        """Create points for an ellipse shape."""
        return self.generate_ellipse_points(50, 50, 40, 30)
    
    @pytest.fixture
    def tear_shape_points(self):
        """Create points for a tear/drop shape."""
        return self.generate_tear_shape_points(50, 50)
    
    @pytest.fixture
    def peanut_shape_points(self):
        """Create points for a smooth peanut shape."""
        return self.generate_peanut_shape_points(50, 50)
    
    @pytest.fixture
    def sharp_corner_points(self):
        """Create points with a sharp 90-degree corner."""
        points = []
        for i in range(20):
            points.append(Point(i, 0))
        for i in range(20):
            points.append(Point(20, i))
        return points
    
    @pytest.fixture
    def l_shape_points(self):
        """Create points forming a simple L-shaped corner."""
        points = []
        # Horizontal line
        for i in range(50):
            points.append(Point(i, 0))
        
        # Vertical line
        for i in range(50):
            points.append(Point(50, i))
        
        return points

    # ==================== Helper Methods ====================

    def generate_circle_points(self, center_x, center_y, radius, num_points=200):
        """Generate points along a circle."""
        points = []
        for i in range(num_points):
            angle = 2 * pi * i / num_points
            x = center_x + radius * cos(angle)
            y = center_y + radius * sin(angle)
            points.append(Point(x, y))
        return points
    
    def generate_ellipse_points(self, center_x, center_y, width, height, num_points=200):
        """Generate points along an ellipse."""
        points = []
        for i in range(num_points):
            angle = 2 * pi * i / num_points
            x = center_x + width * cos(angle)
            y = center_y + height * sin(angle)
            points.append(Point(x, y))
        return points
    
    def generate_rectangle_points(self, x, y, width, height, num_points_per_side=50):
        """Generate points along a rectangle."""
        points = []
        
        # Top side
        for i in range(num_points_per_side):
            px = x + (width * i / num_points_per_side)
            py = y
            points.append(Point(px, py))
        
        # Right side
        for i in range(num_points_per_side):
            px = x + width
            py = y + (height * i / num_points_per_side)
            points.append(Point(px, py))
        
        # Bottom side
        for i in range(num_points_per_side):
            px = x + width - (width * i / num_points_per_side)
            py = y + height
            points.append(Point(px, py))
        
        # Left side
        for i in range(num_points_per_side):
            px = x
            py = y + height - (height * i / num_points_per_side)
            points.append(Point(px, py))
        
        return points
    
    def generate_tear_shape_points(self, center_x, center_y, size=100, num_points=200):
        """Generate points for a tear/drop shape (has 1 sharp corner at the pointy end)."""
        points = []
        for i in range(num_points):
            angle = 2 * pi * i / num_points
            r = size * (1 - cos(angle))
            x = center_x + r * cos(angle)
            y = center_y + r * sin(angle)
            points.append(Point(x, y))
        return points
    
    def generate_peanut_shape_points(self, center_x, center_y, size=100, num_points=200, waist_factor=0.5):
        """Generate points for a peanut shape with a distinct waist in the middle."""
        points = []
        for i in range(num_points):
            angle = 2 * pi * i / num_points
            r = size * (waist_factor + (1 - waist_factor) * (cos(angle) ** 2))
            x = center_x + r * cos(angle)
            y = center_y + r * sin(angle)
            points.append(Point(x, y))
        return points

    # ==================== Initialization Tests ====================

    def test_initialization_default_params(self):
        """Test that detector initializes with default parameters."""
        detector = CornerDetector()
        
        assert detector.window_size == 15
        assert detector.direction_change_threshold == pytest.approx(0.8)
        assert detector.angle_threshold == pytest.approx(pi / 6)
        assert detector.minimum_corner_distance == 5
        assert detector.smoothness_threshold == pytest.approx(0.72)
        assert detector.corner_strength_threshold == pytest.approx(0.45)
        assert detector.ellipse_aspect_ratio_threshold == pytest.approx(1.2)
        assert detector.debug_enabled == True
    
    def test_initialization_custom_params(self):
        """Test that detector initializes with custom parameters."""
        detector = CornerDetector(
            window_size=20,
            direction_change_threshold=1.0,
            angle_threshold=pi/4,
            minimum_corner_distance=10,
            smoothness_threshold=0.8,
            corner_strength_threshold=0.6,
            ellipse_aspect_ratio_threshold=1.5,
            debug_enabled=False
        )
        
        assert detector.window_size == 20
        assert detector.direction_change_threshold == pytest.approx(1.0)
        assert detector.angle_threshold == pytest.approx(pi/4)
        assert detector.minimum_corner_distance == 10
        assert detector.smoothness_threshold == pytest.approx(0.8)
        assert detector.corner_strength_threshold == pytest.approx(0.6)
        assert detector.ellipse_aspect_ratio_threshold == pytest.approx(1.5)
        assert detector.debug_enabled == False

    # ==================== Basic Functionality Tests ====================

    def test_detection_with_empty_boundary_points(self, detector):
        """Test corner detection with empty boundary points."""
        corners, debug_data = detector.detect_corners([])
        
        assert corners == []
        assert isinstance(debug_data, dict)
    
    def test_detection_with_small_number_of_points(self, detector):
        """Test corner detection with very few points."""
        points = [Point(0, 0), Point(1, 0), Point(1, 1), Point(0, 1)]
        corners, debug_data = detector.detect_corners(points)
        
        assert corners == []  # Too few points for detection
        assert isinstance(debug_data, dict)
    
    def test_debug_data_structure(self, debug_detector, rectangle_points):
        """Test that debug data has the expected structure."""
        corners, debug_data = debug_detector.detect_corners(rectangle_points)
        
        assert isinstance(debug_data, dict)
        assert 'shape_analysis' in debug_data
        assert 'candidate_detection' in debug_data
        assert 'strength_calculations' in debug_data
        assert 'clustering' in debug_data
        assert 'final_decisions' in debug_data
        assert 'all_steps' in debug_data
        
        # Check that all_steps contains messages
        assert len(debug_data['all_steps']) > 0

    # ==================== Shape Detection Tests ====================

    def test_rectangle_detection(self, detector, rectangle_points):
        """Test corner detection on a rectangle (should find 4 corners)."""
        corners, debug_data = detector.detect_corners(rectangle_points)
        
        # Should find exactly 4 corners for a rectangle
        assert len(corners) == 4
        
        # Corners should be well-spaced
        total_points = len(rectangle_points)
        for i in range(len(corners)):
            for j in range(i + 1, len(corners)):
                distance = min(
                    abs(corners[i] - corners[j]),
                    total_points - abs(corners[i] - corners[j])
                )
                assert distance > 10
        
        # Check debug data
        if 'final_decisions' in debug_data:
            assert 'final_corners' in debug_data['final_decisions']
            assert len(debug_data['final_decisions']['final_corners']) == 4
    
    def test_circle_detection(self, detector, circle_points):
        """Test corner detection on a circle (should find 0 corners)."""
        corners, debug_data = detector.detect_corners(circle_points)
        
        # Circle should have no corners
        assert len(corners) == 0
        
        # Check shape analysis in debug data
        if 'shape_analysis' in debug_data:
            assert debug_data['shape_analysis'].get('is_ellipse', False) or \
                   debug_data['shape_analysis'].get('too_smooth', False)
    
    def test_ellipse_detection(self, detector, ellipse_points):
        """Test corner detection on an ellipse (should find 0 corners)."""
        corners, debug_data = detector.detect_corners(ellipse_points)
        
        # Ellipse should have no corners
        assert len(corners) == 0
        
        # Check shape analysis
        if 'shape_analysis' in debug_data:
            assert debug_data['shape_analysis'].get('is_ellipse', False) or \
                   debug_data['shape_analysis'].get('too_smooth', False)
    
    def test_tear_shape_detection(self, detector, tear_shape_points):
        """Test corner detection on a tear/drop shape (should find 1 sharp corner)."""
        corners, debug_data = detector.detect_corners(tear_shape_points)
        
        # Tear shape should have 1 corner
        assert len(corners) == 1
        
        # Check debug data has information about the corner
        if 'final_decisions' in debug_data:
            assert len(debug_data['final_decisions'].get('final_corners', [])) == 1
    
    def test_peanut_shape_detection(self, detector, peanut_shape_points):
        """Test corner detection on a peanut shape (should find 0 corners)."""
        corners, debug_data = detector.detect_corners(peanut_shape_points)
        
        # Smooth peanut shape should have no corners
        assert len(corners) == 0

    # ==================== Edge Case Tests ====================

    def test_detection_with_large_number_of_points(self, detector):
        """Test corner detection with a very large number of points."""
        rectangle_points = self.generate_rectangle_points(0, 0, 100, 50, num_points_per_side=200)
        
        corners, debug_data = detector.detect_corners(rectangle_points)
        
        # Should still find 4 corners
        assert len(corners) == 4
        
        # All corners should have valid indices
        for corner_idx in corners:
            assert 0 <= corner_idx < len(rectangle_points)

    # ==================== Internal Method Tests ====================

    def test_angle_calculation(self, detector, l_shape_points):
        """Test angle calculation indirectly by checking corner detection."""
        # Create an L-shape (should have 3 corners)
        corners, debug_data = detector.detect_corners(l_shape_points)
        
        assert len(corners) > 0
    
    def test_corner_strength_calculation(self, debug_detector, rectangle_points):
        """Test strength calculation through debug data."""
        corners, debug_data = debug_detector.detect_corners(rectangle_points)
        
        # Should find 4 corners
        assert len(corners) == 4
        
        # Check strength calculations in debug data
        if 'strength_calculations' in debug_data:
            strengths = debug_data['strength_calculations']
            
            # Some strengths should be calculated
            assert len(strengths) > 0
            
            # All strengths should be between 0 and 1
            for strength in strengths.values():
                assert 0 <= strength <= 1
        
        # Check final decisions include strengths
        if 'final_decisions' in debug_data and 'corner_strengths' in debug_data['final_decisions']:
            final_strengths = debug_data['final_decisions']['corner_strengths']
            assert len(final_strengths) == len(corners)
            
            for idx, strength in final_strengths.items():
                assert idx in corners
                assert 0 <= strength <= 1
                assert strength >= 0.45  # Should meet threshold
    
    def test_candidate_combination(self, debug_detector, rectangle_points):
        """Test candidate combination through debug data."""
        corners, debug_data = debug_detector.detect_corners(rectangle_points)
        
        # Check candidate detection methods in debug data
        if 'candidate_detection' in debug_data:
            candidate_data = debug_data['candidate_detection']
            
            # Should have multiple detection methods
            assert 'angle_method' in candidate_data
            assert 'direction_method' in candidate_data
            assert 'curvature_method' in candidate_data
            
            # Should have combined results
            if 'combined_votes' in candidate_data:
                combined = candidate_data['combined_votes']
                assert len(combined) > 0
                
                # Check votes are reasonable
                for votes in combined.values():
                    assert votes >= 0
    
    def test_corner_refinement(self, debug_detector, rectangle_points):
        """Test refinement process through debug data."""
        corners, debug_data = debug_detector.detect_corners(rectangle_points)
        
        # Should have refinement details in debug data
        if 'refinement_details' in debug_data:
            refinement_details = debug_data['refinement_details']
            
            # Should have some refinement details
            assert len(refinement_details) > 0
            
            # Check structure of refinement details
            for detail in refinement_details:
                assert 'cluster' in detail
                assert 'best_candidate' in detail
                assert 'refined_candidate' in detail
                assert 'accepted' in detail

    # ==================== Parameter Sensitivity Tests ====================

    def test_different_angle_thresholds(self):
        """Test corner detection with different angle thresholds."""
        points = []
        
        # Square with rounded corners
        for i in range(50):
            points.append(Point(i, 0))
        for i in range(10):
            angle = pi/2 * i/10
            points.append(Point(50 + 5*cos(angle), 5 + 5*sin(angle)))
        for i in range(50):
            points.append(Point(55 - i, 10))
        
        # Test with strict threshold
        strict_detector = CornerDetector(angle_threshold=pi/3, debug_enabled=False)
        strict_corners, _ = strict_detector.detect_corners(points)
        
        # Test with lenient threshold
        lenient_detector = CornerDetector(angle_threshold=pi/12, debug_enabled=False)
        lenient_corners, _ = lenient_detector.detect_corners(points)
        
        # Lenient should find at least as many corners as strict
        assert len(lenient_corners) >= len(strict_corners)
    
    def test_different_smoothness_thresholds(self, ellipse_points):
        """Test ellipse detection with different smoothness thresholds."""
        # Test with low threshold (0.5)
        low_thresh_detector = CornerDetector(smoothness_threshold=0.5, debug_enabled=False)
        low_corners, low_debug = low_thresh_detector.detect_corners(ellipse_points)
        
        # Test with high threshold (0.9)
        high_thresh_detector = CornerDetector(smoothness_threshold=0.9, debug_enabled=False)
        high_corners, high_debug = high_thresh_detector.detect_corners(ellipse_points)
        
        # Both should detect ellipse as having no corners
        if 'shape_analysis' in low_debug:
            low_smoothness = low_debug['shape_analysis'].get('smoothness_score', 0)

            assert 0.78 < low_smoothness < 0.8 # ellipse smoothness ~ 0.795
            assert len(low_corners) == 0
        
        if 'shape_analysis' in high_debug:
            high_smoothness = high_debug['shape_analysis'].get('smoothness_score', 0)

            assert 0.78 < high_smoothness < 0.8 # ellipse smoothness ~ 0.795
            assert len(high_corners) == 0
    
    def test_minimum_corner_distance_enforcement(self):
        """Test that minimum corner distance is properly enforced."""
        points = []
        
        # Two close right angles
        for i in range(10):
            points.append(Point(i, 0))
        points.append(Point(10, 0))
        points.append(Point(10, 1))
        points.append(Point(10, 2))
        for i in range(10):
            points.append(Point(10 - i, 2))
        
        # Test with minimum distance of 5
        detector = CornerDetector(minimum_corner_distance=5, debug_enabled=False)
        corners, _ = detector.detect_corners(points)
        
        # Should only keep one of the two close corners
        assert len(corners) <= 2
        
        if len(corners) == 2:
            # Check they're sufficiently spaced
            distance = min(
                abs(corners[0] - corners[1]),
                len(points) - abs(corners[0] - corners[1])
            )
            assert distance >= 5

    # ==================== Integration Tests ====================

    def test_consistency_across_runs(self, detector, rectangle_points):
        """Test that corner detection is consistent across multiple runs."""
        results = []
        for _ in range(5):
            corners, _ = detector.detect_corners(rectangle_points)
            results.append(sorted(corners))
        
        # All results should be the same
        for i in range(1, len(results)):
            assert results[i] == results[0]
    
    def test_closed_shape_handling(self, detector):
        """Test that closed shapes are handled correctly."""
        points = self.generate_rectangle_points(0, 0, 100, 50, num_points_per_side=25)
        closed_points = points + [points[0]]
        
        corners, debug_data = detector.detect_corners(closed_points)
        
        # Should find 4 corners
        assert len(corners) == 4
        
        # Check corners are reasonable
        for corner_idx in corners:
            assert 0 <= corner_idx < len(closed_points)
    
    def test_scale_invariance(self):
        """Test that corner detection works at different scales."""
        # Generate small rectangle
        small_points = self.generate_rectangle_points(0, 0, 10, 5, num_points_per_side=20)
        
        # Generate large rectangle
        large_points = self.generate_rectangle_points(0, 0, 100, 50, num_points_per_side=20)
        
        detector = CornerDetector(debug_enabled=False)
        
        small_corners, _ = detector.detect_corners(small_points)
        large_corners, _ = detector.detect_corners(large_points)
        
        # Both should find 4 corners
        assert len(small_corners) == 4
        assert len(large_corners) == 4

    # ==================== Performance Tests ====================

    def test_performance_with_many_points(self, detector):
        """Test that detector handles large number of points efficiently."""
        dense_points = self.generate_circle_points(50, 50, 40, num_points=1000)
        
        import time
        start_time = time.time()
        corners, debug_data = detector.detect_corners(dense_points)
        end_time = time.time()
        
        # Should complete in reasonable time
        assert end_time - start_time < 2.0
        
        # Circle should have no corners
        assert len(corners) == 0

    # ==================== Error Handling Tests ====================

    def test_invalid_input_types(self, detector):
        """Test handling of invalid input types."""
        invalid_points = [Point(0, 0), "not a point", Point(1, 1)]
        
        try:
            corners, debug_data = detector.detect_corners(invalid_points)
            # If it doesn't fail, verify structure
            assert isinstance(corners, list)
            assert isinstance(debug_data, dict)
        except (AttributeError, TypeError, IndexError):
            # Any of these would be reasonable errors
            pass
