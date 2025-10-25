from typing import List
from dataclasses import dataclass
from .....core.entities.color import Color


@dataclass
class FakeColor(Color):
    """
    Test double for Color entity that provides deterministic behavior for testing.
    
    This fake implementation allows controlled testing of color-related functionality
    without relying on the actual color processing logic.
    """
    
    def __init__(self, r: int = 0, g: int = 0, b: int = 0, a: int = 255):
        super().__init__(r, g, b, a)
        self.categorization_calls = 0
        self.dominant_calls = 0
    
    def to_hex(self) -> str:
        """Convert color to hexadecimal representation for testing purposes."""
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"
    
    def is_similar_to(self, other: 'Color', tolerance: int = 10) -> bool:
        """
        Determine if this color is similar to another within the given tolerance.
        
        Args:
            other: Color to compare against
            tolerance: Maximum allowed difference per channel
            
        Returns:
            True if all color channels are within tolerance range
        """
        return (abs(self.r - other.r) <= tolerance and
                abs(self.g - other.g) <= tolerance and
                abs(self.b - other.b) <= tolerance)


class FakeColorAnalyzer:
    """
    Test double for ColorAnalyzer that provides predictable color analysis results.
    
    This fake tracks method calls and returns predefined results to enable
    reliable and deterministic testing of color analysis dependencies.
    """
    
    def __init__(self):
        self.categorize_calls = []
        self.get_dominant_calls = []
        self.predefined_categories = {
            'red': FakeColor(255, 0, 0),
            'green': FakeColor(0, 255, 0),
            'blue': FakeColor(0, 0, 255),
            'black': FakeColor(0, 0, 0),
            'white': FakeColor(255, 255, 255)
        }
    
    def categorize(self, color: Color) -> str:
        """
        Categorize color into predefined color names for testing.
        
        Args:
            color: Color to categorize
            
        Returns:
            String representing the color category ('red', 'green', 'blue', 'white', or 'black')
        """
        self.categorize_calls.append(color)
        
        # Simple threshold-based categorization for predictable testing
        if color.r > 200 and color.g < 100 and color.b < 100:
            return 'red'
        elif color.g > 200 and color.r < 100 and color.b < 100:
            return 'green'
        elif color.b > 200 and color.r < 100 and color.g < 100:
            return 'blue'
        elif color.r > 200 and color.g > 200 and color.b > 200:
            return 'white'
        else:
            return 'black'
    
    def get_dominant_color(self, colors: List[Color]) -> Color:
        """
        Calculate dominant color by averaging all input colors.
        
        Args:
            colors: List of colors to analyze
            
        Returns:
            Average color as the dominant color, or black for empty lists
        """
        self.get_dominant_calls.append(colors)
        
        if not colors:
            return FakeColor(0, 0, 0)
        
        # Use average as a simple dominant color calculation for testing
        avg_r = sum(c.r for c in colors) // len(colors)
        avg_g = sum(c.g for c in colors) // len(colors)
        avg_b = sum(c.b for c in colors) // len(colors)
        
        return FakeColor(avg_r, avg_g, avg_b)