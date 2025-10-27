"""
Test fixtures for bitmap tracer image processing and contour detection.
Provides synthetic images for testing color detection, contour extraction, and tracing algorithms.
"""

from typing import List, Tuple, Optional, Dict
import pytest
import numpy as np
from unittest.mock import Mock

from core.entities.contour import ClosedContour
from core.entities.color import Color, ColorCategory
from interfaces.gateways.image_loader import ImageLoader


class ImageFixtures:
    """
    Synthetic image test data for bitmap tracer pipeline validation.
    Includes color patterns, geometric shapes, and edge cases for image processing tests.
    """
    
    # Standard test image dimensions
    SMALL_DIMENSIONS = (100, 100)
    MEDIUM_DIMENSIONS = (400, 300) 
    LARGE_DIMENSIONS = (800, 600)
    
    @classmethod
    def create_blank_canvas(cls, width: int, height: int, color: Tuple[int, int, int] = (255, 255, 255)) -> np.ndarray:
        """Create uniform background image for isolation testing."""
        image = np.zeros((height, width, 3), dtype=np.uint8)
        image[:, :] = color
        return image
    
    @classmethod
    def create_geometric_shapes_image(cls, width: int = 400, height: int = 300) -> np.ndarray:
        """Image with primary color shapes for contour and color detection testing."""
        image = cls.create_blank_canvas(width, height, (255, 255, 255))
        
        # Blue square - should detect as closed contour
        image[50:100, 50:100] = [255, 0, 0]
        
        # Red circular area - tests curve detection
        center_red = (150, 75)
        for y in range(50, 100):
            for x in range(125, 175):
                if (x - center_red[0])**2 + (y - center_red[1])**2 <= 400:
                    image[y, x] = [0, 0, 255]
        
        # Green triangular area - tests polygon detection
        for y in range(50, 100):
            for x in range(200, 250):
                if (x - 200) + (y - 50) <= 50:
                    image[y, x] = [0, 255, 0]
        
        # Small red dot - tests point detection thresholds
        image[180:185, 180:185] = [0, 0, 255]
        
        # Blue line segment - tests open path detection
        for i in range(50):
            image[200 + i, 100] = [255, 0, 0]
        
        return image
    
    @classmethod
    def create_solid_color_image(cls, color: Color, width: int = 200, height: int = 200) -> np.ndarray:
        """Uniform color image for basic color detection validation."""
        bgr_color = color.to_bgr_tuple()
        return cls.create_blank_canvas(width, height, bgr_color)
    
    @classmethod
    def create_random_noise_image(cls, width: int = 200, height: int = 200, noise_density: float = 0.1) -> np.ndarray:
        """Noisy image for testing robustness against image artifacts."""
        image = cls.create_blank_canvas(width, height, (255, 255, 255))
        noise_mask = np.random.random((height, width)) < noise_density
        image[noise_mask] = [0, 0, 0]
        return image
    
    @classmethod
    def create_color_gradient_image(cls, width: int = 200, height: int = 200) -> np.ndarray:
        """Smooth color transition image for testing color segmentation."""
        image = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Blue-to-red gradient tests color range detection
        for y in range(height):
            for x in range(width):
                blue_intensity = int(255 * (1 - x / width))
                red_intensity = int(255 * (x / width))
                image[y, x] = [blue_intensity, 0, red_intensity]
        
        return image
    
    @classmethod
    def create_contour_validation_image(cls) -> np.ndarray:
        """Image with specific shapes for contour property testing."""
        image = cls.create_blank_canvas(300, 300, (255, 255, 255))
        
        # Large rectangle - tests area filtering
        image[50:100, 50:150] = [255, 0, 0]
        
        # Tiny square - tests minimum size detection
        image[120:130, 120:130] = [0, 0, 255]
        
        # Irregular polygon - tests vertex count and shape complexity
        polygon_points = [(200, 50), (250, 50), (250, 100), (225, 125), (200, 100)]
        for i in range(len(polygon_points)):
            start = polygon_points[i]
            end = polygon_points[(i + 1) % len(polygon_points)]
            if start[0] == end[0]:
                y_min, y_max = min(start[1], end[1]), max(start[1], end[1])
                image[y_min:y_max, start[0]] = [0, 255, 0]
            else:
                x_min, x_max = min(start[0], end[0]), max(start[0], end[0])
                image[start[1], x_min:x_max] = [0, 255, 0]
        
        return image
    
    @classmethod
    def create_mock_image_loader(cls, image_data: Optional[np.ndarray] = None, 
                               simulate_failure: bool = False) -> ImageLoader:
        """Mock image loader for testing file I/O interactions."""
        mock_loader = Mock(spec=ImageLoader)
        
        if simulate_failure:
            mock_loader.load_image.side_effect = FileNotFoundError("Image file not found")
            mock_loader.validate_image_path.return_value = False
        else:
            if image_data is None:
                image_data = cls.create_geometric_shapes_image()
            
            mock_loader.load_image.return_value = image_data
            mock_loader.validate_image_path.return_value = True
            mock_loader.get_image_dimensions.return_value = (image_data.shape[1], image_data.shape[0])
        
        return mock_loader
    
    @classmethod
    def get_tracing_test_contours(cls) -> List[ClosedContour]:
        """Contours representing typical bitmap tracing results."""
        from tests.shared.fixtures.contour_fixtures import ContourFixtures
        
        return [
            ContourFixtures.SQUARE,      # Expected blue path
            ContourFixtures.CIRCLE,      # Expected blue path  
            ContourFixtures.TRIANGLE,    # Expected green path
            ContourFixtures.TINY,        # Expected red point
            ContourFixtures.OPEN_PATH,   # Tests closure algorithm
            ContourFixtures.IRREGULAR_POLYGON # Tests complex shape handling
        ]
    
    @classmethod
    def get_expected_color_assignments(cls) -> Dict[ClosedContour, ColorCategory]:
        """Expected color categorizations for tracing validation."""
        from tests.shared.fixtures.contour_fixtures import ContourFixtures
        
        return {
            ContourFixtures.SQUARE: ColorCategory.BLUE,
            ContourFixtures.CIRCLE: ColorCategory.BLUE,
            ContourFixtures.TRIANGLE: ColorCategory.GREEN,
            ContourFixtures.TINY: ColorCategory.RED,
            ContourFixtures.IRREGULAR_POLYGON: ColorCategory.GREEN
        }
    
    @classmethod
    def get_image_test_suite(cls) -> List[Tuple[np.ndarray, str]]:
        """Comprehensive image set for algorithm validation."""
        return [
            (cls.create_geometric_shapes_image(), "geometric_shapes"),
            (cls.create_blank_canvas(200, 200), "blank_white"),
            (cls.create_blank_canvas(200, 200, (0, 0, 0)), "blank_black"),
            (cls.create_random_noise_image(), "random_noise"),
            (cls.create_color_gradient_image(), "color_gradient"),
            (cls.create_contour_validation_image(), "contour_validation")
        ]
    
    @classmethod
    def get_resolution_test_cases(cls) -> List[Tuple[int, int]]:
        """Image dimensions for testing scale invariance."""
        return [
            cls.SMALL_DIMENSIONS,
            cls.MEDIUM_DIMENSIONS, 
            cls.LARGE_DIMENSIONS,
            (640, 480),
            (1920, 1080)
        ]


