from datetime import datetime
from svg_to_getdp.interfaces.debug.debug_coordinator import DebugCoordinator


class GeometryDebugWriter(DebugCoordinator):
    """Handles writing debug information for geometry conversion."""
    
    def __init__(self):
        super().__init__()
    
    def write_geometry_debug_info(self, svg_file_path: str, outlines, wires):
        """
        Write geometry conversion results to a debug text file.
        Follows the same structure as write_svg_parser_debug_info.
        """
        self.set_svg_file(svg_file_path)
        debug_filename = self.get_debug_filename("geometry_debug", ".txt")
        
        with open(debug_filename, 'w') as f:
            f.write(f"Geometry Conversion Debug Information\n")
            f.write(f"=====================================\n")
            f.write(f"Input SVG: {svg_file_path}\n")
            f.write(f"Processed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Debug run timestamp: {self.get_shared_timestamp()}\n")
            f.write(f"\n")
            
            f.write(f"Summary:\n")
            f.write(f"  Total outlines: {len(outlines)}\n")
            f.write(f"  Total wires: {len(wires)}\n")
            f.write(f"\n")
            
            # Outlines Section
            f.write(f"OUTLINES\n")
            f.write(f"===============\n\n")

            for i, outline in enumerate(outlines):
                f.write(f"Outline {i+1}:\n")
                f.write(f"  Color: {outline.color.name}\n")
                f.write(f"  Segments: {len(outline.bezier_segments)}\n")
                f.write(f"  Corners: {len(outline.corners)}\n")
                f.write(f"  Closed: {outline.is_closed}\n")

                # Segment details with control points
                f.write(f"  Segments:\n")
                for seg_idx, segment in enumerate(outline.bezier_segments):
                    f.write(f"    Segment {seg_idx} (Degree {segment.degree}):\n")
                    for cp_idx, control_point in enumerate(segment.control_points):
                        f.write(f"      Control Point {cp_idx}: ({control_point.x:.6f}, {control_point.y:.6f})\n")
                
                # Corner coordinates
                if outline.corners:
                    f.write(f"  Corners:\n")
                    for corner_idx, corner in enumerate(outline.corners):
                        f.write(f"    Corner {corner_idx}: ({corner.x:.6f}, {corner.y:.6f})\n")
                
                # Sample points along the outline
                f.write(f"  Sampled Outline Points (t=0 to 1):\n")
                for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
                    point = outline.evaluate(t)
                    f.write(f"    t={t:.2f}: ({point.x:.6f}, {point.y:.6f})\n")
                
                f.write(f"\n")
            
            # Wires Section
            f.write(f"WIRES\n")
            f.write(f"=====\n\n")
            
            for i, (point, color) in enumerate(wires):
                f.write(f"Wire {i+1}:\n")
                f.write(f"  Color: {color.name}\n")
                f.write(f"  Position: ({point.x:.6f}, {point.y:.6f})\n\n")
        
        print(f"Geometry debug information written to: {debug_filename}")
        return debug_filename
    
    @staticmethod
    def save_results(outlines, wires, output_path: str):
        """Save conversion results to file with coordinates."""
        with open(output_path, 'w') as f:
            f.write("SVG to Geometry Conversion Results\n")
            f.write("=" * 50 + "\n\n")
            
            # Outlines Section
            f.write("OUTLINES\n")
            f.write("=" * 50 + "\n\n")
            
            for i, outline in enumerate(outlines):
                f.write(f"Outline {i+1}:\n")
                f.write(f"  Color: {outline.color.name}\n")
                f.write(f"  Segments: {len(outline.bezier_segments)}\n")
                f.write(f"  Corners: {len(outline.corners)}\n")
                f.write(f"  Closed: {outline.is_closed}\n")

                # Segment details with control points
                f.write("  Segments:\n")
                for seg_idx, segment in enumerate(outline.bezier_segments):
                    f.write(f"    Segment {seg_idx} (Degree {segment.degree}):\n")
                    for cp_idx, control_point in enumerate(segment.control_points):
                        f.write(f"      Control Point {cp_idx}: ({control_point.x:.6f}, {control_point.y:.6f})\n")
                
                # Corner coordinates
                if outline.corners:
                    f.write("  Corners:\n")
                    for corner_idx, corner in enumerate(outline.corners):
                        f.write(f"    Corner {corner_idx}: ({corner.x:.6f}, {corner.y:.6f})\n")
                
                # Sample points along the outline
                f.write("  Sampled Outline Points (t=0 to 1):\n")
                for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
                    point = outline.evaluate(t)
                    f.write(f"    t={t:.2f}: ({point.x:.6f}, {point.y:.6f})\n")
                
                f.write("\n")
            
            # Wires Section
            f.write("WIRES\n")
            f.write("=" * 50 + "\n\n")
            
            for i, (point, color) in enumerate(wires):
                f.write(f"Wire {i+1}:\n")
                f.write(f"  Color: {color.name}\n")
                f.write(f"  Position: ({point.x:.6f}, {point.y:.6f})\n\n")
                