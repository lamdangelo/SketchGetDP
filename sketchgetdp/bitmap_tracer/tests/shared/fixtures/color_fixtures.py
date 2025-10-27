"""
Test fixtures for bitmap tracer color detection.
Defines colors for tracing primary colors (blue, red, green) and excluding others.
"""

from typing import Dict, List, Tuple
import pytest

from core.entities.color import Color, ColorCategory


class ColorFixtures:
    """
    Standardized color definitions for bitmap tracer testing.
    Colors are in BGR format (OpenCV standard) with variants for:
    - Primary traceable colors (blue, red, green)
    - Excluded colors (white, black, yellows, purples, etc.)
    - Borderline cases for categorization edge testing
    """
    
    # Primary traceable colors
    BLUE_PURE = Color(b=255, g=0, r=0)
    BLUE_DARK = Color(b=128, g=0, r=0)
    BLUE_LIGHT = Color(b=255, g=100, r=100)
    
    RED_PURE = Color(b=0, g=0, r=255)
    RED_DARK = Color(b=0, g=0, r=128)
    RED_LIGHT = Color(b=100, g=100, r=255)
    
    GREEN_PURE = Color(b=0, g=255, r=0)
    GREEN_DARK = Color(b=0, g=128, r=0)
    GREEN_LIGHT = Color(b=100, g=255, r=100)
    
    # Colors excluded from tracing
    WHITE_PURE = Color(b=255, g=255, r=255)
    WHITE_OFF = Color(b=240, g=240, r=240)
    BLACK_PURE = Color(b=0, g=0, r=0)
    BLACK_DARK_GRAY = Color(b=30, g=30, r=30)
    
    # Non-primary colors excluded from tracing
    YELLOW = Color(b=0, g=255, r=255)
    PURPLE = Color(b=255, g=0, r=255)
    CYAN = Color(b=255, g=255, r=0)
    ORANGE = Color(b=0, g=165, r=255)
    
    # Grayscale variants
    GRAY_MEDIUM = Color(b=128, g=128, r=128)
    GRAY_LIGHT = Color(b=200, g=200, r=200)
    GRAY_DARK = Color(b=80, g=80, r=80)
    
    # Categorization edge cases
    BLUE_GREEN_BORDER = Color(b=127, g=127, r=0)
    RED_BLUE_BORDER = Color(b=127, g=0, r=127)
    RED_GREEN_BORDER = Color(b=0, g=127, r=127)

    @classmethod
    def get_traceable_colors(cls) -> List[Color]:
        """Colors that should be detected and traced by the bitmap tracer."""
        return [
            cls.BLUE_PURE, cls.BLUE_DARK, cls.BLUE_LIGHT,
            cls.RED_PURE, cls.RED_DARK, cls.RED_LIGHT,
            cls.GREEN_PURE, cls.GREEN_DARK, cls.GREEN_LIGHT
        ]

    @classmethod
    def get_excluded_colors(cls) -> List[Color]:
        """Colors that should be ignored by the bitmap tracer."""
        return [
            cls.WHITE_PURE, cls.WHITE_OFF,
            cls.BLACK_PURE, cls.BLACK_DARK_GRAY,
            cls.YELLOW, cls.PURPLE, cls.CYAN, cls.ORANGE,
            cls.GRAY_MEDIUM, cls.GRAY_LIGHT, cls.GRAY_DARK
        ]

    @classmethod
    def get_categorization_edges(cls) -> List[Color]:
        """Colors that test categorization boundaries."""
        return [
            cls.BLUE_GREEN_BORDER,
            cls.RED_BLUE_BORDER, 
            cls.RED_GREEN_BORDER
        ]

    @classmethod
    def get_all_colors(cls) -> List[Color]:
        """All available color fixtures."""
        return (cls.get_traceable_colors() + 
                cls.get_excluded_colors() + 
                cls.get_categorization_edges())

    @classmethod
    def get_expected_categorization(cls) -> Dict[ColorCategory, List[Color]]:
        """Expected bitmap tracer categorization results."""
        return {
            ColorCategory.BLUE: [cls.BLUE_PURE, cls.BLUE_DARK, cls.BLUE_LIGHT],
            ColorCategory.RED: [cls.RED_PURE, cls.RED_DARK, cls.RED_LIGHT],
            ColorCategory.GREEN: [cls.GREEN_PURE, cls.GREEN_DARK, cls.GREEN_LIGHT],
            ColorCategory.WHITE: [cls.WHITE_PURE, cls.WHITE_OFF, cls.GRAY_LIGHT],
            ColorCategory.BLACK: [cls.BLACK_PURE, cls.BLACK_DARK_GRAY, cls.GRAY_DARK],
            ColorCategory.OTHER: [cls.YELLOW, cls.PURPLE, cls.CYAN, cls.ORANGE, cls.GRAY_MEDIUM]
        }

    @classmethod
    def get_expected_hex_codes(cls) -> Dict[ColorCategory, str]:
        """Expected hex output for each primary color category."""
        return {
            ColorCategory.BLUE: "#0000FF",
            ColorCategory.RED: "#FF0000", 
            ColorCategory.GREEN: "#00FF00"
        }


