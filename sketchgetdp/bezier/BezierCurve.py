""" This module contains the BezierCurve class, which represents a single Bézier curve.

Author: Laura D'Angelo
"""

import math
import matplotlib.pyplot as plt
import numpy as np


class BezierCurve:
    """ This class represents a single Bézier curve.

    Attributes:
        control_points (np.array): A (degree+1) x 2 array of control points for the Bézier curve.
        degree (int): The degree of the Bézier curve.
    """

    def __init__(self, control_points: np.array) -> "BezierCurve":
        """ The constructor for the BezierCurve class.

        Parameters:
            control_points (np.array): An array of control points for the Bézier curve.
        """
        self.control_points = control_points
        self.degree = np.size(control_points, 0) - 1

    def evaluate(self, t: np.array) -> np.array:
        """ This method evaluates the Bézier curve at given parameters t.

        Parameters:
            t (np.array): The parameters at which to evaluate the Bézier curve.

        Returns:
            np.array: The evaluated points on the Bézier curve.
        """
        # Ensure t has the correct shape
        if np.size(t, 0) < np.size(t, 1):
            t = np.transpose(t)

        # Evaluate the Bézier curve using the Bernstein polynomial
        value = np.zeros((np.size(t, 0), 2))
        n = self.degree
        for i in range(n + 1):
            value += math.comb(n, i) * t**i * (1 - t)**(n - i) * self.control_points[i, :]
        return value 
    
    def evaluate_derivative(self, t: np.array) -> np.array:
        """ This method evaluates the derivative of the Bézier curve at given parameters t.

        Parameters:
            t (np.array): The parameters at which to evaluate the derivative of the Bézier curve.

        Returns:
            np.array: The evaluated points on the derivative of the Bézier curve.
        """
        # Ensure t has the correct shape
        if np.size(t, 0) < np.size(t, 1):
            t = np.transpose(t)

        # Evaluate the derivative of the Bézier curve 
        value = np.zeros((np.size(t, 1), 2))
        n = self.degree
        for i in range(n):
            value += math.comb(n-1, i) * t**i * (1 - t)**(n - i - 1) * (self.control_points[:, i+1] -
                                                                        self.control_points[:, i])
        return value
    
    def plot(self) -> None:
        """ This method plots the Bézier curve and its control polygon.

        Returns:
            None
        """
        t = np.linspace(0, 1, 100)[:, np.newaxis]
        evaluated_points = self.evaluate(t)
        plt.plot(evaluated_points[:, 0], evaluated_points[:, 1], label='Bézier Curve')
        plt.plot(self.control_points[:, 0], self.control_points[:, 1], 'ro--', label='Control Points')
        plt.legend()
        plt.show()