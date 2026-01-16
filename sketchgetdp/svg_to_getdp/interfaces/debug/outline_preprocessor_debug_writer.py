"""
Debug writer for outline preprocessing operations.
Captures processing order, created entities, and physical group assignments.
"""

import os
from typing import List, Dict, Any
from sketchgetdp.svg_to_getdp.core.entities.outline import Outline


class OutlinePreprocessorDebugWriter:
    """Debug writer for outline preprocessing operations."""
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
    
    def write_preprocessing_debug_info(
        self,
        svg_file_path: str,
        outlines: List[Outline],
        preprocessor_instance: 'OutlinePreprocessor',
        gmsh_results: Dict[str, Any]
    ) -> str:
        """
        Write debug information for outline preprocessing.
        
        Args:
            svg_file_path: Path to the SVG file being processed
            outlines: List of outlines that were preprocessed
            preprocessor_instance: The OutlinePreprocessor instance used
            gmsh_results: Results dictionary from ConvertGeometryToGmsh.execute()
            
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
        debug_file = self._get_debug_filename("outline_preprocessing_debug")
        
        # Write debug information
        with open(debug_file, 'w') as f:
            self._write_header(f, outlines)
            self._write_processing_order(f, preprocessor_instance, outlines)
            self._write_entity_summary(f, preprocessor_instance)
            self._write_physical_groups(f, preprocessor_instance)
        
        print(f"Outline preprocessing debug information written to: {debug_file}")
                
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
        file_obj.write("OUTLINE PREPROCESSING DEBUG\n")
        file_obj.write("=" * 80 + "\n\n")
        file_obj.write(f"SVG File: {self._svg_file_path}\n")
        file_obj.write(f"Timestamp: {self._shared_timestamp}\n")
        file_obj.write(f"Total Outlines: {len(outlines)}\n")
        file_obj.write(f"Output Mesh: {self._svg_name}.msh\n\n")
    
    def _write_processing_order(self, file_obj, preprocessor_instance, outlines: List[Outline]):
        """Write the processing order (innermost to outermost)."""
        file_obj.write("=" * 80 + "\n")
        file_obj.write("PROCESSING ORDER (INNERMOST TO OUTERMOST)\n")
        file_obj.write("=" * 80 + "\n\n")
        
        try:
            processing_order = preprocessor_instance.get_processing_order()
            if processing_order:
                for i, outline_idx in enumerate(processing_order):
                    if 0 <= outline_idx < len(outlines):
                        outline = outlines[outline_idx]
                        file_obj.write(f"{i+1}. Outline {outline_idx} ({outline.color.name}):\n")
                        file_obj.write(f"   - Segments: {len(outline.bezier_segments)}\n")
                        file_obj.write(f"   - Control Points: {len(outline.control_points)}\n")
                        file_obj.write(f"   - Unique Points: {len(outline.unique_control_points)}\n")
                        file_obj.write(f"   - Is Closed: {outline.is_closed}\n")
                        
                        # Get curve loop tag if available
                        try:
                            curve_loop_tag = preprocessor_instance.get_curve_loop_tag(outline_idx)
                            file_obj.write(f"   - Curve Loop Tag: {curve_loop_tag}\n")
                        except (KeyError, AttributeError):
                            pass
                        file_obj.write("\n")
            else:
                file_obj.write("No processing order available (using input order)\n")
        except AttributeError:
            file_obj.write("Processing order not available in preprocessor instance\n")

        file_obj.write("\n")
    
    def _write_entity_summary(self, file_obj, preprocessor_instance):
        """Write summary of created entities (points, curves, surfaces)."""
        file_obj.write("=" * 80 + "\n")
        file_obj.write("ENTITY CREATION SUMMARY\n")
        file_obj.write("=" * 80 + "\n\n")
        
        # Try to access internal tracking (if attributes exist)
        try:
            # Points
            if hasattr(preprocessor_instance, '_created_points'):
                points_count = len(preprocessor_instance._created_points)
                file_obj.write(f"Created Points: {points_count}\n")
                # Write first few points as example
                file_obj.write("  Sample Points (Point -> Gmsh Tag):\n")
                for point, tag in list(preprocessor_instance._created_points.items())[:5]:
                    file_obj.write(f"    ({point.x:.6f}, {point.y:.6f}) -> {tag}\n")
                if points_count > 5:
                    file_obj.write(f"    ... and {points_count - 5} more points\n")
                file_obj.write("\n")

            # Curve tags per outline
            if hasattr(preprocessor_instance, '_curve_tags_per_outline'):
                total_curves = 0
                for idx, curve_tags in preprocessor_instance._curve_tags_per_outline.items():
                    total_curves += len(curve_tags)
                file_obj.write(f"Total Created Curves: {total_curves}\n")
                
                file_obj.write("  Curves per Outline:\n")
                for idx, curve_tags in preprocessor_instance._curve_tags_per_outline.items():
                    file_obj.write(f"    Outline {idx}: {len(curve_tags)} curves (tags: {curve_tags})\n")
                file_obj.write("\n")
            
            # Curve loops
            if hasattr(preprocessor_instance, '_curve_loops'):
                file_obj.write(f"Created Curve Loops: {len(preprocessor_instance._curve_loops)}\n")
                for idx, loop_tag in preprocessor_instance._curve_loops.items():
                    file_obj.write(f"    Outline {idx}: Curve Loop Tag {loop_tag}\n")
                file_obj.write("\n")
            
            # Surfaces
            if hasattr(preprocessor_instance, '_surface_tags'):
                file_obj.write(f"Created Surfaces: {len(preprocessor_instance._surface_tags)}\n")
                for idx, surface_tag in preprocessor_instance._surface_tags.items():
                    file_obj.write(f"    Outline {idx}: Surface Tag {surface_tag}\n")
                file_obj.write("\n")
                
        except Exception as e:
            file_obj.write(f"Unable to extract entity details: {e}\n")
        
        file_obj.write("\n")
    
    def _write_physical_groups(self, file_obj, preprocessor_instance):
        """Write physical group assignments."""
        file_obj.write("=" * 80 + "\n")
        file_obj.write("PHYSICAL GROUP ASSIGNMENTS\n")
        file_obj.write("=" * 80 + "\n\n")
        
        try:
            # Try to get the summary from the preprocessor instance
            if hasattr(preprocessor_instance, 'get_physical_group_summary'):
                summary = preprocessor_instance.get_physical_group_summary()
                file_obj.write(summary + "\n")
            else:
                file_obj.write("Physical group summary method not available\n")
                
            # Also try to access internal tracking if available
            if hasattr(preprocessor_instance, '_physical_groups_by_type'):
                pg_by_type = preprocessor_instance._physical_groups_by_type
                
                # Boundary groups (1D curves)
                boundary_groups = pg_by_type.get('boundary', {})
                file_obj.write(f"Boundary Physical Groups (1D): {len(boundary_groups)}\n")
                for pg_value, curve_tags in boundary_groups.items():
                    unique_tags = list(dict.fromkeys(curve_tags))
                    file_obj.write(f"  Tag {pg_value}: {len(unique_tags)} curves\n")
                    if len(unique_tags) <= 10:  # Don't list all tags if too many
                        file_obj.write(f"    Curve tags: {unique_tags}\n")
                    else:
                        file_obj.write(f"    Curve tags: {unique_tags[:5]} ... and {len(unique_tags)-5} more\n")
                file_obj.write("\n")
                
                # Domain groups (2D surfaces)
                domain_groups = pg_by_type.get('domain', {})
                file_obj.write(f"Domain Physical Groups (2D): {len(domain_groups)}\n")
                for pg_value, surface_tags in domain_groups.items():
                    unique_tags = list(dict.fromkeys(surface_tags))
                    file_obj.write(f"  Tag {pg_value}: {len(unique_tags)} surfaces\n")
                    file_obj.write(f"    Surface tags: {unique_tags}\n")
                file_obj.write("\n")
                
        except Exception as e:
            file_obj.write(f"Unable to extract physical group details: {e}\n")
        
        file_obj.write("\n")
        