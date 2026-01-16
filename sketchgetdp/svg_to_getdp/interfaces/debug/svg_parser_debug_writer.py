from datetime import datetime
from svg_to_getdp.interfaces.debug.debug_coordinator import DebugCoordinator


class SVGParserDebugWriter(DebugCoordinator):
    """Handles writing debug information for SVG parsing."""
    
    def __init__(self):
        super().__init__()
    
    def write_svg_parser_debug_info(self, svg_file_path: str, colored_outlines: dict):
        """
        Write SVG parser results to a debug text file.
        """
        self.set_svg_file(svg_file_path)
        debug_filename = self.get_debug_filename("svg_parser_debug", ".txt")
        
        with open(debug_filename, 'w') as f:
            f.write(f"SVG Parser Debug Information\n")
            f.write(f"============================\n")
            f.write(f"Input SVG: {svg_file_path}\n")
            f.write(f"Processed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Debug run timestamp: {self.get_shared_timestamp()}\n")
            f.write(f"\n")
            
            total_outlines = 0
            for color, outlines in colored_outlines.items():
                f.write(f"Color: {color}\n")
                f.write(f"Number of outlines: {len(outlines)}\n")
                total_outlines += len(outlines)
                
                for i, outline in enumerate(outlines):
                    f.write(f"  Outline {i+1}:\n")
                    f.write(f"    Is closed: {outline.is_closed}\n")
                    f.write(f"    Number of points: {len(outline.points)}\n")
                    f.write(f"    Points:\n")
                    
                    for j, point in enumerate(outline.points):
                        f.write(f"      [{j}] x={point.x:.6f}, y={point.y:.6f}\n")
                    
                    # Calculate bounding box
                    if outline.points:
                        x_coords = [p.x for p in outline.points]
                        y_coords = [p.y for p in outline.points]
                        f.write(f"    Bounding box: x=[{min(x_coords):.6f}, {max(x_coords):.6f}], "
                               f"y=[{min(y_coords):.6f}, {max(y_coords):.6f}]\n")
                    
                    f.write(f"\n")
                
                f.write(f"\n")
            
            f.write(f"Total outlines processed: {total_outlines}\n")
            f.write(f"\n")
            
            # Summary statistics
            f.write(f"Summary by color:\n")
            for color, outlines in colored_outlines.items():
                total_points = sum(len(outline.points) for outline in outlines)
                avg_points = total_points / len(outlines) if outlines else 0
                closed_count = sum(1 for outline in outlines if outline.is_closed)
                
                f.write(f"  {color}: {len(outlines)} outlines, {total_points} total points, "
                       f"{avg_points:.1f} avg points, {closed_count} closed\n")
        
        print(f"SVG parser debug information written to: {debug_filename}")
        