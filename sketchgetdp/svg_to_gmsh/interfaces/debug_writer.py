import os
from datetime import datetime


class DebugWriter:
    """Utility class for writing debug information about SVG parsing results."""
    
    def _write_debug_info(self, svg_file_path: str, colored_boundaries: dict):
        """
        Write SVG parser results to a debug text file.
        """
        # Create debug directory if it doesn't exist
        debug_dir = "debug"
        os.makedirs(debug_dir, exist_ok=True)
        
        # Create debug filename based on input SVG filename and timestamp
        svg_filename = os.path.basename(svg_file_path)
        svg_name = os.path.splitext(svg_filename)[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_filename = f"{debug_dir}/svg_parser_debug_{svg_name}_{timestamp}.txt"
        
        with open(debug_filename, 'w') as f:
            f.write(f"SVG Parser Debug Information\n")
            f.write(f"============================\n")
            f.write(f"Input SVG: {svg_file_path}\n")
            f.write(f"Processed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"\n")
            
            f.write(f"Color Groups Found: {len(colored_boundaries)}\n")
            f.write(f"\n")
            
            total_boundaries = 0
            for color, boundaries in colored_boundaries.items():
                f.write(f"Color: {color}\n")
                f.write(f"Number of boundaries: {len(boundaries)}\n")
                total_boundaries += len(boundaries)
                
                for i, boundary in enumerate(boundaries):
                    f.write(f"  Boundary {i+1}:\n")
                    f.write(f"    Is closed: {boundary.is_closed}\n")
                    f.write(f"    Number of points: {len(boundary.points)}\n")
                    f.write(f"    Points:\n")
                    
                    for j, point in enumerate(boundary.points):
                        f.write(f"      [{j}] x={point.x:.6f}, y={point.y:.6f}\n")
                    
                    # Calculate bounding box
                    if boundary.points:
                        x_coords = [p.x for p in boundary.points]
                        y_coords = [p.y for p in boundary.points]
                        f.write(f"    Bounding box: x=[{min(x_coords):.6f}, {max(x_coords):.6f}], "
                               f"y=[{min(y_coords):.6f}, {max(y_coords):.6f}]\n")
                    
                    f.write(f"\n")
                
                f.write(f"\n")
            
            f.write(f"Total boundaries processed: {total_boundaries}\n")
            f.write(f"\n")
            
            # Summary statistics
            f.write(f"Summary by color:\n")
            for color, boundaries in colored_boundaries.items():
                total_points = sum(len(boundary.points) for boundary in boundaries)
                avg_points = total_points / len(boundaries) if boundaries else 0
                closed_count = sum(1 for boundary in boundaries if boundary.is_closed)
                
                f.write(f"  {color}: {len(boundaries)} boundaries, {total_points} total points, "
                       f"{avg_points:.1f} avg points, {closed_count} closed\n")
        
        print(f"SVG parser debug information written to: {debug_filename}")
    