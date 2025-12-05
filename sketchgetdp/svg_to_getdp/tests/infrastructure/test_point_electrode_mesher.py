import pytest
import tempfile
import os
from unittest.mock import Mock
import yaml

from svg_to_getdp.core.entities.point import Point
from svg_to_getdp.core.entities.color import Color
from svg_to_getdp.core.entities.physical_group import (
    DOMAIN_COIL_POSITIVE, 
    DOMAIN_COIL_NEGATIVE
)
from svg_to_getdp.infrastructure.point_electrode_mesher import PointElectrodeMesher


@pytest.fixture
def mock_factory():
    """Create a mock Gmsh factory."""
    factory = Mock()
    factory.addPoint = Mock(return_value=1)  # Mock point tag
    factory.addPhysicalGroup = Mock()
    return factory


@pytest.fixture
def sample_electrodes():
    """Create sample electrode data for testing."""
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
        'coil_currents': {
            'coil_1': 1,
            'coil_2': -1,
            'coil_3': 1,
            'coil_4': -1
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


class TestPointElectrodeMesher:
    """Test suite for PointElectrodeMesher class."""
    
    def test_init_with_valid_config(self, mock_factory, temp_config_file):
        """Test initialization with a valid config file."""
        mesher = PointElectrodeMesher(mock_factory, temp_config_file)
        
        assert mesher.factory == mock_factory
        assert mesher.config_path == temp_config_file
        assert mesher.coil_currents == {
            'coil_1': 1,
            'coil_2': -1,
            'coil_3': 1,
            'coil_4': -1
        }
    
    def test_init_with_missing_config_file(self, mock_factory):
        """Test initialization with a non-existent config file."""
        non_existent_path = "/non/existent/path/config.yaml"
        
        # Should handle gracefully and have empty coil_currents
        mesher = PointElectrodeMesher(mock_factory, non_existent_path)
        assert mesher.coil_currents == {}
    
    def test_init_with_invalid_yaml(self, mock_factory):
        """Test initialization with invalid YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name
        
        try:
            # Should handle gracefully
            mesher = PointElectrodeMesher(mock_factory, temp_path)
            assert mesher.coil_currents == {}
        finally:
            os.unlink(temp_path)
    
    def test_sort_electrodes(self, mock_factory, temp_empty_config_file):
        """Test electrode sorting from top to bottom, left to right."""
        mesher = PointElectrodeMesher(mock_factory, temp_empty_config_file)
        
        electrodes = [
            (Point(2.0, 1.0), Color("red", (255, 0, 0))),    # Top right
            (Point(1.0, 2.0), Color("blue", (0, 0, 255))),   # Top left (highest y)
            (Point(1.0, 0.0), Color("green", (0, 255, 0))),  # Bottom left
            (Point(2.0, 1.5), Color("black", (0, 0, 0))),    # Top middle
        ]
        
        sorted_electrodes = mesher._sort_electrodes(electrodes)
        
        # Expected order: highest y first, then smallest x for same y
        expected_order = [
            (Point(1.0, 2.0), Color("blue", (0, 0, 255))),   # Highest y
            (Point(2.0, 1.5), Color("black", (0, 0, 0))),    # Second highest y
            (Point(2.0, 1.0), Color("red", (255, 0, 0))),    # Third highest y
            (Point(1.0, 0.0), Color("green", (0, 255, 0))),  # Lowest y
        ]
        
        assert len(sorted_electrodes) == len(expected_order)
        for (exp_point, exp_color), (act_point, act_color) in zip(expected_order, sorted_electrodes):
            assert exp_point.x == act_point.x
            assert exp_point.y == act_point.y
            assert exp_color.name == act_color.name
            assert exp_color.rgb == act_color.rgb
    
    def test_electrode_sort_key(self, mock_factory, temp_empty_config_file):
        """Test the sort key function."""
        mesher = PointElectrodeMesher(mock_factory, temp_empty_config_file)
        
        test_cases = [
            ((Point(1.0, 2.0), Color("red", (255, 0, 0))), (-2.0, 1.0)),
            ((Point(3.0, 1.0), Color("blue", (0, 0, 255))), (-1.0, 3.0)),
            ((Point(0.0, 0.0), Color("green", (0, 255, 0))), (0.0, 0.0)),
            ((Point(2.0, 1.0), Color("black", (0, 0, 0))), (-1.0, 2.0)),
        ]
        
        for electrode, expected_key in test_cases:
            assert mesher._electrode_sort_key(electrode) == expected_key
    
    def test_get_physical_group_for_electrode(self, mock_factory, temp_config_file):
        """Test physical group assignment based on coil currents."""
        mesher = PointElectrodeMesher(mock_factory, temp_config_file)
        
        # Mock coil currents from temp_config_file
        assert mesher.coil_currents == {
            'coil_1': 1,
            'coil_2': -1,
            'coil_3': 1,
            'coil_4': -1
        }
        
        # Test positive current
        group = mesher._get_physical_group_for_electrode(0, Color("red", (255, 0, 0)))
        assert group == DOMAIN_COIL_POSITIVE
        
        # Test negative current
        group = mesher._get_physical_group_for_electrode(1, Color("blue", (0, 0, 255)))
        assert group == DOMAIN_COIL_NEGATIVE
        
        # Test invalid index (should use default from config or raise error)
        # Note: The error message includes the actual current_sign value (None) and coil_name
        with pytest.raises(ValueError, match=r"Invalid current sign None for coil_11"):
            mesher._get_physical_group_for_electrode(10, Color("green", (0, 255, 0)))
    
    def test_get_physical_group_with_missing_config(self, mock_factory, temp_empty_config_file):
        """Test physical group assignment with missing coil currents."""
        mesher = PointElectrodeMesher(mock_factory, temp_empty_config_file)
        
        # With empty config, all should raise ValueError
        # Note: The error message includes the actual current_sign value (None) and coil_name
        with pytest.raises(ValueError, match=r"Invalid current sign None for coil_1"):
            mesher._get_physical_group_for_electrode(0, Color("red", (255, 0, 0)))
    
    def test_mesh_electrodes_empty_list(self, mock_factory, temp_empty_config_file):
        """Test meshing with empty electrode list."""
        mesher = PointElectrodeMesher(mock_factory, temp_empty_config_file)
        
        results = mesher.mesh_electrodes([])
        assert results == {}
        
        # Verify no Gmsh calls were made
        mock_factory.addPoint.assert_not_called()
        mock_factory.addPhysicalGroup.assert_not_called()
    
    def test_mesh_electrodes_with_valid_data(self, mock_factory, temp_config_file, sample_electrodes):
        """Test meshing with valid electrode data."""
        mesher = PointElectrodeMesher(mock_factory, temp_config_file)
        
        # Mock sequential point tags
        mock_factory.addPoint.side_effect = [1, 2, 3, 4]
        
        results = mesher.mesh_electrodes(sample_electrodes)
        
        # Check results structure
        assert len(results) == 4
        
        for i in range(4):
            assert i in results
            assert 'original_index' in results[i]
            assert 'point' in results[i]
            assert 'color' in results[i]
            assert 'gmsh_point_tag' in results[i]
            assert 'physical_group' in results[i]
            assert 'coil_name' in results[i]
            
            # Check coil name
            assert results[i]['coil_name'] == f"coil_{i + 1}"
            
            # Check point tags
            assert results[i]['gmsh_point_tag'] == i + 1
        
        # Verify Gmsh calls
        assert mock_factory.addPoint.call_count == 4
        
        # Check that addPhysicalGroup was called for each point
        assert mock_factory.addPhysicalGroup.call_count == 4
        
        # Check point creation parameters
        sorted_electrodes = mesher._sort_electrodes(sample_electrodes)
        for i, (point, color) in enumerate(sorted_electrodes):
            mock_factory.addPoint.assert_any_call(point.x, point.y, 0.0, 0.05)
    
    def test_mesh_electrodes_sorted_order(self, mock_factory, temp_config_file):
        """Verify electrodes are processed in sorted order."""
        mesher = PointElectrodeMesher(mock_factory, temp_config_file)
        
        electrodes = [
            (Point(10.0, 5.0), Color("red", (255, 0, 0))),    # Should be last (lowest y)
            (Point(5.0, 10.0), Color("blue", (0, 0, 255))),   # Should be first (highest y)
            (Point(7.0, 8.0), Color("green", (0, 255, 0))),   # Should be second
        ]
        
        mock_factory.addPoint.side_effect = [1, 2, 3]
        
        results = mesher.mesh_electrodes(electrodes)
        
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
    
    def test_get_electrode_summary(self, mock_factory, temp_config_file, sample_electrodes):
        """Test the summary generation method."""
        mesher = PointElectrodeMesher(mock_factory, temp_config_file)
        
        # Create mock results similar to what mesh_electrodes would produce
        mock_results = {
            0: {
                'original_index': 0,
                'point': Point(1.0, 2.0),
                'color': Color("red", (255, 0, 0)),
                'gmsh_point_tag': 1,
                'physical_group': DOMAIN_COIL_POSITIVE,
                'coil_name': 'coil_1'
            },
            1: {
                'original_index': 1,
                'point': Point(2.0, 1.0),
                'color': Color("blue", (0, 0, 255)),
                'gmsh_point_tag': 2,
                'physical_group': DOMAIN_COIL_NEGATIVE,
                'coil_name': 'coil_2'
            }
        }
        
        summary = mesher.get_electrode_summary(mock_results)
        
        # Basic checks on summary content
        assert "Point Electrode Summary (sorted order):" in summary
        assert "Electrode 1:" in summary
        assert "Electrode 2:" in summary
        assert "Position: (1.000, 2.000)" in summary
        assert "Position: (2.000, 1.000)" in summary
        assert "Color: red" in summary
        assert "Color: blue" in summary
        assert "Coil Name: coil_1" in summary
        assert "Coil Name: coil_2" in summary
        assert "Physical Group: domain_coil_positive" in summary
        assert "Physical Group: domain_coil_negative" in summary
        assert "Current Sign: Positive (+)" in summary
        assert "Current Sign: Negative (-)" in summary
        assert "Gmsh Point Tag: 1" in summary
        assert "Gmsh Point Tag: 2" in summary
    
    def test_get_electrode_summary_empty(self, mock_factory, temp_config_file):
        """Test summary generation with empty results."""
        mesher = PointElectrodeMesher(mock_factory, temp_config_file)
        
        summary = mesher.get_electrode_summary({})
        
        assert "Point Electrode Summary (sorted order):" in summary
        assert "Electrode 1:" not in summary  # No electrode entries
        assert "Electrode 2:" not in summary  # No electrode entries
