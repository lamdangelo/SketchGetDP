"""
Interface for SVG parsing operations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List
from dataclasses import dataclass
from svg_to_getdp.core.entities.point import Point
from svg_to_getdp.core.entities.color import Color

@dataclass
class RawOutline:
    """
    Temporary data structure for raw outline data extracted from SVG.
    This will be converted to Outline later after Bezier fitting.
    """
    points: List[Point]
    color: Color
    is_closed: bool = True
    
    def __post_init__(self):
        """Validate the raw outline data."""
        # Allow single points for red dots, but require >=3 points for other colors
        if self.color != Color.RED and len(self.points) < 3:
            raise ValueError(f"Raw outline must have at least 3 points for color {self.color.name}, got {len(self.points)}")
        elif self.color == Color.RED and len(self.points) < 1:
            raise ValueError("Red dot must have at least 1 point")


class SVGParserInterface(ABC):
    """
    Abstract interface for SVG parsing.
    """
    
    @abstractmethod
    def extract_outlines_by_color(self, svg_file_path: str) -> Dict[Color, List[RawOutline]]:
        """
        Parse SVG file and extract outlines grouped by color.
        
        Args:
            svg_file_path: Path to the SVG file
            
        Returns:
            Dictionary mapping colors to lists of RawOutline objects containing raw points.

        Raises:
            ValueError: If the SVG file is invalid or cannot be parsed
        """
        pass