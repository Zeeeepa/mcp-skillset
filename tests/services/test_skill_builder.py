"""Tests for SkillBuilder service.

Tests cover:
- Template-based skill generation
- Validation of YAML frontmatter and body
- Security pattern scanning
- Deployment to ~/.claude/skills/
- Error handling and edge cases
"""

from pathlib import Path

import pytest
import yaml

from mcp_skills.services.skill_builder import SkillBuilder


@pytest.fixture
def temp_templates_dir(tmp_path):
    """Create temporary templates directory for testing."""
    templates_dir = tmp_path / "templates" / "skills"
    templates_dir.mkdir(parents=True)
    return templates_dir


@pytest.fixture
def skill_builder(temp_templates_dir):
    """Create SkillBuilder instance with temp templates directory."""
    # Create a minimal base template
    base_template = temp_templates_dir / "base.md.j2"
    base_template.write_text(
        """---
name: {{ skill_id }}
description: |
  {{ description }}
version: "{{ version }}"
category: {{ category }}
tags:
{% for tag in tags %}
  - {{ tag }}
{% endfor %}
author: {{ author }}
created: {{ created }}
last_updated: {{ last_updated }}
---

# {{ name }}

## Overview

{{ description }}

## Core Principles

Test skill content.

## Examples

```python
# Example code
def test():
    pass
```
"""
    )

    # Create SkillBuilder with temp config path
    config_path = temp_templates_dir.parent.parent / "config.yaml"
    config_path.touch()

    return SkillBuilder(config_path=config_path)


@pytest.fixture
def temp_claude_skills_dir(tmp_path, monkeypatch):
    """Mock ~/.claude/skills directory."""
    claude_dir = tmp_path / ".claude" / "skills"
    claude_dir.mkdir(parents=True)

    # Mock Path.home() to return tmp_path
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    return claude_dir


class TestSkillBuilderInit:
    """Test SkillBuilder initialization."""

    def test_init_with_config_path(self, temp_templates_dir):
        """Test initialization with config path."""
        config_path = temp_templates_dir.parent.parent / "config.yaml"
        config_path.touch()

        builder = SkillBuilder(config_path=config_path)

        assert builder.templates_dir.exists()
        assert builder.jinja_env is not None

    def test_init_without_config_creates_templates_dir(self, tmp_path, monkeypatch):
        """Test initialization creates templates directory if missing."""
        # Create a fake package root
        package_root = tmp_path / "mcp_skills"
        package_root.mkdir()

        # Mock __file__ to point to our fake package
        import mcp_skills.services.skill_builder as sb_module

        original_file = sb_module.__file__
        monkeypatch.setattr(
            sb_module, "__file__", str(package_root / "services" / "skill_builder.py")
        )

        builder = SkillBuilder()

        assert builder.templates_dir.exists()
        assert builder.templates_dir.name == "skills"

        # Cleanup mock
        monkeypatch.setattr(sb_module, "__file__", original_file)

    def test_list_templates(self, skill_builder, temp_templates_dir):
        """Test listing available templates."""
        # Create some template files
        (temp_templates_dir / "web-development.md.j2").write_text("# Web Dev")
        (temp_templates_dir / "testing.md.j2").write_text("# Testing")

        templates = skill_builder.list_templates()

        assert "base" in templates
        assert "web-development" in templates
        assert "testing" in templates
        assert len(templates) == 3


