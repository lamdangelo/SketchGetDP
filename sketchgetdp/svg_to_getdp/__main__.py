"""
SVG to Getdp - Package Entry Point

This module allows the package to be executed as:
python -m svg_to_getdp [arguments]
"""

from pathlib import Path

def main():
    """Main entry point for the SVG to Geometry converter"""
    
    # Import here to ensure path is set correctly
    from .interfaces.arg_parser import ArgParser
    
    # Parse command line arguments
    arg_parser = ArgParser()
    args = arg_parser.parse_args()
    
    try:
        # MODE 1: Simulation-only mode (existing mesh)
        if args.simulation_only:
            from .core.use_cases.run_getdp_simulation import RunGetDPSimulation
            
            # Get mesh name from the provided mesh file
            mesh_path = Path(args.simulation_only)
            if not mesh_path.exists():
                raise FileNotFoundError(f"Mesh file not found: {args.simulation_only}")
            
            # Remove .msh extension if present
            mesh_name = mesh_path.stem
            
            print(f"\n=== Running GetDP Simulation on Existing Mesh ===")
            print(f"Mesh file: {args.simulation_only}")
            print(f"Config file: {args.config}")
            
            # Initialize and run GetDP simulation
            getdp_usecase = RunGetDPSimulation()
            getdp_usecase.execute(
                mesh_name=mesh_name,
                use_config_yaml=True,
                config_yaml_path=args.config,
                show_simulation_result=not args.no_gui
            )
            
            print(f"\n✓ GetDP simulation completed successfully!")
            print(f"  Results saved to: results/")
            
            return 0
        
        # MODE 2 & 3: Normal processing (SVG → Gmsh)
        from svg_to_getdp.core.use_cases.convert_svg_to_geometry import ConvertSVGToGeometry
        from svg_to_getdp.core.use_cases.convert_geometry_to_gmsh import ConvertGeometryToGmsh
        from svg_to_getdp.infrastructure.svg_parser import SVGParser
        from svg_to_getdp.infrastructure.corner_detector import CornerDetector
        from svg_to_getdp.infrastructure.bezier_fitter import BezierFitter
        from sketchgetdp.svg_to_getdp.infrastructure.outline_grouper import OutlineGrouper
        from sketchgetdp.svg_to_getdp.infrastructure.outline_preprocessor import OutlinePreprocessor
        from svg_to_getdp.infrastructure.wire_preprocessor import WirePreprocessor
        
        # Initialize infrastructure services for SVG conversion
        svg_parser = SVGParser()
        corner_detector = CornerDetector(debug_enabled=True)  # Enable debug mode
        bezier_fitter = BezierFitter()
        
        # Initialize SVG conversion use case with dependencies
        converter = ConvertSVGToGeometry(svg_parser, corner_detector, bezier_fitter)
        
        # Execute the SVG conversion use case with debug data collection
        outlines, wires, colored_outlines, corner_debug_data = converter.execute(args.svg_file)
        
        # Output conversion results
        print(f"Successfully converted {len(outlines)} outlines and {len(wires)} wires:")
        
        for i, outline in enumerate(outlines):
            print(f"  Outline {i+1}: {len(outline.bezier_segments)} segments, "
                  f"{len(outline.corners)} corners, color: {outline.color.name.lower()}")
        
        for i, (point, color) in enumerate(wires):
            print(f"  Wire {i+1}: at ({point.x:.3f}, {point.y:.3f}), color: {color.name.lower()}")
        
        # Handle debug output of svg to geometry conversion
        if args.debug:
            try:
                from svg_to_getdp.interfaces.debug.debug_coordinator import DebugCoordinator
                from svg_to_getdp.interfaces.debug.svg_parser_debug_writer import SVGParserDebugWriter
                from svg_to_getdp.interfaces.debug.corner_detector_debug_writer import CornerDetectorDebugWriter
                from svg_to_getdp.interfaces.debug.geometry_debug_writer import GeometryDebugWriter
                from svg_to_getdp.interfaces.debug.curve_visualizer import CurveVisualizer
                
                # Initialize debug coordinator first
                debug_coordinator = DebugCoordinator()
                debug_coordinator.set_svg_file(args.svg_file)
                shared_timestamp = debug_coordinator.get_shared_timestamp()
                
                # Initialize debug writers with the same timestamp
                svg_parser_debug_writer = SVGParserDebugWriter()
                svg_parser_debug_writer._shared_timestamp = shared_timestamp
                
                corner_detector_debug_writer = CornerDetectorDebugWriter()
                corner_detector_debug_writer._shared_timestamp = shared_timestamp
                
                geometry_debug_writer = GeometryDebugWriter()
                geometry_debug_writer._shared_timestamp = shared_timestamp
                
                # Write SVG parser debug info
                print(f"\n=== Writing SVG Parser Debug ===")
                svg_parser_debug_writer.write_svg_parser_debug_info(
                    svg_file_path=args.svg_file,
                    colored_outlines=colored_outlines
                )
                
                # Write corner detection debug info
                print(f"\n=== Writing Corner Detection Debug ===")
                if corner_debug_data:
                    corner_detector_debug_writer.write_corner_detection_debug_info(
                        svg_file_path=args.svg_file,
                        corner_debug_data=corner_debug_data,
                        outlines=outlines
                    )
                
                # Write geometry debug info
                print(f"\n=== Generating Geometry Debug ===")
                summary_path = geometry_debug_writer.write_geometry_debug_info(
                    svg_file_path=args.svg_file,
                    outlines=outlines,
                    wires=wires
                )
                
                # Generate geometry plot
                try:
                    plot_path = CurveVisualizer.save_plot_with_coordinator(
                        outlines=outlines,
                        coordinator=debug_coordinator,
                        wires=wires,
                        colored_outlines=colored_outlines,
                        show_control_points=True,
                        show_corners=True,
                        show_raw_outlines=True
                    )
                    
                except ImportError as e:
                    print(f"  Geometry plot unavailable: {e}")
                    print("  Install with: pip install matplotlib")
                except Exception as e:
                    print(f"  Geometry plot error: {e}")
                    import traceback
                    traceback.print_exc()
                
            except ImportError as e:
                print(f"Debug output unavailable: {e}")
            except Exception as e:
                print(f"Debug output error: {e}")
                import traceback
                traceback.print_exc()
        
        # Determine config file path
        config_file_path = Path(args.config)
        if not config_file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file_path}")
        
        # ALWAYS perform Gmsh meshing
        print("\n=== Starting Gmsh Meshing ===")
        
        # Initialize infrastructure services for Gmsh conversion
        outline_grouper = OutlineGrouper()
        outline_preprocessor = OutlinePreprocessor()
        wire_preprocessor = WirePreprocessor()
        
        # Initialize Gmsh conversion use case
        gmsh_converter = ConvertGeometryToGmsh(
            outline_grouper=outline_grouper,
            outline_preprocessor=outline_preprocessor,
            wire_preprocessor=wire_preprocessor
        )
        
        # Determine mesh name (output filename)
        if args.mesh_name:
            # User specified custom mesh name
            mesh_name = args.mesh_name
        else:
            # Default: use SVG filename without extension
            svg_path = Path(args.svg_file)
            mesh_name = svg_path.stem
        
        # Execute Gmsh conversion
        gmsh_results = gmsh_converter.execute(
            outlines=outlines,
            wires=wires,
            config_file_path=str(config_file_path),
            model_name="svg_geometry",
            output_filename=mesh_name,
            dimension=2,
            show_gui=not args.no_gui
        )
        
        print(f"\n✓ Gmsh meshing completed successfully!")
        print(f"  Mesh saved to: {mesh_name}.msh")
        
        # Handle debug output of geometry to Gmsh conversion
        if args.debug:
            try:
                from svg_to_getdp.interfaces.debug.debug_coordinator import DebugCoordinator
                from sketchgetdp.svg_to_getdp.interfaces.debug.outline_grouper_debug_writer import OutlineGrouperDebugWriter
                from sketchgetdp.svg_to_getdp.interfaces.debug.outline_preprocessor_debug_writer import OutlinePreprocessorDebugWriter
                from svg_to_getdp.interfaces.debug.wire_preprocessor_debug_writer import WirePreprocessorDebugWriter
                
                # Initialize debug writers with the same timestamp
                grouping_debug_writer = OutlineGrouperDebugWriter()
                grouping_debug_writer.set_shared_timestamp(shared_timestamp)

                preprocessing_debug_writer = OutlinePreprocessorDebugWriter()
                preprocessing_debug_writer.set_shared_timestamp(shared_timestamp)
                
                wire_debug_writer = WirePreprocessorDebugWriter()
                wire_debug_writer.set_shared_timestamp(shared_timestamp)

                # Write outline grouping debug
                if "debug_data" in gmsh_results and "outline_grouping" in gmsh_results["debug_data"]:
                    print(f"\n=== Writing Outline Grouping Debug ===")

                    grouping_debug_data = gmsh_results["debug_data"]["outline_grouping"]
                    grouping_debug_file = grouping_debug_writer.write_grouping_debug_info(
                        svg_file_path=args.svg_file,
                        outlines=grouping_debug_data["outlines"],
                        grouping_result=grouping_debug_data["grouping_result"],
                        grouper_instance=grouping_debug_data["grouper_instance"]
                    )
                    
                # Write outline preprocessing debug
                print(f"\n=== Writing Outline Preprocessing Debug ===")
                preprocessing_debug_file = preprocessing_debug_writer.write_preprocessing_debug_info(
                    svg_file_path=args.svg_file,
                    outlines=outlines,
                    preprocessor_instance=outline_preprocessor,
                    gmsh_results=gmsh_results
                )
                
                # Write wire preprocessor debug
                print(f"\n=== Writing Wire Preprocessor Debug ===")
                wire_debug_file = wire_debug_writer.write_wire_preprocessor_debug_info(
                    svg_file_path=args.svg_file,
                    wires=wires,
                    config_file_path=str(config_file_path),
                    wire_preprocessor_instance=wire_preprocessor,
                    gmsh_results=gmsh_results 
                )
                    
            except ImportError as e:
                print(f"Gmsh debug output unavailable: {e}")
            except Exception as e:
                print(f"Gmsh debug output error: {e}")
                import traceback
                traceback.print_exc()
        
        # MODE 3: Run GetDP simulation if requested
        if args.run_simulation:
            from .core.use_cases.run_getdp_simulation import RunGetDPSimulation
            
            print("\n=== Starting GetDP Simulation ===")
            
            # Initialize and run GetDP simulation
            getdp_usecase = RunGetDPSimulation()
            getdp_usecase.execute(
                mesh_name=mesh_name,
                use_config_yaml=True,
                config_yaml_path=args.config,
                show_simulation_result=not args.no_gui
            )
            
            print(f"\n✓ GetDP simulation completed successfully!")
            print(f"  Results saved to: results/")
            
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        print(f"Current working directory: {Path.cwd()}")
        return 1
    except Exception as e:
        print(f"Error processing: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
    