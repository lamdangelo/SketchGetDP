"""
Image Loader Gateway Interface

Defines the abstraction for image loading operations that infrastructure components
must implement. This interface follows the Dependency Inversion Principle, allowing
high-level modules to depend on abstractions rather than concrete implementations.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple
import numpy as np


class ImageLoader(ABC):
    """Contracts for loading and validating image data from various sources."""
    
    @abstractmethod
    def load_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        Load image data from the filesystem into a processable format.
        
        Implementations should handle file format decoding, color space conversion,
        and memory allocation for the image data.
        
        Args:
            image_path: Absolute or relative path to the image file
            
        Returns:
            Image data as numpy array with shape (height, width, channels),
            or None when file cannot be loaded
            
        Raises:
            FileNotFoundError: When image_path does not exist
            PermissionError: When image_path cannot be read
            ValueError: When file contains invalid image data
        """
        pass
    
    @abstractmethod
    def get_image_dimensions(self, image: np.ndarray) -> Tuple[int, int]:
        """
        Extract width and height from loaded image data.
        
        This method provides a consistent way to access image dimensions
        regardless of the underlying image representation.
        
        Args:
            image: Valid image data as returned by load_image()
            
        Returns:
            Tuple containing (width, height) in pixels
            
        Raises:
            ValueError: When image parameter is not a valid image array
        """
        pass
    
    @abstractmethod
    def validate_image_path(self, image_path: str) -> bool:
        """
        Verify that an image file exists and is accessible before loading.
        
        This pre-validation prevents unnecessary processing attempts
        on non-existent or inaccessible files.
        
        Args:
            image_path: Path to verify
            
        Returns:
            True if file exists, is readable, and has supported image extension
        """
        pass