"""
Coordinates the image tracing workflow from input image to SVG output.

The TracingController is the primary interface for the bitmap tracing functionality.
It orchestrates the complete workflow while maintaining separation of concerns
between use cases, business rules, and external interfaces.

Key Responsibilities:
- Validate and sanitize input parameters
- Coordinate execution of use cases in proper sequence
- Handle errors and transform them for presentation
- Provide status information about the system
- Maintain dependency inversion through constructor injection
"""

import os
from typing import Optional, Dict, Any

# Internal imports follow clean architecture dependency direction
from ...infrastructure.configuration.config_loader import ConfigLoader
from ...infrastructure.image_processing.contour_detector import ContourDetector
from ...infrastructure.image_processing.color_analyzer import ColorAnalyzer
from ...infrastructure.svg_generation.svg_generator import SVGGenerator
from ...infrastructure.point_detection.point_detector import PointDetector
from ...infrastructure.svg_generation.shape_processor import ShapeProcessor
from ...core.use_cases.image_tracing import ImageTracingUseCase
from ...core.use_cases.structure_filtering import StructureFilteringUseCase
from ...interfaces.presenters.svg_presenter import SVGPresenter
from ...interfaces.gateways.image_loader import ImageLoader
from ...interfaces.gateways.config_repository import ConfigRepository


