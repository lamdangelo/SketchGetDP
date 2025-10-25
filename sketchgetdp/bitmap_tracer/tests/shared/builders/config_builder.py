"""
Constructs test configuration objects that faithfully replicate the production config.yaml structure.
Enables isolated testing of configuration-dependent components without file system dependencies.
"""

from typing import Dict, Any, List, Optional, Union


class StructureLimitsConfig:
    """Controls structure preservation limits during filtering."""

    def __init__(self) -> None:
        self.red_dots: int = 10
        self.blue_paths: int = 5
        self.green_paths: int = 5


class ContourDetectionConfig:
    """Defines geometric constraints for valid contour identification."""

    def __init__(self) -> None:
        self.min_area: int = 150
        self.max_area_ratio: float = 0.8
        self.point_max_area: int = 100
        self.point_max_perimeter: int = 80
        self.closure_tolerance: float = 5.0
        self.circularity_threshold: float = 0.01


class CurveFittingConfig:
    """Governs pixel contour to smooth vector path conversion."""

    def __init__(self) -> None:
        self.angle_threshold: int = 25
        self.min_curve_angle: int = 120
        self.epsilon_factor: float = 0.0015
        self.closure_threshold: float = 10.0


class ColorDetectionConfig:
    """Specifies HSV ranges and thresholds for color categorization."""

    def __init__(self) -> None:
        self.blue_hue_range: List[int] = [100, 140]
        self.red_hue_range: List[List[int]] = [[0, 10], [170, 180]]
        self.green_hue_range: List[int] = [35, 85]
        self.color_difference_threshold: int = 20
        self.min_saturation: int = 50
        self.max_value_white: int = 200
        self.min_value_black: int = 50


class SVGGenerationConfig:
    """Determines final SVG output visual styling."""

    def __init__(self) -> None:
        self.point_radius: int = 4
        self.stroke_width: int = 2
        self.blue_color: str = "#0000FF"
        self.red_color: str = "#FF0000"
        self.green_color: str = "#00FF00"


class TracingConfig:
    """Aggregates all configuration domains into complete tracing specification."""

    def __init__(self) -> None:
        self.structure_limits: StructureLimitsConfig = StructureLimitsConfig()
        self.contour_detection: ContourDetectionConfig = ContourDetectionConfig()
        self.curve_fitting: CurveFittingConfig = CurveFittingConfig()
        self.color_detection: ColorDetectionConfig = ColorDetectionConfig()
        self.svg_generation: SVGGenerationConfig = SVGGenerationConfig()


