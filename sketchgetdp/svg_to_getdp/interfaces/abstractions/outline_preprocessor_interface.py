"""
Interface for outline preprocessing operations.
Defines the contract for converting Outline objects into Gmsh geometry.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from sketchgetdp.svg_to_getdp.core.entities.outline import Outline


class OutlinePreprocessorInterface(ABC):
    """
    Defines the interface for preprocessing Outline objects in Gmsh.
    Implementations should handle geometry creation, physical group assignment,
    and proper hole/surface relationships.
    """
    
    @abstractmethod
    def preprocess_outlines(self, 
                        factory: Any,
                        outlines: List[Outline], 
                        properties: List[Dict[str, Any]]) -> None:
        """
        Preprocess all outlines with their properties.
        
        Args:
            factory: Gmsh geometry factory (gmsh.model.geo)
            outlines: List of Outline objects to preprocess
            properties: List of dictionaries with "holes" and "physical_groups" keys
                       Each dictionary corresponds to the outline at the same index
        
        Raises:
            ValueError: When number of outlines doesn't match number of property dictionaries
        """
        pass