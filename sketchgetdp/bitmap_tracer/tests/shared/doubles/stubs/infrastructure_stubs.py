from tests.shared.doubles.stubs.entity_stubs import PointStub


class SVGGeneratorStub:
    """
    Test stub for SVG generation infrastructure that returns predefined SVG content.
    Simulates both batch and incremental SVG generation patterns for testing output composition.
    """
    
    def __init__(self, svg_output=None):
        self.svg_output = svg_output or "<svg></svg>"
        self.generate_called = False
        self.last_contours_passed = None
        self.last_points_passed = None
        self.last_colors_passed = None
        
    def generate_svg(self, contours, points, colors=None):
        self.generate_called = True
        self.last_contours_passed = contours
        self.last_points_passed = points
        self.last_colors_passed = colors or {}
        return self.svg_output
    
    def generate(self, contours, points):
        """Compatibility method for systems using simplified generation interface."""
        return self.generate_svg(contours, points)
    
    def add_shape(self, contour, color_hex):
        """Simulates incremental SVG generation by tracking individual shape additions."""
        if not hasattr(self, 'added_shapes'):
            self.added_shapes = []
        self.added_shapes.append((contour, color_hex))
    
    def add_point_marker(self, point_data, color_hex):
        """Simulates incremental point marker addition for testing marker placement logic."""
        if not hasattr(self, 'added_points'):
            self.added_points = []
        self.added_points.append((point_data, color_hex))


class PointDetectorStub:
    """
    Stub for point detection infrastructure that returns predefined point locations.
    Supports both contour-based and region-based detection approaches for comprehensive testing.
    """
    
    def __init__(self, points_to_return=None, center_point=None):
        self.points_to_return = points_to_return or []
        self.center_point = center_point or PointStub.create()
        self.detect_called = False
        self.last_contour_passed = None
        self.last_image_region_passed = None
        
    def detect_points(self, contour):
        self.detect_called = True
        self.last_contour_passed = contour
        return self.points_to_return
    
    def detect_points_in_region(self, image_region):
        """Alternative interface for systems using region-based point detection."""
        self.detect_called = True
        self.last_image_region_passed = image_region
        return self.points_to_return
    
    def is_point_structure(self, contour):
        """Determines if contour represents a point-like structure based on configured point data."""
        return len(self.points_to_return) > 0
    
    def get_contour_center(self, contour):
        """Calculates geometric center for contour analysis tests."""
        return self.center_point.to_point() if hasattr(self.center_point, 'to_point') else self.center_point


class CurveFitterStub:
    """
    Test double for curve fitting algorithms that returns predefined simplified points.
    Simulates multiple curve approximation techniques used in different infrastructure implementations.
    """
    
    def __init__(self, fitted_points=None, simplification_ratio=0.5):
        self.fitted_points = fitted_points or []
        self.simplification_ratio = simplification_ratio
        self.fit_called = False
        self.last_points_passed = None
        self.last_tolerance_passed = None
        
    def fit_curve(self, points, tolerance=None):
        self.fit_called = True
        self.last_points_passed = points
        self.last_tolerance_passed = tolerance
        return self.fitted_points
    
    def simplify_contour(self, points, epsilon=None):
        """Alternative interface for systems using contour simplification terminology."""
        self.fit_called = True
        self.last_points_passed = points
        self.last_tolerance_passed = epsilon
        return self.fitted_points
    
    def approximate_polygon(self, points, precision=None):
        """Simulates polygon approximation algorithms for testing geometric simplification."""
        self.fit_called = True
        self.last_points_passed = points
        self.last_tolerance_passed = precision
        return self.fitted_points


class ImageLoaderStub:
    """
    Stub for image loading infrastructure that returns predefined image objects.
    Tracks loading calls to verify image source handling in file system tests.
    """
    
    def __init__(self, image_to_return=None):
        self.image_to_return = image_to_return
        self.load_called = False
        self.last_path_passed = None
        
    def load_image(self, image_path):
        self.load_called = True
        self.last_path_passed = image_path
        return self.image_to_return
    
    def load(self, image_path):
        """Compatibility method for infrastructure with minimal interface requirements."""
        return self.load_image(image_path)


class ConfigLoaderStub:
    """
    Test stub for configuration loading infrastructure that returns predefined settings.
    Verifies configuration source handling and access patterns in infrastructure tests.
    """
    
    def __init__(self, config_data=None):
        self.config_data = config_data or {}
        self.load_called = False
        self.last_path_passed = None
        
    def load_config(self, config_path):
        self.load_called = True
        self.last_path_passed = config_path
        return self.config_data
    
    def get(self, key, default=None):
        return self.config_data.get(key, default)