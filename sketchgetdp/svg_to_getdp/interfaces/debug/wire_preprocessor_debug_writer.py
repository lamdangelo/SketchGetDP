"""
Debug writer for wire preprocessor operations.
Captures wire sorting, clustering, and Gmsh entity creation.
"""

import os
import math
from typing import List, Tuple, Dict, Any
from svg_to_getdp.core.entities.point import Point
from svg_to_getdp.core.entities.color import Color
from svg_to_getdp.interfaces.abstractions.wire_preprocessor_interface import WirePreprocessorInterface


class WirePreprocessorDebugWriter:
    """Debug writer for wire preprocessor operations."""
    
    def __init__(self):
        """Initialize the debug writer."""
        self._shared_timestamp = None
        self._svg_file_path = None
        self._svg_name = None
    
    def set_shared_timestamp(self, timestamp: str):
        """Set the shared timestamp for debug outputs."""
        self._shared_timestamp = timestamp
    
    def set_svg_file(self, svg_file_path: str):
        """Set the SVG file being processed."""
        self._svg_file_path = svg_file_path
        svg_filename = os.path.basename(svg_file_path)
        self._svg_name = os.path.splitext(svg_filename)[0]
    
    def write_wire_preprocessor_debug_info(
        self,
        svg_file_path: str,
        wires: List[Tuple[Point, Color]],
        config_file_path: str,
        wire_preprocessor_instance: WirePreprocessorInterface,
        gmsh_results: Dict[str, Any]
    ) -> str:
        """
        Write debug information for wire preprocessor operations.
        
        Args:
            svg_file_path: Path to the SVG file being processed
            wires: Original list of (point, color) tuples representing wires
            config_file_path: Path to the YAML configuration file
            wire_preprocessor_instance: The WirePreprocessor instance used
            gmsh_results: Full Gmsh results dictionary from ConvertGeometryToGmsh.execute()
            
        Returns:
            Path to the generated debug file
        """
        self.set_svg_file(svg_file_path)
        
        if not self._shared_timestamp:
            raise ValueError("Shared timestamp not set. Call set_shared_timestamp() first.")
        
        # Create debug directory
        debug_dir = "debug"
        os.makedirs(debug_dir, exist_ok=True)
        
        # Generate debug filename
        debug_file = self._get_debug_filename("wire_preprocessor_debug")
        
        # Extract wire_results from gmsh_results
        wire_results = gmsh_results.get("wire_results", {})
        
        # Write debug information
        with open(debug_file, 'w') as f:
            self._write_header(f, wires, config_file_path, gmsh_results)
            self._write_configuration_summary(f, config_file_path, wire_preprocessor_instance)
            self._write_wire_sorting_info(f, wires, wire_preprocessor_instance)
            self._write_clustering_info(f, wires, wire_preprocessor_instance, wire_results)
            self._write_gmsh_entity_info(f, wire_results)
            self._write_cluster_statistics(f, wire_results)
        
        print(f"Wire preprocessor debug information written to: {debug_file}")
                
        return debug_file
    
    def _get_debug_filename(self, prefix: str, extension: str = ".txt") -> str:
        """Generate a debug filename with timestamp."""
        if not self._svg_name:
            raise ValueError("SVG file not set. Call set_svg_file() first.")
        
        debug_dir = "debug"
        return f"{debug_dir}/{prefix}_{self._svg_name}_{self._shared_timestamp}{extension}"
    
    def _write_header(self, file_obj, wires: List[Tuple[Point, Color]], config_file_path: str, gmsh_results: Dict):
        """Write a header section to the debug file."""
        file_obj.write("=" * 80 + "\n")
        file_obj.write("WIRE PREPROCESSOR DEBUG\n")
        file_obj.write("=" * 80 + "\n\n")
        file_obj.write(f"SVG File: {self._svg_file_path}\n")
        file_obj.write(f"Config File: {config_file_path}\n")
        file_obj.write(f"Timestamp: {self._shared_timestamp}\n")
        file_obj.write(f"Total Wires: {len(wires)}\n")
        
        # Count wires by color
        color_count = {}
        for _, color in wires:
            color_name = color.name
            color_count[color_name] = color_count.get(color_name, 0) + 1
        
        for color_name, count in color_count.items():
            file_obj.write(f"  - {color_name}: {count}\n")
        
        file_obj.write("\n")
    
    def _write_configuration_summary(self, file_obj, config_file_path: str, wire_preprocessor: WirePreprocessorInterface):
        """Write wire cluster configuration from YAML."""
        file_obj.write("=" * 80 + "\n")
        file_obj.write("WIRE CLUSTER CONFIGURATION\n")
        file_obj.write("=" * 80 + "\n\n")
        
        try:
            # Try to access internal method to load clusters
            if hasattr(wire_preprocessor, '_load_wire_clusters'):
                clusters = wire_preprocessor._load_wire_clusters(config_file_path)
                
                total_wires_configured = sum(cluster.wire_count for cluster in clusters)
                file_obj.write(f"Total wires in configuration: {total_wires_configured}\n")
                file_obj.write(f"Number of clusters: {len(clusters)}\n\n")
                
                for i, cluster in enumerate(clusters):
                    polarity = "+" if cluster.current_sign == 1 else "-"
                    file_obj.write(f"Cluster {i+1}: {cluster.name}\n")
                    file_obj.write(f"  Wire count: {cluster.wire_count}\n")
                    file_obj.write(f"  Current sign: {cluster.current_sign} ({polarity})\n\n")
            else:
                file_obj.write("Unable to extract cluster configuration: _load_wire_clusters method not found\n")
                
        except Exception as e:
            file_obj.write(f"Error loading cluster configuration: {e}\n")
        
        file_obj.write("\n")
    
    def _write_wire_sorting_info(self, file_obj, wires: List[Tuple[Point, Color]], wire_preprocessor: WirePreprocessorInterface):
        """Write information about wire sorting order."""
        file_obj.write("=" * 80 + "\n")
        file_obj.write("WIRE SORTING (TOP-TO-BOTTOM, LEFT-TO-RIGHT)\n")
        file_obj.write("=" * 80 + "\n\n")
        
        try:
            # Convert to Wire objects if needed
            wire_objects = []
            for i, (point, color) in enumerate(wires):
                # Create a simple wire-like object
                class SimpleWire:
                    def __init__(self, point, color, index):
                        self.point = point
                        self.color = color
                        self.original_index = index
                
                wire_objects.append(SimpleWire(point, color, i))
            
            # Try to sort using the preprocessor's method
            if hasattr(wire_preprocessor, '_sort_wires'):
                sorted_wires = wire_preprocessor._sort_wires(wire_objects)
                
                file_obj.write("Sorted wire order:\n")
                file_obj.write(f"{'Index':<8} {'Original':<10} {'X':<12} {'Y':<12} {'Color':<10}\n")
                file_obj.write("-" * 52 + "\n")
                
                for i, wire in enumerate(sorted_wires):
                    file_obj.write(f"{i+1:<8} {wire.original_index:<10} {wire.point.x:<12.6f} {wire.point.y:<12.6f} {wire.color.name:<10}\n")
            else:
                # Manual sorting
                sorted_wires = sorted(wire_objects, key=lambda w: (-w.point.y, w.point.x))
                file_obj.write("Wires sorted manually (preprocessor method not available):\n")
                file_obj.write(f"{'Index':<8} {'Original':<10} {'X':<12} {'Y':<12} {'Color':<10}\n")
                file_obj.write("-" * 52 + "\n")
                
                for i, wire in enumerate(sorted_wires):
                    file_obj.write(f"{i+1:<8} {wire.original_index:<10} {wire.point.x:<12.6f} {wire.point.y:<12.6f} {wire.color.name:<10}\n")
        
        except Exception as e:
            file_obj.write(f"Error during wire sorting debug: {e}\n")
        
        file_obj.write("\n")
    
    def _write_clustering_info(self, file_obj, wires: List[Tuple[Point, Color]], wire_preprocessor: WirePreprocessorInterface, wire_results: Dict):
        """Write information about proximity-based clustering."""
        file_obj.write("=" * 80 + "\n")
        file_obj.write("WIRE CLUSTERING BY PROXIMITY\n")
        file_obj.write("=" * 80 + "\n\n")
        
        if not wire_results:
            file_obj.write("No wire results available\n\n")
            return
        
        try:
            # Group wires by cluster
            clusters = {}
            for wire_data in wire_results.values():
                cluster_name = wire_data['cluster_name']
                if cluster_name not in clusters:
                    clusters[cluster_name] = {
                        'current_sign': wire_data['physical_group'].current_sign if hasattr(wire_data['physical_group'], 'current_sign') else None,
                        'wire_count': 0,
                        'wires': [],
                        'positions': [],
                        'original_indices': []
                    }
                clusters[cluster_name]['wire_count'] += 1
                clusters[cluster_name]['wires'].append(wire_data['wire_name'])
                clusters[cluster_name]['positions'].append(
                    (wire_data['point'].x, wire_data['point'].y)
                )
                clusters[cluster_name]['original_indices'].append(wire_data['wire_index'])
            
            # Write cluster summary
            file_obj.write(f"Clusters created: {len(clusters)}\n\n")
            
            for cluster_name, cluster_info in clusters.items():
                polarity = "+" if cluster_info['current_sign'] == 1 else "-"
                file_obj.write(f"Cluster '{cluster_name}' ({polarity}):\n")
                file_obj.write(f"  Wire count: {cluster_info['wire_count']}\n")
                file_obj.write(f"  Wire names: {', '.join(cluster_info['wires'])}\n")
                file_obj.write(f"  Original indices: {cluster_info['original_indices']}\n")
                
                # Calculate intra-cluster distances
                if cluster_info['wire_count'] > 1:
                    positions = cluster_info['positions']
                    max_distance = 0
                    min_distance = float('inf')
                    
                    for i in range(len(positions)):
                        for j in range(i+1, len(positions)):
                            x1, y1 = positions[i]
                            x2, y2 = positions[j]
                            distance = math.sqrt((x1-x2)**2 + (y1-y2)**2)
                            max_distance = max(max_distance, distance)
                            min_distance = min(min_distance, distance)
                    
                    file_obj.write(f"  Intra-cluster distances:\n")
                    file_obj.write(f"    Max: {max_distance:.6f}\n")
                    file_obj.write(f"    Min: {min_distance:.6f}\n")
                
                file_obj.write("\n")
                
        except Exception as e:
            file_obj.write(f"Error extracting clustering info: {e}\n")
        
        file_obj.write("\n")
    
    def _write_gmsh_entity_info(self, file_obj, wire_results: Dict):
        """Write information about Gmsh entities created."""
        file_obj.write("=" * 80 + "\n")
        file_obj.write("GMSH ENTITY CREATION\n")
        file_obj.write("=" * 80 + "\n\n")
        
        if not wire_results:
            file_obj.write("No wire results available\n\n")
            return
        
        # Count positive and negative wires
        positive_wires = []
        negative_wires = []
        
        for wire_data in wire_results.values():
            if wire_data['physical_group'].current_sign == 1:
                positive_wires.append(wire_data)
            else:
                negative_wires.append(wire_data)
        
        file_obj.write(f"Positive wires (+): {len(positive_wires)}\n")
        file_obj.write(f"Negative wires (-): {len(negative_wires)}\n\n")
        
        # Write Gmsh point tags
        file_obj.write("Gmsh Point Tags:\n")
        file_obj.write(f"{'Wire':<12} {'Original':<10} {'Gmsh Tag':<12} {'Physical Group':<15} {'Cluster':<15} {'Position':<25}\n")
        file_obj.write("-" * 90 + "\n")
        
        for wire_data in wire_results.values():
            polarity = "+" if wire_data['physical_group'].current_sign == 1 else "-"
            file_obj.write(
                f"{wire_data['wire_name']:<12} "
                f"{wire_data['wire_index']:<10} "
                f"{wire_data['gmsh_point_tag']:<12} "
                f"{wire_data['physical_group'].name:<15} "
                f"{wire_data['cluster_name']:<15} "
                f"({wire_data['point'].x:.6f}, {wire_data['point'].y:.6f})\n"
            )
        
        file_obj.write("\n")
    
    def _write_cluster_statistics(self, file_obj, wire_results: Dict):
        """Write detailed cluster statistics."""
        file_obj.write("=" * 80 + "\n")
        file_obj.write("CLUSTER STATISTICS\n")
        file_obj.write("=" * 80 + "\n\n")
        
        if not wire_results:
            file_obj.write("No wire results available\n\n")
            return
        
        # Group wires by cluster
        clusters = {}
        for wire_data in wire_results.values():
            cluster_name = wire_data['cluster_name']
            if cluster_name not in clusters:
                clusters[cluster_name] = {
                    'current_sign': wire_data['physical_group'].current_sign if hasattr(wire_data['physical_group'], 'current_sign') else None,
                    'wires': [],
                    'positions': []
                }
            clusters[cluster_name]['wires'].append(wire_data)
            clusters[cluster_name]['positions'].append(
                (wire_data['point'].x, wire_data['point'].y)
            )
        
        # Calculate statistics for each cluster
        for cluster_name, cluster_info in clusters.items():
            polarity = "+" if cluster_info['current_sign'] == 1 else "-"
            positions = cluster_info['positions']
            
            # Calculate cluster center
            avg_x = sum(p[0] for p in positions) / len(positions)
            avg_y = sum(p[1] for p in positions) / len(positions)
            
            # Calculate distances from center
            distances = []
            for x, y in positions:
                distance = math.sqrt((x - avg_x)**2 + (y - avg_y)**2)
                distances.append(distance)
            
            max_distance = max(distances) if distances else 0
            min_distance = min(distances) if distances else 0
            avg_distance = sum(distances) / len(distances) if distances else 0
            
            file_obj.write(f"Cluster '{cluster_name}' ({polarity}):\n")
            file_obj.write(f"  Wire count: {len(positions)}\n")
            file_obj.write(f"  Center: ({avg_x:.6f}, {avg_y:.6f})\n")
            file_obj.write(f"  Distance from center:\n")
            file_obj.write(f"    Max: {max_distance:.6f}\n")
            file_obj.write(f"    Min: {min_distance:.6f}\n")
            file_obj.write(f"    Avg: {avg_distance:.6f}\n")
            
            # Wire distances relative to center
            file_obj.write(f"  Wire distances from center:\n")
            for wire_data, distance in zip(cluster_info['wires'], distances):
                file_obj.write(f"    {wire_data['wire_name']}: {distance:.6f} "
                             f"at ({wire_data['point'].x:.6f}, {wire_data['point'].y:.6f})\n")
            
            file_obj.write("\n")
            