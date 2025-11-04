import os
import sys
import numpy as np
import cv2
from unittest.mock import patch

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
sys.path.insert(0, project_root)

from core.entities.point import Point
from infrastructure.point_detection.point_detector import PointDetector


class TestPointDetector:
    """Verify point detection logic for small, compact contours"""
    
    def setup_method(self):
        # Fresh detector for each test prevents state leakage
        self.detector = PointDetector(max_area=100, max_perimeter=80)
    
    def test_initialization(self):
        """Ensure detector starts with correct size thresholds"""
        detector = PointDetector(max_area=50, max_perimeter=40)
        assert detector.max_area == 50
        assert detector.max_perimeter == 40
    
    def test_set_config(self):
        """Allow runtime adjustment of detection parameters"""
        config = {'point_max_area': 75, 'point_max_perimeter': 60}
        self.detector.set_config(config)
        assert self.detector.max_area == 75
        assert self.detector.max_perimeter == 60
    
    def test_set_config_partial(self):
        """Maintain existing values when config is incomplete"""
        config = {'point_max_area': 75}
        self.detector.set_config(config)
        # Perimeter unchanged because not in config
        assert self.detector.max_perimeter == 80
    
    def test_is_point_valid_contour(self):
        """Accept contours that meet both size criteria"""
        contour = np.array([[[10, 10]], [[12, 10]], [[12, 12]], [[10, 12]]], dtype=np.int32)
        
        with patch.object(cv2, 'contourArea', return_value=50), \
             patch.object(cv2, 'arcLength', return_value=30):
            
            assert self.detector.is_point(contour) is True
    
    def test_is_point_too_large_area(self):
        """Reject contours that exceed area threshold"""
        contour = np.array([[[0, 0]], [[20, 0]], [[20, 20]], [[0, 20]]], dtype=np.int32)
        
        with patch.object(cv2, 'contourArea', return_value=150), \
             patch.object(cv2, 'arcLength', return_value=30):
            
            assert self.detector.is_point(contour) is False
    
    def test_is_point_too_large_perimeter(self):
        """Reject contours that exceed perimeter threshold"""
        contour = np.array([[[0, 0]], [[20, 0]], [[20, 20]], [[0, 20]]], dtype=np.int32)
        
        with patch.object(cv2, 'contourArea', return_value=50), \
             patch.object(cv2, 'arcLength', return_value=100):
            
            assert self.detector.is_point(contour) is False
    
    def test_is_point_invalid_contour(self):
        """Reject degenerate contours that cannot form shapes"""
        invalid_contour = np.array([[[10, 10]], [[12, 10]]], dtype=np.int32)
        assert self.detector.is_point(invalid_contour) is False
    
    def test_get_center_valid_contour(self):
        """Calculate geometric center using moment analysis"""
        contour = np.array([[[0, 0]], [[10, 0]], [[10, 10]], [[0, 10]]], dtype=np.int32)
        
        center = self.detector.get_center(contour)
        
        assert center.x == 5  # Centroid of rectangle
        assert center.y == 5
    
    def test_get_center_invalid_contour(self):
        """Avoid center calculation for invalid contours"""
        invalid_contour = np.array([[[10, 10]], [[12, 10]]], dtype=np.int32)
        assert self.detector.get_center(invalid_contour) is None
    
    def test_get_center_zero_moment(self):
        """Handle edge case where contour has no area"""
        contour = np.array([[[0, 0]], [[10, 0]], [[10, 10]], [[0, 10]]], dtype=np.int32)
        
        with patch.object(cv2, 'moments') as mock_moments:
            mock_moments.return_value = {'m00': 0, 'm10': 100, 'm01': 100}
            assert self.detector.get_center(contour) is None
    
    def test_detect_point_valid(self):
        """Complete pipeline: validate contour and return center"""
        contour = np.array([[[5, 5]], [[7, 5]], [[7, 7]], [[5, 7]]], dtype=np.int32)
        
        with patch.object(cv2, 'contourArea', return_value=50), \
             patch.object(cv2, 'arcLength', return_value=30), \
             patch.object(cv2, 'moments') as mock_moments:
            
            mock_moments.return_value = {'m00': 1, 'm10': 6, 'm01': 6}
            point = self.detector.detect_point(contour)
            
            assert point.x == 6
            assert point.y == 6
    
    def test_detect_point_invalid(self):
        """Return None when contour fails point criteria"""
        contour = np.array([[[0, 0]], [[20, 0]], [[20, 20]], [[0, 20]]], dtype=np.int32)
        
        with patch.object(cv2, 'contourArea', return_value=150), \
             patch.object(cv2, 'arcLength', return_value=30):
            
            assert self.detector.detect_point(contour) is None
    
    def test_get_contour_center(self):
        """Provide center calculation without point validation"""
        contour = np.array([[[0, 0]], [[8, 0]], [[8, 8]], [[0, 8]]], dtype=np.int32)
        
        center = self.detector.get_contour_center(contour)
        
        assert center.x == 4  # Useful for larger shapes beyond points
        assert center.y == 4
    
    def test_create_point_marker(self):
        """Generate SVG-compatible representation for rendering"""
        center = Point(10, 15)
        marker = self.detector.create_point_marker(center, radius=5)
        
        assert marker == {
            'type': 'circle',
            'cx': 10,
            'cy': 15,
            'r': 5
        }


class TestPointDetectorIntegration:
    """Verify detector works with actual OpenCV operations"""
    
    def setup_method(self):
        self.detector = PointDetector(max_area=100, max_perimeter=80)
    
    def test_real_contour_detection(self):
        """Ensure mathematical correctness with real contour calculations"""
        image = np.zeros((100, 100), dtype=np.uint8)
        cv2.circle(image, (50, 50), 3, 255, -1)
        
        contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            contour = contours[0]
            center = self.detector.detect_point(contour)
            
            # Small circle should be detected as point with correct center
            assert center is not None
            assert abs(center.x - 50) <= 2  # Allow small calculation tolerance
            assert abs(center.y - 50) <= 2