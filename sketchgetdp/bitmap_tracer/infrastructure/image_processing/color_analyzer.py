import cv2
import numpy as np
from collections import defaultdict
from typing import Tuple, Optional, Dict, List


class ColorAnalyzer:
    """
    Analyzes and categorizes colors in images and contours using HSV color space.
    
    This class provides color classification capabilities that distinguish between
    major color groups (blue, red, green) while filtering out background colors
    (white, black) and undefined colors.
    """

    def categorize(self, bgr_color: List[int]) -> Tuple[str, Optional[str]]:
        """
        Classifies a BGR color pixel into one of the predefined color categories.
        
        Uses HSV color space for more perceptually accurate color discrimination
        compared to RGB/BGR. The categorization focuses on the three primary colors
        used in the tracing system while excluding background and noise colors.
        
        Args:
            bgr_color: List of [blue, green, red] color values (0-255 range)
            
        Returns:
            Tuple containing:
            - Color category name as string ('blue', 'red', 'green', 'white', 'black', 'other')
            - Standardized hex color code for primary colors, None for others
        """
        b, g, r = bgr_color
        
        # Convert to HSV for perceptual color analysis
        # HSV provides better separation of hue, saturation, and brightness
        hsv = cv2.cvtColor(np.uint8([[[b, g, r]]]), cv2.COLOR_BGR2HSV)[0][0]
        hue, saturation, value = hsv
        
        # Filter out near-white colors (high brightness, low saturation)
        # These typically represent background or highlight areas
        if value > 200 and saturation < 50:
            return "white", None
        
        # Filter out near-black colors (very low brightness)
        # These represent shadows or dark background elements
        if value < 50:
            return "black", None
        
        # Primary color classification using both HSV and RGB criteria
        # Dual criteria provide robustness across different color representations
        if (hue >= 100 and hue <= 140) or (b > g + 20 and b > r + 20):
            return "blue", "#0000FF"
        elif (hue >= 0 and hue <= 10) or (hue >= 170 and hue <= 180) or (r > g + 20 and r > b + 20):
            return "red", "#FF0000"
        elif (hue >= 35 and hue <= 85) or (g > r + 20 and g > b + 20):
            return "green", "#00FF00"
        else:
            return "other", None
    
    def get_dominant(self, contour: np.ndarray, original_image: np.ndarray) -> Optional[str]:
        """
        Identifies the dominant stroke color along a contour's boundary.
        
        Analyzes the actual drawn stroke rather than filled areas by sampling
        pixels along the contour boundary. This ensures we capture the intended
        drawing color rather than any interior fill colors.
        
        Args:
            contour: numpy array of contour points
            original_image: source BGR image containing the color information
            
        Returns:
            Standardized hex color code for the dominant stroke color,
            or None if no valid stroke color could be determined
        """
        # Create boundary mask to isolate the actual stroke pixels
        # Using thickness=2 to capture the stroke width adequately
        boundary_mask = np.zeros(original_image.shape[:2], np.uint8)
        cv2.drawContours(boundary_mask, [contour], 0, 255, 2)
        
        boundary_pixels = original_image[boundary_mask == 255]
        
        # Early return if no boundary pixels were sampled
        if len(boundary_pixels) == 0:
            return None
        
        # Tally color categories from all boundary pixels
        color_categories = defaultdict(int)
        
        for pixel in boundary_pixels:
            b, g, r = pixel
            category, hex_color = self.categorize([b, g, r])
            # Only count meaningful color categories, ignore background colors
            if category not in ["white", "black", "other"]:
                color_categories[category] += 1
        
        # Determine the most frequent valid color category
        if color_categories:
            dominant_category = max(color_categories.items(), key=lambda x: x[1])[0]
            
            # Map category to standardized hex color
            if dominant_category == "blue":
                return "#0000FF"
            elif dominant_category == "red":
                return "#FF0000"
            elif dominant_category == "green":
                return "#00FF00"
        
        return None
    
    def analyze_contour_color(self, contour: np.ndarray, image: np.ndarray) -> Dict:
        """
        Performs comprehensive color analysis on a contour.
        
        Provides a complete color profile for a contour including dominant color
        and geometric properties. Useful for debugging and quality analysis.
        
        Args:
            contour: numpy array of contour points to analyze
            image: source BGR image for color sampling
            
        Returns:
            Dictionary containing:
            - dominant_color: Hex code of dominant stroke color
            - contour_area: Geometric area of the contour
            - contour_points: Number of points in the contour
        """
        dominant_color = self.get_dominant(contour, image)
        
        return {
            'dominant_color': dominant_color,
            'contour_area': cv2.contourArea(contour),
            'contour_points': len(contour)
        }