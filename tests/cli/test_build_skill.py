"""Tests for build-skill CLI command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from mcp_skills.cli.main import cli


@pytest.fixture
def runner():
    """Create Click CLI runner."""
    return CliRunner()


@pytest.fixture
def mock_builder():
    """Mock SkillBuilder service."""
    with patch("mcp_skills.services.skill_builder.SkillBuilder") as mock:
        builder_instance = MagicMock()
        mock.return_value = builder_instance

        # Default successful build result
        builder_instance.build_skill.return_value = {
            "status": "success",
            "skill_path": str(
                Path.home() / ".claude" / "skills" / "test-skill" / "SKILL.md"
            ),
            "skill_id": "test-skill",
            "message": "Skill 'test-skill' created successfully",
            "warnings": None,
        }

        # Default template list
        builder_instance.list_templates.return_value = [
            "base",
            "web-development",
            "api-development",
            "testing",
        ]

        # Default template context generation
        builder_instance._build_template_context.return_value = {
            "name": "Test Skill",
            "skill_id": "test-skill",
            "description": "Test description",
            "domain": "testing",
            "tags": ["test"],
        }

        # Default template generation
        builder_instance._generate_from_template.return_value = """---
name: test-skill
description: Test description
---

# Test Skill

This is a test skill."""

        yield builder_instance


class TestBuildSkillHelp:
    """Test command help and documentation."""

    def test_help_output(self, runner):
        """Test --help flag displays command documentation."""
        result = runner.invoke(cli, ["build-skill", "--help"])

        assert result.exit_code == 0
        assert "Build a progressive skill from template" in result.output
        assert "--name" in result.output
        assert "--description" in result.output
        assert "--domain" in result.output
        assert "--tags" in result.output
        assert "--template" in result.output
        assert "--interactive" in result.output
        assert "--preview" in result.output
        assert "--no-deploy" in result.output

    def test_help_includes_examples(self, runner):
        """Test help includes usage examples."""
        result = runner.invoke(cli, ["build-skill", "--help"])

        assert "Examples:" in result.output
        assert "mcp-skillset build-skill" in result.output
        assert "--interactive" in result.output


class TestBuildSkillStandardMode:
    """Test standard mode with all required arguments."""

    def test_build_with_all_required_args(self, runner, mock_builder):
        """Test successful build with all required arguments."""
        result = runner.invoke(
            cli,
            [
                "build-skill",
                "--name",
                "FastAPI Testing",
                "--description",
                "Test FastAPI endpoints with pytest",
                "--domain",
                "web development",
            ],
        )

        assert result.exit_code == 0
        assert "✓" in result.output
        assert "test-skill" in result.output
        assert "created successfully" in result.output

        # Verify SkillBuilder was called correctly
        mock_builder.build_skill.assert_called_once()
        call_kwargs = mock_builder.build_skill.call_args.kwargs
        assert call_kwargs["name"] == "FastAPI Testing"
        assert call_kwargs["description"] == "Test FastAPI endpoints with pytest"
        assert call_kwargs["domain"] == "web development"
        assert call_kwargs["deploy"] is True

    def test_build_with_tags(self, runner, mock_builder):
        """Test build with comma-separated tags."""
        result = runner.invoke(
            cli,
            [
                "build-skill",
                "--name",
                "Test Skill",
                "--description",
                "Test description",
                "--domain",
                "testing",
                "--tags",
                "fastapi,pytest,testing",
            ],
        )

        assert result.exit_code == 0

        call_kwargs = mock_builder.build_skill.call_args.kwargs
        assert call_kwargs["tags"] == ["fastapi", "pytest", "testing"]

    def test_build_with_template_selection(self, runner, mock_builder):
        """Test build with specific template."""
        result = runner.invoke(
            cli,
            [
                "build-skill",
                "--name",
                "Test Skill",
                "--description",
                "Test description",
                "--domain",
                "web development",
                "--template",
                "web-development",
            ],
        )

        assert result.exit_code == 0

        call_kwargs = mock_builder.build_skill.call_args.kwargs
        assert call_kwargs["template"] == "web-development"

    def test_build_without_deploy(self, runner, mock_builder):
        """Test --no-deploy flag prevents deployment."""
        # Update mock to return None for skill_path when deploy=False
        mock_builder.build_skill.return_value = {
            "status": "success",
            "skill_path": None,  # No deployment
            "skill_id": "test-skill",
            "message": "Skill 'test-skill' created successfully",
            "warnings": None,
        }

        result = runner.invoke(
            cli,
            [
                "build-skill",
                "--name",
                "Test Skill",
                "--description",
                "Test description",
                "--domain",
                "testing",
                "--no-deploy",
            ],
        )

        assert result.exit_code == 0

        call_kwargs = mock_builder.build_skill.call_args.kwargs
        assert call_kwargs["deploy"] is False
        assert "not deployed" in result.output


class TestBuildSkillValidation:
    """Test validation and error handling."""

    def test_missing_name_parameter(self, runner, mock_builder):
        """Test error when --name is missing."""
        result = runner.invoke(
            cli,
            [
                "build-skill",
                "--description",
                "Test description",
                "--domain",
                "testing",
            ],
        )

        assert result.exit_code == 1
        assert "Error: --name is required" in result.output

    def test_missing_description_parameter(self, runner, mock_builder):
        """Test error when --description is missing."""
        result = runner.invoke(
            cli,
            [
                "build-skill",
                "--name",
                "Test Skill",
                "--domain",
                "testing",
            ],
        )

        assert result.exit_code == 1
        assert "Error: --description is required" in result.output

    def test_missing_domain_parameter(self, runner, mock_builder):
        """Test error when --domain is missing."""
        result = runner.invoke(
            cli,
            [
                "build-skill",
                "--name",
                "Test Skill",
                "--description",
                "Test description",
            ],
        )

        assert result.exit_code == 1
        assert "Error: --domain is required" in result.output

    def test_validation_errors_displayed(self, runner, mock_builder):
        """Test validation errors are displayed clearly."""
        mock_builder.build_skill.return_value = {
            "status": "error",
            "skill_path": None,
            "skill_id": "test-skill",
            "message": "Skill validation failed",
            "errors": [
                "Missing required field: name",
                "Description too short (5 chars, minimum 20)",
            ],
        }

        result = runner.invoke(
            cli,
            [
                "build-skill",
                "--name",
                "Test",
                "--description",
                "Short",
                "--domain",
                "testing",
            ],
        )

        assert result.exit_code == 1
        assert "Build failed" in result.output
        assert "Missing required field: name" in result.output
        assert "Description too short" in result.output

    def test_validation_warnings_displayed(self, runner, mock_builder):
        """Test validation warnings are shown but don't block."""
        mock_builder.build_skill.return_value = {
            "status": "success",
            "skill_path": str(
                Path.home() / ".claude" / "skills" / "test-skill" / "SKILL.md"
            ),
            "skill_id": "test-skill",
            "message": "Skill created successfully",
            "warnings": [
                "No tags specified. Tags improve discoverability.",
                "No version specified. Consider adding semantic version.",
            ],
        }

        result = runner.invoke(
            cli,
            [
                "build-skill",
                "--name",
                "Test Skill",
                "--description",
                "A test skill for validation",
                "--domain",
                "testing",
            ],
        )

        assert result.exit_code == 0
        assert "created successfully" in result.output
        assert "Warnings:" in result.output
        assert "No tags specified" in result.output
        assert "No version specified" in result.output


