"""
Configuration loader implementation.

Responsible for loading configuration parameters from YAML files and providing
type-safe access to different configuration categories. This class implements
the ConfigRepository interface from the application core.
"""

import yaml
import os
from typing import Tuple, Dict, Any, Optional
from interfaces.gateways.config_repository import ConfigRepository


class ConfigLoader(ConfigRepository):
    """
    Loads and manages application configuration from YAML files.
    """
    
    def __init__(self, default_config_path: str = "config.yaml") -> None:
        self.default_config_path = default_config_path
        self._config_cache = None
        self._overrides = {}  # For runtime configuration overrides
    
    def load_config(self, config_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Load configuration data from the YAML file.
        
        Args:
            config_path: Optional path to config file, uses default if not provided
            
        Returns:
            Dictionary containing all configuration key-value pairs, or None if loading fails
        """
        if self._config_cache is not None:
            return self._apply_overrides(self._config_cache)
            
        actual_config_path = config_path or self.default_config_path
        
        if not os.path.exists(actual_config_path):
            print(f"⚠️ Configuration file not found: {actual_config_path}, using defaults")
            self._config_cache = {}
            return self._apply_overrides(self._config_cache)
        
        try:
            with open(actual_config_path, 'r') as file:
                config = yaml.safe_load(file)
                self._config_cache = config or {}
                print(f"✅ Loaded configuration from: {actual_config_path}")
                return self._apply_overrides(self._config_cache)
        except yaml.YAMLError as e:
            print(f"❌ Error parsing YAML configuration {actual_config_path}: {e}")
            return None
        except Exception as e:
            print(f"❌ Error loading configuration {actual_config_path}: {e}")
            return None
    
    def get_structure_limits(self) -> Tuple[int, int, int]:
        """Get the maximum number of structures to keep for each color category."""
        config = self.load_config() or {}
        
        red_dots = config.get('red_dots', 0)
        blue_paths = config.get('blue_paths', 0)
        green_paths = config.get('green_paths', 0)
        
        return red_dots, blue_paths, green_paths
    
    def get_contour_detection_params(self) -> Dict[str, Any]:
        """Get parameters for contour detection and filtering."""
        config = self.load_config() or {}
        
        return {
            'point_max_area': config.get('point_max_area', 100),
            'point_max_perimeter': config.get('point_max_perimeter', 80)
        }
    
    def get_color_detection_params(self) -> Dict[str, Any]:
        """Get parameters for color categorization."""
        config = self.load_config() or {}
        
        return {
            'blue_hue_range': config.get('blue_hue_range', [100, 140]),
            'red_hue_range': config.get('red_hue_range', [[0, 10], [170, 180]]),
            'green_hue_range': config.get('green_hue_range', [35, 85]),
            'min_saturation': config.get('min_saturation', 50),
            'max_value_white': config.get('max_value_white', 200),
            'min_value_black': config.get('min_value_black', 50)
        }
    
    def _apply_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply runtime overrides to the configuration."""
        if not self._overrides:
            return config
        
        result = config.copy()
        result.update(self._overrides)
        return result
    