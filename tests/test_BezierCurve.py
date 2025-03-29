import unittest
import numpy as np
from sketchgetdp.bezier import BezierCurve


class TestBezierCurve(unittest.TestCase):
    def setUp(self):
        """Set up a BezierCurve instance for testing.
        """
        self.control_points = np.array([[0, 0], [1, 2], [2, 2], [3, 0]])
        self.bezier_curve = BezierCurve(self.control_points)

    def test_init(self):
        """Test the initialization of the BezierCurve class.
        """
        self.assertIsInstance(self.bezier_curve, BezierCurve)
        self.assertEqual(self.bezier_curve.degree, 3)

    def test_evaluate(self):
        """Test the evaluate method of the BezierCurve class.
        """
        t = np.array([0, 0.5, 1])
        expected_result = np.array([[0, 0], [1.5, 2], [3, 0]])
        result = self.bezier_curve.evaluate(t)
        self.assertTrue(np.allclose(result, expected_result))

    def test_evaluate_derivative(self):
        """Test the evaluate_derivative method of the BezierCurve class.
        """
        t = np.array([0, 0.5, 1])
        expected_result = np.array([[3, -6], [3, 0], [0, 0]])
        result = self.bezier_curve.evaluate_derivative(t)
        self.assertTrue(np.allclose(result, expected_result))