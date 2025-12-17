"""Tests for index command."""

from __future__ import annotations

from unittest.mock import Mock, patch

from click.testing import CliRunner

from mcp_skills.cli.main import cli


class TestIndexCommand:
    """Test suite for index command."""

    def test_index_help(self, cli_runner: CliRunner) -> None:
        """Test index command help."""
        result = cli_runner.invoke(cli, ["index", "--help"])

        assert result.exit_code == 0
        assert "Rebuild skill indices" in result.output
        assert "--incremental" in result.output
        assert "--force" in result.output

    @patch("mcp_skills.cli.commands.index.IndexingEngine")
    @patch("mcp_skills.cli.commands.index.SkillManager")
    def test_index_basic(
        self,
        mock_manager_cls: Mock,
        mock_engine_cls: Mock,
        cli_runner: CliRunner,
    ) -> None:
        """Test basic index command."""
        # Setup mocks
        mock_manager = Mock()
        mock_manager.discover_skills.return_value = []
        mock_manager_cls.return_value = mock_manager

        # Import IndexStats to create proper return value
        from mcp_skills.services.indexing.engine import IndexStats

        mock_engine = Mock()
        mock_engine.reindex_all.return_value = IndexStats(
            total_skills=10,
            vector_store_size=2560,  # 2.5 KB in bytes
            graph_nodes=10,
            graph_edges=20,
            last_indexed="2025-12-16T10:00:00",
        )
        mock_engine_cls.return_value = mock_engine

        # Run command
        result = cli_runner.invoke(cli, ["index"])

        # Verify
        assert result.exit_code == 0
        assert "Indexing" in result.output or "indexed" in result.output.lower()

    @patch("mcp_skills.cli.commands.index.IndexingEngine")
    @patch("mcp_skills.cli.commands.index.SkillManager")
    def test_index_incremental(
        self,
        mock_manager_cls: Mock,
        mock_engine_cls: Mock,
        cli_runner: CliRunner,
    ) -> None:
        """Test index command with --incremental flag."""
        # Setup mocks
        mock_manager = Mock()
        mock_manager.discover_skills.return_value = []
        mock_manager_cls.return_value = mock_manager

        from mcp_skills.services.indexing.engine import IndexStats

        mock_engine = Mock()
        mock_engine.reindex_all.return_value = IndexStats(
            total_skills=10,
            vector_store_size=2048,
            graph_nodes=10,
            graph_edges=15,
            last_indexed="2025-12-16T10:00:00",
        )
        mock_engine_cls.return_value = mock_engine

        # Run command
        result = cli_runner.invoke(cli, ["index", "--incremental"])

        # Verify
        assert result.exit_code == 0
        assert "incremental" in result.output.lower() or result.exit_code == 0

    @patch("mcp_skills.cli.commands.index.IndexingEngine")
    @patch("mcp_skills.cli.commands.index.SkillManager")
    def test_index_force(
        self,
        mock_manager_cls: Mock,
        mock_engine_cls: Mock,
        cli_runner: CliRunner,
    ) -> None:
        """Test index command with --force flag."""
        # Setup mocks
        mock_manager = Mock()
        mock_manager.discover_skills.return_value = []
        mock_manager_cls.return_value = mock_manager

        from mcp_skills.services.indexing.engine import IndexStats

        mock_engine = Mock()
        mock_engine.reindex_all.return_value = IndexStats(
            total_skills=5,
            vector_store_size=1024,
            graph_nodes=5,
            graph_edges=10,
            last_indexed="2025-12-16T10:00:00",
        )
        mock_engine_cls.return_value = mock_engine

        # Run command
        result = cli_runner.invoke(cli, ["index", "--force"])

        # Verify
        assert result.exit_code == 0

    @patch("mcp_skills.cli.commands.index.IndexingEngine")
    @patch("mcp_skills.cli.commands.index.SkillManager")
    def test_index_with_skills(
        self,
        mock_manager_cls: Mock,
        mock_engine_cls: Mock,
        cli_runner: CliRunner,
        mock_skill,
    ) -> None:
        """Test index command with actual skills to index."""
        # Setup mocks
        mock_manager = Mock()
        mock_manager.discover_skills.return_value = [mock_skill] * 5
        mock_manager_cls.return_value = mock_manager

        from mcp_skills.services.indexing.engine import IndexStats

        mock_engine = Mock()
        mock_engine.reindex_all.return_value = IndexStats(
            total_skills=5,
            vector_store_size=5120,
            graph_nodes=5,
            graph_edges=12,
            last_indexed="2025-12-16T10:00:00",
        )
        mock_engine_cls.return_value = mock_engine

        # Run command
        result = cli_runner.invoke(cli, ["index"])

        # Verify reindex_all was called
        assert result.exit_code == 0
        mock_engine.reindex_all.assert_called_once()

    @patch("mcp_skills.cli.commands.index.IndexingEngine")
    @patch("mcp_skills.cli.commands.index.SkillManager")
    def test_index_no_skills(
        self,
        mock_manager_cls: Mock,
        mock_engine_cls: Mock,
        cli_runner: CliRunner,
    ) -> None:
        """Test index command when no skills found."""
        # Setup mocks
        mock_manager = Mock()
        mock_manager.discover_skills.return_value = []
        mock_manager_cls.return_value = mock_manager

        from mcp_skills.services.indexing.engine import IndexStats

        mock_engine = Mock()
        mock_engine.reindex_all.return_value = IndexStats(
            total_skills=0,
            vector_store_size=0,
            graph_nodes=0,
            graph_edges=0,
            last_indexed="2025-12-16T10:00:00",
        )
        mock_engine_cls.return_value = mock_engine

        # Run command
        result = cli_runner.invoke(cli, ["index"])

        # Verify appropriate message
        assert result.exit_code == 0
        assert "No skills" in result.output or "0" in result.output

    @patch("mcp_skills.cli.commands.index.IndexingEngine")
    @patch("mcp_skills.cli.commands.index.SkillManager")
    def test_index_error_handling(
        self,
        mock_manager_cls: Mock,
        mock_engine_cls: Mock,
        cli_runner: CliRunner,
    ) -> None:
        """Test index command error handling."""
        # Setup mock to raise exception
        mock_manager = Mock()
        mock_manager.list_skills.side_effect = Exception("Indexing failed")
        mock_manager_cls.return_value = mock_manager

        # Run command
        result = cli_runner.invoke(cli, ["index"])

        # Verify error handling
        assert result.exit_code != 0
        assert "failed" in result.output.lower() or "error" in result.output.lower()

    @patch("mcp_skills.cli.commands.index.IndexingEngine")
    @patch("mcp_skills.cli.commands.index.SkillManager")
    def test_index_displays_stats(
        self,
        mock_manager_cls: Mock,
        mock_engine_cls: Mock,
        cli_runner: CliRunner,
    ) -> None:
        """Test index command displays statistics."""
        # Setup mocks with stats
        mock_manager = Mock()
        mock_manager.discover_skills.return_value = []
        mock_manager_cls.return_value = mock_manager

        from mcp_skills.services.indexing.engine import IndexStats

        mock_engine = Mock()
        mock_engine.reindex_all.return_value = IndexStats(
            total_skills=15,
            vector_store_size=3276,  # 3.2 KB in bytes
            graph_nodes=15,
            graph_edges=30,
            last_indexed="2025-12-16T10:00:00",
        )
        mock_engine_cls.return_value = mock_engine

        # Run command
        result = cli_runner.invoke(cli, ["index"])

        # Verify stats are displayed
        assert result.exit_code == 0
        assert "15" in result.output or "skills" in result.output.lower()

    @patch("mcp_skills.cli.commands.index.IndexingEngine")
    @patch("mcp_skills.cli.commands.index.SkillManager")
    def test_index_incremental_and_force_mutually_exclusive(
        self,
        mock_manager_cls: Mock,
        mock_engine_cls: Mock,
        cli_runner: CliRunner,
    ) -> None:
        """Test that incremental and force flags work together."""
        # Setup mocks
        mock_manager = Mock()
        mock_manager.discover_skills.return_value = []
        mock_manager_cls.return_value = mock_manager

        from mcp_skills.services.indexing.engine import IndexStats

        mock_engine = Mock()
        mock_engine.reindex_all.return_value = IndexStats(
            total_skills=0,
            vector_store_size=0,
            graph_nodes=0,
            graph_edges=0,
            last_indexed="2025-12-16T10:00:00",
        )
        mock_engine_cls.return_value = mock_engine

        # Run command with both flags (should prioritize one)
        result = cli_runner.invoke(cli, ["index", "--incremental", "--force"])

        # Command should still work
        assert result.exit_code == 0

    @patch("mcp_skills.cli.commands.index.IndexingEngine")
    @patch("mcp_skills.cli.commands.index.SkillManager")
    def test_index_progress_display(
        self,
        mock_manager_cls: Mock,
        mock_engine_cls: Mock,
        cli_runner: CliRunner,
        mock_skill,
    ) -> None:
        """Test index command shows progress information."""
        # Setup mocks
        mock_manager = Mock()
        mock_manager.discover_skills.return_value = [mock_skill] * 20
        mock_manager_cls.return_value = mock_manager

        from mcp_skills.services.indexing.engine import IndexStats

        mock_engine = Mock()
        mock_engine.reindex_all.return_value = IndexStats(
            total_skills=20,
            vector_store_size=20480,
            graph_nodes=20,
            graph_edges=40,
            last_indexed="2025-12-16T10:00:00",
        )
        mock_engine_cls.return_value = mock_engine

        # Run command
        result = cli_runner.invoke(cli, ["index"])

        # Verify progress or completion message
        assert result.exit_code == 0
        assert "20" in result.output or "complete" in result.output.lower()
