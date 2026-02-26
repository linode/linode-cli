"""
Unit tests for the LKE apl_enabled parameter.

This module tests the handling of the apl_enabled boolean parameter
for LKE cluster operations (create and update).
"""

import argparse

import pytest

from linodecli.baked.operation import TYPES


class TestLKEAplEnabled:
    """
    Test suite for validating the apl_enabled parameter handling.
    """

    def test_apl_enabled_boolean_true(self):
        """
        Test that apl_enabled=true is parsed correctly.
        """
        parser = argparse.ArgumentParser(prog="lke-cluster-create")
        parser.add_argument(
            "--apl_enabled",
            type=TYPES["boolean"],
            help="Whether APL is enabled on the cluster",
        )

        result = parser.parse_args(["--apl_enabled", "true"])
        assert result.apl_enabled is True

    def test_apl_enabled_boolean_false(self):
        """
        Test that apl_enabled=false is parsed correctly.
        """
        parser = argparse.ArgumentParser(prog="lke-cluster-create")
        parser.add_argument(
            "--apl_enabled",
            type=TYPES["boolean"],
            help="Whether APL is enabled on the cluster",
        )

        result = parser.parse_args(["--apl_enabled", "false"])
        assert result.apl_enabled is False

    def test_apl_enabled_default_none(self):
        """
        Test that apl_enabled defaults to None when not specified.
        """
        parser = argparse.ArgumentParser(prog="lke-cluster-create")
        parser.add_argument(
            "--apl_enabled",
            type=TYPES["boolean"],
            help="Whether APL is enabled on the cluster",
        )

        result = parser.parse_args([])
        assert result.apl_enabled is None

    def test_apl_enabled_with_other_params(self):
        """
        Test that apl_enabled works correctly with other cluster parameters.
        """
        parser = argparse.ArgumentParser(prog="lke-cluster-create")
        parser.add_argument("--region", type=str, required=True)
        parser.add_argument("--label", type=str, required=True)
        parser.add_argument("--k8s_version", type=str, required=True)
        parser.add_argument(
            "--apl_enabled",
            type=TYPES["boolean"],
            help="Whether APL is enabled on the cluster",
        )

        result = parser.parse_args(
            [
                "--region",
                "us-east",
                "--label",
                "my-cluster",
                "--k8s_version",
                "1.28",
                "--apl_enabled",
                "true",
            ]
        )

        assert result.region == "us-east"
        assert result.label == "my-cluster"
        assert result.k8s_version == "1.28"
        assert result.apl_enabled is True

    def test_apl_enabled_case_insensitive(self):
        """
        Test that apl_enabled accepts various case formats.
        """
        parser = argparse.ArgumentParser(prog="lke-cluster-create")
        parser.add_argument(
            "--apl_enabled",
            type=TYPES["boolean"],
            help="Whether APL is enabled on the cluster",
        )

        # Test uppercase TRUE
        result = parser.parse_args(["--apl_enabled", "TRUE"])
        assert result.apl_enabled is True

        # Test uppercase FALSE
        result = parser.parse_args(["--apl_enabled", "FALSE"])
        assert result.apl_enabled is False

        # Test mixed case
        result = parser.parse_args(["--apl_enabled", "True"])
        assert result.apl_enabled is True

    def test_apl_enabled_numeric_values(self):
        """
        Test that apl_enabled accepts numeric boolean representations.
        """
        parser = argparse.ArgumentParser(prog="lke-cluster-create")
        parser.add_argument(
            "--apl_enabled",
            type=TYPES["boolean"],
            help="Whether APL is enabled on the cluster",
        )

        # Test "1" for true
        result = parser.parse_args(["--apl_enabled", "1"])
        assert result.apl_enabled is True

        # Test "0" for false
        result = parser.parse_args(["--apl_enabled", "0"])
        assert result.apl_enabled is False

    def test_apl_enabled_update_operation(self):
        """
        Test that apl_enabled can be updated in an update operation.
        """
        parser = argparse.ArgumentParser(prog="lke-cluster-update")
        parser.add_argument("cluster_id", type=str)
        parser.add_argument(
            "--apl_enabled",
            type=TYPES["boolean"],
            help="Whether APL is enabled on the cluster",
        )

        # Test enabling APL
        result = parser.parse_args(["12345", "--apl_enabled", "true"])
        assert result.cluster_id == "12345"
        assert result.apl_enabled is True

        # Test disabling APL
        result = parser.parse_args(["12345", "--apl_enabled", "false"])
        assert result.cluster_id == "12345"
        assert result.apl_enabled is False

    @pytest.mark.parametrize(
        "input_value,expected_output",
        [
            ("true", True),
            ("false", False),
            ("TRUE", True),
            ("FALSE", False),
            ("1", True),
            ("0", False),
            ("yes", True),
            ("no", False),
        ],
    )
    def test_apl_enabled_various_inputs(self, input_value, expected_output):
        """
        Parametrized test for various apl_enabled input values.
        """
        parser = argparse.ArgumentParser(prog="lke-cluster-create")
        parser.add_argument(
            "--apl_enabled",
            type=TYPES["boolean"],
            help="Whether APL is enabled on the cluster",
        )

        result = parser.parse_args(["--apl_enabled", input_value])
        assert result.apl_enabled == expected_output


