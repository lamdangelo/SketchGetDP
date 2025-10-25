from typing import List
from .....infrastructure.image_processing.contour_closure_service import ContourClosureService
from .....infrastructure.image_processing.contour_detector import ContourDetector
from .....infrastructure.point_detection.point_detector import PointDetector
from .....infrastructure.svg_generation.svg_generator import SVGGenerator
from .....core.entities.contour import Contour
from .....core.entities.point import Point
from .contour_fakes import FakeContour
from .point_fakes import FakePointData


class FakeContourClosureService(ContourClosureService):
    """
    Fake implementation of ContourClosureService for testing.
    
    Tracks method calls and provides configurable behavior for testing different scenarios.
    """
    
    def __init__(self):
        self.ensure_closure_calls = []
        self.is_closed_calls = []
        self.calculate_closure_gap_calls = []
        self.auto_close_contours = True
        self.closure_gap_threshold = 5.0
    
    def ensure_closure(self, contour: Contour) -> Contour:
        self.ensure_closure_calls.append(contour)
        
        # Auto-close contours when configured for testing closure behavior
        if self.auto_close_contours and not contour.is_closed:
            return FakeContour.create_closed_square(50, 50, 20)
        
        return contour
    
    def is_closed(self, contour: Contour) -> bool:
        self.is_closed_calls.append(contour)
        return contour.is_closed
    
    def calculate_closure_gap(self, contour: Contour) -> float:
        self.calculate_closure_gap_calls.append(contour)
        
        # Closed contours have no gap by definition
        if contour.is_closed:
            return 0.0
        
        # Return predetermined test value for consistent testing
        return 3.5


class FakeContourDetector(ContourDetector):
    """
    Fake implementation of ContourDetector for testing.
    
    Allows pre-configuring detection results and tracking method invocations.
    """
    
    def __init__(self):
        self.detect_calls = []
        self.preprocess_calls = []
        self.predefined_contours = []
        self.should_fail = False
    
    def detect(self, image_data) -> List[Contour]:
        self.detect_calls.append(image_data)
        
        if self.should_fail:
            return []
        
        if self.predefined_contours:
            return self.predefined_contours
        
        # Default test contours when no specific contours are predefined
        return [
            FakeContour.create_closed_square(0, 0, 10),
            FakeContour.create_closed_square(20, 20, 15)
        ]
    
    def preprocess(self, image_data):
        self.preprocess_calls.append(image_data)
        return image_data


class FakePointDetector(PointDetector):
    """
    Fake implementation of PointDetector for testing.
    
    Provides configurable point detection behavior and call tracking.
    """
    
    def __init__(self):
        self.is_point_calls = []
        self.get_center_calls = []
        self.create_marker_calls = []
        self.point_radius = 2.0
        self.is_point_result = True
    
    def is_point(self, contour: Contour, min_radius: float, max_radius: float) -> bool:
        self.is_point_calls.append((contour, min_radius, max_radius))
        return self.is_point_result
    
    def get_center(self, contour: Contour) -> Point:
        self.get_center_calls.append(contour)
        return FakePointData.create_point(25, 25)
    
    def create_marker(self, center: Point, radius: float) -> Contour:
        self.create_marker_calls.append((center, radius))
        return FakeContour.create_closed_circle(center.x, center.y, radius)


class FakeSVGGenerator(SVGGenerator):
    """
    Fake implementation of SVGGenerator for testing.
    
    Tracks all generation calls and allows pre-setting SVG output for predictable tests.
    """
    
    def __init__(self):
        self.generate_calls = []
        self.add_path_calls = []
        self.add_point_calls = []
        self.generated_svg = '<svg></svg>'
    
    def generate(self, width: float, height: float) -> str:
        self.generate_calls.append((width, height))
        return self.generated_svg
    
    def add_path(self, points: List[Point], is_closed: bool = True, **attributes):
        self.add_path_calls.append((points, is_closed, attributes))
    
    def add_point(self, center: Point, radius: float, **attributes):
        self.add_point_calls.append((center, radius, attributes))
    
    def set_generated_svg(self, svg_content: str):
        self.generated_svg = svg_content