"""
Presenters for formatting and presenting tracing results.
Presenters convert application data into specific output formats like SVG.
"""

from .svg_presenter import SVGPresenter

__all__ = ["SVGPresenter"]