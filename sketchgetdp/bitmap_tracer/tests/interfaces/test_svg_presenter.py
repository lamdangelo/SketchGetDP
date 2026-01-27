import os
import sys
import pytest
import tempfile
from unittest.mock import Mock

# Required for importing project modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
sys.path.insert(0, project_root)

from interfaces.presenters.svg_presenter import SVGPresenter
from core.entities.point import Point
from core.entities.contour import Contour
from core.entities.color import ColorCategory


class TestSVGPresenter:
    """Validates SVG generation from geometric primitives."""
    
    @pytest.fixture
    def temp_output_path(self):
        """Isolates tests by using temporary files that auto-clean."""
        with tempfile.NamedTemporaryFile(suffix='.svg', delete=False) as f:
            temp_path = f.name
        yield temp_path
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    @pytest.fixture
    def sample_points(self):
        """Provides consistent test data across multiple tests."""
        return [Point(10, 20), Point(30, 40), Point(50, 60)]
    
    @pytest.fixture
    def sample_contour(self, sample_points):
        """Creates closed shape for testing path generation."""
        return Contour(points=sample_points, is_closed=True, closure_gap=0.0)
    
    @pytest.fixture
    def basic_presenter(self, temp_output_path):
        """Base presenter instance to avoid constructor duplication."""
        return SVGPresenter(temp_output_path, width=800, height=600)

    def test_initialization(self, temp_output_path):
        """Ensures presenter starts in clean state."""
        presenter = SVGPresenter(temp_output_path, width=800, height=600)
        
        assert presenter.output_path == temp_output_path
        assert presenter.width == 800
        assert presenter.height == 600
        assert presenter.elements_count['points'] == 0
    
    def test_add_point_red(self, basic_presenter):
        """Red points increment special counter for highlighting."""
        point = Point(100, 150)
        color = Mock()
        color.categorize.return_value = (ColorCategory.RED, "#FF0000")
        color.to_hex.return_value = "#FF0000"
        
        basic_presenter.add_point(point, color)
        
        assert basic_presenter.elements_count['red_points'] == 1
    
    def test_add_point_blue(self, basic_presenter):
        """Non-red points use standard counting."""
        point = Point(200, 250)
        color = Mock()
        color.categorize.return_value = (ColorCategory.BLUE, "#0000FF")
        color.to_hex.return_value = "#0000FF"
        
        basic_presenter.add_point(point, color)
        
        assert basic_presenter.elements_count['red_points'] == 0
    
    def test_add_path_blue(self, basic_presenter):
        """Color categorization drives both styling and statistics."""
        path_data = "M 10,20 L 30,40 L 50,60 Z"
        color = Mock()
        color.categorize.return_value = (ColorCategory.BLUE, "#0000FF")
        
        basic_presenter.add_path(path_data, color)
        
        assert basic_presenter.elements_count['blue_paths'] == 1
    
    def test_add_path_green(self, basic_presenter):
        """Separate counters allow color-specific analytics."""
        path_data = "M 10,20 L 30,40 L 50,60 Z"
        color = Mock()
        color.categorize.return_value = (ColorCategory.GREEN, "#00FF00")
        
        basic_presenter.add_path(path_data, color)
        
        assert basic_presenter.elements_count['green_paths'] == 1
    
    def test_add_contour_as_path(self, basic_presenter, sample_contour):
        """Contours become paths while preserving color semantics."""
        color = Mock()
        color.categorize.return_value = (ColorCategory.BLUE, "#0000FF")
        
        basic_presenter.add_contour_as_path(sample_contour, color)
        
        assert basic_presenter.elements_count['blue_paths'] == 1
    
    def test_add_empty_contour(self, basic_presenter):
        """Empty contours avoid generating invalid paths."""
        empty_contour = Contour(points=[], is_closed=False, closure_gap=0.0)
        color = Mock()
        color.categorize.return_value = (ColorCategory.BLUE, "#0000FF")
        
        basic_presenter.add_contour_as_path(empty_contour, color)
        
        assert basic_presenter.elements_count['paths'] == 0
    
    def test_convert_contour_to_path_data(self, basic_presenter, sample_contour):
        """Path data must match point sequence and closure flag."""
        path_data = basic_presenter._convert_contour_to_path_data(sample_contour)
        
        assert "M 10,20" in path_data
        assert "L 30,40" in path_data
        assert "Z" in path_data  # Closed contours get termination
    
    def test_save_svg(self, basic_presenter, temp_output_path):
        """File output must succeed and create valid SVG structure."""
        point = Point(100, 150)
        color = Mock()
        color.categorize.return_value = (ColorCategory.RED, "#FF0000")
        color.to_hex.return_value = "#FF0000"
        basic_presenter.add_point(point, color)
        
        result = basic_presenter.save()
        
        assert result is True
        assert os.path.exists(temp_output_path)

    def test_path_stroke_color_mapping(self, basic_presenter):
        """Categorized colors map to consistent stroke values."""
        blue_color = Mock()
        blue_color.categorize.return_value = (ColorCategory.BLUE, "#0000FF")
        
        stroke_color = basic_presenter._get_path_stroke_color(blue_color)
        
        assert stroke_color == "#0000FF"
    
    def test_path_counter_increment(self, basic_presenter):
        """Color-specific counting supports usage analytics."""
        blue_color = Mock()
        blue_color.categorize.return_value = (ColorCategory.BLUE, "#0000FF")
        
        basic_presenter._increment_path_counter(blue_color)
        
        assert basic_presenter.elements_count['blue_paths'] == 1
    
    def test_build_path_commands_closed(self, basic_presenter, sample_contour):
        """Closed contours must include termination command."""
        commands = basic_presenter._build_path_commands_from_contour(sample_contour)
        
        assert commands[-1] == "Z"
    
    def test_build_path_commands_open(self, basic_presenter):
        """Open contours omit termination for incomplete shapes."""
        points = [Point(10, 20), Point(30, 40)]
        contour = Contour(points=points, is_closed=False, closure_gap=0.0)
        
        commands = basic_presenter._build_path_commands_from_contour(contour)
        
        assert "Z" not in commands
    
    def test_contour_with_single_point(self, basic_presenter):
        """Single points create positioning-only paths."""
        single_point_contour = Contour(points=[Point(10, 20)], is_closed=False, closure_gap=0.0)
        
        path_data = basic_presenter._convert_contour_to_path_data(single_point_contour)
        
        assert path_data == "M 10,20"  # Move-to without drawing
    
    def test_contour_with_two_points(self, basic_presenter):
        """Two points form simple line segments."""
        two_point_contour = Contour(points=[Point(10, 20), Point(30, 40)], is_closed=False, closure_gap=0.0)
        
        path_data = basic_presenter._convert_contour_to_path_data(two_point_contour)
        
        assert path_data == "M 10,20 L 30,40"
    
    def test_empty_contour_path_data(self, basic_presenter):
        """Empty contours prevent invalid SVG generation."""
        empty_contour = Contour(points=[], is_closed=False, closure_gap=0.0)
        
        path_data = basic_presenter._convert_contour_to_path_data(empty_contour)
        
        assert path_data == ""
        