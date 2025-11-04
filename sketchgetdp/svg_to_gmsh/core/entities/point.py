from dataclasses import dataclass
import math
from typing import Tuple


@dataclass(frozen=True)
class Point:
    """A 0D point entity representing a position in 2D space."""
    
    x: float = 0.0
    y: float = 0.0
    
    def __post_init__(self):
        """Validate coordinates after initialization"""
        if not isinstance(self.x, (int, float)) or not isinstance(self.y, (int, float)):
            raise TypeError("Coordinates must be numeric")
        
        if math.isnan(self.x) or math.isnan(self.y):
            raise ValueError("Coordinates cannot be NaN")
    
    def distance_to(self, other: 'Point') -> float:
        """Calculate Euclidean distance to another point."""
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def distance_to_origin(self) -> float:
        """Calculate distance from origin (0,0)."""
        return math.sqrt(self.x**2 + self.y**2)
    