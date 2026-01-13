"""
Unit tests for Color class.

Tests color creation, validation, conversion, and predefined color functionality.
"""
import pytest

from core.entities.color import Color


class TestColor:
    """Test suite for Color class."""

    # ==================== Basic Functionality Tests ====================

    def test_color_creation(self):
        """Test that a color can be created with name and RGB values."""
        color = Color("red", (255, 0, 0))
        
        assert color.name == "red"
        assert color.rgb == (255, 0, 0)
    
    def test_predefined_colors(self):
        """Test that predefined colors are available and correct."""
        assert Color.RED.name == "red"
        assert Color.RED.rgb == (255, 0, 0)
        
        assert Color.GREEN.name == "green"
        assert Color.GREEN.rgb == (0, 255, 0)
        
        assert Color.BLUE.name == "blue"
        assert Color.BLUE.rgb == (0, 0, 255)
        
        assert Color.BLACK.name == "black"
        assert Color.BLACK.rgb == (0, 0, 0)
    
    def test_color_equality(self):
        """Test that colors with same name and RGB are equal."""
        color1 = Color("red", (255, 0, 0))
        color2 = Color("red", (255, 0, 0))
        color3 = Color("blue", (0, 0, 255))
        
        assert color1 == color2
        assert color1 != color3
    
    def test_color_hash(self):
        """Test that colors are hashable."""
        color1 = Color("red", (255, 0, 0))
        color2 = Color("red", (255, 0, 0))
        color3 = Color("green", (0, 255, 0))
        color4 = Color("black", (0, 0, 0))
        
        color_set = {color1, color2, color3, color4}
        assert len(color_set) == 3  # color1 and color2 are duplicates
        assert color1 in color_set
        assert color2 in color_set
        assert color3 in color_set
        assert color4 in color_set

    # ==================== Immutability Tests ====================

    def test_color_immutability(self):
        """Test that Color is immutable."""
        color = Color("red", (255, 0, 0))
        
        with pytest.raises(AttributeError):
            color.name = "blue"
        with pytest.raises(AttributeError):
            color.rgb = (0, 0, 255)

    # ==================== String Representation Tests ====================

    def test_color_repr(self):
        """Test the string representation of Color."""
        color = Color("red", (255, 0, 0))
        repr_str = repr(color)
        
        assert "Color" in repr_str
        assert "red" in repr_str
        assert "(255, 0, 0)" in repr_str
    
    def test_color_str(self):
        """Test the human-readable string representation."""
        color = Color("green", (0, 255, 0))
        str_repr = str(color)
        
        assert "Color" in str_repr        
        assert "green" in str_repr
        assert "(0, 255, 0)" in str_repr

    # ==================== Conversion Methods Tests ====================

    def test_to_hex(self):
        """Test conversion to hexadecimal format."""
        assert Color.RED.to_hex() == "#ff0000"
        assert Color.GREEN.to_hex() == "#00ff00"
        assert Color.BLUE.to_hex() == "#0000ff"
        assert Color.BLACK.to_hex() == "#000000"
    
    def test_to_normalized_rgb(self):
        """Test conversion to normalized RGB values."""
        red_norm = Color.RED.to_normalized_rgb()
        green_norm = Color.GREEN.to_normalized_rgb()
        blue_norm = Color.BLUE.to_normalized_rgb()
        black_norm = Color.BLACK.to_normalized_rgb()
        
        assert red_norm == (1.0, 0.0, 0.0)
        assert green_norm == (0.0, 1.0, 0.0)
        assert blue_norm == (0.0, 0.0, 1.0)
        assert black_norm == (0.0, 0.0, 0.0)
        
        # Test with mid-range values using allowed color names
        dark_red = Color("red", (128, 0, 0))
        dark_red_norm = dark_red.to_normalized_rgb()
        expected_red = (128/255.0, 0.0, 0.0)
        assert dark_red_norm == pytest.approx(expected_red)
        
        dark_green = Color("green", (0, 128, 0))
        dark_green_norm = dark_green.to_normalized_rgb()
        expected_green = (0.0, 128/255.0, 0.0)
        assert dark_green_norm == pytest.approx(expected_green)
        
        dark_black = Color("black", (64, 64, 64))
        dark_black_norm = dark_black.to_normalized_rgb()
        expected_black = (64/255.0, 64/255.0, 64/255.0)
        assert dark_black_norm == pytest.approx(expected_black)

    # ==================== Validation Tests ====================

    def test_invalid_color_name(self):
        """Test that color rejects invalid names."""
        with pytest.raises(ValueError, match="Color must be 'red', 'green', 'blue', or 'black'"):
            Color("yellow", (255, 255, 0))
        with pytest.raises(ValueError, match="Color must be 'red', 'green', 'blue', or 'black'"):
            Color("", (255, 0, 0))
        with pytest.raises(ValueError, match="Color must be 'red', 'green', 'blue', or 'black'"):
            Color("RED", (255, 0, 0))  # case sensitive
        with pytest.raises(ValueError, match="Color must be 'red', 'green', 'blue', or 'black'"):
            Color("gray", (128, 128, 128))
    
    def test_invalid_name_type(self):
        """Test that color name must be a string."""
        with pytest.raises(TypeError, match="Color name must be a string"):
            Color(123, (255, 0, 0))
        with pytest.raises(TypeError, match="Color name must be a string"):
            Color(None, (255, 0, 0))
    
    def test_invalid_rgb_format(self):
        """Test that RGB must be a tuple of 3 integers."""
        with pytest.raises(ValueError, match="RGB must be a tuple of 3 integers"):
            Color("red", [255, 0, 0])  # list instead of tuple
        with pytest.raises(ValueError, match="RGB must be a tuple of 3 integers"):
            Color("red", (255, 0))     # too few elements
        with pytest.raises(ValueError, match="RGB must be a tuple of 3 integers"):
            Color("red", (255, 0, 0, 0))  # too many elements
    
    def test_invalid_rgb_values(self):
        """Test that RGB values must be between 0 and 255."""
        with pytest.raises(ValueError, match="RGB values must be integers between 0 and 255"):
            Color("red", (-1, 0, 0))   # negative value
        with pytest.raises(ValueError, match="RGB values must be integers between 0 and 255"):
            Color("red", (256, 0, 0))  # value too high
        with pytest.raises(ValueError, match="RGB values must be integers between 0 and 255"):
            Color("red", (255.5, 0, 0))  # float instead of int
        with pytest.raises(ValueError, match="RGB values must be integers between 0 and 255"):
            Color("red", ("255", 0, 0))  # string instead of int

    # ==================== Parameterized Tests ====================

    @pytest.mark.parametrize("name,rgb,expected_hex,expected_norm", [
        ("red", (128, 0, 0), "#800000", (128/255.0, 0.0, 0.0)),
        ("green", (0, 128, 0), "#008000", (0.0, 128/255.0, 0.0)),
        ("blue", (0, 0, 128), "#000080", (0.0, 0.0, 128/255.0)),
        ("black", (64, 64, 64), "#404040", (64/255.0, 64/255.0, 64/255.0)),
    ])
    def test_color_conversions(self, name, rgb, expected_hex, expected_norm):
        """Test various color conversion scenarios."""
        color = Color(name, rgb)
        
        assert color.to_hex() == expected_hex
        assert color.to_normalized_rgb() == pytest.approx(expected_norm)

    # ==================== Predefined Colors Tests ====================

    def test_predefined_colors_are_singletons(self):
        """Test that predefined colors behave like singletons."""
        red1 = Color.RED
        red2 = Color.RED
        green = Color.GREEN
        black = Color.BLACK
        
        assert red1 is red2  # They should be the same instance
        assert red1 is not green
        assert red1 is not black
