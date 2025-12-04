import argparse
from typing import List

class ArgParser:
    """Command line argument parser for SVG to Gmsh converter"""
    
    def parse_args(self, args: List[str] = None) -> argparse.Namespace:
        parser = argparse.ArgumentParser(
            description='Convert SVG sketches to Gmsh mesh with Bézier boundary curves',
            epilog=(
                'Examples:\n'
                '  python -m svg_to_gmsh drawing.svg\n'
                '  python -m svg_to_gmsh sketch.svg --visualize\n'
                '  python -m svg_to_gmsh design.svg --output-plot curves.png\n'
                '  python -m svg_to_gmsh design.svg --mesh-name my_mesh --no-gui\n'
                '  python -m svg_to_gmsh design.svg --gmsh-config custom_config.yaml\n'
            ),
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # Required argument
        parser.add_argument(
            'svg_file', 
            help='Path to SVG file to process'
        )
        
        # Gmsh meshing options
        parser.add_argument(
            '--gmsh-config',
            type=str,
            help='Path to YAML configuration file for coil currents and mesh settings (default: config.yaml)'
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
            help='Disable Gmsh GUI display (run in batch mode)'
        )
        
        # Debug options
        parser.add_argument(
            '--debug', '-d', 
            action='store_true',
            help='Enable debug mode to output intermediate processing information'
        )
        
        # Output options
        parser.add_argument(
            '--output', '-o', 
            help='Save text results to specified file (intermediate results)'
        )
        
        # Visualization options
        parser.add_argument(
            '--visualize', '-v', 
            action='store_true',
            help='Display interactive visualization of Bézier curves'
        )
        
        parser.add_argument(
            '--output-plot',
            help='Save visualization plot to specified file (instead of displaying)'
        )
        
        return parser.parse_args(args)