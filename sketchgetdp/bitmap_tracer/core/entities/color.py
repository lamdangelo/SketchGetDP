from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


class ColorCategory(Enum):
    """
    The three primary colors we track plus ignored categories.
    This classification drives the entire tracing strategy.
    """
    BLUE = "blue"
    RED = "red" 
    GREEN = "green"
    WHITE = "white"    # Background - ignored
    BLACK = "black"    # Noise - ignored  
    OTHER = "other"    # Unsupported colors - ignored


@dataclass(frozen=True)
class Color:
    """
    Represents a color in BGR format (OpenCV standard).
    Immutable to ensure consistent color handling throughout the pipeline.
    """
    b: int
    g: int
    r: int
    
    # Standardized output colors ensure consistent SVG appearance
    CATEGORY_HEX_COLORS = {
        ColorCategory.BLUE: "#0000FF",
        ColorCategory.RED: "#FF0000", 
        ColorCategory.GREEN: "#00FF00"
    }
    
    def to_bgr_tuple(self) -> Tuple[int, int, int]:
        """OpenCV and most image processing libraries use BGR format."""
        return (self.b, self.g, self.r)
    
    def to_rgb_tuple(self) -> Tuple[int, int, int]:
        """Standard RGB format for web and most graphics applications."""
        return (self.r, self.g, self.b)
    
    def to_hex(self) -> str:
        """Hex format required for SVG color attributes."""
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}".upper()
    
    def categorize(self) -> Tuple[ColorCategory, Optional[str]]:
        """
        Core color classification logic.
        Uses HSV space for more accurate color perception than RGB.
        Returns both category and standardized output color.
        """
        import cv2
        import numpy as np
        
        bgr_array = np.uint8([[[self.b, self.g, self.r]]])
        hsv = cv2.cvtColor(bgr_array, cv2.COLOR_BGR2HSV)[0][0]
        hue, saturation, value = hsv
        
        # High value + low saturation = white/light colors (background)
        if value > 200 and saturation < 50:
            return ColorCategory.WHITE, None
        
        # Low value = dark colors (noise)
        if value < 50:
            return ColorCategory.BLACK, None
        
        # Primary color detection uses both HSV ranges and RGB relationships
        # as fallback for edge cases
        if (hue >= 100 and hue <= 140) or (self.b > self.g + 20 and self.b > self.r + 20):
            return ColorCategory.BLUE, self.CATEGORY_HEX_COLORS[ColorCategory.BLUE]
        elif (hue >= 0 and hue <= 10) or (hue >= 170 and hue <= 180) or (self.r > self.g + 20 and self.r > self.b + 20):
            return ColorCategory.RED, self.CATEGORY_HEX_COLORS[ColorCategory.RED]
        elif (hue >= 35 and hue <= 85) or (self.g > self.r + 20 and self.g > self.b + 20):
            return ColorCategory.GREEN, self.CATEGORY_HEX_COLORS[ColorCategory.GREEN]
        else:
            return ColorCategory.OTHER, None
    
    def is_ignored_color(self) -> bool:
        """Determines if this color should be excluded from tracing results."""
        category, _ = self.categorize()
        return category in [ColorCategory.WHITE, ColorCategory.BLACK, ColorCategory.OTHER]
    
    def is_primary_color(self) -> bool:
        """Checks if this is one of the three colors we actively trace."""
        category, _ = self.categorize()
        return category in [ColorCategory.BLUE, ColorCategory.RED, ColorCategory.GREEN]
    
    @classmethod
    def from_bgr_tuple(cls, bgr_tuple: Tuple[int, int, int]) -> 'Color':
        """Primary constructor - images from OpenCV are in BGR format."""
        return cls(b=bgr_tuple[0], g=bgr_tuple[1], r=bgr_tuple[2])
    
    @classmethod
    def from_rgb_tuple(cls, rgb_tuple: Tuple[int, int, int]) -> 'Color':
        """Alternative constructor for RGB sources."""
        return cls(b=rgb_tuple[2], g=rgb_tuple[1], r=rgb_tuple[0])
    
    @classmethod
    def from_hex(cls, hex_code: str) -> 'Color':
        """Constructor for web colors and configuration values."""
        hex_code = hex_code.lstrip('#')
        
        # Support both #RGB and #RRGGBB formats
        if len(hex_code) == 3:
            hex_code = ''.join(character * 2 for character in hex_code)
        
        red = int(hex_code[0:2], 16)
        green = int(hex_code[2:4], 16) 
        blue = int(hex_code[4:6], 16)
        
        return cls(b=blue, g=green, r=red)