"""
Applies SVG transforms to points and coordinates.
Handles matrix, rotate, scale, and translate transformations.
"""

import re
import math
from typing import Tuple


class SvgTransformApplier:
    """
    Applies SVG transform operations to points.
    Supports matrix(), rotate(), scale(), and translate() transforms.
    """
    
    def apply_transform_to_point(self, x: float, y: float, transform_str: str) -> Tuple[float, float]:
        """
        Apply SVG transform to a point.
        Handles matrix(), rotate(), scale(), and translate() transforms.
        """
        if not transform_str:
            return x, y
        
        # Parse matrix transform: matrix(a,b,c,d,e,f)
        matrix_match = re.match(
            r'matrix\s*\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)',
            transform_str
        )
        
        if matrix_match:
            a, b, c, d, e, f = map(float, matrix_match.groups())
            # Apply matrix transformation
            new_x = a * x + c * y + e
            new_y = b * x + d * y + f
            return new_x, new_y
        
        # Parse rotate transform: rotate(angle, cx, cy) or rotate(angle)
        rotate_match = re.match(
            r'rotate\s*\(\s*([-\d.]+)\s*(?:,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*)?\)',
            transform_str
        )
        
        if rotate_match:
            angle = float(rotate_match.group(1))
            # Convert to radians
            angle_rad = math.radians(angle)
            
            if rotate_match.group(2) and rotate_match.group(3):
                # Has center point
                cx = float(rotate_match.group(2))
                cy = float(rotate_match.group(3))
                # Translate to origin, rotate, translate back
                x_translated = x - cx
                y_translated = y - cy
                new_x = x_translated * math.cos(angle_rad) - y_translated * math.sin(angle_rad) + cx
                new_y = x_translated * math.sin(angle_rad) + y_translated * math.cos(angle_rad) + cy
            else:
                # No center point, rotate around origin (0,0)
                new_x = x * math.cos(angle_rad) - y * math.sin(angle_rad)
                new_y = x * math.sin(angle_rad) + y * math.cos(angle_rad)
            
            return new_x, new_y
        
        # Handle translate transforms
        translate_match = re.match(
            r'translate\s*\(\s*([-\d.]+)\s*(?:,\s*([-\d.]+)\s*)?\)',
            transform_str
        )
        if translate_match:
            tx = float(translate_match.group(1))
            ty = float(translate_match.group(2)) if translate_match.group(2) else 0
            return x + tx, y + ty
        
        # Handle scale transforms: scale(sx, sy) or scale(s)
        scale_match = re.match(
            r'scale\s*\(\s*([-\d.]+)\s*(?:,\s*([-\d.]+)\s*)?\)',
            transform_str
        )
        if scale_match:
            sx = float(scale_match.group(1))
            sy = float(scale_match.group(2)) if scale_match.group(2) else sx
            return x * sx, y * sy
        
        # Return original point if transform not recognized
        print(f"WARNING: Unsupported transform format: {transform_str}")
        return x, y
    