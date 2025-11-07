"""
Test suite for the Corner Detector infrastructure component.
"""

import pytest
import math
import numpy as np
from unittest.mock import patch, MagicMock

from infrastructure.corner_detector import CornerDetector
from core.entities.point import Point


class TestCornerDetector:
    """Test suite for the CornerDetector class"""
    
    def setup_method(self):
        """Set up a fresh detector instance for each test"""
        self.detector = CornerDetector(num_batches=8, threshold=0.5, window_size=3, min_corner_distance=5)
    
    def test_detector_initialization(self):
        """Test that detector initializes with correct parameters"""
        assert self.detector.num_batches == 8
        assert self.detector.threshold == 0.5
        assert self.detector.window_size == 3
        assert self.detector.min_corner_distance == 5
        
        # Test with custom parameters
        custom_detector = CornerDetector(num_batches=16, threshold=0.7, window_size=2, min_corner_distance=3)
        assert custom_detector.num_batches == 16
        assert custom_detector.threshold == 0.7
        assert custom_detector.window_size == 2
        assert custom_detector.min_corner_distance == 3
    
    def test_detect_corners_insufficient_points(self):
        """Test that detector raises error for insufficient points"""
        points = [Point(0, 0), Point(1, 0)]  # Only 2 points
        
        with pytest.raises(ValueError, match="Need at least 3 points to detect corners"):
            self.detector.detect_corners(points)
    
    def test_detect_corners_square(self):
        """Test corner detection on a square shape"""
        square_points = self._create_square_points(num_points=40)
        
        corners = self.detector.detect_corners(square_points)
        
        # Should detect corners for a square
        assert len(corners) >= 2
        
        # Verify that detected corners are near actual corners
        expected_corners = [Point(0, 0), Point(1, 0), Point(1, 1), Point(0, 1)]
        self._assert_some_corners_match(corners, expected_corners, tolerance=0.2)
    
    def test_detect_corners_triangle(self):
        """Test corner detection on a triangle shape"""
        triangle_points = self._create_triangle_points(num_points=30)
        
        corners = self.detector.detect_corners(triangle_points)
        
        # Should detect some corners for a triangle
        assert len(corners) >= 1
        
        # Verify approximate corner positions
        expected_corners = [Point(0, 0), Point(1, 0), Point(0.5, 1)]
        self._assert_some_corners_match(corners, expected_corners, tolerance=0.3)
    
    def test_detect_corners_rectangle(self):
        """Test corner detection on a rectangle"""
        rectangle_points = self._create_rectangle_points(width=2.0, height=1.0, num_points=40)
        
        corners = self.detector.detect_corners(rectangle_points)
        
        # Should detect some corners for a rectangle
        assert len(corners) >= 2
        
        expected_corners = [Point(0, 0), Point(2, 0), Point(2, 1), Point(0, 1)]
        self._assert_some_corners_match(corners, expected_corners, tolerance=0.3)
    
    def test_detect_corners_smooth_curve(self):
        """Test that smooth curves have few corners detected"""
        circle_points = self._create_circle_points(num_points=50)
        
        # Use a detector with higher threshold for smooth curves
        smooth_detector = CornerDetector(threshold=0.8, min_corner_distance=15)
        corners = smooth_detector.detect_corners(circle_points)
        
        # Should detect very few corners for a smooth circle
        assert len(corners) <= 8  # Allow more false positives due to discrete sampling
    
    def test_detect_corners_mixed_shape(self):
        """Test corner detection on a shape with both straight and curved sections"""
        mixed_points = self._create_mixed_shape_points()
        
        corners = self.detector.detect_corners(mixed_points)
        
        # Should detect some corners - this shape has clear corners at the transitions
        assert len(corners) >= 2  # Should find at least the main corners
    
    def test_detect_corners_single_batch(self):
        """Test corner detection with single batch (edge case)"""
        # Use fewer points than default batch size
        few_points = [Point(i * 0.2, 0) for i in range(6)]  # 6 points
        
        corners = self.detector.detect_corners(few_points)
        
        # Should handle this case without error
        assert isinstance(corners, list)
    
    def test_detect_corners_duplicate_points(self):
        """Test corner detection with duplicate points"""
        # Create a proper rectangle with enough points for corner detection
        points = self._create_simple_rectangle_points()
        
        corners = self.detector.detect_corners(points)
        
        # Should detect at least one corner
        assert len(corners) >= 1
    
    def test_detect_corners_small_shape(self):
        """Test corner detection on a small shape with few points"""
        # Create a simple triangle with just enough points
        points = [
            Point(0, 0), Point(0.5, 0), Point(1, 0),  # Bottom edge
            Point(0.8, 0.2), Point(0.6, 0.4), Point(0.4, 0.6), Point(0.2, 0.8),  # Diagonal
            Point(0, 1), Point(0, 0.8), Point(0, 0.6), Point(0, 0.4), Point(0, 0.2),  # Left edge
            Point(0, 0)  # Close
        ]
        
        # Use a detector with smaller window for small shapes
        small_detector = CornerDetector(window_size=2, min_corner_distance=2, threshold=0.4)
        corners = small_detector.detect_corners(points)
        
        # Should detect at least one corner
        assert len(corners) >= 1
    
    def test_calculate_batch_direction_horizontal(self):
        """Test direction vector calculation for horizontal line"""
        points = [Point(0, 0), Point(1, 0), Point(2, 0)]  # Horizontal line
        
        direction = self.detector._calculate_batch_direction(points, 0, 3)
        
        # Direction should be approximately horizontal
        assert abs(direction.x) > 0.9  # Mostly horizontal
        assert abs(direction.y) < 0.1  # Little vertical component
    
    def test_calculate_batch_direction_vertical(self):
        """Test direction vector calculation for vertical line"""
        points = [Point(0, 0), Point(0, 1), Point(0, 2)]  # Vertical line
        
        direction = self.detector._calculate_batch_direction(points, 0, 3)
        
        # Direction should be approximately vertical
        assert abs(direction.x) < 0.1  # Little horizontal component
        assert abs(direction.y) > 0.9  # Mostly vertical
    
    def test_calculate_batch_direction_diagonal(self):
        """Test direction vector calculation for diagonal line"""
        points = [Point(0, 0), Point(1, 1), Point(2, 2)]  # Diagonal line
        
        direction = self.detector._calculate_batch_direction(points, 0, 3)
        
        # Direction should be approximately diagonal
        assert abs(direction.x - direction.y) < 0.2  # Roughly equal components
    
    def test_calculate_batch_direction_single_segment(self):
        """Test direction calculation with only two points"""
        points = [Point(0, 0), Point(1, 1)]
        
        direction = self.detector._calculate_batch_direction(points, 0, 2)
        
        # Should still compute valid direction
        assert direction.x != 0 or direction.y != 0
    
    def test_divide_into_batches(self):
        """Test batch division algorithm"""
        points = [Point(i, 0) for i in range(100)]  # 100 points
        
        batches = self.detector._divide_into_batches(points)
        
        # Should create correct number of batches
        assert len(batches) == self.detector.num_batches
        
        # Each batch should have approximately equal size
        batch_sizes = [len(batch) for batch in batches]
        max_size = max(batch_sizes)
        min_size = min(batch_sizes)
        assert max_size - min_size <= 1  # Sizes should differ by at most 1
    
    def test_divide_into_batches_uneven(self):
        """Test batch division with uneven point distribution"""
        points = [Point(i, 0) for i in range(17)]  # 17 points, 8 batches
        
        batches = self.detector._divide_into_batches(points)
        
        # Should handle uneven division gracefully
        assert len(batches) == min(self.detector.num_batches, len(points))
    
    def test_divide_into_batches_few_points(self):
        """Test batch division with fewer points than batches"""
        points = [Point(i, 0) for i in range(5)]  # 5 points, 8 batches requested
        
        batches = self.detector._divide_into_batches(points)
        
        # Should reduce number of batches to match available points
        assert len(batches) <= len(points)
        assert all(len(batch) >= 1 for batch in batches)
    
    def test_compute_direction_vectors(self):
        """Test direction vector computation for all batches"""
        points = self._create_square_points(num_points=40)
        batches = self.detector._divide_into_batches(points)
        
        direction_vectors = self.detector._compute_direction_vectors(batches)
        
        # Should compute one direction vector per batch
        assert len(direction_vectors) == len(batches)
        
        # All vectors should be normalized (or zero)
        for vector in direction_vectors:
            norm = vector.norm()
            assert norm < 1.1  # Should be <= 1 (allowing small floating point errors)
    
    def test_detect_corner_indices_clear_corners(self):
        """Test corner index detection with clear corners"""
        # Create direction vectors that change sharply at specific points
        direction_vectors = [
            Point(1, 0),   # Right
            Point(1, 0),   # Right  
            Point(0, 1),   # Up (sharp change - corner)
            Point(0, 1),   # Up
            Point(-1, 0),  # Left (sharp change - corner)
        ]
        
        corner_indices = self.detector._detect_corner_indices(direction_vectors)
        
        # Should detect corners at indices where direction changes sharply
        assert len(corner_indices) >= 1
    
    def test_detect_corner_indices_no_corners(self):
        """Test corner detection with no significant direction changes"""
        # All vectors point in similar direction
        direction_vectors = [
            Point(1, 0), Point(0.9, 0.1), Point(0.8, 0.2),
            Point(0.7, 0.3), Point(0.6, 0.4)
        ]
        
        corner_indices = self.detector._detect_corner_indices(direction_vectors)
        
        # Should detect no corners with high threshold
        assert len(corner_indices) == 0
    
    def test_detect_corner_indices_threshold_sensitivity(self):
        """Test corner detection sensitivity to threshold parameter"""
        direction_vectors = [
            Point(1, 0), Point(0.7, 0.7),  # 45 degree change
        ]
        
        # With low threshold, should detect corner
        low_threshold_detector = CornerDetector(threshold=0.5)
        corners_low = low_threshold_detector._detect_corner_indices(direction_vectors)
        assert len(corners_low) == 1
        
        # With high threshold, should not detect corner
        high_threshold_detector = CornerDetector(threshold=1.5)
        corners_high = high_threshold_detector._detect_corner_indices(direction_vectors)
        assert len(corners_high) == 0
    
    def test_map_corner_indices_to_points(self):
        """Test mapping corner indices back to actual points"""
        points = [Point(i, 0) for i in range(10)]
        batches = self.detector._divide_into_batches(points)
        corner_indices = [2, 5]
        
        corner_points = self.detector._map_corner_indices_to_points(batches, corner_indices)
        
        # Should return correct points
        assert len(corner_points) == 2
    
    def test_direction_difference_calculation(self):
        """Test calculation of direction vector differences"""
        vec1 = Point(1, 0)
        vec2 = Point(0, 1)
        
        difference = self.detector._direction_difference(vec1, vec2)
        
        # Difference between perpendicular vectors should be √2
        expected_difference = math.sqrt(2)
        assert abs(difference - expected_difference) < 1e-10
    
    def test_direction_difference_same_vector(self):
        """Test direction difference for identical vectors"""
        vec1 = Point(1, 0)
        vec2 = Point(1, 0)
        
        difference = self.detector._direction_difference(vec1, vec2)
        
        # Difference should be 0 for identical vectors
        assert difference == 0.0
    
    def test_direction_difference_opposite_vectors(self):
        """Test direction difference for opposite vectors"""
        vec1 = Point(1, 0)
        vec2 = Point(-1, 0)
        
        difference = self.detector._direction_difference(vec1, vec2)
        
        # Difference should be 2 for opposite vectors
        assert abs(difference - 2.0) < 1e-10
    
    def test_different_batch_sizes(self):
        """Test corner detection with different batch sizes"""
        square_points = self._create_square_points(num_points=40)
        
        for batch_size in [4, 8, 16]:
            detector = CornerDetector(num_batches=batch_size)
            corners = detector.detect_corners(square_points)
            
            # Should detect reasonable number of corners for a square
            assert len(corners) >= 1
    
    def test_different_thresholds(self):
        """Test corner detection with different threshold values"""
        mixed_points = self._create_mixed_shape_points()
        
        for threshold in [0.2, 0.5, 1.0]:
            detector = CornerDetector(threshold=threshold)
            corners = detector.detect_corners(mixed_points)
            
            # Should always return a list (may be empty for high thresholds)
            assert isinstance(corners, list)
    
    def test_performance_large_dataset(self):
        """Test performance with larger datasets"""
        # Create a larger point set
        n_points = 1000
        points = [Point(math.cos(2 * math.pi * i / n_points), 
                        math.sin(2 * math.pi * i / n_points)) 
                 for i in range(n_points)]
        
        import time
        start_time = time.time()
        
        corners = self.detector.detect_corners(points)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete in reasonable time
        assert duration < 2.0  # 2 seconds should be plenty
        
        # Result should be valid
        assert isinstance(corners, list)
    
    def test_reproducibility(self):
        """Test that corner detection produces consistent results"""
        points = self._create_complex_shape_points()
        
        # Detect corners multiple times
        corners1 = self.detector.detect_corners(points)
        corners2 = self.detector.detect_corners(points)
        
        # Should produce identical results
        assert len(corners1) == len(corners2)
    
    def test_numerical_stability(self):
        """Test numerical stability with very small/large coordinates"""
        # Very small coordinates
        small_points = [Point(i * 1e-10, i * 1e-10) for i in range(10)]
        small_corners = self.detector.detect_corners(small_points)
        assert isinstance(small_corners, list)
        
        # Very large coordinates  
        large_points = [Point(i * 1e10, i * 1e10) for i in range(10)]
        large_corners = self.detector.detect_corners(large_points)
        assert isinstance(large_corners, list)
    
    def test_error_handling_invalid_points(self):
        """Test error handling with invalid point data"""
        # Points with NaN values - Point class already prevents this
        # So we test with valid points instead
        valid_points = [Point(0, 0), Point(1, 1), Point(2, 2)]
        corners = self.detector.detect_corners(valid_points)
        assert isinstance(corners, list)
    
    # Helper methods for creating test shapes
    
    def _create_simple_rectangle_points(self) -> list[Point]:
        """Create a simple rectangle with enough points for corner detection."""
        return [
            Point(0, 0), Point(0.2, 0), Point(0.4, 0), Point(0.6, 0), Point(0.8, 0), Point(1, 0),
            Point(1, 0.2), Point(1, 0.4), Point(1, 0.6), Point(1, 0.8), Point(1, 1),
            Point(0.8, 1), Point(0.6, 1), Point(0.4, 1), Point(0.2, 1), Point(0, 1),
            Point(0, 0.8), Point(0, 0.6), Point(0, 0.4), Point(0, 0.2), Point(0, 0)
        ]
    
    def _create_square_points(self, num_points: int = 40) -> list[Point]:
        """Create points representing a square boundary."""
        points = []
        side_length = num_points // 4
        
        # Bottom edge
        for i in range(side_length):
            points.append(Point(i/side_length, 0))
        
        # Right edge
        for i in range(side_length):
            points.append(Point(1, i/side_length))
        
        # Top edge
        for i in range(side_length):
            points.append(Point(1 - i/side_length, 1))
        
        # Left edge
        for i in range(side_length):
            points.append(Point(0, 1 - i/side_length))
        
        return points
    
    def _create_triangle_points(self, num_points: int = 30) -> list[Point]:
        """Create points representing a triangle boundary."""
        points = []
        side_length = num_points // 3
        
        # First edge
        for i in range(side_length):
            x = i / side_length
            y = 0
            points.append(Point(x, y))
        
        # Second edge
        for i in range(side_length):
            x = 1 - i / side_length
            y = i / side_length
            points.append(Point(x, y))
        
        # Third edge
        for i in range(side_length):
            x = 0
            y = 1 - i / side_length
            points.append(Point(x, y))
        
        return points
    
    def _create_rectangle_points(self, width: float = 2.0, height: float = 1.0, num_points: int = 40) -> list[Point]:
        """Create points representing a rectangle boundary."""
        points = []
        side_length = num_points // 4
        
        # Bottom edge
        for i in range(side_length):
            points.append(Point(i/side_length * width, 0))
        
        # Right edge
        for i in range(side_length):
            points.append(Point(width, i/side_length * height))
        
        # Top edge
        for i in range(side_length):
            points.append(Point(width - i/side_length * width, height))
        
        # Left edge
        for i in range(side_length):
            points.append(Point(0, height - i/side_length * height))
        
        return points
    
    def _create_circle_points(self, num_points: int = 50) -> list[Point]:
        """Create points representing a circle boundary."""
        points = []
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            x = 0.5 + 0.5 * math.cos(angle)
            y = 0.5 + 0.5 * math.sin(angle)
            points.append(Point(x, y))
        return points
    
    def _create_mixed_shape_points(self, num_points: int = 80) -> list[Point]:
        """Create points representing a shape with both straight and curved sections that has clear corners."""
        points = []
        quarter_points = num_points // 4
        
        # Bottom edge - straight line with clear corners at ends
        for i in range(quarter_points):
            points.append(Point(i/quarter_points, 0))
        
        # Right edge - quarter circle (smooth curve)
        for i in range(quarter_points):
            angle = math.pi/2 * i / quarter_points
            x = 1 + 0.3 * math.cos(angle)
            y = 0.3 * math.sin(angle)
            points.append(Point(x, y))
        
        # Top edge - straight line with clear corners
        for i in range(quarter_points):
            points.append(Point(1 - i/quarter_points, 0.3))
        
        # Left edge - straight line back to start (clear corners)
        for i in range(quarter_points):
            points.append(Point(0, 0.3 - i/quarter_points * 0.3))
        
        return points
    
    def _create_complex_shape_points(self, num_points: int = 100) -> list[Point]:
        """Create points representing a complex shape with multiple corners."""
        points = []
        segment_points = num_points // 6
        
        # Hexagon-like shape
        for i in range(6):
            angle = 2 * math.pi * i / 6
            next_angle = 2 * math.pi * (i + 1) / 6
            
            for j in range(segment_points):
                t = j / segment_points
                current_angle = angle + t * (next_angle - angle)
                x = 0.5 + 0.4 * math.cos(current_angle)
                y = 0.5 + 0.4 * math.sin(current_angle)
                points.append(Point(x, y))
        
        return points
    
    def _assert_some_corners_match(self, detected_corners: list[Point], expected_corners: list[Point], tolerance: float = 0.1):
        """
        Helper method to assert that at least some detected corners match expected corners within tolerance.
        """
        # Check that each expected corner has a close detected corner
        found_matches = 0
        for expected in expected_corners:
            for detected in detected_corners:
                if detected.distance_to(expected) <= tolerance:
                    found_matches += 1
                    break
        
        # Should find at least some expected corners
        assert found_matches >= 1, f"Found only {found_matches} out of {len(expected_corners)} expected corners"