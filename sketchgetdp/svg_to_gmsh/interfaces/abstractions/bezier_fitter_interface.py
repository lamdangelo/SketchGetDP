"""
Interface for bezier fitting operations.
"""

from abc import ABC, abstractmethod
from typing import List
from ...core.entities.point import Point
from ...core.entities.boundary_curve import BoundaryCurve

class BezierFitterInterface(ABC):
    """
    Abstract interface for bezier fitting.
    """
    
    @abstractmethod
    def fit_boundary_curve(self, points: List[Point], corner_indices: List[int], color, is_closed: bool = True) -> BoundaryCurve:
        """
        Fit piecewise Bézier curves with optimized continuity and accuracy.
        """
        pass