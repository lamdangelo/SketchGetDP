# test_structure_filtering.py
import pytest
from unittest.mock import Mock, patch
from core.use_cases.structure_filtering import StructureFilteringUseCase


# Mock Contour class for testing
class MockContour:
    def __init__(self, area: float, perimeter: float = 10.0):
        self.area = area
        self.perimeter = perimeter


class TestStructureFilteringUseCase:
    
    def setup_method(self):
        self.use_case = StructureFilteringUseCase()
    
    def test_execute_basic_filtering(self):
        """Test basic filtering with limits"""
        structures = {
            'red_points': ['r1', 'r2', 'r3', 'r4', 'r5'],
            'blue_structures': ['b1', 'b2', 'b3'],
            'green_structures': ['g1', 'g2']
        }
        config = {'red_dots': 3, 'blue_paths': 2, 'green_paths': 1}
        
        result = self.use_case.execute(structures, config)
        
        assert len(result['red_points']) == 3
        assert len(result['blue_structures']) == 2
        assert len(result['green_structures']) == 1
    
    def test_execute_within_limits(self):
        """Test when structures are already within limits"""
        structures = {
            'red_points': ['r1', 'r2'],
            'blue_structures': ['b1'],
            'green_structures': []
        }
        config = {'red_dots': 5, 'blue_paths': 3, 'green_paths': 2}
        
        result = self.use_case.execute(structures, config)
        
        assert result['red_points'] == ['r1', 'r2']
        assert result['blue_structures'] == ['b1']
        assert result['green_structures'] == []
    
    def test_execute_zero_limits(self):
        """Test with zero limits (should not filter)"""
        structures = {
            'red_points': ['r1', 'r2'],
            'blue_structures': ['b1'],
            'green_structures': ['g1']
        }
        config = {'red_dots': 0, 'blue_paths': 0, 'green_paths': 0}
        
        result = self.use_case.execute(structures, config)
        
        assert len(result['red_points']) == 2
        assert len(result['blue_structures']) == 1
        assert len(result['green_structures']) == 1
    
    def test_execute_missing_keys(self):
        """Test with missing structure or config keys"""
        structures = {'red_points': ['r1', 'r2']}  # Missing others
        config = {'red_dots': 1}
        
        result = self.use_case.execute(structures, config)
        
        assert result['red_points'] == ['r1']
        assert 'blue_structures' in result
        assert 'green_structures' in result
    
    def test_filter_structures_by_area_basic(self):
        """Test basic area filtering"""
        structures = [
            (100.0, 'large'),
            (50.0, 'medium'),
            (25.0, 'small'),
            (10.0, 'tiny')
        ]
        
        result = self.use_case.filter_structures_by_area(structures, max_count=2)
        
        assert len(result) == 2
        assert result[0][0] == 100.0  # Largest area
        assert result[1][0] == 50.0   # Second largest
    
    def test_filter_structures_by_area_no_limit(self):
        """Test area filtering with high limit"""
        structures = [
            (100.0, 'large'),
            (50.0, 'medium')
        ]
        
        result = self.use_case.filter_structures_by_area(structures, max_count=10)
        
        assert len(result) == 2
    
    def test_filter_structures_by_area_zero_limit(self):
        """Test area filtering with zero limit"""
        structures = [
            (100.0, 'large'),
            (50.0, 'medium')
        ]
        
        result = self.use_case.filter_structures_by_area(structures, max_count=0)
        
        assert len(result) == 0
    
    def test_filter_contours_by_size_basic(self):
        """Test basic size filtering of contours"""
        contours = [
            MockContour(area=25.0),
            MockContour(area=50.0),
            MockContour(area=75.0),
            MockContour(area=100.0)
        ]
        
        result = self.use_case.filter_contours_by_size(
            contours, min_area=50.0, max_area=75.0
        )
        
        assert len(result) == 2
        assert all(50.0 <= c.area <= 75.0 for c in result)
    
    def test_filter_contours_by_size_boundary(self):
        """Test size filtering with boundary values"""
        contours = [
            MockContour(area=50.0),  # Exactly min
            MockContour(area=75.0),  # Exactly max
            MockContour(area=49.9),  # Just below min
            MockContour(area=75.1)   # Just above max
        ]
        
        result = self.use_case.filter_contours_by_size(
            contours, min_area=50.0, max_area=75.0
        )
        
        assert len(result) == 2
    
    def test_filter_by_circularity_basic(self):
        """Test basic circularity filtering"""
        # Perfect circle: area = πr², perimeter = 2πr
        # For r=5: area ≈ 78.54, perimeter ≈ 31.42
        contours = [
            MockContour(area=78.54, perimeter=31.42),  # High circularity (~1.0)
            MockContour(area=10.0, perimeter=100.0),   # Low circularity (~0.013)
        ]
        
        result = self.use_case.filter_by_circularity(contours, min_circularity=0.5)
        
        assert len(result) == 1
        assert result[0].area == 78.54
    
    def test_filter_by_circularity_default(self):
        """Test circularity filtering with default threshold"""
        contours = [
            MockContour(area=10.0, perimeter=50.0),   # Circularity ~0.05
            MockContour(area=5.0, perimeter=100.0),   # Circularity ~0.006 (below default)
        ]
        
        result = self.use_case.filter_by_circularity(contours)
        
        # Default min_circularity is 0.01
        assert len(result) == 1
    
    def test_sort_contours_by_area_descending(self):
        """Test sorting contours by area (largest first)"""
        contours = [
            MockContour(area=25.0),
            MockContour(area=100.0),
            MockContour(area=50.0)
        ]
        
        result = self.use_case.sort_contours_by_area(contours, descending=True)
        
        assert result[0].area == 100.0
        assert result[1].area == 50.0
        assert result[2].area == 25.0
    
    def test_sort_contours_by_area_ascending(self):
        """Test sorting contours by area (smallest first)"""
        contours = [
            MockContour(area=100.0),
            MockContour(area=25.0),
            MockContour(area=50.0)
        ]
        
        result = self.use_case.sort_contours_by_area(contours, descending=False)
        
        assert result[0].area == 25.0
        assert result[1].area == 50.0
        assert result[2].area == 100.0
    
    def test_sort_contours_by_area_empty(self):
        """Test sorting empty contour list"""
        contours = []
        
        result = self.use_case.sort_contours_by_area(contours, descending=True)
        
        assert len(result) == 0
    
    @patch('builtins.print')
    def test_execute_exception_handling(self, mock_print):
        """Test exception handling in execute method"""
        # Create a structure that will cause an error when trying to get length
        bad_structures = Mock()
        bad_structures.get.return_value = None
        
        config = {'red_dots': 5}
        
        # Should not raise exception, should return original structures
        result = self.use_case.execute(bad_structures, config)
        
        assert result == bad_structures
        mock_print.assert_called()
