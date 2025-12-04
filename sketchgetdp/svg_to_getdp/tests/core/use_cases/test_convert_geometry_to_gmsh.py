"""
Pytest for the ConvertGeometryToGmsh use case.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
import yaml
from pathlib import Path

# Import core entities
from svg_to_getdp.core.entities.point import Point
from svg_to_getdp.core.entities.bezier_segment import BezierSegment
from svg_to_getdp.core.entities.boundary_curve import BoundaryCurve
from svg_to_getdp.core.entities.color import Color
from svg_to_getdp.core.entities.physical_group import (
    DOMAIN_VA, DOMAIN_VI_IRON, DOMAIN_VI_AIR, BOUNDARY_GAMMA, BOUNDARY_OUT,
    DOMAIN_COIL_POSITIVE, DOMAIN_COIL_NEGATIVE
)

# Import use case
from svg_to_getdp.core.use_cases.convert_geometry_to_gmsh import ConvertGeometryToGmsh

# Import REAL implementations instead of interfaces
from svg_to_getdp.infrastructure.boundary_curve_grouper import BoundaryCurveGrouper
from svg_to_getdp.infrastructure.boundary_curve_mesher import BoundaryCurveMesher
from svg_to_getdp.infrastructure.point_electrode_mesher import PointElectrodeMesher


@pytest.fixture
def sample_config_file():
    """Create a temporary config file for testing."""
    config_content = {
        "coil_currents": {
            "coil_1": 1,
            "coil_2": -1
        },
        "mesh_size": 0.1
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_content, f)
        temp_config_path = f.name
    
    yield temp_config_path
    
    # Cleanup
    if os.path.exists(temp_config_path):
        os.unlink(temp_config_path)


@pytest.fixture
def sample_boundary_curves():
    """Create sample boundary curves for testing."""
    bezier_segments = [
        BezierSegment([Point(0.0, 0.0), Point(0.5, 0.0), Point(1.0, 0.0)], degree=2),
        BezierSegment([Point(1.0, 0.0), Point(1.0, 1.0), Point(0.0, 1.0)], degree=2),
        BezierSegment([Point(0.0, 1.0), Point(0.0, 0.0), Point(0.0, 0.0)], degree=2),
    ]
    
    curve1 = BoundaryCurve(
        bezier_segments=bezier_segments,
        corners=[Point(0.0, 0.0), Point(1.0, 0.0), Point(1.0, 1.0), Point(0.0, 1.0)],
        color=Color.BLUE,
        is_closed=True
    )
    
    curve2 = BoundaryCurve(
        bezier_segments=[
            BezierSegment([Point(0.2, 0.2), Point(0.5, 0.2), Point(0.8, 0.2)], degree=2),
            BezierSegment([Point(0.8, 0.2), Point(0.8, 0.8), Point(0.2, 0.8)], degree=2),
            BezierSegment([Point(0.2, 0.8), Point(0.2, 0.2), Point(0.2, 0.2)], degree=2),
        ],
        corners=[Point(0.2, 0.2), Point(0.8, 0.2), Point(0.8, 0.8), Point(0.2, 0.8)],
        color=Color.GREEN,
        is_closed=True
    )
    
    return [curve1, curve2]


@pytest.fixture
def sample_point_electrodes():
    """Create sample point electrodes for testing."""
    return [
        (Point(0.3, 0.3), Color.RED),
        (Point(0.7, 0.7), Color.RED),
    ]


class TestConvertGeometryToGmsh:
    """Test cases for geometry to Gmsh conversion using pytest."""
    
    @pytest.fixture
    def mock_factory(self):
        """Create a mock factory for Gmsh operations."""
        return Mock()
    
    @pytest.fixture
    def boundary_curve_grouper(self):
        """Return real implementation instead of mock."""
        return BoundaryCurveGrouper()
    
    @pytest.fixture
    def boundary_curve_mesher(self):
        """Return real implementation WITHOUT factory - factory is passed to method."""
        return BoundaryCurveMesher()  # No factory in constructor
    
    @pytest.fixture
    def point_electrode_mesher(self):
        """Return real implementation WITHOUT factory - factory is passed to method."""
        return PointElectrodeMesher()  # No factory in constructor
    
    @pytest.fixture
    def converter(self, boundary_curve_grouper, boundary_curve_mesher, point_electrode_mesher):
        """Create the converter with real implementations."""
        return ConvertGeometryToGmsh(
            boundary_curve_grouper,
            boundary_curve_mesher,
            point_electrode_mesher
        )
    
    @pytest.fixture
    def mock_gmsh_toolbox(self):
        """Mock the Gmsh toolbox functions."""
        with patch('svg_to_getdp.core.use_cases.convert_geometry_to_gmsh.initialize_gmsh') as mock_init, \
             patch('svg_to_getdp.core.use_cases.convert_geometry_to_gmsh.set_characteristic_mesh_length') as mock_set_mesh, \
             patch('svg_to_getdp.core.use_cases.convert_geometry_to_gmsh.mesh_and_save') as mock_mesh_save, \
             patch('svg_to_getdp.core.use_cases.convert_geometry_to_gmsh.show_model') as mock_show, \
             patch('svg_to_getdp.core.use_cases.convert_geometry_to_gmsh.finalize_gmsh') as mock_finalize:
            
            mock_factory = Mock()
            mock_init.return_value = mock_factory
            
            yield {
                'initialize_gmsh': mock_init,
                'set_characteristic_mesh_length': mock_set_mesh,
                'mesh_and_save': mock_mesh_save,
                'show_model': mock_show,
                'finalize_gmsh': mock_finalize,
                'factory': mock_factory
            }
    
    def test_initialization(self, boundary_curve_grouper, boundary_curve_mesher, point_electrode_mesher):
        """Test that the use case initializes correctly with real implementations."""
        converter = ConvertGeometryToGmsh(
            boundary_curve_grouper,
            boundary_curve_mesher,
            point_electrode_mesher
        )
        
        assert converter.boundary_curve_grouper == boundary_curve_grouper
        assert converter.boundary_curve_mesher == boundary_curve_mesher
        assert converter.point_electrode_mesher == point_electrode_mesher
        assert isinstance(converter.boundary_curve_grouper, BoundaryCurveGrouper)
        assert isinstance(converter.boundary_curve_mesher, BoundaryCurveMesher)
        assert isinstance(converter.point_electrode_mesher, PointElectrodeMesher)
    
    def test_execute_successful_conversion(
        self, converter, sample_boundary_curves, sample_point_electrodes, 
        sample_config_file, mock_gmsh_toolbox
    ):
        """Test successful execution of the geometry to Gmsh conversion."""
        # Setup mocks for Gmsh functions (still need to mock Gmsh itself)
        mock_gmsh_toolbox['initialize_gmsh'].return_value = mock_gmsh_toolbox['factory']
        
        # Mock the methods of the real implementations
        # Since we're using real classes, we need to patch their methods
        with patch.object(converter.point_electrode_mesher, 'mesh_electrodes') as mock_mesh_electrodes, \
             patch.object(converter.boundary_curve_grouper, 'group_boundary_curves') as mock_group_boundary_curves, \
             patch.object(converter.boundary_curve_mesher, 'mesh_boundary_curves') as mock_mesh_boundary_curves:
            
            # Setup return values
            electrode_results = {
                0: {
                    'original_index': 0,
                    'point': Point(0.3, 0.3),
                    'color': Color.RED,
                    'gmsh_point_tag': 1,
                    'physical_group': DOMAIN_COIL_POSITIVE,
                    'coil_name': 'coil_1'
                },
                1: {
                    'original_index': 1,
                    'point': Point(0.7, 0.7),
                    'color': Color.RED,
                    'gmsh_point_tag': 2,
                    'physical_group': DOMAIN_COIL_NEGATIVE,
                    'coil_name': 'coil_2'
                }
            }
            mock_mesh_electrodes.return_value = electrode_results
            
            grouping_result = [
                {
                    "holes": [1],  # Curve 1 contains curve 2 as a hole
                    "physical_groups": [DOMAIN_VI_IRON, BOUNDARY_OUT]
                },
                {
                    "holes": [],
                    "physical_groups": [DOMAIN_VI_AIR]
                }
            ]
            mock_group_boundary_curves.return_value = grouping_result
            
            # Execute with updated parameter order
            result = converter.execute(
                boundary_curves=sample_boundary_curves,
                point_electrodes=sample_point_electrodes,
                config_file_path=sample_config_file,
                model_name="test_model",
                output_filename="test_mesh",
                mesh_size=0.05,
                dimension=2,
                show_gui=False
            )
            
            # Assert
            # Verify Gmsh initialization
            mock_gmsh_toolbox['initialize_gmsh'].assert_called_once_with("test_model")
            
            # Verify mesh size setting
            mock_gmsh_toolbox['set_characteristic_mesh_length'].assert_called_once_with(0.05)
            
            # Verify point electrode processing
            mock_mesh_electrodes.assert_called_once_with(
                mock_gmsh_toolbox['factory'],  # factory first
                sample_config_file,            # config_path second
                sample_point_electrodes,       # electrodes third
                point_size=0.05                # point_size (using mesh_size)
            )
            
            # Verify boundary curve grouping
            mock_group_boundary_curves.assert_called_once_with(sample_boundary_curves)
            
            # Verify boundary curve meshing
            mock_mesh_boundary_curves.assert_called_once_with(
                mock_gmsh_toolbox['factory'],  # factory first
                sample_boundary_curves,
                grouping_result
            )
            
            # Verify synchronization
            mock_gmsh_toolbox['factory'].synchronize.assert_called_once()
            
            # Verify mesh generation
            mock_gmsh_toolbox['mesh_and_save'].assert_called_once_with("test_mesh", 2)
            
            # Verify GUI not shown
            mock_gmsh_toolbox['show_model'].assert_not_called()
            
            # Verify finalization
            mock_gmsh_toolbox['finalize_gmsh'].assert_called_once()
            
            # Verify result structure
            assert result["model_name"] == "test_model"
            assert result["output_filename"] == "test_mesh"
            assert result["mesh_size"] == 0.05
            assert result["dimension"] == 2
            assert result["factory_initialized"] is True
            assert result["mesh_size_set"] is True
            assert result["electrode_results"] == electrode_results
            assert result["grouping_result"] == grouping_result
            assert result["boundary_mesher"] == converter.boundary_curve_mesher
            assert result["geometry_synchronized"] is True
            assert result["mesh_generated"] is True
            assert "gui_shown" not in result  # Since show_gui=False
    
    def test_execute_with_gui(
        self, converter, sample_boundary_curves, sample_point_electrodes, 
        sample_config_file, mock_gmsh_toolbox
    ):
        """Test execution with GUI enabled."""
        # Setup mocks
        mock_gmsh_toolbox['initialize_gmsh'].return_value = mock_gmsh_toolbox['factory']
        
        with patch.object(converter.point_electrode_mesher, 'mesh_electrodes') as mock_mesh_electrodes, \
             patch.object(converter.boundary_curve_grouper, 'group_boundary_curves') as mock_group_boundary_curves, \
             patch.object(converter.boundary_curve_mesher, 'mesh_boundary_curves') as mock_mesh_boundary_curves:
            
            mock_mesh_electrodes.return_value = {}
            mock_group_boundary_curves.return_value = []
            
            # Execute with show_gui=True
            result = converter.execute(
                boundary_curves=sample_boundary_curves,
                point_electrodes=sample_point_electrodes,
                config_file_path=sample_config_file,
                model_name="test_model",
                output_filename="test_mesh",
                mesh_size=0.05,
                dimension=2,
                show_gui=True  # GUI enabled
            )
            
            # Verify GUI was shown
            mock_gmsh_toolbox['show_model'].assert_called_once()
            assert result["gui_shown"] is True
    
    def test_invalid_boundary_curves_type(self, converter, sample_point_electrodes, sample_config_file):
        """Test error when boundary_curves is not a list."""
        with pytest.raises(ValueError, match="boundary_curves must be a list"):
            converter.execute(
                boundary_curves="not a list",  # Invalid type
                point_electrodes=sample_point_electrodes,
                config_file_path=sample_config_file
            )
    
    def test_invalid_point_electrodes_type(self, converter, sample_boundary_curves, sample_config_file):
        """Test error when point_electrodes is not a list."""
        with pytest.raises(ValueError, match="point_electrodes must be a list"):
            converter.execute(
                boundary_curves=sample_boundary_curves,
                point_electrodes="not a list",  # Invalid type
                config_file_path=sample_config_file
            )
    
    def test_config_file_not_found(self, converter, sample_boundary_curves, sample_point_electrodes):
        """Test error when config file doesn't exist."""
        non_existent_config = "/path/to/nonexistent/config.yaml"
        
        with pytest.raises(FileNotFoundError, match=f"Configuration file not found: {non_existent_config}"):
            converter.execute(
                boundary_curves=sample_boundary_curves,
                point_electrodes=sample_point_electrodes,
                config_file_path=non_existent_config
            )
    
    def test_empty_boundary_curves_warning(
        self, converter, sample_point_electrodes, sample_config_file, mock_gmsh_toolbox
    ):
        """Test warning when no boundary curves are provided."""
        # Setup mocks
        mock_gmsh_toolbox['initialize_gmsh'].return_value = mock_gmsh_toolbox['factory']
        
        with patch.object(converter.point_electrode_mesher, 'mesh_electrodes') as mock_mesh_electrodes, \
             patch.object(converter.boundary_curve_grouper, 'group_boundary_curves') as mock_group_boundary_curves, \
             patch.object(converter.boundary_curve_mesher, 'mesh_boundary_curves') as mock_mesh_boundary_curves, \
             patch('builtins.print') as mock_print:
            
            mock_mesh_electrodes.return_value = {}
            mock_group_boundary_curves.return_value = []
            
            # Execute with empty boundary curves
            result = converter.execute(
                boundary_curves=[],  # Empty list
                point_electrodes=sample_point_electrodes,
                config_file_path=sample_config_file,
                show_gui=False
            )
            
            # Verify warning was printed
            mock_print.assert_any_call("Warning: No boundary curves provided")
            
            # Verify grouping was still called with empty list
            mock_group_boundary_curves.assert_called_once_with([])
    
    def test_exception_handling(
        self, converter, sample_boundary_curves, sample_point_electrodes, 
        sample_config_file, mock_gmsh_toolbox
    ):
        """Test that exceptions are properly handled and Gmsh is finalized."""
        # Setup mocks to raise an exception
        mock_gmsh_toolbox['initialize_gmsh'].return_value = mock_gmsh_toolbox['factory']
        
        with patch.object(converter.point_electrode_mesher, 'mesh_electrodes') as mock_mesh_electrodes:
            # Make mesh_electrodes raise an exception
            mock_mesh_electrodes.side_effect = RuntimeError("Test error")
            
            # Execute and expect exception
            with pytest.raises(RuntimeError, match="Test error"):
                converter.execute(
                    boundary_curves=sample_boundary_curves,
                    point_electrodes=sample_point_electrodes,
                    config_file_path=sample_config_file,
                    show_gui=False
                )
            
            # Verify Gmsh was finalized even after exception
            mock_gmsh_toolbox['finalize_gmsh'].assert_called_once()


