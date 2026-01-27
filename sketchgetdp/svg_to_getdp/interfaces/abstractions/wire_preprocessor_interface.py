"""
Interface for wire preprocessing operations.
Defines the contract for creating Gmsh entities from wires with physical groups.
Prepares wire geometry for meshing but doesn't perform the meshing itself.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any
from svg_to_getdp.core.entities.point import Point
from svg_to_getdp.core.entities.color import Color

class WirePreprocessorInterface(ABC):
    """
    Defines the interface for creating Gmsh entities for wires.
    Implementations should handle wire sorting, physical group assignment, and preparation for meshing.
    """
    
    @abstractmethod
    def prepare_wires(self, 
                      factory: Any,
                      config_path: str,
                      wires: List[Tuple[Point, Color]]) -> Dict[int, Dict[str, Any]]:
        """
        Prepare Gmsh entities for wires with physical groups.
        
        Args:
            factory: Gmsh factory object
            config_path: Path to the YAML configuration file
            wires: List of (point, color) tuples representing wires
            
        Returns:
            Dictionary mapping wire indices to their Gmsh tags and physical groups.
        """
        pass
