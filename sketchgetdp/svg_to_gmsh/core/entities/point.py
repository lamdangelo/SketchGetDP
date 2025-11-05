from dataclasses import dataclass
import math


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

    def __add__(self, other: 'Point') -> 'Point':
        """Vector addition"""
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other: 'Point') -> 'Point':
        """Vector subtraction"""
        return Point(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> 'Point':
        """Scalar multiplication"""
        return Point(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> 'Point':
        """Reverse scalar multiplication"""
        return self.__mul__(scalar)

    def norm(self) -> float:
        """Euclidean norm (magnitude) of the vector"""
        return math.sqrt(self.x**2 + self.y**2)

    def __truediv__(self, scalar: float) -> 'Point':
        """Scalar division"""
        if scalar == 0:
            raise ValueError("Division by zero")
        return Point(self.x / scalar, self.y / scalar)

    def __eq__(self, other: object) -> bool:
        """Equality comparison"""
        if not isinstance(other, Point):
            return False
        return math.isclose(self.x, other.x) and math.isclose(self.y, other.y)

    def __repr__(self) -> str:
        """Better representation for debugging"""
        return f"Point({self.x}, {self.y})"
    