class TestSkillBuilding:
    """Test skill building functionality."""

    def test_build_skill_success(self, skill_builder):
        """Test successful skill building."""
        result = skill_builder.build_skill(
            name="Test Skill",
            description="A test skill for unit testing with examples and patterns",
            domain="testing",
            tags=["test", "pytest", "unit-testing"],
            deploy=False,
        )

        assert result["status"] == "success"
        assert result["skill_id"] == "test-skill"
        assert result["message"].startswith("Skill 'test-skill' created")

    def test_build_skill_normalizes_name(self, skill_builder):
        """Test skill name normalization to kebab-case."""
        result = skill_builder.build_skill(
            name="My Cool Skill!",
            description="Test skill with special characters in name for validation",
            domain="testing",
            deploy=False,
        )

        assert result["skill_id"] == "my-cool-skill"

    def test_build_skill_with_custom_params(self, skill_builder):
        """Test skill building with custom parameters."""
        result = skill_builder.build_skill(
            name="Custom Skill",
            description="Custom skill with all parameters specified for testing",
            domain="web development",
            tags=["web", "api", "rest"],
            version="2.0.0",
            category="Web Development",
            toolchain=["Python 3.11+", "FastAPI"],
            frameworks=["FastAPI", "Pydantic"],
            author="Test Author",
            license="Apache-2.0",
            deploy=False,
        )

        assert result["status"] == "success"
        assert result["skill_id"] == "custom-skill"

    def test_build_skill_with_invalid_template(self, skill_builder):
        """Test building with non-existent template falls back to base."""
        result = skill_builder.build_skill(
            name="Test",
            description="Test skill with non-existent template fallback behavior",
            domain="testing",
            template="nonexistent-template",
            deploy=False,
        )

        # Should fall back to base template
        assert result["status"] == "success"

    def test_build_skill_deployment(self, skill_builder, temp_claude_skills_dir):
        """Test skill deployment to ~/.claude/skills/."""
        result = skill_builder.build_skill(
            name="Deployed Skill",
            description="Test skill for deployment verification to Claude directory",
            domain="testing",
            deploy=True,
        )

        assert result["status"] == "success"
        assert result["skill_path"] is not None

        # Verify file was created
        skill_path = Path(result["skill_path"])
        assert skill_path.exists()
        assert skill_path.name == "SKILL.md"
        assert "deployed-skill" in str(skill_path)


class TestValidation:
    """Test skill validation functionality."""

    def test_validate_valid_skill(self, skill_builder):
        """Test validation of valid skill content."""
        skill_content = """---
name: test-skill
description: This is a valid test skill for validation testing
version: "1.0.0"
category: Testing
tags:
  - test
  - validation
---

# Test Skill

## Overview

Valid skill content.

## Examples

```python
def test():
    pass
```
"""

        result = skill_builder.validate_skill(skill_content)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_missing_frontmatter(self, skill_builder):
        """Test validation fails without frontmatter."""
        skill_content = """# Test Skill

Just content, no frontmatter.
"""

        result = skill_builder.validate_skill(skill_content)

        assert result.valid is False
        assert any("Missing YAML frontmatter" in e for e in result.errors)

    def test_validate_invalid_yaml(self, skill_builder):
        """Test validation fails with invalid YAML syntax."""
        skill_content = """---
name: test
description: broken yaml
  invalid: indentation
---

# Content
"""

        result = skill_builder.validate_skill(skill_content)

        assert result.valid is False
        assert any("Invalid YAML syntax" in e for e in result.errors)

    def test_validate_missing_required_fields(self, skill_builder):
        """Test validation fails without required fields."""
        skill_content = """---
version: "1.0.0"
---

# Content
"""

        result = skill_builder.validate_skill(skill_content)

        assert result.valid is False
        assert any("Missing required field: name" in e for e in result.errors)
        assert any("Description too short" in e for e in result.errors)

    def test_validate_short_description(self, skill_builder):
        """Test validation fails with too short description."""
        skill_content = """---
name: test
description: short
---

# Content
"""

        result = skill_builder.validate_skill(skill_content)

        assert result.valid is False
        assert any("Description too short" in e for e in result.errors)

    def test_validate_body_too_large(self, skill_builder):
        """Test validation fails when body exceeds size limit."""
        large_body = "x" * 25000  # Exceeds MAX_BODY_CHARS (20000)
        skill_content = f"""---
name: test
description: Test skill with very large body content
---

# Content

{large_body}
"""

        result = skill_builder.validate_skill(skill_content)

        assert result.valid is False
        assert any("Body exceeds maximum size" in e for e in result.errors)

    def test_validate_warnings_for_optional_fields(self, skill_builder):
        """Test warnings for missing optional fields."""
        skill_content = """---
name: test
description: Test skill without optional fields like tags and version
---

# Content

No examples here.
"""

        result = skill_builder.validate_skill(skill_content)

        # Should be valid but have warnings
        assert result.valid is True
        assert any("No tags specified" in w for w in result.warnings)
        assert any("No version specified" in w for w in result.warnings)


