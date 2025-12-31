"""Tests for install command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

from click.testing import CliRunner

from mcp_skills.cli.main import cli
from mcp_skills.services.agent_detector import DetectedAgent
from mcp_skills.services.agent_installer import InstallResult


class TestInstallCommand:
    """Test suite for install command."""

    def test_install_help(self, cli_runner: CliRunner) -> None:
        """Test install command help."""
        result = cli_runner.invoke(cli, ["install", "--help"])

        assert result.exit_code == 0
        assert "Install MCP SkillSet for AI agents" in result.output
        assert "--agent" in result.output
        assert "--dry-run" in result.output
        assert "--force" in result.output
        assert "--with-hooks" in result.output

    @patch("mcp_skills.cli.commands.install.AgentInstaller")
    @patch("mcp_skills.cli.commands.install.AgentDetector")
    def test_install_single_agent(
        self,
        mock_detector_cls: Mock,
        mock_installer_cls: Mock,
        cli_runner: CliRunner,
    ) -> None:
        """Test install command for single agent."""
        # Mock detected agent
        mock_agent = DetectedAgent(
            id="claude-code",
            name="Claude Code",
            config_path="/path/to/claude_desktop_config.json",
            exists=True,
        )

        # Setup detector mock
        mock_detector = Mock()
        mock_detector.detect_agent.return_value = mock_agent
        mock_detector_cls.return_value = mock_detector

        # Setup installer mock
        mock_result = InstallResult(
            success=True,
            agent_name="Claude Code",
            agent_id="claude-code",
            config_path=Path("/path/to/config.json"),
            changes_made="Added mcp-skillset server",
            backup_path="/backup/path",
        )
        mock_installer = Mock()
        mock_installer.install.return_value = mock_result
        mock_installer_cls.return_value = mock_installer

        # Run command
        result = cli_runner.invoke(
            cli, ["install", "--agent", "claude-code", "--force"]
        )

        # Verify
        assert result.exit_code == 0
        mock_detector.detect_agent.assert_called_once_with("claude-code")
        mock_installer.install.assert_called_once()

    @patch("mcp_skills.cli.commands.install.AgentInstaller")
    @patch("mcp_skills.cli.commands.install.AgentDetector")
    def test_install_all_agents(
        self,
        mock_detector_cls: Mock,
        mock_installer_cls: Mock,
        cli_runner: CliRunner,
    ) -> None:
        """Test install command for all agents."""
        # Mock detected agents (excluding claude-desktop by default)
        mock_agents = [
            DetectedAgent(
                id="claude-code",
                name="Claude Code",
                config_path="/path/to/config.json",
                exists=True,
            ),
            DetectedAgent(
                id="cursor",
                name="Cursor",
                config_path="/path/to/cursor/config.json",
                exists=True,
            ),
            DetectedAgent(
                id="claude-desktop",
                name="Claude Desktop",
                config_path="/path/to/claude/config.json",
                exists=True,
            ),
        ]

        # Setup detector mock
        mock_detector = Mock()
        mock_detector.detect_all.return_value = mock_agents
        mock_detector_cls.return_value = mock_detector

        # Setup installer mock
        mock_result = InstallResult(
            success=True,
            agent_name="Agent",
            agent_id="generic-agent",
            config_path=Path("/path/to/config.json"),
            changes_made="Added mcp-skillset server",
        )
        mock_installer = Mock()
        mock_installer.install.return_value = mock_result
        mock_installer_cls.return_value = mock_installer

        # Run command
        result = cli_runner.invoke(cli, ["install", "--agent", "all", "--force"])

        # Verify - should install for all except claude-desktop (2 agents)
        assert result.exit_code == 0
        mock_detector.detect_all.assert_called_once()
        assert mock_installer.install.call_count == 2  # Excludes claude-desktop

    @patch("mcp_skills.cli.commands.install.AgentInstaller")
    @patch("mcp_skills.cli.commands.install.AgentDetector")
    def test_install_dry_run(
        self,
        mock_detector_cls: Mock,
        mock_installer_cls: Mock,
        cli_runner: CliRunner,
    ) -> None:
        """Test install command with --dry-run flag."""
        # Mock detected agent
        mock_agent = DetectedAgent(
            id="claude-code",
            name="Claude Code",
            config_path="/path/to/config.json",
            exists=True,
        )

        # Setup detector mock
        mock_detector = Mock()
        mock_detector.detect_agent.return_value = mock_agent
        mock_detector_cls.return_value = mock_detector

        # Setup installer mock
        mock_result = InstallResult(
            success=True,
            agent_name="Claude Code",
            agent_id="claude-code",
            config_path=Path("/path/to/config.json"),
            changes_made="Would add mcp-skillset server",
        )
        mock_installer = Mock()
        mock_installer.install.return_value = mock_result
        mock_installer_cls.return_value = mock_installer

        # Run command
        result = cli_runner.invoke(
            cli,
            ["install", "--agent", "claude-code", "--dry-run"],
        )

        # Verify
        assert result.exit_code == 0
        assert "DRY RUN" in result.output or "dry run" in result.output.lower()
        mock_installer.install.assert_called_once()
        # Verify dry_run=True was passed
        call_kwargs = mock_installer.install.call_args.kwargs
        assert call_kwargs.get("dry_run") is True

    @patch("mcp_skills.cli.commands.install.AgentInstaller")
    @patch("mcp_skills.cli.commands.install.AgentDetector")
    def test_install_force(
        self,
        mock_detector_cls: Mock,
        mock_installer_cls: Mock,
        cli_runner: CliRunner,
    ) -> None:
        """Test install command with --force flag."""
        # Mock detected agent
        mock_agent = DetectedAgent(
            id="cursor",
            name="Cursor",
            config_path="/path/to/config.json",
            exists=True,
        )

        # Setup detector mock
        mock_detector = Mock()
        mock_detector.detect_agent.return_value = mock_agent
        mock_detector_cls.return_value = mock_detector

        # Setup installer mock
        mock_result = InstallResult(
            success=True,
            agent_name="Cursor",
            agent_id="cursor",
            config_path=Path("/path/to/config.json"),
            changes_made="Overwrote existing config",
        )
        mock_installer = Mock()
        mock_installer.install.return_value = mock_result
        mock_installer_cls.return_value = mock_installer

        # Run command
        result = cli_runner.invoke(
            cli,
            ["install", "--agent", "cursor", "--force"],
        )

        # Verify
        assert result.exit_code == 0
        mock_installer.install.assert_called_once()
        # Verify force=True was passed
        call_kwargs = mock_installer.install.call_args.kwargs
        assert call_kwargs.get("force") is True

    @patch("mcp_skills.cli.commands.install.AgentInstaller")
    @patch("mcp_skills.cli.commands.install.AgentDetector")
    def test_install_agent_not_found(
        self,
        mock_detector_cls: Mock,
        mock_installer_cls: Mock,
        cli_runner: CliRunner,
    ) -> None:
        """Test install command when agent is not installed."""
        # Mock agent not found
        mock_agent = DetectedAgent(
            id="cursor",
            name="Cursor",
            config_path="/path/to/config.json",
            exists=False,
        )

        # Setup detector mock
        mock_detector = Mock()
        mock_detector.detect_agent.return_value = mock_agent
        mock_detector_cls.return_value = mock_detector

        # Run command
        result = cli_runner.invoke(cli, ["install", "--agent", "cursor", "--force"])

        # Verify - should exit early when no agents found
        assert result.exit_code == 0
        # Installer should not be called
        mock_installer_cls.return_value.install.assert_not_called()

    @patch("mcp_skills.cli.commands.install.AgentInstaller")
    @patch("mcp_skills.cli.commands.install.AgentDetector")
    def test_install_error_handling(
        self,
        mock_detector_cls: Mock,
        mock_installer_cls: Mock,
        cli_runner: CliRunner,
    ) -> None:
        """Test install command handles errors gracefully."""
        # Mock detected agent
        mock_agent = DetectedAgent(
            id="claude-code",
            name="Claude Code",
            config_path="/path/to/config.json",
            exists=True,
        )

        # Setup detector mock
        mock_detector = Mock()
        mock_detector.detect_agent.return_value = mock_agent
        mock_detector_cls.return_value = mock_detector

        # Setup installer mock to raise error
        mock_installer = Mock()
        mock_installer.install.side_effect = Exception("Installation failed")
        mock_installer_cls.return_value = mock_installer

        # Run command
        result = cli_runner.invoke(
            cli, ["install", "--agent", "claude-code", "--force"]
        )

        # Verify error handling
        assert result.exit_code == 1
        assert "failed" in result.output.lower() or "error" in result.output.lower()

    @patch("mcp_skills.cli.commands.install.AgentInstaller")
    @patch("mcp_skills.cli.commands.install.AgentDetector")
    def test_install_failed_result(
        self,
        mock_detector_cls: Mock,
        mock_installer_cls: Mock,
        cli_runner: CliRunner,
    ) -> None:
        """Test install command handles failed install result."""
        # Mock detected agent
        mock_agent = DetectedAgent(
            id="cursor",
            name="Cursor",
            config_path="/path/to/config.json",
            exists=True,
        )

        # Setup detector mock
        mock_detector = Mock()
        mock_detector.detect_agent.return_value = mock_agent
        mock_detector_cls.return_value = mock_detector

        # Setup installer mock with failure
        mock_result = InstallResult(
            success=False,
            agent_name="Cursor",
            agent_id="cursor",
            config_path=Path("/path/to/config.json"),
            error="Config file is locked",
        )
        mock_installer = Mock()
        mock_installer.install.return_value = mock_result
        mock_installer_cls.return_value = mock_installer

        # Run command
        result = cli_runner.invoke(cli, ["install", "--agent", "cursor", "--force"])

        # Verify - should show failure but not crash
        assert result.exit_code == 0
        assert "✗" in result.output or "Failed" in result.output

    @patch("mcp_skills.cli.commands.install.AgentInstaller")
    @patch("mcp_skills.cli.commands.install.AgentDetector")
    def test_install_displays_backup_path(
        self,
        mock_detector_cls: Mock,
        mock_installer_cls: Mock,
        cli_runner: CliRunner,
    ) -> None:
        """Test install command displays backup path."""
        # Mock detected agent
        mock_agent = DetectedAgent(
            id="claude-code",
            name="Claude Code",
            config_path="/path/to/config.json",
            exists=True,
        )

        # Setup detector mock
        mock_detector = Mock()
        mock_detector.detect_agent.return_value = mock_agent
        mock_detector_cls.return_value = mock_detector

        # Setup installer mock
        mock_result = InstallResult(
            success=True,
            agent_name="Claude Code",
            agent_id="claude-code",
            config_path=Path("/path/to/config.json"),
            changes_made="Updated config",
            backup_path="/backup/config.json.backup",
        )
        mock_installer = Mock()
        mock_installer.install.return_value = mock_result
        mock_installer_cls.return_value = mock_installer

        # Run command
        result = cli_runner.invoke(
            cli, ["install", "--agent", "claude-code", "--force"]
        )

        # Verify backup path is shown
        assert result.exit_code == 0
        assert "Backup:" in result.output or "backup" in result.output.lower()
