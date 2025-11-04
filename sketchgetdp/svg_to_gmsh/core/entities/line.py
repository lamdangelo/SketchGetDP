# core/entities/line.py
from dataclasses import dataclass
import math
from typing import Any

from core.entities.point import Point


@dataclass(frozen=True)
class Line:
    """A 1D line segment entity representing a connection between two points in 2D space."""
    
    start: Point
    end: Point
    
    def __post_init__(self):
        """Validate line after initialization"""
        if not isinstance(self.start, Point) or not isinstance(self.end, Point):
            raise TypeError("Start and end must be Point instances")
    
    @property
    def length(self) -> float:
        """Calculate the length of the line segment."""
        return self.start.distance_to(self.end)
    
    @property
    def midpoint(self) -> Point:
        """Calculate the midpoint of the line segment."""
        mid_x = (self.start.x + self.end.x) / 2
        mid_y = (self.start.y + self.end.y) / 2
        return Point(mid_x, mid_y)
    
    @property
    def slope(self) -> float:
        """Calculate the slope of the line (rise over run)."""
        if self.is_vertical:
            raise ValueError("Vertical line has undefined slope")
        return (self.end.y - self.start.y) / (self.end.x - self.start.x)
    
    @property
    def is_vertical(self) -> bool:
        """Check if the line is vertical."""
        return math.isclose(self.start.x, self.end.x)
    
    @property
    def is_horizontal(self) -> bool:
        """Check if the line is horizontal."""
        return math.isclose(self.start.y, self.end.y)
    
    def contains_point(self, point: Point) -> bool:
        """Check if a point lies on the line segment."""
        if not isinstance(point, Point):
            raise TypeError("Point must be a Point instance")
        
        # Check if point is collinear and within segment bounds
        cross_product = (point.y - self.start.y) * (self.end.x - self.start.x) - \
                       (point.x - self.start.x) * (self.end.y - self.start.y)
        
        if not math.isclose(cross_product, 0, abs_tol=1e-10):
            return False
        
        # Check if point is within the segment bounds
        dot_product = (point.x - self.start.x) * (self.end.x - self.start.x) + \
                     (point.y - self.start.y) * (self.end.y - self.start.y)
        
        if dot_product < 0:
            return False
        
        squared_length = self.length ** 2
        if dot_product > squared_length:
            return False
        
        return True
    
    def is_parallel_to(self, other: 'Line') -> bool:
        """Check if this line is parallel to another line."""
        if not isinstance(other, Line):
            raise TypeError("Other must be a Line instance")
        
        # Both vertical
        if self.is_vertical and other.is_vertical:
            return True
        
        # One vertical, one not
        if self.is_vertical != other.is_vertical:
            return False
        
        # Both non-vertical - compare slopes
        return math.isclose(self.slope, other.slope)
    
    def reversed(self) -> 'Line':
        """Return a new line with start and end points swapped."""
        return Line(self.end, self.start)
    
    def __eq__(self, other: Any) -> bool:
        """Two lines are equal if they have the same start and end points."""
        if not isinstance(other, Line):
            return False
        return self.start == other.start and self.end == other.end
    
    def __hash__(self) -> int:
        """Hash based on start and end points."""
        return hash((self.start, self.end))
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"Line from {self.start} to {self.end}"
    
    def __repr__(self) -> str:
        """Developer-friendly string representation."""
        return f"Line(start={self.start!r}, end={self.end!r})"