from unittest.mock import Mock

class SVGGeneratorMock:
    """Mock for SVGGenerator with output tracking"""
    
    def __init__(self):
        self.generate = Mock(return_value="<svg></svg>")
        self.add_path = Mock()
        self.add_point = Mock()
        self.generated_content = None
    
    def generate(self, contours, points) -> str:
        self.generated_content = "<svg></svg>"
        return self.generated_content

class ShapeProcessorMock:
    """Mock for ShapeProcessor with processing tracking"""
    
    def __init__(self):
        self.process_shape = Mock()
        self.filter_shapes = Mock(return_value=[])
        self.sort_by_area = Mock(return_value=[])
        self.processed_shapes = []