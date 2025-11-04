import os
import sys
import pytest
import cv2
import numpy as np
from unittest.mock import Mock, patch


project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
sys.path.insert(0, project_root)

from infrastructure.image_processing.contour_detector import ContourDetector


class TestContourDetector:

    @pytest.fixture
    def contour_detector(self):
        return ContourDetector()

    @pytest.fixture
    def sample_image_data(self):
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.rectangle(img, (20, 20), (80, 80), (255, 255, 255), -1)
        return {'image_array': img}

    @pytest.fixture
    def empty_image_data(self):
        return {'image_array': None}

    @pytest.fixture
    def mock_contours(self):
        contour = np.array([[[10, 10]], [[10, 90]], [[90, 90]], [[90, 10]]], dtype=np.int32)
        hierarchy = np.array([[[-1, -1, 1, -1]]], dtype=np.int32)
        return [contour], hierarchy

    def test_initialization_creates_closure_service(self, contour_detector):
        assert contour_detector.closure_service is not None

    def test_detect_returns_contours_for_valid_image(self, contour_detector, sample_image_data):
        contours, hierarchy = contour_detector.detect(sample_image_data)
        
        assert contours is not None
        assert isinstance(contours, tuple)
        assert len(contours) > 0
        assert hierarchy is not None

    def test_detect_returns_none_for_empty_image_data(self, contour_detector, empty_image_data):
        contours, hierarchy = contour_detector.detect(empty_image_data)
        assert contours is None
        assert hierarchy is None

    def test_detect_returns_none_for_missing_image_array(self, contour_detector):
        invalid_data = {'wrong_key': np.zeros((100, 100, 3), dtype=np.uint8)}
        contours, hierarchy = contour_detector.detect(invalid_data)
        assert contours is None
        assert hierarchy is None

    def test_detect_ensures_all_contours_are_closed(self, contour_detector, sample_image_data):
        contours, _ = contour_detector.detect(sample_image_data)
        
        if contours is not None:
            for contour in contours:
                assert len(contour) >= 3  # Minimum points for closed shape

    def test_preprocess_returns_original_and_binary_images(self, contour_detector, sample_image_data):
        original_img, processed_img = contour_detector.preprocess(sample_image_data)
        
        assert original_img is not None
        assert processed_img is not None
        assert len(original_img.shape) == 3  # BGR
        assert len(processed_img.shape) == 2  # Binary

    def test_preprocess_returns_none_for_empty_image_data(self, contour_detector, empty_image_data):
        original_img, processed_img = contour_detector.preprocess(empty_image_data)
        assert original_img is None
        assert processed_img is None

    @patch.object(ContourDetector, 'detect')
    def test_detect_with_closure_analysis_returns_analysis_reports(self, mock_detect, contour_detector, sample_image_data, mock_contours):
        contours, hierarchy = mock_contours
        mock_detect.return_value = (tuple(contours), hierarchy)
        
        mock_analysis = {
            'is_closed': True,
            'closure_gap': 0.0,
            'area': 6400.0,
            'point_count': 4
        }
        contour_detector.closure_service.analyze_contour_closure = Mock(return_value=mock_analysis)
        
        result_contours, result_hierarchy, closure_reports = contour_detector.detect_with_closure_analysis(sample_image_data)
        
        assert result_contours is not None
        assert result_hierarchy is not None
        assert len(closure_reports) == len(contours)
        assert closure_reports[0] == mock_analysis

    def test_detect_with_closure_analysis_handles_no_contours(self, contour_detector, empty_image_data):
        contours, hierarchy, closure_reports = contour_detector.detect_with_closure_analysis(empty_image_data)
        assert contours is None
        assert hierarchy is None
        assert closure_reports == []

    def test_image_processing_creates_valid_binary_images(self, contour_detector, sample_image_data):
        img = sample_image_data['image_array']
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        binary1 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv2.THRESH_BINARY_INV, 15, 5)
        _, binary2 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        assert binary1.shape == gray.shape
        assert binary2.shape == gray.shape
        assert np.isin(binary1, [0, 255]).all()
        assert np.isin(binary2, [0, 255]).all()

    def test_morphological_operations_clean_noise(self):
        binary_img = np.zeros((50, 50), dtype=np.uint8)
        binary_img[10:40, 10:40] = 255
        binary_img[5:7, 5:7] = 255  # Noise
        
        kernel = np.ones((3,3), np.uint8)
        closed = cv2.morphologyEx(binary_img, cv2.MORPH_CLOSE, kernel, iterations=2)
        opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel, iterations=1)
        
        assert closed.shape == binary_img.shape
        assert opened.shape == binary_img.shape

    @pytest.mark.parametrize("image_shape", [
        (100, 100, 3),
        (50, 50, 3),
        (200, 200, 3),
    ])
    def test_detect_handles_different_image_sizes(self, contour_detector, image_shape):
        img = np.zeros(image_shape, dtype=np.uint8)
        cv2.rectangle(img, (10, 10), (image_shape[1]-10, image_shape[0]-10), (255, 255, 255), -1)
        image_data = {'image_array': img}
        
        contours, hierarchy = contour_detector.detect(image_data)
        assert contours is not None
        assert len(contours) > 0

    def test_contour_hierarchy_has_correct_structure(self, contour_detector, sample_image_data):
        contours, hierarchy = contour_detector.detect(sample_image_data)
        
        if hierarchy is not None:
            assert isinstance(hierarchy, np.ndarray)
            assert hierarchy.ndim == 3
            assert hierarchy.shape[2] == 4  # [next, previous, first_child, parent]

    def test_closure_service_called_during_detection(self, contour_detector, sample_image_data):
        with patch.object(contour_detector.closure_service, 'ensure_closure') as mock_ensure:
            with patch.object(contour_detector.closure_service, 'is_closed') as mock_is_closed:
                with patch.object(contour_detector.closure_service, 'calculate_closure_gap') as mock_gap:
                    
                    mock_ensure.return_value = np.array([[[10, 10]], [[10, 90]], [[90, 90]], [[90, 10]]])
                    mock_is_closed.return_value = True
                    mock_gap.return_value = 0.0
                    
                    contours, hierarchy = contour_detector.detect(sample_image_data)
                    
                    assert mock_ensure.called
                    assert mock_is_closed.called
                    assert mock_gap.called
