from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Point:
    """
    Represents a coordinate in 2D space. 
    This is a value object and should be immutable.
    """
    x: float
    y: float
    
    def to_tuple(self) -> Tuple[float, float]:
        """Required for compatibility with OpenCV and other libraries that expect tuples."""
        return (self.x, self.y)
    
    def distance_to(self, other: 'Point') -> float:
        """Euclidean distance calculation for spatial analysis."""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
    
    @classmethod
    def from_tuple(cls, point_tuple: Tuple[float, float]) -> 'Point':
        """Factory method for creating Points from external data formats."""
        return cls(x=point_tuple[0], y=point_tuple[1])


@dataclass(frozen=True)
class PointData:
    """
    Enhanced point information for the tracing algorithm.
    Contains metadata needed for point detection and SVG generation.
    """
    x: float
    y: float
    radius: float = 0.0
    is_small_point: bool = False
    
    @property
    def center(self) -> Point:
        """The center coordinate is the primary spatial identifier."""
        return Point(self.x, self.y)
    
    def to_point(self) -> Point:
        """Extracts the basic spatial information when full metadata isn't needed."""
        return Point(self.x, self.y)