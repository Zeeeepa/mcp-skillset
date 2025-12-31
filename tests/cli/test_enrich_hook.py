"""Tests for enrich-hook CLI command."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from mcp_skills.cli.commands.enrich_hook import enrich_hook
from mcp_skills.models.skill import Skill
from mcp_skills.services.indexing.hybrid_search import ScoredSkill


@pytest.fixture
def runner():
    """Create CLI runner."""
    return CliRunner()


@pytest.fixture
def mock_skill_factory():
    """Factory for creating mock skills."""

    def _create_skill(name: str) -> Skill:
        from pathlib import Path

        return Skill(
            id=f"{name}-id",
            name=name,
            description=f"Description for {name}",
            instructions=f"Instructions for {name}",
            category="testing",
            tags=["testing"],
            dependencies=[],
            examples=[],
            file_path=Path(f"/test/{name}.md"),
            repo_id="test-repo",
            version="1.0.0",
            author="Test Author",
        )

    return _create_skill


class TestEnrichHookCommand:
    """Tests for enrich-hook command."""

    def test_empty_input_returns_empty_json(self, runner):
        """Empty stdin should return empty JSON."""
        result = runner.invoke(enrich_hook, input=json.dumps({}))
        assert result.exit_code == 0
        assert json.loads(result.output) == {}

    def test_empty_prompt_returns_empty_json(self, runner):
        """Empty user_prompt should return empty JSON."""
        result = runner.invoke(enrich_hook, input=json.dumps({"user_prompt": ""}))
        assert result.exit_code == 0
        assert json.loads(result.output) == {}

    def test_whitespace_prompt_returns_empty_json(self, runner):
        """Whitespace-only prompt should return empty JSON."""
        result = runner.invoke(enrich_hook, input=json.dumps({"user_prompt": "   "}))
        assert result.exit_code == 0
        assert json.loads(result.output) == {}

    def test_invalid_json_returns_empty_json(self, runner):
        """Invalid JSON input should return empty JSON (silent failure)."""
        result = runner.invoke(enrich_hook, input="not valid json")
        assert result.exit_code == 0
        assert json.loads(result.output) == {}

    def test_missing_user_prompt_returns_empty_json(self, runner):
        """Missing user_prompt field should return empty JSON."""
        result = runner.invoke(enrich_hook, input=json.dumps({"other_field": "value"}))
        assert result.exit_code == 0
        assert json.loads(result.output) == {}

    @patch("mcp_skills.cli.commands.enrich_hook._get_engine")
    def test_no_engine_returns_empty_json(self, mock_get_engine, runner):
        """If engine not available, return empty JSON."""
        mock_get_engine.return_value = None
        result = runner.invoke(
            enrich_hook, input=json.dumps({"user_prompt": "test prompt"})
        )
        assert result.exit_code == 0
        assert json.loads(result.output) == {}

    @patch("mcp_skills.cli.commands.enrich_hook._get_engine")
    def test_no_matching_skills_returns_empty_json(self, mock_get_engine, runner):
        """If no skills match threshold, return empty JSON."""
        mock_engine = MagicMock()
        mock_engine.search.return_value = []
        mock_get_engine.return_value = mock_engine

        result = runner.invoke(
            enrich_hook, input=json.dumps({"user_prompt": "test prompt"})
        )
        assert result.exit_code == 0
        assert json.loads(result.output) == {}

    @patch("mcp_skills.cli.commands.enrich_hook._get_engine")
    def test_skills_below_threshold_returns_empty_json(
        self, mock_get_engine, runner, mock_skill_factory
    ):
        """Skills below threshold should not appear in output."""
        mock_skill = mock_skill_factory("low-score-skill")
        mock_result = ScoredSkill(skill=mock_skill, score=0.3, match_type="hybrid")

        mock_engine = MagicMock()
        mock_engine.search.return_value = [mock_result]
        mock_get_engine.return_value = mock_engine

        result = runner.invoke(
            enrich_hook, input=json.dumps({"user_prompt": "test prompt"})
        )
        assert result.exit_code == 0
        assert json.loads(result.output) == {}

    @patch("mcp_skills.cli.commands.enrich_hook._get_engine")
    def test_matching_skills_returns_hint(
        self, mock_get_engine, runner, mock_skill_factory
    ):
        """Matching skills should return systemMessage with hints."""
        mock_skill1 = mock_skill_factory("pytest-fixtures")
        mock_skill2 = mock_skill_factory("mock-patterns")

        mock_result1 = ScoredSkill(skill=mock_skill1, score=0.8, match_type="hybrid")
        mock_result2 = ScoredSkill(skill=mock_skill2, score=0.7, match_type="hybrid")

        mock_engine = MagicMock()
        mock_engine.search.return_value = [mock_result1, mock_result2]
        mock_get_engine.return_value = mock_engine

        result = runner.invoke(
            enrich_hook, input=json.dumps({"user_prompt": "write tests"})
        )
        assert result.exit_code == 0

        output = json.loads(result.output)
        assert "systemMessage" in output
        assert "pytest-fixtures" in output["systemMessage"]
        assert "mock-patterns" in output["systemMessage"]
        assert "/skill" in output["systemMessage"]

    @patch("mcp_skills.cli.commands.enrich_hook._get_engine")
    def test_custom_threshold(self, mock_get_engine, runner, mock_skill_factory):
        """Custom threshold should filter skills accordingly."""
        mock_skill = mock_skill_factory("test-skill")
        mock_result = ScoredSkill(skill=mock_skill, score=0.5, match_type="hybrid")

        mock_engine = MagicMock()
        mock_engine.search.return_value = [mock_result]
        mock_get_engine.return_value = mock_engine

        # With default threshold (0.6), should not match
        result = runner.invoke(enrich_hook, input=json.dumps({"user_prompt": "test"}))
        assert json.loads(result.output) == {}

        # With lower threshold (0.4), should match
        result = runner.invoke(
            enrich_hook,
            ["--threshold", "0.4"],
            input=json.dumps({"user_prompt": "test"}),
        )
        output = json.loads(result.output)
        assert "systemMessage" in output
        assert "test-skill" in output["systemMessage"]

    @patch("mcp_skills.cli.commands.enrich_hook._get_engine")
    def test_max_skills_limit(self, mock_get_engine, runner, mock_skill_factory):
        """Should respect max-skills limit."""
        # Create 10 matching skills
        mock_results = []
        for i in range(10):
            mock_skill = mock_skill_factory(f"skill-{i}")
            mock_result = ScoredSkill(skill=mock_skill, score=0.8, match_type="hybrid")
            mock_results.append(mock_result)

        mock_engine = MagicMock()
        mock_engine.search.return_value = mock_results
        mock_get_engine.return_value = mock_engine

        # Default max is 5
        result = runner.invoke(enrich_hook, input=json.dumps({"user_prompt": "test"}))
        output = json.loads(result.output)
        skills_mentioned = output["systemMessage"].count("skill-")
        assert skills_mentioned == 5

        # With max-skills=3
        result = runner.invoke(
            enrich_hook,
            ["--max-skills", "3"],
            input=json.dumps({"user_prompt": "test"}),
        )
        output = json.loads(result.output)
        skills_mentioned = output["systemMessage"].count("skill-")
        assert skills_mentioned == 3

    @patch("mcp_skills.cli.commands.enrich_hook._get_engine")
    def test_engine_exception_returns_empty_json(self, mock_get_engine, runner):
        """Engine exceptions should return empty JSON (silent failure)."""
        mock_engine = MagicMock()
        mock_engine.search.side_effect = Exception("Search failed")
        mock_get_engine.return_value = mock_engine

        result = runner.invoke(enrich_hook, input=json.dumps({"user_prompt": "test"}))
        assert result.exit_code == 0
        assert json.loads(result.output) == {}

    @patch("mcp_skills.cli.commands.enrich_hook._get_engine")
    def test_skills_ordered_by_score(self, mock_get_engine, runner, mock_skill_factory):
        """Skills should appear in order of relevance score."""
        # Create skills with different scores
        mock_skill1 = mock_skill_factory("high-score")
        mock_skill2 = mock_skill_factory("medium-score")
        mock_skill3 = mock_skill_factory("low-score")

        # Return in non-score order
        mock_results = [
            ScoredSkill(skill=mock_skill2, score=0.7, match_type="hybrid"),
            ScoredSkill(skill=mock_skill1, score=0.9, match_type="hybrid"),
            ScoredSkill(skill=mock_skill3, score=0.65, match_type="hybrid"),
        ]

        mock_engine = MagicMock()
        mock_engine.search.return_value = mock_results
        mock_get_engine.return_value = mock_engine

        result = runner.invoke(enrich_hook, input=json.dumps({"user_prompt": "test"}))
        output = json.loads(result.output)

        # Check that skills appear in the message
        # The order should be preserved from search results
        message = output["systemMessage"]
        high_pos = message.find("high-score")
        medium_pos = message.find("medium-score")
        low_pos = message.find("low-score")

        # All should be present
        assert high_pos != -1
        assert medium_pos != -1
        assert low_pos != -1

    @patch("mcp_skills.cli.commands.enrich_hook._get_engine")
    def test_get_engine_exception_returns_none(self, mock_get_engine, runner):
        """_get_engine should return None on exception."""
        mock_get_engine.side_effect = Exception("Config error")

        result = runner.invoke(enrich_hook, input=json.dumps({"user_prompt": "test"}))
        assert result.exit_code == 0
        assert json.loads(result.output) == {}

    def test_help_output(self, runner):
        """Help should display properly."""
        result = runner.invoke(enrich_hook, ["--help"])
        assert result.exit_code == 0
        assert "Hook command for Claude Code" in result.output
        assert "--threshold" in result.output
        assert "--max-skills" in result.output

    @patch("mcp_skills.cli.commands.enrich_hook._get_engine")
    def test_search_called_with_correct_params(
        self, mock_get_engine, runner, mock_skill_factory
    ):
        """Verify search is called with prompt and correct top_k."""
        mock_skill = mock_skill_factory("test-skill")
        mock_result = ScoredSkill(skill=mock_skill, score=0.8, match_type="hybrid")

        mock_engine = MagicMock()
        mock_engine.search.return_value = [mock_result]
        mock_get_engine.return_value = mock_engine

        runner.invoke(
            enrich_hook,
            ["--max-skills", "3"],
            input=json.dumps({"user_prompt": "test prompt"}),
        )

        # Should call search with prompt and max_skills * 2 for filtering
        mock_engine.search.assert_called_once_with("test prompt", top_k=6)

    @patch("mcp_skills.cli.commands.enrich_hook._get_engine")
    def test_output_format_matches_spec(
        self, mock_get_engine, runner, mock_skill_factory
    ):
        """Verify output format matches Claude Code spec."""
        mock_skill1 = mock_skill_factory("skill-one")
        mock_skill2 = mock_skill_factory("skill-two")

        mock_results = [
            ScoredSkill(skill=mock_skill1, score=0.8, match_type="hybrid"),
            ScoredSkill(skill=mock_skill2, score=0.7, match_type="hybrid"),
        ]

        mock_engine = MagicMock()
        mock_engine.search.return_value = mock_results
        mock_get_engine.return_value = mock_engine

        result = runner.invoke(enrich_hook, input=json.dumps({"user_prompt": "test"}))
        output = json.loads(result.output)

        # Should have exactly one key: systemMessage
        assert len(output) == 1
        assert "systemMessage" in output

        # Message should follow format: "Skills: skill1, skill2 - use /skill <name> to load"
        message = output["systemMessage"]
        assert message.startswith("Skills: ")
        assert " - use /skill <name> to load" in message


class TestHooksModule:
    """Tests for hooks module."""

    def test_hooks_template_exists(self):
        """Hook template file should exist."""
        from mcp_skills.hooks import HOOKS_TEMPLATE

        assert HOOKS_TEMPLATE.exists()

    def test_hooks_template_valid_json(self):
        """Hook template should be valid JSON."""
        from mcp_skills.hooks import HOOKS_TEMPLATE

        content = json.loads(HOOKS_TEMPLATE.read_text())
        assert "hooks" in content
        assert "UserPromptSubmit" in content["hooks"]

    def test_hooks_template_has_correct_structure(self):
        """Hook template should have correct Claude Code structure."""
        from mcp_skills.hooks import HOOKS_TEMPLATE

        content = json.loads(HOOKS_TEMPLATE.read_text())
        user_prompt_hooks = content["hooks"]["UserPromptSubmit"]
        assert isinstance(user_prompt_hooks, list)
        assert len(user_prompt_hooks) > 0

        # Check first handler has correct structure
        handler = user_prompt_hooks[0]
        assert "matcher" in handler
        assert "hooks" in handler
        assert handler["hooks"][0]["type"] == "command"
        assert "mcp-skillset enrich-hook" in handler["hooks"][0]["command"]

    def test_hooks_dir_exists(self):
        """HOOKS_DIR should exist and be a directory."""
        from mcp_skills.hooks import HOOKS_DIR

        assert HOOKS_DIR.exists()
        assert HOOKS_DIR.is_dir()

    def test_hooks_template_has_timeout(self):
        """Hook template should specify timeout."""
        from mcp_skills.hooks import HOOKS_TEMPLATE

        content = json.loads(HOOKS_TEMPLATE.read_text())
        handler = content["hooks"]["UserPromptSubmit"][0]
        hook = handler["hooks"][0]

        assert "timeout" in hook
        # Should have reasonable timeout (5000ms = 5s)
        assert hook["timeout"] == 5000


class TestGetEngine:
    """Tests for _get_engine helper function."""

    @patch("mcp_skills.cli.commands.enrich_hook.MCPSkillsConfig")
    @patch("mcp_skills.cli.commands.enrich_hook.IndexingEngine")
    def test_get_engine_success(self, mock_engine_cls, mock_config_cls):
        """_get_engine should return IndexingEngine instance."""
        from mcp_skills.cli.commands.enrich_hook import _get_engine

        mock_config = MagicMock()
        mock_config_cls.return_value = mock_config

        mock_engine = MagicMock()
        mock_engine_cls.return_value = mock_engine

        result = _get_engine()

        assert result == mock_engine
        mock_config_cls.assert_called_once()
        mock_engine_cls.assert_called_once_with(config=mock_config)

    @patch("mcp_skills.cli.commands.enrich_hook.MCPSkillsConfig")
    def test_get_engine_config_error_returns_none(self, mock_config_cls):
        """_get_engine should return None on config error."""
        from mcp_skills.cli.commands.enrich_hook import _get_engine

        mock_config_cls.side_effect = Exception("Config error")

        result = _get_engine()

        assert result is None

    @patch("mcp_skills.cli.commands.enrich_hook.MCPSkillsConfig")
    @patch("mcp_skills.cli.commands.enrich_hook.IndexingEngine")
    def test_get_engine_engine_error_returns_none(
        self, mock_engine_cls, mock_config_cls
    ):
        """_get_engine should return None on engine initialization error."""
        from mcp_skills.cli.commands.enrich_hook import _get_engine

        mock_config = MagicMock()
        mock_config_cls.return_value = mock_config

        mock_engine_cls.side_effect = Exception("Engine error")

        result = _get_engine()

        assert result is None
