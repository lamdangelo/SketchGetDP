"""
Interface for SVG parsing operations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List
from dataclasses import dataclass
from ...core.entities.point import Point
from ...core.entities.color import Color

@dataclass
class RawBoundary:
    """
    Temporary data structure for raw boundary data extracted from SVG.
    This will be converted to BoundaryCurve later after Bezier fitting.
    """
    points: List[Point]
    color: Color
    is_closed: bool = True
    
    def __post_init__(self):
        """Validate the raw boundary data."""
        # Allow single points for red dots, but require >=3 points for other colors
        if self.color != Color.RED and len(self.points) < 3:
            raise ValueError(f"Raw boundary must have at least 3 points for color {self.color.name}, got {len(self.points)}")
        elif self.color == Color.RED and len(self.points) < 1:
            raise ValueError("Red dot must have at least 1 point")


class SVGParserInterface(ABC):
    """
    Abstract interface for SVG parsing.
    """
    
    @abstractmethod
    def extract_boundaries_by_color(self, svg_file_path: str) -> Dict[Color, List[RawBoundary]]:
        """
        Parse SVG file and extract boundary curves grouped by color.
        
        Args:
            svg_file_path: Path to the SVG file
            
        Returns:
            Dictionary mapping colors to lists of RawBoundary objects containing raw points.
            
        Raises:
            ValueError: If the SVG file is invalid or cannot be parsed
        """
        pass