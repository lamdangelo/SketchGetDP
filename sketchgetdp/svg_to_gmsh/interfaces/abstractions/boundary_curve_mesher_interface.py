"""
Interface for boundary curve meshing operations.
Defines the contract for converting BoundaryCurve objects into Gmsh geometry.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from ...core.entities.boundary_curve import BoundaryCurve


class BoundaryCurveMesherInterface(ABC):
    """
    Defines the interface for meshing BoundaryCurve objects in Gmsh.
    Implementations should handle geometry creation, physical group assignment,
    and proper hole/surface relationships.
    """
    
    @abstractmethod
    def mesh_boundary_curves(self, 
                           boundary_curves: List[BoundaryCurve], 
                           properties: List[Dict[str, Any]]) -> None:
        """
        Mesh all boundary curves with their properties.
        
        Args:
            boundary_curves: List of BoundaryCurve objects to mesh
            properties: List of dictionaries with "holes" and "physical_groups" keys
                       Each dictionary corresponds to the boundary curve at the same index
        
        Raises:
            ValueError: When number of boundary curves doesn't match number of property dictionaries
        """
        pass