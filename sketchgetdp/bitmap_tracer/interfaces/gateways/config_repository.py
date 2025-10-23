"""
Configuration Repository Gateway Interface

Defines the abstraction for configuration management operations that infrastructure
components must implement. This interface centralizes all configuration access
patterns behind a consistent abstraction.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Any, Dict, Optional


class ConfigRepository(ABC):
    """Contracts for managing application configuration state and defaults."""
    
    @abstractmethod
    def load_config(self, config_path: str = "config.yaml") -> bool:
        """
        Load and parse configuration from persistent storage.
        
        Implementations should handle YAML parsing, schema validation,
        and setting appropriate defaults for missing values.
        
        Args:
            config_path: Path to configuration file in YAML format
            
        Returns:
            True if configuration was successfully loaded and validated,
            False if file is missing or contains invalid data
        """
        pass
    
    @abstractmethod
    def get_color_limits(self) -> Tuple[int, int, int]:
        """
        Retrieve the maximum number of structures to process for each color category.
        
        These limits control the filtering behavior during image tracing,
        ensuring only the most significant structures are processed.
        
        Returns:
            Tuple of (red_dots_limit, blue_paths_limit, green_paths_limit)
            where each limit represents the maximum count for that color category
        """
        pass
    
    @abstractmethod
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a specific configuration value by key.
        
        This method provides type-safe access to individual configuration
        parameters with fallback to default values.
        
        Args:
            key: Configuration parameter name to retrieve
            default: Value to return if key is not found in configuration
            
        Returns:
            Configuration value for the specified key, or default if not found
        """
        pass
    
    @abstractmethod
    def get_all_config(self) -> Dict[str, Any]:
        """
        Retrieve complete configuration as a dictionary.
        
        Useful for debugging, logging, or when multiple related configuration
        values need to be accessed together.
        
        Returns:
            Dictionary containing all configuration key-value pairs
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        Verify that loaded configuration meets application requirements.
        
        Performs semantic validation beyond basic syntax checking,
        ensuring all required parameters are present and within valid ranges.
        
        Returns:
            True if configuration is complete and valid for tracing operations
        """
        pass
    
    @abstractmethod
    def set_config_override(self, key: str, value: Any) -> None:
        """
        Temporarily override a configuration value at runtime.
        
        Primarily used for testing scenarios or dynamic configuration
        changes without modifying persistent configuration files.
        
        Args:
            key: Configuration parameter to override
            value: New value to use for this session
            
        Warning:
            Overrides are session-specific and not persisted to disk
        """
        pass