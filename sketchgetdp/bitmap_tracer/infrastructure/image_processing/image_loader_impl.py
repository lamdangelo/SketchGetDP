"""
Concrete implementation of ImageLoader using OpenCV.

This implementation provides the actual image loading functionality
that the abstract interface defines.
"""

import os
import cv2
import numpy as np
from typing import Optional, Tuple
from interfaces.gateways.image_loader import ImageLoader


class OpenCVImageLoader(ImageLoader):
    """Concrete image loader implementation using OpenCV library."""
    
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    
    def load_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        Load image using OpenCV's imread function.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Image as numpy array in BGR format, or None if loading fails
        """
        try:
            if not self.validate_image_path(image_path):
                return None
                
            # Load image in color mode (BGR format)
            image = cv2.imread(image_path, cv2.IMREAD_COLOR)
            
            if image is None:
                print(f"⚠️ OpenCV could not decode image: {image_path}")
                return None
                
            print(f"✅ Loaded image: {image_path} - Shape: {image.shape}")
            return image
            
        except Exception as error:
            print(f"❌ Error loading image {image_path}: {error}")
            return None
    
    def get_image_dimensions(self, image: np.ndarray) -> Tuple[int, int]:
        """
        Extract width and height from image array.
        
        Args:
            image: numpy array with shape (height, width, channels)
            
        Returns:
            Tuple of (width, height)
        """
        if not isinstance(image, np.ndarray) or image.ndim < 2:
            raise ValueError("Invalid image array provided")
            
        height, width = image.shape[:2]
        return width, height
    
    def validate_image_path(self, image_path: str) -> bool:
        """
        Validate that the image file exists and has supported format.
        
        Args:
            image_path: Path to validate
            
        Returns:
            True if file is valid and accessible
        """
        if not os.path.exists(image_path):
            print(f"❌ Image file not found: {image_path}")
            return False
            
        if not os.access(image_path, os.R_OK):
            print(f"❌ Cannot read image file: {image_path}")
            return False
            
        file_ext = os.path.splitext(image_path)[1].lower()
        if file_ext not in self.SUPPORTED_FORMATS:
            print(f"❌ Unsupported image format: {file_ext}")
            return False
            
        return True