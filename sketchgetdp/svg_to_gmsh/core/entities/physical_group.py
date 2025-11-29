from dataclasses import dataclass
from typing import ClassVar, Optional
from color import Color


@dataclass(frozen=True)
class PhysicalGroup:
    """A physical group entity representing different domains and boundaries in the system."""
    
    # Pre-defined class variables for all physical groups
    DOMAIN_VI_IRON: ClassVar['PhysicalGroup'] = None
    DOMAIN_VI_AIR: ClassVar['PhysicalGroup'] = None
    DOMAIN_VA: ClassVar['PhysicalGroup'] = None
    DOMAIN_COIL_POSITIVE: ClassVar['PhysicalGroup'] = None
    DOMAIN_COIL_NEGATIVE: ClassVar['PhysicalGroup'] = None
    BOUNDARY_GAMMA: ClassVar['PhysicalGroup'] = None
    BOUNDARY_OUT: ClassVar['PhysicalGroup'] = None
    
    name: str
    description: str
    group_type: str  # "domain" or "boundary"
    color: Optional[Color] = None
    current_sign: Optional[int] = None  # 1 for positive, -1 for negative, None for non-coil domains
    
    def __post_init__(self):
        """Validate physical group after initialization"""
        if not isinstance(self.name, str):
            raise TypeError("Physical group name must be a string")
        
        if not isinstance(self.description, str):
            raise TypeError("Physical group description must be a string")
        
        if self.group_type not in ["domain", "boundary"]:
            raise ValueError("Group type must be either 'domain' or 'boundary'")
        
        if self.color is not None and not isinstance(self.color, Color):
            raise TypeError("Color must be an instance of Color class or None")
        
        if self.current_sign not in [None, 1, -1]:
            raise ValueError("Current sign must be None, 1 (positive), or -1 (negative)")
        
        # Validate coil-specific constraints
        if "coil" in self.name:
            if self.current_sign is None:
                raise ValueError("Coil domains must have a current sign (1 or -1)")
            if self.color != Color.RED:
                raise ValueError("Coil domains must be red")
        else:
            if self.current_sign is not None:
                raise ValueError("Only coil domains can have a current sign")
    
    def has_color(self) -> bool:
        """Check if this physical group has an associated color."""
        return self.color is not None
    
    def is_coil(self) -> bool:
        """Check if this is a coil domain."""
        return "coil" in self.name and self.group_type == "domain"
    
    def is_boundary(self) -> bool:
        """Check if this is a boundary."""
        return self.group_type == "boundary"
    
    def is_domain(self) -> bool:
        """Check if this is a domain."""
        return self.group_type == "domain"

PhysicalGroup.DOMAIN_VI_IRON = PhysicalGroup(
    name="domain_Vi_iron",
    description="Iron domain in Vi region",
    group_type="domain",
    color=Color.BLUE
)

PhysicalGroup.DOMAIN_VI_AIR = PhysicalGroup(
    name="domain_Vi_air", 
    description="Air domain in Vi region",
    group_type="domain",
    color=Color.GREEN
)

PhysicalGroup.DOMAIN_VA = PhysicalGroup(
    name="domain_Va",
    description="Va domain",
    group_type="domain", 
    color=Color.BLACK
)

PhysicalGroup.DOMAIN_COIL_POSITIVE = PhysicalGroup(
    name="domain_coil_positive",
    description="Coil domain with positive current",
    group_type="domain",
    color=Color.RED,
    current_sign=1
)

PhysicalGroup.DOMAIN_COIL_NEGATIVE = PhysicalGroup(
    name="domain_coil_negative", 
    description="Coil domain with negative current",
    group_type="domain",
    color=Color.RED,
    current_sign=-1
)

PhysicalGroup.BOUNDARY_GAMMA = PhysicalGroup(
    name="boundary_gamma",
    description="Interface boundary between Vi and Va regions",
    group_type="boundary"
)

PhysicalGroup.BOUNDARY_OUT = PhysicalGroup(
    name="boundary_out",
    description="Outermost boundary",
    group_type="boundary"
)