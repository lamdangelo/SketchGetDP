import argparse
from typing import List

class ArgParser:
    """Simple argument parser for CLI input"""
    
    def parse_args(self, args: List[str] = None) -> argparse.Namespace:
        parser = argparse.ArgumentParser(description='Convert SVG to geometry representation')
        parser.add_argument('svg_file', help='Path to SVG file to process')
        parser.add_argument('--output', '-o', help='Output file path (optional)')
        parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
        return parser.parse_args(args)