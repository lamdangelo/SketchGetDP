"""
Unit tests for ConvertGeometryToGmsh use case.

Tests geometry to Gmsh conversion functionality with various outlines,
wire configurations, and edge cases.
"""

import os
import tempfile
import time
from unittest.mock import Mock, patch
import pytest
import yaml

from svg_to_getdp.core.entities.point import Point
from svg_to_getdp.core.entities.bezier_segment import BezierSegment
from sketchgetdp.svg_to_getdp.core.entities.outline import Outline
from svg_to_getdp.core.entities.color import Color
from svg_to_getdp.core.entities.physical_group import (
    DOMAIN_VI_IRON,
    DOMAIN_VI_AIR,
    BOUNDARY_OUT,
    DOMAIN_COIL_POSITIVE,
    DOMAIN_COIL_NEGATIVE,
)
from svg_to_getdp.core.use_cases.convert_geometry_to_gmsh import ConvertGeometryToGmsh
from sketchgetdp.svg_to_getdp.infrastructure.outline_grouper import OutlineGrouper
from sketchgetdp.svg_to_getdp.infrastructure.outline_preprocessor import OutlinePreprocessor
from sketchgetdp.svg_to_getdp.infrastructure.wire_preprocessor import WirePreprocessor


class TestConvertGeometryToGmsh:
    """Test suite for ConvertGeometryToGmsh class."""

    # ==================== Fixtures ====================

    @pytest.fixture
    def outline_grouper(self):
        """Create an OutlineGrouper instance for testing."""
        return OutlineGrouper()
    
    @pytest.fixture
    def outline_preprocessor(self):
        """Create an OutlinePreprocessor instance for testing."""
        return OutlinePreprocessor()

    @pytest.fixture
    def wire_preprocessor(self):
        """Create a WirePreprocessor instance for testing."""
        return WirePreprocessor()
    
    @pytest.fixture
    def converter(self, outline_grouper, outline_preprocessor, wire_preprocessor):
        """Create a ConvertGeometryToGmsh instance for testing."""
        return ConvertGeometryToGmsh(
            outline_grouper, outline_preprocessor, wire_preprocessor
        )
    
    @pytest.fixture
    def temporary_configuration_file(self):
        """Create a temporary configuration file for testing."""
        configuration = {
            "wire_currents": {"wire_1": 1, "wire_2": -1},
            "mesh_size": 0.1,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as file:
            yaml.dump(configuration, file)
            config_path = file.name

        yield config_path

        if os.path.exists(config_path):
            os.unlink(config_path)
    
    @pytest.fixture
    def sample_outlines(self):
        """Create sample outlines for testing."""
        outer_outline = Outline(
            bezier_segments=[
                BezierSegment(
                    [Point(0.0, 0.0), Point(0.5, 0.0), Point(1.0, 0.0)], degree=2
                ),
                BezierSegment(
                    [Point(1.0, 0.0), Point(1.0, 1.0), Point(0.0, 1.0)], degree=2
                ),
                BezierSegment(
                    [Point(0.0, 1.0), Point(0.0, 0.0), Point(0.0, 0.0)], degree=2
                ),
            ],
            corners=[
                Point(0.0, 0.0),
                Point(1.0, 0.0),
                Point(1.0, 1.0),
                Point(0.0, 1.0),
            ],
            color=Color.BLUE,
            is_closed=True,
        )

        inner_outline = Outline(
            bezier_segments=[
                BezierSegment(
                    [Point(0.2, 0.2), Point(0.5, 0.2), Point(0.8, 0.2)], degree=2
                ),
                BezierSegment(
                    [Point(0.8, 0.2), Point(0.8, 0.8), Point(0.2, 0.8)], degree=2
                ),
                BezierSegment(
                    [Point(0.2, 0.8), Point(0.2, 0.2), Point(0.2, 0.2)], degree=2
                ),
            ],
            corners=[
                Point(0.2, 0.2),
                Point(0.8, 0.2),
                Point(0.8, 0.8),
                Point(0.2, 0.8),
            ],
            color=Color.GREEN,
            is_closed=True,
        )

        return [outer_outline, inner_outline]
    
    @pytest.fixture
    def sample_wires(self):
        """Create sample wire points for testing."""
        return [
            (Point(0.3, 0.3), Color.RED),
            (Point(0.7, 0.7), Color.RED),
        ]
    
    @pytest.fixture
    def gmsh_mocks(self):
        """Mock all Gmsh toolbox functions."""
        with patch(
            "svg_to_getdp.core.use_cases.convert_geometry_to_gmsh.initialize_gmsh"
        ) as mock_init, patch(
            "svg_to_getdp.core.use_cases.convert_geometry_to_gmsh.set_characteristic_mesh_length"
        ) as mock_set_mesh, patch(
            "svg_to_getdp.core.use_cases.convert_geometry_to_gmsh.mesh_and_save"
        ) as mock_mesh_save, patch(
            "svg_to_getdp.core.use_cases.convert_geometry_to_gmsh.show_model"
        ) as mock_show, patch(
            "svg_to_getdp.core.use_cases.convert_geometry_to_gmsh.finalize_gmsh"
        ) as mock_finalize:

            mock_factory = Mock()
            mock_factory.synchronize = Mock()
            mock_init.return_value = mock_factory

            yield {
                "initialize_gmsh": mock_init,
                "set_characteristic_mesh_length": mock_set_mesh,
                "mesh_and_save": mock_mesh_save,
                "show_model": mock_show,
                "finalize_gmsh": mock_finalize,
                "factory": mock_factory,
            }
    
    @pytest.fixture
    def many_outlines(self):
        """Create many outlines for performance testing."""
        many_outlines = []
        for i in range(10):
            bezier_segments = [
                BezierSegment(
                    [Point(i, i), Point(i + 1, i), Point(i + 1, i + 1)], degree=2
                ),
                BezierSegment(
                    [Point(i + 1, i + 1), Point(i, i + 1), Point(i, i)], degree=2
                ),
            ]
            outline = Outline(
                bezier_segments=bezier_segments,
                corners=[
                    Point(i, i),
                    Point(i + 1, i),
                    Point(i + 1, i + 1),
                    Point(i, i + 1),
                ],
                color=Color.BLUE,
                is_closed=True,
            )
            many_outlines.append(outline)
        return many_outlines

    # ==================== Initialization Tests ====================

    def test_initializes_with_dependencies(
        self, outline_grouper, outline_preprocessor, wire_preprocessor
    ):
        """Test that converter initializes with all dependencies."""
        converter = ConvertGeometryToGmsh(
            outline_grouper, outline_preprocessor, wire_preprocessor
        )

        assert converter.outline_grouper == outline_grouper
        assert converter.outline_preprocessor == outline_preprocessor
        assert converter.wire_preprocessor == wire_preprocessor

    # ==================== Basic Functionality Tests ====================

    def test_executes_successfully(
        self,
        converter,
        sample_outlines,
        sample_wires,
        temporary_configuration_file,
        gmsh_mocks,
    ):
        """Test successful execution of the geometry to Gmsh conversion."""
        with patch.object(
            converter.wire_preprocessor, "prepare_wires"
        ) as mock_prepare_wires, patch.object(
            converter.outline_grouper, "group_outlines"
        ) as mock_group_outlines, patch.object(
            converter.outline_preprocessor, "preprocess_outlines"
        ) as mock_preprocess_outlines:

            wire_results = {
                0: {
                    "original_index": 0,
                    "point": Point(0.3, 0.3),
                    "color": Color.RED,
                    "gmsh_point_tag": 1,
                    "physical_group": DOMAIN_COIL_POSITIVE,
                    "wire_name": "wire_1",
                },
                1: {
                    "original_index": 1,
                    "point": Point(0.7, 0.7),
                    "color": Color.RED,
                    "gmsh_point_tag": 2,
                    "physical_group": DOMAIN_COIL_NEGATIVE,
                    "wire_name": "wire_2",
                },
            }
            mock_prepare_wires.return_value = wire_results

            grouping_result = [
                {
                    "holes": [1],
                    "physical_groups": [DOMAIN_VI_IRON, BOUNDARY_OUT],
                },
                {"holes": [], "physical_groups": [DOMAIN_VI_AIR]},
            ]
            mock_group_outlines.return_value = grouping_result

            result = converter.execute(
                outlines=sample_outlines,
                wires=sample_wires,
                config_file_path=temporary_configuration_file,
                model_name="test_model",
                output_filename="test_mesh",
                dimension=2,
                show_gui=False,
            )

            # Verify Gmsh initialization
            gmsh_mocks["initialize_gmsh"].assert_called_once_with("test_model")
            gmsh_mocks["set_characteristic_mesh_length"].assert_called_once_with(0.1)

            # Verify dependencies are called correctly
            mock_prepare_wires.assert_called_once_with(
                gmsh_mocks["factory"],
                temporary_configuration_file,
                sample_wires,
            )
            mock_group_outlines.assert_called_once_with(sample_outlines)
            mock_preprocess_outlines.assert_called_once_with(
                gmsh_mocks["factory"], sample_outlines, grouping_result
            )

            # Verify Gmsh operations
            gmsh_mocks["factory"].synchronize.assert_called_once()
            gmsh_mocks["mesh_and_save"].assert_called_once_with("test_mesh", 2)
            gmsh_mocks["show_model"].assert_not_called()
            gmsh_mocks["finalize_gmsh"].assert_called_once()

            # Verify result structure
            assert result["model_name"] == "test_model"
            assert result["output_filename"] == "test_mesh"
            assert result["mesh_size"] == 0.1
            assert result["wire_results"] == wire_results
            assert result["geometry_synchronized"] is True
            assert result["mesh_generated"] is True
            assert "gui_shown" not in result

    def test_executes_with_gui(
        self,
        converter,
        sample_outlines,
        sample_wires,
        temporary_configuration_file,
        gmsh_mocks,
    ):
        """Test execution with GUI display enabled."""
        with patch.object(
            converter.wire_preprocessor, "prepare_wires"
        ) as mock_prepare_wires, patch.object(
            converter.outline_grouper, "group_outlines"
        ) as mock_group_outlines, patch.object(
            converter.outline_preprocessor, "preprocess_outlines"
        ) as mock_preprocess_outlines:

            mock_prepare_wires.return_value = {}
            mock_group_outlines.return_value = []

            result = converter.execute(
                outlines=sample_outlines,
                wires=sample_wires,
                config_file_path=temporary_configuration_file,
                model_name="test_model",
                output_filename="test_mesh",
                dimension=2,
                show_gui=True,
            )

            gmsh_mocks["show_model"].assert_called_once()
            assert result["gui_shown"] is True

    # ==================== Edge Case Tests ====================

    def test_warns_when_no_outlines_provided(
        self, converter, sample_wires, temporary_configuration_file, gmsh_mocks
    ):
        """Test warning when no outlines are provided."""
        with patch.object(
            converter.wire_preprocessor, "prepare_wires"
        ) as mock_prepare_wires, patch.object(
            converter.outline_grouper, "group_outlines"
        ) as mock_group_outlines, patch.object(
            converter.outline_preprocessor, "preprocess_outlines"
        ) as mock_preprocess_outlines, patch(
            "builtins.print"
        ) as mock_print:

            mock_prepare_wires.return_value = {}
            mock_group_outlines.return_value = []

            converter.execute(
                outlines=[],
                wires=sample_wires,
                config_file_path=temporary_configuration_file,
                show_gui=False,
            )

            mock_print.assert_any_call("Warning: No outlines provided")

    def test_handles_different_mesh_sizes(
        self, converter, sample_outlines, sample_wires, gmsh_mocks
    ):
        """Test handling of different mesh sizes from configuration."""
        configuration = {
            "wire_currents": {"wire_1": 1, "wire_2": -1},
            "mesh_size": 0.05,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as file:
            yaml.dump(configuration, file)
            config_path = file.name

        try:
            with patch.object(
                converter.wire_preprocessor, "prepare_wires"
            ) as mock_prepare_wires, patch.object(
                converter.outline_grouper, "group_outlines"
            ) as mock_group_outlines, patch.object(
                converter.outline_preprocessor, "preprocess_outlines"
            ) as mock_preprocess_outlines:

                mock_prepare_wires.return_value = {}
                mock_group_outlines.return_value = []

                result = converter.execute(
                    outlines=sample_outlines,
                    wires=sample_wires,
                    config_file_path=config_path,
                    show_gui=False,
                )

                gmsh_mocks["set_characteristic_mesh_length"].assert_called_once_with(
                    0.05
                )
                assert result["mesh_size"] == 0.05
        finally:
            if os.path.exists(config_path):
                os.unlink(config_path)

    # ==================== Error Handling Tests ====================

    def test_rejects_invalid_outline_type(
        self, converter, sample_wires, temporary_configuration_file
    ):
        """Test rejection of invalid outlines type."""
        with pytest.raises(ValueError, match="outlines must be a list"):
            converter.execute(
                outlines="not a list",
                wires=sample_wires,
                config_file_path=temporary_configuration_file,
            )

    def test_rejects_invalid_wires_type(
        self, converter, sample_outlines, temporary_configuration_file
    ):
        """Test rejection of invalid wires type."""
        with pytest.raises(ValueError, match="wires must be a list"):
            converter.execute(
                outlines=sample_outlines,
                wires="not a list",
                config_file_path=temporary_configuration_file,
            )

    def test_rejects_nonexistent_configuration_file(
        self, converter, sample_outlines, sample_wires
    ):
        """Test rejection of nonexistent configuration file."""
        nonexistent_config = "/path/to/nonexistent/config.yaml"

        with pytest.raises(
            FileNotFoundError,
            match=f"Configuration file not found: {nonexistent_config}",
        ):
            converter.execute(
                outlines=sample_outlines,
                wires=sample_wires,
                config_file_path=nonexistent_config,
            )

    def test_handles_exceptions_gracefully(
        self,
        converter,
        sample_outlines,
        sample_wires,
        temporary_configuration_file,
        gmsh_mocks,
    ):
        """Test graceful handling of exceptions during execution."""
        with patch.object(
            converter.wire_preprocessor, "prepare_wires"
        ) as mock_prepare_wires:
            mock_prepare_wires.side_effect = RuntimeError("Test error")

            with pytest.raises(RuntimeError, match="Test error"):
                converter.execute(
                    outlines=sample_outlines,
                    wires=sample_wires,
                    config_file_path=temporary_configuration_file,
                    show_gui=False,
                )

            gmsh_mocks["finalize_gmsh"].assert_called_once()

    # ==================== Integration Tests ====================

    def test_produces_consistent_results_across_runs(
        self,
        converter,
        sample_outlines,
        sample_wires,
        temporary_configuration_file,
        gmsh_mocks,
    ):
        """Test consistent results across multiple execution runs."""
        results = []

        with patch.object(
            converter.wire_preprocessor, "prepare_wires"
        ) as mock_prepare_wires, patch.object(
            converter.outline_grouper, "group_outlines"
        ) as mock_group_outlines, patch.object(
            converter.outline_preprocessor, "preprocess_outlines"
        ) as mock_preprocess_outlines:

            mock_prepare_wires.return_value = {}
            mock_group_outlines.return_value = []

            for _ in range(3):
                result = converter.execute(
                    outlines=sample_outlines,
                    wires=sample_wires,
                    config_file_path=temporary_configuration_file,
                    show_gui=False,
                )
                results.append(result)

        for i in range(1, len(results)):
            assert results[i].keys() == results[0].keys()

    # ==================== Performance Tests ====================

    def test_handles_many_outlines_efficiently(
        self, converter, sample_wires, temporary_configuration_file, gmsh_mocks, many_outlines
    ):
        """Test efficient handling of many outlines."""
        with patch.object(
            converter.wire_preprocessor, "prepare_wires"
        ) as mock_prepare_wires, patch.object(
            converter.outline_grouper, "group_outlines"
        ) as mock_group_outlines, patch.object(
            converter.outline_preprocessor, "preprocess_outlines"
        ) as mock_preprocess_outlines:

            mock_prepare_wires.return_value = {}
            mock_group_outlines.return_value = []

            start_time = time.time()
            result = converter.execute(
                outlines=many_outlines,
                wires=sample_wires,
                config_file_path=temporary_configuration_file,
                show_gui=False,
            )
            end_time = time.time()

            assert end_time - start_time < 5.0
            assert result["mesh_generated"] is True
            