class ConfigBuilder:
    """
    Fluent interface for constructing test configurations.
    
    Encapsulates configuration object creation complexity while exposing
    simple, readable API for test setup. Each method modifies one coherent
    configuration aspect, allowing tests to express exact needs without
    construction detail coupling.
    """

    def __init__(self) -> None:
        self._reset_builder_state()

    def _reset_builder_state(self) -> None:
        """Restores all configuration components to default values."""
        self._structure_limits = StructureLimitsConfig()
        self._contour_detection = ContourDetectionConfig()
        self._curve_fitting = CurveFittingConfig()
        self._color_detection = ColorDetectionConfig()
        self._svg_generation = SVGGenerationConfig()

    def with_structure_limits(
        self,
        red_dots: Optional[int] = None,
        blue_paths: Optional[int] = None,
        green_paths: Optional[int] = None
    ) -> 'ConfigBuilder':
        """Sets maximum structure counts for each color category."""
        if red_dots is not None:
            self._structure_limits.red_dots = red_dots
        if blue_paths is not None:
            self._structure_limits.blue_paths = blue_paths
        if green_paths is not None:
            self._structure_limits.green_paths = green_paths
        return self

    def with_contour_detection(
        self,
        min_area: Optional[int] = None,
        max_area_ratio: Optional[float] = None,
        point_max_area: Optional[int] = None,
        point_max_perimeter: Optional[int] = None,
        closure_tolerance: Optional[float] = None,
        circularity_threshold: Optional[float] = None
    ) -> 'ConfigBuilder':
        """Adjusts geometric criteria for contour detection."""
        if min_area is not None:
            self._contour_detection.min_area = min_area
        if max_area_ratio is not None:
            self._contour_detection.max_area_ratio = max_area_ratio
        if point_max_area is not None:
            self._contour_detection.point_max_area = point_max_area
        if point_max_perimeter is not None:
            self._contour_detection.point_max_perimeter = point_max_perimeter
        if closure_tolerance is not None:
            self._contour_detection.closure_tolerance = closure_tolerance
        if circularity_threshold is not None:
            self._contour_detection.circularity_threshold = circularity_threshold
        return self

    def with_curve_fitting(
        self,
        angle_threshold: Optional[int] = None,
        min_curve_angle: Optional[int] = None,
        epsilon_factor: Optional[float] = None,
        closure_threshold: Optional[float] = None
    ) -> 'ConfigBuilder':
        """Modifies path simplification and curve detection parameters."""
        if angle_threshold is not None:
            self._curve_fitting.angle_threshold = angle_threshold
        if min_curve_angle is not None:
            self._curve_fitting.min_curve_angle = min_curve_angle
        if epsilon_factor is not None:
            self._curve_fitting.epsilon_factor = epsilon_factor
        if closure_threshold is not None:
            self._curve_fitting.closure_threshold = closure_threshold
        return self

    def with_color_detection(
        self,
        blue_hue_range: Optional[List[int]] = None,
        red_hue_range: Optional[List[List[int]]] = None,
        green_hue_range: Optional[List[int]] = None,
        color_difference_threshold: Optional[int] = None,
        min_saturation: Optional[int] = None,
        max_value_white: Optional[int] = None,
        min_value_black: Optional[int] = None
    ) -> 'ConfigBuilder':
        """Updates color detection thresholds and HSV ranges."""
        if blue_hue_range is not None:
            self._color_detection.blue_hue_range = blue_hue_range
        if red_hue_range is not None:
            self._color_detection.red_hue_range = red_hue_range
        if green_hue_range is not None:
            self._color_detection.green_hue_range = green_hue_range
        if color_difference_threshold is not None:
            self._color_detection.color_difference_threshold = color_difference_threshold
        if min_saturation is not None:
            self._color_detection.min_saturation = min_saturation
        if max_value_white is not None:
            self._color_detection.max_value_white = max_value_white
        if min_value_black is not None:
            self._color_detection.min_value_black = min_value_black
        return self

    def with_svg_generation(
        self,
        point_radius: Optional[int] = None,
        stroke_width: Optional[int] = None,
        blue_color: Optional[str] = None,
        red_color: Optional[str] = None,
        green_color: Optional[str] = None
    ) -> 'ConfigBuilder':
        """Customizes SVG output element visual appearance."""
        if point_radius is not None:
            self._svg_generation.point_radius = point_radius
        if stroke_width is not None:
            self._svg_generation.stroke_width = stroke_width
        if blue_color is not None:
            self._svg_generation.blue_color = blue_color
        if red_color is not None:
            self._svg_generation.red_color = red_color
        if green_color is not None:
            self._svg_generation.green_color = green_color
        return self

    def build(self) -> TracingConfig:
        """Assembles final configuration object from configured components."""
        final_config = TracingConfig()
        
        final_config.structure_limits = self._structure_limits
        final_config.contour_detection = self._contour_detection
        final_config.curve_fitting = self._curve_fitting
        final_config.color_detection = self._color_detection
        final_config.svg_generation = self._svg_generation
        
        return final_config

    def build_dict(self) -> Dict[str, Any]:
        """Produces dictionary representation matching YAML file structure."""
        config = self.build()
        return {
            'red_dots': config.structure_limits.red_dots,
            'blue_paths': config.structure_limits.blue_paths,
            'green_paths': config.structure_limits.green_paths,
            'min_area': config.contour_detection.min_area,
            'max_area_ratio': config.contour_detection.max_area_ratio,
            'point_max_area': config.contour_detection.point_max_area,
            'point_max_perimeter': config.contour_detection.point_max_perimeter,
            'closure_tolerance': config.contour_detection.closure_tolerance,
            'circularity_threshold': config.contour_detection.circularity_threshold,
            'angle_threshold': config.curve_fitting.angle_threshold,
            'min_curve_angle': config.curve_fitting.min_curve_angle,
            'epsilon_factor': config.curve_fitting.epsilon_factor,
            'closure_threshold': config.curve_fitting.closure_threshold,
            'blue_hue_range': config.color_detection.blue_hue_range,
            'red_hue_range': config.color_detection.red_hue_range,
            'green_hue_range': config.color_detection.green_hue_range,
            'color_difference_threshold': config.color_detection.color_difference_threshold,
            'min_saturation': config.color_detection.min_saturation,
            'max_value_white': config.color_detection.max_value_white,
            'min_value_black': config.color_detection.min_value_black,
            'point_radius': config.svg_generation.point_radius,
            'stroke_width': config.svg_generation.stroke_width,
            'blue_color': config.svg_generation.blue_color,
            'red_color': config.svg_generation.red_color,
            'green_color': config.svg_generation.green_color
        }


def create_default_config() -> TracingConfig:
    """Provides standard configuration used in production environments."""
    return ConfigBuilder().build()


def create_minimal_config() -> TracingConfig:
    """Creates configuration minimizing processing for fast test execution."""
    return (ConfigBuilder()
            .with_structure_limits(red_dots=2, blue_paths=1, green_paths=1)
            .with_contour_detection(min_area=300, max_area_ratio=0.5)
            .with_curve_fitting(epsilon_factor=0.01)
            .build())


def create_sensitive_config() -> TracingConfig:
    """Optimizes configuration for detecting small, subtle features."""
    return (ConfigBuilder()
            .with_contour_detection(
                min_area=50,
                point_max_area=50,
                closure_tolerance=2.0,
                circularity_threshold=0.005
            )
            .with_color_detection(
                color_difference_threshold=10,
                min_saturation=30
            )
            .build())


def create_strict_config() -> TracingConfig:
    """Applies strict filtering for high-quality, well-defined output."""
    return (ConfigBuilder()
            .with_structure_limits(red_dots=5, blue_paths=3, green_paths=3)
            .with_contour_detection(
                min_area=200,
                circularity_threshold=0.02,
                max_area_ratio=0.6
            )
            .with_curve_fitting(
                angle_threshold=15,
                min_curve_angle=135,
                epsilon_factor=0.0005
            )
            .build())