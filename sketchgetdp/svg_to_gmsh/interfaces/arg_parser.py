import argparse
from typing import List

class ArgParser:
    """Command line argument parser for SVG to Geometry converter"""
    
    def parse_args(self, args: List[str] = None) -> argparse.Namespace:
        parser = argparse.ArgumentParser(
            description='Convert SVG sketches to boundary curves with Bézier representations and point electrodes',
            epilog=(
                'Examples:\n'
                '  python -m svg_to_gmsh drawing.svg\n'
                '  python -m svg_to_gmsh sketch.svg --visualize\n'
                '  python -m svg_to_gmsh design.svg --output-plot curves.png\n'
            ),
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # Required argument
        parser.add_argument(
            'svg_file', 
            help='Path to SVG file to process'
        )
        
        # Output options
        parser.add_argument(
            '--output', '-o', 
            help='Save text results to specified file'
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