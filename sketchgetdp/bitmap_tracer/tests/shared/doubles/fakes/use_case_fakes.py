from typing import List, Optional
from .....core.use_cases.image_tracing import ImageTracingUseCase
from .....core.use_cases.structure_filtering import StructureFilteringUseCase
from .....core.entities.contour import Contour

class FakeImageTracingUseCase(ImageTracingUseCase):
    """Test double for ImageTracingUseCase that allows controlled behavior for unit tests."""
    
    def __init__(self):
        self.execute_calls = []
        self.traced_contours = []
        self.should_fail = False
        self.error_message = ""
    
    def execute(self, image_path: str, config: Optional[dict] = None) -> List[Contour]:
        self.execute_calls.append((image_path, config))
        
        if self.should_fail:
            raise Exception(self.error_message)
        
        return self.traced_contours
    
    def set_traced_contours(self, contours: List[Contour]):
        """Configure the contours that execute() will return."""
        self.traced_contours = contours

class FakeStructureFilteringUseCase(StructureFilteringUseCase):
    """Test double for StructureFilteringUseCase with area-based filtering for testing."""
    
    def __init__(self):
        self.filter_calls = []
        self.filtered_contours = []
        self.removed_contours = []
    
    def filter(self, contours: List[Contour], criteria: dict) -> List[Contour]:
        self.filter_calls.append((contours, criteria))
        
        min_area = criteria.get('min_area', 0)
        max_area = criteria.get('max_area', float('inf'))
        
        filtered = []
        removed = []
        
        for contour in contours:
            area = self._calculate_area(contour)
            if min_area <= area <= max_area:
                filtered.append(contour)
            else:
                removed.append(contour)
        
        self.removed_contours = removed
        self.filtered_contours = filtered
        
        return filtered
    
    def _calculate_area(self, contour: Contour) -> float:
        # Using shoelace formula for polygon area calculation
        if len(contour.points) < 3:
            return 0.0
        
        area = 0.0
        n = len(contour.points)
        for i in range(n):
            j = (i + 1) % n
            area += contour.points[i].x * contour.points[j].y
            area -= contour.points[j].x * contour.points[i].y
        
        return abs(area) / 2.0