class ConfigLoaderStub:
    """
    Test stub for configuration loading that provides default parameter values
    for image processing and SVG generation.
    """
    
    def __init__(self, config_values=None):
        # Default configuration optimized for typical diagram tracing scenarios
        self.config_values = config_values or {
            # Structure limits prevent excessive resource usage
            'red_dots': 10,
            'blue_paths': 5,
            'green_paths': 5,
            
            # Parameters tuned for reliable shape detection in hand-drawn diagrams
            'min_area': 150,
            'max_area_ratio': 0.8,
            'point_max_area': 100,
            'point_max_perimeter': 80,
            'closure_tolerance': 5.0,
            'circularity_threshold': 0.01,
            
            # Curve simplification parameters balancing accuracy and simplicity
            'angle_threshold': 25,
            'min_curve_angle': 120,
            'epsilon_factor': 0.0015,
            'closure_threshold': 10.0,
            
            # HSV ranges calibrated for typical diagram marker colors
            'blue_hue_range': [100, 140],
            'red_hue_range': [[0, 10], [170, 180]],  # Red wraps around HSV spectrum
            'green_hue_range': [35, 85],
            'color_difference_threshold': 20,
            'min_saturation': 50,
            'max_value_white': 200,
            'min_value_black': 50,
            
            # SVG output styling parameters
            'point_radius': 4,
            'stroke_width': 2,
            'blue_color': "#0000FF",
            'red_color': "#FF0000",
            'green_color': "#00FF00"
        }
        self.load_called = False
        self.load_count = 0
        
    def load_config(self):
        """Track method calls for test verification."""
        self.load_called = True
        self.load_count += 1
        return self.config_values
    
    def get(self, key, default=None):
        return self.config_values.get(key, default)
    
    def get_structure_limits(self):
        """Get constraints that prevent combinatorial explosion in complex diagrams."""
        return {
            'red_dots': self.config_values.get('red_dots', 10),
            'blue_paths': self.config_values.get('blue_paths', 5),
            'green_paths': self.config_values.get('green_paths', 5)
        }
    
    def get_contour_params(self):
        """Get parameters for distinguishing meaningful shapes from noise."""
        return {
            'min_area': self.config_values.get('min_area', 150),
            'max_area_ratio': self.config_values.get('max_area_ratio', 0.8),
            'point_max_area': self.config_values.get('point_max_area', 100),
            'point_max_perimeter': self.config_values.get('point_max_perimeter', 80),
            'closure_tolerance': self.config_values.get('closure_tolerance', 5.0),
            'circularity_threshold': self.config_values.get('circularity_threshold', 0.01)
        }
    
    def get_curve_params(self):
        """Get parameters for simplifying complex paths while preserving intent."""
        return {
            'angle_threshold': self.config_values.get('angle_threshold', 25),
            'min_curve_angle': self.config_values.get('min_curve_angle', 120),
            'epsilon_factor': self.config_values.get('epsilon_factor', 0.0015),
            'closure_threshold': self.config_values.get('closure_threshold', 10.0)
        }
    
    def get_color_params(self):
        """Get HSV parameters tuned for common colored marker detection."""
        return {
            'blue_hue_range': self.config_values.get('blue_hue_range', [100, 140]),
            'red_hue_range': self.config_values.get('red_hue_range', [[0, 10], [170, 180]]),
            'green_hue_range': self.config_values.get('green_hue_range', [35, 85]),
            'color_difference_threshold': self.config_values.get('color_difference_threshold', 20),
            'min_saturation': self.config_values.get('min_saturation', 50),
            'max_value_white': self.config_values.get('max_value_white', 200),
            'min_value_black': self.config_values.get('min_value_black', 50)
        }
    
    def get_svg_params(self):
        """Get styling parameters for clean SVG output."""
        return {
            'point_radius': self.config_values.get('point_radius', 4),
            'stroke_width': self.config_values.get('stroke_width', 2),
            'blue_color': self.config_values.get('blue_color', "#0000FF"),
            'red_color': self.config_values.get('red_color', "#FF0000"),
            'green_color': self.config_values.get('green_color', "#00FF00")
        }
    
    def update_config(self, updates):
        """Update configuration values for testing different scenarios."""
        self.config_values.update(updates)
    
    def reset(self):
        """Reset call tracking to ensure test isolation between cases."""
        self.load_called = False
        self.load_count = 0


class ConfigRepositoryStub:
    """Minimal stub for configuration repository interface testing."""
    
    def __init__(self, config_data=None):
        self.config_data = config_data or {}
        self.load_called = False
        
    def load_config(self):
        self.load_called = True
        return self.config_data
    
    def get(self, key, default=None):
        return self.config_data.get(key, default)
    
    def get_tracing_parameters(self):
        """Extract only the parameters relevant to image tracing operations."""
        return {
            key: self.config_data[key] for key in [
                'min_area', 'max_area_ratio', 'point_max_area', 'point_max_perimeter',
                'closure_tolerance', 'circularity_threshold'
            ] if key in self.config_data
        }