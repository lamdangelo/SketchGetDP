import os
import sys
import pytest
import numpy as np

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
sys.path.insert(0, project_root)

from infrastructure.image_processing.contour_closure_service import ContourClosureService, ClosedContour


class TestContourClosureService:
    
    @pytest.fixture
    def service(self):
        return ContourClosureService()
    
    @pytest.fixture
    def perfectly_closed_contour(self):
        return np.array([[[0, 0]], [[0, 10]], [[10, 10]], [[10, 0]], [[0, 0]]], dtype=np.float32)
    
    @pytest.fixture
    def obviously_open_contour(self):
        return np.array([[[0, 0]], [[0, 10]], [[10, 10]], [[20, 20]]], dtype=np.float32)
    
    @pytest.fixture
    def too_small_contour(self):
        return np.array([[[0, 0]], [[5, 5]]], dtype=np.float32)

    def test_ensure_closure_preserves_already_closed_contour(self, service, perfectly_closed_contour):
        result = service.ensure_closure(perfectly_closed_contour, tolerance=5.0)
        assert np.array_equal(result, perfectly_closed_contour)

    def test_ensure_closure_closes_open_contour(self, service, obviously_open_contour):
        result = service.ensure_closure(obviously_open_contour, tolerance=5.0)
        assert len(result) == len(obviously_open_contour) + 1
        assert np.array_equal(result[0], result[-1])

    def test_ensure_closure_ignores_small_contours(self, service, too_small_contour):
        result = service.ensure_closure(too_small_contour, tolerance=5.0)
        assert np.array_equal(result, too_small_contour)

    def test_ensure_closure_respects_tolerance_threshold(self, service):
        contour_with_small_gap = np.array([[[0, 0]], [[1, 0]], [[2, 0]], [[3, 0]]], dtype=np.float32)
        
        result_with_loose_tolerance = service.ensure_closure(contour_with_small_gap, tolerance=5.0)
        assert len(result_with_loose_tolerance) == len(contour_with_small_gap)
        
        result_with_tight_tolerance = service.ensure_closure(contour_with_small_gap, tolerance=2.0)
        assert len(result_with_tight_tolerance) == len(contour_with_small_gap) + 1

    def test_is_closed_returns_true_for_closed_contour(self, service, perfectly_closed_contour):
        assert service.is_closed(perfectly_closed_contour, tolerance=5.0) == True

    def test_is_closed_returns_false_for_open_contour(self, service, obviously_open_contour):
        assert service.is_closed(obviously_open_contour, tolerance=5.0) == False

    def test_is_closed_returns_false_for_insufficient_points(self, service, too_small_contour):
        assert service.is_closed(too_small_contour, tolerance=5.0) == False

    def test_calculate_closure_gap_returns_zero_for_perfectly_closed_contour(self, service, perfectly_closed_contour):
        gap = service.calculate_closure_gap(perfectly_closed_contour)
        assert gap == pytest.approx(0.0)

    def test_calculate_closure_gap_returns_correct_distance_for_open_contour(self, service, obviously_open_contour):
        gap = service.calculate_closure_gap(obviously_open_contour)
        expected_gap = np.linalg.norm(np.array([0, 0]) - np.array([20, 20]))
        assert gap == pytest.approx(expected_gap)

    def test_calculate_closure_gap_returns_infinity_for_small_contours(self, service, too_small_contour):
        gap = service.calculate_closure_gap(too_small_contour)
        assert gap == float('inf')

    def test_create_closed_contour_object_for_closed_contour(self, service, perfectly_closed_contour):
        contour_object = service.create_closed_contour_object(perfectly_closed_contour, tolerance=5.0)
        
        assert isinstance(contour_object, ClosedContour)
        assert contour_object.is_closed == True
        assert contour_object.closure_gap == pytest.approx(0.0)
        assert len(contour_object.points) == len(perfectly_closed_contour)

    def test_create_closed_contour_object_for_open_contour(self, service, obviously_open_contour):
        contour_object = service.create_closed_contour_object(obviously_open_contour, tolerance=5.0)
        
        assert isinstance(contour_object, ClosedContour)
        assert contour_object.is_closed == False
        assert contour_object.closure_gap > 5.0
        assert len(contour_object.points) == len(obviously_open_contour) + 1

    def test_analyze_contour_closure_provides_comprehensive_metrics(self, service, perfectly_closed_contour):
        analysis = service.analyze_contour_closure(perfectly_closed_contour)
        
        assert analysis['is_closed'] == True
        assert analysis['closure_gap'] == pytest.approx(0.0)
        assert analysis['point_count'] == 5
        assert analysis['needs_closure'] == False
        assert analysis['area'] > 0
        assert analysis['perimeter'] > 0

    def test_analyze_contour_closure_identifies_open_contours(self, service, obviously_open_contour):
        analysis = service.analyze_contour_closure(obviously_open_contour)
        
        assert analysis['is_closed'] == False
        assert analysis['closure_gap'] > 5.0
        assert analysis['needs_closure'] == True

    def test_analyze_contour_closure_handles_small_contours(self, service, too_small_contour):
        analysis = service.analyze_contour_closure(too_small_contour)
        
        assert analysis['is_closed'] == False
        assert analysis['closure_gap'] == float('inf')
        assert analysis['point_count'] == 2

    def test_all_methods_handle_empty_contour(self, service):
        empty_contour = np.array([], dtype=np.float32).reshape(0, 1, 2)
        
        assert len(service.ensure_closure(empty_contour)) == 0
        assert service.is_closed(empty_contour) == False
        assert service.calculate_closure_gap(empty_contour) == float('inf')
        
        analysis = service.analyze_contour_closure(empty_contour)
        assert analysis['point_count'] == 0
