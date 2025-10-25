from dataclasses import dataclass
from .....core.entities.point import Point


@dataclass
class FakePoint(Point):
    """Fake Point implementation for testing.
    
    Tracks method calls and uses Manhattan distance for simplified calculations.
    Useful for verifying interactions without complex geometric computations.
    """
    
    def __init__(self, x: float = 0, y: float = 0):
        """Initialize FakePoint with tracking capabilities.
        
        Args:
            x: X coordinate. Defaults to 0.
            y: Y coordinate. Defaults to 0.
        """
        super().__init__(x, y)
        self.distance_calls = []
        self.transform_calls = []
    
    def distance_to(self, other: Point) -> float:
        """Calculate Manhattan distance to another point and track the call.
        
        Args:
            other: The point to calculate distance to.
            
        Returns:
            Manhattan distance between the points.
        """
        self.distance_calls.append(other)
        return abs(self.x - other.x) + abs(self.y - other.y)
    
    def transform(self, dx: float, dy: float) -> 'FakePoint':
        """Create transformed point and track the transformation parameters.
        
        Args:
            dx: Translation in x direction.
            dy: Translation in y direction.
            
        Returns:
            New FakePoint instance with applied transformation.
        """
        self.transform_calls.append((dx, dy))
        return FakePoint(self.x + dx, self.y + dy)


class FakePointData:
    """Test data container for point-related information.
    
    Simulates point data structure with processing state tracking.
    """
    
    def __init__(self, x: float = 0, y: float = 0, radius: float = 1.0, 
                 is_small_point: bool = True):
        """Initialize FakePointData with geometric properties.
        
        Args:
            x: X coordinate. Defaults to 0.
            y: Y coordinate. Defaults to 0.
            radius: Point radius. Defaults to 1.0.
            is_small_point: Size classification. Defaults to True.
        """
        self.x = x
        self.y = y
        self.radius = radius
        self.is_small_point = is_small_point
        self.was_processed = False
    
    def __eq__(self, other: object) -> bool:
        """Compare two FakePointData instances for equality.
        
        Args:
            other: Object to compare with.
            
        Returns:
            True if all properties match, False otherwise.
        """
        if not isinstance(other, FakePointData):
            return False
        return (self.x == other.x and 
                self.y == other.y and 
                self.radius == other.radius and 
                self.is_small_point == other.is_small_point)