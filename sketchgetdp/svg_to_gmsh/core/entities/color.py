from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class Color:
    """A simple color entity supporting red, green, and blue colors."""
    
    RED: ClassVar['Color'] = None
    GREEN: ClassVar['Color'] = None
    BLUE: ClassVar['Color'] = None
    
    name: str
    rgb: tuple[int, int, int]
    
    def __post_init__(self):
        """Validate color after initialization"""
        if not isinstance(self.name, str):
            raise TypeError("Color name must be a string")
        
        if self.name not in ["red", "green", "blue"]:
            raise ValueError("Color must be 'red', 'green', or 'blue'")
        
        if not isinstance(self.rgb, tuple) or len(self.rgb) != 3:
            raise ValueError("RGB must be a tuple of 3 integers")
        
        for value in self.rgb:
            if not isinstance(value, int) or value < 0 or value > 255:
                raise ValueError("RGB values must be integers between 0 and 255")
    
    def to_hex(self) -> str:
        """Convert RGB color to hexadecimal format."""
        return f"#{self.rgb[0]:02x}{self.rgb[1]:02x}{self.rgb[2]:02x}"
    
    def to_normalized_rgb(self) -> tuple[float, float, float]:
        """Convert RGB color to normalized values (0.0 to 1.0)."""
        return (self.rgb[0] / 255.0, self.rgb[1] / 255.0, self.rgb[2] / 255.0)


# Initialize the class variables after class definition
Color.RED = Color("red", (255, 0, 0))
Color.GREEN = Color("green", (0, 255, 0))
Color.BLUE = Color("blue", (0, 0, 255))