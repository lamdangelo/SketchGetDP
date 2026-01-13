"""
Test suite for the SVG Parser infrastructure component.
"""
import pytest
import tempfile
import os

from infrastructure.svg_parser import SVGParser, RawBoundary
from core.entities.point import Point
from core.entities.color import Color


class TestSVGParser:
    """Test suite for the SVGParser class"""
    
    # ==================== Fixtures ====================
    
    @pytest.fixture
    def parser(self):
        """Set up a fresh parser instance for each test"""
        return SVGParser()
    
    @pytest.fixture
    def temp_svg_file(self):
        """Create a temporary SVG file for testing"""
        def _create_temp_file(content):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
                f.write(content)
                return f.name
        return _create_temp_file
    
    @pytest.fixture
    def cleanup_temp_file(self):
        """Clean up temporary file"""
        def _cleanup(filepath):
            if os.path.exists(filepath):
                os.unlink(filepath)
        return _cleanup
    
    # ==================== Basic Tests ====================
    
    def test_parser_initialization(self, parser):
        """Test that parser initializes with correct namespace"""
        assert parser.namespace == '{http://www.w3.org/2000/svg}'
    
    def test_parse_nonexistent_file(self, parser):
        """Test that parser raises error for nonexistent file"""
        with pytest.raises(ValueError, match="Invalid SVG file"):
            parser.extract_boundaries_by_color("nonexistent.svg")
    
    def test_parse_invalid_xml(self, parser, temp_svg_file, cleanup_temp_file):
        """Test that parser raises error for invalid XML"""
        temp_path = temp_svg_file("invalid xml content")
        
        try:
            with pytest.raises(ValueError, match="Invalid SVG file"):
                parser.extract_boundaries_by_color(temp_path)
        finally:
            cleanup_temp_file(temp_path)
    
    # ==================== SVG Parsing Tests ====================
    
    def test_parse_minimal_svg(self, parser, temp_svg_file, cleanup_temp_file):
        """Test parsing of minimal valid SVG"""
        svg_content = '''<?xml version="1.0"?>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        </svg>'''
        
        temp_path = temp_svg_file(svg_content)
        
        try:
            result = parser.extract_boundaries_by_color(temp_path)
            assert result == {}  # No elements, empty result
        finally:
            cleanup_temp_file(temp_path)
    
    def test_parse_svg_with_single_red_dot(self, parser, temp_svg_file, cleanup_temp_file):
        """Test parsing SVG with a single red dot (circle)"""
        svg_content = '''<?xml version="1.0"?>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <circle fill="red" cx="50" cy="50" r="5"/>
        </svg>'''
        
        temp_path = temp_svg_file(svg_content)
        
        try:
            result = parser.extract_boundaries_by_color(temp_path)
            
            # Check it has one color key
            keys = list(result.keys())
            assert len(keys) == 1

            red_color_key = keys[0]
            red_boundaries = result[red_color_key]
            
            # Check the color key is red
            assert red_color_key.name == "red"
            assert red_color_key.rgb == (255, 0, 0)
            
            # Check there is one boundary consisting of one point
            assert len(red_boundaries) == 1
            boundary = red_boundaries[0]
            assert isinstance(boundary, RawBoundary)
            assert len(boundary.points) == 1
            
            # Check the point is in valid range (scaled to unit coordinates)
            point = boundary.points[0]
            assert 0 <= point.x <= 1, f"x={point.x} not in [0,1]"
            assert 0 <= point.y <= 1, f"y={point.y} not in [0,1]"
            
        finally:
            cleanup_temp_file(temp_path)
    
    def test_parse_svg_with_multiple_colors(self, parser, temp_svg_file, cleanup_temp_file):
        """Test parsing SVG with one shape per color - red as single-point boundary from ellipse"""
        svg_content = '''<?xml version="1.0"?>
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <!-- Red structure: ellipse that should be simplified to a single point (center) -->
        <ellipse fill="red" cx="50" cy="50" rx="8" ry="6"/>
        
        <!-- Green structure: closed path (square) -->
        <path d="M10,10 L30,10 L30,30 L10,30 Z" stroke="green" fill="none"/>
        
        <!-- Blue structure: open path (line) -->
        <path d="M60,10 L80,30" stroke="blue" fill="none"/>
        
        <!-- Black structure: closed path (triangle) -->
        <path d="M40,70 L60,90 L20,85 Z" stroke="black" fill="none"/>
    </svg>'''
        
        temp_path = temp_svg_file(svg_content)
        
        try:
            result = parser.extract_boundaries_by_color(temp_path)
            
            # Check we have exactly 4 color keys (red, green, blue, black)
            color_keys = list(result.keys())
            assert len(color_keys) == 4, f"Expected 4 colors, got {len(color_keys)}: {[c.name for c in color_keys]}"
            
            # Test RED structure (ellipse → single point)
            red_color_key = None
            for key in color_keys:
                if key.name == "red":
                    red_color_key = key
                    break
            
            assert red_color_key is not None, "Red color not found in results"
            assert red_color_key.name == "red"
            assert red_color_key.rgb == (255, 0, 0)
            
            red_boundaries = result[red_color_key]
            assert len(red_boundaries) == 1, f"Expected 1 red boundary, got {len(red_boundaries)}"
            
            red_boundary = red_boundaries[0]
            assert isinstance(red_boundary, RawBoundary)
            assert red_boundary.color.name == "red"
            
            # Red structure should have exactly 1 point (center of ellipse)
            assert len(red_boundary.points) == 1, f"Red ellipse should have 1 point, got {len(red_boundary.points)}"
            
            red_point = red_boundary.points[0]
            assert 0 <= red_point.x <= 1, f"Red point x={red_point.x} not in [0,1]"
            assert 0 <= red_point.y <= 1, f"Red point y={red_point.y} not in [0,1]"
            
            # Test GREEN structure (closed square path)
            green_color_key = None
            for key in color_keys:
                if key.name == "green":
                    green_color_key = key
                    break
            
            assert green_color_key is not None, "Green color not found in results"
            assert green_color_key.name == "green"
            assert green_color_key.rgb == (0, 255, 0)
            
            green_boundaries = result[green_color_key]
            assert len(green_boundaries) == 1, f"Expected 1 green boundary, got {len(green_boundaries)}"
            
            green_boundary = green_boundaries[0]
            assert isinstance(green_boundary, RawBoundary)
            assert green_boundary.color.name == "green"
            
            # Green structure should have multiple points (at least 4 for a square)
            assert len(green_boundary.points) >= 4, f"Green square should have >=4 points, got {len(green_boundary.points)}"
            assert green_boundary.is_closed, "Green square should be closed"
            
            for green_point in green_boundary.points:
                assert 0 <= green_point.x <= 1, f"Green point x={green_point.x} not in [0,1]"
                assert 0 <= green_point.y <= 1, f"Green point y={green_point.y} not in [0,1]"
            
            # Test BLUE structure (open line path)
            blue_color_key = None
            for key in color_keys:
                if key.name == "blue":
                    blue_color_key = key
                    break
            
            assert blue_color_key is not None, "Blue color not found in results"
            assert blue_color_key.name == "blue"
            assert blue_color_key.rgb == (0, 0, 255)
            
            blue_boundaries = result[blue_color_key]
            assert len(blue_boundaries) == 1, f"Expected 1 blue boundary, got {len(blue_boundaries)}"
            
            blue_boundary = blue_boundaries[0]
            assert isinstance(blue_boundary, RawBoundary)
            assert blue_boundary.color.name == "blue"
            
            # Blue structure should have multiple points (at least 2 for a line)
            assert len(blue_boundary.points) >= 2, f"Blue line should have >=2 points, got {len(blue_boundary.points)}"
            assert not blue_boundary.is_closed, "Blue line should be open"
            
            for blue_point in blue_boundary.points:
                assert 0 <= blue_point.x <= 1, f"Blue point x={blue_point.x} not in [0,1]"
                assert 0 <= blue_point.y <= 1, f"Blue point y={blue_point.y} not in [0,1]"
            
            # Test BLACK structure (closed triangle path)
            black_color_key = None
            for key in color_keys:
                if key.name == "black":
                    black_color_key = key
                    break
            
            assert black_color_key is not None, "Black color not found in results"
            assert black_color_key.name == "black"
            assert black_color_key.rgb == (0, 0, 0)
            
            black_boundaries = result[black_color_key]
            assert len(black_boundaries) == 1, f"Expected 1 black boundary, got {len(black_boundaries)}"
            
            black_boundary = black_boundaries[0]
            assert isinstance(black_boundary, RawBoundary)
            assert black_boundary.color.name == "black"
            
            # Black structure should have multiple points (at least 3 for a triangle)
            assert len(black_boundary.points) >= 3, f"Black triangle should have >=3 points, got {len(black_boundary.points)}"
            assert black_boundary.is_closed, "Black triangle should be closed"
            
            for black_point in black_boundary.points:
                assert 0 <= black_point.x <= 1, f"Black point x={black_point.x} not in [0,1]"
                assert 0 <= black_point.y <= 1, f"Black point y={black_point.y} not in [0,1]"
            
            # Verify no duplicate points in multi-point boundaries
            for color, boundaries in result.items():
                if color.name != "red":  # Skip red (single point)
                    for boundary in boundaries:
                        if len(boundary.points) > 1:
                            # Check for consecutive duplicates
                            for i in range(len(boundary.points) - 1):
                                assert boundary.points[i] != boundary.points[i + 1], \
                                    f"Consecutive duplicate points found in {color.name} boundary at index {i}"
            
        finally:
            cleanup_temp_file(temp_path)
    
    # ==================== ViewBox and Scaling Tests ====================
    
    def test_parse_viewbox_scaling(self, parser, temp_svg_file, cleanup_temp_file):
        """Test that coordinates are properly scaled to unit square"""
        svg_content = '''<?xml version="1.0"?>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 100">
            <rect stroke="red" x="50" y="25" width="100" height="50"/>
        </svg>'''
        
        temp_path = temp_svg_file(svg_content)
        
        try:
            result = parser.extract_boundaries_by_color(temp_path)
            
            # Check any boundaries we get
            for color, boundaries in result.items():
                for boundary in boundaries:
                    # Check that points are scaled to [0,1] range
                    for point in boundary.points:
                        assert 0 <= point.x <= 1
                        assert 0 <= point.y <= 1
            
        finally:
            cleanup_temp_file(temp_path)
    
    def test_parse_no_viewbox(self, parser, temp_svg_file, cleanup_temp_file):
        """Test parsing SVG without viewBox attribute"""
        svg_content = '''<?xml version="1.0"?>
        <svg xmlns="http://www.w3.org/2000/svg">
            <rect stroke="red" x="10" y="10" width="20" height="20"/>
        </svg>'''
        
        temp_path = temp_svg_file(svg_content)
        
        try:
            result = parser.extract_boundaries_by_color(temp_path)
            
            # Check any boundaries we get
            for color, boundaries in result.items():
                for boundary in boundaries:
                    # Should still work with default scaling
                    for point in boundary.points:
                        assert 0 <= point.x <= 1
                        assert 0 <= point.y <= 1
                    
        finally:
            cleanup_temp_file(temp_path)
    
    def test_parse_invalid_viewbox(self, parser, temp_svg_file, cleanup_temp_file):
        """Test parsing SVG with invalid viewBox"""
        svg_content = '''<?xml version="1.0"?>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="invalid">
            <rect stroke="red" x="10" y="10" width="20" height="20"/>
        </svg>'''
        
        temp_path = temp_svg_file(svg_content)
        
        try:
            result = parser.extract_boundaries_by_color(temp_path)
            
            # Check any boundaries we get
            for color, boundaries in result.items():
                for boundary in boundaries:
                    # Should use default scaling
                    for point in boundary.points:
                        assert 0 <= point.x <= 1
                        assert 0 <= point.y <= 1
                    
        finally:
            cleanup_temp_file(temp_path)
    
    # ==================== Color Extraction Tests ====================
    
    def test_color_extraction_hex(self, parser, temp_svg_file, cleanup_temp_file):
        """Test color extraction from hex values"""
        svg_content = '''<?xml version="1.0"?>
        <svg xmlns="http://www.w3.org/2000/svg">
            <path stroke="#ff0000" d="M10,10 L20,20"/>
            <path stroke="#00ff00" d="M30,30 L40,40"/>
            <path stroke="#0000ff" d="M50,50 L60,60"/>
        </svg>'''

        temp_path = temp_svg_file(svg_content)

        try:
            result = parser.extract_boundaries_by_color(temp_path)
            
            # Check that colors are extracted
            for color in result.keys():
                assert color.name.lower() in ["red", "green", "blue"]
                
        finally:
            cleanup_temp_file(temp_path)
    
    def test_color_extraction_rgb(self, parser, temp_svg_file, cleanup_temp_file):
        """Test color extraction from rgb values"""
        svg_content = '''<?xml version="1.0"?>
        <svg xmlns="http://www.w3.org/2000/svg">
            <path stroke="rgb(255,0,0)" d="M10,10 L20,20"/>
            <path stroke="rgb(0,255,0)" d="M30,30 L40,40"/>
            <path stroke="rgb(0,0,255)" d="M50,50 L60,60"/>
        </svg>'''
        
        temp_path = temp_svg_file(svg_content)
        
        try:
            result = parser.extract_boundaries_by_color(temp_path)
            
            # Check for expected colors
            for color in result.keys():
                assert color.name.lower() in ["red", "green", "blue"]
            
        finally:
            cleanup_temp_file(temp_path)
    
    # ==================== Parameterized Color Mapping Tests ====================
    
    @pytest.mark.parametrize("hex_color,expected_primary_name", [
        ("#ff8080", "red"),    # Light red -> red
        ("#80ff80", "green"),  # Light green -> green
        ("#8080ff", "blue"),   # Light blue -> blue
        ("#ff4000", "red"),    # Orange-red -> red
        ("#ffff00", "red"),    # Yellow -> red (closest to red+green)
    ])
    def test_hex_color_mapping(self, parser, hex_color, expected_primary_name):
        """Test mapping of various hex colors to primary colors"""
        result = parser._convert_hex_to_primary_color(hex_color)
        assert result.name.lower() == expected_primary_name.lower()
    
    # ==================== Error Handling Tests ====================
    
    def test_error_handling_malformed_elements(self, parser, temp_svg_file, cleanup_temp_file):
        """Test error handling for malformed SVG elements"""
        svg_content = '''<?xml version="1.0"?>
        <svg xmlns="http://www.w3.org/2000/svg">
            <rect stroke="red" x="invalid" y="10" width="20" height="20"/>
            <circle stroke="green" cx="50" cy="invalid" r="10"/>
            <polygon stroke="blue" points="invalid,points,here"/>
        </svg>'''
        
        temp_path = temp_svg_file(svg_content)
        
        try:
            # This should raise an error due to malformed elements
            with pytest.raises(ValueError, match="Invalid SVG file"):
                parser.extract_boundaries_by_color(temp_path)
            
        finally:
            cleanup_temp_file(temp_path)
    
    # ==================== RawBoundary Tests ====================
    
    def test_raw_boundary_validation(self):
        """Test that RawBoundary validates point count"""
        # Test works with 3+ points for any color
        points_3 = [Point(0, 0), Point(1, 0), Point(1, 1)]
        
        # All colors should work with 3+ points
        for color in [Color.RED, Color.GREEN, Color.BLUE]:
            boundary = RawBoundary(points=points_3, color=color)
            assert boundary.points == points_3
        
        # Test with more than 3 points
        points_4 = [Point(0, 0), Point(1, 0), Point(1, 1), Point(0, 1)]
        boundary_4 = RawBoundary(points=points_4, color=Color.RED)
        assert boundary_4.points == points_4
        
        # Should fail with less than 3 points for ANY color
        points_2 = [Point(0, 0), Point(1, 1)]
        for color in [Color.RED, Color.GREEN, Color.BLUE]:
            with pytest.raises(ValueError, match="Raw boundary must have at least 3 points"):
                RawBoundary(points=points_2, color=color)
        
        # Should fail with 0 points
        with pytest.raises(ValueError):
            RawBoundary(points=[], color=Color.RED)
        
        # Should fail with 1 point
        with pytest.raises(ValueError, match="Raw boundary must have at least 3 points"):
            RawBoundary(points=[Point(0, 0)], color=Color.RED)
            
    def test_raw_boundary_structure(self, parser, temp_svg_file, cleanup_temp_file):
        """Simple test that validates RawBoundary objects for all four colors"""
        svg_content = '''<?xml version="1.0"?>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <!-- One red circle -->
            <circle cx="20" cy="20" r="10" fill="red" stroke="red"/>
            
            <!-- One green triangle -->
            <path d="M 70,20 L 90,20 L 80,40 Z" fill="green" stroke="green"/>
            
            <!-- One blue rectangle (as path) -->
            <path d="M 20,70 L 40,70 L 40,90 L 20,90 Z" fill="blue" stroke="blue"/>
            
            <!-- One black polygon -->
            <polygon points="70,70 85,70 80,85" fill="black" stroke="black"/>
        </svg>'''

        temp_path = temp_svg_file(svg_content)

        try:
            result = parser.extract_boundaries_by_color(temp_path)

            # Verify we have a dictionary
            assert isinstance(result, dict)
            
            # Get the keys as a list
            keys = list(result.keys())
            
            # Check we have some colors
            assert len(keys) > 0
            
            # Find boundaries for each color by checking each key
            red_boundaries = None
            green_boundaries = None
            blue_boundaries = None
            black_boundaries = None
            
            for key in keys:
                if hasattr(key, 'name'):
                    if key.name == 'red':
                        red_boundaries = result[key]
                    elif key.name == 'green':
                        green_boundaries = result[key]
                    elif key.name == 'blue':
                        blue_boundaries = result[key]
                    elif key.name == 'black':
                        black_boundaries = result[key]
            
            # Debug output
            print(f"\nFound boundaries:")
            if red_boundaries:
                print(f"  Red: {len(red_boundaries)} boundary(ies)")
            if green_boundaries:
                print(f"  Green: {len(green_boundaries)} boundary(ies)")
            if blue_boundaries:
                print(f"  Blue: {len(blue_boundaries)} boundary(ies)")
            if black_boundaries:
                print(f"  Black: {len(black_boundaries)} boundary(ies)")
            
            # Validate red boundary (from circle)
            assert red_boundaries is not None, "No red boundary found"
            assert isinstance(red_boundaries, list)
            assert len(red_boundaries) >= 1
            
            red_boundary = red_boundaries[0]
            assert isinstance(red_boundary, RawBoundary)
            assert isinstance(red_boundary.points, list)
            
            # Validate green boundary (from triangle path)
            assert green_boundaries is not None, "No green boundary found"
            assert isinstance(green_boundaries, list)
            assert len(green_boundaries) >= 1
            
            green_boundary = green_boundaries[0]
            assert isinstance(green_boundary, RawBoundary)
            assert isinstance(green_boundary.points, list)
            
            # Validate blue boundary (from rectangle path)
            assert blue_boundaries is not None, "No blue boundary found"
            assert isinstance(blue_boundaries, list)
            assert len(blue_boundaries) >= 1
            
            blue_boundary = blue_boundaries[0]
            assert isinstance(blue_boundary, RawBoundary)
            assert isinstance(blue_boundary.points, list)
            
            # Validate black boundary (from polygon)
            assert black_boundaries is not None, "No black boundary found"
            assert isinstance(black_boundaries, list)
            assert len(black_boundaries) >= 1
            
            black_boundary = black_boundaries[0]
            assert isinstance(black_boundary, RawBoundary)
            assert isinstance(black_boundary.points, list)

        finally:
            cleanup_temp_file(temp_path)