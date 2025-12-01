import yaml
from typing import List, Tuple
from ..core.entities.point import Point
from ..core.entities.color import Color
from ..core.entities.physical_group import (
    DOMAIN_COIL_POSITIVE, 
    DOMAIN_COIL_NEGATIVE
)

class PointElectrodeMesher:
    """
    Mesher for point electrodes that sorts them and creates Gmsh entities with physical groups.
    """
    
    def __init__(self, factory, config_path: str):
        """
        Initialize the point electrode mesher.
        
        Args:
            factory: Gmsh factory object
            config_path: Path to the YAML configuration file
        """
        self.factory = factory
        self.config_path = config_path
        self.coil_currents = self._load_coil_currents()
        
    def _load_coil_currents(self) -> dict:
        """
        Load coil current directions from the YAML configuration file.
        
        Returns:
            Dictionary mapping coil names to current directions
        """
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
                return config.get('coil_currents', {})
        except Exception as e:
            print(f"Warning: Could not load config file {self.config_path}: {e}")
            return {}
    
    def _sort_electrodes(self, electrodes: List[Tuple[Point, Color]]) -> List[Tuple[Point, Color]]:
        """
        Sort electrodes from top to bottom and left to right.
        
        Args:
            electrodes: List of (point, color) tuples
            
        Returns:
            Sorted list of electrodes
        """
        return sorted(electrodes, key=self._electrode_sort_key)

    def _electrode_sort_key(self, elem: Tuple[Point, Color]) -> Tuple[float, float]:
        """
        Key function for sorting electrodes from top to bottom and left to right.
        
        Args:
            elem: A tuple containing (Point, Color) where Point has x and y coordinates
            
        Returns:
            Tuple suitable for sorting: (-y, x) to sort higher y first (top to bottom),
            then lower x first (left to right)
        """
        point, color = elem
        return (-point.y, point.x)
    
    def _get_physical_group_for_electrode(self, index: int, color: Color):
        """
        Get the appropriate physical group for an electrode based on its index and color.
        
        Args:
            index: Electrode index (0-based)
            color: Electrode color
            
        Returns:
            Appropriate PhysicalGroup instance
        """
        coil_name = f"coil_{index + 1}"
        current_sign = self.coil_currents.get(coil_name)
        
        if current_sign == 1:
            return DOMAIN_COIL_POSITIVE
        elif current_sign == -1:
            return DOMAIN_COIL_NEGATIVE
        else:
            raise ValueError(f"Invalid current sign {current_sign} for {coil_name}")
    
    def mesh_electrodes(self, electrodes: List[Tuple[Point, Color]], point_size: float = 0.1) -> dict:
        """
        Create Gmsh entities for point electrodes with physical groups.
        
        Args:
            electrodes: List of (point, color) tuples representing electrodes
            point_size: Size parameter for the point entities
            
        Returns:
            Dictionary mapping electrode indices to their Gmsh tags and physical groups
        """
        if not electrodes:
            print("Warning: No electrodes provided")
            return {}
        
        sorted_electrodes = self._sort_electrodes(electrodes)
        
        results = {}
        
        for i, (point, color) in enumerate(sorted_electrodes):
            # Create Gmsh point entity
            point_tag = self.factory.addPoint(point.x, point.y, 0.0, point_size)
            physical_group = self._get_physical_group_for_electrode(i, color)
            self.factory.addPhysicalGroup(0, [point_tag], physical_group.value)
            
            # Store results
            results[i] = {
                'original_index': i,
                'point': point,
                'color': color,
                'gmsh_point_tag': point_tag,
                'physical_group': physical_group,
                'coil_name': f"coil_{i + 1}"
            }
            
        return results
    
    def get_electrode_summary(self, results: dict) -> str:
        """
        Generate a summary of the created electrodes.
        
        Args:
            results: Results dictionary from mesh_electrodes
            
        Returns:
            Formatted summary string
        """
        summary = ["Point Electrode Summary (sorted order):"]
        summary.append("-" * 50)
        
        for i, data in results.items():
            current_sign = "Positive (+)" if data['physical_group'].current_sign == 1 else "Negative (-)" if data['physical_group'].current_sign == -1 else "None"
            summary.append(f"Electrode {i+1}:")
            summary.append(f"  Position: ({data['point'].x:.3f}, {data['point'].y:.3f})")
            summary.append(f"  Color: {data['color'].name}")
            summary.append(f"  Coil Name: {data['coil_name']}")
            summary.append(f"  Physical Group: {data['physical_group'].name}")
            summary.append(f"  Current Sign: {current_sign}")
            summary.append(f"  Gmsh Point Tag: {data['gmsh_point_tag']}")
            summary.append("")
        
        return "\n".join(summary)