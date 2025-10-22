"""
Configuration loader implementation.

Responsible for loading configuration parameters from YAML files and providing
type-safe access to different configuration categories. This class implements
the ConfigRepository interface from the application core.
"""

import yaml
import os
from typing import Tuple, Dict, Any
from ...interfaces.gateways.config_repository import ConfigRepository


class ConfigLoader(ConfigRepository):
    """
    Loads and manages application configuration from YAML files.
    
    This class serves as the concrete implementation of the ConfigRepository
    interface, providing configuration data to the application while abstracting
    the details of configuration storage and format.
    
    Attributes:
        config_path: Path to the YAML configuration file
        _config_cache: Internal cache for loaded configuration to avoid repeated file reads
    """
    
    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize with the path to the configuration file.
        
        Args:
            config_path: Relative or absolute path to the YAML configuration file
        """
        self.config_path = config_path
        self._config_cache = None
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration data from the YAML file.
        
        Uses caching to avoid repeated file system access. Subsequent calls
        return the cached configuration unless reload_config() is called.
        
        Returns:
            Dictionary containing all configuration key-value pairs
            
        Raises:
            FileNotFoundError: When the configuration file does not exist
            yaml.YAMLError: When the configuration file contains invalid YAML
            Exception: For any other file reading or parsing errors
        """
        if self._config_cache is not None:
            return self._config_cache
            
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
                self._config_cache = config or {}
                return self._config_cache
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing YAML configuration: {e}")
        except Exception as e:
            raise Exception(f"Error loading configuration: {e}")
    
    def get_structure_limits(self) -> Tuple[int, int, int]:
        """Get the maximum number of structures to keep for each color category.
        
        These limits control how many contours of each color are preserved
        during the filtering process. Structures are kept based on area size
        (largest first) up to these limits.
        
        Returns:
            Tuple containing (red_dots_limit, blue_paths_limit, green_paths_limit)
        """
        config = self.load_config()
        
        red_dots = config.get('red_dots', 0)
        blue_paths = config.get('blue_paths', 0)
        green_paths = config.get('green_paths', 0)
        
        return red_dots, blue_paths, green_paths
    
    def get_contour_detection_params(self) -> Dict[str, Any]:
        """Get parameters for contour detection and filtering.
        
        Returns parameters that control how contours are detected from the
        source image and which contours are considered valid for processing.
        
        Returns:
            Dictionary containing:
            - min_area: Minimum contour area to be considered valid
            - max_area_ratio: Maximum contour area as ratio of total image area
            - point_max_area: Maximum area for a contour to be classified as a point
            - point_max_perimeter: Maximum perimeter for point classification
            - closure_tolerance: Distance threshold for automatic contour closure
            - circularity_threshold: Minimum circularity for valid contours
        """
        config = self.load_config()
        
        return {
            'min_area': config.get('min_area', 150),
            'max_area_ratio': config.get('max_area_ratio', 0.8),
            'point_max_area': config.get('point_max_area', 100),
            'point_max_perimeter': config.get('point_max_perimeter', 80),
            'closure_tolerance': config.get('closure_tolerance', 5.0),
            'circularity_threshold': config.get('circularity_threshold', 0.01)
        }
    
    def get_curve_fitting_params(self) -> Dict[str, Any]:
        """Get parameters for curve fitting and path simplification.
        
        These parameters control the smart curve fitting algorithm that
        converts pixel-based contours into smooth SVG paths.
        
        Returns:
            Dictionary containing:
            - angle_threshold: Angle below which segments are treated as straight lines
            - min_curve_angle: Minimum angle for considering a segment as a curve
            - epsilon_factor: Factor for contour simplification (Douglas-Peucker)
            - closure_threshold: Maximum gap distance for considering a path closed
        """
        config = self.load_config()
        
        return {
            'angle_threshold': config.get('angle_threshold', 25),
            'min_curve_angle': config.get('min_curve_angle', 120),
            'epsilon_factor': config.get('epsilon_factor', 0.0015),
            'closure_threshold': config.get('closure_threshold', 10.0)
        }
    
    def get_color_detection_params(self) -> Dict[str, Any]:
        """Get parameters for color categorization.
        
        Returns thresholds and ranges used to categorize pixels into
        blue, red, green, white, or black categories.
        
        Returns:
            Dictionary containing:
            - blue_hue_range: HSV hue range for blue color detection
            - red_hue_range: HSV hue ranges for red color detection
            - green_hue_range: HSV hue range for green color detection
            - color_difference_threshold: RGB difference threshold for color dominance
            - min_saturation: Minimum saturation to avoid classifying as white
            - max_value_white: Maximum value above which colors are considered white
            - min_value_black: Minimum value below which colors are considered black
        """
        config = self.load_config()
        
        return {
            'blue_hue_range': config.get('blue_hue_range', [100, 140]),
            'red_hue_range': config.get('red_hue_range', [[0, 10], [170, 180]]),
            'green_hue_range': config.get('green_hue_range', [35, 85]),
            'color_difference_threshold': config.get('color_difference_threshold', 20),
            'min_saturation': config.get('min_saturation', 50),
            'max_value_white': config.get('max_value_white', 200),
            'min_value_black': config.get('min_value_black', 50)
        }
    
    def get_svg_params(self) -> Dict[str, Any]:
        """Get parameters for SVG generation and styling.
        
        Returns visual parameters that control the appearance of the
        generated SVG output.
        
        Returns:
            Dictionary containing:
            - point_radius: Radius of point markers in the SVG
            - stroke_width: Width of path strokes in the SVG
            - blue_color: Hex color code for blue paths
            - red_color: Hex color code for red points
            - green_color: Hex color code for green paths
        """
        config = self.load_config()
        
        return {
            'point_radius': config.get('point_radius', 4),
            'stroke_width': config.get('stroke_width', 2),
            'blue_color': config.get('blue_color', '#0000FF'),
            'red_color': config.get('red_color', '#FF0000'),
            'green_color': config.get('green_color', '#00FF00')
        }
    
    def reload_config(self) -> None:
        """Force reload of configuration from file.
        
        Clears the internal cache, ensuring that the next configuration
        access will read from the file system. This is useful when the
        configuration file has been modified during runtime.
        """
        self._config_cache = None
    
    def get_limits(self) -> Tuple[int, int, int]:
        """Get structure limits (alias for get_structure_limits).
        
        Provides backward compatibility with existing code that expects
        this method name.
        
        Returns:
            Tuple containing (red_dots_limit, blue_paths_limit, green_paths_limit)
        """
        return self.get_structure_limits()