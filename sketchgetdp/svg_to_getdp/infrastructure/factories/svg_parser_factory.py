"""
Factory for creating SVG parser instances.
Implements the Factory pattern for dependency injection.
"""

from typing import Optional
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
    
    @staticmethod  
    def create_with_config(samples_per_segment: int = 20, 
                          points_per_unit_length: int = 1000) -> SVGParserInterface:
        """
        Create an SVG parser with custom configuration.
        
        Args:
            samples_per_segment: Number of samples per SVG path segment
            points_per_unit_length: Target points per unit length for resampling
            
        Returns:
            SVGParserInterface: A configured parser instance
        """
        return SvgParser(
            samples_per_segment=samples_per_segment,
            points_per_unit_length=points_per_unit_length
        )
    
    @staticmethod
    def from_config_dict(config: Optional[dict] = None) -> SVGParserInterface:
        """
        Create a parser from a configuration dictionary.
        
        Args:
            config: Dictionary with parser configuration. If None, uses defaults.
                   Expected keys: 'samples_per_segment', 'points_per_unit_length'
                   
        Returns:
            SVGParserInterface: A configured parser instance
        """
        if config is None:
            config = {}
        
        samples = config.get('samples_per_segment', 20)
        points_per_unit = config.get('points_per_unit_length', 1000)
        
        return SvgParserFactory.create_with_config(samples, points_per_unit)
    