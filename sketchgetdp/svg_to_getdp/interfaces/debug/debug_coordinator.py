import os
from datetime import datetime


class DebugCoordinator:
    """Main utility class for coordinating all debug writing operations."""
    
    def __init__(self):
        """Initialize DebugCoordinator with a shared timestamp for all debug outputs."""
        self._shared_timestamp = None
        self._svg_file_path = None
        self._svg_name = None
    
    def set_svg_file(self, svg_file_path: str):
        """Set the SVG file being processed."""
        self._svg_file_path = svg_file_path
        svg_filename = os.path.basename(svg_file_path)
        self._svg_name = os.path.splitext(svg_filename)[0]
    
    def get_shared_timestamp(self) -> str:
        """
        Get a shared timestamp for all debug outputs in this run.
        Creates a new timestamp on first call, reuses it for subsequent calls.
        """
        if self._shared_timestamp is None:
            self._shared_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self._shared_timestamp
    
    def get_debug_directory(self) -> str:
        """Get the debug directory path, creating it if necessary."""
        debug_dir = "debug"
        os.makedirs(debug_dir, exist_ok=True)
        return debug_dir
    
    def get_debug_filename(self, prefix: str, extension: str = ".txt") -> str:
        """Generate a debug filename with timestamp."""
        if not self._svg_name:
            raise ValueError("SVG file not set. Call set_svg_file() first.")
        
        timestamp = self.get_shared_timestamp()
        debug_dir = self.get_debug_directory()
        return f"{debug_dir}/{prefix}_{self._svg_name}_{timestamp}{extension}"
    
    def get_debug_plot_filename(self, prefix: str = "geometry_plot", extension: str = ".png") -> str:
        """Generate a debug plot filename with timestamp."""
        return self.get_debug_filename(prefix, extension)
    
    def get_svg_name(self) -> str:
        """Get the base name of the SVG file."""
        if not self._svg_name:
            raise ValueError("SVG file not set. Call set_svg_file() first.")
        return self._svg_name
    
    def get_svg_file_path(self) -> str:
        """Get the full SVG file path."""
        if not self._svg_file_path:
            raise ValueError("SVG file not set. Call set_svg_file() first.")
        return self._svg_file_path
    