# Pytest fixtures - self-explanatory, minimal comments
@pytest.fixture
def color_fixtures():
    return ColorFixtures

@pytest.fixture
def traceable_colors():
    return ColorFixtures.get_traceable_colors()

@pytest.fixture
def excluded_colors():
    return ColorFixtures.get_excluded_colors()

@pytest.fixture
def edge_case_colors():
    return ColorFixtures.get_categorization_edges()

@pytest.fixture
def blue_variants():
    return [ColorFixtures.BLUE_PURE, ColorFixtures.BLUE_DARK, ColorFixtures.BLUE_LIGHT]

@pytest.fixture  
def red_variants():
    return [ColorFixtures.RED_PURE, ColorFixtures.RED_DARK, ColorFixtures.RED_LIGHT]

@pytest.fixture
def green_variants():
    return [ColorFixtures.GREEN_PURE, ColorFixtures.GREEN_DARK, ColorFixtures.GREEN_LIGHT]


# Test data generators
def traceable_color_test_cases():
    """Test cases for bitmap tracer color detection."""
    return [
        (ColorFixtures.BLUE_PURE, ColorCategory.BLUE, "#0000FF"),
        (ColorFixtures.BLUE_DARK, ColorCategory.BLUE, "#0000FF"),
        (ColorFixtures.BLUE_LIGHT, ColorCategory.BLUE, "#0000FF"),
        (ColorFixtures.RED_PURE, ColorCategory.RED, "#FF0000"),
        (ColorFixtures.RED_DARK, ColorCategory.RED, "#FF0000"),
        (ColorFixtures.RED_LIGHT, ColorCategory.RED, "#FF0000"),
        (ColorFixtures.GREEN_PURE, ColorCategory.GREEN, "#00FF00"),
        (ColorFixtures.GREEN_DARK, ColorCategory.GREEN, "#00FF00"),
        (ColorFixtures.GREEN_LIGHT, ColorCategory.GREEN, "#00FF00"),
    ]


def excluded_color_test_cases():
    """Test cases for colors excluded from tracing."""
    return [
        (ColorFixtures.WHITE_PURE, ColorCategory.WHITE),
        (ColorFixtures.WHITE_OFF, ColorCategory.WHITE),
        (ColorFixtures.BLACK_PURE, ColorCategory.BLACK),
        (ColorFixtures.BLACK_DARK_GRAY, ColorCategory.BLACK),
        (ColorFixtures.YELLOW, ColorCategory.OTHER),
        (ColorFixtures.PURPLE, ColorCategory.OTHER),
        (ColorFixtures.CYAN, ColorCategory.OTHER),
        (ColorFixtures.ORANGE, ColorCategory.OTHER),
    ]


def color_conversion_test_cases():
    """Test cases for color format conversions."""
    return [
        (ColorFixtures.BLUE_PURE, (255, 0, 0), (0, 0, 255), "#0000FF"),
        (ColorFixtures.RED_PURE, (0, 0, 255), (255, 0, 0), "#FF0000"),
        (ColorFixtures.GREEN_PURE, (0, 255, 0), (0, 255, 0), "#00FF00"),
        (ColorFixtures.WHITE_PURE, (255, 255, 255), (255, 255, 255), "#FFFFFF"),
        (ColorFixtures.BLACK_PURE, (0, 0, 0), (0, 0, 0), "#000000"),
    ]