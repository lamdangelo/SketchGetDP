import numpy as np
from typing import List, Tuple, Optional
from core.entities.point import Point
from core.entities.contour import Contour


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
            # Detect contours from the image
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

    def detect_points(self, contour: Contour, config: dict = None) -> Optional[Point]:
        """
        Identifies if a contour represents a point marker rather than a path.
        """
        if config and hasattr(self.point_detector, 'set_config'):
            self.point_detector.set_config(config)
        
        numpy_contour = np.array([[[point.x, point.y]] for point in contour.points], dtype=np.int32)
        point = self.point_detector.detect_point(numpy_contour)
        
        if point:
            print(f"  📍 Point detected at ({point.x}, {point.y})")
        else:
            print(f"  ❌ Point NOT detected - area: {contour.area:.1f}, perimeter: {contour.perimeter:.1f}, points: {len(contour.points)}")
        
        return point
    
    def _convert_to_contour_entity(self, raw_contour) -> Contour:
        """
        Convert raw OpenCV contour to our domain Contour entity.
        
        Args:
            raw_contour: Raw contour from OpenCV's findContours()
            
        Returns:
            Contour entity with points and calculated properties
        """
        return Contour.from_numpy_contour(raw_contour)
    