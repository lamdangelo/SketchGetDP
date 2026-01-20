"""
Debug writer for outline grouping operations.
"""

import os
from typing import List, Dict
from svg_to_getdp.core.entities.outline import Outline


class OutlineGrouperDebugWriter:
    """Debug writer for outline grouping operations."""
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
        outlines: List[Outline],
        grouping_result: List[Dict],
        grouper_instance: 'OutlineGrouper'
    ) -> str:
        """
        Write debug information for outline grouping.
        
        Args:
            svg_file_path: Path to the SVG file being processed
            outlines: List of outlines
            grouping_result: Result from OutlineGrouper.group_outlines()
            grouper_instance: The OutlineGrouper instance used
            
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
        debug_file = self._get_debug_filename("outline_grouping_debug")
        
        # Write debug information
        with open(debug_file, 'w') as f:
            self._write_header(f, outlines)
            self._write_grouping_summary(f, outlines, grouping_result, grouper_instance)
            self._write_containment_hierarchy(f, outlines, grouping_result, grouper_instance)

        print(f"Outline grouping debug information written to: {debug_file}")
                
        return debug_file
    
    def _get_debug_filename(self, prefix: str, extension: str = ".txt") -> str:
        """Generate a debug filename with timestamp."""
        if not self._svg_name:
            raise ValueError("SVG file not set. Call set_svg_file() first.")
        
        debug_dir = "debug"
        return f"{debug_dir}/{prefix}_{self._svg_name}_{self._shared_timestamp}{extension}"
    
    def _write_header(self, file_obj, outlines: List[Outline]):
        """Write a header section to the debug file."""
        file_obj.write("=" * 80 + "\n")
        file_obj.write("OUTLINE GROUPING DEBUG\n")
        file_obj.write("=" * 80 + "\n\n")
        file_obj.write(f"SVG File: {self._svg_file_path}\n")
        file_obj.write(f"Timestamp: {self._shared_timestamp}\n")
        
        # Count outlines by type
        va_count = sum(1 for outline in outlines if outline.color.name == "black")
        vi_iron_count = sum(1 for outline in outlines if outline.color.name == "blue")
        vi_air_count = sum(1 for outline in outlines if outline.color.name == "green")
        
        file_obj.write(f"Total Outlines: {len(outlines)}\n")
        file_obj.write(f"  - Va outlines (black): {va_count}\n")
        file_obj.write(f"  - Vi-iron outlines (blue): {vi_iron_count}\n")
        file_obj.write(f"  - Vi-air outlines (green): {vi_air_count}\n\n")

    def _write_grouping_summary(self, file_obj, outlines, grouping_result, grouper_instance):
        """Write the main grouping summary similar to print_grouping_summary."""
        file_obj.write("=" * 80 + "\n")
        file_obj.write("OUTLINE GROUPING SUMMARY\n")
        file_obj.write("=" * 80 + "\n\n")

        for i, (outline, group_info) in enumerate(zip(outlines, grouping_result)):
            file_obj.write(f"Outline {i}:\n")
            file_obj.write(f"  Color: {outline.color.name}\n")
            file_obj.write(f"  Classification: {grouper_instance.classify_outline_color(outline)}\n")
            file_obj.write(f"  Is Closed: {outline.is_closed}\n")
            file_obj.write(f"  Bezier Segments: {len(outline.bezier_segments)}\n")
            file_obj.write(f"  Control Points: {len(outline.control_points)}\n")
            file_obj.write(f"  Holes (contained outlines): {group_info['holes']}\n")
            file_obj.write(f"  Physical Groups ({len(group_info['physical_groups'])}):\n")
            for pg in group_info['physical_groups']:
                file_obj.write(f"    - {pg.name} (type: {pg.group_type}, value: {pg.value})\n")
            file_obj.write("\n")
    
    def _write_containment_hierarchy(self, file_obj, outlines, grouping_result, grouper_instance):
        """Write the containment hierarchy tree."""
        file_obj.write("=" * 80 + "\n")
        file_obj.write("CONTAINMENT HIERARCHY\n")
        file_obj.write("=" * 80 + "\n\n")

        n = len(outlines)
        has_parent = [False] * n
        
        for i in range(n):
            for hole_idx in grouping_result[i]["holes"]:
                has_parent[hole_idx] = True
        
        roots = [i for i in range(n) if not has_parent[i]]
        
        def write_tree(node_idx: int, depth: int = 0):
            indent = "  " * depth
            outline = outlines[node_idx]
            classification = grouper_instance.classify_outline_color(outline)
            
            # Get bounding box
            try:
                min_x, max_x, min_y, max_y = grouper_instance.get_outline_bounding_box(outline)
                bbox_info = f"bbox: [{min_x:.3f}, {max_x:.3f}] x [{min_y:.3f}, {max_y:.3f}]"
            except Exception:
                bbox_info = "bbox: N/A"
            
            file_obj.write(f"{indent}└─ Outline {node_idx} ({outline.color.name}, {classification}, {bbox_info})\n")
            
            for hole_idx in grouping_result[node_idx]["holes"]:
                write_tree(hole_idx, depth + 1)
        
        if not roots:
            file_obj.write("No root outlines found (all outlines have parents)\n")
        else:
            for root_idx in roots:
                write_tree(root_idx)
        
        file_obj.write("\n")
        