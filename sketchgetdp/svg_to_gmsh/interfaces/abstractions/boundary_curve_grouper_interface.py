"""
Interface for grouping boundary curves into hierarchical structures.
Defines the contract for analyzing containment relationships and assigning physical groups.
"""

from abc import ABC, abstractmethod
from typing import List, Dict
from ...core.entities.boundary_curve import BoundaryCurve
from ...core.entities.physical_group import PhysicalGroup

class BoundaryCurveGrouperInterface(ABC):
    """
    Defines the interface for grouping boundary curves into hierarchical structures
    with containment relationships and assigning appropriate physical groups.
    """
    
    @abstractmethod
    def group_boundary_curves(self, boundary_curves: List[BoundaryCurve]) -> List[Dict]:
        """
        Group boundary curves into hierarchical structure and assign physical groups.
        
        Args:
            boundary_curves: List of boundary curves to process
            
        Returns:
            List of dictionaries, one per boundary curve, containing:
            - "holes": List of indices of curves contained by this curve
            - "physical_groups": List of PhysicalGroup objects for this curve
        """
        pass