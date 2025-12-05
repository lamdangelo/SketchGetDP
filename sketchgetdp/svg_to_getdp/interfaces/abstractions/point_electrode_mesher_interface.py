"""
Interface for point electrode meshing operations.
Defines the contract for creating Gmsh entities from point electrodes with physical groups.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any
from ...core.entities.point import Point
from ...core.entities.color import Color

class PointElectrodeMesherInterface(ABC):
    """
    Defines the interface for creating Gmsh entities for point electrodes.
    Implementations should handle electrode sorting, physical group assignment, and mesh creation.
    """
    
    @abstractmethod
    def mesh_electrodes(self, 
                        factory: Any,
                        config_path: str,
                        electrodes: List[Tuple[Point, Color]]) -> Dict[int, Dict[str, Any]]:
        """
        Create Gmsh entities for point electrodes with physical groups.
        
        Args:
            factory: Gmsh factory object
            config_path: Path to the YAML configuration file
            electrodes: List of (point, color) tuples representing electrodes
            
        Returns:
            Dictionary mapping electrode indices to their Gmsh tags and physical groups.
        """
        pass
