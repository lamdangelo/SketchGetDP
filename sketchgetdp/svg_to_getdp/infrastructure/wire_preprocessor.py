import yaml
from typing import List, Tuple, Any
from ..core.entities.point import Point
from ..core.entities.color import Color
from ..core.entities.physical_group import (
    DOMAIN_COIL_POSITIVE, 
    DOMAIN_COIL_NEGATIVE
)
from ..interfaces.abstractions.wire_preprocessor_interface import WirePreprocessorInterface

class WirePreprocessor(WirePreprocessorInterface):
    """
    Preprocessor for wires that sorts them and creates Gmsh entities with physical groups.
    Prepares wire geometry for meshing but doesn't perform the meshing itself.
    """
    
    def __init__(self):
        self.factory = None
        self.wire_currents = {}
    
    def prepare_wires(self, 
                      factory: Any,
                      config_path: str,
                      wires: List[Tuple[Point, Color]]) -> dict:
        """
        Prepare Gmsh entities for wires with physical groups.
        
        Args:
            factory: Gmsh factory object
            config_path: Path to the YAML configuration file
            wires: List of (point, color) tuples representing wires
            
        Returns:
            Dictionary mapping wire indices to their Gmsh tags and physical groups
        """
        self.factory = factory
        self.wire_currents = self._load_wire_currents(config_path)
        
        if not wires:
            print("Warning: No wires provided")
            return {}
        
        sorted_wires = self._sort_wires(wires)
        
        # Collect points by their polarity
        positive_point_tags = []
        negative_point_tags = []
        results = {}
        
        for i, (point, color) in enumerate(sorted_wires):
            # Create Gmsh point entity
            point_tag = self.factory.addPoint(point.x, point.y, 0.0)
            physical_group = self._get_physical_group_for_wire(i, color)
            
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
                'wire_name': f"wire_{i + 1}"
            }
        
        # Create ONE physical group for all positive points
        if positive_point_tags:
            self.factory.addPhysicalGroup(0, positive_point_tags, DOMAIN_COIL_POSITIVE.value)
            print(f"Created positive wire physical group (tag {DOMAIN_COIL_POSITIVE.value}) "
                  f"with {len(positive_point_tags)} wires")
        
        # Create ONE physical group for all negative points  
        if negative_point_tags:
            self.factory.addPhysicalGroup(0, negative_point_tags, DOMAIN_COIL_NEGATIVE.value)
            print(f"Created negative wire physical group (tag {DOMAIN_COIL_NEGATIVE.value}) "
                  f"with {len(negative_point_tags)} wires")
        
        # Print summary
        print(f"Total wires processed: {len(wires)}")
        print(f"  Positive: {len(positive_point_tags)}")
        print(f"  Negative: {len(negative_point_tags)}")
            
        return results
    
    def _load_wire_currents(self, config_path: str) -> dict:
        """
        Load wire current directions from the YAML configuration file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Dictionary mapping wire names to current directions
        """
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
                return config.get('wire_currents', {})
        except Exception as e:
            print(f"Warning: Could not load config file {config_path}: {e}")
            return {}
    
    def _sort_wires(self, wires: List[Tuple[Point, Color]]) -> List[Tuple[Point, Color]]:
        """
        Sort wires from top to bottom and left to right.
        
        Args:
            wires: List of (point, color) tuples
            
        Returns:
            Sorted list of wires
        """
        return sorted(wires, key=self._wire_sort_key)

    def _wire_sort_key(self, elem: Tuple[Point, Color]) -> Tuple[float, float]:
        """
        Key function for sorting wires from top to bottom and left to right.
        
        Args:
            elem: A tuple containing (Point, Color) where Point has x and y coordinates
            
        Returns:
            Tuple suitable for sorting: (-y, x) to sort higher y first (top to bottom),
            then lower x first (left to right)
        """
        point, color = elem
        return (-point.y, point.x)
    
    def _get_physical_group_for_wire(self, index: int, color: Color):
        """
        Get the appropriate physical group for a wire based on its index and color.
        
        Args:
            index: Wire index (0-based)
            color: Wire color
            
        Returns:
            Appropriate PhysicalGroup instance
        """
        wire_name = f"wire_{index + 1}"
        current_sign = self.wire_currents.get(wire_name)
        
        if current_sign == 1:
            return DOMAIN_COIL_POSITIVE
        elif current_sign == -1:
            return DOMAIN_COIL_NEGATIVE
        else:
            raise ValueError(f"Invalid current sign {current_sign} for {wire_name}")
    
    def get_wire_summary(self, results: dict) -> str:
        """
        Generate a summary of the created wires.
        
        Args:
            results: Results dictionary from prepare_wires
            
        Returns:
            Formatted summary string
        """
        if not results:
            return "No wires processed."
        
        # Count positive and negative wires
        positive_count = sum(1 for data in results.values() 
                            if data['physical_group'] == DOMAIN_COIL_POSITIVE)
        negative_count = sum(1 for data in results.values() 
                            if data['physical_group'] == DOMAIN_COIL_NEGATIVE)
        
        summary = ["Wire Summary (sorted order):"]
        summary.append("-" * 50)
        summary.append(f"Total wires: {len(results)}")
        summary.append(f"Positive wires (+): {positive_count} (physical group tag: {DOMAIN_COIL_POSITIVE.value})")
        summary.append(f"Negative wires (-): {negative_count} (physical group tag: {DOMAIN_COIL_NEGATIVE.value})")
        summary.append("-" * 50)
        
        for i, data in results.items():
            polarity = "Positive (+)" if data['physical_group'] == DOMAIN_COIL_POSITIVE else "Negative (-)"
            summary.append(f"Wire {i+1} ({polarity}):")
            summary.append(f"  Position: ({data['point'].x:.3f}, {data['point'].y:.3f})")
            summary.append(f"  Color: {data['color'].name}")
            summary.append(f"  Wire Name: {data['wire_name']}")
            summary.append(f"  Gmsh Point Tag: {data['gmsh_point_tag']}")
            summary.append("")
        
        return "\n".join(summary)
