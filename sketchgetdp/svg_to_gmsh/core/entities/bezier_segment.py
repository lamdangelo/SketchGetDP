import math
from typing import List
from ...core.entities.point import Point


class BezierSegment:
    """
    Represents a single Bézier curve segment of degree n.
    Based on the mathematical definition from the paper.
    """
    
    def __init__(self, control_points: List[Point], degree: int):
        """
        Initialize Bézier segment with control points and degree.
        
        Args:
            control_points: List of n+1 control points (b_0, b_1, ..., b_n)
            degree: Degree n of the Bézier curve
        """
        if len(control_points) != degree + 1:
            raise ValueError(f"Degree {degree} requires {degree + 1} control points, "
                           f"but got {len(control_points)}")
        
        self.control_points = control_points
        self.degree = degree
        
    def bernstein_basis(self, i: int, t: float) -> float:
        """
        Compute the i-th Bernstein basis polynomial of degree n at parameter t.
        
        Args:
            i: Index of the basis polynomial (0 <= i <= n)
            t: Parameter value in [0, 1]
            
        Returns:
            Value of B_{i,n}(t)
        """
        if not 0 <= i <= self.degree:
            raise ValueError(f"Index i must be between 0 and {self.degree}, got {i}")
        
        return math.comb(self.degree, i) * (t ** i) * ((1 - t) ** (self.degree - i))
    
    def evaluate(self, t: float) -> Point:
        """
        Evaluate the Bézier curve at parameter t.
        
        Args:
            t: Parameter value in [0, 1]
            
        Returns:
            Point on the curve C(t)
        """
        if not (0 <= t <= 1):
            raise ValueError(f"Parameter t must be in [0, 1], got {t}")
        
        result = Point(0.0, 0.0)
        for i, control_point in enumerate(self.control_points):
            basis_val = self.bernstein_basis(i, t)
            result = result + control_point * basis_val
            
        return result
    
    def derivative(self, t: float) -> Point:
        """
        Compute the derivative of the Bézier curve at parameter t.
        
        Args:
            t: Parameter value in [0, 1]
            
        Returns:
            Derivative vector dC/dt at parameter t
        """
        if not (0 <= t <= 1):
            raise ValueError(f"Parameter t must be in [0, 1], got {t}")
        
        if self.degree == 0:
            return Point(0.0, 0.0)
            
        result = Point(0.0, 0.0)
        for i in range(self.degree):
            # Difference between consecutive control points
            diff = self.control_points[i + 1] - self.control_points[i]
            # Bernstein basis of degree n-1
            basis_val = math.comb(self.degree - 1, i) * (t ** i) * ((1 - t) ** (self.degree - 1 - i))
            result = result + diff * (self.degree * basis_val)
            
        return result
    
    @property
    def start_point(self) -> Point:
        """First control point b_0 (start of curve)"""
        return self.control_points[0]
    
    @property
    def end_point(self) -> Point:
        """Last control point b_n (end of curve)"""
        return self.control_points[-1]
    
    def get_curve_points(self, num_points: int = 100) -> List[Point]:
        """
        Sample the Bézier curve at multiple parameter values.
        
        Args:
            num_points: Number of points to sample
            
        Returns:
            List of points along the curve
        """
        if num_points < 2:
            raise ValueError("Number of points must be at least 2")
            
        return [self.evaluate(t) for t in [i / (num_points - 1) for i in range(num_points)]]
    
    def __repr__(self) -> str:
        return f"BezierSegment(degree={self.degree}, control_points={len(self.control_points)})"
    
    def __eq__(self, other: object) -> bool:
        """Equality comparison for Bézier segments"""
        if not isinstance(other, BezierSegment):
            return False
        return (self.degree == other.degree and 
                self.control_points == other.control_points)