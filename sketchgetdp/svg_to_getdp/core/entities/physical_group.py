from dataclasses import dataclass
from typing import Optional
from ...core.entities.color import Color


@dataclass(frozen=True)
class PhysicalGroup:
    """A physical group entity representing different domains and boundaries in the system."""
    
    name: str
    description: str
    group_type: str  # "domain" or "boundary"
    value: int  # Numeric identifier for the physical group
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
        
        if not isinstance(self.value, int):
            raise TypeError("Value must be an integer")
        
        if self.color is not None and not isinstance(self.color, Color):
            raise TypeError("Color must be an instance of Color class or None")
        
        if self.current_sign not in [None, 1, -1]:
            raise ValueError("Current sign must be None, 1 (positive), or -1 (negative)")
        
        # Validate coil-specific constraints
        # Only apply coil rules if it's a domain AND has "coil" in name (case-insensitive)
        if self.group_type == "domain" and "coil" in self.name.lower():
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
        return self.group_type == "domain" and "coil" in self.name.lower()
    
    def is_boundary(self) -> bool:
        """Check if this is a boundary."""
        return self.group_type == "boundary"
    
    def is_domain(self) -> bool:
        """Check if this is a domain."""
        return self.group_type == "domain"


# Module-level constants instead of class variables
DOMAIN_VI_IRON = PhysicalGroup(
    name="domain_Vi_iron",
    description="Iron domain in Vi region",
    group_type="domain",
    value=2,
    color=Color.BLUE
)

DOMAIN_VI_AIR = PhysicalGroup(
    name="domain_Vi_air", 
    description="Air domain in Vi region",
    group_type="domain",
    value=3,
    color=Color.GREEN
)

DOMAIN_VA = PhysicalGroup(
    name="domain_Va",
    description="Va domain",
    group_type="domain", 
    value=1,
    color=Color.BLACK
)

DOMAIN_COIL_POSITIVE = PhysicalGroup(
    name="domain_coil_positive",
    description="Coil domain with positive current",
    group_type="domain",
    value=101,
    color=Color.RED,
    current_sign=1
)

DOMAIN_COIL_NEGATIVE = PhysicalGroup(
    name="domain_coil_negative", 
    description="Coil domain with negative current",
    group_type="domain",
    value=102,
    color=Color.RED,
    current_sign=-1
)

BOUNDARY_GAMMA = PhysicalGroup(
    name="boundary_gamma",
    description="Interface boundary between Vi and Va regions",
    group_type="boundary",
    value=11
)

BOUNDARY_OUT = PhysicalGroup(
    name="boundary_out",
    description="Outermost boundary",
    group_type="boundary",
    value=12
)