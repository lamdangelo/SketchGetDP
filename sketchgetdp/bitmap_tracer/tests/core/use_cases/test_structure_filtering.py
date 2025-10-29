import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
sys.path.insert(0, project_root)

import pytest
from unittest.mock import Mock, patch

from core.entities.contour import Contour
from core.use_cases.structure_filtering import StructureFilteringUseCase


class TestStructureFilteringUseCase:
    
    @pytest.fixture
    def use_case(self):
        """Fixture providing the use case instance with mocked shape processor."""
        mock_shape_processor = Mock()
        return StructureFilteringUseCase(shape_processor=mock_shape_processor)
    
    @pytest.fixture
    def use_case_no_processor(self):
        """Fixture providing the use case instance without shape processor."""
        return StructureFilteringUseCase()
    
    @pytest.fixture
    def mock_contours(self):
        """Fixture providing mock contours of different sizes."""
        small = Mock(spec=Contour)
        small.area = 50.0
        small.perimeter = 25.0
        
        medium = Mock(spec=Contour)
        medium.area = 200.0
        medium.perimeter = 50.0
        
        large = Mock(spec=Contour)
        large.area = 500.0
        large.perimeter = 80.0
        
        return small, medium, large
    
    @pytest.fixture
    def sample_structures(self):
        """Fixture providing sample structures for testing."""
        return {
            'red_points': ['red1', 'red2', 'red3', 'red4'],
            'blue_structures': ['blue1', 'blue2', 'blue3'],
            'green_structures': ['green1', 'green2']
        }

    def test_init_with_shape_processor(self, use_case):
        assert use_case.shape_processor is not None

    def test_init_without_shape_processor(self, use_case_no_processor):
        assert use_case_no_processor.shape_processor is None

    @pytest.mark.parametrize("config,expected_red,expected_blue,expected_green", [
        ({'red_dots': 2, 'blue_paths': 1, 'green_paths': 3}, 2, 1, 2),
        ({'red_dots': 0, 'blue_paths': 0, 'green_paths': 0}, 4, 3, 2),
        ({}, 4, 3, 2),
    ])
    def test_execute_applies_config_limits(self, use_case, sample_structures, config, 
                                         expected_red, expected_blue, expected_green):
        with patch('builtins.print'):
            result = use_case.execute(sample_structures, config)

        assert len(result['red_points']) == expected_red
        assert len(result['blue_structures']) == expected_blue
        assert len(result['green_structures']) == expected_green

    def test_execute_empty_structures(self, use_case):
        structures = {'red_points': [], 'blue_structures': [], 'green_structures': []}
        config = {'red_dots': 5, 'blue_paths': 5, 'green_paths': 5}

        result = use_case.execute(structures, config)

        assert result['red_points'] == []
        assert result['blue_structures'] == []
        assert result['green_structures'] == []

    def test_execute_handles_malformed_input_gracefully(self, use_case):
        structures = {'invalid_key': 'invalid_value'}
        config = {'invalid_config': 'value'}

        with patch('builtins.print'), patch('traceback.print_exc') as mock_traceback:
            result = use_case.execute(structures, config)

        expected = {'red_points': [], 'blue_structures': [], 'green_structures': []}
        assert result == expected
        mock_traceback.assert_not_called()

    def test_execute_partial_structures_applies_limits_to_present_keys(self, use_case):
        structures = {'red_points': ['red1', 'red2'], 'invalid_key': 'invalid_value'}
        config = {'red_dots': 1}

        with patch('builtins.print'):
            result = use_case.execute(structures, config)

        assert len(result['red_points']) == 1
        assert result['blue_structures'] == []
        assert result['green_structures'] == []

    def test_execute_returns_original_structures_on_exception(self, use_case):
        class FaultyStructures:
            def get(self, key, default=None):
                raise Exception("Simulated error")

        structures = FaultyStructures()
        config = {'red_dots': 1, 'blue_paths': 1, 'green_paths': 1}

        with patch('builtins.print') as mock_print, patch('traceback.print_exc') as mock_traceback:
            result = use_case.execute(structures, config)

        assert result == structures
        mock_print.assert_called_with("❌ Structure filtering error: Simulated error")
        mock_traceback.assert_called_once()

    @pytest.mark.parametrize("structures,max_count,expected", [
        ([(100.0, 'large'), (50.0, 'medium'), (10.0, 'small'), (5.0, 'tiny')], 2, 2),
        ([(100.0, 'struct1'), (50.0, 'struct2')], 0, 0),
        ([(100.0, 'struct1'), (50.0, 'struct2')], 5, 2),
    ])
    def test_filter_structures_by_area_limits_count(self, use_case, structures, max_count, expected):
        result = use_case.filter_structures_by_area(structures, max_count)
        assert len(result) == expected

    @pytest.mark.parametrize("contours,min_area,max_area,expected_count", [
        (['small', 'medium', 'large'], 100.0, 300.0, 1),
        (['small', 'large'], 1000.0, 2000.0, 0),
        ([], 100.0, 300.0, 0),
    ])
    def test_filter_contours_by_size_keeps_contours_in_range(self, use_case, mock_contours, 
                                                           contours, min_area, max_area, expected_count):
        # Map string references to actual mock contours
        contour_map = {
            'small': mock_contours[0],
            'medium': mock_contours[1], 
            'large': mock_contours[2]
        }
        contour_list = [contour_map[c] for c in contours]
        
        result = use_case.filter_contours_by_size(contour_list, min_area, max_area)
        assert len(result) == expected_count

    def test_filter_by_circularity_keeps_contours_above_threshold(self, use_case):
        high_circularity = Mock(spec=Contour)
        high_circularity.area = 78.54
        high_circularity.perimeter = 31.42
        
        low_circularity = Mock(spec=Contour)
        low_circularity.area = 100.0
        low_circularity.perimeter = 100.0
        
        contours = [high_circularity, low_circularity]
        min_circularity = 0.8

        result = use_case.filter_by_circularity(contours, min_circularity)

        assert len(result) == 1
        assert result[0] == high_circularity

    def test_filter_by_circularity_handles_zero_perimeter(self, use_case):
        zero_perimeter_contour = Mock(spec=Contour)
        zero_perimeter_contour.area = 100.0
        zero_perimeter_contour.perimeter = 0.0
        
        contours = [zero_perimeter_contour]
        min_circularity = 0.1

        result = use_case.filter_by_circularity(contours, min_circularity)

        assert result == []

    @pytest.mark.parametrize("descending,expected_order", [
        (True, ['large', 'medium', 'small']),
        (False, ['small', 'medium', 'large']),
    ])
    def test_sort_contours_by_area(self, use_case, mock_contours, descending, expected_order):
        # Create a list in mixed order
        contours = [mock_contours[0], mock_contours[2], mock_contours[1]]  # small, large, medium
        
        result = use_case.sort_contours_by_area(contours, descending=descending)
        
        # Map expected order string to actual mock contours
        order_map = {
            'small': mock_contours[0],
            'medium': mock_contours[1],
            'large': mock_contours[2]
        }
        expected_result = [order_map[name] for name in expected_order]
        
        assert result == expected_result

    def test_sort_contours_by_area_empty_list(self, use_case):
        result = use_case.sort_contours_by_area([], descending=True)
        assert result == []

    def test_filter_top_level_contours_placeholder(self, use_case, mock_contours):
        contours = [mock_contours[0], mock_contours[1]]
        hierarchy_data = Mock()

        result = use_case.filter_top_level_contours(contours, hierarchy_data)

        assert result == contours

    def test_categorize_structures_by_color_placeholder(self, use_case, mock_contours):
        contours = [mock_contours[0], mock_contours[1]]
        original_image = Mock()

        result = use_case.categorize_structures_by_color(contours, original_image)

        assert result == {}