class TestBuildSkillInteractiveMode:
    """Test interactive mode with prompts."""

    def test_interactive_mode_basic(self, runner, mock_builder):
        """Test interactive mode with basic inputs."""
        result = runner.invoke(
            cli,
            ["build-skill", "--interactive"],
            input="Test Skill\nTest description for interactive mode\ntesting\ntest,interactive\n1\ny\n",
        )

        assert result.exit_code == 0
        assert "Skill name:" in result.output
        assert "Description:" in result.output
        assert "Domain" in result.output
        assert "Tags" in result.output
        assert "Available Templates:" in result.output

    def test_interactive_template_selection(self, runner, mock_builder):
        """Test template selection in interactive mode."""
        result = runner.invoke(
            cli,
            ["build-skill", "--interactive"],
            input="Test Skill\nTest description\ntesting\ntest\n3\ny\n",
        )

        assert result.exit_code == 0

        # Verify template selection
        call_kwargs = mock_builder.build_skill.call_args.kwargs
        # Template 3 should be "api-development"
        assert call_kwargs["template"] in [
            "base",
            "web-development",
            "api-development",
            "testing",
        ]

    def test_interactive_no_deploy(self, runner, mock_builder):
        """Test declining deployment in interactive mode."""
        result = runner.invoke(
            cli,
            ["build-skill", "--interactive"],
            input="Test Skill\nTest description\ntesting\ntest\n1\nn\n",
        )

        assert result.exit_code == 0

        call_kwargs = mock_builder.build_skill.call_args.kwargs
        assert call_kwargs["deploy"] is False


