"""
Classifies SVG colors into the application's Color enum.
Handles extraction from attributes, style strings, and color parsing.
"""

import re
import math
from typing import Dict
from svg_to_getdp.core.entities.color import Color


class SvgColorClassifier:
    """
    Classifies colors from SVG attributes and strings.
    Maps various color representations to the application's Color enum.
    """
    
    def extract_color_from_attributes(self, attributes: Dict) -> Color:
        """
        Extract color from svgpathtools attributes dictionary.
        """
        # Check stroke, fill, and style attributes
        stroke = attributes.get('stroke')
        fill = attributes.get('fill')
        style = attributes.get('style')
        
        color_str = None
        
        # Priority: stroke -> fill -> style attribute
        if stroke and stroke != 'none':
            color_str = stroke
        elif fill and fill != 'none':
            color_str = fill
        elif style:
            # Parse style attribute
            style_parts = [part.strip() for part in style.split(';')]
            for part in style_parts:
                if part.startswith('stroke:'):
                    color_parts = part.split(':', 1)
                    if len(color_parts) == 2:
                        potential_color = color_parts[1].strip()
                        if potential_color and potential_color != 'none':
                            color_str = potential_color
                            break
                elif part.startswith('fill:'):
                    color_parts = part.split(':', 1)
                    if len(color_parts) == 2:
                        potential_color = color_parts[1].strip()
                        if potential_color and potential_color != 'none':
                            color_str = potential_color
                            break
        
        if not color_str or color_str == 'none':
            raise ValueError(f"No valid color found in attributes: {attributes}")
        
        return self.parse_color_string(color_str)
    
    def extract_color_from_style(self, style_string: str) -> Color:
        """
        Extract color from SVG style attribute.
        """
        if not style_string:
            raise ValueError("No style attribute found")
        
        # Parse style string
        style_parts = [part.strip() for part in style_string.split(';')]
        color_str = None
        
        for part in style_parts:
            if part.startswith('fill:'):
                color_parts = part.split(':', 1)
                if len(color_parts) == 2:
                    color_str = color_parts[1].strip()
                    break
        
        if not color_str or color_str == 'none':
            raise ValueError(f"No valid fill color found in style: {style_string}")
        
        return self.parse_color_string(color_str)
    
    def parse_color_string(self, color_string: str) -> Color:
        """Convert color string to Color enum."""
        normalized_color = color_string.lower().strip()
        
        if self._is_red_color(normalized_color):
            return Color.RED
        elif self._is_green_color(normalized_color):
            return Color.GREEN
        elif self._is_blue_color(normalized_color):
            return Color.BLUE
        elif self._is_black_color(normalized_color):
            return Color.BLACK
        elif normalized_color.startswith('#'):
            return self._convert_hex_to_primary_color(normalized_color)
        elif normalized_color.startswith('rgb'):
            return self._parse_rgb_color_string(normalized_color)
        else:
            return self._infer_color_from_name(normalized_color)
    
    def _is_red_color(self, color_string: str) -> bool:
        """Check if color string represents a red color."""
        red_representations = {
            '#ff0000', 'red', '#f00', '#ff0000ff',
            'rgb(255,0,0)', 'rgb(255, 0, 0)',
            '#fa0000'
        }
        return color_string in red_representations
    
    def _is_green_color(self, color_string: str) -> bool:
        """Check if color string represents a green color."""
        green_representations = {
            '#00ff00', 'green', '#0f0', '#00ff00ff',
            'rgb(0,255,0)', 'rgb(0, 255, 0)',
            '#00f700'
        }
        return color_string in green_representations
    
    def _is_blue_color(self, color_string: str) -> bool:
        """Check if color string represents a blue color."""
        blue_representations = {
            '#0000ff', 'blue', '#00f', '#0000ffff',
            'rgb(0,0,255)', 'rgb(0, 0, 255)',
            '#0000fb'
        }
        return color_string in blue_representations
    
    def _is_black_color(self, color_string: str) -> bool:
        """Check if color string represents a black color."""
        black_representations = {
            '#000000', 'black', '#000', '#000000ff',
            'rgb(0,0,0)', 'rgb(0, 0, 0)'
        }
        return color_string in black_representations
    
    def _infer_color_from_name(self, color_name: str) -> Color:
        """Infer color from color name containing color hint."""
        if 'red' in color_name:
            return Color.RED
        elif 'green' in color_name:
            return Color.GREEN
        elif 'blue' in color_name:
            return Color.BLUE
        else:
            raise ValueError(f"Unknown color format: '{color_name}'")
    
    def _parse_rgb_color_string(self, rgb_string: str) -> Color:
        """Parse RGB color string and find closest primary color."""
        match = re.match(r'rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*[\d.]+\s*)?\)', rgb_string)
        if not match:
            raise ValueError(f"Invalid RGB color format: '{rgb_string}'")
        
        red, green, blue = map(int, match.groups())
        return self._find_closest_primary_color(red, green, blue)
    
    def _convert_hex_to_primary_color(self, hex_string: str) -> Color:
        """Convert hex color to closest primary color."""
        hex_digits = hex_string.lstrip('#')
        
        try:
            if len(hex_digits) == 6:
                red = int(hex_digits[0:2], 16)
                green = int(hex_digits[2:4], 16)
                blue = int(hex_digits[4:6], 16)
            elif len(hex_digits) == 3:
                red = int(hex_digits[0] * 2, 16)
                green = int(hex_digits[1] * 2, 16)
                blue = int(hex_digits[2] * 2, 16)
            else:
                raise ValueError(f"Invalid hex color length: {len(hex_digits)}")
            
            return self._find_closest_primary_color(red, green, blue)
            
        except ValueError as e:
            raise ValueError(f"Invalid hex color format '#{hex_digits}': {e}")

    def _find_closest_primary_color(self, red: int, green: int, blue: int) -> Color:
        """Find the closest primary color using Euclidean distance in RGB space."""
        primary_colors = {
            Color.RED: (255, 0, 0),
            Color.GREEN: (0, 255, 0),
            Color.BLUE: (0, 0, 255),
            Color.BLACK: (0, 0, 0)
        }
        
        min_distance = float('inf')
        closest_color = None
        
        for color, (target_red, target_green, target_blue) in primary_colors.items():
            distance = math.sqrt(
                (red - target_red)**2 + 
                (green - target_green)**2 + 
                (blue - target_blue)**2
            )
            if distance < min_distance:
                min_distance = distance
                closest_color = color
        
        if closest_color is None:
            raise ValueError(f"Could not determine closest primary color for RGB({red},{green},{blue})")
        
        return closest_color
    