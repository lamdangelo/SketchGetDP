import pytest
import numpy as np
from unittest.mock import Mock, MagicMock, patch
from typing import List, Dict, Optional
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
sys.path.insert(0, project_root)

# Import the use case and entities
from bitmap_tracer.core.use_cases.image_tracing import ImageTracingUseCase
from bitmap_tracer.core.entities.point import Point
from bitmap_tracer.core.entities.contour import Contour
from bitmap_tracer.core.entities.color import ColorCategory


class TestImageTracingUseCase:
    """Test suite for ImageTracingUseCase"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mocked dependencies for the use case"""
        contour_detector = Mock()
        color_analyzer = Mock()
        point_detector = Mock()
        
        return {
            'contour_detector': contour_detector,
            'color_analyzer': color_analyzer,
            'point_detector': point_detector
        }
    
    @pytest.fixture
    def use_case(self, mock_dependencies):
        """Create use case instance with mocked dependencies"""
        return ImageTracingUseCase(
            contour_detector=mock_dependencies['contour_detector'],
            color_analyzer=mock_dependencies['color_analyzer'],
            point_detector=mock_dependencies['point_detector']
        )
    
    @pytest.fixture
    def sample_image_data(self):
        """Sample image data for testing"""
        return {
            'image_array': np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8),
            'filename': 'test_image.png',
            'width': 100,
            'height': 100
        }
    
    @pytest.fixture
    def sample_config(self):
        """Sample configuration for testing"""
        return {
            'point_max_area': 2000,
            'point_max_perimeter': 165,
            'angle_threshold': 25,
            'min_curve_angle': 120
        }
    
    @pytest.fixture
    def sample_contours(self):
        """Create sample contours for testing"""
        contour1 = Mock(spec=Contour)
        contour1.points = [Point(10, 10), Point(20, 10), Point(15, 20)]
        contour1.area = 50.0
        contour1.perimeter = 30.0
        contour1.get_center.return_value = Point(15, 13.3)
        contour1.center = (15, 13.3)
        
        contour2 = Mock(spec=Contour)
        contour2.points = [Point(50, 50), Point(60, 50), Point(55, 60)]
        contour2.area = 50.0
        contour2.perimeter = 30.0
        contour2.get_center.return_value = Point(55, 53.3)
        contour2.center = (55, 53.3)
        
        return [contour1, contour2]
    
    @pytest.fixture
    def sample_raw_contours(self):
        """Create sample raw OpenCV contours"""
        contour1 = np.array([[[10, 10]], [[20, 10]], [[15, 20]]], dtype=np.int32)
        contour2 = np.array([[[50, 50]], [[60, 50]], [[55, 60]]], dtype=np.int32)
        return (contour1, contour2), None  # contours, hierarchy

    def test_initialization(self, mock_dependencies):
        """Test use case initialization with dependencies"""
        use_case = ImageTracingUseCase(
            contour_detector=mock_dependencies['contour_detector'],
            color_analyzer=mock_dependencies['color_analyzer'],
            point_detector=mock_dependencies['point_detector']
        )
        
        assert use_case.contour_detector == mock_dependencies['contour_detector']
        assert use_case.color_analyzer == mock_dependencies['color_analyzer']
        assert use_case.point_detector == mock_dependencies['point_detector']
    
    def test_initialization_without_dependencies(self):
        """Test use case initialization without dependencies"""
        use_case = ImageTracingUseCase()
        
        assert use_case.contour_detector is None
        assert use_case.color_analyzer is None
        assert use_case.point_detector is None
    
    def test_execute_successful_tracing(self, use_case, mock_dependencies, sample_image_data, sample_config):
        """Test successful execution of image tracing workflow"""
        raw_contours = (
            np.array([[[10, 10]], [[20, 10]], [[15, 20]]], dtype=np.int32),
            np.array([[[50, 50]], [[60, 50]], [[55, 60]]], dtype=np.int32)
        )
        mock_dependencies['contour_detector'].detect.return_value = (raw_contours, None)
        mock_dependencies['color_analyzer'].categorize.side_effect = ['red', 'blue']
        

        mock_dependencies['point_detector'].detect_point.side_effect = [
            Point(15, 13),
            None
        ]
        
        with patch.object(use_case, '_convert_to_contour_entity') as mock_convert:
            mock_contour1 = Mock(spec=Contour)
            mock_contour1.points = [Point(10, 10), Point(20, 10), Point(15, 20)]
            mock_contour1.area = 50.0
            mock_contour1.perimeter = 30.0
            mock_contour1.get_center.return_value = Point(15, 13.3)
            
            mock_contour2 = Mock(spec=Contour)
            mock_contour2.points = [Point(50, 50), Point(60, 50), Point(55, 60)]
            mock_contour2.area = 50.0
            mock_contour2.perimeter = 30.0
            mock_contour2.get_center.return_value = Point(55, 53.3)
            
            mock_convert.side_effect = [mock_contour1, mock_contour2]
            
            result = use_case.execute(sample_image_data, sample_config)
        
        assert result['success'] is True
        assert len(result['structures']['red_points']) == 1
        assert len(result['structures']['blue_structures']) == 1
        assert len(result['structures']['green_structures']) == 0
        assert result['total_contours'] == 2
        assert result['processed_contours'] == 2
        
        # Verify dependency calls
        mock_dependencies['contour_detector'].detect.assert_called_once_with(sample_image_data)
        assert mock_dependencies['color_analyzer'].categorize.call_count == 2
        assert mock_dependencies['point_detector'].detect_point.call_count == 2
    
    def test_execute_with_no_contours(self, use_case, mock_dependencies, sample_image_data, sample_config):
        """Test execution when no contours are found"""
        mock_dependencies['contour_detector'].detect.return_value = (None, None)
        
        result = use_case.execute(sample_image_data, sample_config)
        
        assert result['success'] is True
        assert len(result['structures']['red_points']) == 0
        assert len(result['structures']['blue_structures']) == 0
        assert len(result['structures']['green_structures']) == 0
        assert result['total_contours'] == 0
        assert result['processed_contours'] == 0
    
    def test_execute_with_empty_contours(self, use_case, mock_dependencies, sample_image_data, sample_config):
        """Test execution when empty contours are returned"""
        mock_dependencies['contour_detector'].detect.return_value = ((), None)
        
        result = use_case.execute(sample_image_data, sample_config)
        
        assert result['success'] is True
        assert len(result['structures']['red_points']) == 0
        assert len(result['structures']['blue_structures']) == 0
        assert len(result['structures']['green_structures']) == 0
        assert result['total_contours'] == 0
        assert result['processed_contours'] == 0
    
    def test_execute_with_exception(self, use_case, mock_dependencies, sample_image_data, sample_config):
        """Test execution when an exception occurs"""
        mock_dependencies['contour_detector'].detect.side_effect = Exception("Detection failed")
        
        result = use_case.execute(sample_image_data, sample_config)
        
        assert result['success'] is False
        assert "Detection failed" in result['error']
        assert len(result['structures']['red_points']) == 0
        assert len(result['structures']['blue_structures']) == 0
        assert len(result['structures']['green_structures']) == 0
        assert result['total_contours'] == 0
        assert result['processed_contours'] == 0
    
    def test_detect_contours_success(self, use_case, mock_dependencies, sample_image_data):
        """Test successful contour detection"""
        raw_contours = (np.array([[[10, 10]], [[20, 10]], [[15, 20]]], dtype=np.int32),)
        mock_dependencies['contour_detector'].detect.return_value = (raw_contours, None)
        
        with patch.object(use_case, '_convert_to_contour_entity') as mock_convert:
            mock_contour = Mock(spec=Contour)
            mock_convert.return_value = mock_contour
            
            contours = use_case.detect_contours(sample_image_data)
        
        assert len(contours) == 1
        mock_dependencies['contour_detector'].detect.assert_called_once_with(sample_image_data)
        mock_convert.assert_called_once()
    
    def test_detect_contours_no_detector(self, sample_image_data):
        """Test contour detection when no detector is available"""
        use_case = ImageTracingUseCase()  # No dependencies
        
        contours = use_case.detect_contours(sample_image_data)
        
        assert contours == []
    
    def test_detect_contours_none_result(self, use_case, mock_dependencies, sample_image_data):
        """Test contour detection when detector returns None"""
        mock_dependencies['contour_detector'].detect.return_value = (None, None)
        
        contours = use_case.detect_contours(sample_image_data)
        
        assert contours == []
    
    def test_detect_contours_empty_result(self, use_case, mock_dependencies, sample_image_data):
        """Test contour detection when detector returns empty result"""
        mock_dependencies['contour_detector'].detect.return_value = ([], None)
        
        contours = use_case.detect_contours(sample_image_data)
        
        assert contours == []
    
    def test_ensure_contour_closure(self, use_case):
        """Test contour closure method (currently returns the same contour)"""
        contour = Mock(spec=Contour)
        
        result = use_case.ensure_contour_closure(contour, tolerance=5.0)
        
        assert result == contour
    
    def test_fit_curves_to_contour_insufficient_points(self, use_case):
        """Test curve fitting with insufficient contour points"""
        contour = Mock(spec=Contour)
        contour.points = [Point(1, 1), Point(2, 2)]
        
        result = use_case.fit_curves_to_contour(contour)
        
        assert result is None
    
    def test_fit_curves_to_contour_sufficient_points(self, use_case):
        """Test curve fitting with sufficient contour points"""
        contour = Mock(spec=Contour)
        contour.points = [Point(1, 1), Point(2, 2), Point(3, 1)]
        
        with patch.object(use_case, 'ensure_contour_closure') as mock_closure:
            mock_closure.return_value = contour
            
            result = use_case.fit_curves_to_contour(contour)
        
        assert result is None
        mock_closure.assert_called_once_with(contour)
    
    def test_detect_points_with_detector(self, use_case, mock_dependencies):
        """Test point detection using the point detector service"""
        contour = Mock(spec=Contour)
        contour.points = [Point(10, 10), Point(20, 10), Point(15, 20)]
        
        expected_point = Point(15, 13)
        mock_dependencies['point_detector'].detect_point.return_value = expected_point
        
        config = {'some_setting': 'value'}
        
        result = use_case.detect_points(contour, config)
        
        assert result.x == expected_point.x
        assert result.y == expected_point.y
        mock_dependencies['point_detector'].set_config.assert_called_once_with(config)
        mock_dependencies['point_detector'].detect_point.assert_called_once()
    
    def test_detect_points_with_detector_no_config(self, use_case, mock_dependencies):
        """Test point detection without providing config"""
        contour = Mock(spec=Contour)
        contour.points = [Point(10, 10), Point(20, 10), Point(15, 20)]
        
        expected_point = Point(15, 13)
        mock_dependencies['point_detector'].detect_point.return_value = expected_point
        
        result = use_case.detect_points(contour)
        
        assert result.x == expected_point.x
        assert result.y == expected_point.y

        mock_dependencies['point_detector'].set_config.assert_not_called()
        mock_dependencies['point_detector'].detect_point.assert_called_once()
    
    def test_detect_points_fallback_success(self):
        """Test fallback point detection when point detector is not available"""
        use_case = ImageTracingUseCase()
        
        contour = Mock(spec=Contour)
        contour.points = [Point(10, 10), Point(20, 10), Point(15, 20)]
        contour.area = 50.0  # Below threshold
        contour.perimeter = 30.0  # Below threshold
        contour.get_center.return_value = Point(15, 13.3)
        
        config = {
            'point_max_area': 2000,
            'point_max_perimeter': 165
        }
        
        result = use_case.detect_points(contour, config)
        
        assert result.x == 15
        assert result.y == 13.3
        contour.get_center.assert_called_once()
    
    def test_detect_points_fallback_area_too_large(self):
        """Test fallback point detection when area exceeds threshold"""
        use_case = ImageTracingUseCase()
        
        contour = Mock(spec=Contour)
        contour.points = [Point(10, 10), Point(20, 10), Point(15, 20)]
        contour.area = 3000.0  # Above threshold
        contour.perimeter = 30.0  # Below threshold
        contour.get_center.return_value = Point(15, 13.3)
        
        config = {
            'point_max_area': 2000,
            'point_max_perimeter': 165
        }
        
        result = use_case.detect_points(contour, config)
        
        assert result is None
    
    def test_detect_points_fallback_perimeter_too_large(self):
        """Test fallback point detection when perimeter exceeds threshold"""
        use_case = ImageTracingUseCase()
        
        contour = Mock(spec=Contour)
        contour.points = [Point(10, 10), Point(20, 10), Point(15, 20)]
        contour.area = 50.0  # Below threshold
        contour.perimeter = 200.0  # Above threshold
        contour.get_center.return_value = Point(15, 13.3)
        
        config = {
            'point_max_area': 2000,
            'point_max_perimeter': 165
        }
        
        result = use_case.detect_points(contour, config)
        
        assert result is None
    
    def test_detect_points_fallback_insufficient_points(self):
        """Test fallback point detection with insufficient contour points"""
        use_case = ImageTracingUseCase()
        
        contour = Mock(spec=Contour)
        contour.points = [Point(10, 10), Point(20, 10)]
        contour.area = 50.0
        contour.perimeter = 30.0
        
        config = {
            'point_max_area': 2000,
            'point_max_perimeter': 165
        }
        
        result = use_case.detect_points(contour, config)
        
        assert result is None
        contour.get_center.assert_not_called()
    
    def test_detect_points_fallback_no_center(self):
        """Test fallback point detection when contour has no center"""
        use_case = ImageTracingUseCase()
        
        contour = Mock(spec=Contour)
        contour.points = [Point(10, 10), Point(20, 10), Point(15, 20)]
        contour.area = 50.0  # Below threshold
        contour.perimeter = 30.0  # Below threshold
        contour.get_center.return_value = None
        
        config = {
            'point_max_area': 2000,
            'point_max_perimeter': 165
        }
        
        result = use_case.detect_points(contour, config)
        
        assert result is None
    
    def test_detect_points_fallback_default_config(self):
        """Test fallback point detection using default config values"""
        use_case = ImageTracingUseCase()
        
        contour = Mock(spec=Contour)
        contour.points = [Point(10, 10), Point(20, 10), Point(15, 20)]
        contour.area = 50.0  # Below default threshold
        contour.perimeter = 30.0  # Below default threshold
        contour.get_center.return_value = Point(15, 13.3)
        
        result = use_case.detect_points(contour)
        
        assert result.x == 15
        assert result.y == 13.3
    
    def test_get_contour_center(self, use_case):
        """Test getting contour center coordinates"""
        contour = Mock(spec=Contour)
        contour.center = (15.5, 25.5)
        
        result = use_case.get_contour_center(contour)
        
        assert result == (15.5, 25.5)
    
    def test_convert_to_contour_entity(self, use_case):
        """Test conversion of raw contour to Contour entity"""
        raw_contour = np.array([[[10, 10]], [[20, 10]], [[15, 20]]], dtype=np.int32)
        
        with patch('bitmap_tracer.core.use_cases.image_tracing.Contour') as MockContour:
            mock_contour = Mock(spec=Contour)
            MockContour.from_numpy_contour.return_value = mock_contour
            
            result = use_case._convert_to_contour_entity(raw_contour)
        
        assert result == mock_contour
        MockContour.from_numpy_contour.assert_called_once_with(raw_contour)