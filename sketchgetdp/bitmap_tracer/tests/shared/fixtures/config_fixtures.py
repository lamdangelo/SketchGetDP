"""
Test fixtures for bitmap tracer configuration validation and loading.
Provides configuration objects for testing different parameter scenarios.
"""

from typing import Dict, Any, List
import pytest
import yaml

from infrastructure.configuration.config_loader import ConfigLoader


class ConfigFixtures:
    """
    Configuration test data for bitmap tracer parameter validation.
    Includes valid configurations for different scenarios and invalid cases for error testing.
    """
    
    # Valid configurations for normal operation testing
    STANDARD_CONFIG = {
        'red_dots': 10,
        'blue_paths': 5,
        'green_paths': 5,
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
        'blue_color': "#0000FF",
        'red_color': "#FF0000",
        'green_color': "#00FF00"
    }
    
    ESSENTIAL_CONFIG = {
        'red_dots': 5,
        'blue_paths': 3,
        'green_paths': 3,
        'min_area': 100,
        'max_area_ratio': 0.9,
        'point_max_area': 50,
        'closure_tolerance': 3.0,
        'blue_hue_range': [100, 140],
        'red_hue_range': [[0, 10], [170, 180]],
        'green_hue_range': [35, 85],
        'point_radius': 3,
        'stroke_width': 2,
        'blue_color': "#0000FF",
        'red_color': "#FF0000",
        'green_color': "#00FF00"
    }
    
    # Precision-focused configurations
    SENSITIVE_DETECTION_CONFIG = {
        **STANDARD_CONFIG,
        'min_area': 1,
        'closure_tolerance': 0.1,
        'epsilon_factor': 0.0001,
        'closure_threshold': 1.0,
        'color_difference_threshold': 5
    }
    
    ROBUST_DETECTION_CONFIG = {
        **STANDARD_CONFIG,
        'min_area': 500,
        'closure_tolerance': 20.0,
        'epsilon_factor': 0.01,
        'closure_threshold': 50.0,
        'color_difference_threshold': 50
    }
    
    # Structure limit configurations
    HIGH_CAPACITY_CONFIG = {
        **STANDARD_CONFIG,
        'red_dots': 100,
        'blue_paths': 50,
        'green_paths': 50
    }
    
    LOW_CAPACITY_CONFIG = {
        **STANDARD_CONFIG,
        'red_dots': 1,
        'blue_paths': 1,
        'green_paths': 1
    }
    
    # Invalid configurations for validation error testing
    INCOMPLETE_CONFIG = {
        'red_dots': 10,
        'blue_paths': 5
    }
    
    TYPE_ERROR_CONFIG = {
        'red_dots': "invalid",
        'blue_paths': 5.5,
        'min_area': "large",
        'max_area_ratio': "high",
        'blue_color': 123456,
        'blue_hue_range': "100-140"
    }
    
    RANGE_ERROR_CONFIG = {
        **STANDARD_CONFIG,
        'min_area': -10,
        'max_area_ratio': 1.5,
        'point_max_area': -50,
        'closure_tolerance': -1.0,
        'red_dots': -5,
        'point_radius': 0
    }
    
    COLOR_FORMAT_ERROR_CONFIG = {
        **STANDARD_CONFIG,
        'blue_color': "not_a_color",
        'red_color': "#GG0000",
        'green_color': "00FF00"
    }
    
    HUE_RANGE_ERROR_CONFIG = {
        **STANDARD_CONFIG,
        'blue_hue_range': [200, 100],
        'red_hue_range': [[200, 10]],
        'green_hue_range': [-10, 300]
    }

    @classmethod
    def create_test_config_file(cls, config_data: Dict[str, Any], file_path: str) -> None:
        """Create temporary YAML config file for file loading tests."""
        with open(file_path, 'w') as f:
            yaml.dump(config_data, f)
    
    @classmethod
    def get_operational_configs(cls) -> List[Dict[str, Any]]:
        """Configurations that should pass validation and work in production."""
        return [
            cls.STANDARD_CONFIG,
            cls.ESSENTIAL_CONFIG,
            cls.SENSITIVE_DETECTION_CONFIG,
            cls.ROBUST_DETECTION_CONFIG,
            cls.HIGH_CAPACITY_CONFIG,
            cls.LOW_CAPACITY_CONFIG
        ]
    
    @classmethod
    def get_validation_error_configs(cls) -> List[Dict[str, Any]]:
        """Configurations that should fail validation with specific errors."""
        return [
            cls.INCOMPLETE_CONFIG,
            cls.TYPE_ERROR_CONFIG,
            cls.RANGE_ERROR_CONFIG,
            cls.COLOR_FORMAT_ERROR_CONFIG,
            cls.HUE_RANGE_ERROR_CONFIG
        ]
    
    @classmethod
    def get_structure_limit_configs(cls) -> List[Dict[str, Any]]:
        """Configurations for testing structure count boundaries."""
        return [
            cls.STANDARD_CONFIG,
            cls.HIGH_CAPACITY_CONFIG,
            cls.LOW_CAPACITY_CONFIG
        ]
    
    @classmethod
    def get_contour_parameter_configs(cls) -> List[Dict[str, Any]]:
        """Configurations for testing contour detection sensitivity."""
        return [
            cls.STANDARD_CONFIG,
            cls.SENSITIVE_DETECTION_CONFIG,
            cls.ROBUST_DETECTION_CONFIG
        ]
    
    @classmethod
    def get_color_detection_configs(cls) -> List[Dict[str, Any]]:
        """Configurations for testing color detection parameters."""
        return [
            cls.STANDARD_CONFIG,
            {**cls.STANDARD_CONFIG, 'color_difference_threshold': 10},
            {**cls.STANDARD_CONFIG, 'color_difference_threshold': 40}
        ]


