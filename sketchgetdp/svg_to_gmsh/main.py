from interfaces.arg_parser import ArgParser
from core.use_cases.convert_svg_to_geometry import ConvertSVGToGeometry
from infrastructure.svg_parser import SVGParser
from infrastructure.corner_detector import CornerDetector
from infrastructure.bezier_fitter import BezierFitter

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
        boundary_curves, point_electrodes = converter.execute(args.svg_file)
        
        # Output results
        print(f"Successfully converted {len(boundary_curves)} boundary curves and {len(point_electrodes)} point electrodes:")
        
        for i, curve in enumerate(boundary_curves):
            print(f"  Curve {i+1}: {len(curve.bezier_segments)} segments, "
                  f"{len(curve.corners)} corners, color: {curve.color.name}")
        
        for i, (point, color) in enumerate(point_electrodes):
            print(f"  Point electrode {i+1}: at ({point.x:.3f}, {point.y:.3f}), color: {color.name}")
        
        # Optional: Save output if specified
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
    """Save conversion results to file (basic implementation)"""
    with open(output_path, 'w') as f:
        f.write("Boundary Curves Conversion Results\n")
        f.write("=" * 40 + "\n\n")
        
        for i, curve in enumerate(boundary_curves):
            f.write(f"Curve {i+1}:\n")
            f.write(f"  Color: {curve.color.name}\n")
            f.write(f"  Segments: {len(curve.bezier_segments)}\n")
            f.write(f"  Corners: {len(curve.corners)}\n")
            f.write(f"  Closed: {curve.is_closed}\n\n")
        
        f.write("Point Electrodes\n")
        f.write("=" * 40 + "\n\n")
        
        for i, (point, color) in enumerate(point_electrodes):
            f.write(f"Point Electrode {i+1}:\n")
            f.write(f"  Color: {color.name}\n")
            f.write(f"  Position: ({point.x:.6f}, {point.y:.6f})\n\n")

if __name__ == "__main__":
    exit(main())