# Pytest fixtures - self-documenting names
@pytest.fixture
def image_fixtures():
    return ImageFixtures

@pytest.fixture
def geometric_shapes_image():
    return ImageFixtures.create_geometric_shapes_image()

@pytest.fixture
def blank_white_image():
    return ImageFixtures.create_blank_canvas(200, 200, (255, 255, 255))

@pytest.fixture
def blank_black_image():
    return ImageFixtures.create_blank_canvas(200, 200, (0, 0, 0))

@pytest.fixture
def noise_image():
    return ImageFixtures.create_random_noise_image()

@pytest.fixture
def gradient_image():
    return ImageFixtures.create_color_gradient_image()

@pytest.fixture
def contour_validation_image():
    return ImageFixtures.create_contour_validation_image()

@pytest.fixture
def solid_blue_image():
    blue_color = Color(b=255, g=0, r=0)
    return ImageFixtures.create_solid_color_image(blue_color)

@pytest.fixture
def solid_red_image():
    red_color = Color(b=0, g=0, r=255)
    return ImageFixtures.create_solid_color_image(red_color)

@pytest.fixture
def solid_green_image():
    green_color = Color(b=0, g=255, r=0)
    return ImageFixtures.create_solid_color_image(green_color)

@pytest.fixture
def working_image_loader(geometric_shapes_image):
    return ImageFixtures.create_mock_image_loader(geometric_shapes_image)

