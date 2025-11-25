"""Tests for setup command."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, Mock, patch

import pytest
from click.testing import CliRunner

from mcp_skills.cli.main import cli

if TYPE_CHECKING:
    from mcp_skills.models.config import MCPSkillsConfig
    from mcp_skills.models.toolchain import ToolchainInfo


class TestSetupCommand:
    """Test suite for setup command."""

    def test_setup_help(self, cli_runner: CliRunner) -> None:
        """Test setup command help."""
        result = cli_runner.invoke(cli, ["setup", "--help"])

        assert result.exit_code == 0
        assert "Auto-configure mcp-skillset for your project" in result.output
        assert "--project-dir" in result.output
        assert "--config" in result.output
        assert "--auto" in result.output

    @patch("mcp_skills.cli.main.ToolchainDetector")
    @patch("mcp_skills.cli.main.RepositoryManager")
    @patch("mcp_skills.cli.main.IndexingEngine")
    @patch("mcp_skills.cli.main.AgentDetector")
    @patch("mcp_skills.cli.main.AgentInstaller")
    def test_setup_auto_mode(
        self,
        mock_installer_cls: Mock,
        mock_detector_cls: Mock,
        mock_engine_cls: Mock,
        mock_repo_cls: Mock,
        mock_toolchain_cls: Mock,
        cli_runner: CliRunner,
        mock_toolchain_info: ToolchainInfo,
        tmp_path: Path,
    ) -> None:
        """Test setup command in auto mode."""
        # Setup mocks
        mock_toolchain = Mock()
        mock_toolchain.detect.return_value = mock_toolchain_info
        mock_toolchain_cls.return_value = mock_toolchain

        mock_repo_manager = Mock()
        mock_repo_manager.DEFAULT_REPOS = []
        mock_repo_manager.add_repository.return_value = None
        mock_repo_cls.return_value = mock_repo_manager

        mock_engine = Mock()
        mock_engine.index_skills.return_value = None
        mock_engine.get_stats.return_value = {
            "total_skills": 5,
            "total_embeddings": 50,
        }
        mock_engine_cls.return_value = mock_engine

        mock_detector = Mock()
        mock_detector.detect_agent.return_value = "claude"
        mock_detector_cls.return_value = mock_detector

        mock_installer = Mock()
        mock_installer.install_agent.return_value = {"status": "success"}
        mock_installer_cls.return_value = mock_installer

        # Run command
        config_path = tmp_path / "config.yaml"
        result = cli_runner.invoke(
            cli,
            ["setup", "--project-dir", str(tmp_path), "--config", str(config_path), "--auto"],
        )

        # Verify
        assert result.exit_code == 0
        assert "Starting mcp-skillset setup" in result.output
        assert "Detecting project toolchain" in result.output
        assert "Python" in result.output

    @patch("mcp_skills.cli.main.ToolchainDetector")
    def test_setup_toolchain_detection_failure(
        self,
        mock_toolchain_cls: Mock,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test setup command when toolchain detection fails."""
        # Setup mock to raise exception
        mock_toolchain = Mock()
        mock_toolchain.detect.side_effect = Exception("Detection failed")
        mock_toolchain_cls.return_value = mock_toolchain

        # Run command
        result = cli_runner.invoke(
            cli,
            ["setup", "--project-dir", str(tmp_path), "--auto"],
        )

        # Verify error handling
        assert result.exit_code != 0
        assert "Setup failed" in result.output or "Detection failed" in result.output

    @patch("mcp_skills.cli.main.ToolchainDetector")
    @patch("mcp_skills.cli.main.RepositoryManager")
    def test_setup_with_custom_config_path(
        self,
        mock_repo_cls: Mock,
        mock_toolchain_cls: Mock,
        cli_runner: CliRunner,
        mock_toolchain_info: ToolchainInfo,
        tmp_path: Path,
    ) -> None:
        """Test setup command with custom config path."""
        # Setup mocks
        mock_toolchain = Mock()
        mock_toolchain.detect.return_value = mock_toolchain_info
        mock_toolchain_cls.return_value = mock_toolchain

        mock_repo_manager = Mock()
        mock_repo_manager.DEFAULT_REPOS = []
        mock_repo_cls.return_value = mock_repo_manager

        # Run command with custom config path
        custom_config = tmp_path / "custom" / "config.yaml"
        result = cli_runner.invoke(
            cli,
            [
                "setup",
                "--project-dir",
                str(tmp_path),
                "--config",
                str(custom_config),
                "--auto",
            ],
        )

        # Verify custom path is used
        assert str(custom_config) in result.output or result.exit_code == 0

    @patch("mcp_skills.cli.main.ToolchainDetector")
    @patch("mcp_skills.cli.main.RepositoryManager")
    @patch("mcp_skills.cli.main.IndexingEngine")
    def test_setup_with_repository_cloning(
        self,
        mock_engine_cls: Mock,
        mock_repo_cls: Mock,
        mock_toolchain_cls: Mock,
        cli_runner: CliRunner,
        mock_toolchain_info: ToolchainInfo,
        tmp_path: Path,
    ) -> None:
        """Test setup command includes repository cloning."""
        # Setup mocks
        mock_toolchain = Mock()
        mock_toolchain.detect.return_value = mock_toolchain_info
        mock_toolchain_cls.return_value = mock_toolchain

        mock_repo_manager = Mock()
        mock_repo_manager.DEFAULT_REPOS = [
            {"url": "https://github.com/example/skills.git"}
        ]
        mock_repo_manager.add_repository.return_value = None
        mock_repo_cls.return_value = mock_repo_manager

        mock_engine = Mock()
        mock_engine.index_skills.return_value = None
        mock_engine_cls.return_value = mock_engine

        # Run command
        result = cli_runner.invoke(
            cli,
            ["setup", "--project-dir", str(tmp_path), "--auto"],
        )

        # Verify repository setup step is included
        assert result.exit_code == 0
        assert "Setting up skill repositories" in result.output

    def test_setup_invalid_project_dir(self, cli_runner: CliRunner) -> None:
        """Test setup command with invalid project directory."""
        result = cli_runner.invoke(
            cli,
            ["setup", "--project-dir", "/nonexistent/path", "--auto"],
        )

        # Should fail with path error
        assert result.exit_code != 0

    @patch("mcp_skills.cli.main.ToolchainDetector")
    @patch("mcp_skills.cli.main.RepositoryManager")
    @patch("mcp_skills.cli.main.IndexingEngine")
    def test_setup_indexing_step(
        self,
        mock_engine_cls: Mock,
        mock_repo_cls: Mock,
        mock_toolchain_cls: Mock,
        cli_runner: CliRunner,
        mock_toolchain_info: ToolchainInfo,
        tmp_path: Path,
    ) -> None:
        """Test setup command includes indexing step."""
        # Setup mocks
        mock_toolchain = Mock()
        mock_toolchain.detect.return_value = mock_toolchain_info
        mock_toolchain_cls.return_value = mock_toolchain

        mock_repo_manager = Mock()
        mock_repo_manager.DEFAULT_REPOS = []
        mock_repo_cls.return_value = mock_repo_manager

        mock_engine = Mock()
        mock_engine.index_skills.return_value = None
        mock_engine.get_stats.return_value = {
            "total_skills": 10,
            "total_embeddings": 100,
        }
        mock_engine_cls.return_value = mock_engine

        # Run command
        result = cli_runner.invoke(
            cli,
            ["setup", "--project-dir", str(tmp_path), "--auto"],
        )

        # Verify indexing step
        assert result.exit_code == 0
        assert "Indexing skills" in result.output or "indexed" in result.output.lower()
