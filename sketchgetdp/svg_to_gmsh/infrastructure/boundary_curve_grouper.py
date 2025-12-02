from typing import List, Dict, Tuple
from ..core.entities.boundary_curve import BoundaryCurve
from ..core.entities.physical_group import PhysicalGroup, DOMAIN_VA, DOMAIN_VI_IRON, DOMAIN_VI_AIR, BOUNDARY_GAMMA, BOUNDARY_OUT
from ..core.entities.point import Point

class BoundaryCurveGrouper:
    """
    Groups boundary curves into hierarchical structure with containment relationships
    and assigns physical groups based on containment logic.
    """

    @staticmethod
    def group_boundary_curves(boundary_curves: List[BoundaryCurve]) -> List[Dict]:
        """
        Main function to group boundary curves and assign physical groups.
        
        Args:
            boundary_curves: List of boundary curves to process
            
        Returns:
            List of dictionaries, one per boundary curve, with keys:
            - "holes": List of indices of curves contained by this curve
            - "physical_groups": List of PhysicalGroup objects for this curve
        """
        if not boundary_curves:
            return []
        
        # Get containment hierarchy
        containment_map = BoundaryCurveGrouper.get_containment_hierarchy(boundary_curves)
        
        # Find the outermost curve (contains all others but is not contained by any)
        outermost_candidates = []
        for i in range(len(boundary_curves)):
            # Count how many other curves contain this one
            contained_by_count = sum(1 for j in range(len(boundary_curves)) 
                                if i != j and i in containment_map[j])
            
            if contained_by_count == 0:
                outermost_candidates.append(i)
        
        # If multiple outermost candidates, choose the one with largest bounding box AREA
        if outermost_candidates:
            # Calculate areas for all candidates
            candidate_areas = []
            for idx in outermost_candidates:
                min_x, max_x, min_y, max_y = BoundaryCurveGrouper.get_curve_bounding_box(boundary_curves[idx])
                area = (max_x - min_x) * (max_y - min_y)
                candidate_areas.append((idx, area))
            
            # Find the index with largest area
            outermost_idx = max(candidate_areas, key=lambda item: item[1])[0]
        else:
            raise ValueError("No outermost candidates found")
        
        # Classify all curves
        classifications = [BoundaryCurveGrouper.classify_curve_color(curve) 
                        for curve in boundary_curves]
        
        # Check which Va curves are inside Vi curves
        va_in_vi_flags = [False] * len(boundary_curves)
        
        for i, (curve, classification) in enumerate(zip(boundary_curves, classifications)):
            if classification == "va":
                # Check if this Va curve is inside any Vi curve
                for j, (other_curve, other_classification) in enumerate(zip(boundary_curves, classifications)):
                    if i != j and (other_classification == "vi_iron" or other_classification == "vi_air"):
                        if BoundaryCurveGrouper.is_curve_inside_other(curve, other_curve):
                            va_in_vi_flags[i] = True
                            break
        
        # Build result dictionaries
        result = []
        for i, curve in enumerate(boundary_curves):
            is_outermost = (i == outermost_idx)
            is_va_in_vi = va_in_vi_flags[i]
            
            # Get holes (contained curves)
            holes = containment_map.get(i, [])
            
            # Get physical groups
            physical_groups = BoundaryCurveGrouper.get_physical_groups_for_curve(
                curve=curve,
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
    def is_point_inside_boundary(point: Point, boundary: BoundaryCurve, num_samples: int = 1000) -> bool:
        """
        Check if a point is inside a closed boundary curve using ray casting algorithm.
        
        Args:
            point: The point to test
            boundary: The closed boundary curve
            num_samples: Number of samples for boundary approximation
            
        Returns:
            True if point is inside the boundary, False otherwise
        """
        if not boundary.is_closed:
            return False
            
        # Sample points along the boundary
        boundary_points = boundary.get_curve_points(num_samples)
        
        # Count intersections with horizontal ray to the right
        intersections = 0
        n = len(boundary_points)
        
        for i in range(n):
            p1 = boundary_points[i]
            p2 = boundary_points[(i + 1) % n]
            
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
    def get_curve_bounding_box(curve: BoundaryCurve) -> Tuple[float, float, float, float]:
        """
        Get the bounding box of a boundary curve.
        
        Args:
            curve: BoundaryCurve with control points
            
        Returns:
            Tuple of (min_x, max_x, min_y, max_y)
            
        Raises:
            ValueError: If the curve has no control points
        """
        control_points = curve.control_points
        if not control_points:
            raise ValueError(f"BoundaryCurve must have at least one control point. Got {len(control_points)} points.")
            
        min_x = min(p.x for p in control_points)
        max_x = max(p.x for p in control_points)
        min_y = min(p.y for p in control_points)
        max_y = max(p.y for p in control_points)
        
        return (min_x, max_x, min_y, max_y)
    
    @staticmethod
    def is_curve_inside_other(curve: BoundaryCurve, outer_curve: BoundaryCurve) -> bool:
        """
        Check if one boundary curve is completely inside another.
        
        Args:
            curve: The inner curve candidate
            outer_curve: The potential outer curve
            
        Returns:
            True if curve is completely inside outer_curve
        """
        if not curve.is_closed or not outer_curve.is_closed:
            return False
            
        # Quick bounding box test - inner curve must be completely within outer curve's bbox
        inner_min_x, inner_max_x, inner_min_y, inner_max_y = BoundaryCurveGrouper.get_curve_bounding_box(curve)
        outer_min_x, outer_max_x, outer_min_y, outer_max_y = BoundaryCurveGrouper.get_curve_bounding_box(outer_curve)
        
        if not (inner_min_x >= outer_min_x and inner_max_x <= outer_max_x and
                inner_min_y >= outer_min_y and inner_max_y <= outer_max_y):
            return False
            
        # Sample points from the inner curve and check if they're all inside outer curve
        sample_points = curve.get_curve_points(num_points=10)
        for point in sample_points:
            if not BoundaryCurveGrouper.is_point_inside_boundary(point, outer_curve):
                return False
                
        return True
    
    @staticmethod
    def get_containment_hierarchy(boundary_curves: List[BoundaryCurve]) -> Dict[int, List[int]]:
        """
        Determine containment hierarchy among boundary curves.
        
        Args:
            boundary_curves: List of all boundary curves
            
        Returns:
            Dictionary mapping curve index to list of indices of its immediate children
        """
        n = len(boundary_curves)
        containment_map = {i: [] for i in range(n)}
        
        # Sort curves by area (approximated by bounding box area) from largest to smallest
        curve_areas = []
        for i, curve in enumerate(boundary_curves):
            min_x, max_x, min_y, max_y = BoundaryCurveGrouper.get_curve_bounding_box(curve)
            area = (max_x - min_x) * (max_y - min_y)
            curve_areas.append((i, area))
        
        # Sort by area descending
        curve_areas.sort(key=lambda x: x[1], reverse=True)
        sorted_indices = [idx for idx, _ in curve_areas]
        
        # Check containment relationships - only assign immediate parents
        for i in range(n):
            outer_idx = sorted_indices[i]
            for j in range(i + 1, n):
                inner_idx = sorted_indices[j]
                
                # Check if inner is contained by outer
                if BoundaryCurveGrouper.is_curve_inside_other(
                    boundary_curves[inner_idx], 
                    boundary_curves[outer_idx]
                ):
                    # Check if inner curve already has a parent in the sorted list
                    # (i.e., check if there's another curve between outer and inner in the sorted list)
                    has_closer_parent = False
                    for k in range(i + 1, j):
                        potential_parent_idx = sorted_indices[k]
                        if BoundaryCurveGrouper.is_curve_inside_other(
                            boundary_curves[inner_idx],
                            boundary_curves[potential_parent_idx]
                        ):
                            has_closer_parent = True
                            break
                    
                    if not has_closer_parent:
                        containment_map[outer_idx].append(inner_idx)
        
        return containment_map
    
    @staticmethod
    def classify_curve_color(curve: BoundaryCurve) -> str:
        """
        Classify a boundary curve based on its color.
        
        Args:
            curve: Boundary curve with color property
            
        Returns:
            String classification: "va", "vi_iron", or "vi_air"
        """
        if curve.color.name == "black":
            return "va"
        elif curve.color.name == "blue":
            return "vi_iron"
        elif curve.color.name == "green":
            return "vi_air"
        else:
            raise ValueError(f"Unknown curve color: {curve.color.name}")
    
    @staticmethod
    def get_physical_groups_for_curve(curve: BoundaryCurve, 
                                     classification: str,
                                     is_outermost: bool = False,
                                     is_va_in_vi: bool = False) -> List[PhysicalGroup]:
        """
        Get physical groups for a boundary curve based on classification and context.
        
        Args:
            curve: Boundary curve
            classification: Curve classification from classify_curve_color
            is_outermost: Whether this is the outermost boundary
            is_va_in_vi: Whether this Va curve is inside a Vi curve
            
        Returns:
            List of physical groups assigned to this curve
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
        
        # Add boundary_out if this is the outermost curve
        if is_outermost:
            physical_groups.append(BOUNDARY_OUT)
        
        return physical_groups
    
    @staticmethod
    def print_grouping_summary(boundary_curves: List[BoundaryCurve], grouping_result: List[Dict]):
        """
        Print a summary of the grouping results for debugging.
        
        Args:
            boundary_curves: Original boundary curves
            grouping_result: Result from group_boundary_curves
        """
        print("=" * 80)
        print("BOUNDARY CURVE GROUPING SUMMARY")
        print("=" * 80)
        
        for i, (curve, group_info) in enumerate(zip(boundary_curves, grouping_result)):
            print(f"\nCurve {i}:")
            print(f"  Color: {curve.color.name}")
            print(f"  Classification: {BoundaryCurveGrouper.classify_curve_color(curve)}")
            print(f"  Holes (contained curves): {group_info['holes']}")
            print(f"  Physical Groups:")
            for pg in group_info['physical_groups']:
                print(f"    - {pg.name} (type: {pg.group_type}, value: {pg.value})")
        
        print("\n" + "=" * 80)
        print("CONTAINMENT HIERARCHY")
        print("=" * 80)
        
        # Build tree structure
        n = len(boundary_curves)
        has_parent = [False] * n
        
        for i in range(n):
            for hole_idx in grouping_result[i]["holes"]:
                has_parent[hole_idx] = True
        
        roots = [i for i in range(n) if not has_parent[i]]
        
        def print_tree(node_idx: int, depth: int = 0):
            indent = "  " * depth
            curve = boundary_curves[node_idx]
            classification = BoundaryCurveGrouper.classify_curve_color(curve)
            print(f"{indent}└─ Curve {node_idx} ({curve.color.name}, {classification})")
            
            for hole_idx in grouping_result[node_idx]["holes"]:
                print_tree(hole_idx, depth + 1)
        
        for root_idx in roots:
            print_tree(root_idx)
            