import yaml
import math
from typing import List, Tuple, Any
from dataclasses import dataclass
from svg_to_getdp.core.entities.point import Point
from svg_to_getdp.core.entities.color import Color
from svg_to_getdp.core.entities.physical_group import (
    DOMAIN_COIL_POSITIVE, 
    DOMAIN_COIL_NEGATIVE
)
from svg_to_getdp.interfaces.abstractions.wire_preprocessor_interface import WirePreprocessorInterface


@dataclass
class Wire:
    """Represents a single wire."""
    point: Point
    color: Color
    original_index: int


@dataclass
class WireCluster:
    """Represents a cluster of wires that are close to each other."""
    name: str  # e.g., "cluster_1"
    wire_count: int
    current_sign: int  # 1 for positive, -1 for negative
    wires: List[Wire] = None
    
    def __post_init__(self):
        if self.wires is None:
            self.wires = []


class WirePreprocessor(WirePreprocessorInterface):
    """
    Preprocessor for wires that clusters them by proximity and creates Gmsh entities.
    """
    
    def __init__(self):
        self.factory = None
        self.wire_clusters: List[WireCluster] = []
        self.all_wires: List[Wire] = []
    
    def prepare_wires(self, 
                      factory: Any,
                      config_path: str,
                      wires: List[Tuple[Point, Color]]) -> dict:
        """
        Prepare Gmsh entities for wires with physical groups using cluster configuration.
        
        Args:
            factory: Gmsh factory object
            config_path: Path to the YAML configuration file
            wires: List of (point, color) tuples representing wires
            
        Returns:
            Dictionary mapping wire indices to their Gmsh tags and physical groups
        """
        self.factory = factory
        # Load wire cluster configuration
        self.wire_clusters = self._load_wire_clusters(config_path)
        
        if not wires:
            print("Warning: No wires provided")
            return {}
        
        # Convert given wires to Wire objects
        self.all_wires = [Wire(point=p, color=c, original_index=i) 
                         for i, (p, c) in enumerate(wires)]
        
        # First, sort all wires from top to bottom and left to right
        sorted_wires = self._sort_wires(self.all_wires)
        
        # Validate total wire count matches cluster configuration
        total_cluster_wires = sum(cluster.wire_count for cluster in self.wire_clusters)
        if total_cluster_wires != len(sorted_wires):
            raise ValueError(
                f"Number of wires ({len(sorted_wires)}) doesn't match cluster configuration "
                f"({total_cluster_wires} wires defined in {len(self.wire_clusters)} clusters)"
            )
        
        # Now cluster the wires based on proximity
        self._perform_clustering(sorted_wires)
        
        # Create Gmsh entities and collect results
        positive_point_tags = []
        negative_point_tags = []
        results = {}
        
        for cluster_idx, cluster in enumerate(self.wire_clusters):
            for wire_idx_in_cluster, wire in enumerate(cluster.wires):
                # Create Gmsh point entity
                point_tag = self.factory.addPoint(wire.point.x, wire.point.y, 0.0)
                
                # Get physical group based on cluster
                physical_group = self._get_physical_group_for_cluster(cluster)
                
                # Store point tag based on polarity
                if physical_group == DOMAIN_COIL_POSITIVE:
                    positive_point_tags.append(point_tag)
                elif physical_group == DOMAIN_COIL_NEGATIVE:
                    negative_point_tags.append(point_tag)
                else:
                    raise ValueError(f"Unknown physical group type: {physical_group}")
                
                # Store results
                results[wire.original_index] = {
                    'point': wire.point,
                    'color': wire.color,
                    'gmsh_point_tag': point_tag,
                    'physical_group': physical_group,
                    'wire_index': wire.original_index,
                    'wire_name': f"wire_{wire.original_index + 1}",
                    'cluster_name': cluster.name,
                    'wire_in_cluster_index': wire_idx_in_cluster,
                    'cluster_index': cluster_idx
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
        print(f"  Clusters: {len(self.wire_clusters)}")
            
        return results
    
    def _load_wire_clusters(self, config_path: str) -> List[WireCluster]:
        """
        Load wire cluster configuration from the YAML configuration file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            List of WireCluster objects sorted by cluster name
        """
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
                
                if 'wire_clusters' not in config:
                    raise ValueError("Config file must contain 'wire_clusters' section")
                
                wire_clusters_config = config['wire_clusters']
                
                if not isinstance(wire_clusters_config, dict):
                    raise ValueError("'wire_clusters' must be a dictionary")
                
                # Create clusters from configuration
                clusters = []
                for cluster_name, cluster_config in wire_clusters_config.items():
                    if not isinstance(cluster_config, dict):
                        raise ValueError(f"Cluster '{cluster_name}' configuration must be a dictionary")
                    
                    if 'wire_count' not in cluster_config:
                        raise ValueError(f"Cluster '{cluster_name}' must have 'wire_count'")
                    
                    if 'current_sign' not in cluster_config:
                        raise ValueError(f"Cluster '{cluster_name}' must have 'current_sign'")
                    
                    wire_count = cluster_config['wire_count']
                    current_sign = cluster_config['current_sign']
                    
                    # Validate current_sign
                    if current_sign not in [1, -1]:
                        raise ValueError(f"Cluster '{cluster_name}': current_sign must be 1 or -1, got {current_sign}")
                    
                    # Validate wire_count
                    if not isinstance(wire_count, int) or wire_count <= 0:
                        raise ValueError(f"Cluster '{cluster_name}': wire_count must be a positive integer, got {wire_count}")
                    
                    clusters.append(WireCluster(
                        name=cluster_name,
                        wire_count=wire_count,
                        current_sign=current_sign
                    ))
                
                # Sort clusters by name to ensure consistent ordering
                clusters.sort(key=lambda c: c.name)
                
                if not clusters:
                    raise ValueError("No wire clusters defined in configuration")
                
                return clusters
                
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file: {e}")
    
    def _sort_wires(self, wires: List[Wire]) -> List[Wire]:
        """
        Sort wires from top to bottom and left to right.
        
        Args:
            wires: List of Wire objects
            
        Returns:
            Sorted list of wires
        """
        return sorted(wires, key=lambda w: (-w.point.y, w.point.x))
    
    def _calculate_distance(self, wire1: Wire, wire2: Wire) -> float:
        """
        Calculate Euclidean distance between two wires.
        
        Args:
            wire1: First wire
            wire2: Second wire
            
        Returns:
            Distance between wires
        """
        dx = wire1.point.x - wire2.point.x
        dy = wire1.point.y - wire2.point.y
        return math.sqrt(dx*dx + dy*dy)
    
    def _perform_clustering(self, sorted_wires: List[Wire]):
        """
        Perform proximity-based clustering of wires.
        
        Args:
            sorted_wires: All wires sorted from top to bottom, left to right
        """
        available_wires = sorted_wires.copy()
        
        for cluster in self.wire_clusters:
            # Clear any existing wires in cluster
            cluster.wires.clear()
            
            if not available_wires:
                raise ValueError(f"Not enough wires for cluster {cluster.name}. "
                               f"Need {cluster.wire_count}, but no wires left.")
            
            # Start with the first available wire as seed
            seed_wire = available_wires[0]
            cluster.wires.append(seed_wire)
            available_wires.remove(seed_wire)
            
            # Find remaining wires for this cluster
            while len(cluster.wires) < cluster.wire_count:
                if not available_wires:
                    raise ValueError(f"Not enough wires for cluster {cluster.name}. "
                                   f"Need {cluster.wire_count}, but only have {len(cluster.wires)}.")
                
                # Find the closest wire to any wire already in the cluster
                closest_wire = None
                min_distance = float('inf')
                
                for cluster_wire in cluster.wires:
                    for candidate_wire in available_wires:
                        distance = self._calculate_distance(cluster_wire, candidate_wire)
                        if distance < min_distance:
                            min_distance = distance
                            closest_wire = candidate_wire
                
                if closest_wire is None:
                    raise ValueError(f"Cannot find wire close enough for cluster {cluster.name}")
                
                cluster.wires.append(closest_wire)
                available_wires.remove(closest_wire)
            
            # Sort wires within cluster for consistent ordering
            cluster.wires.sort(key=lambda w: (-w.point.y, w.point.x))
    
    def _get_physical_group_for_cluster(self, cluster: WireCluster):
        """
        Get the appropriate physical group for a cluster.
        
        Args:
            cluster: WireCluster object
            
        Returns:
            Appropriate PhysicalGroup instance
        """
        if cluster.current_sign == 1:
            return DOMAIN_COIL_POSITIVE
        elif cluster.current_sign == -1:
            return DOMAIN_COIL_NEGATIVE
        else:
            raise ValueError(f"Invalid current sign {cluster.current_sign} for cluster {cluster.name}")
    