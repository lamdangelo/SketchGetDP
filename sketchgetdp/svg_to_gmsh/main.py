import os
import sys

# Add the parent directory to Python path so svg_to_gmsh package can be found
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from svg_to_gmsh.interfaces.arg_parser import ArgParser
from svg_to_gmsh.core.use_cases.convert_svg_to_geometry import ConvertSVGToGeometry
from svg_to_gmsh.infrastructure.svg_parser import SVGParser
from svg_to_gmsh.infrastructure.corner_detector import CornerDetector
from svg_to_gmsh.infrastructure.bezier_fitter import BezierFitter

def main():
    """Main entry point for the SVG to Geometry converter"""
    
    # Parse command line arguments
    arg_parser = ArgParser()
    args = arg_parser.parse_args()
    
    try:
        # Initialize infrastructure services
        svg_parser = SVGParser()
        corner_detector = CornerDetector()
        bezier_fitter = BezierFitter()
        
        # Initialize use case with dependencies
        converter = ConvertSVGToGeometry(svg_parser, corner_detector, bezier_fitter)
        
        # Execute the use case
        boundary_curves, point_electrodes, colored_boundaries = converter.execute(args.svg_file)
        
        # Output results
        print(f"Successfully converted {len(boundary_curves)} boundary curves and {len(point_electrodes)} point electrodes:")
        
        for i, curve in enumerate(boundary_curves):
            print(f"  Curve {i+1}: {len(curve.bezier_segments)} segments, "
                  f"{len(curve.corners)} corners, color: {curve.color.name.lower()}")
        
        for i, (point, color) in enumerate(point_electrodes):
            print(f"  Point electrode {i+1}: at ({point.x:.3f}, {point.y:.3f}), color: {color.name.lower()}")
        
        # Handle debug output if requested
        if args.debug:
            try:
                from svg_to_gmsh.interfaces.debug_writer import DebugWriter
                
                DebugWriter()._write_debug_info(
                    svg_file_path=args.svg_file,
                    colored_boundaries=colored_boundaries
                )
            
            except ImportError:
                print("Debug output unavailable: required module not found")
            except Exception as e:
                print(f"Debug output error: {e}")
        
        # Handle visualization if requested
        if args.visualize or args.output_plot:
            try:
                from svg_to_gmsh.interfaces.curve_visualizer import CurveVisualizer
                
                if args.output_plot:
                    # Save plot to file
                    CurveVisualizer.save_plot_to_file(
                        boundary_curves=boundary_curves,
                        point_electrodes=point_electrodes,
                        colored_boundaries=colored_boundaries,
                        filename=args.output_plot,
                        show_control_points=True,
                        show_corners=True
                    )
                elif args.visualize:
                    # Display interactive plot
                    print("\nGenerating visualization...")
                    CurveVisualizer.display_boundary_curves(
                        boundary_curves=boundary_curves,
                        point_electrodes=point_electrodes,
                        colored_boundaries=colored_boundaries,
                        show_control_points=colored_boundaries,
                        show_corners=True,
                        show_raw_boundaries=True
                    )
                    
            except ImportError:
                print("Visualization unavailable: matplotlib not installed")
                print("Install with: pip install matplotlib")
            except Exception as e:
                print(f"Visualization error: {e}")
        
        # Optional: Save results to file if specified
        if args.output:
            save_results(boundary_curves, point_electrodes, args.output)
            print(f"Results saved to {args.output}")
            
    except Exception as e:
        print(f"Error processing SVG file: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0

def save_results(boundary_curves, point_electrodes, output_path: str):
    """Save conversion results to file with coordinates"""
    with open(output_path, 'w') as f:
        f.write("SVG to Geometry Conversion Results\n")
        f.write("=" * 50 + "\n\n")
        
        # Boundary Curves Section
        f.write("BOUNDARY CURVES\n")
        f.write("=" * 50 + "\n\n")
        
        for i, curve in enumerate(boundary_curves):
            f.write(f"Curve {i+1}:\n")
            f.write(f"  Color: {curve.color.name}\n")
            f.write(f"  Segments: {len(curve.bezier_segments)}\n")
            f.write(f"  Corners: {len(curve.corners)}\n")
            f.write(f"  Closed: {curve.is_closed}\n")
            
            # Segment details with control points
            f.write("  Segments:\n")
            for seg_idx, segment in enumerate(curve.bezier_segments):
                f.write(f"    Segment {seg_idx} (Degree {segment.degree}):\n")
                for cp_idx, control_point in enumerate(segment.control_points):
                    f.write(f"      Control Point {cp_idx}: ({control_point.x:.6f}, {control_point.y:.6f})\n")
            
            # Corner coordinates
            if curve.corners:
                f.write("  Corners:\n")
                for corner_idx, corner in enumerate(curve.corners):
                    f.write(f"    Corner {corner_idx}: ({corner.x:.6f}, {corner.y:.6f})\n")
            
            # Sample points along the curve
            f.write("  Sampled Curve Points (t=0 to 1):\n")
            for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
                point = curve.evaluate(t)
                f.write(f"    t={t:.2f}: ({point.x:.6f}, {point.y:.6f})\n")
            
            f.write("\n")
        
        # Point Electrodes Section
        f.write("POINT ELECTRODES\n")
        f.write("=" * 50 + "\n\n")
        
        for i, (point, color) in enumerate(point_electrodes):
            f.write(f"Point Electrode {i+1}:\n")
            f.write(f"  Color: {color.name}\n")
            f.write(f"  Position: ({point.x:.6f}, {point.y:.6f})\n\n")

if __name__ == "__main__":
    exit(main())