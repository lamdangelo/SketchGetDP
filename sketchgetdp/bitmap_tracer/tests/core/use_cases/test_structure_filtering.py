import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
sys.path.insert(0, project_root)

import pytest
from unittest.mock import Mock, patch

from core.entities.contour import Contour
from core.use_cases.structure_filtering import StructureFilteringUseCase


class TestStructureFilteringUseCase:
    
    def setup_method(self):
        self.mock_shape_processor = Mock()
        self.use_case = StructureFilteringUseCase(shape_processor=self.mock_shape_processor)
        
        self.mock_contour_small = Mock(spec=Contour)
        self.mock_contour_small.area = 50.0
        self.mock_contour_small.perimeter = 25.0
        
        self.mock_contour_medium = Mock(spec=Contour)
        self.mock_contour_medium.area = 200.0
        self.mock_contour_medium.perimeter = 50.0
        
        self.mock_contour_large = Mock(spec=Contour)
        self.mock_contour_large.area = 500.0
        self.mock_contour_large.perimeter = 80.0

    def test_init_with_shape_processor(self):
        use_case = StructureFilteringUseCase(shape_processor=self.mock_shape_processor)
        assert use_case.shape_processor == self.mock_shape_processor

    def test_init_without_shape_processor(self):
        use_case = StructureFilteringUseCase()
        assert use_case.shape_processor is None

    def test_execute_applies_config_limits(self):
        structures = {
            'red_points': ['red1', 'red2', 'red3', 'red4'],
            'blue_structures': ['blue1', 'blue2', 'blue3'],
            'green_structures': ['green1', 'green2']
        }
        config = {'red_dots': 2, 'blue_paths': 1, 'green_paths': 3}

        with patch('builtins.print'):
            result = self.use_case.execute(structures, config)

        assert len(result['red_points']) == 2
        assert len(result['blue_structures']) == 1
        assert len(result['green_structures']) == 2

    def test_execute_no_limits_when_config_zero(self):
        structures = {
            'red_points': ['red1', 'red2'],
            'blue_structures': ['blue1'],
            'green_structures': ['green1']
        }
        config = {'red_dots': 0, 'blue_paths': 0, 'green_paths': 0}

        result = self.use_case.execute(structures, config)

        assert len(result['red_points']) == 2
        assert len(result['blue_structures']) == 1
        assert len(result['green_structures']) == 1

    def test_execute_empty_structures(self):
        structures = {'red_points': [], 'blue_structures': [], 'green_structures': []}
        config = {'red_dots': 5, 'blue_paths': 5, 'green_paths': 5}

        result = self.use_case.execute(structures, config)

        assert result['red_points'] == []
        assert result['blue_structures'] == []
        assert result['green_structures'] == []

    def test_execute_handles_malformed_input_gracefully(self):
        structures = {'invalid_key': 'invalid_value'}
        config = {'invalid_config': 'value'}

        with patch('builtins.print'), patch('traceback.print_exc') as mock_traceback:
            result = self.use_case.execute(structures, config)

        expected = {'red_points': [], 'blue_structures': [], 'green_structures': []}
        assert result == expected
        mock_traceback.assert_not_called()

    def test_execute_partial_structures_applies_limits_to_present_keys(self):
        structures = {'red_points': ['red1', 'red2'], 'invalid_key': 'invalid_value'}
        config = {'red_dots': 1}

        with patch('builtins.print'):
            result = self.use_case.execute(structures, config)

        assert len(result['red_points']) == 1
        assert result['blue_structures'] == []
        assert result['green_structures'] == []

    def test_execute_missing_config_keys_uses_defaults(self):
        structures = {
            'red_points': ['red1', 'red2', 'red3'],
            'blue_structures': ['blue1', 'blue2'],
            'green_structures': ['green1']
        }
        config = {}

        result = self.use_case.execute(structures, config)

        assert len(result['red_points']) == 3
        assert len(result['blue_structures']) == 2
        assert len(result['green_structures']) == 1

    def test_execute_returns_original_structures_on_exception(self):
        class FaultyStructures:
            def get(self, key, default=None):
                raise Exception("Simulated error")

        structures = FaultyStructures()
        config = {'red_dots': 1, 'blue_paths': 1, 'green_paths': 1}

        with patch('builtins.print') as mock_print, patch('traceback.print_exc') as mock_traceback:
            result = self.use_case.execute(structures, config)

        assert result == structures
        mock_print.assert_any_call("❌ Structure filtering error: Simulated error")
        mock_traceback.assert_called_once()

    def test_filter_structures_by_area_limits_count(self):
        structures = [
            (100.0, 'large'),
            (50.0, 'medium'), 
            (10.0, 'small'),
            (5.0, 'tiny')
        ]
        max_count = 2

        result = self.use_case.filter_structures_by_area(structures, max_count)

        assert len(result) == 2
        assert result[0] == (100.0, 'large')
        assert result[1] == (50.0, 'medium')

    def test_filter_structures_by_area_zero_max_returns_empty(self):
        structures = [(100.0, 'struct1'), (50.0, 'struct2')]
        max_count = 0

        result = self.use_case.filter_structures_by_area(structures, max_count)

        assert result == []

    def test_filter_structures_by_area_no_filtering_when_under_limit(self):
        structures = [(100.0, 'struct1'), (50.0, 'struct2')]
        max_count = 5

        result = self.use_case.filter_structures_by_area(structures, max_count)

        assert len(result) == 2
        assert result[0][0] == 100.0
        assert result[1][0] == 50.0

    def test_filter_contours_by_size_keeps_contours_in_range(self):
        contours = [self.mock_contour_small, self.mock_contour_medium, self.mock_contour_large]
        min_area = 100.0
        max_area = 300.0

        result = self.use_case.filter_contours_by_size(contours, min_area, max_area)

        assert len(result) == 1
        assert result[0] == self.mock_contour_medium

    def test_filter_contours_by_size_returns_empty_when_all_outside_range(self):
        contours = [self.mock_contour_small, self.mock_contour_large]
        min_area = 1000.0
        max_area = 2000.0

        result = self.use_case.filter_contours_by_size(contours, min_area, max_area)

        assert result == []

    def test_filter_contours_by_size_empty_input(self):
        contours = []
        min_area = 100.0
        max_area = 300.0

        result = self.use_case.filter_contours_by_size(contours, min_area, max_area)

        assert result == []

    def test_filter_by_circularity_keeps_contours_above_threshold(self):
        high_circularity = Mock(spec=Contour)
        high_circularity.area = 78.54
        high_circularity.perimeter = 31.42
        
        low_circularity = Mock(spec=Contour)
        low_circularity.area = 100.0
        low_circularity.perimeter = 100.0
        
        contours = [high_circularity, low_circularity]
        min_circularity = 0.8

        result = self.use_case.filter_by_circularity(contours, min_circularity)

        assert len(result) == 1
        assert result[0] == high_circularity

    def test_filter_by_circularity_handles_zero_perimeter(self):
        zero_perimeter_contour = Mock(spec=Contour)
        zero_perimeter_contour.area = 100.0
        zero_perimeter_contour.perimeter = 0.0
        
        contours = [zero_perimeter_contour]
        min_circularity = 0.1

        result = self.use_case.filter_by_circularity(contours, min_circularity)

        assert result == []

    def test_sort_contours_by_area_descending(self):
        contours = [self.mock_contour_small, self.mock_contour_large, self.mock_contour_medium]

        result = self.use_case.sort_contours_by_area(contours, descending=True)

        assert result == [self.mock_contour_large, self.mock_contour_medium, self.mock_contour_small]

    def test_sort_contours_by_area_ascending(self):
        contours = [self.mock_contour_large, self.mock_contour_small, self.mock_contour_medium]

        result = self.use_case.sort_contours_by_area(contours, descending=False)

        assert result == [self.mock_contour_small, self.mock_contour_medium, self.mock_contour_large]

    def test_sort_contours_by_area_empty_list(self):
        contours = []

        result = self.use_case.sort_contours_by_area(contours, descending=True)

        assert result == []

    def test_filter_top_level_contours_placeholder(self):
        contours = [self.mock_contour_small, self.mock_contour_medium]
        hierarchy_data = Mock()

        result = self.use_case.filter_top_level_contours(contours, hierarchy_data)

        assert result == contours

    def test_categorize_structures_by_color_placeholder(self):
        contours = [self.mock_contour_small, self.mock_contour_medium]
        original_image = Mock()

        result = self.use_case.categorize_structures_by_color(contours, original_image)

        assert result == {}
