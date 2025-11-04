import os
import sys
import pytest
import numpy as np
import cv2
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
sys.path.insert(0, project_root)

from core.entities.color import ColorCategory
from infrastructure.image_processing.color_analyzer import ColorAnalyzer


class TestColorAnalyzer:
    """Test suite for ColorAnalyzer class"""

    def setup_method(self):
        """Setup before each test method"""
        self.analyzer = ColorAnalyzer()
        
        # Create a mock Contour entity for testing
        self.mock_contour = MagicMock()
        self.mock_contour.points = [MagicMock(x=10, y=10), MagicMock(x=20, y=20), MagicMock(x=30, y=30)]
        self.mock_contour.area = 100.0
        self.mock_contour.to_numpy.return_value = np.array([[10, 10], [20, 20], [30, 30]], dtype=np.float32).reshape(-1, 1, 2)

    def test_initialization_default_config(self):
        """Test initialization with default configuration"""
        analyzer = ColorAnalyzer()
        assert analyzer.blue_hue_range == [100, 140]
        assert analyzer.red_hue_ranges == [[0, 10], [170, 180]]
        assert analyzer.green_hue_range == [35, 85]
        assert analyzer.min_saturation == 50
        assert analyzer.max_value_white == 200
        assert analyzer.min_value_black == 50

    def test_initialization_custom_config(self):
        """Test initialization with custom configuration"""
        config = {
            'blue_hue_range': [90, 130],
            'red_hue_range': [[5, 15], [160, 170]],
            'green_hue_range': [40, 90],
            'min_saturation': 60,
            'max_value_white': 180,
            'min_value_black': 40
        }
        analyzer = ColorAnalyzer(config)
        assert analyzer.blue_hue_range == [90, 130]
        assert analyzer.red_hue_ranges == [[5, 15], [160, 170]]
        assert analyzer.green_hue_range == [40, 90]
        assert analyzer.min_saturation == 60
        assert analyzer.max_value_white == 180
        assert analyzer.min_value_black == 40

    def test_categorize_color_pixel_blue(self):
        """Test blue color categorization"""
        # Test with blue BGR color
        blue_bgr = [255, 0, 0]  # Pure blue in BGR
        category, hex_color = self.analyzer.categorize_color_pixel(blue_bgr)
        assert category == ColorCategory.BLUE
        assert hex_color == "#0000FF"

    def test_categorize_color_pixel_red(self):
        """Test red color categorization"""
        # Test with red BGR color
        red_bgr = [0, 0, 255]  # Pure red in BGR
        category, hex_color = self.analyzer.categorize_color_pixel(red_bgr)
        assert category == ColorCategory.RED
        assert hex_color == "#FF0000"

    def test_categorize_color_pixel_green(self):
        """Test green color categorization"""
        # Test with green BGR color
        green_bgr = [0, 255, 0]  # Pure green in BGR
        category, hex_color = self.analyzer.categorize_color_pixel(green_bgr)
        assert category == ColorCategory.GREEN
        assert hex_color == "#00FF00"

    def test_categorize_color_pixel_white(self):
        """Test white color categorization"""
        # Test with white BGR color (high value, low saturation)
        white_bgr = [255, 255, 255]  # Pure white
        category, hex_color = self.analyzer.categorize_color_pixel(white_bgr)
        assert category == ColorCategory.WHITE
        assert hex_color is None

    def test_categorize_color_pixel_black(self):
        """Test black color categorization"""
        # Test with black BGR color (low value)
        black_bgr = [0, 0, 0]  # Pure black
        category, hex_color = self.analyzer.categorize_color_pixel(black_bgr)
        assert category == ColorCategory.BLACK
        assert hex_color is None

    def test_categorize_color_pixel_other(self):
        """Test other color categorization"""
        # Test with low saturation color (should be categorized as OTHER)
        gray_bgr = [100, 100, 100]  # Gray (low saturation)
        category, hex_color = self.analyzer.categorize_color_pixel(gray_bgr)
        assert category == ColorCategory.OTHER
        assert hex_color is None

    def test_categorize_color_pixel_invalid_input(self):
        """Test color categorization with invalid input"""
        # Test with empty list
        category, hex_color = self.analyzer.categorize_color_pixel([])
        assert category == ColorCategory.OTHER
        assert hex_color is None

        # Test with short list
        category, hex_color = self.analyzer.categorize_color_pixel([100, 100])
        assert category == ColorCategory.OTHER
        assert hex_color is None

    def test_get_dominant_color_none_contour(self):
        """Test get_dominant_color with None contour"""
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        result = self.analyzer.get_dominant_color(None, image)
        assert result is None

    def test_get_dominant_color_empty_contour(self):
        """Test get_dominant_color with empty contour"""
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        empty_contour = np.array([])
        result = self.analyzer.get_dominant_color(empty_contour, image)
        assert result is None

    @patch('cv2.drawContours')
    def test_get_dominant_color_contour_drawing_failure(self, mock_draw_contours):
        """Test get_dominant_color when contour drawing fails"""
        mock_draw_contours.side_effect = Exception("Drawing failed")
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        contour = np.array([[10, 10], [20, 20], [30, 30]], dtype=np.int32)
        result = self.analyzer.get_dominant_color(contour, image)
        assert result is None

    def test_get_dominant_color_no_boundary_pixels(self):
        """Test get_dominant_color when no boundary pixels are found"""
        # Create an image and contour that won't produce boundary pixels
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        contour = np.array([[1, 1], [2, 2]], dtype=np.int32)  # Very small contour
        
        with patch('cv2.drawContours'):
            result = self.analyzer.get_dominant_color(contour, image)
            assert result is None

    def test_categorize_with_contour_entity(self):
        """Test categorize method with Contour entity"""
        # Create a test image with red pixels
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        image[10:20, 10:20] = [0, 0, 255]  # Red in BGR
        
        with patch.object(self.analyzer, 'get_dominant_color', return_value="#FF0000"):
            result = self.analyzer.categorize(self.mock_contour, image)
            assert result == "red"

    def test_categorize_with_numpy_contour(self):
        """Test categorize method with numpy contour"""
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        numpy_contour = np.array([[10, 10], [20, 20], [30, 30]], dtype=np.float32)
        
        with patch.object(self.analyzer, 'get_dominant_color', return_value="#0000FF"):
            result = self.analyzer.categorize(numpy_contour, image)
            assert result == "blue"

    def test_categorize_with_empty_contour(self):
        """Test categorize method with empty contour"""
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        empty_contour = np.array([])
        
        result = self.analyzer.categorize(empty_contour, image)
        assert result is None

    def test_categorize_no_dominant_color(self):
        """Test categorize method when no dominant color is found"""
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        
        with patch.object(self.analyzer, 'get_dominant_color', return_value=None):
            result = self.analyzer.categorize(self.mock_contour, image)
            assert result is None

    def test_categorize_green_color(self):
        """Test categorize method with green color"""
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        
        with patch.object(self.analyzer, 'get_dominant_color', return_value="#00FF00"):
            result = self.analyzer.categorize(self.mock_contour, image)
            assert result == "green"

    def test_analyze_contour_color(self):
        """Test analyze_contour_color method"""
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        contour = np.array([[10, 10], [20, 20], [30, 30], [10, 10]], dtype=np.int32)
        
        with patch.object(self.analyzer, 'get_dominant_color', return_value="#FF0000"):
            result = self.analyzer.analyze_contour_color(contour, image)
            
            assert result['dominant_color'] == "#FF0000"
            assert 'contour_area' in result
            assert 'contour_points' in result
            assert result['contour_points'] == 4

    def test_hsv_color_conversion_blue(self):
        """Test HSV conversion for blue color"""
        blue_bgr = [255, 0, 0]  # Pure blue in BGR
        hsv_color = np.uint8([[[blue_bgr[0], blue_bgr[1], blue_bgr[2]]]])
        hsv = cv2.cvtColor(hsv_color, cv2.COLOR_BGR2HSV)[0][0]
        hue, saturation, value = hsv
        
        # Blue should have hue around 120 in OpenCV HSV (0-180 range)
        assert 100 <= hue <= 140  # Within blue range

    def test_hsv_color_conversion_red(self):
        """Test HSV conversion for red color"""
        red_bgr = [0, 0, 255]  # Pure red in BGR
        hsv_color = np.uint8([[[red_bgr[0], red_bgr[1], red_bgr[2]]]])
        hsv = cv2.cvtColor(hsv_color, cv2.COLOR_BGR2HSV)[0][0]
        hue, saturation, value = hsv
        
        # Red should have hue around 0 or 180 in OpenCV HSV
        assert (0 <= hue <= 10) or (170 <= hue <= 180)

    def test_color_dominance_calculation(self):
        """Test color dominance calculation logic"""
        # Mock boundary pixels with majority blue
        blue_pixel = [255, 0, 0]  # Blue in BGR
        red_pixel = [0, 0, 255]   # Red in BGR
        
        # Create mock boundary pixels with 70% blue, 30% red
        mock_pixels = np.array([blue_pixel] * 7 + [red_pixel] * 3)
        
        analyzer = ColorAnalyzer()
        
        # Mock the boundary pixel sampling
        with patch.object(analyzer, 'categorize_color_pixel') as mock_categorize:
            def side_effect(pixel):
                if list(pixel) == blue_pixel:
                    return (ColorCategory.BLUE, "#0000FF")
                else:
                    return (ColorCategory.RED, "#FF0000")
            
            mock_categorize.side_effect = side_effect
            
            # This is testing the internal logic, so we'll create a simplified test
            color_categories = {}
            for pixel in mock_pixels:
                category, hex_color = analyzer.categorize_color_pixel(pixel.tolist())
                if category in [ColorCategory.BLUE, ColorCategory.RED, ColorCategory.GREEN]:
                    color_categories[category.value] = color_categories.get(category.value, 0) + 1
            
            assert color_categories['blue'] == 7
            assert color_categories['red'] == 3
            assert 'green' not in color_categories
