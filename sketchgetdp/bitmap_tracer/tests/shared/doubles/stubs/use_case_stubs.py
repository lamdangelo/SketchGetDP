class ImageTracingStub:
    """
    Stub for image tracing use cases that returns configurable tracing results.
    Tracks execution calls to verify image processing workflow integration.
    """
    
    def __init__(self, tracing_result=None, contours_to_return=None, points_to_return=None):
        # Default result structure matching real use case output format
        self.tracing_result = tracing_result or {
            'success': True,
            'contours': contours_to_return or [],
            'points': points_to_return or [],
            'svg_data': '<svg></svg>'
        }
        self.contours_to_return = contours_to_return or []
        self.points_to_return = points_to_return or []
        self.trace_called = False
        self.last_image_passed = None
        self.last_config_passed = None
        
    def execute(self, image_input, config=None):
        self.trace_called = True
        self.last_image_passed = image_input
        self.last_config_passed = config
        return self.tracing_result
    
    def trace_image(self, image_path, options=None):
        """Alternative interface for systems using different terminology."""
        self.trace_called = True
        self.last_image_passed = image_path
        self.last_config_passed = options
        return self.tracing_result
    
    def get_detected_contours(self):
        """Get contours separately for testing contour processing in isolation."""
        return self.contours_to_return
    
    def get_detected_points(self):
        """Get points separately for testing point detection logic independently."""
        return self.points_to_return


class StructureFilteringStub:
    """
    Test double for structure filtering that simulates contour and point filtering.
    Verifies filtering criteria application in architectural validation tests.
    """
    
    def __init__(self, filtered_contours=None, filtered_points=None):
        self.filtered_contours = filtered_contours or []
        self.filtered_points = filtered_points or []
        self.filter_called = False
        self.last_contours_passed = None
        self.last_points_passed = None
        self.last_criteria_passed = None
        
    def execute(self, contours, points, criteria):
        self.filter_called = True
        self.last_contours_passed = contours
        self.last_points_passed = points
        self.last_criteria_passed = criteria
        return {
            'contours': self.filtered_contours,
            'points': self.filtered_points
        }
    
    def filter_structures(self, contours, criteria):
        """Simplified interface for contour-only filtering scenarios."""
        self.filter_called = True
        self.last_contours_passed = contours
        self.last_criteria_passed = criteria
        return self.filtered_contours
    
    def filter_by_area(self, contours, min_area=0.0, max_area=float('inf')):
        """Specialized method for testing area-based geometric constraints."""
        self.filter_called = True
        self.last_contours_passed = contours
        self.last_criteria_passed = {'min_area': min_area, 'max_area': max_area}
        return self.filtered_contours
    
    def filter_by_circularity(self, contours, min_circularity=0.0):
        """Specialized method for testing circular shape detection logic."""
        self.filter_called = True
        self.last_contours_passed = contours
        self.last_criteria_passed = {'min_circularity': min_circularity}
        return self.filtered_contours


class ColorCategorizationStub:
    """
    Stub for color analysis use cases that returns predefined color categorizations.
    Tracks region analysis to verify color processing in multi-region images.
    """
    
    def __init__(self, categorized_colors=None, dominant_colors=None):
        self.categorized_colors = categorized_colors or {}
        self.dominant_colors = dominant_colors or {}
        self.categorize_called = False
        self.last_image_passed = None
        self.last_regions_passed = None
        
    def execute(self, image, regions_of_interest=None):
        self.categorize_called = True
        self.last_image_passed = image
        self.last_regions_passed = regions_of_interest or []
        return {
            'categorized_colors': self.categorized_colors,
            'dominant_colors': self.dominant_colors
        }
    
    def categorize_image_colors(self, image):
        """Compatibility method for systems expecting single-image analysis."""
        return self.execute(image)


class SVGGenerationStub:
    """
    Test stub for SVG generation use cases that returns predefined SVG content.
    Verifies composition of geometric elements and styling in output generation.
    """
    
    def __init__(self, svg_output=None):
        self.svg_output = svg_output or "<svg></svg>"
        self.generate_called = False
        self.last_contours_passed = None
        self.last_points_passed = None
        self.last_colors_passed = None
        
    def execute(self, contours, points, color_mapping):
        self.generate_called = True
        self.last_contours_passed = contours
        self.last_points_passed = points
        self.last_colors_passed = color_mapping
        return self.svg_output
    
    def generate_from_tracing_data(self, tracing_data):
        """Convenience method for systems that bundle tracing data together."""
        self.generate_called = True
        self.last_contours_passed = tracing_data.get('contours', [])
        self.last_points_passed = tracing_data.get('points', [])
        return self.svg_output