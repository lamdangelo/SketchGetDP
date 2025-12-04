import pytest

from core.entities.color import Color


class TestColor:
    """Test suite for the simple Color entity with red, green, and blue colors"""
    
    def test_color_creation(self):
        """Test that a color can be created with name and RGB values"""
        color = Color("red", (255, 0, 0))
        assert color.name == "red"
        assert color.rgb == (255, 0, 0)
    
    def test_predefined_colors(self):
        """Test that predefined colors are available and correct"""
        assert Color.RED.name == "red"
        assert Color.RED.rgb == (255, 0, 0)
        
        assert Color.GREEN.name == "green"
        assert Color.GREEN.rgb == (0, 255, 0)
        
        assert Color.BLUE.name == "blue"
        assert Color.BLUE.rgb == (0, 0, 255)
    
    def test_color_immutability(self):
        """Test that Color is immutable"""
        color = Color("red", (255, 0, 0))
        
        with pytest.raises(AttributeError):
            color.name = "blue"
        with pytest.raises(AttributeError):
            color.rgb = (0, 0, 255)
    
    def test_color_equality(self):
        """Test that colors with same name and RGB are equal"""
        color1 = Color("red", (255, 0, 0))
        color2 = Color("red", (255, 0, 0))
        color3 = Color("blue", (0, 0, 255))
        
        assert color1 == color2
        assert color1 != color3
    
    def test_color_hash(self):
        """Test that colors are hashable"""
        color1 = Color("red", (255, 0, 0))
        color2 = Color("red", (255, 0, 0))
        color3 = Color("green", (0, 255, 0))
        
        color_set = {color1, color2, color3}
        assert len(color_set) == 2  # color1 and color2 are duplicates
        assert color1 in color_set
        assert color2 in color_set
        assert color3 in color_set
    
    def test_color_repr(self):
        """Test the string representation of Color"""
        color = Color("red", (255, 0, 0))
        repr_str = repr(color)
        
        assert "Color" in repr_str
        assert "red" in repr_str
        assert "255" in repr_str
    
    def test_color_str(self):
        """Test the human-readable string representation"""
        color = Color("green", (0, 255, 0))
        str_repr = str(color)
        
        assert "green" in str_repr
        assert "0" in str_repr
        assert "255" in str_repr
    
    def test_to_hex(self):
        """Test conversion to hexadecimal format"""
        assert Color.RED.to_hex() == "#ff0000"
        assert Color.GREEN.to_hex() == "#00ff00"
        assert Color.BLUE.to_hex() == "#0000ff"
        
        # Test with custom color variants
        dark_red = Color("red", (128, 0, 0))
        assert dark_red.to_hex() == "#800000"
    
    def test_to_normalized_rgb(self):
        """Test conversion to normalized RGB values"""
        red_norm = Color.RED.to_normalized_rgb()
        green_norm = Color.GREEN.to_normalized_rgb()
        blue_norm = Color.BLUE.to_normalized_rgb()
        
        assert red_norm == (1.0, 0.0, 0.0)
        assert green_norm == (0.0, 1.0, 0.0)
        assert blue_norm == (0.0, 0.0, 1.0)
        
        # Test with mid-range values using allowed color names
        dark_red = Color("red", (128, 0, 0))
        dark_red_norm = dark_red.to_normalized_rgb()
        expected_red = (128/255.0, 0.0, 0.0)
        assert dark_red_norm == pytest.approx(expected_red)
        
        dark_green = Color("green", (0, 128, 0))
        dark_green_norm = dark_green.to_normalized_rgb()
        expected_green = (0.0, 128/255.0, 0.0)
        assert dark_green_norm == pytest.approx(expected_green)
    
    def test_invalid_color_name(self):
        """Test that color rejects invalid names"""
        with pytest.raises(ValueError, match="Color must be 'red', 'green', or 'blue'"):
            Color("yellow", (255, 255, 0))
        with pytest.raises(ValueError, match="Color must be 'red', 'green', or 'blue'"):
            Color("", (255, 0, 0))
        with pytest.raises(ValueError, match="Color must be 'red', 'green', or 'blue'"):
            Color("RED", (255, 0, 0))  # case sensitive
        with pytest.raises(ValueError, match="Color must be 'red', 'green', or 'blue'"):
            Color("gray", (128, 128, 128))
    
    def test_invalid_name_type(self):
        """Test that color name must be a string"""
        with pytest.raises(TypeError, match="Color name must be a string"):
            Color(123, (255, 0, 0))
        with pytest.raises(TypeError, match="Color name must be a string"):
            Color(None, (255, 0, 0))
    
    def test_invalid_rgb_format(self):
        """Test that RGB must be a tuple of 3 integers"""
        with pytest.raises(ValueError, match="RGB must be a tuple of 3 integers"):
            Color("red", [255, 0, 0])  # list instead of tuple
        with pytest.raises(ValueError, match="RGB must be a tuple of 3 integers"):
            Color("red", (255, 0))     # too few elements
        with pytest.raises(ValueError, match="RGB must be a tuple of 3 integers"):
            Color("red", (255, 0, 0, 0))  # too many elements
    
    def test_invalid_rgb_values(self):
        """Test that RGB values must be between 0 and 255"""
        with pytest.raises(ValueError, match="RGB values must be integers between 0 and 255"):
            Color("red", (-1, 0, 0))   # negative value
        with pytest.raises(ValueError, match="RGB values must be integers between 0 and 255"):
            Color("red", (256, 0, 0))  # value too high
        with pytest.raises(ValueError, match="RGB values must be integers between 0 and 255"):
            Color("red", (255.5, 0, 0))  # float instead of int
        with pytest.raises(ValueError, match="RGB values must be integers between 0 and 255"):
            Color("red", ("255", 0, 0))  # string instead of int
    
    @pytest.mark.parametrize("name,rgb,expected_hex,expected_norm", [
        ("red", (255, 0, 0), "#ff0000", (1.0, 0.0, 0.0)),
        ("green", (0, 255, 0), "#00ff00", (0.0, 1.0, 0.0)),
        ("blue", (0, 0, 255), "#0000ff", (0.0, 0.0, 1.0)),
        ("red", (128, 0, 0), "#800000", (128/255.0, 0.0, 0.0)),
        ("green", (0, 128, 0), "#008000", (0.0, 128/255.0, 0.0)),
        ("blue", (0, 0, 128), "#000080", (0.0, 0.0, 128/255.0)),
    ])
    def test_color_conversions(self, name, rgb, expected_hex, expected_norm):
        """Test various color conversion scenarios"""
        color = Color(name, rgb)
        
        assert color.to_hex() == expected_hex
        assert color.to_normalized_rgb() == pytest.approx(expected_norm)
    
    def test_edge_case_rgb_values(self):
        """Test edge cases for RGB values"""
        # Minimum values
        min_color = Color("red", (0, 0, 0))
        assert min_color.to_hex() == "#000000"
        assert min_color.to_normalized_rgb() == (0.0, 0.0, 0.0)
        
        # Maximum values
        max_color = Color("blue", (255, 255, 255))
        assert max_color.to_hex() == "#ffffff"
        assert max_color.to_normalized_rgb() == (1.0, 1.0, 1.0)
    
    def test_predefined_colors_are_singletons(self):
        """Test that predefined colors behave like singletons"""
        red1 = Color.RED
        red2 = Color.RED
        green = Color.GREEN
        
        assert red1 is red2  # They should be the same instance
        assert red1 is not green
    
    def test_can_create_custom_variants(self):
        """Test that we can create custom variants of the base colors"""
        dark_red = Color("red", (128, 0, 0))
        light_red = Color("red", (255, 128, 128))
        
        assert dark_red.name == "red"
        assert dark_red.rgb == (128, 0, 0)
        assert light_red.name == "red"
        assert light_red.rgb == (255, 128, 128)
        
        # They should not be equal to each other or the predefined red
        assert dark_red != light_red
        assert dark_red != Color.RED
        assert light_red != Color.RED
    
    def test_allowed_color_names_case_sensitive(self):
        """Test that color names are case sensitive"""
        # These should work
        Color("red", (255, 0, 0))
        Color("green", (0, 255, 0))
        Color("blue", (0, 0, 255))
        
        # These should fail due to case sensitivity
        with pytest.raises(ValueError):
            Color("Red", (255, 0, 0))
        with pytest.raises(ValueError):
            Color("GREEN", (0, 255, 0))
        with pytest.raises(ValueError):
            Color("Blue", (0, 0, 255))