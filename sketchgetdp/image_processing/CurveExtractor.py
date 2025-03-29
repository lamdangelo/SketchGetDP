""" This module is used to extract the curve(s) from a given image.

Author: Laura D'Angelo
"""

from PIL import Image 
import numpy as np
import matplotlib.pyplot as plt


class CurveExtractor:
    """ This class is used to extract the curve(s) from a given image.

    Attributes:
        image_path (str): The path to the image file.
        image (PIL.Image): The image object.
        image_array (np.array): The image as a numpy array.
        curve (np.array): The x- and y-coordinates of the extracted curve, normalized to [0, 1]².
    """

    def __init__(self, image_path: str) -> "CurveExtractor":
        """ The constructor for the CurveExtractor class. Reads an image file found at the path 
        image_path.

        Parameters:
            image_path (str): The path to the image file.
        """
        self.image_path = image_path
        self.image = Image.open(self.image_path)
        self.image_array = np.array(self.image)
        self.curve = None


    def extract_curve(self) -> np.array:
        """ This method extracts the curve from the image by converting the image to a binary image,
        then to a binary array, from which the coordinates of the curve are extracted and normalized.

        Returns:
            np.array: The x- and y-coordinates of the extracted curve, normalized to [0, 1]².
        """
        # Convert the image to binary image
        binary_image = self.image.convert('1', dither=Image.NONE)

        # Convert the binary image to a numpy array. Black pixels are 0 and white pixels are 1, 
        # so we need to negate the binary array.
        binary_array = np.array(binary_image)
        negated_binary_array = np.logical_not(binary_array)

        # Extract the curve and normalize the coordinates to [0, 1]
        indices_row, indices_col = np.where(negated_binary_array)
        image_size_x = np.size(negated_binary_array, 0)
        image_size_y = np.size(negated_binary_array, 1)
        x_coordinates = indices_row / image_size_x
        y_coordinates = indices_col / image_size_y
        curve = np.array([x_coordinates, y_coordinates]).T

        self.curve = curve
        return curve
    

    def plot_curve(self):
        """ This method plots the extracted normalized curve on a xy-plane.

        Returns:
            None
        """
        # Check if the curve has already been extracted. If not, extract the curve before plotting.
        if self.curve is None:
            self.extract_curve()

        # Plot the curve
        plt.plot(self.curve[:, 1], self.curve[:, 0], 'x')
        plt.show()
        