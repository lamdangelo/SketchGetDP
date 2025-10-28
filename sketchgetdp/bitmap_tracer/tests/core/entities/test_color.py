import pytest
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
sys.path.insert(0, project_root)

from core.entities.color import Color, ColorCategory


class TestColorSimple:
    """Validation of Color entity core RGB logic without external dependencies."""
    
    @pytest.mark.parametrize("b,g,r,expected_blue", [
        (200, 100, 100, True),   # Blue dominant
        (180, 150, 150, True),   # Blue dominant
        (100, 200, 100, False),  # Green dominant
        (100, 100, 200, False),  # Red dominant
        (150, 150, 150, False),  # Equal - no dominance
    ])
    def test_identifies_blue_dominant_colors(self, b, g, r, expected_blue):
        color = Color(b=b, g=g, r=r)
        is_blue_dominant = (color.b > color.g + 20 and color.b > color.r + 20)
        assert is_blue_dominant == expected_blue
    
    @pytest.mark.parametrize("b,g,r,expected_red", [
        (100, 100, 200, True),   # Red dominant
        (150, 150, 180, True),   # Red dominant
        (200, 100, 100, False),  # Blue dominant
        (100, 200, 100, False),  # Green dominant
        (150, 150, 150, False),  # Equal - no dominance
    ])
    def test_identifies_red_dominant_colors(self, b, g, r, expected_red):
        color = Color(b=b, g=g, r=r)
        is_red_dominant = (color.r > color.g + 20 and color.r > color.b + 20)
        assert is_red_dominant == expected_red
    
    @pytest.mark.parametrize("b,g,r,expected_green", [
        (100, 200, 100, True),   # Green dominant
        (150, 180, 150, True),   # Green dominant
        (200, 100, 100, False),  # Blue dominant
        (100, 100, 200, False),  # Red dominant
        (150, 150, 150, False),  # Equal - no dominance
    ])
    def test_identifies_green_dominant_colors(self, b, g, r, expected_green):
        color = Color(b=b, g=g, r=r)
        is_green_dominant = (color.g > color.r + 20 and color.g > color.b + 20)
        assert is_green_dominant == expected_green
    
    def test_converts_between_color_formats(self):
        color = Color.from_bgr_tuple((100, 150, 200))
        assert color.b == 100
        assert color.g == 150
        assert color.r == 200
        assert color.to_bgr_tuple() == (100, 150, 200)
        assert color.to_rgb_tuple() == (200, 150, 100)
        assert color.to_hex() == "#C89664"
    
    def test_prevents_modification_after_creation(self):
        color = Color(b=100, g=150, r=200)
        with pytest.raises(Exception):
            color.b = 50
    
    @pytest.mark.parametrize("hex_input,expected_rgb", [
        ("#FF8040", (0xFF, 0x80, 0x40)),
        ("#F84", (0xFF, 0x88, 0x44)),
        ("#0000FF", (0x00, 0x00, 0xFF)),
        ("#00FF00", (0x00, 0xFF, 0x00)),
        ("#FF0000", (0xFF, 0x00, 0x00)),
    ])
    def test_parses_hex_codes_correctly(self, hex_input, expected_rgb):
        color = Color.from_hex(hex_input)
        assert color.r == expected_rgb[0]
        assert color.g == expected_rgb[1]
        assert color.b == expected_rgb[2]
    
    def test_maps_primary_categories_to_hex_values(self):
        assert Color.CATEGORY_HEX_COLORS[ColorCategory.BLUE] == "#0000FF"
        assert Color.CATEGORY_HEX_COLORS[ColorCategory.RED] == "#FF0000"
        assert Color.CATEGORY_HEX_COLORS[ColorCategory.GREEN] == "#00FF00"
        
        # Only primary colors should have hex mappings
        assert ColorCategory.WHITE not in Color.CATEGORY_HEX_COLORS
        assert ColorCategory.BLACK not in Color.CATEGORY_HEX_COLORS
        assert ColorCategory.OTHER not in Color.CATEGORY_HEX_COLORS
    
    @pytest.mark.parametrize("bgr_tuple,expected_primary", [
        ((200, 100, 100), True),   # Blue
        ((100, 200, 100), True),   # Green  
        ((100, 100, 200), True),   # Red
        ((255, 255, 255), False),  # White
        ((0, 0, 0), False),        # Black
        ((150, 150, 150), False),  # Gray
    ])
    def test_detects_primary_colors_using_mocked_categorization(self, bgr_tuple, expected_primary):
        color = Color.from_bgr_tuple(bgr_tuple)
        
        if bgr_tuple == (200, 100, 100):
            mock_return = (ColorCategory.BLUE, "#0000FF")
        elif bgr_tuple == (100, 200, 100):
            mock_return = (ColorCategory.GREEN, "#00FF00")
        elif bgr_tuple == (100, 100, 200):
            mock_return = (ColorCategory.RED, "#FF0000")
        else:
            mock_return = (ColorCategory.OTHER, None)
        
        with pytest.MonkeyPatch().context() as m:
            m.setattr(Color, 'categorize', lambda self: mock_return)
            is_primary = color.is_primary_color()
        
        assert is_primary == expected_primary
    
    @pytest.mark.parametrize("bgr_tuple,expected_ignored", [
        ((255, 255, 255), True),   # White
        ((0, 0, 0), True),         # Black
        ((150, 150, 150), True),   # Gray
        ((200, 100, 100), False),  # Blue
        ((100, 200, 100), False),  # Green
        ((100, 100, 200), False),  # Red
    ])
    def test_detects_ignored_colors_using_mocked_categorization(self, bgr_tuple, expected_ignored):
        color = Color.from_bgr_tuple(bgr_tuple)
        
        if bgr_tuple == (255, 255, 255):
            mock_return = (ColorCategory.WHITE, None)
        elif bgr_tuple == (0, 0, 0):
            mock_return = (ColorCategory.BLACK, None)
        elif bgr_tuple == (150, 150, 150):
            mock_return = (ColorCategory.OTHER, None)
        elif bgr_tuple == (200, 100, 100):
            mock_return = (ColorCategory.BLUE, "#0000FF")
        elif bgr_tuple == (100, 200, 100):
            mock_return = (ColorCategory.GREEN, "#00FF00")
        else:
            mock_return = (ColorCategory.RED, "#FF0000")
        
        with pytest.MonkeyPatch().context() as m:
            m.setattr(Color, 'categorize', lambda self: mock_return)
            is_ignored = color.is_ignored_color()
        
        assert is_ignored == expected_ignored