class TracingController:
    """
    Primary controller for bitmap-to-vector image tracing operations.
    
    This controller follows the Single Responsibility Principle by focusing
    solely on coordinating the tracing workflow. It delegates specific
    responsibilities to specialized use cases and infrastructure components.
    
    Dependencies are injected to support testability and follow the
    Dependency Inversion Principle.
    """

    def __init__(self, 
                 config_repository: Optional[ConfigRepository] = None,
                 image_loader: Optional[ImageLoader] = None,
                 contour_detector: Optional[ContourDetector] = None,
                 color_analyzer: Optional[ColorAnalyzer] = None,
                 point_detector: Optional[PointDetector] = None,
                 shape_processor: Optional[ShapeProcessor] = None,
                 svg_generator: Optional[SVGGenerator] = None,
                 svg_presenter: Optional[SVGPresenter] = None):
        """
        Initialize controller with dependencies.
        
        All dependencies are optional to allow for flexible testing and
        default implementations. This follows the Null Object Pattern
        for optional dependencies.
        
        Args:
            config_repository: Repository for configuration data access
            image_loader: Service for loading image data from filesystem
            contour_detector: Detects contours in loaded images
            color_analyzer: Analyzes and categorizes colors in contours
            point_detector: Identifies point-like structures in contours
            shape_processor: Processes and filters geometric shapes
            svg_generator: Converts processed structures to SVG format
            svg_presenter: Handles presentation of SVG results
        """
        self.config_repository = config_repository or ConfigRepository()
        self.image_loader = image_loader or ImageLoader()
        self.contour_detector = contour_detector or ContourDetector()
        self.color_analyzer = color_analyzer or ColorAnalyzer()
        self.point_detector = point_detector or PointDetector()
        self.shape_processor = shape_processor or ShapeProcessor()
        self.svg_generator = svg_generator or SVGGenerator()
        self.svg_presenter = svg_presenter or SVGPresenter()
        
        # Use cases encapsulate business rules and workflow logic
        self.image_tracing_use_case = ImageTracingUseCase(
            contour_detector=self.contour_detector,
            color_analyzer=self.color_analyzer,
            point_detector=self.point_detector
        )
        
        self.structure_filtering_use_case = StructureFilteringUseCase(
            shape_processor=self.shape_processor
        )

    def trace_image(self, 
                   image_path: str, 
                   output_svg_path: str = "output.svg",
                   config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute complete bitmap-to-SVG tracing workflow.
        
        This is the main entry point for the tracing functionality.
        The method coordinates the entire pipeline while maintaining
        clean separation between concerns.
        
        Workflow Steps:
        1. Load configuration parameters
        2. Load and validate input image
        3. Detect and analyze contours with color categorization
        4. Filter structures based on configuration limits
        5. Generate SVG output from processed structures
        6. Present results to the user
        
        Args:
            image_path: Filesystem path to source bitmap image
            output_svg_path: Destination path for generated SVG file
            config_path: Optional path to YAML configuration file
            
        Returns:
            Dictionary containing:
            - success: Boolean indicating overall operation success
            - output_path: Path to generated SVG file (on success)
            - statistics: Counts of different structure types processed
            - metadata: Additional information about the operation
            - error: Description of failure (when success is False)
            
        Example:
            >>> controller = TracingController()
            >>> result = controller.trace_image("input.jpg", "output.svg")
            >>> if result['success']:
            ...     print(f"Generated {result['statistics']['total_structures']} structures")
        """
        try:
            print(f"⚡ Starting image tracing: {image_path}")
            
            # Step 1: Load configuration - business rules about structure limits
            config = self._load_configuration(config_path)
            if not config:
                return self._create_error_response("Failed to load configuration")
            
            # Step 2: Load image data - external interface concern
            image_data = self._load_image_data(image_path)
            if not image_data:
                return self._create_error_response(f"Could not load image: {image_path}")
            
            print(f"📐 Image size: {image_data['width']}x{image_data['height']}")
            
            # Step 3: Execute image tracing use case - core business logic
            tracing_result = self._execute_tracing_use_case(image_data, config)
            if not tracing_result.get('success', False):
                return self._create_error_response("Image tracing failed")
            
            # Step 4: Filter structures based on configuration limits
            filtered_structures = self._execute_filtering_use_case(tracing_result, config)
            
            # Step 5: Generate SVG output - external representation concern
            svg_result = self._generate_svg_output(filtered_structures, image_data, output_svg_path)
            if not svg_result.get('success', False):
                return self._create_error_response("SVG generation failed")
            
            # Step 6: Present results to user
            presentation_result = self._present_results(output_svg_path, tracing_result, filtered_structures)
            
            return self._create_success_response(output_svg_path, filtered_structures, config, image_data)
            
        except Exception as error:
            # All exceptions are caught and transformed for consistent error handling
            error_message = f"Unexpected error during tracing: {str(error)}"
            print(f"❌ {error_message}")
            return self._create_error_response(error_message)

    def trace_image_with_defaults(self, image_path: str) -> Dict[str, Any]:
        """
        Convenience method for tracing with default output path and configuration.
        
        This method provides a simplified interface for common use cases
        where default settings are acceptable.
        
        Args:
            image_path: Filesystem path to source bitmap image
            
        Returns:
            Same structure as trace_image() method
            
        Example:
            >>> controller = TracingController()
            >>> result = controller.trace_image_with_defaults("simple_shape.jpg")
        """
        output_path = os.path.splitext(image_path)[0] + ".svg"
        return self.trace_image(image_path, output_path)

    def get_tracing_status(self) -> Dict[str, Any]:
        """
        Provide system status and capability information.
        
        This method supports system monitoring and discovery by
        revealing what operations and formats are supported.
        
        Returns:
            Dictionary containing:
            - status: Current operational status
            - capabilities: Supported formats and features
            - dependencies: Status of required components
            
        Example:
            >>> status = controller.get_tracing_status()
            >>> if status['dependencies']['image_loader']:
            ...     print("Image loading is available")
        """
        return {
            'status': 'ready',
            'capabilities': {
                'image_formats': ['jpg', 'jpeg', 'png', 'bmp'],
                'output_format': 'svg',
                'color_categories': ['red', 'blue', 'green'],
                'structure_types': ['points', 'paths']
            },
            'dependencies': {
                'config_repository': self.config_repository is not None,
                'image_loader': self.image_loader is not None,
                'contour_detector': self.contour_detector is not None,
                'color_analyzer': self.color_analyzer is not None,
                'point_detector': self.point_detector is not None,
                'shape_processor': self.shape_processor is not None,
                'svg_generator': self.svg_generator is not None,
                'svg_presenter': self.svg_presenter is not None
            }
        }

    def _load_configuration(self, config_path: Optional[str]) -> Optional[Dict]:
        """Load configuration from repository."""
        return self.config_repository.load_config(config_path)

    def _load_image_data(self, image_path: str) -> Optional[Dict]:
        """Load and validate image data."""
        return self.image_loader.load_image(image_path)

    def _execute_tracing_use_case(self, image_data: Dict, config: Dict) -> Dict[str, Any]:
        """Execute the image tracing use case with provided data."""
        return self.image_tracing_use_case.execute(
            image_data=image_data,
            config=config
        )

    def _execute_filtering_use_case(self, tracing_result: Dict, config: Dict) -> Dict[str, Any]:
        """Execute structure filtering based on configuration limits."""
        return self.structure_filtering_use_case.execute(
            structures=tracing_result['structures'],
            config=config
        )

    def _generate_svg_output(self, structures: Dict, image_data: Dict, output_path: str) -> Dict[str, Any]:
        """Generate SVG file from processed structures."""
        return self.svg_generator.generate(
            structures=structures,
            width=image_data['width'],
            height=image_data['height'],
            output_path=output_path
        )

    def _present_results(self, svg_path: str, tracing_result: Dict, filtered_structures: Dict) -> Dict[str, Any]:
        """Present tracing results through the presenter."""
        return self.svg_presenter.present(
            svg_path=svg_path,
            tracing_metadata=tracing_result.get('metadata', {}),
            filtering_metadata=filtered_structures.get('metadata', {})
        )

    def _create_success_response(self, 
                               output_path: str, 
                               structures: Dict, 
                               config: Dict,
                               image_data: Dict) -> Dict[str, Any]:
        """
        Create standardized success response.
        
        This method ensures consistent response structure across all
        successful operations, making it easier for clients to parse results.
        """
        return {
            'success': True,
            'output_path': output_path,
            'statistics': {
                'red_points': len(structures.get('red_points', [])),
                'blue_paths': len(structures.get('blue_structures', [])),
                'green_paths': len(structures.get('green_structures', [])),
                'total_structures': (
                    len(structures.get('red_points', [])) +
                    len(structures.get('blue_structures', [])) +
                    len(structures.get('green_structures', []))
                )
            },
            'metadata': {
                'image_size': f"{image_data['width']}x{image_data['height']}",
                'config_limits': {
                    'red_dots': config.get('red_dots', 0),
                    'blue_paths': config.get('blue_paths', 0),
                    'green_paths': config.get('green_paths', 0)
                }
            }
        }

    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """
        Create standardized error response.
        
        All errors follow the same structure, making error handling
        predictable for clients. This follows the Consistent Error
        Handling principle.
        """
        return {
            'success': False,
            'error': error_message,
            'statistics': {
                'red_points': 0,
                'blue_paths': 0,
                'green_paths': 0,
                'total_structures': 0
            },
            'metadata': {}
        }