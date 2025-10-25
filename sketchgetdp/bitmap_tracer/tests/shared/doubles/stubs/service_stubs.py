from core.entities.contour import ClosedContour
from core.entities.color import ColorCategory
from tests.shared.doubles.stubs.entity_stubs import ColorStub


class ContourDetectorStub:
    """
    Stub for contour detection that returns predefined contours for testing.
    Tracks method calls to verify test interactions.
    """
    
    def __init__(self, contours_to_return=None):
        self.contours_to_return = contours_to_return or []
        self.detect_called = False
        self.last_image_passed = None
        
    def detect(self, image):
        self.detect_called = True
        self.last_image_passed = image
        return self.contours_to_return

    def detect_from_image(self, image):
        """Alternative interface for infrastructure components with different naming conventions."""
        return self.detect(image)


class ColorAnalyzerStub:
    """
    Test double for color analysis that returns configurable color categorizations.
    Verifies analysis calls and parameters in color processing tests.
    """
    
    def __init__(self, category_to_return=ColorCategory.WHITE, hex_color_to_return=None, dominant_color=None):
        self.category_to_return = category_to_return
        self.hex_color_to_return = hex_color_to_return or "#FFFFFF"
        self.dominant_color = dominant_color or ColorStub.create()
        self.categorize_called = False
        self.last_color_passed = None
        self.get_dominant_called = False
        self.last_region_passed = None
        
    def categorize(self, color):
        self.categorize_called = True
        self.last_color_passed = color
        return self.category_to_return, self.hex_color_to_return
        
    def get_dominant_color(self, image_region):
        self.get_dominant_called = True
        self.last_region_passed = image_region
        return self.dominant_color

    def analyze_color(self, color):
        """Compatibility method for systems using 'analyze' terminology instead of 'categorize'."""
        return self.categorize(color)


class ContourClosureServiceStub:
    """
    Stub for contour closure logic that simulates gap detection and closure behavior.
    Allows testing both closed and open contour scenarios.
    """
    
    def __init__(self, should_close=True, gap_size=0.0):
        # Configurable to test both successful closure and gap detection scenarios
        self.should_close = should_close
        self.gap_size = gap_size
        self.ensure_closure_called = False
        self.last_contour_passed = None
        
    def ensure_closure(self, contour):
        self.ensure_closure_called = True
        self.last_contour_passed = contour
        return ClosedContour(
            points=contour.points,
            is_closed=self.should_close,
            closure_gap=self.gap_size
        )

    def close_contour(self, contour):
        """Alternative method name for systems with different closure terminology."""
        return self.ensure_closure(contour)


class PointDetectorStub:
    """
    Test stub for point detection that returns predefined interest points.
    Tracks detection calls to verify contour analysis in tests.
    """
    
    def __init__(self, points_to_return=None):
        self.points_to_return = points_to_return or []
        self.detect_called = False
        self.last_contour_passed = None
        
    def detect_points(self, contour):
        self.detect_called = True
        self.last_contour_passed = contour
        return self.points_to_return


class CurveFitterStub:
    """
    Stub for curve fitting algorithms that returns predefined fitted points.
    Verifies that curve fitting is called with correct point sequences.
    """
    
    def __init__(self, fitted_points=None):
        self.fitted_points = fitted_points or []
        self.fit_called = False
        self.last_points_passed = None
        
    def fit_curve(self, points):
        self.fit_called = True
        self.last_points_passed = points
        return self.fitted_points


class SVGGeneratorStub:
    """
    Test double for SVG generation that returns predefined SVG content.
    Tracks generation calls and parameters to verify output composition.
    """
    
    def __init__(self, svg_output=None):
        self.svg_output = svg_output or "<svg></svg>"
        self.generate_called = False
        self.last_contours_passed = None
        self.last_points_passed = None
        
    def generate(self, contours, points):
        self.generate_called = True
        self.last_contours_passed = contours
        self.last_points_passed = points
        return self.svg_output