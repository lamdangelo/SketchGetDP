"""
Unit tests for config_loader.py
"""

import os
import sys
import pytest
import tempfile
import yaml
from unittest.mock import mock_open, patch

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
sys.path.insert(0, project_root)

from infrastructure.configuration.config_loader import ConfigLoader


class TestConfigLoader:
    """Test cases for ConfigLoader class."""

    @pytest.fixture
    def sample_config_data(self):
        """Sample configuration data for testing."""
        return {
            'red_dots': 10,
            'blue_paths': 5,
            'green_paths': 8,
            'min_area': 150,
            'max_area_ratio': 0.8,
            'point_max_area': 100,
            'point_max_perimeter': 80,
            'closure_tolerance': 5.0,
            'circularity_threshold': 0.01,
            'angle_threshold': 25,
            'min_curve_angle': 120,
            'epsilon_factor': 0.0015,
            'closure_threshold': 10.0,
            'blue_hue_range': [100, 140],
            'red_hue_range': [[0, 10], [170, 180]],
            'green_hue_range': [35, 85],
            'color_difference_threshold': 20,
            'min_saturation': 50,
            'max_value_white': 200,
            'min_value_black': 50,
            'point_radius': 4,
            'stroke_width': 2,
            'blue_color': '#0000FF',
            'red_color': '#FF0000',
            'green_color': '#00FF00',
            'custom_setting': 'test_value'
        }

    @pytest.fixture
    def config_loader(self):
        """Create a ConfigLoader instance for testing."""
        return ConfigLoader()

    @pytest.fixture
    def temp_config_file(self, sample_config_data):
        """Create a temporary config file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_config_data, f)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_initialization(self):
        """Test ConfigLoader initialization."""
        loader = ConfigLoader()
        assert loader.default_config_path == "config.yaml"
        assert loader._config_cache is None
        assert loader._overrides == {}

        custom_loader = ConfigLoader("custom_config.yaml")
        assert custom_loader.default_config_path == "custom_config.yaml"

    def test_load_config_success(self, temp_config_file, sample_config_data):
        """Test successful configuration loading."""
        loader = ConfigLoader(temp_config_file)
        config = loader.load_config()
        
        assert config is not None
        for key, value in sample_config_data.items():
            assert config[key] == value

    def test_load_config_file_not_found(self, config_loader):
        """Test loading when config file doesn't exist."""
        config = config_loader.load_config("non_existent_config.yaml")
        
        assert config == {}

    def test_load_config_invalid_yaml(self):
        """Test loading invalid YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name
        
        try:
            loader = ConfigLoader(temp_path)
            config = loader.load_config()
            
            assert config is None
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_load_config_caching(self, temp_config_file):
        """Test that config is cached after first load."""
        loader = ConfigLoader(temp_config_file)
        
        # First load
        config1 = loader.load_config()
        assert loader._config_cache is not None
        
        # Second load should use cache
        config2 = loader.load_config()
        assert config1 == config2

    def test_get_structure_limits(self, temp_config_file):
        """Test getting structure limits."""
        loader = ConfigLoader(temp_config_file)
        red_dots, blue_paths, green_paths = loader.get_structure_limits()
        
        assert red_dots == 10
        assert blue_paths == 5
        assert green_paths == 8

    def test_get_structure_limits_defaults(self, config_loader):
        """Test getting structure limits with defaults."""
        red_dots, blue_paths, green_paths = config_loader.get_structure_limits()
        
        assert red_dots == 0
        assert blue_paths == 0
        assert green_paths == 0

    def test_get_config_value(self, temp_config_file):
        """Test getting specific config value."""
        loader = ConfigLoader(temp_config_file)
        
        value = loader.get_config_value('custom_setting')
        assert value == 'test_value'
        
        default_value = loader.get_config_value('non_existent_key', 'default')
        assert default_value == 'default'

    def test_get_all_config(self, temp_config_file, sample_config_data):
        """Test getting all configuration."""
        loader = ConfigLoader(temp_config_file)
        config = loader.get_all_config()
        
        assert isinstance(config, dict)
        assert config['custom_setting'] == 'test_value'

    def test_get_contour_detection_params(self, temp_config_file):
        """Test getting contour detection parameters."""
        loader = ConfigLoader(temp_config_file)
        params = loader.get_contour_detection_params()
        
        expected_keys = [
            'min_area', 'max_area_ratio', 'point_max_area', 
            'point_max_perimeter', 'closure_tolerance', 'circularity_threshold'
        ]
        
        for key in expected_keys:
            assert key in params
            assert isinstance(params[key], (int, float))

    def test_get_curve_fitting_params(self, temp_config_file):
        """Test getting curve fitting parameters."""
        loader = ConfigLoader(temp_config_file)
        params = loader.get_curve_fitting_params()
        
        expected_keys = [
            'angle_threshold', 'min_curve_angle', 'epsilon_factor', 'closure_threshold'
        ]
        
        for key in expected_keys:
            assert key in params
            assert isinstance(params[key], (int, float))

    def test_get_color_detection_params(self, temp_config_file):
        """Test getting color detection parameters."""
        loader = ConfigLoader(temp_config_file)
        params = loader.get_color_detection_params()
        
        expected_keys = [
            'blue_hue_range', 'red_hue_range', 'green_hue_range',
            'color_difference_threshold', 'min_saturation', 
            'max_value_white', 'min_value_black'
        ]
        
        for key in expected_keys:
            assert key in params
            assert params[key] is not None

    def test_get_svg_params(self, temp_config_file):
        """Test getting SVG parameters."""
        loader = ConfigLoader(temp_config_file)
        params = loader.get_svg_params()
        
        expected_keys = [
            'point_radius', 'stroke_width', 'blue_color', 
            'red_color', 'green_color'
        ]
        
        for key in expected_keys:
            assert key in params
            assert params[key] is not None

    def test_reload_config(self, temp_config_file):
        """Test configuration reloading."""
        loader = ConfigLoader(temp_config_file)
        
        # Load config first to populate cache
        loader.load_config()
        assert loader._config_cache is not None
        
        # Reload should clear cache
        loader.reload_config()
        assert loader._config_cache is None

    def test_get_limits_alias(self, temp_config_file):
        """Test that get_limits is an alias for get_structure_limits."""
        loader = ConfigLoader(temp_config_file)
        
        limits1 = loader.get_structure_limits()
        limits2 = loader.get_limits()
        
        assert limits1 == limits2

    def test_set_config_override(self, temp_config_file):
        """Test setting configuration overrides."""
        loader = ConfigLoader(temp_config_file)
        
        # Load config first
        original_value = loader.get_config_value('custom_setting')
        
        # Set override
        loader.set_config_override('custom_setting', 'overridden_value')
        
        # Check that override is applied
        overridden_value = loader.get_config_value('custom_setting')
        assert overridden_value == 'overridden_value'
        assert overridden_value != original_value
        
        # Check that override is in the overrides dict
        assert 'custom_setting' in loader._overrides
        assert loader._overrides['custom_setting'] == 'overridden_value'

    def test_apply_overrides_internal(self, temp_config_file):
        """Test internal _apply_overrides method."""
        loader = ConfigLoader(temp_config_file)
        
        # Load config to populate cache
        original_config = loader.load_config()
        
        # Set some overrides
        loader._overrides = {
            'custom_setting': 'overridden',
            'new_setting': 'new_value'
        }
        
        # Apply overrides
        overridden_config = loader._apply_overrides(original_config)
        
        # Check original config is not modified
        assert original_config['custom_setting'] == 'test_value'
        
        # Check overrides are applied
        assert overridden_config['custom_setting'] == 'overridden'
        assert overridden_config['new_setting'] == 'new_value'

    def test_empty_config_file(self):
        """Test loading an empty config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write('')  # Empty file
            temp_path = f.name
        
        try:
            loader = ConfigLoader(temp_path)
            config = loader.load_config()
            
            assert config == {}
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_none_config_path(self, config_loader):
        """Test loading with None config path (should use default)."""
        # This will try to load from default path which may not exist
        config = config_loader.load_config(None)
        
        # Should return empty dict if default file doesn't exist
        assert config == {}

    def test_multiple_overrides(self, temp_config_file):
        """Test multiple configuration overrides."""
        loader = ConfigLoader(temp_config_file)
        
        # Set multiple overrides
        loader.set_config_override('setting1', 'value1')
        loader.set_config_override('setting2', 'value2')
        loader.set_config_override('custom_setting', 'final_value')
        
        config = loader.get_all_config()
        
        assert config['setting1'] == 'value1'
        assert config['setting2'] == 'value2'
        assert config['custom_setting'] == 'final_value'
