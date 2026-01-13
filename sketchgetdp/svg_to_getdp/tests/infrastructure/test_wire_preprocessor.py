"""
Unit tests for WirePreprocessor class.

Tests wire preprocessing functionality including clustering,
configuration loading, and physical group assignment.
"""
import pytest
import yaml
import tempfile
import os
import math
from unittest.mock import Mock, patch

from svg_to_getdp.infrastructure.wire_preprocessor import WirePreprocessor, Wire, WireCluster
from svg_to_getdp.core.entities.point import Point
from svg_to_getdp.core.entities.color import Color
from svg_to_getdp.core.entities.physical_group import DOMAIN_COIL_POSITIVE, DOMAIN_COIL_NEGATIVE


class TestWirePreprocessor:
    """Test suite for WirePreprocessor class."""

    # ==================== Fixtures ====================

    @pytest.fixture
    def preprocessor(self):
        """Create a wire preprocessor instance for testing."""
        return WirePreprocessor()
    
    @pytest.fixture
    def mock_factory(self):
        """Create a mock factory for testing."""
        return Mock()
    
    @pytest.fixture
    def basic_wires(self):
        """Create basic wire test data."""
        return [
            (Point(0.0, 0.0), Color.RED),
            (Point(1.0, 0.0), Color.RED),
            (Point(0.0, 1.0), Color.RED),
            (Point(1.0, 1.0), Color.RED),
            (Point(0.5, 0.5), Color.RED),
            (Point(1.5, 0.5), Color.RED)
        ]
    
    @pytest.fixture
    def spatially_distributed_wires(self):
        """Create spatially distributed wires for clustering tests."""
        return [
            Wire(Point(0.0, 0.0), Color.RED, 0),
            Wire(Point(1.0, 0.0), Color.RED, 1),
            Wire(Point(2.0, 0.0), Color.RED, 2),
            Wire(Point(10.0, 0.0), Color.RED, 3),
            Wire(Point(11.0, 0.0), Color.RED, 4),
        ]
    
    @pytest.fixture
    def sorted_wire_test_data(self):
        """Create unsorted wires for sorting tests."""
        return [
            Wire(Point(2.0, 1.0), Color.RED, 0),
            Wire(Point(1.0, 2.0), Color.RED, 1),
            Wire(Point(2.0, 2.0), Color.RED, 2),
            Wire(Point(0.0, 0.0), Color.RED, 3),
        ]
    
    @pytest.fixture
    def distance_calculation_wires(self):
        """Create wires for distance calculation tests."""
        return (
            Wire(Point(0.0, 0.0), Color.RED, 0),
            Wire(Point(3.0, 4.0), Color.RED, 1)
        )

    # ==================== Helper Methods ====================

    def create_temporary_configuration_file(self, configuration_content: dict) -> str:
        """Creates a temporary YAML configuration file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as configuration_file:
            yaml.dump(configuration_content, configuration_file)
            return configuration_file.name

    # ==================== Initialization Tests ====================

    def test_initial_state_is_empty(self, preprocessor):
        """Verifies WirePreprocessor starts with empty collections and no factory."""
        assert preprocessor.factory is None
        assert preprocessor.wire_clusters == []
        assert preprocessor.all_wires == []

    # ==================== Basic Functionality Tests ====================

    def test_sorts_wires_from_top_to_bottom_left_to_right(self, preprocessor, sorted_wire_test_data):
        """Ensures wires are sorted by descending y, then ascending x coordinates."""
        unsorted_wires = sorted_wire_test_data
        
        sorted_wires = preprocessor._sort_wires(unsorted_wires)
        
        assert sorted_wires[0].original_index == 1  # (1.0, 2.0) - highest y
        assert sorted_wires[1].original_index == 2  # (2.0, 2.0) - same y, x > 1.0
        assert sorted_wires[2].original_index == 0  # (2.0, 1.0) - lower y
        assert sorted_wires[3].original_index == 3  # (0.0, 0.0) - lowest y
    
    def test_calculates_euclidean_distance_between_wires(self, preprocessor, distance_calculation_wires):
        """Validates distance calculation between two wire positions."""
        first_wire, second_wire = distance_calculation_wires
        
        calculated_distance = preprocessor._calculate_distance(first_wire, second_wire)
        
        assert math.isclose(calculated_distance, 5.0)
    
    def test_maps_cluster_current_sign_to_physical_group(self, preprocessor):
        """Tests that cluster current signs correctly map to physical groups."""
        positive_current_cluster = WireCluster(name="positive_cluster", wire_count=1, current_sign=1)
        negative_current_cluster = WireCluster(name="negative_cluster", wire_count=1, current_sign=-1)
        
        positive_physical_group = preprocessor._get_physical_group_for_cluster(positive_current_cluster)
        assert positive_physical_group.value == DOMAIN_COIL_POSITIVE.value
        assert positive_physical_group.name == DOMAIN_COIL_POSITIVE.name
        
        negative_physical_group = preprocessor._get_physical_group_for_cluster(negative_current_cluster)
        assert negative_physical_group.value == DOMAIN_COIL_NEGATIVE.value
        assert negative_physical_group.name == DOMAIN_COIL_NEGATIVE.name
        
        invalid_current_cluster = WireCluster(name="invalid_cluster", wire_count=1, current_sign=0)
        with pytest.raises(ValueError, match="Invalid current sign"):
            preprocessor._get_physical_group_for_cluster(invalid_current_cluster)

    # ==================== Configuration Loading Tests ====================

    def test_loads_wire_clusters_from_valid_configuration(self, preprocessor):
        """Validates loading wire clusters from properly formatted YAML configuration."""
        valid_configuration = {
            'wire_clusters': {
                'cluster_1': {
                    'wire_count': 3,
                    'current_sign': 1
                },
                'cluster_2': {
                    'wire_count': 2,
                    'current_sign': -1
                }
            }
        }
        
        configuration_file_path = self.create_temporary_configuration_file(valid_configuration)
        
        try:
            loaded_clusters = preprocessor._load_wire_clusters(configuration_file_path)
            
            assert len(loaded_clusters) == 2
            
            # Clusters are sorted alphabetically by name
            first_cluster = loaded_clusters[0]
            assert first_cluster.name == 'cluster_1'
            assert first_cluster.wire_count == 3
            assert first_cluster.current_sign == 1
            assert first_cluster.wires == []
            
            second_cluster = loaded_clusters[1]
            assert second_cluster.name == 'cluster_2'
            assert second_cluster.wire_count == 2
            assert second_cluster.current_sign == -1
            assert second_cluster.wires == []
            
        finally:
            os.unlink(configuration_file_path)
    
    @pytest.mark.parametrize("configuration_content, expected_error_message", [
        (
            {'other_section': {'foo': 'bar'}},
            "Config file must contain 'wire_clusters' section"
        ),
        (
            {
                'wire_clusters': {
                    'cluster_1': {
                        'wire_count': -5,
                        'current_sign': 1
                    }
                }
            },
            "wire_count must be a positive integer"
        ),
        (
            {
                'wire_clusters': {
                    'cluster_1': {
                        'wire_count': 0,
                        'current_sign': 1
                    }
                }
            },
            "wire_count must be a positive integer"
        ),
        (
            {
                'wire_clusters': {
                    'cluster_1': {
                        'wire_count': 3,
                        'current_sign': 0
                    }
                }
            },
            "current_sign must be 1 or -1"
        ),
        (
            {
                'wire_clusters': {
                    'cluster_1': 'not_a_dict'
                }
            },
            "Cluster 'cluster_1' configuration must be a dictionary"
        ),
        (
            {
                'wire_clusters': {
                    'cluster_1': {
                        'current_sign': 1
                    }
                }
            },
            "Cluster 'cluster_1' must have 'wire_count'"
        ),
        (
            {
                'wire_clusters': {
                    'cluster_1': {
                        'wire_count': 3
                    }
                }
            },
            "Cluster 'cluster_1' must have 'current_sign'"
        ),
    ])
    def test_raises_error_for_invalid_configuration(self, preprocessor, configuration_content, expected_error_message):
        """Verifies appropriate errors are raised for various invalid configuration scenarios."""
        configuration_file_path = self.create_temporary_configuration_file(configuration_content)
        
        try:
            with pytest.raises(ValueError, match=expected_error_message):
                preprocessor._load_wire_clusters(configuration_file_path)
        finally:
            os.unlink(configuration_file_path)
    
    def test_raises_error_when_configuration_file_not_found(self, preprocessor):
        """Ensures FileNotFoundError is raised when configuration file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            preprocessor._load_wire_clusters("/nonexistent/path/config.yaml")
    
    def test_raises_error_for_invalid_yaml_syntax(self, preprocessor):
        """Verifies invalid YAML syntax triggers appropriate error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temporary_file:
            temporary_file.write("invalid: yaml: [")
            configuration_file_path = temporary_file.name
        
        try:
            with pytest.raises(ValueError, match="Invalid YAML"):
                preprocessor._load_wire_clusters(configuration_file_path)
        finally:
            os.unlink(configuration_file_path)

    # ==================== Clustering Tests ====================

    def test_clusters_wires_based_on_spatial_proximity(self, preprocessor, spatially_distributed_wires):
        """Tests that spatially close wires are grouped into the same cluster."""
        wires = spatially_distributed_wires
        
        preprocessor.wire_clusters = [
            WireCluster(name="first_cluster", wire_count=3, current_sign=1),
            WireCluster(name="second_cluster", wire_count=2, current_sign=-1)
        ]
        
        preprocessor._perform_clustering(wires)
        
        # First three close wires should be in first cluster
        assert len(preprocessor.wire_clusters[0].wires) == 3
        first_cluster_indices = {wire.original_index for wire in preprocessor.wire_clusters[0].wires}
        assert first_cluster_indices == {0, 1, 2}
        
        # Last two close wires should be in second cluster
        assert len(preprocessor.wire_clusters[1].wires) == 2
        second_cluster_indices = {wire.original_index for wire in preprocessor.wire_clusters[1].wires}
        assert second_cluster_indices == {3, 4}
    
    def test_raises_error_when_insufficient_wires_for_cluster(self, preprocessor):
        """Ensures error is raised when cluster requires more wires than available."""
        available_wires = [
            Wire(Point(0.0, 0.0), Color.RED, 0),
            Wire(Point(1.0, 0.0), Color.RED, 1),
        ]
        
        preprocessor.wire_clusters = [
            WireCluster(name="large_cluster", wire_count=3, current_sign=1),  # Needs 3 wires
        ]
        
        with pytest.raises(ValueError, match="Not enough wires for cluster"):
            preprocessor._perform_clustering(available_wires)

    # ==================== Integration Tests ====================

    def test_returns_empty_dict_when_no_wires_but_configuration_expected(self, preprocessor, mock_factory):
        """Handles case where configuration expects wires but none are provided."""
        configuration_expecting_wires = {
            'wire_clusters': {
                'cluster_1': {
                    'wire_count': 1,
                    'current_sign': 1
                }
            }
        }
        
        configuration_file_path = self.create_temporary_configuration_file(configuration_expecting_wires)
        
        try:
            result = preprocessor.prepare_wires(
                factory=mock_factory,
                config_path=configuration_file_path,
                wires=[]
            )
            
            assert result == {}
            mock_factory.addPoint.assert_not_called()
            mock_factory.addPhysicalGroup.assert_not_called()
            
        finally:
            os.unlink(configuration_file_path)
    
    def test_raises_error_when_wire_count_mismatches_configuration(self, preprocessor, mock_factory):
        """Verifies error when total wires don't match cluster configuration requirements."""
        configuration_content = {
            'wire_clusters': {
                'cluster_1': {
                    'wire_count': 5,  # Expects 5 wires
                    'current_sign': 1
                }
            }
        }
        
        configuration_file_path = self.create_temporary_configuration_file(configuration_content)
        
        available_wires = [
            (Point(0.0, 0.0), Color.RED),
            (Point(1.0, 0.0), Color.RED),
            (Point(2.0, 0.0), Color.RED)  # Only 3 wires
        ]
        
        try:
            with pytest.raises(ValueError, match="Number of wires.*doesn't match cluster configuration"):
                preprocessor.prepare_wires(
                    factory=mock_factory,
                    config_path=configuration_file_path,
                    wires=available_wires
                )
        finally:
            os.unlink(configuration_file_path)
    
    @patch('svg_to_getdp.infrastructure.wire_preprocessor.WirePreprocessor._load_wire_clusters')
    def test_prepares_wires_and_assigns_to_clusters(self, mock_load_clusters, preprocessor, mock_factory):
        """Integration test verifying complete wire preparation with factory interaction."""
        mock_clusters = [
            WireCluster(name="positive_cluster", wire_count=3, current_sign=1),
            WireCluster(name="negative_cluster", wire_count=3, current_sign=-1)
        ]
        mock_load_clusters.return_value = mock_clusters
        
        spatially_separated_wires = [
            # First spatial group - should form positive cluster
            (Point(0.0, 10.0), Color.RED),
            (Point(1.0, 10.0), Color.RED),
            (Point(0.0, 9.0), Color.RED),
            
            # Second spatial group - should form negative cluster
            (Point(100.0, 0.0), Color.RED),
            (Point(101.0, 0.0), Color.RED),
            (Point(100.0, 1.0), Color.RED),
        ]
        
        mock_factory.addPoint.side_effect = list(range(1, 7))
        
        wire_results = preprocessor.prepare_wires(
            factory=mock_factory,
            config_path="dummy_path.yaml",
            wires=spatially_separated_wires
        )
        
        assert mock_factory.addPoint.call_count == 6
        assert mock_factory.addPhysicalGroup.call_count == 2
        
        # Verify physical group assignments
        positive_physical_group_call = mock_factory.addPhysicalGroup.call_args_list[0]
        assert positive_physical_group_call[0][2] == DOMAIN_COIL_POSITIVE.value
        
        negative_physical_group_call = mock_factory.addPhysicalGroup.call_args_list[1]
        assert negative_physical_group_call[0][2] == DOMAIN_COIL_NEGATIVE.value
        
        # Verify result structure
        assert len(wire_results) == 6
        
        for wire_index in range(6):
            wire_data = wire_results[wire_index]
            assert 'point' in wire_data
            assert 'color' in wire_data
            assert 'gmsh_point_tag' in wire_data
            assert 'physical_group' in wire_data
            assert 'wire_index' in wire_data
            assert 'wire_name' in wire_data
            assert 'cluster_name' in wire_data
            assert 'wire_in_cluster_index' in wire_data
            assert 'cluster_index' in wire_data
        
        # Verify clustering logic
        first_group_cluster = wire_results[0]['cluster_name']
        assert wire_results[1]['cluster_name'] == first_group_cluster
        assert wire_results[2]['cluster_name'] == first_group_cluster
        
        second_group_cluster = wire_results[3]['cluster_name']
        assert wire_results[4]['cluster_name'] == second_group_cluster
        assert wire_results[5]['cluster_name'] == second_group_cluster
        
        assert first_group_cluster != second_group_cluster
        
        positive_wire_count = sum(
            1 for index in range(6)
            if wire_results[index]['physical_group'].value == DOMAIN_COIL_POSITIVE.value
        )
        negative_wire_count = sum(
            1 for index in range(6)
            if wire_results[index]['physical_group'].value == DOMAIN_COIL_NEGATIVE.value
        )
        
        assert positive_wire_count == 3
        assert negative_wire_count == 3

    # ==================== Summary and Reporting Tests ====================

    def test_generates_summary_from_wire_results(self, preprocessor):
        """Tests generation of human-readable summary from processed wire data."""
        wire_processing_results = {
            0: {
                'point': Point(0.0, 0.0),
                'color': Color.RED,
                'physical_group': DOMAIN_COIL_POSITIVE,
                'wire_name': 'wire_1',
                'cluster_name': 'positive_cluster',
                'wire_in_cluster_index': 0,
                'cluster_index': 0,
                'gmsh_point_tag': 1
            },
            1: {
                'point': Point(1.0, 1.0),
                'color': Color.RED,
                'physical_group': DOMAIN_COIL_NEGATIVE,
                'wire_name': 'wire_2',
                'cluster_name': 'negative_cluster',
                'wire_in_cluster_index': 0,
                'cluster_index': 1,
                'gmsh_point_tag': 2
            }
        }
        
        summary = preprocessor.get_wire_summary(wire_processing_results)
        
        assert "Wire Summary" in summary
        assert "Total wires: 2" in summary
        assert "Positive wires (+): 1" in summary
        assert "Negative wires (-): 1" in summary
        assert "Clusters: 2" in summary

    # ==================== Edge Case Tests ====================

    @pytest.mark.parametrize("configuration_content, wire_positions, expected_cluster_characteristics", [
        (
            {
                'wire_clusters': {
                    'single_cluster': {
                        'wire_count': 4,
                        'current_sign': 1
                    }
                }
            },
            [(float(i), float(i)) for i in range(4)],
            [('single_cluster', 4, DOMAIN_COIL_POSITIVE.value)]
        ),
        (
            {
                'wire_clusters': {
                    'cluster_A': {
                        'wire_count': 2,
                        'current_sign': 1
                    },
                    'cluster_B': {
                        'wire_count': 2,
                        'current_sign': -1
                    }
                }
            },
            [
                (0.0, 0.0),
                (0.1, 0.0),
                (100.0, 100.0),
                (100.1, 100.0),
            ],
            [('cluster_A', 2, DOMAIN_COIL_POSITIVE.value), 
             ('cluster_B', 2, DOMAIN_COIL_NEGATIVE.value)]
        ),
    ])
    def test_handles_edge_cases_in_wire_preparation(self, preprocessor, mock_factory, 
                                                    configuration_content, wire_positions, 
                                                    expected_cluster_characteristics):
        """Tests various edge cases in wire preparation and clustering."""
        configuration_file_path = self.create_temporary_configuration_file(configuration_content)
        
        test_wires = [(Point(x, y), Color.RED) for x, y in wire_positions]
        
        mock_factory.addPoint.side_effect = list(range(1, len(test_wires) + 1))
        
        try:
            wire_results = preprocessor.prepare_wires(
                factory=mock_factory,
                config_path=configuration_file_path,
                wires=test_wires
            )
            
            assert len(wire_results) == len(test_wires)
            assert mock_factory.addPoint.call_count == len(test_wires)
            
            # Analyze cluster distribution
            cluster_analysis = {}
            for wire_data in wire_results.values():
                cluster_name = wire_data['cluster_name']
                if cluster_name not in cluster_analysis:
                    cluster_analysis[cluster_name] = {
                        'wire_count': 0,
                        'physical_group_value': wire_data['physical_group'].value,
                        'wire_names': set()
                    }
                cluster_analysis[cluster_name]['wire_count'] += 1
                cluster_analysis[cluster_name]['wire_names'].add(wire_data['wire_name'])
            
            # Verify cluster characteristics match expectations
            assert len(cluster_analysis) == len(expected_cluster_characteristics)
            
            sorted_cluster_names = sorted(cluster_analysis.keys())
            for cluster_index, (expected_cluster_name, expected_wire_count, expected_physical_group_value) \
                    in enumerate(expected_cluster_characteristics):
                
                actual_cluster_name = sorted_cluster_names[cluster_index]
                cluster_data = cluster_analysis[actual_cluster_name]
                
                assert cluster_data['wire_count'] == expected_wire_count
                assert cluster_data['physical_group_value'] == expected_physical_group_value
            
        finally:
            os.unlink(configuration_file_path)

    # ==================== Performance Tests ====================

    def test_performance_with_many_wires(self, preprocessor, mock_factory):
        """Test that preprocessor handles large number of wires efficiently."""
        # Create many wires
        many_wires = [(Point(i * 1.0, i * 1.0), Color.RED) for i in range(100)]
        
        # Configuration for 100 wires in a single cluster
        configuration_content = {
            'wire_clusters': {
                'large_cluster': {
                    'wire_count': 100,
                    'current_sign': 1
                }
            }
        }
        
        configuration_file_path = self.create_temporary_configuration_file(configuration_content)
        
        mock_factory.addPoint.side_effect = list(range(1, 101))
        
        import time
        start_time = time.time()
        try:
            wire_results = preprocessor.prepare_wires(
                factory=mock_factory,
                config_path=configuration_file_path,
                wires=many_wires
            )
            end_time = time.time()
            
            # Should complete in reasonable time
            assert end_time - start_time < 5.0
            
            # Should have 100 wires
            assert len(wire_results) == 100
            assert mock_factory.addPoint.call_count == 100
            
        finally:
            os.unlink(configuration_file_path)

    # ==================== Error Handling Tests ====================

    def test_error_handling_with_invalid_wire_data(self, preprocessor, mock_factory):
        """Test handling of invalid wire data."""
        invalid_wires = [
            (Point(0.0, 0.0), Color.RED),
            "not a wire",
            (Point(1.0, 1.0), Color.RED)
        ]
        
        configuration_content = {
            'wire_clusters': {
                'test_cluster': {
                    'wire_count': 3,
                    'current_sign': 1
                }
            }
        }
        
        configuration_file_path = self.create_temporary_configuration_file(configuration_content)
        
        try:
            with pytest.raises((TypeError, AttributeError, ValueError)):
                preprocessor.prepare_wires(
                    factory=mock_factory,
                    config_path=configuration_file_path,
                    wires=invalid_wires
                )
        finally:
            os.unlink(configuration_file_path)
