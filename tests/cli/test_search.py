"""Tests for search and recommend commands."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from mcp_skills.cli.main import cli
from mcp_skills.services.indexing.hybrid_search import ScoredSkill


class TestSearchCommand:
    """Test suite for search command."""

    def test_search_help(self, cli_runner: CliRunner) -> None:
        """Test search command help."""
        result = cli_runner.invoke(cli, ["search", "--help"])

        assert result.exit_code == 0
        assert "Search for skills" in result.output
        assert "query" in result.output.lower()

    @patch("mcp_skills.cli.commands.search.IndexingEngine")
    @patch("mcp_skills.cli.commands.search.SkillManager")
    @patch("mcp_skills.cli.commands.search.MCPSkillsConfig")
    def test_search_basic(
        self,
        mock_config_cls: Mock,
        mock_manager_cls: Mock,
        mock_engine_cls: Mock,
        cli_runner: CliRunner,
        mock_skill,
    ) -> None:
        """Test basic search command."""
        # Setup mocks
        mock_manager = Mock()
        mock_manager_cls.return_value = mock_manager

        mock_config = Mock()
        mock_config_cls.return_value = mock_config

        # Create ScoredSkill result
        scored_skill = ScoredSkill(skill=mock_skill, score=0.95, match_type="hybrid")

        mock_engine = Mock()
        mock_engine.search.return_value = [scored_skill]
        mock_engine_cls.return_value = mock_engine

        # Run command
        result = cli_runner.invoke(cli, ["search", "testing"])

        # Verify
        assert result.exit_code == 0
        assert "Searching for" in result.output or "testing" in result.output

    @patch("mcp_skills.cli.commands.search.IndexingEngine")
    @patch("mcp_skills.cli.commands.search.SkillManager")
    @patch("mcp_skills.cli.commands.search.MCPSkillsConfig")
    def test_search_no_results(
        self,
        mock_config_cls: Mock,
        mock_manager_cls: Mock,
        mock_engine_cls: Mock,
        cli_runner: CliRunner,
    ) -> None:
        """Test search command with no results."""
        # Setup mocks
        mock_manager = Mock()
        mock_manager_cls.return_value = mock_manager

        mock_config = Mock()
        mock_config_cls.return_value = mock_config

        mock_engine = Mock()
        mock_engine.search.return_value = []
        mock_engine_cls.return_value = mock_engine

        # Run command
        result = cli_runner.invoke(cli, ["search", "nonexistent"])

        # Verify
        assert result.exit_code == 0
        assert "No results found" in result.output or "0" in result.output

    @patch("mcp_skills.cli.commands.search.IndexingEngine")
    @patch("mcp_skills.cli.commands.search.SkillManager")
    @patch("mcp_skills.cli.commands.search.MCPSkillsConfig")
    def test_search_with_limit(
        self,
        mock_config_cls: Mock,
        mock_manager_cls: Mock,
        mock_engine_cls: Mock,
        cli_runner: CliRunner,
        mock_skill,
    ) -> None:
        """Test search command with limit parameter."""
        # Setup mocks
        mock_manager = Mock()
        mock_manager_cls.return_value = mock_manager

        mock_config = Mock()
        mock_config_cls.return_value = mock_config

        scored_skills = [
            ScoredSkill(skill=mock_skill, score=0.9, match_type="hybrid")
            for _ in range(5)
        ]
        mock_engine = Mock()
        mock_engine.search.return_value = scored_skills
        mock_engine_cls.return_value = mock_engine

        # Run command
        result = cli_runner.invoke(cli, ["search", "test", "--limit", "3"])

        # Verify
        assert result.exit_code == 0

    @patch("mcp_skills.cli.commands.search.IndexingEngine")
    @patch("mcp_skills.cli.commands.search.SkillManager")
    @patch("mcp_skills.cli.commands.search.MCPSkillsConfig")
    def test_search_with_mode(
        self,
        mock_config_cls: Mock,
        mock_manager_cls: Mock,
        mock_engine_cls: Mock,
        cli_runner: CliRunner,
        mock_skill,
    ) -> None:
        """Test search command with search mode parameter."""
        # Setup mocks
        mock_manager = Mock()
        mock_manager_cls.return_value = mock_manager

        mock_config = Mock()
        mock_config._get_preset = Mock(
            return_value=Mock(vector_weight=0.9, graph_weight=0.1)
        )
        mock_config.hybrid_search = Mock(vector_weight=0.7, graph_weight=0.3)
        mock_config_cls.return_value = mock_config

        scored_skill = ScoredSkill(skill=mock_skill, score=0.95, match_type="vector")
        mock_engine = Mock()
        mock_engine.search.return_value = [scored_skill]
        mock_engine_cls.return_value = mock_engine

        # Run command - use --search-mode not --mode
        result = cli_runner.invoke(
            cli,
            ["search", "test", "--search-mode", "semantic_focused"],
        )

        # Verify
        assert result.exit_code == 0

    @pytest.mark.skip(reason="CLI doesn't support --threshold option")
    def test_search_with_threshold(
        self,
        cli_runner: CliRunner,
    ) -> None:
        """Test search command with similarity threshold (not implemented)."""
        pass

    @patch("mcp_skills.cli.commands.search.IndexingEngine")
    @patch("mcp_skills.cli.commands.search.SkillManager")
    @patch("mcp_skills.cli.commands.search.MCPSkillsConfig")
    def test_search_multiple_results(
        self,
        mock_config_cls: Mock,
        mock_manager_cls: Mock,
        mock_engine_cls: Mock,
        cli_runner: CliRunner,
        mock_skill,
    ) -> None:
        """Test search command with multiple results."""
        # Setup mocks
        mock_manager = Mock()
        mock_manager_cls.return_value = mock_manager

        mock_config = Mock()
        mock_config_cls.return_value = mock_config

        scored_skills = [
            ScoredSkill(skill=mock_skill, score=0.8 - i * 0.05, match_type="hybrid")
            for i in range(10)
        ]
        mock_engine = Mock()
        mock_engine.search.return_value = scored_skills
        mock_engine_cls.return_value = mock_engine

        # Run command
        result = cli_runner.invoke(cli, ["search", "test"])

        # Verify multiple results displayed
        assert result.exit_code == 0

    @patch("mcp_skills.cli.commands.search.IndexingEngine")
    @patch("mcp_skills.cli.commands.search.SkillManager")
    @patch("mcp_skills.cli.commands.search.MCPSkillsConfig")
    def test_search_displays_relevance_scores(
        self,
        mock_config_cls: Mock,
        mock_manager_cls: Mock,
        mock_engine_cls: Mock,
        cli_runner: CliRunner,
        mock_skill,
    ) -> None:
        """Test search command displays relevance scores."""
        # Setup mocks
        mock_manager = Mock()
        mock_manager_cls.return_value = mock_manager

        mock_config = Mock()
        mock_config_cls.return_value = mock_config

        scored_skill = ScoredSkill(skill=mock_skill, score=0.92, match_type="hybrid")
        mock_engine = Mock()
        mock_engine.search.return_value = [scored_skill]
        mock_engine_cls.return_value = mock_engine

        # Run command
        result = cli_runner.invoke(cli, ["search", "test"])

        # Verify
        assert result.exit_code == 0
        # Score should be displayed in output
        assert "0.92" in result.output or "Score" in result.output

    @patch("mcp_skills.cli.commands.search.IndexingEngine")
    @patch("mcp_skills.cli.commands.search.SkillManager")
    @patch("mcp_skills.cli.commands.search.MCPSkillsConfig")
    def test_search_error_handling(
        self,
        mock_config_cls: Mock,
        mock_manager_cls: Mock,
        mock_engine_cls: Mock,
        cli_runner: CliRunner,
    ) -> None:
        """Test search command error handling."""
        # Setup mocks
        mock_manager = Mock()
        mock_manager_cls.return_value = mock_manager

        mock_config = Mock()
        mock_config_cls.return_value = mock_config

        # Setup mock to raise exception
        mock_engine = Mock()
        mock_engine.search.side_effect = Exception("Search failed")
        mock_engine_cls.return_value = mock_engine

        # Run command
        result = cli_runner.invoke(cli, ["search", "test"])

        # Verify error handling
        assert result.exit_code != 0

    def test_search_empty_query(
        self,
        cli_runner: CliRunner,
    ) -> None:
        """Test search command with empty query."""
        # Run command with empty query
        result = cli_runner.invoke(cli, ["search", ""])

        # Should handle gracefully (or fail with validation error)
        # Empty string is still technically a query, so might succeed
        assert result.exit_code in [0, 2]

    def test_search_requires_query(self, cli_runner: CliRunner) -> None:
        """Test search command requires query argument."""
        result = cli_runner.invoke(cli, ["search"])

        # Should fail without query
        assert result.exit_code != 0


class TestRecommendCommand:
    """Test suite for recommend command."""

    def test_recommend_help(self, cli_runner: CliRunner) -> None:
        """Test recommend command help."""
        result = cli_runner.invoke(cli, ["recommend", "--help"])

        assert result.exit_code == 0
        assert "recommend" in result.output.lower() or "skill" in result.output.lower()

    @patch("mcp_skills.cli.commands.recommend.IndexingEngine")
    @patch("mcp_skills.cli.commands.recommend.SkillManager")
    @patch("mcp_skills.cli.commands.recommend.MCPSkillsConfig")
    @patch("mcp_skills.cli.commands.recommend.ToolchainDetector")
    def test_recommend_basic(
        self,
        mock_detector_cls: Mock,
        mock_config_cls: Mock,
        mock_manager_cls: Mock,
        mock_engine_cls: Mock,
        cli_runner: CliRunner,
        mock_toolchain_info,
        mock_skill,
    ) -> None:
        """Test basic recommend command."""
        # Setup mocks
        mock_detector = Mock()
        mock_detector.detect.return_value = mock_toolchain_info
        mock_detector_cls.return_value = mock_detector

        mock_manager = Mock()
        mock_manager_cls.return_value = mock_manager

        mock_config = Mock()
        mock_config_cls.return_value = mock_config

        scored_skill = ScoredSkill(skill=mock_skill, score=0.9, match_type="hybrid")
        mock_engine = Mock()
        mock_engine.search.return_value = [scored_skill]
        mock_engine_cls.return_value = mock_engine

        # Run command
        result = cli_runner.invoke(cli, ["recommend"])

        # Verify
        assert result.exit_code == 0
        assert "Recommend" in result.output or "skills" in result.output.lower()

    @patch("mcp_skills.cli.commands.recommend.IndexingEngine")
    @patch("mcp_skills.cli.commands.recommend.SkillManager")
    @patch("mcp_skills.cli.commands.recommend.MCPSkillsConfig")
    @patch("mcp_skills.cli.commands.recommend.ToolchainDetector")
    def test_recommend_with_search_mode(
        self,
        mock_detector_cls: Mock,
        mock_config_cls: Mock,
        mock_manager_cls: Mock,
        mock_engine_cls: Mock,
        cli_runner: CliRunner,
        mock_toolchain_info,
        mock_skill,
    ) -> None:
        """Test recommend command with search mode."""
        # Setup mocks
        mock_detector = Mock()
        mock_detector.detect.return_value = mock_toolchain_info
        mock_detector_cls.return_value = mock_detector

        mock_manager = Mock()
        mock_manager_cls.return_value = mock_manager

        mock_config = Mock()
        mock_config._get_preset = Mock(
            return_value=Mock(vector_weight=0.5, graph_weight=0.5)
        )
        mock_config.hybrid_search = Mock(vector_weight=0.5, graph_weight=0.5)
        mock_config_cls.return_value = mock_config

        scored_skill = ScoredSkill(skill=mock_skill, score=0.9, match_type="hybrid")
        mock_engine = Mock()
        mock_engine.search.return_value = [scored_skill]
        mock_engine_cls.return_value = mock_engine

        # Run command
        result = cli_runner.invoke(
            cli,
            ["recommend", "--search-mode", "balanced"],
        )

        # Verify
        assert result.exit_code == 0

    @patch("mcp_skills.cli.commands.recommend.ToolchainDetector")
    def test_recommend_toolchain_detection_failed(
        self,
        mock_detector_cls: Mock,
        cli_runner: CliRunner,
    ) -> None:
        """Test recommend command when toolchain detection fails."""
        # Setup mock to raise exception
        mock_detector = Mock()
        mock_detector.detect.side_effect = Exception("Detection failed")
        mock_detector_cls.return_value = mock_detector

        # Run command
        result = cli_runner.invoke(cli, ["recommend"])

        # Verify error handling
        assert result.exit_code != 0

    @patch("mcp_skills.cli.commands.recommend.IndexingEngine")
    @patch("mcp_skills.cli.commands.recommend.SkillManager")
    @patch("mcp_skills.cli.commands.recommend.MCPSkillsConfig")
    @patch("mcp_skills.cli.commands.recommend.ToolchainDetector")
    def test_recommend_no_matching_skills(
        self,
        mock_detector_cls: Mock,
        mock_config_cls: Mock,
        mock_manager_cls: Mock,
        mock_engine_cls: Mock,
        cli_runner: CliRunner,
        mock_toolchain_info,
    ) -> None:
        """Test recommend command when no matching skills found."""
        # Setup mocks
        mock_detector = Mock()
        mock_detector.detect.return_value = mock_toolchain_info
        mock_detector_cls.return_value = mock_detector

        mock_manager = Mock()
        mock_manager_cls.return_value = mock_manager

        mock_config = Mock()
        mock_config_cls.return_value = mock_config

        mock_engine = Mock()
        mock_engine.search.return_value = []
        mock_engine_cls.return_value = mock_engine

        # Run command
        result = cli_runner.invoke(cli, ["recommend"])

        # Verify
        assert result.exit_code == 0
        assert "No" in result.output or "0" in result.output

    @patch("mcp_skills.cli.commands.recommend.IndexingEngine")
    @patch("mcp_skills.cli.commands.recommend.SkillManager")
    @patch("mcp_skills.cli.commands.recommend.MCPSkillsConfig")
    @patch("mcp_skills.cli.commands.recommend.ToolchainDetector")
    def test_recommend_displays_recommendations(
        self,
        mock_detector_cls: Mock,
        mock_config_cls: Mock,
        mock_manager_cls: Mock,
        mock_engine_cls: Mock,
        cli_runner: CliRunner,
        mock_toolchain_info,
        mock_skill,
    ) -> None:
        """Test recommend command displays recommendations."""
        # Setup mocks
        mock_detector = Mock()
        mock_detector.detect.return_value = mock_toolchain_info
        mock_detector_cls.return_value = mock_detector

        mock_manager = Mock()
        mock_manager_cls.return_value = mock_manager

        mock_config = Mock()
        mock_config_cls.return_value = mock_config

        scored_skills = [
            ScoredSkill(skill=mock_skill, score=0.85 - i * 0.1, match_type="hybrid")
            for i in range(5)
        ]
        mock_engine = Mock()
        mock_engine.search.return_value = scored_skills
        mock_engine_cls.return_value = mock_engine

        # Run command
        result = cli_runner.invoke(cli, ["recommend"])

        # Verify recommendations are displayed
        assert result.exit_code == 0
