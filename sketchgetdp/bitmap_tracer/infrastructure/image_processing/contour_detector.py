import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict
from .contour_closure_service import ContourClosureService


class ContourDetector:
    """
    Detects and extracts contours from bitmap images using multiple thresholding strategies.
    This class is responsible for the initial image processing and contour detection phase,
    converting raster images into vectorizable shapes.
    """

    def __init__(self):
        """Initialize the contour detector with closure service."""
        self.closure_service = ContourClosureService()

    def detect(self, image_data: Dict) -> Tuple[Optional[tuple], Optional[np.ndarray]]:
        """
        Detects all contours in the provided image data using a multi-method thresholding approach.
        
        Args:
            image_data: Dictionary containing 'image_array' with the image data
            
        Returns:
            Tuple containing:
            - Tuple of detected contours (or None if image loading fails)
            - Contour hierarchy information as numpy array (or None if no contours detected)
        """
        print(f"🔍 Detecting contours in image data...")
        
        # Extract image array from the data dictionary
        img = image_data.get('image_array')
        if img is None:
            print(f"❌ No image array found in image data")
            return None, None
        
        height, width = img.shape[:2]
        print(f"📐 Image size: {width}x{height}")
        
        # Convert to grayscale as contour detection operates on single channel
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply multiple thresholding methods for robustness
        binary1 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                    cv2.THRESH_BINARY_INV, 15, 5)
        
        _, binary2 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Combine results from both methods to capture all potential contours
        combined = cv2.bitwise_or(binary1, binary2)
        
        # Apply morphological operations to clean up noise and connect broken segments
        kernel = np.ones((3,3), np.uint8)
        cleaned = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel, iterations=2)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Extract contours with hierarchy to preserve parent-child relationships
        contours, hierarchy = cv2.findContours(cleaned, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_KCOS)
        
        # ENSURE ALL CONTOURS ARE CLOSED - THIS IS THE KEY FIX
        closed_contours = []
        for i, contour in enumerate(contours):
            # Use the closure service to guarantee this contour is closed
            closed_contour = self.closure_service.ensure_closure(contour)
            closed_contours.append(closed_contour)
            
            # Debug information about closure status
            original_length = len(contour)
            closed_length = len(closed_contour)
            is_closed = self.closure_service.is_closed(closed_contour)
            closure_gap = self.closure_service.calculate_closure_gap(contour)
            
            closure_status = "🔒 CLOSED" if is_closed else "🔓 OPEN"
            if closed_length > original_length:
                closure_status += " (forced)"
                
            print(f"  {closure_status} Contour {i+1}: {original_length} → {closed_length} points, gap: {closure_gap:.1f}px")
        
        print(f"✅ Found {len(closed_contours)} total contours (all ensured closed)")
        return tuple(closed_contours), hierarchy
    
    def preprocess(self, image_data: Dict) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Prepares an image for contour detection by applying preprocessing transformations.
        
        Args:
            image_data: Dictionary containing 'image_array' with the image data
            
        Returns:
            Tuple containing:
            - Original BGR image as numpy array (or None if loading fails)
            - Preprocessed binary image ready for contour detection (or None if loading fails)
        """
        img = image_data.get('image_array')
        if img is None:
            return None, None
        
        # Convert to single channel for thresholding operations
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Dual thresholding strategy for comprehensive feature capture
        binary1 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY_INV, 15, 5)
        
        _, binary2 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Merge thresholding results
        combined = cv2.bitwise_or(binary1, binary2)
        
        # Morphological cleaning to reduce noise and improve contour quality
        kernel = np.ones((3,3), np.uint8)
        cleaned = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel, iterations=2)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel, iterations=1)
        
        return img, cleaned
    
    def detect_with_closure_analysis(self, image_data: Dict) -> Tuple[Optional[tuple], Optional[np.ndarray], List[Dict]]:
        """
        Enhanced detection with detailed closure analysis for debugging and quality control.
        
        Args:
            image_data: Dictionary containing 'image_array' with the image data
            
        Returns:
            Tuple containing:
            - Tuple of closed contours
            - Contour hierarchy
            - List of closure analysis reports for each contour
        """
        contours, hierarchy = self.detect(image_data)
        
        if contours is None:
            return None, None, []
        
        # Generate detailed closure analysis for each contour
        closure_reports = []
        for i, contour in enumerate(contours):
            analysis = self.closure_service.analyze_contour_closure(contour)
            closure_reports.append(analysis)
            
            status = "CLOSED" if analysis['is_closed'] else "OPEN"
            print(f"  📊 Contour {i+1}: {status}, gap: {analysis['closure_gap']:.2f}px, "
                  f"area: {analysis['area']:.1f}, points: {analysis['point_count']}")
        
        return contours, hierarchy, closure_reports