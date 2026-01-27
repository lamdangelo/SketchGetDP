"""
Interface for grouping outlines into hierarchical structures.
Defines the contract for analyzing containment relationships and assigning physical groups.
"""

from abc import ABC, abstractmethod
from typing import List, Dict
from svg_to_getdp.core.entities.outline import Outline

class OutlineGrouperInterface(ABC):
    """
    Defines the interface for grouping outlines into hierarchical structures
    with containment relationships and assigning appropriate physical groups.
    """
    
    @abstractmethod
    def group_outlines(self, outlines: List[Outline]) -> List[Dict]:
        """
        Group outlines into hierarchical structure and assign physical groups.
        
        Args:
            outlines: List of outlines to process
            
        Returns:
            List of dictionaries, one per outline, containing:
            - "holes": List of indices of outlines contained by this outline
            - "physical_groups": List of PhysicalGroup objects for this outline
        """
        pass
    