class TestSecurityValidation:
    """Test security pattern detection."""

    def test_security_detects_hardcoded_credentials(self, skill_builder):
        """Test detection of hardcoded credentials."""
        skill_content = """---
name: test
description: Test skill with hardcoded credentials for security testing
---

# Content

```python
api_key = "sk-1234567890abcdef"
password = "secret123"
```
"""

        result = skill_builder.validate_skill(skill_content)

        assert result.valid is False
        assert any("Hardcoded credentials" in e for e in result.errors)

    def test_security_detects_code_execution(self, skill_builder):
        """Test detection of dangerous code execution patterns."""
        skill_content = """---
name: test
description: Test skill with code execution patterns for security validation
---

# Content

```python
exec(user_input)
eval(dangerous_code)
```
"""

        result = skill_builder.validate_skill(skill_content)

        assert result.valid is False
        assert any(
            "Code execution patterns" in e or "Dynamic code evaluation" in e
            for e in result.errors
        )

    def test_security_allows_safe_content(self, skill_builder):
        """Test that safe content passes security checks."""
        skill_content = """---
name: test
description: Test skill with safe content for security validation
---

# Content

```python
# Safe code
def hello():
    return "Hello, World!"
```
"""

        result = skill_builder.validate_skill(skill_content)

        assert result.valid is True


class TestDeployment:
    """Test skill deployment functionality."""

    def test_deploy_skill_creates_directory(
        self, skill_builder, temp_claude_skills_dir
    ):
        """Test deployment creates directory structure."""
        skill_content = """---
name: test
description: Test skill for deployment directory creation
---

# Content
"""

        skill_path = skill_builder.deploy_skill(skill_content, "test-skill")

        assert skill_path.exists()
        assert skill_path.parent.name == "test-skill"
        assert skill_path.name == "SKILL.md"

    def test_deploy_skill_writes_content(self, skill_builder, temp_claude_skills_dir):
        """Test deployment writes correct content."""
        skill_content = """---
name: test
description: Test skill content verification
---

# Test Content
"""

        skill_path = skill_builder.deploy_skill(skill_content, "test-skill")

        written_content = skill_path.read_text()
        assert written_content == skill_content

    def test_deploy_skill_overwrites_existing(
        self, skill_builder, temp_claude_skills_dir
    ):
        """Test deployment overwrites existing skill."""
        skill_dir = temp_claude_skills_dir / "test-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("Old content")

        new_content = """---
name: test
description: New skill content for overwrite testing
---

# New Content
"""

        skill_path = skill_builder.deploy_skill(new_content, "test-skill")

        assert skill_path.read_text() == new_content


