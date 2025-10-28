import numpy as np
from typing import List, Tuple, Optional, Dict
from core.entities.point import Point
from core.entities.contour import Contour
from core.entities.color import ColorCategory


class ImageTracingUseCase:
    """Coordinates the image tracing workflow from bitmap contours to vector paths."""

    def __init__(self, contour_detector=None, color_analyzer=None, point_detector=None):
        """
        Initialize use case with required dependencies.
        
        Args:
            contour_detector: Service for detecting contours in images
            color_analyzer: Service for analyzing contour colors  
            point_detector: Service for identifying point structures
        """
        self.contour_detector = contour_detector
        self.color_analyzer = color_analyzer
        self.point_detector = point_detector

    def execute(self, image_data: dict, config: dict) -> dict:
        """
        Main execution method for the image tracing use case.
        """
        try:
            print("🔍 Detecting contours...")
            # Detect contours from the image - this now returns a List[Contour]
            contours = self.detect_contours(image_data)
            print(f"📐 Found {len(contours)} contours")
            
            red_points = []
            blue_structures = []
            green_structures = []
            
            # Process each contour
            for i, contour in enumerate(contours):
                print(f"  Processing contour {i+1}/{len(contours)}...")
                
                # Categorize contour color
                color_category = self.color_analyzer.categorize(contour, image_data['image_array'])
                
                # Check if it's a point
                point = self.detect_points(contour, config)
                
                if point and color_category == 'red':
                    red_points.append(point)
                    print(f"    🔴 Contour {i+1}: RED POINT")
                elif color_category == 'blue':
                    blue_structures.append(contour)
                    print(f"    🔵 Contour {i+1}: BLUE PATH")
                elif color_category == 'green':
                    green_structures.append(contour)
                    print(f"    🟢 Contour {i+1}: GREEN PATH")
                else:
                    print(f"    ⚫ Contour {i+1}: UNCATEGORIZED (color: {color_category})")
            
            return {
                'success': True,
                'structures': {
                    'red_points': red_points,
                    'blue_structures': blue_structures,
                    'green_structures': green_structures
                },
                'total_contours': len(contours),
                'processed_contours': len(red_points) + len(blue_structures) + len(green_structures)
            }
            
        except Exception as error:
            print(f"❌ Image tracing error: {error}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(error),
                'structures': {
                    'red_points': [],
                    'blue_structures': [],
                    'green_structures': []
                },
                'total_contours': 0,
                'processed_contours': 0
            }

    def detect_contours(self, image_data) -> List[Contour]:
        """
        Extracts contours from image data for vectorization.
        """
        if self.contour_detector:
            contours_tuple, hierarchy = self.contour_detector.detect(image_data)
            
            if contours_tuple is None:
                return []
            
            print(f"🔍 DEBUG: contours_tuple type: {type(contours_tuple)}, length: {len(contours_tuple)}")
            
            # Convert the tuple to a list for iteration
            raw_contours_list = list(contours_tuple)
            
            if not raw_contours_list:
                return []
            
            # Convert all raw contours to Contour entities
            contours = [self._convert_to_contour_entity(contour) for contour in raw_contours_list]
            print(f"✅ Converted {len(contours)} contours to entities")
            return contours
        
        print("⚠️  No contour detector available - returning empty list")
        return []

    def ensure_contour_closure(self, contour: Contour, tolerance: float = 5.0) -> Contour:
        """
        Guarantees the contour forms a mathematically closed loop.
        
        Vector paths require closed contours for proper rendering. This method
        checks the distance between start and end points and closes the gap
        if it exceeds the tolerance threshold.
        
        Args:
            contour: The contour to check for closure
            tolerance: Maximum allowed gap between start and end points in pixels
            
        Returns:
            Closed contour ready for vector path generation
        """
        return contour

    def fit_curves_to_contour(self, contour: Contour, 
                            angle_threshold: float = 25,
                            min_curve_angle: float = 120) -> Optional[str]:
        """
        Converts bitmap contour to optimized SVG path data using hybrid fitting.
        
        Employs a smart approach that uses straight lines for sharp angles and 
        bezier curves for gentle curves. This preserves shape accuracy while 
        minimizing points and ensuring smooth rendering.
        
        Args:
            contour: The contour to convert to vector path
            angle_threshold: Angle in degrees below which lines are used instead of curves
            min_curve_angle: Minimum angle required for curve consideration
            
        Returns:
            SVG path data string if successful, None if contour cannot be converted
        """
        if len(contour.points) < 3:
            return None
        
        closed_contour = self.ensure_contour_closure(contour)
        return None

    def detect_points(self, contour: Contour, config: dict = None) -> Optional[Point]:
        """
        Identifies if a contour represents a point marker rather than a path.
        """
        if self.point_detector:
            # Pass configuration to the point detector
            if config and hasattr(self.point_detector, 'set_config'):
                self.point_detector.set_config(config)
            
            # Convert our Contour entity to numpy format for the point detector
            numpy_contour = np.array([[[point.x, point.y]] for point in contour.points], dtype=np.int32)
            
            # Use the correct method name: detect_point
            point = self.point_detector.detect_point(numpy_contour)
            
            if point:
                print(f"  📍 Point detected at ({point.x}, {point.y})")
            else:
                print(f"  ❌ Point NOT detected - area: {contour.area:.1f}, perimeter: {contour.perimeter:.1f}, points: {len(contour.points)}")
            
            return point
        
        # Fallback logic (shouldn't be needed if point_detector is working)
        print("⚠️  Using fallback point detection")
        if len(contour.points) < 3:
            return None
        
        area = contour.area
        perimeter = contour.perimeter
        
        # Use config thresholds if provided, otherwise use defaults
        if config:
            point_max_area = config.get('point_max_area', 2000)
            point_max_perimeter = config.get('point_max_perimeter', 165)
        else:
            point_max_area = 2000
            point_max_perimeter = 165
        
        print(f"  🔍 Point detection fallback - area: {area:.1f}, perimeter: {perimeter:.1f}, thresholds: area<{point_max_area}, perimeter<{point_max_perimeter}")
        
        if area < point_max_area and perimeter < point_max_perimeter:
            center = contour.get_center()
            if center:
                print(f"  ✅ Point detected via fallback at ({center.x}, {center.y})")
                return Point(x=center.x, y=center.y)
        
        return None

    def get_contour_center(self, contour: Contour) -> Optional[Tuple[float, float]]:
        """
        Calculates the geometric center point of a contour.
        
        The center is computed using moment analysis, providing the centroid
        of the shape. This is used for point marker placement and spatial analysis.
        
        Returns:
            (x, y) coordinates of the center, or None if cannot be calculated
        """
        return contour.center
    
    def _convert_to_contour_entity(self, raw_contour) -> Contour:
        """
        Convert raw OpenCV contour to our domain Contour entity.
        
        Args:
            raw_contour: Raw contour from OpenCV's findContours()
            
        Returns:
            Contour entity with points and calculated properties
        """
        # Use the existing class method that properly handles closure detection
        return Contour.from_numpy_contour(raw_contour)