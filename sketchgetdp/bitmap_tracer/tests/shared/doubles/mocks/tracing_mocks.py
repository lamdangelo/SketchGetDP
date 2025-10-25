from unittest.mock import Mock
from typing import List
from core.entities.contour import ClosedContour

class BitmapTracerMock:
    """Mock for BitmapTracer with call tracking"""
    
    def __init__(self):
        self.trace_image = Mock(return_value=True)
        self.trace_calls = []
    
    def trace_image(self, image_path: str) -> bool:
        self.trace_calls.append(image_path)
        return True

class ContourDetectorMock:
    """Mock for ContourDetector with verification capabilities"""
    
    def __init__(self):
        self.detect = Mock(return_value=[])
        self.preprocess = Mock()
        self.detect_calls = []
        self.preprocess_calls = []
    
    def detect(self, image_path: str) -> List[ClosedContour]:
        self.detect_calls.append(image_path)
        return self.detect.return_value