class TestLKEAplEnabledIntegrationWithOtherFields:
    """
    Test suite for validating apl_enabled in context of full cluster operations.
    """

    def test_create_cluster_with_all_fields_and_apl(self):
        """
        Test creating a cluster with all fields including apl_enabled.
        """
        parser = argparse.ArgumentParser(prog="lke-cluster-create")
        parser.add_argument("--region", type=str, required=True)
        parser.add_argument("--label", type=str, required=True)
        parser.add_argument("--k8s_version", type=str, required=True)
        parser.add_argument("--tier", type=str)
        parser.add_argument(
            "--apl_enabled",
            type=TYPES["boolean"],
            help="Whether APL is enabled on the cluster",
        )
        parser.add_argument(
            "--node_pools.type",
            type=str,
            action="append",
            dest="node_pools_type",
        )
        parser.add_argument(
            "--node_pools.count",
            type=int,
            action="append",
            dest="node_pools_count",
        )

        result = parser.parse_args(
            [
                "--region",
                "us-east",
                "--label",
                "production-cluster",
                "--k8s_version",
                "1.28",
                "--tier",
                "standard",
                "--apl_enabled",
                "true",
                "--node_pools.type",
                "g6-standard-8",
                "--node_pools.count",
                "3",
            ]
        )

        assert result.region == "us-east"
        assert result.label == "production-cluster"
        assert result.k8s_version == "1.28"
        assert result.tier == "standard"
        assert result.apl_enabled is True
        assert result.node_pools_type == ["g6-standard-8"]
        assert result.node_pools_count == [3]

    def test_update_cluster_partial_with_apl(self):
        """
        Test updating a cluster with only apl_enabled changed.
        """
        parser = argparse.ArgumentParser(prog="lke-cluster-update")
        parser.add_argument("cluster_id", type=str)
        parser.add_argument("--label", type=str)
        parser.add_argument(
            "--apl_enabled",
            type=TYPES["boolean"],
            help="Whether APL is enabled on the cluster",
        )

        # Test updating only apl_enabled
        result = parser.parse_args(["12345", "--apl_enabled", "true"])
        assert result.cluster_id == "12345"
        assert result.apl_enabled is True
        assert result.label is None

        # Test updating label and apl_enabled
        result = parser.parse_args(
            ["12345", "--label", "new-label", "--apl_enabled", "false"]
        )
        assert result.cluster_id == "12345"
        assert result.label == "new-label"
        assert result.apl_enabled is False
