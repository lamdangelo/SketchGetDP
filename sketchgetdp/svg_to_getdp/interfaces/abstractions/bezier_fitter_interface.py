"""
Interface for Bézier curve fitting operations.
Defines the contract for fitting Bézier curves to boundary point data.
"""

from abc import ABC, abstractmethod
from typing import List
from svg_to_getdp.core.entities.point import Point
from sketchgetdp.svg_to_getdp.core.entities.outline import Outline

class BezierFitterInterface(ABC):
    """
    Defines the interface for fitting piecewise Bézier curves.
    Implementations should handle corner detection, continuity enforcement, and curve optimization.
    """
    
    @abstractmethod
    def fit_outline(self, points: List[Point], corner_indices: List[int], 
                          color, is_closed: bool = True) -> Outline:
        """
        Fit piecewise Bézier curves with optimized continuity and accuracy.
        
        Args:
            points: List of outline points to fit curves to
            corner_indices: Indices of points that represent sharp corners
            color: Visual color representation for the outline
            is_closed: Whether the outline forms a closed loop
            
        Returns:
            Outline object containing fitted Bézier segments and corner information
        """
        pass