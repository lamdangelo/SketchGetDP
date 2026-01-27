"""
Interface for SVG parsing operations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List
from svg_to_getdp.core.entities.color import Color
from svg_to_getdp.core.entities.raw_outline import RawOutline


class SVGParserInterface(ABC):
    """
    Abstract interface for SVG parsing.
    """
    
    @abstractmethod
    def extract_raw_outlines_by_color(self, svg_file_path: str) -> Dict[Color, List[RawOutline]]:
        """
        Parse SVG file and extract raw_outlines grouped by color.
        
        Args:
            svg_file_path: Path to the SVG file
            
        Returns:
            Dictionary mapping colors to lists of RawOutline objects containing raw points.

        Raises:
            ValueError: If the SVG file is invalid or cannot be parsed
        """
        pass
    