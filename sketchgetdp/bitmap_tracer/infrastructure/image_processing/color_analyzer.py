import cv2
import numpy as np
from collections import defaultdict
from typing import Tuple, Optional, Dict, List
from core.entities.color import ColorCategory

class ColorAnalyzer:
    """
    Analyzes and categorizes colors in images and contours using HSV color space.
    
    This class provides color classification capabilities that distinguish between
    major color groups (blue, red, green) while filtering out background colors
    (white, black) and undefined colors.
    """

    def __init__(self, config: Dict = None):
        """
        Initialize with optional configuration for color ranges.
        
        Args:
            config: Dictionary containing color detection parameters
        """
        self.config = config or {}
        # Set default ranges if not provided in config
        self.blue_hue_range = self.config.get('blue_hue_range', [100, 140])
        self.red_hue_ranges = self.config.get('red_hue_range', [[0, 10], [170, 180]])
        self.green_hue_range = self.config.get('green_hue_range', [35, 85])
        self.min_saturation = self.config.get('min_saturation', 50)
        self.max_value_white = self.config.get('max_value_white', 200)
        self.min_value_black = self.config.get('min_value_black', 50)

    def categorize_color_pixel(self, bgr_color: List[int]) -> Tuple[ColorCategory, Optional[str]]:
        """
        Classifies a BGR color pixel into one of the predefined color categories.
        
        Uses HSV color space for more perceptually accurate color discrimination
        compared to RGB/BGR. The categorization focuses on the three primary colors
        used in the tracing system while excluding background and noise colors.
        
        Args:
            bgr_color: List of [blue, green, red] color values (0-255 range)
            
        Returns:
            Tuple containing:
            - ColorCategory enum value
            - Standardized hex color code for primary colors, None for others
        """
        if len(bgr_color) < 3:
            return ColorCategory.OTHER, None
            
        b, g, r = bgr_color[:3]
        
        # Convert to HSV for perceptual color analysis
        # HSV provides better separation of hue, saturation, and brightness
        hsv_color = np.uint8([[[b, g, r]]])
        hsv = cv2.cvtColor(hsv_color, cv2.COLOR_BGR2HSV)[0][0]
        hue, saturation, value = hsv
        
        # Debug output for red colors
        if r > 150 and g < 100 and b < 100:
            print(f"🔴 Potential red: RGB=({r},{g},{b}), HSV=({hue},{saturation},{value})")
        
        # Filter out near-white colors (high brightness, low saturation)
        if value > self.max_value_white and saturation < self.min_saturation:
            return ColorCategory.WHITE, None
        
        # Filter out near-black colors (very low brightness)
        if value < self.min_value_black:
            return ColorCategory.BLACK, None
        
        # Ensure minimum saturation for colorfulness
        if saturation < self.min_saturation:
            return ColorCategory.OTHER, None
        
        # Blue classification
        blue_low, blue_high = self.blue_hue_range
        if (blue_low <= hue <= blue_high) or (b > g + 20 and b > r + 20):
            return ColorCategory.BLUE, "#0000FF"
        
        # Red classification - handle the two red ranges in HSV
        for red_low, red_high in self.red_hue_ranges:
            if red_low <= hue <= red_high:
                return ColorCategory.RED, "#FF0000"
        # Also check RGB dominance for red
        if (r > g + 30 and r > b + 30):
            return ColorCategory.RED, "#FF0000"
        
        # Green classification
        green_low, green_high = self.green_hue_range
        if (green_low <= hue <= green_high) or (g > r + 20 and g > b + 20):
            return ColorCategory.GREEN, "#00FF00"
        
        return ColorCategory.OTHER, None

    def get_dominant_color(self, contour: np.ndarray, original_image: np.ndarray) -> Optional[str]:
        """Identifies dominant stroke color along contour boundary."""
        if contour is None:
            print("❌ Contour is None")
            return None
            
        try:
            # Ensure contour is in the correct format for OpenCV
            if len(contour) == 0:
                print("❌ Empty contour array")
                return None
                
            print(f"🔍 Initial contour shape: {contour.shape}, dtype: {contour.dtype}")
            
            # Make a copy and ensure it's the exact format OpenCV expects
            contour_fixed = contour.astype(np.int32)  # OpenCV often prefers int32 for drawContours
            print(f"🔍 Fixed contour shape: {contour_fixed.shape}, dtype: {contour_fixed.dtype}")
            
            # Create boundary mask to isolate the actual stroke pixels
            boundary_mask = np.zeros(original_image.shape[:2], np.uint8)
            
            # Try different approaches for drawing contours
            try:
                # Method 1: Direct drawing
                cv2.drawContours(boundary_mask, [contour_fixed], 0, 255, 2)
            except Exception as e1:
                print(f"⚠️ Method 1 failed: {e1}")
                try:
                    # Method 2: Ensure it's a list of contours
                    cv2.drawContours(boundary_mask, [contour_fixed], -1, 255, 2)
                except Exception as e2:
                    print(f"⚠️ Method 2 failed: {e2}")
                    try:
                        # Method 3: Convert to list of points
                        points = contour_fixed.reshape(-1, 2)
                        contour_list = [points.astype(np.int32)]
                        cv2.drawContours(boundary_mask, contour_list, 0, 255, 2)
                    except Exception as e3:
                        print(f"❌ All contour drawing methods failed: {e3}")
                        return None
            
            # Check if we successfully drew anything
            if np.count_nonzero(boundary_mask) == 0:
                print("⚠️ No pixels drawn in boundary mask")
                return None
                
            boundary_pixels = original_image[boundary_mask == 255]
            
            # Early return if no boundary pixels were sampled
            if len(boundary_pixels) == 0:
                print("⚠️ No boundary pixels found for color analysis")
                return None
            
            print(f"🔍 Found {len(boundary_pixels)} boundary pixels for analysis")
            
            # Tally color categories from all boundary pixels
            color_categories = defaultdict(int)
            total_pixels = len(boundary_pixels)
            
            # Sample every 10th pixel for performance (unless it's a small contour)
            step = max(1, total_pixels // 100)  # Sample at most 100 pixels
            
            sampled_pixels = boundary_pixels[::step]
            print(f"🔍 Analyzing {len(sampled_pixels)} sampled pixels")
            
            for pixel in sampled_pixels:
                category, hex_color = self.categorize_color_pixel(pixel.tolist())
                # Only count meaningful color categories, ignore background colors
                if category in [ColorCategory.BLUE, ColorCategory.RED, ColorCategory.GREEN]:
                    color_categories[category.value] += 1
            
            # Debug output with percentages
            if color_categories:
                category_info = []
                for category, count in color_categories.items():
                    percentage = (count / len(sampled_pixels)) * 100
                    category_info.append(f"{category}: {count}({percentage:.1f}%)")
                print(f"🎨 Color distribution: {', '.join(category_info)}")
            else:
                print("🎨 No primary colors detected in boundary pixels")
                # Let's check what colors we ARE seeing
                unique_colors = np.unique(boundary_pixels, axis=0)
                print(f"🔍 Unique colors found: {len(unique_colors)}")
                if len(unique_colors) > 0:
                    for i, color in enumerate(unique_colors[:5]):  # Show first 5 unique colors
                        b, g, r = color
                        print(f"   Color {i}: BGR({b},{g},{r})")
            
            # Determine the most frequent valid color category
            if color_categories:
                dominant_category = max(color_categories.items(), key=lambda x: x[1])[0]
                
                # Map category to standardized hex color
                color_map = {
                    "blue": "#0000FF",
                    "red": "#FF0000", 
                    "green": "#00FF00"
                }
                dominant_color = color_map.get(dominant_category)
                print(f"🎯 Dominant color: {dominant_color}")
                return dominant_color
            
            print("⚠️ No valid color categories found")
            return None
            
        except Exception as e:
            print(f"❌ Error in get_dominant_color: {e}")
            import traceback
            traceback.print_exc()
            return None

    def categorize(self, contour, image: np.ndarray) -> Optional[str]:
        """
        MAIN INTERFACE METHOD - Updated to handle Contour entities properly
        """
        # Handle both Contour entities and legacy numpy arrays
        if hasattr(contour, 'to_numpy'):
            # It's a Contour entity - convert to numpy for OpenCV processing
            contour_points = contour.to_numpy()
            print(f"🔍 ColorAnalyzer.categorize() called with Contour entity: {len(contour.points)} points, area: {contour.area:.1f}")
            print(f"🔍 Contour numpy shape: {contour_points.shape}, dtype: {contour_points.dtype}")
            print(f"🔍 First few points: {contour_points[:3] if len(contour_points) > 0 else 'EMPTY'}")
        elif hasattr(contour, 'points'):
            # Alternative check for Contour entity
            contour_points = np.array([[point.x, point.y] for point in contour.points], dtype=np.float32).reshape(-1, 1, 2)
            print(f"🔍 ColorAnalyzer.categorize() called with Contour entity: {len(contour.points)} points, area: {contour.area:.1f}")
            print(f"🔍 Manual numpy shape: {contour_points.shape}, dtype: {contour_points.dtype}")
        else:
            # It's a numpy array (legacy support)
            contour_points = contour
            print(f"🔍 ColorAnalyzer.categorize() called with numpy contour: {len(contour)} points")
        
        # Check if contour_points is valid
        if contour_points is None or len(contour_points) == 0:
            print("❌ Empty contour points, skipping color analysis")
            return None
        
        hex_color = self.get_dominant_color(contour_points, image)
        
        if hex_color == "#FF0000":
            print("✅ Categorized as RED")
            return "red"
        elif hex_color == "#0000FF":
            print("✅ Categorized as BLUE")
            return "blue"
        elif hex_color == "#00FF00":
            print("✅ Categorized as GREEN") 
            return "green"
        else:
            print(f"❌ No dominant color found, got: {hex_color}")
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
        dominant_color = self.get_dominant_color(contour, image)
        
        return {
            'dominant_color': dominant_color,
            'contour_area': cv2.contourArea(contour),
            'contour_points': len(contour)
        }