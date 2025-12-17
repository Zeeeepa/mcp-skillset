"""Tests for mcp (serve) command."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from mcp_skills.cli.main import cli


class TestMCPCommand:
    """Test suite for mcp command."""

    def test_mcp_help(self, cli_runner: CliRunner) -> None:
        """Test mcp command help."""
        result = cli_runner.invoke(cli, ["mcp", "--help"])

        assert result.exit_code == 0
        assert "Start MCP server" in result.output
        assert "--dev" in result.output

    @pytest.mark.skip(
        reason="MCP server has I/O file closure issues with Click test runner"
    )
    @patch("mcp_skills.cli.commands.mcp_server.MCPSkillsServer")
    @patch("mcp_skills.models.config.MCPSkillsConfig")
    def test_mcp_basic(
        self,
        mock_config_cls: Mock,
        mock_server_cls: Mock,
        cli_runner: CliRunner,
        mock_config,
    ) -> None:
        """Test basic mcp command."""
        # Setup mocks
        mock_config_cls.load.return_value = mock_config

        mock_server = Mock()
        mock_server.run.return_value = None
        mock_server_cls.return_value = mock_server

        # Run command (will timeout or need ctrl+c)
        result = cli_runner.invoke(cli, ["mcp"])

        # Verify
        assert "Starting MCP server" in result.output

    @pytest.mark.skip(
        reason="MCP server has I/O file closure issues with Click test runner"
    )
    @patch("mcp_skills.cli.commands.mcp_server.MCPSkillsServer")
    @patch("mcp_skills.models.config.MCPSkillsConfig")
    def test_mcp_dev_mode(
        self,
        mock_config_cls: Mock,
        mock_server_cls: Mock,
        cli_runner: CliRunner,
        mock_config,
    ) -> None:
        """Test mcp command with --dev flag."""
        # Setup mocks
        mock_config_cls.load.return_value = mock_config

        mock_server = Mock()
        mock_server.run.return_value = None
        mock_server_cls.return_value = mock_server

        # Run command
        result = cli_runner.invoke(cli, ["mcp", "--dev"])

        # Verify
        assert "Starting MCP server" in result.output
        assert "dev" in result.output.lower() or "development" in result.output.lower()

    @patch("mcp_skills.mcp.server.configure_services")
    def test_mcp_server_initialization_error(
        self,
        mock_configure: Mock,
        cli_runner: CliRunner,
    ) -> None:
        """Test mcp command handles server initialization errors."""
        # Setup mock to raise exception during service configuration
        mock_configure.side_effect = Exception("Server initialization failed")

        # Run command
        result = cli_runner.invoke(cli, ["mcp"])

        # Verify error handling
        assert result.exit_code != 0

    @patch("mcp_skills.mcp.server.main")
    @patch("mcp_skills.mcp.server.configure_services")
    def test_mcp_config_load_error(
        self,
        mock_configure: Mock,
        mock_main: Mock,
        cli_runner: CliRunner,
    ) -> None:
        """Test mcp command handles config loading errors."""
        # Setup mock to raise exception during configuration
        mock_configure.side_effect = Exception("Config load failed")

        # Run command
        result = cli_runner.invoke(cli, ["mcp"])

        # Verify error handling
        assert result.exit_code != 0
        # main should not be called if configure fails
        mock_main.assert_not_called()

    @patch("mcp_skills.mcp.server.main")
    @patch("mcp_skills.mcp.server.configure_services")
    def test_mcp_displays_startup_message(
        self,
        mock_configure: Mock,
        mock_main: Mock,
        cli_runner: CliRunner,
    ) -> None:
        """Test mcp command displays startup message."""
        # Setup mocks to prevent actual server startup
        mock_configure.return_value = None
        mock_main.return_value = None

        # Run command
        result = cli_runner.invoke(cli, ["mcp"])

        # Verify startup message appears
        assert result.exit_code == 0
        assert "MCP" in result.output or "server" in result.output.lower()

    @pytest.mark.skip(reason="MCP server runs indefinitely")
    @patch("mcp_skills.cli.commands.mcp_server.MCPSkillsServer")
    @patch("mcp_skills.models.config.MCPSkillsConfig")
    def test_mcp_can_be_interrupted(
        self,
        mock_config_cls: Mock,
        mock_server_cls: Mock,
        cli_runner: CliRunner,
        mock_config,
    ) -> None:
        """Test mcp command can be interrupted with Ctrl+C."""
        # Setup mocks
        mock_config_cls.load.return_value = mock_config

        mock_server = Mock()
        mock_server.run.side_effect = KeyboardInterrupt()
        mock_server_cls.return_value = mock_server

        # Run command
        result = cli_runner.invoke(cli, ["mcp"])

        # Verify graceful shutdown
        assert "Shutting down" in result.output or result.exit_code == 1

    @patch("mcp_skills.mcp.server.main")
    @patch("mcp_skills.mcp.server.configure_services")
    def test_mcp_verifies_skills_available(
        self,
        mock_configure: Mock,
        mock_main: Mock,
        cli_runner: CliRunner,
    ) -> None:
        """Test mcp command verifies skills are available."""
        # Setup mocks to prevent actual server startup
        mock_configure.return_value = None
        mock_main.return_value = None

        # Run command (should succeed even with no skills)
        result = cli_runner.invoke(cli, ["mcp"])

        # Command should succeed with mocked services
        assert result.exit_code == 0
        mock_configure.assert_called_once()
        mock_main.assert_called_once()


class TestMCPCommandIntegration:
    """Integration tests for mcp command."""

    @pytest.mark.skip(reason="Requires full MCP server setup")
    def test_mcp_full_startup_sequence(
        self,
        cli_runner: CliRunner,
    ) -> None:
        """Test full MCP server startup sequence."""
        # This would require actual server setup
        pass

    @pytest.mark.skip(reason="Requires client connection")
    def test_mcp_handles_client_connections(
        self,
        cli_runner: CliRunner,
    ) -> None:
        """Test MCP server handles client connections."""
        # This would require actual client to connect
        pass
