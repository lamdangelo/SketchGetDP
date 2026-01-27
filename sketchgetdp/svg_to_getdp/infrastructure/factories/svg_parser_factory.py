"""
Factory for creating SVG parser instances.
Implements the Factory pattern for dependency injection.
"""

from svg_to_getdp.infrastructure.svg_processing.svg_parser import SvgParser
from svg_to_getdp.interfaces.abstractions.svg_parser_interface import SVGParserInterface


class SvgParserFactory:
    """
    Factory for creating SVG parser instances.
    
    Follows the Factory pattern to decouple object creation from usage.
    This allows for easy swapping of implementations and centralized configuration.
    """
    
    @staticmethod
    def create_default() -> SVGParserInterface:
        """
        Create a default SVG parser with standard settings.
        
        Returns:
            SVGParserInterface: A parser instance with default parameters
        """
        return SvgParser()
