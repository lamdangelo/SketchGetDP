import pytest
import tempfile
import os
from unittest.mock import Mock
import yaml

from svg_to_getdp.core.entities.point import Point
from svg_to_getdp.core.entities.color import Color
from svg_to_getdp.core.entities.physical_group import (
    DOMAIN_WIRE_POSITIVE, 
    DOMAIN_WIRE_NEGATIVE
)
from sketchgetdp.svg_to_getdp.infrastructure.wire_preprocessor import WirePreprocessor


@pytest.fixture
def mock_factory():
    """Create a mock Gmsh factory."""
    factory = Mock()
    factory.addPoint = Mock(return_value=1)  # Mock point tag
    factory.addPhysicalGroup = Mock()
    return factory


@pytest.fixture
def sample_wires():
    """Create sample wire data for testing."""
    return [
        (Point(0.0, 0.0), Color("red", (255, 0, 0))),
        (Point(1.0, 1.0), Color("blue", (0, 0, 255))),
        (Point(2.0, 0.0), Color("green", (0, 255, 0))),
        (Point(0.5, -1.0), Color("black", (0, 0, 0))),
    ]


@pytest.fixture
def temp_config_file():
    """Create a temporary YAML config file for testing."""
    config_data = {
        'wire_currents': {
            'wire_1': 1,
            'wire_2': -1,
            'wire_3': 1,
            'wire_4': -1
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    os.unlink(temp_path)


@pytest.fixture
def temp_empty_config_file():
    """Create a temporary empty YAML config file for testing."""
    config_data = {}
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    os.unlink(temp_path)


class TestWirePreprocessor:
    """Test suite for WirePreprocessor class."""
    
    def test_init_with_valid_config(self, mock_factory, temp_config_file):
        """Test initialization with a valid config file."""
        preprocessor = WirePreprocessor()
        preprocessor.factory = mock_factory
        preprocessor.wire_currents = preprocessor._load_wire_currents(temp_config_file)
        
        assert preprocessor.wire_currents == {
            'wire_1': 1,
            'wire_2': -1,
            'wire_3': 1,
            'wire_4': -1
        }
    
    def test_init_with_missing_config_file(self):
        """Test initialization with a non-existent config file."""
        preprocessor = WirePreprocessor()
        
        # Should handle gracefully and have empty wire_currents
        non_existent_path = "/non/existent/path/config.yaml"
        wire_currents = preprocessor._load_wire_currents(non_existent_path)
        assert wire_currents == {}
    
    def test_init_with_invalid_yaml(self):
        """Test initialization with invalid YAML file."""
        preprocessor = WirePreprocessor()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name
        
        try:
            # Should handle gracefully
            wire_currents = preprocessor._load_wire_currents(temp_path)
            assert wire_currents == {}
        finally:
            os.unlink(temp_path)
    
    def test_sort_wires(self, temp_empty_config_file):
        """Test wire sorting from top to bottom, left to right."""
        preprocessor = WirePreprocessor()
        
        wires = [
            (Point(2.0, 1.0), Color("red", (255, 0, 0))),    # Top right
            (Point(1.0, 2.0), Color("blue", (0, 0, 255))),   # Top left (highest y)
            (Point(1.0, 0.0), Color("green", (0, 255, 0))),  # Bottom left
            (Point(2.0, 1.5), Color("black", (0, 0, 0))),    # Top middle
        ]
        
        sorted_wires = preprocessor._sort_wires(wires)
        
        # Expected order: highest y first, then smallest x for same y
        expected_order = [
            (Point(1.0, 2.0), Color("blue", (0, 0, 255))),   # Highest y
            (Point(2.0, 1.5), Color("black", (0, 0, 0))),    # Second highest y
            (Point(2.0, 1.0), Color("red", (255, 0, 0))),    # Third highest y
            (Point(1.0, 0.0), Color("green", (0, 255, 0))),  # Lowest y
        ]
        
        assert len(sorted_wires) == len(expected_order)
        for (exp_point, exp_color), (act_point, act_color) in zip(expected_order, sorted_wires):
            assert exp_point.x == act_point.x
            assert exp_point.y == act_point.y
            assert exp_color.name == act_color.name
            assert exp_color.rgb == act_color.rgb
    
    def test_wire_sort_key(self):
        """Test the sort key function."""
        preprocessor = WirePreprocessor()
        
        test_cases = [
            ((Point(1.0, 2.0), Color("red", (255, 0, 0))), (-2.0, 1.0)),
            ((Point(3.0, 1.0), Color("blue", (0, 0, 255))), (-1.0, 3.0)),
            ((Point(0.0, 0.0), Color("green", (0, 255, 0))), (0.0, 0.0)),
            ((Point(2.0, 1.0), Color("black", (0, 0, 0))), (-1.0, 2.0)),
        ]
        
        for wire, expected_key in test_cases:
            assert preprocessor._wire_sort_key(wire) == expected_key
    
    def test_get_physical_group_for_wire(self, temp_config_file):
        """Test physical group assignment based on wire currents."""
        preprocessor = WirePreprocessor()
        preprocessor.wire_currents = preprocessor._load_wire_currents(temp_config_file)
        
        # Mock wire currents from temp_config_file
        assert preprocessor.wire_currents == {
            'wire_1': 1,
            'wire_2': -1,
            'wire_3': 1,
            'wire_4': -1
        }
        
        # Test positive current
        group = preprocessor._get_physical_group_for_wire(0, Color("red", (255, 0, 0)))
        assert group == DOMAIN_WIRE_POSITIVE
        
        # Test negative current
        group = preprocessor._get_physical_group_for_wire(1, Color("blue", (0, 0, 255)))
        assert group == DOMAIN_WIRE_NEGATIVE
        
        # Test invalid index (should use default from config or raise error)
        with pytest.raises(ValueError, match=r"Invalid current sign None for wire_11"):
            preprocessor._get_physical_group_for_wire(10, Color("green", (0, 255, 0)))
    
    def test_get_physical_group_with_missing_config(self, temp_empty_config_file):
        """Test physical group assignment with missing wire currents."""
        preprocessor = WirePreprocessor()
        preprocessor.wire_currents = preprocessor._load_wire_currents(temp_empty_config_file)
        
        # With empty config, all should raise ValueError
        with pytest.raises(ValueError, match=r"Invalid current sign None for wire_1"):
            preprocessor._get_physical_group_for_wire(0, Color("red", (255, 0, 0)))
    
    def test_prepare_wires_empty_list(self, mock_factory, temp_empty_config_file):
        """Test preparing with empty wire list."""
        preprocessor = WirePreprocessor()
        
        results = preprocessor.prepare_wires(mock_factory, temp_empty_config_file, [])
        assert results == {}
        
        # Verify no Gmsh calls were made
        mock_factory.addPoint.assert_not_called()
        mock_factory.addPhysicalGroup.assert_not_called()
    
    def test_prepare_wires_with_valid_data(self, mock_factory, temp_config_file, sample_wires):
        """Test preparing with valid wire data."""
        preprocessor = WirePreprocessor()
        
        # Mock sequential point tags
        mock_factory.addPoint.side_effect = [1, 2, 3, 4]
        
        results = preprocessor.prepare_wires(mock_factory, temp_config_file, sample_wires)
        
        # Check results structure
        assert len(results) == 4
        
        for i in range(4):
            assert i in results
            assert 'original_index' in results[i]
            assert 'point' in results[i]
            assert 'color' in results[i]
            assert 'gmsh_point_tag' in results[i]
            assert 'physical_group' in results[i]
            assert 'wire_name' in results[i]
            
            # Check wire name
            assert results[i]['wire_name'] == f"wire_{i + 1}"
            
            # Check point tags
            assert results[i]['gmsh_point_tag'] == i + 1
        
        # Verify Gmsh calls
        assert mock_factory.addPoint.call_count == 4
        
        # Check that addPhysicalGroup was called twice (once for positive, once for negative)
        assert mock_factory.addPhysicalGroup.call_count == 2
        
        # Check point creation parameters
        sorted_wires = preprocessor._sort_wires(sample_wires)
        for i, (point, color) in enumerate(sorted_wires):
            mock_factory.addPoint.assert_any_call(point.x, point.y, 0.0)
    
    def test_prepare_wires_sorted_order(self, mock_factory, temp_config_file):
        """Verify wires are processed in sorted order."""
        preprocessor = WirePreprocessor()
        
        wires = [
            (Point(10.0, 5.0), Color("red", (255, 0, 0))),    # Should be last (lowest y)
            (Point(5.0, 10.0), Color("blue", (0, 0, 255))),   # Should be first (highest y)
            (Point(7.0, 8.0), Color("green", (0, 255, 0))),   # Should be second
        ]
        
        mock_factory.addPoint.side_effect = [1, 2, 3]
        
        results = preprocessor.prepare_wires(mock_factory, temp_config_file, wires)
        
        # Verify processing order by checking the stored original points
        # Results are stored in processing order (which should be sorted)
        sorted_points = [
            (Point(5.0, 10.0), Color("blue", (0, 0, 255))),
            (Point(7.0, 8.0), Color("green", (0, 255, 0))),
            (Point(10.0, 5.0), Color("red", (255, 0, 0))),
        ]
        
        for i, (expected_point, expected_color) in enumerate(sorted_points):
            assert results[i]['point'].x == expected_point.x
            assert results[i]['point'].y == expected_point.y
            assert results[i]['color'].name == expected_color.name
            assert results[i]['color'].rgb == expected_color.rgb
    
    def test_get_wire_summary(self, temp_config_file):
        """Test the summary generation method."""
        preprocessor = WirePreprocessor()
        
        # Create mock results similar to what prepare_wires would produce
        mock_results = {
            0: {
                'original_index': 0,
                'point': Point(1.0, 2.0),
                'color': Color("red", (255, 0, 0)),
                'gmsh_point_tag': 1,
                'physical_group': DOMAIN_WIRE_POSITIVE,
                'wire_name': 'wire_1'
            },
            1: {
                'original_index': 1,
                'point': Point(2.0, 1.0),
                'color': Color("blue", (0, 0, 255)),
                'gmsh_point_tag': 2,
                'physical_group': DOMAIN_WIRE_NEGATIVE,
                'wire_name': 'wire_2'
            }
        }
        
        summary = preprocessor.get_wire_summary(mock_results)
        
        # Basic checks on summary content
        assert "Wire Summary (sorted order):" in summary
        assert "Wire 1:" in summary
        assert "Wire 2:" in summary
        assert "Position: (1.000, 2.000)" in summary
        assert "Position: (2.000, 1.000)" in summary
        assert "Color: red" in summary
        assert "Color: blue" in summary
        assert "Wire Name: wire_1" in summary
        assert "Wire Name: wire_2" in summary
        assert "Gmsh Point Tag: 1" in summary
        assert "Gmsh Point Tag: 2" in summary
    
    def test_get_wire_summary_empty(self):
        """Test summary generation with empty results."""
        preprocessor = WirePreprocessor()
        
        summary = preprocessor.get_wire_summary({})
        
        assert summary == "No wires processed."