class TestBuildSkillPreviewMode:
    """Test preview mode without deployment."""

    def test_preview_shows_content(self, runner, mock_builder):
        """Test --preview flag shows content without deploying."""
        result = runner.invoke(
            cli,
            [
                "build-skill",
                "--name",
                "Test Skill",
                "--description",
                "Test description for preview",
                "--domain",
                "testing",
                "--preview",
            ],
        )

        assert result.exit_code == 0
        assert "Preview:" in result.output
        assert "name: test-skill" in result.output
        assert "Test Skill" in result.output
        assert "Preview mode: Skill not deployed" in result.output

        # Verify deployment was skipped
        call_kwargs = mock_builder.build_skill.call_args.kwargs
        assert call_kwargs["deploy"] is False

    def test_preview_truncates_long_content(self, runner, mock_builder):
        """Test preview truncates content over 50 lines."""
        # Generate long content
        long_content = "---\nname: test\n---\n\n" + "\n".join(
            [f"Line {i}" for i in range(100)]
        )
        mock_builder._generate_from_template.return_value = long_content

        result = runner.invoke(
            cli,
            [
                "build-skill",
                "--name",
                "Test Skill",
                "--description",
                "Test description",
                "--domain",
                "testing",
                "--preview",
            ],
        )

        assert result.exit_code == 0
        assert "more lines" in result.output


class TestBuildSkillTemplates:
    """Test template functionality."""

    def test_all_templates_available(self, runner, mock_builder):
        """Test all template options are valid."""
        templates = ["base", "web-development", "api-development", "testing"]

        for template in templates:
            result = runner.invoke(
                cli,
                [
                    "build-skill",
                    "--name",
                    "Test Skill",
                    "--description",
                    "Test description",
                    "--domain",
                    "testing",
                    "--template",
                    template,
                ],
            )

            assert result.exit_code == 0
            call_kwargs = mock_builder.build_skill.call_args.kwargs
            assert call_kwargs["template"] == template

    def test_invalid_template_rejected(self, runner, mock_builder):
        """Test invalid template name is rejected."""
        result = runner.invoke(
            cli,
            [
                "build-skill",
                "--name",
                "Test Skill",
                "--description",
                "Test description",
                "--domain",
                "testing",
                "--template",
                "invalid-template",
            ],
        )

        assert result.exit_code != 0
        assert "Invalid value for '--template'" in result.output


class TestBuildSkillOutput:
    """Test output formatting and messages."""

    def test_success_output_format(self, runner, mock_builder):
        """Test success message includes all required information."""
        result = runner.invoke(
            cli,
            [
                "build-skill",
                "--name",
                "Test Skill",
                "--description",
                "Test description",
                "--domain",
                "testing",
            ],
        )

        assert result.exit_code == 0
        assert "Building Progressive Skill" in result.output
        assert "Building skill..." in result.output
        assert "created successfully" in result.output
        assert "Deployment Path:" in result.output
        assert "Next Steps:" in result.output
        assert "Review the skill file" in result.output
        assert "Restart Claude Code" in result.output

    def test_error_output_format(self, runner, mock_builder):
        """Test error messages are clear and actionable."""
        mock_builder.build_skill.return_value = {
            "status": "error",
            "skill_path": None,
            "skill_id": "test-skill",
            "message": "Template not found: custom-template",
        }

        result = runner.invoke(
            cli,
            [
                "build-skill",
                "--name",
                "Test Skill",
                "--description",
                "Test description",
                "--domain",
                "testing",
            ],
        )

        assert result.exit_code == 1
        assert "✗" in result.output
        assert "Build failed" in result.output


class TestBuildSkillEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_tags_string(self, runner, mock_builder):
        """Test empty tags string is handled correctly."""
        result = runner.invoke(
            cli,
            [
                "build-skill",
                "--name",
                "Test Skill",
                "--description",
                "Test description",
                "--domain",
                "testing",
                "--tags",
                "",
            ],
        )

        assert result.exit_code == 0

        call_kwargs = mock_builder.build_skill.call_args.kwargs
        assert call_kwargs["tags"] == []

    def test_keyboard_interrupt_handling(self, runner, mock_builder):
        """Test graceful handling of keyboard interrupt."""
        mock_builder.build_skill.side_effect = KeyboardInterrupt()

        result = runner.invoke(
            cli,
            [
                "build-skill",
                "--name",
                "Test Skill",
                "--description",
                "Test description",
                "--domain",
                "testing",
            ],
        )

        assert result.exit_code == 1
        assert "cancelled by user" in result.output

    def test_exception_handling(self, runner, mock_builder):
        """Test graceful handling of unexpected exceptions."""
        mock_builder.build_skill.side_effect = RuntimeError("Unexpected error")

        result = runner.invoke(
            cli,
            [
                "build-skill",
                "--name",
                "Test Skill",
                "--description",
                "Test description",
                "--domain",
                "testing",
            ],
        )

        assert result.exit_code == 1
        assert "Build failed" in result.output
        assert "Unexpected error" in result.output

    def test_whitespace_in_tags(self, runner, mock_builder):
        """Test tags with extra whitespace are trimmed."""
        result = runner.invoke(
            cli,
            [
                "build-skill",
                "--name",
                "Test Skill",
                "--description",
                "Test description",
                "--domain",
                "testing",
                "--tags",
                " tag1 , tag2 , tag3 ",
            ],
        )

        assert result.exit_code == 0

        call_kwargs = mock_builder.build_skill.call_args.kwargs
        assert call_kwargs["tags"] == ["tag1", "tag2", "tag3"]


class TestBuildSkillIntegration:
    """Integration tests with actual SkillBuilder service."""

    def test_real_builder_base_template(self, runner, tmp_path):
        """Test with real SkillBuilder using base template."""
        # Use actual SkillBuilder but deploy to temp directory
        with patch("mcp_skills.services.skill_builder.Path.home") as mock_home:
            mock_home.return_value = tmp_path

            result = runner.invoke(
                cli,
                [
                    "build-skill",
                    "--name",
                    "Integration Test Skill",
                    "--description",
                    "A comprehensive test skill for integration testing purposes",
                    "--domain",
                    "testing",
                    "--tags",
                    "integration,test,automation",
                ],
            )

            assert result.exit_code == 0

            # Verify file was created
            skill_path = (
                tmp_path / ".claude" / "skills" / "integration-test-skill" / "SKILL.md"
            )
            assert skill_path.exists()

            # Verify content
            content = skill_path.read_text()
            assert "name: integration-test-skill" in content
            assert "Integration Test Skill" in content
            assert "integration" in content

    def test_real_builder_validation_failure(self, runner):
        """Test real validation errors from SkillBuilder."""
        result = runner.invoke(
            cli,
            [
                "build-skill",
                "--name",
                "Bad Skill",
                "--description",
                "Too short",  # Less than 20 chars
                "--domain",
                "testing",
            ],
        )

        # Should fail validation
        assert result.exit_code == 1
        assert "validation failed" in result.output.lower()