class TestConvertGeometryToGmshIntegration:
    """Integration-style tests with real implementations."""
    
    @pytest.fixture
    def converter(self, sample_config_file):
        """Create converter with real implementations."""
        grouper = BoundaryCurveGrouper()
        mesher = BoundaryCurveMesher()  # No factory in constructor
        electrode_mesher = PointElectrodeMesher()  # No factory in constructor
        
        return ConvertGeometryToGmsh(grouper, mesher, electrode_mesher)
    
    def test_real_implementations_instantiation(self, converter):
        """Verify that real implementations are used."""
        assert isinstance(converter.boundary_curve_grouper, BoundaryCurveGrouper)
        assert isinstance(converter.boundary_curve_mesher, BoundaryCurveMesher)
        assert isinstance(converter.point_electrode_mesher, PointElectrodeMesher)
    
    def test_execute_with_real_implementations(
        self, converter, sample_boundary_curves, sample_point_electrodes, sample_config_file
    ):
        """Test execution with real implementations (still mocking Gmsh)."""
        # Mock Gmsh functions since we don't want to actually run Gmsh
        with patch('svg_to_getdp.core.use_cases.convert_geometry_to_gmsh.initialize_gmsh') as mock_init, \
            patch('svg_to_getdp.core.use_cases.convert_geometry_to_gmsh.set_characteristic_mesh_length') as mock_set_mesh, \
            patch('svg_to_getdp.core.use_cases.convert_geometry_to_gmsh.mesh_and_save') as mock_mesh_save, \
            patch('svg_to_getdp.core.use_cases.convert_geometry_to_gmsh.show_model') as mock_show, \
            patch('svg_to_getdp.core.use_cases.convert_geometry_to_gmsh.finalize_gmsh'):
            
            # Mock factory
            mock_factory = Mock()
            mock_factory.synchronize = Mock()
            mock_init.return_value = mock_factory
            
            # Mock methods of the real implementations to control behavior
            with patch.object(converter.point_electrode_mesher, 'mesh_electrodes') as mock_mesh_electrodes, \
                patch.object(converter.boundary_curve_grouper, 'group_boundary_curves') as mock_group_boundary_curves, \
                patch.object(converter.boundary_curve_mesher, 'mesh_boundary_curves') as mock_mesh_boundary_curves:
                
                # Setup return values
                mock_mesh_electrodes.return_value = {}
                mock_group_boundary_curves.return_value = []
                
                # Execute
                result = converter.execute(
                    boundary_curves=sample_boundary_curves,
                    point_electrodes=sample_point_electrodes,
                    config_file_path=sample_config_file,
                    show_gui=False
                )
                
                # Verify interactions
                mock_mesh_electrodes.assert_called_once_with(
                    mock_factory,
                    sample_config_file,
                    sample_point_electrodes,
                    point_size=0.1
                )
                mock_group_boundary_curves.assert_called_once()
                mock_mesh_boundary_curves.assert_called_once_with(
                    mock_factory,
                    sample_boundary_curves,
                    []
                )
                mock_factory.synchronize.assert_called_once()
                mock_mesh_save.assert_called_once()
                
                assert result["mesh_generated"] is True