"""
Debug writer for boundary curve grouping operations.
"""

import os
from typing import List, Dict
from svg_to_getdp.core.entities.boundary_curve import BoundaryCurve


class BoundaryCurveGrouperDebugWriter:
    """Debug writer for boundary curve grouping operations."""
    
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
    
    def write_grouping_debug_info(
        self,
        svg_file_path: str,
        boundary_curves: List[BoundaryCurve],
        grouping_result: List[Dict],
        grouper_instance: 'BoundaryCurveGrouper'
    ) -> str:
        """
        Write debug information for boundary curve grouping.
        
        Args:
            svg_file_path: Path to the SVG file being processed
            boundary_curves: List of boundary curves
            grouping_result: Result from BoundaryCurveGrouper.group_boundary_curves()
            grouper_instance: The BoundaryCurveGrouper instance used
            
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
        debug_file = self._get_debug_filename("boundary_curve_grouping_debug")
        
        # Write debug information
        with open(debug_file, 'w') as f:
            self._write_header(f, boundary_curves)
            self._write_grouping_summary(f, boundary_curves, grouping_result, grouper_instance)
            self._write_containment_hierarchy(f, boundary_curves, grouping_result, grouper_instance)
        
        print(f"Boundary curve grouping debug information written to: {debug_file}")
                
        return debug_file
    
    def _get_debug_filename(self, prefix: str, extension: str = ".txt") -> str:
        """Generate a debug filename with timestamp."""
        if not self._svg_name:
            raise ValueError("SVG file not set. Call set_svg_file() first.")
        
        debug_dir = "debug"
        return f"{debug_dir}/{prefix}_{self._svg_name}_{self._shared_timestamp}{extension}"
    
    def _write_header(self, file_obj, boundary_curves: List[BoundaryCurve]):
        """Write a header section to the debug file."""
        file_obj.write("=" * 80 + "\n")
        file_obj.write("BOUNDARY CURVE GROUPING DEBUG\n")
        file_obj.write("=" * 80 + "\n\n")
        file_obj.write(f"SVG File: {self._svg_file_path}\n")
        file_obj.write(f"Timestamp: {self._shared_timestamp}\n")
        
        # Count curves by type
        va_count = sum(1 for curve in boundary_curves if curve.color.name == "black")
        vi_iron_count = sum(1 for curve in boundary_curves if curve.color.name == "blue")
        vi_air_count = sum(1 for curve in boundary_curves if curve.color.name == "green")
        
        file_obj.write(f"Total Boundary Curves: {len(boundary_curves)}\n")
        file_obj.write(f"  - Va curves (black): {va_count}\n")
        file_obj.write(f"  - Vi-iron curves (blue): {vi_iron_count}\n")
        file_obj.write(f"  - Vi-air curves (green): {vi_air_count}\n\n")
    
    def _write_grouping_summary(self, file_obj, boundary_curves, grouping_result, grouper_instance):
        """Write the main grouping summary similar to print_grouping_summary."""
        file_obj.write("=" * 80 + "\n")
        file_obj.write("BOUNDARY CURVE GROUPING SUMMARY\n")
        file_obj.write("=" * 80 + "\n\n")
        
        for i, (curve, group_info) in enumerate(zip(boundary_curves, grouping_result)):
            file_obj.write(f"Curve {i}:\n")
            file_obj.write(f"  Color: {curve.color.name}\n")
            file_obj.write(f"  Classification: {grouper_instance.classify_curve_color(curve)}\n")
            file_obj.write(f"  Is Closed: {curve.is_closed}\n")
            file_obj.write(f"  Bezier Segments: {len(curve.bezier_segments)}\n")
            file_obj.write(f"  Control Points: {len(curve.control_points)}\n")
            file_obj.write(f"  Holes (contained curves): {group_info['holes']}\n")
            file_obj.write(f"  Physical Groups ({len(group_info['physical_groups'])}):\n")
            for pg in group_info['physical_groups']:
                file_obj.write(f"    - {pg.name} (type: {pg.group_type}, value: {pg.value})\n")
            file_obj.write("\n")
    
    def _write_containment_hierarchy(self, file_obj, boundary_curves, grouping_result, grouper_instance):
        """Write the containment hierarchy tree."""
        file_obj.write("=" * 80 + "\n")
        file_obj.write("CONTAINMENT HIERARCHY\n")
        file_obj.write("=" * 80 + "\n\n")
        
        n = len(boundary_curves)
        has_parent = [False] * n
        
        for i in range(n):
            for hole_idx in grouping_result[i]["holes"]:
                has_parent[hole_idx] = True
        
        roots = [i for i in range(n) if not has_parent[i]]
        
        def write_tree(node_idx: int, depth: int = 0):
            indent = "  " * depth
            curve = boundary_curves[node_idx]
            classification = grouper_instance.classify_curve_color(curve)
            
            # Get bounding box
            try:
                min_x, max_x, min_y, max_y = grouper_instance.get_curve_bounding_box(curve)
                bbox_info = f"bbox: [{min_x:.3f}, {max_x:.3f}] x [{min_y:.3f}, {max_y:.3f}]"
            except Exception:
                bbox_info = "bbox: N/A"
            
            file_obj.write(f"{indent}└─ Curve {node_idx} ({curve.color.name}, {classification}, {bbox_info})\n")
            
            for hole_idx in grouping_result[node_idx]["holes"]:
                write_tree(hole_idx, depth + 1)
        
        if not roots:
            file_obj.write("No root curves found (all curves have parents)\n")
        else:
            for root_idx in roots:
                write_tree(root_idx)
        
        file_obj.write("\n")
        