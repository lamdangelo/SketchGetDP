"""
SVG to Gmsh Geometry Converter - Package Entry Point

This module allows the package to be executed as:
python -m svg_to_gmsh [arguments]
"""

from pathlib import Path

def main():
    """Main entry point for the SVG to Geometry converter"""
    
    # Import here to ensure path is set correctly
    from .interfaces.arg_parser import ArgParser
    from .core.use_cases.convert_svg_to_geometry import ConvertSVGToGeometry
    from .core.use_cases.convert_geometry_to_gmsh import ConvertGeometryToGmsh
    from .infrastructure.svg_parser import SVGParser
    from .infrastructure.corner_detector import CornerDetector
    from .infrastructure.bezier_fitter import BezierFitter
    from .infrastructure.boundary_curve_grouper import BoundaryCurveGrouper
    from .infrastructure.boundary_curve_mesher import BoundaryCurveMesher
    from .infrastructure.point_electrode_mesher import PointElectrodeMesher
    
    # Parse command line arguments
    arg_parser = ArgParser()
    args = arg_parser.parse_args()
    
    try:
        # Initialize infrastructure services for SVG conversion
        svg_parser = SVGParser()
        corner_detector = CornerDetector()
        bezier_fitter = BezierFitter()
        
        # Initialize SVG conversion use case with dependencies
        converter = ConvertSVGToGeometry(svg_parser, corner_detector, bezier_fitter)
        
        # Execute the SVG conversion use case
        boundary_curves, point_electrodes, colored_boundaries = converter.execute(args.svg_file)
        
        # Output conversion results
        print(f"Successfully converted {len(boundary_curves)} boundary curves and {len(point_electrodes)} point electrodes:")
        
        for i, curve in enumerate(boundary_curves):
            print(f"  Curve {i+1}: {len(curve.bezier_segments)} segments, "
                  f"{len(curve.corners)} corners, color: {curve.color.name.lower()}")
        
        for i, (point, color) in enumerate(point_electrodes):
            print(f"  Point electrode {i+1}: at ({point.x:.3f}, {point.y:.3f}), color: {color.name.lower()}")
        
        # Determine config file path
        config_file_path = Path(args.gmsh_config)
        if not config_file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file_path}")
        
        # ALWAYS perform Gmsh meshing (this is now the main purpose)
        print("\n=== Starting Gmsh Meshing ===")
        
        # Initialize infrastructure services for Gmsh conversion
        boundary_curve_grouper = BoundaryCurveGrouper()
        boundary_curve_mesher = BoundaryCurveMesher()
        point_electrode_mesher = PointElectrodeMesher()
        
        # Initialize Gmsh conversion use case
        gmsh_converter = ConvertGeometryToGmsh(
            boundary_curve_grouper=boundary_curve_grouper,
            boundary_curve_mesher=boundary_curve_mesher,
            point_electrode_mesher=point_electrode_mesher
        )
        
        # Determine mesh name (output filename)
        if args.mesh_name:
            # User specified custom mesh name
            mesh_name = args.mesh_name
        else:
            # Default: use SVG filename without extension
            svg_path = Path(args.svg_file)
            mesh_name = svg_path.stem
        
        # Execute Gmsh conversion (mesh size is now read internally from config)
        gmsh_results = gmsh_converter.execute(
            boundary_curves=boundary_curves,
            point_electrodes=point_electrodes,
            config_file_path=str(config_file_path),
            model_name="svg_geometry",
            output_filename=mesh_name,
            dimension=2,
            show_gui=not args.no_gui
        )
        
        print(f"\n✓ Gmsh meshing completed successfully!")
        print(f"  Mesh saved to: {mesh_name}.msh")
        
        # Handle debug output if requested (optional)
        if args.debug:
            try:
                from .interfaces.debug.debug_writer import DebugWriter
                
                DebugWriter()._write_svg_parser_debug_info(
                    svg_file_path=args.svg_file,
                    colored_boundaries=colored_boundaries
                )
            
            except ImportError:
                print("Debug output unavailable: required module not found")
            except Exception as e:
                print(f"Debug output error: {e}")
        
        # Handle visualization if requested (optional)
        if args.visualize or args.output_plot:
            try:
                from .interfaces.debug.curve_visualizer import CurveVisualizer
                
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
                    print(f"Visualization saved to: {args.output_plot}")
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
        
        # Save intermediate results to file if specified (optional)
        if args.output:
            from .interfaces.debug.debug_writer import DebugWriter
            DebugWriter.save_results(boundary_curves, point_electrodes, args.output)
            print(f"Intermediate results saved to: {args.output}")
            
    except Exception as e:
        print(f"Error processing SVG file: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())