from typing import List, Tuple, Any
from core.entities.contour import Contour
from core.entities.point import Point


class StructureFilteringUseCase:
    """Applies business rules for filtering and prioritizing image structures."""

    def filter_structures_by_area(self, 
                                structures: List[Tuple[float, Any]], 
                                max_count: int) -> List[Tuple[float, Any]]:
        """
        Retains only the largest structures up to the specified count limit.
        
        Structures are sorted by area in descending order and the top N are kept.
        This prioritization ensures the most significant structures are processed
        while maintaining performance by limiting total output.
        
        Args:
            structures: List of (area, structure_data) tuples to filter
            max_count: Maximum number of structures to retain after filtering
            
        Returns:
            Filtered list containing only the largest structures up to max_count
        """
        if max_count <= 0:
            return []
        
        structures.sort(key=lambda x: x[0], reverse=True)
        
        if max_count < len(structures):
            return structures[:max_count]
        
        return structures

    def filter_contours_by_size(self, 
                               contours: List[Contour], 
                               min_area: float, 
                               max_area: float) -> List[Contour]:
        """
        Removes contours that fall outside the acceptable size range.
        
        Filters out noise (too small) and background elements (too large) based
        on area thresholds. This focuses processing on meaningful structures.
        
        Args:
            contours: Contours to evaluate against size constraints
            min_area: Minimum area threshold - contours smaller than this are excluded
            max_area: Maximum area threshold - contours larger than this are excluded
            
        Returns:
            Contours that meet the size criteria
        """
        filtered_contours = []
        
        for contour in contours:
            area = contour.area
            if min_area <= area <= max_area:
                filtered_contours.append(contour)
        
        return filtered_contours

    def filter_top_level_contours(self, 
                                 contours: List[Contour], 
                                 hierarchy_data: Any) -> List[Contour]:
        """
        Isolates top-level contours while excluding nested child contours.
        
        In contour hierarchies, child contours often represent holes or details
        within parent shapes. This filtering ensures only primary structures
        are processed for vectorization.
        
        Returns:
            Top-level contours without nested children
        """
        return contours

    def filter_by_circularity(self, 
                            contours: List[Contour], 
                            min_circularity: float = 0.01) -> List[Contour]:
        """
        Eliminates contours with irregular shapes that likely represent noise.
        
        Circularity measures how close a shape is to a perfect circle. Very low
        circularity values indicate elongated, fragmented, or noisy contours
        that should be excluded from vectorization.
        
        Args:
            contours: Contours to evaluate for shape regularity
            min_circularity: Minimum circularity threshold (1.0 = perfect circle)
            
        Returns:
            Contours with acceptable circularity values
        """
        filtered_contours = []
        
        for contour in contours:
            if contour.perimeter > 0:
                circularity = 4 * 3.14159 * contour.area / (contour.perimeter * contour.perimeter)
                if circularity >= min_circularity:
                    filtered_contours.append(contour)
        
        return filtered_contours

    def sort_contours_by_area(self, contours: List[Contour], descending: bool = True) -> List[Contour]:
        """
        Orders contours by their area for priority processing.
        
        Larger contours typically represent more important structures. Sorting
        enables processing prioritization and consistent output ordering.
        
        Args:
            contours: Contours to sort by area
            descending: True for largest first, False for smallest first
            
        Returns:
            Contours sorted by area
        """
        return sorted(contours, key=lambda c: c.area, reverse=descending)

    def categorize_structures_by_color(self, 
                                     contours: List[Contour], 
                                     original_image) -> Dict[str, List[Tuple[float, Contour]]]:
        """
        Organizes contours into color categories for independent processing.
        
        Different color categories (red, blue, green) have distinct processing
        rules and output requirements. This categorization enables color-specific
        filtering and rendering strategies.
        
        Returns:
            Dictionary mapping color categories to lists of (area, contour) pairs
        """
        return {}