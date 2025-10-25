from typing import Dict, Any, Optional
from dataclasses import dataclass
from .....infrastructure.configuration.config_loader import ConfigLoader


@dataclass
class FakeConfig:
    """Configuration data container for testing purposes."""
    
    def __init__(self, data: Dict[str, Any] = None):
        """Initialize with default test configuration data.
        
        Args:
            data: Optional custom configuration data. Uses sensible defaults if not provided.
        """
        self.data = data or {
            'contour_detection': {
                'threshold': 128,
                'approximation_epsilon': 0.02,
                'min_contour_area': 10.0
            },
            'color_analysis': {
                'color_tolerance': 10,
                'dominant_color_threshold': 0.6
            },
            'point_detection': {
                'min_point_radius': 0.5,
                'max_point_radius': 5.0
            },
            'svg_generation': {
                'simplify_tolerance': 0.5,
                'curve_fitting_epsilon': 1.0
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve configuration value using dot notation.
        
        Args:
            key: Dot-separated path to configuration value (e.g., 'contour_detection.threshold')
            default: Value to return if key is not found
            
        Returns:
            Configuration value or default if not found
        """
        keys = key.split('.')
        current = self.data
        
        for key_segment in keys:
            if isinstance(current, dict) and key_segment in current:
                current = current[key_segment]
            else:
                return default
        
        return current
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation.
        
        Args:
            key: Dot-separated path to configuration value
            value: Value to set at the specified path
        """
        keys = key.split('.')
        current = self.data
        
        # Navigate to the parent of the target key, creating dictionaries as needed
        for key_segment in keys[:-1]:
            if key_segment not in current or not isinstance(current[key_segment], dict):
                current[key_segment] = {}
            current = current[key_segment]
        
        # Set the final value
        current[keys[-1]] = value


class FakeConfigLoader(ConfigLoader):
    """Test double for configuration loader.
    
    Simulates configuration loading behavior without external dependencies.
    """
    
    def __init__(self, config_data: Dict[str, Any] = None):
        """Initialize fake config loader.
        
        Args:
            config_data: Optional custom configuration data
        """
        self.config = FakeConfig(config_data)
        self.load_calls = 0
        self.get_limits_calls = []
    
    def load_config(self, config_path: Optional[str] = None) -> bool:
        """Simulate configuration loading.
        
        Always succeeds for testing purposes.
        
        Args:
            config_path: Optional configuration file path (ignored in fake implementation)
            
        Returns:
            Always returns True to indicate successful loading
        """
        self.load_calls += 1
        return True
    
    def get_limits(self, limit_type: str) -> Dict[str, float]:
        """Retrieve predefined limits for various configuration types.
        
        Args:
            limit_type: Type of limits to retrieve ('contour_area', 'point_radius', 'color_tolerance')
            
        Returns:
            Dictionary containing min/max limits for the specified type
        """
        self.get_limits_calls.append(limit_type)
        
        limits = {
            'contour_area': {'min': 10.0, 'max': 10000.0},
            'point_radius': {'min': 0.5, 'max': 5.0},
            'color_tolerance': {'min': 1, 'max': 50}
        }
        
        return limits.get(limit_type, {})
    
    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve configuration value.
        
        Args:
            key: Dot-separated path to configuration value
            default: Value to return if key is not found
            
        Returns:
            Configuration value or default if not found
        """
        return self.config.get(key, default)


class FakeConfigRepository:
    """Test double for configuration repository.
    
    Provides in-memory storage for configuration data during testing.
    """
    
    def __init__(self):
        """Initialize with empty configuration storage."""
        self.configs = {}
        self.save_calls = []
        self.load_calls = []
    
    def save(self, name: str, config: Dict[str, Any]) -> bool:
        """Store configuration in memory.
        
        Args:
            name: Unique identifier for the configuration
            config: Configuration data to store
            
        Returns:
            Always returns True to indicate successful save
        """
        self.save_calls.append((name, config))
        self.configs[name] = config
        return True
    
    def load(self, name: str) -> Optional[Dict[str, Any]]:
        """Retrieve configuration from memory.
        
        Args:
            name: Unique identifier for the configuration to load
            
        Returns:
            Configuration data if found, None otherwise
        """
        self.load_calls.append(name)
        return self.configs.get(name)
    
    def exists(self, name: str) -> bool:
        """Check if configuration exists in storage.
        
        Args:
            name: Unique identifier to check
            
        Returns:
            True if configuration exists, False otherwise
        """
        return name in self.configs