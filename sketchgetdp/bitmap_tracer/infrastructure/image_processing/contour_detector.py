import cv2
import numpy as np
from typing import List, Tuple, Optional


class ContourDetector:
    """
    Detects and extracts contours from bitmap images using multiple thresholding strategies.
    This class is responsible for the initial image processing and contour detection phase,
    converting raster images into vectorizable shapes.
    """

    def detect(self, image_path: str) -> Tuple[Optional[List], Optional[List]]:
        """
        Detects all contours in the specified image using a multi-method thresholding approach.
        
        The detection process uses both adaptive and Otsu's thresholding to ensure
        robust contour extraction across varying image conditions. Contours are returned
        with hierarchy information to preserve structural relationships.
        
        Args:
            image_path: Path to the source image file for contour detection
            
        Returns:
            Tuple containing:
            - List of detected contours (or None if image loading fails)
            - Contour hierarchy information (or None if no contours detected)
            
        Raises:
            No explicit exceptions, but returns None values for failure cases
        """
        print(f"🔍 Detecting contours in: {image_path}")
        
        # Load and validate source image
        img = cv2.imread(image_path)
        if img is None:
            print(f"❌ Could not load image: {image_path}")
            return None, None
        
        height, width = img.shape[:2]
        print(f"📐 Image size: {width}x{height}")
        
        # Convert to grayscale as contour detection operates on single channel
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply multiple thresholding methods for robustness
        # Adaptive threshold handles varying illumination, Otsu finds optimal global threshold
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
        
        print(f"✅ Found {len(contours)} total contours")
        return contours, hierarchy
    
    def preprocess(self, image_path: str) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Prepares an image for contour detection by applying preprocessing transformations.
        
        This method performs the initial image conditioning steps without actually
        detecting contours, useful for debugging or multi-stage processing pipelines.
        
        Args:
            image_path: Path to the source image file for preprocessing
            
        Returns:
            Tuple containing:
            - Original BGR image as numpy array (or None if loading fails)
            - Preprocessed binary image ready for contour detection (or None if loading fails)
        """
        img = cv2.imread(image_path)
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