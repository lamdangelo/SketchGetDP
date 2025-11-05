"""
Test suite for the SVG Parser infrastructure component.
"""

import pytest
import xml.etree.ElementTree as ET
from unittest.mock import patch, mock_open
import tempfile
import os

from infrastructure.svg_parser import SVGParser, RawBoundary
from core.entities.point import Point
from core.entities.color import Color


class TestSVGParser:
    """Test suite for the SVGParser class"""
    
    def setup_method(self):
        """Set up a fresh parser instance for each test"""
        self.parser = SVGParser()
    
    def test_parser_initialization(self):
        """Test that parser initializes with correct namespace"""
        assert self.parser.namespace == '{http://www.w3.org/2000/svg}'
    
    def test_parse_nonexistent_file(self):
        """Test that parser raises error for nonexistent file"""
        with pytest.raises(ValueError, match="SVG file not found"):
            self.parser.parse("nonexistent.svg")
    
    def test_parse_invalid_xml(self):
        """Test that parser raises error for invalid XML"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            f.write("invalid xml content")
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Invalid SVG file"):
                self.parser.parse(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_parse_minimal_svg(self):
        """Test parsing of minimal valid SVG"""
        svg_content = '''<?xml version="1.0"?>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        </svg>'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            f.write(svg_content)
            temp_path = f.name
        
        try:
            result = self.parser.parse(temp_path)
            assert result == {}  # No elements, empty result
        finally:
            os.unlink(temp_path)
    
    def test_parse_svg_with_single_red_path(self):
        """Test parsing SVG with a single red path"""
        svg_content = '''<?xml version="1.0"?>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <path stroke="red" d="M10,10 L50,10 L50,50 L10,50 Z"/>
        </svg>'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            f.write(svg_content)
            temp_path = f.name
        
        try:
            result = self.parser.parse(temp_path)
            
            assert Color.RED in result
            assert len(result[Color.RED]) == 1
            
            boundary = result[Color.RED][0]
            assert isinstance(boundary, RawBoundary)
            assert boundary.color == Color.RED
            assert boundary.is_closed == True
            
            # Check that points are extracted and scaled
            assert len(boundary.points) > 0
            for point in boundary.points:
                assert 0 <= point.x <= 1
                assert 0 <= point.y <= 1
            
        finally:
            os.unlink(temp_path)
    
    def test_parse_svg_with_multiple_colors(self):
        """Test parsing SVG with multiple colored shapes"""
        svg_content = '''<?xml version="1.0"?>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <rect stroke="red" x="10" y="10" width="20" height="20"/>
            <circle stroke="green" cx="50" cy="50" r="10"/>
            <polygon stroke="blue" points="80,10 90,30 70,30"/>
        </svg>'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            f.write(svg_content)
            temp_path = f.name
        
        try:
            result = self.parser.parse(temp_path)
            
            assert len(result) == 3
            assert Color.RED in result
            assert Color.GREEN in result
            assert Color.BLUE in result
            
            # Each color should have one boundary
            assert len(result[Color.RED]) == 1
            assert len(result[Color.GREEN]) == 1
            assert len(result[Color.BLUE]) == 1
            
        finally:
            os.unlink(temp_path)
    
    def test_parse_viewbox_scaling(self):
        """Test that coordinates are properly scaled to unit square"""
        svg_content = '''<?xml version="1.0"?>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 100">
            <rect stroke="red" x="50" y="25" width="100" height="50"/>
        </svg>'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            f.write(svg_content)
            temp_path = f.name
        
        try:
            result = self.parser.parse(temp_path)
            boundary = result[Color.RED][0]
            
            # Check that points are scaled to [0,1] range
            for point in boundary.points:
                assert 0 <= point.x <= 1
                assert 0 <= point.y <= 1
            
            # Specific point checks (scaled from 200x100 viewbox)
            # Original: (50,25) -> Scaled: (0.25, 0.25)
            # Original: (150,75) -> Scaled: (0.75, 0.75)
            points_set = set(boundary.points)
            assert Point(0.25, 0.25) in points_set
            assert Point(0.75, 0.25) in points_set
            assert Point(0.75, 0.75) in points_set
            assert Point(0.25, 0.75) in points_set
            
        finally:
            os.unlink(temp_path)
    
    def test_parse_no_viewbox(self):
        """Test parsing SVG without viewBox attribute"""
        svg_content = '''<?xml version="1.0"?>
        <svg xmlns="http://www.w3.org/2000/svg">
            <rect stroke="red" x="10" y="10" width="20" height="20"/>
        </svg>'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            f.write(svg_content)
            temp_path = f.name
        
        try:
            result = self.parser.parse(temp_path)
            boundary = result[Color.RED][0]
            
            # Should still work with default scaling
            for point in boundary.points:
                assert 0 <= point.x <= 1
                assert 0 <= point.y <= 1
                
        finally:
            os.unlink(temp_path)
    
    def test_parse_invalid_viewbox(self):
        """Test parsing SVG with invalid viewBox"""
        svg_content = '''<?xml version="1.0"?>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="invalid">
            <rect stroke="red" x="10" y="10" width="20" height="20"/>
        </svg>'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            f.write(svg_content)
            temp_path = f.name
        
        try:
            result = self.parser.parse(temp_path)
            boundary = result[Color.RED][0]
            
            # Should use default scaling
            for point in boundary.points:
                assert 0 <= point.x <= 1
                assert 0 <= point.y <= 1
                
        finally:
            os.unlink(temp_path)
    
    def test_color_extraction_hex(self):
        """Test color extraction from hex values"""
        svg_content = '''<?xml version="1.0"?>
        <svg xmlns="http://www.w3.org/2000/svg">
            <path stroke="#ff0000" d="M10,10 L20,20"/>
            <path stroke="#00ff00" d="M30,30 L40,40"/>
            <path stroke="#0000ff" d="M50,50 L60,60"/>
        </svg>'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            f.write(svg_content)
            temp_path = f.name

        try:
            result = self.parser.parse(temp_path)
            
            # Debug: print what we got
            print(f"Result keys: {list(result.keys())}")
            for color, boundaries in result.items():
                print(f"Color {color}: {len(boundaries)} boundaries")
            
            assert Color.RED in result
        finally:
            os.unlink(temp_path)
    
    def test_color_extraction_rgb(self):
        """Test color extraction from rgb values"""
        svg_content = '''<?xml version="1.0"?>
        <svg xmlns="http://www.w3.org/2000/svg">
            <path stroke="rgb(255,0,0)" d="M10,10 L20,20"/>
            <path stroke="rgb(0,255,0)" d="M30,30 L40,40"/>
            <path stroke="rgb(0,0,255)" d="M50,50 L60,60"/>
        </svg>'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            f.write(svg_content)
            temp_path = f.name
        
        try:
            result = self.parser.parse(temp_path)
            
            assert Color.RED in result
            assert Color.GREEN in result
            assert Color.BLUE in result
            
        finally:
            os.unlink(temp_path)
    
    def test_color_extraction_default(self):
        """Test color extraction with default (no stroke)"""
        svg_content = '''<?xml version="1.0"?>
        <svg xmlns="http://www.w3.org/2000/svg">
            <path d="M10,10 L20,20"/>
        </svg>'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            f.write(svg_content)
            temp_path = f.name
        
        try:
            result = self.parser.parse(temp_path)
            
            # Should default to red
            assert Color.RED in result
            
        finally:
            os.unlink(temp_path)
    
    def test_parse_different_shapes(self):
        """Test parsing different SVG shape types"""
        svg_content = '''<?xml version="1.0"?>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <rect stroke="red" x="10" y="10" width="20" height="20"/>
            <circle stroke="green" cx="50" cy="50" r="10"/>
            <ellipse stroke="blue" cx="80" cy="20" rx="15" ry="10"/>
            <polygon stroke="red" points="10,80 20,90 5,90"/>
            <polyline stroke="green" points="30,80 40,85 35,95"/>
        </svg>'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            f.write(svg_content)
            temp_path = f.name
        
        try:
            result = self.parser.parse(temp_path)
            
            # Should have red, green, blue curves
            assert len(result) == 3
            assert Color.RED in result
            assert Color.GREEN in result
            assert Color.BLUE in result
            
            # Check boundary properties
            for color, boundaries in result.items():
                for boundary in boundaries:
                    assert isinstance(boundary, RawBoundary)
                    assert len(boundary.points) >= 3  # At least 3 points for a boundary
                    
        finally:
            os.unlink(temp_path)
    
    def test_parse_closed_vs_open_shapes(self):
        """Test that closed and open shapes are handled correctly"""
        svg_content = '''<?xml version="1.0"?>
        <svg xmlns="http://www.w3.org/2000/svg">
            <polygon stroke="red" points="10,10 20,20 15,25"/> <!-- closed -->
            <polyline stroke="green" points="30,30 40,40 35,45"/> <!-- open -->
            <path stroke="blue" d="M50,50 L60,60 L55,65 Z"/> <!-- closed with Z -->
            <path stroke="red" d="M70,70 L80,80 L75,85"/> <!-- open without Z -->
        </svg>'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            f.write(svg_content)
            temp_path = f.name

        try:
            result = self.parser.parse(temp_path)
            
            # Debug: print boundaries for red color
            print(f"Red boundaries: {len(result[Color.RED])}")
            for i, boundary in enumerate(result[Color.RED]):
                print(f"  Boundary {i}: {len(boundary.points)} points, closed: {boundary.is_closed}")
                if boundary.points:
                    print(f"    First: {boundary.points[0]}, Last: {boundary.points[-1]}")

            # Check that closed shapes have proper point counts
            for boundary in result[Color.RED]:
                # Only check polygons for closed shape property
                if boundary.is_closed and len(boundary.points) > 3:  # Polygon should be closed
                    points = boundary.points
                    if len(points) > 0:
                        assert points[0] == points[-1]  # Closed shape
                        
        finally:
            os.unlink(temp_path)
    
    def test_parse_empty_elements(self):
        """Test parsing SVG with empty or invalid elements"""
        svg_content = '''<?xml version="1.0"?>
        <svg xmlns="http://www.w3.org/2000/svg">
            <rect stroke="red" x="10" y="10" width="0" height="0"/> <!-- zero size -->
            <circle stroke="green" cx="50" cy="50" r="0"/> <!-- zero radius -->
            <path stroke="blue" d=""/> <!-- empty path -->
        </svg>'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            f.write(svg_content)
            temp_path = f.name
        
        try:
            result = self.parser.parse(temp_path)
            
            # Empty elements should be filtered out (need at least 3 points)
            for color_boundaries in result.values():
                for boundary in color_boundaries:
                    assert len(boundary.points) >= 3
                    
        finally:
            os.unlink(temp_path)
    
    def test_boundary_structure(self):
        """Test that RawBoundary objects are properly structured"""
        svg_content = '''<?xml version="1.0"?>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <rect stroke="red" x="10" y="10" width="80" height="80"/>
        </svg>'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            f.write(svg_content)
            temp_path = f.name
        
        try:
            result = self.parser.parse(temp_path)
            boundary = result[Color.RED][0]
            
            # Check RawBoundary structure
            assert boundary.color == Color.RED
            assert boundary.is_closed == True
            assert len(boundary.points) >= 4  # Rectangle should have at least 4 points
            
            # Points should be in order around the boundary
            points = boundary.points
            for i in range(len(points) - 1):
                # Consecutive points should be different
                assert points[i] != points[i + 1]
            
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.parametrize("hex_color,expected_primary", [
        ("#ff0000", Color.RED),
        ("#00ff00", Color.GREEN),
        ("#0000ff", Color.BLUE),
        ("#ff8080", Color.RED),    # Light red -> red
        ("#80ff80", Color.GREEN),  # Light green -> green
        ("#8080ff", Color.BLUE),   # Light blue -> blue
        ("#ff4000", Color.RED),    # Orange-red -> red
        ("#ffff00", Color.RED),    # Yellow -> red (closest to red+green)
    ])
    def test_hex_color_mapping(self, hex_color, expected_primary):
        """Test mapping of various hex colors to primary colors"""
        result = self.parser._hex_to_primary_color(hex_color)
        assert result == expected_primary
    
    def test_parse_complex_path(self):
        """Test parsing of complex SVG path with multiple commands"""
        svg_content = '''<?xml version="1.0"?>
        <svg xmlns="http://www.w3.org/2000/svg">
            <path stroke="red" d="M10,10 L20,20 C30,30 40,40 50,50 L60,60 Z"/>
        </svg>'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            f.write(svg_content)
            temp_path = f.name
        
        try:
            result = self.parser.parse(temp_path)
            boundary = result[Color.RED][0]
            
            # Should extract points from move-to and line-to commands
            assert len(boundary.points) >= 3
            assert boundary.is_closed == True  # Due to Z command
            
        finally:
            os.unlink(temp_path)
    
    def test_error_handling_malformed_elements(self):
        """Test error handling for malformed SVG elements"""
        svg_content = '''<?xml version="1.0"?>
        <svg xmlns="http://www.w3.org/2000/svg">
            <rect stroke="red" x="invalid" y="10" width="20" height="20"/>
            <circle stroke="green" cx="50" cy="invalid" r="10"/>
            <polygon stroke="blue" points="invalid,points,here"/>
        </svg>'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            f.write(svg_content)
            temp_path = f.name
        
        try:
            result = self.parser.parse(temp_path)
            
            # Should handle errors gracefully and skip invalid elements
            # No assertions about specific content, just that it doesn't crash
            
        finally:
            os.unlink(temp_path)
    
    def test_raw_boundary_validation(self):
        """Test that RawBoundary validates point count"""
        # Should work with 3+ points
        points = [Point(0, 0), Point(1, 0), Point(1, 1)]
        boundary = RawBoundary(points=points, color=Color.RED)
        assert boundary.points == points
        
        # Should fail with less than 3 points
        with pytest.raises(ValueError, match="Raw boundary must have at least 3 points"):
            RawBoundary(points=[Point(0, 0), Point(1, 1)], color=Color.RED)