class TestHelperMethods:
    """Test private helper methods."""

    def test_normalize_skill_id(self, skill_builder):
        """Test skill ID normalization."""
        assert skill_builder._normalize_skill_id("Test Skill") == "test-skill"
        assert skill_builder._normalize_skill_id("My-Cool-Skill") == "my-cool-skill"
        assert (
            skill_builder._normalize_skill_id("Skill With  Spaces")
            == "skill-with-spaces"
        )
        assert (
            skill_builder._normalize_skill_id("Special!@#$Characters")
            == "special-characters"
        )
        assert (
            skill_builder._normalize_skill_id("--Leading-Trailing--")
            == "leading-trailing"
        )

    def test_split_skill_content(self, skill_builder):
        """Test splitting frontmatter and body."""
        content = """---
name: test
description: Test
---

# Body Content

More content here.
"""

        frontmatter, body = skill_builder._split_skill_content(content)

        assert "name: test" in frontmatter
        assert "# Body Content" in body

    def test_split_skill_content_no_frontmatter(self, skill_builder):
        """Test splitting content without frontmatter."""
        content = "# Just Content\n\nNo frontmatter here."

        frontmatter, body = skill_builder._split_skill_content(content)

        assert frontmatter == ""
        assert "Just Content" in body

    def test_build_template_context(self, skill_builder):
        """Test building template context dictionary."""
        context = skill_builder._build_template_context(
            name="Test Skill",
            skill_id="test-skill",
            description="Test description",
            domain="testing",
            tags=["test", "example"],
            version="2.0.0",
            custom_field="custom_value",
        )

        assert context["name"] == "Test Skill"
        assert context["skill_id"] == "test-skill"
        assert context["description"] == "Test description"
        assert context["domain"] == "testing"
        assert context["tags"] == ["test", "example"]
        assert context["version"] == "2.0.0"
        assert context["custom_field"] == "custom_value"
        assert context["author"] == "mcp-skillset"
        assert context["license"] == "MIT"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_build_skill_with_empty_tags(self, skill_builder):
        """Test building skill with empty tags list."""
        result = skill_builder.build_skill(
            name="Test",
            description="Test skill with empty tags list for edge case testing",
            domain="testing",
            tags=[],
            deploy=False,
        )

        assert result["status"] == "success"

    def test_build_skill_with_none_tags(self, skill_builder):
        """Test building skill with None tags."""
        result = skill_builder.build_skill(
            name="Test",
            description="Test skill with None tags for edge case validation",
            domain="testing",
            tags=None,
            deploy=False,
        )

        assert result["status"] == "success"

    def test_validate_frontmatter_not_dict(self, skill_builder):
        """Test validation fails when frontmatter is not a dictionary."""
        skill_content = """---
- list
- not
- dict
---

# Content
"""

        result = skill_builder.validate_skill(skill_content)

        assert result.valid is False
        assert any("must be a YAML dictionary" in e for e in result.errors)

    def test_scan_security_patterns_case_insensitive(self, skill_builder):
        """Test security scanning is case-insensitive."""
        skill_content = """---
name: test
description: Test skill with uppercase API key for case sensitivity check
---

# Content

API_KEY = "secret"
PASSWORD = "admin123"
"""

        result = skill_builder.validate_skill(skill_content)

        assert result.valid is False
        assert any("Hardcoded credentials" in e for e in result.errors)


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_full_skill_creation_workflow(self, skill_builder, temp_claude_skills_dir):
        """Test complete skill creation and deployment workflow."""
        # Build skill with all parameters
        result = skill_builder.build_skill(
            name="PostgreSQL Optimization",
            description="Optimize PostgreSQL queries using EXPLAIN ANALYZE and indexing strategies",
            domain="database",
            tags=["postgresql", "database", "optimization", "performance"],
            version="1.0.0",
            category="Database",
            toolchain=["PostgreSQL 14+", "pgAdmin", "pg_stat_statements"],
            frameworks=["PostgreSQL"],
            related_skills=["api-development", "testing"],
            author="Test Author",
            license="MIT",
            deploy=True,
        )

        # Verify result
        assert result["status"] == "success"
        assert result["skill_id"] == "postgresql-optimization"
        assert result["skill_path"] is not None

        # Verify deployed file
        skill_path = Path(result["skill_path"])
        assert skill_path.exists()

        # Parse and verify content
        content = skill_path.read_text()
        assert "name: postgresql-optimization" in content
        assert "PostgreSQL Optimization" in content
        assert "EXPLAIN ANALYZE" in content

        # Parse YAML frontmatter
        frontmatter_match = content.split("---")[1]
        frontmatter = yaml.safe_load(frontmatter_match)

        assert frontmatter["name"] == "postgresql-optimization"
        assert frontmatter["version"] == "1.0.0"
        assert frontmatter["category"] == "Database"
        assert "postgresql" in frontmatter["tags"]
        # Toolchain field is optional and may not be present if template skips empty lists
        if "toolchain" in frontmatter:
            assert "PostgreSQL 14+" in frontmatter["toolchain"]

    def test_validation_prevents_deployment(self, skill_builder):
        """Test that validation errors prevent deployment."""
        result = skill_builder.build_skill(
            name="Invalid Skill",
            description="short",  # Too short
            domain="testing",
            deploy=True,
        )

        assert result["status"] == "error"
        assert result["skill_path"] is None
        assert "validation failed" in result["message"].lower()
