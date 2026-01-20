from typing import List, Dict, Tuple
from svg_to_getdp.core.entities.outline import Outline
from svg_to_getdp.core.entities.physical_group import PhysicalGroup, DOMAIN_VA, DOMAIN_VI_IRON, DOMAIN_VI_AIR, BOUNDARY_GAMMA, BOUNDARY_OUT
from svg_to_getdp.core.entities.point import Point
from svg_to_getdp.interfaces.abstractions.outline_grouper_interface import OutlineGrouperInterface

class OutlineGrouper(OutlineGrouperInterface):
    """
    Groups outlines into hierarchical structure with containment relationships
    and assigns physical groups based on containment logic.
    """

    @staticmethod
    def group_outlines(outlines: List[Outline]) -> List[Dict]:
        """
        Main function to group outlines and assign physical groups.
        
        Args:
            outlines: List of outlines to process
            
        Returns:
            List of dictionaries, one per outline, with keys:
            - "holes": List of indices of outlines contained by this outline
            - "physical_groups": List of PhysicalGroup objects for this outline
        """
        if not outlines:
            return []
        
        # Get containment hierarchy
        containment_map = OutlineGrouper.get_containment_hierarchy(outlines)
        
        # Find the outermost outline (contains all others but is not contained by any)
        outermost_candidates = []
        for i in range(len(outlines)):
            # Count how many other outlines contain this one
            contained_by_count = sum(1 for j in range(len(outlines)) 
                                if i != j and i in containment_map[j])
            
            if contained_by_count == 0:
                outermost_candidates.append(i)
        
        # If multiple outermost candidates, choose the one with largest bounding box AREA
        if outermost_candidates:
            # Calculate areas for all candidates
            candidate_areas = []
            for idx in outermost_candidates:
                min_x, max_x, min_y, max_y = OutlineGrouper.get_outline_bounding_box(outlines[idx])
                area = (max_x - min_x) * (max_y - min_y)
                candidate_areas.append((idx, area))
            
            # Find the index with largest area
            outermost_idx = max(candidate_areas, key=lambda item: item[1])[0]
        else:
            raise ValueError("No outermost candidates found")
        
        # Classify all outlines
        classifications = [OutlineGrouper.classify_outline_color(outline) 
                        for outline in outlines]
        
        # Check which Va outlines are inside Vi outlines
        va_in_vi_flags = [False] * len(outlines)
        for i, (outline, classification) in enumerate(zip(outlines, classifications)):
            if classification == "va":
                # Check if this Va outline is inside any Vi outline
                for j, (other_outline, other_classification) in enumerate(zip(outlines, classifications)):
                    if i != j and (other_classification == "vi_iron" or other_classification == "vi_air"):
                        if OutlineGrouper.is_outline_inside_other(outline, other_outline):
                            va_in_vi_flags[i] = True
                            break
        
        # Build result dictionaries
        result = []
        for i, outline in enumerate(outlines):
            is_outermost = (i == outermost_idx)
            is_va_in_vi = va_in_vi_flags[i]
            
            # Get holes (contained outlines)
            holes = containment_map.get(i, [])
            
            # Get physical groups
            physical_groups = OutlineGrouper.get_physical_groups_for_outline(
                classification=classifications[i],
                is_outermost=is_outermost,
                is_va_in_vi=is_va_in_vi
            )
            
            result.append({
                "holes": holes,
                "physical_groups": physical_groups
            })
        
        return result
    
    @staticmethod
    def is_point_inside_outline(point: Point, outline: Outline, num_samples: int = 1000) -> bool:
        """
        Check if a point is inside a closed outline using ray casting algorithm.
        
        Args:
            point: The point to test
            outline: The closed outline
            num_samples: Number of samples for outline approximation
            
        Returns:
            True if point is inside the outline, False otherwise
        """
        if not outline.is_closed:
            return False
            
        # Sample points along the outline
        outline_points = outline.get_outline_points(num_samples)
        
        # Count intersections with horizontal ray to the right
        intersections = 0
        n = len(outline_points)
        
        for i in range(n):
            p1 = outline_points[i]
            p2 = outline_points[(i + 1) % n]
            
            # Check if point is on the edge (within tolerance)
            # This helps with floating-point precision issues
            if abs(p1.x - point.x) < 1e-10 and abs(p1.y - point.y) < 1e-10:
                return False  # Point is exactly on a vertex
                
            # Check if the segment is horizontal
            if abs(p1.y - p2.y) < 1e-10:
                # Horizontal edge - check if point is on this edge
                if abs(p1.y - point.y) < 1e-10 and \
                min(p1.x, p2.x) <= point.x <= max(p1.x, p2.x):
                    return False  # Point is on horizontal edge
                continue  # Horizontal edges don't affect ray-casting
            
            # Check if ray intersects the edge
            # First check if point is between the y-values of the edge
            if (p1.y > point.y) != (p2.y > point.y):
                # Calculate x-intersection of the edge with the horizontal line through point
                x_intersect = p1.x + (point.y - p1.y) * (p2.x - p1.x) / (p2.y - p1.y)
                
                # Check if intersection is to the right of the point
                if x_intersect > point.x + 1e-10:  # Add small tolerance
                    intersections += 1
                # If intersection is exactly at the point, point is on the edge
                elif abs(x_intersect - point.x) < 1e-10:
                    return False
                    
        return intersections % 2 == 1
    
    @staticmethod
    def get_outline_bounding_box(outline: Outline) -> Tuple[float, float, float, float]:
        """
        Get the bounding box of an outline.
        
        Args:
            outline: Outline with control points
            
        Returns:
            Tuple of (min_x, max_x, min_y, max_y)
            
        Raises:
            ValueError: If the outline has no control points
        """
        control_points = outline.control_points
        if not control_points:
            raise ValueError(f"Outline must have at least one control point. Got {len(control_points)} points.")
            
        min_x = min(p.x for p in control_points)
        max_x = max(p.x for p in control_points)
        min_y = min(p.y for p in control_points)
        max_y = max(p.y for p in control_points)
        
        return (min_x, max_x, min_y, max_y)
    
    @staticmethod
    def is_outline_inside_other(outline: Outline, outer_outline: Outline) -> bool:
        """
        Check if one outline is completely inside another.
        
        Args:
            outline: The inner outline candidate
            outer_outline: The potential outer outline
            
        Returns:
            True if outline is completely inside outer_outline
        """
        if not outline.is_closed or not outer_outline.is_closed:
            return False
            
        # Quick bounding box test - inner outline must be completely within outer outline's bbox
        inner_min_x, inner_max_x, inner_min_y, inner_max_y = OutlineGrouper.get_outline_bounding_box(outline)
        outer_min_x, outer_max_x, outer_min_y, outer_max_y = OutlineGrouper.get_outline_bounding_box(outer_outline)
        
        if not (inner_min_x >= outer_min_x and inner_max_x <= outer_max_x and
                inner_min_y >= outer_min_y and inner_max_y <= outer_max_y):
            return False
            
        # Sample points from the inner outline and check if they're all inside outer outline
        sample_points = outline.get_outline_points(num_points=10)
        for point in sample_points:
            if not OutlineGrouper.is_point_inside_outline(point, outer_outline):
                return False
                
        return True
    
    @staticmethod
    def get_containment_hierarchy(outlines: List[Outline]) -> Dict[int, List[int]]:
        """
        Determine containment hierarchy among outlines.
        
        Args:
            outlines: List of all outlines
            
        Returns:
            Dictionary mapping outline index to list of indices of its immediate children
        """
        n = len(outlines)
        containment_map = {i: [] for i in range(n)}
        
        # Calculate outline areas (approximated by bounding box)
        outline_areas = []
        for i, outline in enumerate(outlines):
            min_x, max_x, min_y, max_y = OutlineGrouper.get_outline_bounding_box(outline)
            area = (max_x - min_x) * (max_y - min_y)
            outline_areas.append((i, area))
        
        # Sort by area descending
        outline_areas.sort(key=lambda x: x[1], reverse=True)
        sorted_indices = [idx for idx, _ in outline_areas]
        
        # Check containment relationships - only assign immediate parents
        for i in range(n):
            outer_idx = sorted_indices[i]
            for j in range(i + 1, n):
                inner_idx = sorted_indices[j]
                
                # Check if inner is contained by outer
                if OutlineGrouper.is_outline_inside_other(
                    outlines[inner_idx], 
                    outlines[outer_idx]
                ):
                    # Check if inner outline already has a parent in the sorted list
                    # (i.e., check if there's another outline between outer and inner in the sorted list)
                    has_closer_parent = False
                    for k in range(i + 1, j):
                        potential_parent_idx = sorted_indices[k]
                        if OutlineGrouper.is_outline_inside_other(
                            outlines[inner_idx],
                            outlines[potential_parent_idx]
                        ):
                            has_closer_parent = True
                            break
                    
                    if not has_closer_parent:
                        containment_map[outer_idx].append(inner_idx)
        
        return containment_map
    
    @staticmethod
    def classify_outline_color(outline: Outline) -> str:
        """
        Classify an outline based on its color.

        Args:
            outline: Outline with color property
            
        Returns:
            String classification: "va", "vi_iron", or "vi_air"
        """
        if outline.color.name == "black":
            return "va"
        elif outline.color.name == "blue":
            return "vi_iron"
        elif outline.color.name == "green":
            return "vi_air"
        else:
            raise ValueError(f"Unknown outline color: {outline.color.name}")

    @staticmethod
    def get_physical_groups_for_outline(classification: str,
                                     is_outermost: bool = False,
                                     is_va_in_vi: bool = False) -> List[PhysicalGroup]:
        """
        Get physical groups for an outline based on classification and context.
        
        Args:
            outline: Outline
            classification: Outline classification from classify_outline_color
            is_outermost: Whether this is the outermost outline
            is_va_in_vi: Whether this Va outline is inside a Vi outline
            
        Returns:
            List of physical groups assigned to this outline
        """
        physical_groups = []
        
        # Assign domain physical group based on color/classification
        if classification == "va":
            if is_va_in_vi:
                # Va boundary inside Vi gets gamma boundary
                physical_groups.append(BOUNDARY_GAMMA)
            physical_groups.append(DOMAIN_VA)
            
        elif classification == "vi_iron":
            physical_groups.append(DOMAIN_VI_IRON)
            
        elif classification == "vi_air":
            physical_groups.append(DOMAIN_VI_AIR)
        
        # Add boundary_out if this is the outermost outline
        if is_outermost:
            physical_groups.append(BOUNDARY_OUT)
        
        return physical_groups
            