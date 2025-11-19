"""
Interface for corner detection operations.
"""

from abc import ABC, abstractmethod
from typing import List
from ...core.entities.point import Point

class CornerDetectorInterface(ABC):
    """
    Abstract interface for corner detection.
    """
    
    @abstractmethod
    def detect_corners(self, boundary_points: List[Point]) -> List[int]:
        """
        Identifies indices of corner points in the boundary point sequence.
        """
        pass