import yaml
from typing import List, Tuple, Any
from ..core.entities.point import Point
from ..core.entities.color import Color
from ..core.entities.physical_group import (
    DOMAIN_COIL_POSITIVE, 
    DOMAIN_COIL_NEGATIVE
)
from ..interfaces.abstractions.point_electrode_mesher_interface import PointElectrodeMesherInterface

class PointElectrodeMesher(PointElectrodeMesherInterface):
    """
    Mesher for point electrodes that sorts them and creates Gmsh entities with physical groups.
    """
    
    def __init__(self):
        self.factory = None
        self.coil_currents = {}
    
    def mesh_electrodes(self, 
                        factory: Any,
                        config_path: str,
                        electrodes: List[Tuple[Point, Color]]) -> dict:
        """
        Create Gmsh entities for point electrodes with physical groups.
        
        Args:
            factory: Gmsh factory object
            config_path: Path to the YAML configuration file
            electrodes: List of (point, color) tuples representing electrodes
            
        Returns:
            Dictionary mapping electrode indices to their Gmsh tags and physical groups
        """
        self.factory = factory
        self.coil_currents = self._load_coil_currents(config_path)
        
        if not electrodes:
            print("Warning: No electrodes provided")
            return {}
        
        sorted_electrodes = self._sort_electrodes(electrodes)
        
        # Collect points by their polarity
        positive_point_tags = []
        negative_point_tags = []
        results = {}
        
        for i, (point, color) in enumerate(sorted_electrodes):
            # Create Gmsh point entity
            point_tag = self.factory.addPoint(point.x, point.y, 0.0)
            physical_group = self._get_physical_group_for_electrode(i, color)
            
            # Store point tag based on polarity
            if physical_group == DOMAIN_COIL_POSITIVE:
                positive_point_tags.append(point_tag)
            elif physical_group == DOMAIN_COIL_NEGATIVE:
                negative_point_tags.append(point_tag)
            else:
                raise ValueError(f"Unknown physical group type: {physical_group}")
            
            # Store results
            results[i] = {
                'original_index': i,
                'point': point,
                'color': color,
                'gmsh_point_tag': point_tag,
                'physical_group': physical_group,
                'coil_name': f"coil_{i + 1}"
            }
        
        # Create ONE physical group for all positive points
        if positive_point_tags:
            self.factory.addPhysicalGroup(0, positive_point_tags, DOMAIN_COIL_POSITIVE.value)
            print(f"Created positive coil physical group (tag {DOMAIN_COIL_POSITIVE.value}) "
                  f"with {len(positive_point_tags)} electrodes")
        
        # Create ONE physical group for all negative points  
        if negative_point_tags:
            self.factory.addPhysicalGroup(0, negative_point_tags, DOMAIN_COIL_NEGATIVE.value)
            print(f"Created negative coil physical group (tag {DOMAIN_COIL_NEGATIVE.value}) "
                  f"with {len(negative_point_tags)} electrodes")
        
        # Print summary
        print(f"Total electrodes processed: {len(electrodes)}")
        print(f"  Positive: {len(positive_point_tags)}")
        print(f"  Negative: {len(negative_point_tags)}")
            
        return results
    
    def _load_coil_currents(self, config_path: str) -> dict:
        """
        Load coil current directions from the YAML configuration file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Dictionary mapping coil names to current directions
        """
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
                return config.get('coil_currents', {})
        except Exception as e:
            print(f"Warning: Could not load config file {config_path}: {e}")
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
    
    def get_electrode_summary(self, results: dict) -> str:
        """
        Generate a summary of the created electrodes.
        
        Args:
            results: Results dictionary from mesh_electrodes
            
        Returns:
            Formatted summary string
        """
        if not results:
            return "No electrodes processed."
        
        # Count positive and negative electrodes
        positive_count = sum(1 for data in results.values() 
                            if data['physical_group'] == DOMAIN_COIL_POSITIVE)
        negative_count = sum(1 for data in results.values() 
                            if data['physical_group'] == DOMAIN_COIL_NEGATIVE)
        
        summary = ["Point Electrode Summary (sorted order):"]
        summary.append("-" * 50)
        summary.append(f"Total electrodes: {len(results)}")
        summary.append(f"Positive coils (+): {positive_count} (physical group tag: {DOMAIN_COIL_POSITIVE.value})")
        summary.append(f"Negative coils (-): {negative_count} (physical group tag: {DOMAIN_COIL_NEGATIVE.value})")
        summary.append("-" * 50)
        
        for i, data in results.items():
            polarity = "Positive (+)" if data['physical_group'] == DOMAIN_COIL_POSITIVE else "Negative (-)"
            summary.append(f"Electrode {i+1} ({polarity}):")
            summary.append(f"  Position: ({data['point'].x:.3f}, {data['point'].y:.3f})")
            summary.append(f"  Color: {data['color'].name}")
            summary.append(f"  Coil Name: {data['coil_name']}")
            summary.append(f"  Gmsh Point Tag: {data['gmsh_point_tag']}")
            summary.append("")
        
        return "\n".join(summary)