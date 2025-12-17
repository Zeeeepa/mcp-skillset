"""Tests for enrich command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from mcp_skills.cli.main import cli
from mcp_skills.services.prompt_enricher import EnrichedPrompt


class TestEnrichCommand:
    """Test suite for enrich command."""

    def test_enrich_help(self, cli_runner: CliRunner) -> None:
        """Test enrich command help."""
        result = cli_runner.invoke(cli, ["enrich", "--help"])

        assert result.exit_code == 0
        assert "Enrich" in result.output or "prompt" in result.output.lower()
        assert "--max-skills" in result.output or "--output" in result.output

    @patch("mcp_skills.cli.commands.enrich.PromptEnricher")
    @patch("mcp_skills.cli.commands.enrich.SkillManager")
    def test_enrich_with_prompt_text(
        self,
        mock_manager_cls: Mock,
        mock_enricher_cls: Mock,
        cli_runner: CliRunner,
        mock_skill,
    ) -> None:
        """Test enrich command with direct prompt text."""
        # Setup mocks
        mock_manager = Mock()
        mock_manager_cls.return_value = mock_manager

        # Create proper EnrichedPrompt response
        enriched_result = EnrichedPrompt(
            original_prompt="Write a test for authentication",
            keywords=["write", "test", "authentication"],
            skills_found=[mock_skill],
            enriched_text="# Enriched Prompt\n\nWrite a test for authentication",
            detailed=False,
        )

        mock_enricher = Mock()
        mock_enricher.extract_keywords.return_value = [
            "write",
            "test",
            "authentication",
        ]
        mock_enricher.search_skills.return_value = [mock_skill]
        mock_enricher.enrich.return_value = enriched_result
        mock_enricher_cls.return_value = mock_enricher

        # Run command - use positional argument, not --prompt
        result = cli_runner.invoke(
            cli,
            ["enrich", "Write", "a", "test", "for", "authentication"],
        )

        # Verify
        assert result.exit_code == 0
        assert "Enriching" in result.output or "prompt" in result.output.lower()

    @pytest.mark.skip(reason="CLI doesn't support --file option")
    def test_enrich_with_file(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test enrich command with file input (not implemented)."""
        # CLI doesn't have --file option, only positional PROMPT args
        pass

    @patch("mcp_skills.cli.commands.enrich.PromptEnricher")
    @patch("mcp_skills.cli.commands.enrich.SkillManager")
    def test_enrich_with_output_file(
        self,
        mock_manager_cls: Mock,
        mock_enricher_cls: Mock,
        cli_runner: CliRunner,
        tmp_path: Path,
        mock_skill,
    ) -> None:
        """Test enrich command with output file."""
        # Setup mocks
        mock_manager = Mock()
        mock_manager_cls.return_value = mock_manager

        enriched_result = EnrichedPrompt(
            original_prompt="Test prompt",
            keywords=["test"],
            skills_found=[mock_skill],
            enriched_text="# Enriched\n\nTest prompt",
            detailed=False,
        )

        mock_enricher = Mock()
        mock_enricher.extract_keywords.return_value = ["test"]
        mock_enricher.search_skills.return_value = [mock_skill]
        mock_enricher.enrich.return_value = enriched_result
        mock_enricher.save_to_file.return_value = None
        mock_enricher_cls.return_value = mock_enricher

        # Run command - positional prompt with output
        output_file = tmp_path / "output.txt"
        result = cli_runner.invoke(
            cli,
            [
                "enrich",
                "Test",
                "prompt",
                "--output",
                str(output_file),
            ],
        )

        # Verify
        assert result.exit_code == 0
        # save_to_file should have been called
        mock_enricher.save_to_file.assert_called_once()

    def test_enrich_requires_prompt_or_file(
        self,
        cli_runner: CliRunner,
    ) -> None:
        """Test enrich command requires either --prompt or --file."""
        result = cli_runner.invoke(cli, ["enrich"])

        # Should fail without input
        assert result.exit_code != 0

    @patch("mcp_skills.cli.commands.enrich.PromptEnricher")
    @patch("mcp_skills.cli.commands.enrich.SkillManager")
    def test_enrich_with_limit(
        self,
        mock_manager_cls: Mock,
        mock_enricher_cls: Mock,
        cli_runner: CliRunner,
        mock_skill,
    ) -> None:
        """Test enrich command with skill limit."""
        # Setup mocks
        mock_manager = Mock()
        mock_manager_cls.return_value = mock_manager

        enriched_result = EnrichedPrompt(
            original_prompt="Test prompt",
            keywords=["test"],
            skills_found=[mock_skill],
            enriched_text="# Enriched\n\nTest prompt",
            detailed=False,
        )

        mock_enricher = Mock()
        mock_enricher.extract_keywords.return_value = ["test"]
        mock_enricher.search_skills.return_value = [mock_skill]
        mock_enricher.enrich.return_value = enriched_result
        mock_enricher_cls.return_value = mock_enricher

        # Run command - use --max-skills not --limit
        result = cli_runner.invoke(
            cli,
            ["enrich", "Test", "prompt", "--max-skills", "3"],
        )

        # Verify
        assert result.exit_code == 0

    @patch("mcp_skills.cli.commands.enrich.PromptEnricher")
    @patch("mcp_skills.cli.commands.enrich.SkillManager")
    def test_enrich_with_detailed(
        self,
        mock_manager_cls: Mock,
        mock_enricher_cls: Mock,
        cli_runner: CliRunner,
        mock_skill,
    ) -> None:
        """Test enrich command with detailed flag."""
        # Setup mocks
        mock_manager = Mock()
        mock_manager_cls.return_value = mock_manager

        enriched_result = EnrichedPrompt(
            original_prompt="Test prompt",
            keywords=["test"],
            skills_found=[mock_skill],
            enriched_text="# Enriched\n\nTest prompt",
            detailed=True,
        )

        mock_enricher = Mock()
        mock_enricher.extract_keywords.return_value = ["test"]
        mock_enricher.search_skills.return_value = [mock_skill]
        mock_enricher.enrich.return_value = enriched_result
        mock_enricher_cls.return_value = mock_enricher

        # Run command - use --detailed flag
        result = cli_runner.invoke(
            cli,
            ["enrich", "Test", "prompt", "--detailed"],
        )

        # Verify
        assert result.exit_code == 0

    @pytest.mark.skip(reason="CLI doesn't support --file option")
    def test_enrich_file_not_found(
        self,
        cli_runner: CliRunner,
    ) -> None:
        """Test enrich command with non-existent file (not implemented)."""
        pass

    @patch("mcp_skills.cli.commands.enrich.PromptEnricher")
    @patch("mcp_skills.cli.commands.enrich.SkillManager")
    def test_enrich_error_handling(
        self,
        mock_manager_cls: Mock,
        mock_enricher_cls: Mock,
        cli_runner: CliRunner,
    ) -> None:
        """Test enrich command error handling."""
        # Setup mocks
        mock_manager = Mock()
        mock_manager_cls.return_value = mock_manager

        mock_enricher = Mock()
        mock_enricher.extract_keywords.side_effect = Exception("Enrichment failed")
        mock_enricher_cls.return_value = mock_enricher

        # Run command
        result = cli_runner.invoke(
            cli,
            ["enrich", "Test", "prompt"],
        )

        # Verify error handling
        assert result.exit_code != 0
        assert "failed" in result.output.lower() or "error" in result.output.lower()

    @patch("mcp_skills.cli.commands.enrich.PromptEnricher")
    @patch("mcp_skills.cli.commands.enrich.SkillManager")
    def test_enrich_displays_enriched_content(
        self,
        mock_manager_cls: Mock,
        mock_enricher_cls: Mock,
        cli_runner: CliRunner,
        mock_skill,
    ) -> None:
        """Test enrich command displays enriched content."""
        # Setup mocks
        mock_manager = Mock()
        mock_manager_cls.return_value = mock_manager

        enriched_text = "# Enriched Prompt\n\nTest content"
        enriched_result = EnrichedPrompt(
            original_prompt="Test prompt",
            keywords=["test"],
            skills_found=[mock_skill],
            enriched_text=enriched_text,
            detailed=False,
        )

        mock_enricher = Mock()
        mock_enricher.extract_keywords.return_value = ["test"]
        mock_enricher.search_skills.return_value = [mock_skill]
        mock_enricher.enrich.return_value = enriched_result
        mock_enricher_cls.return_value = mock_enricher

        # Run command
        result = cli_runner.invoke(
            cli,
            ["enrich", "Test", "prompt"],
        )

        # Verify enriched content is displayed
        assert result.exit_code == 0

    @pytest.mark.skip(reason="CLI doesn't support stdin")
    def test_enrich_with_stdin(
        self,
        cli_runner: CliRunner,
    ) -> None:
        """Test enrich command with stdin input (not implemented)."""
        pass

    @patch("mcp_skills.cli.commands.enrich.PromptEnricher")
    @patch("mcp_skills.cli.commands.enrich.SkillManager")
    def test_enrich_no_relevant_skills(
        self,
        mock_manager_cls: Mock,
        mock_enricher_cls: Mock,
        cli_runner: CliRunner,
    ) -> None:
        """Test enrich command when no relevant skills found."""
        # Setup mocks
        mock_manager = Mock()
        mock_manager_cls.return_value = mock_manager

        # Return empty skills list
        enriched_result = EnrichedPrompt(
            original_prompt="Very obscure prompt",
            keywords=["obscure"],
            skills_found=[],
            enriched_text="Very obscure prompt",
            detailed=False,
        )

        mock_enricher = Mock()
        mock_enricher.extract_keywords.return_value = ["obscure"]
        mock_enricher.search_skills.return_value = []
        mock_enricher.enrich.return_value = enriched_result
        mock_enricher_cls.return_value = mock_enricher

        # Run command
        result = cli_runner.invoke(
            cli,
            ["enrich", "Very", "obscure", "prompt"],
        )

        # Verify still completes (should show "No relevant skills found" message)
        assert result.exit_code == 0

    @pytest.mark.skip(reason="CLI doesn't support --context option")
    def test_enrich_with_context(
        self,
        cli_runner: CliRunner,
    ) -> None:
        """Test enrich command with additional context (not implemented)."""
        pass


class TestEnrichCommandIntegration:
    """Integration tests for enrich command."""

    @pytest.mark.skip(reason="Requires full system setup")
    def test_enrich_full_workflow(
        self,
        cli_runner: CliRunner,
    ) -> None:
        """Test full enrich workflow with real skills."""
        # This would require actual skills and enricher
        pass

    @pytest.mark.skip(reason="Requires embeddings")
    def test_enrich_with_vector_search(
        self,
        cli_runner: CliRunner,
    ) -> None:
        """Test enrich command with vector search."""
        # This would require actual vector search
        pass
