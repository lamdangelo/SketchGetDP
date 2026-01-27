"""
Unit tests for RunGetDPSimulation use case.
"""

import pytest
from unittest.mock import Mock, patch, mock_open
import yaml
import numpy as np

from svg_to_getdp.core.use_cases.run_getdp_simulation import RunGetDPSimulation


class TestRunGetDPSimulation:
    """Test suite for RunGetDPSimulation class."""

    # ==================== Helper Methods ====================

    def _create_default_physical_values(self):
        """Create default physical values for testing."""
        return {
            "Isource": 1,
            "mu0": 4e-7 * np.pi,
            "nu0": 1/(4e-7 * np.pi),
            "nu_iron_linear": 1/(4000 * 4e-7 * np.pi)
        }

    def _assert_physical_values_equal(self, actual, expected, keys=None):
        """Assert that physical values match expected values for given keys."""
        if keys is None:
            keys = ["Isource", "mu0", "nu0", "nu_iron_linear"]
        
        for key in keys:
            if key in expected:
                if isinstance(expected[key], (int, float)):
                    assert actual[key] == pytest.approx(expected[key])
                else:
                    assert actual[key] == expected[key]

    def _mock_use_case_internals(self, use_case, config_data=None, physical_values=None):
        """Context manager to mock internal methods of RunGetDPSimulation."""
        class MockInternals:
            def __init__(self, use_case, config_data=None, physical_values=None):
                self.use_case = use_case
                self.config_data = config_data or {}
                self.physical_values = physical_values or self._create_default_physical_values()
                
            def _create_default_physical_values(self):
                # Use the class method
                return TestRunGetDPSimulation._create_default_physical_values(self)
                
            def __enter__(self):
                self.mock_gmsh = patch.object(self.use_case, '_initialize_gmsh').start()
                self.mock_load_config = patch.object(self.use_case, '_load_config_yaml').start()
                self.mock_run_sim = patch.object(self.use_case, '_run_simulation').start()
                
                self.mock_load_config.return_value = self.config_data
                
                # Mock _define_physical_values to set the values
                self.mock_define = patch.object(self.use_case, '_define_physical_values').start()
                self.mock_define.side_effect = lambda _: setattr(
                    self.use_case, 'physical_values', self.physical_values.copy()
                )
                
                return self
                
            def __exit__(self, *args):
                patch.stopall()
        
        return MockInternals(use_case, config_data, physical_values)

    # ==================== Fixtures ====================

    @pytest.fixture
    def use_case(self):
        """Create a RunGetDPSimulation instance for testing."""
        return RunGetDPSimulation()

    @pytest.fixture
    def mock_all_externals(self):
        """Mock all external dependencies."""
        with patch('svg_to_getdp.core.use_cases.run_getdp_simulation.print_data_to_pro') as mock_print, \
             patch('svg_to_getdp.core.use_cases.run_getdp_simulation.run_magnetostatic_simulation') as mock_run_sim, \
             patch('svg_to_getdp.core.use_cases.run_getdp_simulation.physical_identifiers') as mock_phys_ids:
            mock_phys_ids.return_value = {"test_id": 1}
            yield mock_print, mock_run_sim, mock_phys_ids

    @pytest.fixture
    def mock_gmsh(self):
        """Mock Gmsh module."""
        gmsh_mock = Mock()
        gmsh_mock.initialize.return_value = None
        gmsh_mock.finalize.return_value = None
        return gmsh_mock

    # ==================== Initialization Tests ====================

    def test_init(self, use_case):
        """Test initialization of RunGetDPSimulation."""
        assert use_case.physical_values is None

    # ==================== Basic Functionality Tests ====================

    def test_get_physical_values_no_values(self, use_case):
        """Test get_physical_values when no values are defined."""
        result = use_case.get_physical_values()
        assert result == {}

    def test_get_physical_values_after_definition(self, use_case):
        """Test get_physical_values returns a copy of values."""
        config_data = {
            "physical_values": {
                "Isource": 5,
                "mu0": 1.0e-6
            }
        }
        
        use_case._define_physical_values(config_data)
        
        # Get values and modify the result
        returned_values = use_case.get_physical_values()
        returned_values["Isource"] = 100
        
        # Original should not be modified
        assert use_case.physical_values["Isource"] == 5
        assert returned_values["Isource"] == 100

    # ==================== Configuration Loading Tests ====================

    def test_load_config_yaml_success(self, use_case):
        """Test _load_config_yaml with successful loading."""
        yaml_content = "physical_values:\n  Isource: 5\n  mu0: 1.256637e-06"
        
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            result = use_case._load_config_yaml("config.yaml")
        
        assert result == {"physical_values": {"Isource": 5, "mu0": 1.256637e-06}}
    
    def test_load_config_yaml_file_not_found(self, use_case, capsys):
        """Test _load_config_yaml when file is not found."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            result = use_case._load_config_yaml("nonexistent.yaml")
        
        assert result == {}
        captured = capsys.readouterr()
        assert "Warning: Config file nonexistent.yaml not found" in captured.out
    
    def test_load_config_yaml_yaml_error(self, use_case, capsys):
        """Test _load_config_yaml with YAML parsing error."""
        with patch("builtins.open", mock_open(read_data="invalid: yaml: content:")):
            with patch("yaml.safe_load", side_effect=yaml.YAMLError("Parse error")):
                result = use_case._load_config_yaml("bad.yaml")
        
        assert result == {}
        captured = capsys.readouterr()
        assert "Error parsing YAML file" in captured.out

    # ==================== Physical Values Definition Tests ====================

    @pytest.mark.parametrize("config_data,expected_values", [
        # No config data
        (None, {
            "Isource": 1,
            "mu0": 4e-7 * np.pi,
            "nu0": 1/(4e-7 * np.pi),
            "nu_iron_linear": 1/(4000 * 4e-7 * np.pi)
        }),
        # With config data overriding defaults
        ({"physical_values": {"Isource": 10, "custom_value": 2.5, "mu0": 1.0e-6}}, {
            "Isource": 10,
            "custom_value": 2.5,
            "mu0": 1.0e-6,
            "nu0": 1/(4e-7 * np.pi),
            "nu_iron_linear": 1/(4000 * 4e-7 * np.pi)
        }),
        # With expression strings containing pi
        ({"physical_values": {"Isource": "2*pi", "mu0": "4*pi*1e-7"}}, {
            "Isource": 2 * np.pi,
            "mu0": 4 * np.pi * 1e-7,
            "nu0": 1/(4e-7 * np.pi),
            "nu_iron_linear": 1/(4000 * 4e-7 * np.pi)
        }),
        # With invalid expression string
        ({"physical_values": {"Isource": "invalid*expression", "mu0": 1.0e-6}}, {
            "Isource": "invalid*expression",
            "mu0": 1.0e-6,
            "nu0": 1/(4e-7 * np.pi),
            "nu_iron_linear": 1/(4000 * 4e-7 * np.pi)
        }),
    ])
    def test_define_physical_values(self, use_case, config_data, expected_values):
        """Test _define_physical_values with various configurations."""
        use_case._define_physical_values(config_data)
        
        assert use_case.physical_values is not None
        
        # Check all expected values
        for key, expected_value in expected_values.items():
            if isinstance(expected_value, (int, float)):
                assert use_case.physical_values[key] == pytest.approx(expected_value)
            else:
                assert use_case.physical_values[key] == expected_value

    # ==================== Mesh Name Handling Tests ====================

    @pytest.mark.parametrize("mesh_name,expected", [
        ("test_mesh", "test_mesh.msh"),
        ("test_mesh.msh", "test_mesh.msh"),
        ("model", "model.msh"),
    ])
    def test_execute_mesh_name_handling(self, use_case, mesh_name, expected, mock_all_externals):
        """Test execute method handles mesh name extension correctly."""
        with self._mock_use_case_internals(use_case) as mocked:
            use_case.execute(mesh_name, use_config_yaml=False)
            
            # Check that _run_simulation was called with correct mesh name
            mocked.mock_run_sim.assert_called_once()
            call_args = mocked.mock_run_sim.call_args[0]
            assert call_args[0] == expected

    # ==================== Configuration Usage Tests ====================

    @pytest.mark.parametrize("use_config_yaml,config_path,expected_config_path,config_data", [
        (False, None, None, None),
        (True, None, "config.yaml", {"physical_values": {"Isource": 10}}),
        (True, "custom/config.yaml", "custom/config.yaml", {"test": "data"}),
    ])
    def test_execute_with_config(self, use_case, use_config_yaml, config_path, 
                               expected_config_path, config_data, mock_all_externals):
        """Test execute method with various config YAML configurations."""
        mock_print, mock_run_sim, mock_phys_ids = mock_all_externals
        
        with self._mock_use_case_internals(use_case, config_data=config_data) as mocked:
            # Prepare arguments
            kwargs = {"mesh_name": "test_mesh.msh", "use_config_yaml": use_config_yaml}
            if config_path:
                kwargs["config_yaml_path"] = config_path
            
            # Execute
            use_case.execute(**kwargs)
            
            # Verify calls
            if use_config_yaml:
                mocked.mock_load_config.assert_called_once_with(expected_config_path)
                mocked.mock_define.assert_called_once_with(config_data)
            else:
                mocked.mock_load_config.assert_not_called()
                mocked.mock_define.assert_called_once_with(None)
            
            mocked.mock_run_sim.assert_called_once()

    # ==================== External Function Integration Tests ====================

    def test_execute_calls_external_functions(self, use_case, mock_all_externals):
        """Test that execute calls external functions correctly."""
        mock_print, mock_run_sim, mock_phys_ids = mock_all_externals
        
        with self._mock_use_case_internals(use_case) as mocked:
            # Execute the method
            use_case.execute("test_mesh.msh", use_config_yaml=False)
            
            # Check that external functions were called
            mock_phys_ids.assert_called_once()
            assert mock_print.call_count == 2
    
    def test_run_simulation_calls_external_function(self, use_case):
        """Test _run_simulation calls external function."""
        mock_run_simulation = Mock()
        
        with patch('svg_to_getdp.core.use_cases.run_getdp_simulation.run_magnetostatic_simulation', 
                  mock_run_simulation):
            use_case._run_simulation("test_mesh.msh", True)
            
            mock_run_simulation.assert_called_once_with(
                "test_mesh.msh", show_simulation_result=True
            )

    # ==================== Gmsh Integration Tests ====================

    def test_gmsh_initialized_by_us_flag(self, use_case, mock_gmsh):
        """Test that Gmsh finalize is called when we initialized it."""
        # Mock gmsh.isInitialized to return False first, then True
        mock_gmsh.isInitialized.side_effect = [False, True]
        
        with patch('svg_to_getdp.core.use_cases.run_getdp_simulation.gmsh', mock_gmsh):
            # Mock all other dependencies
            with patch('svg_to_getdp.core.use_cases.run_getdp_simulation.print_data_to_pro'):
                with patch('svg_to_getdp.core.use_cases.run_getdp_simulation.run_magnetostatic_simulation'):
                    with patch('svg_to_getdp.core.use_cases.run_getdp_simulation.physical_identifiers',
                             return_value={"test_id": 1}):
                        with patch.object(use_case, '_load_config_yaml', return_value={}):
                            with patch.object(use_case, '_define_physical_values') as mock_define:
                                mock_define.side_effect = lambda _: setattr(
                                    use_case, 'physical_values', self._create_default_physical_values()
                                )
                                with patch.object(use_case, '_run_simulation'):
                                    # Call execute
                                    use_case.execute("test_mesh.msh", use_config_yaml=False)
        
        # Verify calls
        mock_gmsh.initialize.assert_called_once()
        mock_gmsh.finalize.assert_called_once()
        
        # Check that isInitialized was called twice
        assert mock_gmsh.isInitialized.call_count == 2
    
    def test_gmsh_already_initialized(self, use_case, mock_gmsh):
        """Test that Gmsh is not re-initialized if already initialized."""
        # Mock gmsh.isInitialized to always return True
        mock_gmsh.isInitialized.return_value = True
        
        with patch('svg_to_getdp.core.use_cases.run_getdp_simulation.gmsh', mock_gmsh):
            # Mock all other dependencies
            with patch('svg_to_getdp.core.use_cases.run_getdp_simulation.print_data_to_pro'):
                with patch('svg_to_getdp.core.use_cases.run_getdp_simulation.run_magnetostatic_simulation'):
                    with patch('svg_to_getdp.core.use_cases.run_getdp_simulation.physical_identifiers',
                             return_value={"test_id": 1}):
                        with patch.object(use_case, '_load_config_yaml', return_value={}):
                            with patch.object(use_case, '_define_physical_values') as mock_define:
                                mock_define.side_effect = lambda _: setattr(
                                    use_case, 'physical_values', self._create_default_physical_values()
                                )
                                with patch.object(use_case, '_run_simulation'):
                                    # Call execute
                                    use_case.execute("test_mesh.msh", use_config_yaml=False)
        
        # Verify calls
        mock_gmsh.initialize.assert_not_called()
        mock_gmsh.finalize.assert_not_called()

    # ==================== Error Handling Tests ====================

    def test_gmsh_not_available(self):
        """Test behavior when Gmsh is not available."""
        import svg_to_getdp.core.use_cases.run_getdp_simulation as module
        
        # Save original values
        original_gmsh = module.gmsh
        original_GMSH_AVAILABLE = module.GMSH_AVAILABLE
        
        try:
            # Set GMSH_AVAILABLE to False
            module.GMSH_AVAILABLE = False
            module.gmsh = None
            
            # Create an instance
            use_case = module.RunGetDPSimulation()
            
            # This should raise ImportError
            with pytest.raises(ImportError, match="Gmsh is not available"):
                use_case._initialize_gmsh()
                
        finally:
            # Restore original values
            module.GMSH_AVAILABLE = original_GMSH_AVAILABLE
            module.gmsh = original_gmsh
            