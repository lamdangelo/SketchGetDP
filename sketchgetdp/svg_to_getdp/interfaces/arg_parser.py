import argparse
from typing import List

class ArgParser:
    """Command line argument parser for SVG to Getdp converter"""
    
    def parse_args(self, args: List[str] = None) -> argparse.Namespace:
        parser = argparse.ArgumentParser(
            description='Convert SVG sketches to Getdp-compatible geometry, mesh with Gmsh and simulate with Getdp.',
            epilog=(
                'Examples:\n'
                '  python -m svg_to_getdp drawing.svg\n'
                '  python -m svg_to_getdp design.svg --debug\n'
                '  python -m svg_to_getdp design.svg --mesh-name my_mesh --no-gui\n'
                '  python -m svg_to_getdp design.svg --run-simulation\n'
                '  python -m svg_to_getdp --simulation-only existing_mesh.msh\n'
                '  python -m svg_to_getdp design.svg --config custom_config.yaml --run-simulation --no-gui\n'
            ),
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # SVG file argument (optional for simulation-only mode)
        parser.add_argument(
            'svg_file', 
            nargs='?',  # Make it optional for simulation-only mode
            help='Path to SVG file to process (required unless --simulation-only is used)'
        )
        
        # GetDP Simulation options
        simulation_group = parser.add_argument_group('GetDP Simulation Options')
        
        simulation_group.add_argument(
            '--run-simulation', '-s',
            action='store_true',
            help='Run GetDP simulation after mesh generation (full pipeline: SVG → Gmsh → GetDP)'
        )
        
        simulation_group.add_argument(
            '--simulation-only',
            metavar='MESH_FILE',
            type=str,
            help='Run GetDP simulation on an existing mesh file (skip SVG conversion and Gmsh)'
        )
        
        # Gmsh meshing options
        parser.add_argument(
            '--config',
            default='config.yaml',
            type=str,
            help='Path to YAML configuration file for coil currents, mesh settings and simulation parameters (default: config.yaml)'
        )
        
        parser.add_argument(
            '--mesh-name',
            type=str,
            help='Name for the output mesh file (without .msh extension). '
                 'If not specified, uses the SVG filename.'
        )
        
        parser.add_argument(
            '--no-gui',
            action='store_true',
            help='Disable Gmsh and GetDP GUI display (run in batch mode)'
        )
        
        # Debug options
        parser.add_argument(
            '--debug', '-d', 
            action='store_true',
            help='Enable debug mode to output intermediate processing information including geometry plots and text summaries'
        )
        
        # Parse arguments
        parsed_args = parser.parse_args(args)
        
        # Validate arguments
        self._validate_args(parser, parsed_args)
        
        return parsed_args
    
    def _validate_args(self, parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
        """Validate the parsed arguments for logical consistency."""
        
        # If simulation-only mode is used
        if args.simulation_only:
            # Check that SVG file is not also provided (they're mutually exclusive)
            if args.svg_file:
                parser.error("Cannot specify both SVG file and --simulation-only. "
                           "Use --simulation-only alone for existing meshes.")
            
            # Check that run-simulation is not also specified (redundant)
            if args.run_simulation:
                parser.error("Cannot use both --run-simulation and --simulation-only. "
                           "Use --run-simulation for full pipeline or --simulation-only for existing mesh.")
            
            # Check that mesh-only related options are not used
            if args.mesh_name:
                parser.error("Cannot use --mesh-name with --simulation-only. "
                           "Mesh name is derived from the provided mesh file.")
        
        # If normal mode (not simulation-only)
        else:
            # Check that SVG file is provided
            if not args.svg_file:
                parser.error("SVG file is required unless --simulation-only is used")
            
            # If run-simulation is used with no SVG file (shouldn't happen due to above check)
            if args.run_simulation and not args.svg_file:
                parser.error("SVG file is required for --run-simulation")
