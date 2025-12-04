"""
Boundary curve meshing module for Gmsh integration.
Converts BoundaryCurve objects into Gmsh geometry with proper physical groups.
"""

from typing import List, Dict, Any
from ..core.entities.boundary_curve import BoundaryCurve
from ..core.entities.point import Point
from ..core.entities.physical_group import PhysicalGroup
from ..interfaces.abstractions.boundary_curve_mesher_interface import BoundaryCurveMesherInterface

class BoundaryCurveMesher(BoundaryCurveMesherInterface):
    """
    Meshes BoundaryCurve objects in Gmsh with proper physical group assignment.
    Handles both straight lines and 2nd order Bézier curves.
    """
    
    def __init__(self):
        """
        Initialize the mesher with a Gmsh factory.
        
        Args:
            factory: Gmsh geometry factory (gmsh.model.geo)
        """
        self._point_tags = {}  # Maps Point objects to Gmsh point tags
        self._curve_loops = {}  # Maps boundary curve indices to Gmsh curve loop tags
        self._surface_tags = {}  # Maps boundary curve indices to Gmsh surface tags
        self._created_points = {}  # Tracks created points to avoid duplicates
        self._curve_tags_per_boundary = {}  # Store curve tags per boundary curve index
        self._processing_order = []  # Store the order in which boundary curves were processed
        
        # Track physical groups by type
        self._physical_groups_by_type = {
            'boundary': {},  # physical_group.value -> list of curve tags
            'domain': {}     # physical_group.value -> list of surface tags
        }
        
    def mesh_boundary_curves(self,
                           factory: Any,  # Add factory parameter
                           boundary_curves: List[BoundaryCurve], 
                           properties: List[Dict[str, Any]]) -> None:
        """
        Mesh all boundary curves with their properties.
        Processes boundary curves from innermost to outermost to ensure
        holes are created before the surfaces that contain them.
        
        Args:
            boundary_curves: List of BoundaryCurve objects to mesh
            properties: List of dictionaries with "holes" and "physical_groups" keys
                       Each dictionary corresponds to the boundary curve at the same index
        """
        self.factory = factory
        
        if len(boundary_curves) != len(properties):
            raise ValueError(
                f"Number of boundary curves ({len(boundary_curves)}) "
                f"must match number of property dictionaries ({len(properties)})"
            )
        
        # Determine processing order from innermost to outermost
        self._processing_order = self._get_processing_order(boundary_curves, properties)
        
        # Process boundary curves in topological order (inner to outer)
        for idx in self._processing_order:
            boundary_curve = boundary_curves[idx]
            props = properties[idx]
            self._mesh_single_boundary_curve(idx, boundary_curve, props)
        
        # Now collect all entities by physical group type
        for idx in self._processing_order:
            boundary_curve = boundary_curves[idx]
            props = properties[idx]
            self._collect_physical_groups(idx, boundary_curve, props)
        
        # After all curves and surfaces are created, assign physical groups
        self._assign_physical_groups()
    
    def _get_processing_order(self, 
                            boundary_curves: List[BoundaryCurve], 
                            properties: List[Dict[str, Any]]) -> List[int]:
        """
        Determine the processing order from innermost to outermost boundary curves.
        
        Args:
            boundary_curves: List of BoundaryCurve objects
            properties: List of property dictionaries
            
        Returns:
            List of indices in processing order (innermost to outermost)
        """
        n = len(boundary_curves)
        
        # Build dependency graph: edge from hole to container
        # If A is a hole in B, then A must be processed before B
        adjacency = [[] for _ in range(n)]
        
        for i in range(n):
            if "holes" in properties[i] and properties[i]["holes"]:
                hole_indices = properties[i]["holes"]
                if isinstance(hole_indices, list):
                    for hole_idx in hole_indices:
                        if 0 <= hole_idx < n:
                            # hole_idx must be processed before i
                            adjacency[hole_idx].append(i)
        
        # Calculate in-degree for Kahn's algorithm
        in_degree = [0] * n
        for i in range(n):
            for neighbor in adjacency[i]:
                in_degree[neighbor] += 1
        
        # Start with nodes that have no dependencies (innermost)
        queue = [i for i in range(n) if in_degree[i] == 0]
        processing_order = []
        
        while queue:
            current = queue.pop(0)
            processing_order.append(current)
            
            # For each boundary that depends on this one (containers)
            for neighbor in adjacency[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        if len(processing_order) != n:
            # Cycle detected
            print("Warning: Could not determine topological order. Using input order.")
            return list(range(n))
        
        return processing_order
    
    def _mesh_single_boundary_curve(self, 
                                   idx: int, 
                                   boundary_curve: BoundaryCurve, 
                                   properties: Dict[str, Any]) -> None:
        """
        Mesh a single boundary curve.
        
        Steps:
        1. Draw points
        2. Draw lines (= boundary)
        3. Define curve loop (= potential hole in other domain)
        4. Define curve loop list (curve loop with holes!)
        5. Define plane surface (= surface)
        """
        # Step 1: Create points for all unique control points
        point_tags = []
        for point in boundary_curve.unique_control_points:
            tag = self._create_or_get_point(point)
            point_tags.append(tag)
        
        # Step 2: Create curves (lines and Bézier curves)
        curve_tags = []
        segment_start_idx = 0
        
        for segment in boundary_curve.bezier_segments:
            # Check if segment is a straight line (degree 1 or collinear control points)
            if segment.degree == 1:
                # Straight line segment - use simple line
                line_tag = self.factory.addLine(
                    point_tags[segment_start_idx],
                    point_tags[segment_start_idx + 1]
                )
                curve_tags.append(line_tag)
                segment_start_idx += 1  # Only move by 1 since degree 1 has 2 points
            else:
                # Higher degree Bézier curve
                # For 2nd order Bézier: 3 points
                # For higher degrees: degree + 1 points
                segment_point_tags = point_tags[segment_start_idx:segment_start_idx + segment.degree + 1]
                
                # Create compound Bézier curve in Gmsh
                bezier_tag = self.factory.addBezier(segment_point_tags)
                curve_tags.append(bezier_tag)
                segment_start_idx += segment.degree  # Move by degree for next segment
        
        # Store curve tags for this specific boundary curve
        self._curve_tags_per_boundary[idx] = curve_tags
        
        # Step 3: Define curve loop (for this boundary curve)
        curve_loop_tag = self.factory.addCurveLoop(curve_tags)
        self._curve_loops[idx] = curve_loop_tag
        
        # Step 4: Create curve loop list (main loop + holes)
        curve_loops_for_surface = [curve_loop_tag]
        
        # Add hole loops if specified
        if "holes" in properties and properties["holes"]:
            hole_indices = properties["holes"]
            if isinstance(hole_indices, list):
                for hole_idx in hole_indices:
                    # The hole should already be created since we process inner to outer
                    if hole_idx in self._curve_loops:
                        curve_loops_for_surface.append(self._curve_loops[hole_idx])
                    else:
                        raise ValueError(
                            f"Hole boundary curve {hole_idx} referenced by "
                            f"boundary curve {idx} has not been created yet. "
                            f"Make sure holes are defined correctly."
                        )
        
        # Step 5: Define plane surface
        surface_tag = self.factory.addPlaneSurface(curve_loops_for_surface)
        self._surface_tags[idx] = surface_tag
    
    def _create_or_get_point(self, point: Point) -> int:
        """
        Create a point in Gmsh or return existing tag if point already exists.
        
        Args:
            point: Point object with x, y coordinates
            
        Returns:
            Gmsh point tag
        """
        # Use Point's __eq__ method for comparison with proper tolerance
        for existing_point, tag in self._created_points.items():
            if existing_point == point:  # Uses math.isclose() with default tolerances
                return tag
        
        # Point doesn't exist, create it
        point_tag = self.factory.addPoint(point.x, point.y, 0.0)
        self._created_points[point] = point_tag
        return point_tag
    
    def _collect_physical_groups(self, 
                               idx: int, 
                               boundary_curve: BoundaryCurve, 
                               properties: Dict[str, Any]) -> None:
        """
        Collect entities that belong to each physical group type.
        
        Args:
            idx: Index of the boundary curve
            boundary_curve: BoundaryCurve object
            properties: Dictionary with "physical_groups" key
        """
        if "physical_groups" not in properties:
            return
        
        physical_groups = properties["physical_groups"]
        
        if not isinstance(physical_groups, list):
            physical_groups = [physical_groups]
        
        for pg in physical_groups:
            if not isinstance(pg, PhysicalGroup):
                raise TypeError(f"Physical group must be PhysicalGroup instance, got {type(pg)}")
            
            if pg.is_boundary():
                # Collect curve tags for this boundary group
                if idx in self._curve_tags_per_boundary:
                    if pg.value not in self._physical_groups_by_type['boundary']:
                        self._physical_groups_by_type['boundary'][pg.value] = []
                    self._physical_groups_by_type['boundary'][pg.value].extend(
                        self._curve_tags_per_boundary[idx]
                    )
                    
            elif pg.is_domain():
                # Collect surface tag for this domain group
                if idx in self._surface_tags:
                    if pg.value not in self._physical_groups_by_type['domain']:
                        self._physical_groups_by_type['domain'][pg.value] = []
                    self._physical_groups_by_type['domain'][pg.value].append(
                        self._surface_tags[idx]
                    )
    
    def _assign_physical_groups(self) -> None:
        """
        Assign physical groups after all entities are collected.
        Creates one physical group per type with all relevant entities.
        """
        # Assign boundary groups (1D curves)
        for physical_group_value, curve_tags in self._physical_groups_by_type['boundary'].items():
            if curve_tags:
                # Remove duplicates while preserving order
                unique_curve_tags = list(dict.fromkeys(curve_tags))
                self.factory.addPhysicalGroup(1, unique_curve_tags, physical_group_value)
                print(f"Created boundary physical group (tag {physical_group_value}) "
                      f"with {len(unique_curve_tags)} curves")
        
        # Assign domain groups (2D surfaces)
        for physical_group_value, surface_tags in self._physical_groups_by_type['domain'].items():
            if surface_tags:
                # Remove duplicates while preserving order
                unique_surface_tags = list(dict.fromkeys(surface_tags))
                self.factory.addPhysicalGroup(2, unique_surface_tags, physical_group_value)
                print(f"Created domain physical group (tag {physical_group_value}) "
                      f"with {len(unique_surface_tags)} surfaces")
    
    def get_processing_order(self) -> List[int]:
        """
        Get the order in which boundary curves were processed.
        
        Returns:
            List of indices in processing order (innermost to outermost)
        """
        return self._processing_order.copy()
    
    def get_curve_loop_tag(self, idx: int) -> int:
        """
        Get the curve loop tag for a boundary curve.
        
        Args:
            idx: Index of the boundary curve
            
        Returns:
            Gmsh curve loop tag
        """
        if idx not in self._curve_loops:
            raise KeyError(f"No curve loop found for boundary curve index {idx}")
        return self._curve_loops[idx]
    
    def get_surface_tag(self, idx: int) -> int:
        """
        Get the surface tag for a boundary curve.
        
        Args:
            idx: Index of the boundary curve
            
        Returns:
            Gmsh surface tag
        """
        if idx not in self._surface_tags:
            raise KeyError(f"No surface found for boundary curve index {idx}")
        return self._surface_tags[idx]
    
    def get_curve_tags(self, idx: int) -> List[int]:
        """
        Get the curve tags for a boundary curve.
        
        Args:
            idx: Index of the boundary curve
            
        Returns:
            List of Gmsh curve tags
        """
        if idx not in self._curve_tags_per_boundary:
            raise KeyError(f"No curve tags found for boundary curve index {idx}")
        return self._curve_tags_per_boundary[idx].copy()
    
    def get_physical_group_summary(self) -> str:
        """
        Generate a summary of created physical groups.
        
        Returns:
            Formatted summary string
        """
        summary = ["Boundary Curve Physical Group Summary:"]
        summary.append("-" * 50)
        
        # Boundary groups
        boundary_count = len(self._physical_groups_by_type['boundary'])
        summary.append(f"Boundary Groups (1D curves): {boundary_count}")
        for pg_value, curve_tags in self._physical_groups_by_type['boundary'].items():
            unique_tags = list(dict.fromkeys(curve_tags))
            summary.append(f"  Tag {pg_value}: {len(unique_tags)} curves")
        
        # Domain groups
        domain_count = len(self._physical_groups_by_type['domain'])
        summary.append(f"Domain Groups (2D surfaces): {domain_count}")
        for pg_value, surface_tags in self._physical_groups_by_type['domain'].items():
            unique_tags = list(dict.fromkeys(surface_tags))
            summary.append(f"  Tag {pg_value}: {len(unique_tags)} surfaces")
        
        summary.append("-" * 50)
        return "\n".join(summary)
    
    def clear(self) -> None:
        """
        Clear internal state.
        """
        self._point_tags.clear()
        self._curve_loops.clear()
        self._surface_tags.clear()
        self._created_points.clear()
        self._curve_tags_per_boundary.clear()
        self._processing_order.clear()
        self._physical_groups_by_type['boundary'].clear()
        self._physical_groups_by_type['domain'].clear()