"""
Interface for Bézier curve fitting operations.
Defines the contract for fitting Bézier curves to boundary point data.
"""

from abc import ABC, abstractmethod
from typing import List
from ...core.entities.point import Point
from ...core.entities.boundary_curve import BoundaryCurve

class BezierFitterInterface(ABC):
    """
    Defines the interface for fitting piecewise Bézier curves to boundary points.
    Implementations should handle corner detection, continuity enforcement, and curve optimization.
    """
    
    @abstractmethod
    def fit_boundary_curve(self, points: List[Point], corner_indices: List[int], 
                          color, is_closed: bool = True) -> BoundaryCurve:
        """
        Fit piecewise Bézier curves to boundary points with optimized continuity and accuracy.
        
        Args:
            points: List of boundary points to fit curves to
            corner_indices: Indices of points that represent sharp corners
            color: Visual color representation for the boundary curve
            is_closed: Whether the boundary forms a closed loop
            
        Returns:
            BoundaryCurve object containing fitted Bézier segments and corner information
        """
        pass