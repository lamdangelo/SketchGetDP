class ImageLoaderStub:
    """
    Test stub for image loading gateway that returns predefined image objects.
    Tracks file system access patterns and supports test isolation through reset functionality.
    """
    
    def __init__(self, image_to_return=None):
        self.image_to_return = image_to_return
        self.load_called = False
        self.last_path_passed = None
        self.load_count = 0
        
    def load(self, image_path):
        self.load_called = True
        self.last_path_passed = image_path
        self.load_count += 1
        return self.image_to_return
    
    def load_image(self, image_path):
        """Compatibility method for gateways using different naming conventions."""
        return self.load(image_path)
    
    def reset(self):
        """Clear call tracking to ensure test independence between scenarios."""
        self.load_called = False
        self.last_path_passed = None
        self.load_count = 0


class ConfigRepositoryStub:
    """
    Stub for configuration repository gateway that returns predefined settings.
    Simulates configuration access patterns and section-based retrieval for testing data access layers.
    """
    
    def __init__(self, config_data=None):
        self.config_data = config_data or {}
        self.load_config_called = False
        self.load_count = 0
        self.last_section_requested = None
        
    def load_config(self):
        self.load_config_called = True
        self.load_count += 1
        return self.config_data
    
    def get(self, key, default=None):
        return self.config_data.get(key, default)
        
    def get_limits(self, section):
        """Retrieve configuration limits for specific functional sections."""
        self.last_section_requested = section
        return self.config_data.get(section, {})
    
    def get_tracing_parameters(self):
        """Extract tracing-specific configuration for image processing algorithm tests."""
        return self.config_data.get('tracing', {})
    
    def get_color_thresholds(self):
        """Extract color detection parameters for color analysis gateway tests."""
        return self.config_data.get('colors', {})
    
    def get_svg_settings(self):
        """Extract output generation settings for SVG rendering gateway tests."""
        return self.config_data.get('svg', {})
    
    def reset(self):
        """Reset all tracking state to support clean test execution cycles."""
        self.load_config_called = False
        self.load_count = 0
        self.last_section_requested = None