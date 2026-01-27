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
    def load_config(self, config_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Load and parse configuration from persistent storage.
        
        Implementations should handle YAML parsing, schema validation,
        and setting appropriate defaults for missing values.
        
        Args:
            config_path: Optional path to configuration file in YAML format
            
        Returns:
            Dictionary containing configuration data, or None if loading fails
        """
        pass
    
    @abstractmethod
    def get_structure_limits(self) -> Tuple[int, int, int]:
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
    def get_contour_detection_params(self) -> Dict[str, Any]:
        """
        Retrieve parameters for contour detection and filtering.
        
        These parameters control how contours are detected and filtered
        during image processing.
        
        Returns:
            Dictionary containing contour detection parameters such as
            maximum area and perimeter thresholds
        """
        pass
    
    @abstractmethod
    def get_color_detection_params(self) -> Dict[str, Any]:
        """
        Retrieve parameters for color categorization in HSV space.
        
        These parameters define the hue ranges and thresholds for
        identifying different colors in the image.
        
        Returns:
            Dictionary containing color detection parameters including
            hue ranges for red, blue, green, and saturation/value thresholds
        """
        pass
    