@pytest.fixture
def failing_image_loader():
    return ImageFixtures.create_mock_image_loader(simulate_failure=True)

@pytest.fixture
def tracing_test_contours():
    return ImageFixtures.get_tracing_test_contours()

@pytest.fixture
def expected_color_assignments():
    return ImageFixtures.get_expected_color_assignments()

@pytest.fixture(params=ImageFixtures.get_image_test_suite())
def image_test_case(request):
    return request.param

@pytest.fixture(params=ImageFixtures.get_resolution_test_cases())
def resolution_test_case(request):
    return request.param


# Test data generators with clear testing focus
def image_loader_test_cases():
    """Test cases for image loading error handling and validation."""
    return [
        ("valid_image.png", True, None),
        ("missing_image.jpg", False, FileNotFoundError),
        ("corrupt_image.bmp", False, ValueError),
        ("restricted_image.png", False, PermissionError)
    ]


def contour_extraction_test_cases():
    """Test cases for contour detection algorithm validation."""
    return [
        (ImageFixtures.create_geometric_shapes_image(), 6),
        (ImageFixtures.create_blank_canvas(200, 200), 0),
        (ImageFixtures.create_contour_validation_image(), 3),
        (ImageFixtures.create_random_noise_image(noise_density=0.01), 0)
    ]


def color_classification_test_cases():
    """Test cases for color detection and categorization logic."""
    blue_color = Color(b=255, g=0, r=0)
    red_color = Color(b=0, g=0, r=255)
    green_color = Color(b=0, g=255, r=0)
    white_color = Color(b=255, g=255, r=255)
    black_color = Color(b=0, g=0, r=0)
    yellow_color = Color(b=0, g=255, r=255)
    
    return [
        (blue_color, ColorCategory.BLUE, "#0000FF"),
        (red_color, ColorCategory.RED, "#FF0000"),
        (green_color, ColorCategory.GREEN, "#00FF00"),
        (white_color, ColorCategory.WHITE, None),
        (black_color, ColorCategory.BLACK, None),
        (yellow_color, ColorCategory.OTHER, None)
    ]


def point_identification_test_cases():
    """Test cases for point vs path classification logic."""
    from tests.shared.fixtures.contour_fixtures import ContourFixtures
    
    return [
        (ContourFixtures.TINY, 100, 80, True),
        (ContourFixtures.SQUARE, 100, 80, False),
        (ContourFixtures.TRIANGLE, 100, 80, False),
        (ContourFixtures.LINE, 100, 80, False),
        (ContourFixtures.SINGLE_POINT, 100, 80, False),
        (ContourFixtures.TINY, 10, 10, False),
    ]


def path_closure_test_cases():
    """Test cases for automatic path closure algorithms."""
    from tests.shared.fixtures.contour_fixtures import ContourFixtures
    
    return [
        (ContourFixtures.OPEN_PATH, 5.0, False),
        (ContourFixtures.NEAR_CLOSED, 5.0, True),
        (ContourFixtures.SQUARE, 5.0, True),
        (ContourFixtures.OPEN_PATH, 20.0, True),
    ]


def curve_approximation_test_cases():
    """Test cases for curve simplification and fitting algorithms."""
    from tests.shared.fixtures.contour_fixtures import ContourFixtures
    
    return [
        (ContourFixtures.SQUARE, 25, 120, True),
        (ContourFixtures.CIRCLE, 25, 120, True),
        (ContourFixtures.IRREGULAR_POLYGON, 25, 120, True),
        (ContourFixtures.LINE, 25, 120, False),
        (ContourFixtures.SINGLE_POINT, 25, 120, False),
    ]