# Pytest fixtures - self-explanatory names require minimal comments
@pytest.fixture
def config_fixtures():
    return ConfigFixtures

@pytest.fixture
def standard_config():
    return ConfigFixtures.STANDARD_CONFIG.copy()

@pytest.fixture
def essential_config():
    return ConfigFixtures.ESSENTIAL_CONFIG.copy()

@pytest.fixture
def sensitive_detection_config():
    return ConfigFixtures.SENSITIVE_DETECTION_CONFIG.copy()

@pytest.fixture
def robust_detection_config():
    return ConfigFixtures.ROBUST_DETECTION_CONFIG.copy()

@pytest.fixture
def high_capacity_config():
    return ConfigFixtures.HIGH_CAPACITY_CONFIG.copy()

@pytest.fixture
def low_capacity_config():
    return ConfigFixtures.LOW_CAPACITY_CONFIG.copy()

@pytest.fixture
def type_error_config():
    return ConfigFixtures.TYPE_ERROR_CONFIG.copy()

@pytest.fixture
def range_error_config():
    return ConfigFixtures.RANGE_ERROR_CONFIG.copy()

@pytest.fixture
def color_error_config():
    return ConfigFixtures.COLOR_FORMAT_ERROR_CONFIG.copy()

@pytest.fixture
def temp_config_file(tmp_path, standard_config):
    config_path = tmp_path / "test_config.yaml"
    ConfigFixtures.create_test_config_file(standard_config, config_path)
    return config_path

@pytest.fixture
def temp_minimal_config_file(tmp_path, essential_config):
    config_path = tmp_path / "test_essential_config.yaml"
    ConfigFixtures.create_test_config_file(essential_config, config_path)
    return config_path

@pytest.fixture
def temp_error_config_file(tmp_path, type_error_config):
    config_path = tmp_path / "test_error_config.yaml"
    ConfigFixtures.create_test_config_file(type_error_config, config_path)
    return config_path

@pytest.fixture
def loaded_config(temp_config_file):
    return ConfigLoader(str(temp_config_file))


# Test data generators with clear intent
def operational_config_test_cases():
    """Test cases for valid configuration loading and usage."""
    return [
        (ConfigFixtures.STANDARD_CONFIG, "standard"),
        (ConfigFixtures.ESSENTIAL_CONFIG, "essential"),
        (ConfigFixtures.SENSITIVE_DETECTION_CONFIG, "sensitive"),
        (ConfigFixtures.ROBUST_DETECTION_CONFIG, "robust"),
        (ConfigFixtures.HIGH_CAPACITY_CONFIG, "high_capacity"),
        (ConfigFixtures.LOW_CAPACITY_CONFIG, "low_capacity")
    ]


def validation_error_test_cases():
    """Test cases for configuration validation error handling."""
    return [
        (ConfigFixtures.INCOMPLETE_CONFIG, "incomplete"),
        (ConfigFixtures.TYPE_ERROR_CONFIG, "type_errors"),
        (ConfigFixtures.RANGE_ERROR_CONFIG, "range_errors"),
        (ConfigFixtures.COLOR_FORMAT_ERROR_CONFIG, "color_errors"),
        (ConfigFixtures.HUE_RANGE_ERROR_CONFIG, "hue_range_errors")
    ]


def structure_limit_test_cases():
    """Test cases for structure count parameter validation."""
    return [
        (ConfigFixtures.STANDARD_CONFIG, 10, 5, 5),
        (ConfigFixtures.HIGH_CAPACITY_CONFIG, 100, 50, 50),
        (ConfigFixtures.LOW_CAPACITY_CONFIG, 1, 1, 1)
    ]


def contour_parameter_test_cases():
    """Test cases for contour detection parameter effects."""
    return [
        (ConfigFixtures.STANDARD_CONFIG, 150, 0.8, 5.0),
        (ConfigFixtures.SENSITIVE_DETECTION_CONFIG, 1, 0.8, 0.1),
        (ConfigFixtures.ROBUST_DETECTION_CONFIG, 500, 0.8, 20.0)
    ]


def color_sensitivity_test_cases():
    """Test cases for color detection sensitivity parameters."""
    return [
        (ConfigFixtures.STANDARD_CONFIG, 20, 50, 200),
        ({**ConfigFixtures.STANDARD_CONFIG, 'color_difference_threshold': 10}, 10, 50, 200),
        ({**ConfigFixtures.STANDARD_CONFIG, 'color_difference_threshold': 40}, 40, 50, 200)
    ]


def svg_parameter_test_cases():
    """Test cases for SVG output parameter validation."""
    return [
        (ConfigFixtures.STANDARD_CONFIG, 4, 2, "#0000FF", "#FF0000", "#00FF00"),
        ({
            **ConfigFixtures.STANDARD_CONFIG,
            'point_radius': 8,
            'stroke_width': 4,
            'blue_color': "#000080",
            'red_color': "#800000",
            'green_color': "#008000"
        }, 8, 4, "#000080", "#800000", "#008000")
    ]