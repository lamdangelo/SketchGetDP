import pytest
from svg_to_getdp.core.entities.physical_group import PhysicalGroup
from svg_to_getdp.core.entities.color import Color


class TestPhysicalGroup:
    """Test suite for PhysicalGroup entity"""
    
    def test_valid_domain_creation(self):
        """Test creating a valid domain physical group"""
        pg = PhysicalGroup(
            name="test_domain",
            description="Test domain description",
            group_type="domain",
            value=100
        )
        
        assert pg.name == "test_domain"
        assert pg.description == "Test domain description"
        assert pg.group_type == "domain"
        assert pg.value == 100
        assert pg.color is None
        assert pg.current_sign is None
        assert pg.is_domain() is True
        assert pg.is_boundary() is False
        assert pg.has_color() is False
        assert pg.is_coil() is False
    
    def test_valid_boundary_creation(self):
        """Test creating a valid boundary physical group"""
        pg = PhysicalGroup(
            name="test_boundary",
            description="Test boundary description",
            group_type="boundary",
            value=200,
            color=Color.BLUE
        )
        
        assert pg.name == "test_boundary"
        assert pg.description == "Test boundary description"
        assert pg.group_type == "boundary"
        assert pg.value == 200
        assert pg.color == Color.BLUE
        assert pg.current_sign is None
        assert pg.is_boundary() is True
        assert pg.is_domain() is False
        assert pg.has_color() is True
        assert pg.is_coil() is False
    
    def test_valid_coil_creation(self):
        """Test creating a valid coil domain"""
        # Positive coil
        pg_pos = PhysicalGroup(
            name="coil_positive",
            description="Positive coil domain",
            group_type="domain",
            value=101,
            color=Color.RED,
            current_sign=1
        )
        
        assert pg_pos.name == "coil_positive"
        assert pg_pos.group_type == "domain"
        assert pg_pos.color == Color.RED
        assert pg_pos.current_sign == 1
        assert pg_pos.is_coil() is True
        assert pg_pos.is_domain() is True
        
        # Negative coil
        pg_neg = PhysicalGroup(
            name="domain_coil_negative",
            description="Negative coil domain",
            group_type="domain",
            value=102,
            color=Color.RED,
            current_sign=-1
        )
        
        assert pg_neg.name == "domain_coil_negative"
        assert pg_neg.color == Color.RED
        assert pg_neg.current_sign == -1
        assert pg_neg.is_coil() is True
    
    def test_invalid_name_type(self):
        """Test invalid name type"""
        with pytest.raises(TypeError, match="Physical group name must be a string"):
            PhysicalGroup(
                name=123,  # Should be string
                description="Test",
                group_type="domain",
                value=100
            )
    
    def test_invalid_description_type(self):
        """Test invalid description type"""
        with pytest.raises(TypeError, match="Physical group description must be a string"):
            PhysicalGroup(
                name="test",
                description=456,  # Should be string
                group_type="domain",
                value=100
            )
    
    def test_invalid_group_type(self):
        """Test invalid group type"""
        with pytest.raises(ValueError, match="Group type must be either 'domain' or 'boundary'"):
            PhysicalGroup(
                name="test",
                description="Test",
                group_type="invalid_type",  # Invalid type
                value=100
            )
    
    def test_invalid_value_type(self):
        """Test invalid value type"""
        with pytest.raises(TypeError, match="Value must be an integer"):
            PhysicalGroup(
                name="test",
                description="Test",
                group_type="domain",
                value="not_an_int"  # Should be int
            )
    
    def test_invalid_color_type(self):
        """Test invalid color type"""
        with pytest.raises(TypeError, match="Color must be an instance of Color class or None"):
            PhysicalGroup(
                name="test",
                description="Test",
                group_type="domain",
                value=100,
                color="not_a_color"  # Should be Color instance
            )
    
    def test_invalid_current_sign(self):
        """Test invalid current sign value"""
        with pytest.raises(ValueError, match=r"Current sign must be None, 1 \(positive\), or -1 \(negative\)"):
            PhysicalGroup(
                name="test",
                description="Test",
                group_type="domain",
                value=100,
                current_sign=2  # Invalid current sign
            )
    
    def test_coil_missing_current_sign(self):
        """Test coil domain without current sign"""
        with pytest.raises(ValueError, match="Coil domains must have a current sign"):
            PhysicalGroup(
                name="coil_test",  # Contains "coil"
                description="Coil test",
                group_type="domain",
                value=100,
                color=Color.RED,
                current_sign=None  # Missing for coil
            )
    
    def test_coil_wrong_color(self):
        """Test coil domain with wrong color"""
        with pytest.raises(ValueError, match="Coil domains must be red"):
            PhysicalGroup(
                name="domain_coil_positive",
                description="Coil with wrong color",
                group_type="domain",
                value=100,
                color=Color.BLUE,  # Should be RED
                current_sign=1
            )
    
    def test_non_coil_with_current_sign(self):
        """Test non-coil domain with current sign"""
        with pytest.raises(ValueError, match="Only coil domains can have a current sign"):
            PhysicalGroup(
                name="regular_domain",  # No "coil" in name
                description="Regular domain",
                group_type="domain",
                value=100,
                current_sign=1  # Should be None
            )
    
    def test_frozen_dataclass(self):
        """Test that PhysicalGroup is immutable (frozen dataclass)"""
        pg = PhysicalGroup(
            name="test",
            description="Test",
            group_type="domain",
            value=100
        )
        
        # Should not be able to modify attributes
        with pytest.raises(Exception):
            pg.name = "modified"
        
        with pytest.raises(Exception):
            pg.value = 200
    
    def test_is_coil_method(self):
        """Test the is_coil() method"""
        # Should be True for domains with "coil" in name
        coil_pg = PhysicalGroup(
            name="some_coil_domain",
            description="Coil domain",
            group_type="domain",
            value=100,
            color=Color.RED,
            current_sign=1
        )
        assert coil_pg.is_coil() is True
        
        # Should be False for boundaries even with "coil" in name
        coil_boundary = PhysicalGroup(
            name="boundary_coil",
            description="Coil boundary",
            group_type="boundary",
            value=200
        )
        assert coil_boundary.is_coil() is False
        
        # Should be False for domains without "coil" in name
        non_coil = PhysicalGroup(
            name="regular_domain",
            description="Regular",
            group_type="domain",
            value=300
        )
        assert non_coil.is_coil() is False
    
    def test_module_constants(self):
        """Test the module-level constants"""
        from svg_to_getdp.core.entities.physical_group import (
            DOMAIN_VI_IRON,
            DOMAIN_VI_AIR,
            DOMAIN_VA,
            DOMAIN_COIL_POSITIVE,
            DOMAIN_COIL_NEGATIVE,
            BOUNDARY_GAMMA,
            BOUNDARY_OUT
        )
        
        # Test DOMAIN_VI_IRON
        assert DOMAIN_VI_IRON.name == "domain_Vi_iron"
        assert DOMAIN_VI_IRON.description == "Iron domain in Vi region"
        assert DOMAIN_VI_IRON.group_type == "domain"
        assert DOMAIN_VI_IRON.value == 2
        assert DOMAIN_VI_IRON.color == Color.BLUE
        
        # Test DOMAIN_VI_AIR
        assert DOMAIN_VI_AIR.name == "domain_Vi_air"
        assert DOMAIN_VI_AIR.description == "Air domain in Vi region"
        assert DOMAIN_VI_AIR.group_type == "domain"
        assert DOMAIN_VI_AIR.value == 3
        assert DOMAIN_VI_AIR.color == Color.GREEN
        
        # Test DOMAIN_VA
        assert DOMAIN_VA.name == "domain_Va"
        assert DOMAIN_VA.description == "Va domain"
        assert DOMAIN_VA.group_type == "domain"
        assert DOMAIN_VA.value == 1
        assert DOMAIN_VA.color == Color.BLACK
        
        # Test DOMAIN_COIL_POSITIVE
        assert DOMAIN_COIL_POSITIVE.name == "domain_coil_positive"
        assert DOMAIN_COIL_POSITIVE.description == "Coil domain with positive current"
        assert DOMAIN_COIL_POSITIVE.group_type == "domain"
        assert DOMAIN_COIL_POSITIVE.value == 101
        assert DOMAIN_COIL_POSITIVE.color == Color.RED
        assert DOMAIN_COIL_POSITIVE.current_sign == 1
        assert DOMAIN_COIL_POSITIVE.is_coil() is True
        
        # Test DOMAIN_COIL_NEGATIVE
        assert DOMAIN_COIL_NEGATIVE.name == "domain_coil_negative"
        assert DOMAIN_COIL_NEGATIVE.description == "Coil domain with negative current"
        assert DOMAIN_COIL_NEGATIVE.group_type == "domain"
        assert DOMAIN_COIL_NEGATIVE.value == 102
        assert DOMAIN_COIL_NEGATIVE.color == Color.RED
        assert DOMAIN_COIL_NEGATIVE.current_sign == -1
        assert DOMAIN_COIL_NEGATIVE.is_coil() is True
        
        # Test BOUNDARY_GAMMA
        assert BOUNDARY_GAMMA.name == "boundary_gamma"
        assert BOUNDARY_GAMMA.description == "Interface boundary between Vi and Va regions"
        assert BOUNDARY_GAMMA.group_type == "boundary"
        assert BOUNDARY_GAMMA.value == 11
        assert BOUNDARY_GAMMA.is_boundary() is True
        
        # Test BOUNDARY_OUT
        assert BOUNDARY_OUT.name == "boundary_out"
        assert BOUNDARY_OUT.description == "Outermost boundary"
        assert BOUNDARY_OUT.group_type == "boundary"
        assert BOUNDARY_OUT.value == 12
        assert BOUNDARY_OUT.is_boundary() is True
    
    def test_edge_cases(self):
        """Test edge cases"""
        # Empty strings should be allowed (though maybe not practical)
        pg = PhysicalGroup(
            name="",
            description="",
            group_type="domain",
            value=0
        )
        assert pg.name == ""
        assert pg.description == ""
        
        # Negative value should be allowed
        pg_neg = PhysicalGroup(
            name="test",
            description="Test",
            group_type="domain",
            value=-1
        )
        assert pg_neg.value == -1
    
    def test_has_color_method(self):
        """Test the has_color() method"""
        pg_with_color = PhysicalGroup(
            name="test",
            description="Test",
            group_type="domain",
            value=100,
            color=Color.BLUE
        )
        assert pg_with_color.has_color() is True
        
        pg_without_color = PhysicalGroup(
            name="test",
            description="Test",
            group_type="domain",
            value=100
        )
        assert pg_without_color.has_color() is False
    
    def test_coil_name_variations(self):
        """Test that is_coil() works with different coil name variations"""
        # Test various coil name patterns
        coil_names = [
            "coil",
            "domain_coil",
            "coil_domain",
            "primary_coil",
            "coil_1",
            "my_coil_positive",
            "COIL",  # Case sensitive - should still work
        ]
        
        for name in coil_names:
            pg = PhysicalGroup(
                name=name,
                description=f"Test {name}",
                group_type="domain",
                value=100,
                color=Color.RED,
                current_sign=1
            )
            assert pg.is_coil() is True, f"Failed for name: {name}"
        
        # Non-coil names
        non_coil_names = [
            "air",
            "iron",
            "boundary",
            "domain",
            "coilboundary",  # Contains "coil" but is boundary
        ]
        
        for name in non_coil_names:
            # For boundaries, even with "coil" in name, is_coil() should be False
            pg_type = "boundary" if "coil" in name else "domain"
            pg = PhysicalGroup(
                name=name,
                description=f"Test {name}",
                group_type=pg_type,
                value=100,
                color=Color.RED if pg_type == "domain" and "coil" in name else None,
                current_sign=1 if pg_type == "domain" and "coil" in name else None
            )
            assert pg.is_coil() is False, f"Failed for name: {name}"