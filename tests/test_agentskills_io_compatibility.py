"""Tests for agentskills.io specification compatibility.

Tests cover:
- Parsing agentskills.io format skills
- Backward compatibility with mcp-skillset native format
- Metadata normalization (nested vs flat)
- Spec validation warnings (name format, length limits)
- Mixed format support
"""

from pathlib import Path

import pytest

from mcp_skills.models.skill import Skill
from mcp_skills.services.validators import SkillValidator


@pytest.fixture
def validator() -> SkillValidator:
    """Create SkillValidator instance."""
    return SkillValidator()


@pytest.fixture
def temp_skill_dir(tmp_path: Path) -> Path:
    """Create temporary directory for skill files."""
    skill_dir = tmp_path / "skills"
    skill_dir.mkdir()
    return skill_dir


class TestAgentSkillsIOFormatParsing:
    """Test parsing of agentskills.io format skills."""

    def test_parse_agentskills_io_format_with_nested_metadata(
        self, validator: SkillValidator, temp_skill_dir: Path
    ) -> None:
        """Test parsing agentskills.io format with nested metadata object."""
        skill_file = temp_skill_dir / "test-skill.md"
        skill_file.write_text(
            """---
name: test-skill
description: Test skill for agentskills.io spec compliance
license: MIT
compatibility: Requires Python 3.8+
metadata:
  version: "1.0.0"
  author: Test Author
  tags: [python, testing]
allowed-tools: Bash(git:*) Read Write
---

# Test Skill

This is a test skill following agentskills.io specification.

## Examples

Example 1 content

```python
def test():
    pass
```
""",
            encoding="utf-8",
        )

        # Parse frontmatter
        frontmatter = validator.parse_frontmatter(skill_file)
        assert frontmatter is not None

        # Normalize to flat structure
        normalized = validator.normalize_frontmatter(frontmatter)

        # Verify required fields
        assert normalized["name"] == "test-skill"
        assert "agentskills.io spec" in normalized["description"]

        # Verify nested metadata was flattened
        assert normalized["version"] == "1.0.0"
        assert normalized["author"] == "Test Author"
        assert normalized["tags"] == ["python", "testing"]

        # Verify agentskills.io spec fields
        assert normalized["license"] == "MIT"
        assert "Python 3.8+" in normalized["compatibility"]
        assert "Bash(git:*)" in normalized["allowed-tools"]

    def test_parse_mcp_skillset_native_format(
        self, validator: SkillValidator, temp_skill_dir: Path
    ) -> None:
        """Test parsing mcp-skillset native format (flat structure)."""
        skill_file = temp_skill_dir / "test-skill.md"
        skill_file.write_text(
            """---
name: test-skill
description: Test skill in native mcp-skillset format
category: testing
tags: [python, pytest, tdd]
dependencies: []
version: "1.0.0"
author: Test Author
---

# Test Skill

This is a test skill in native format.

## Examples

Example content
""",
            encoding="utf-8",
        )

        frontmatter = validator.parse_frontmatter(skill_file)
        assert frontmatter is not None

        # Normalize (should not change native format)
        normalized = validator.normalize_frontmatter(frontmatter)

        # Verify all fields preserved
        assert normalized["name"] == "test-skill"
        assert normalized["category"] == "testing"
        assert normalized["tags"] == ["python", "pytest", "tdd"]
        assert normalized["version"] == "1.0.0"
        assert normalized["author"] == "Test Author"

    def test_parse_mixed_format(
        self, validator: SkillValidator, temp_skill_dir: Path
    ) -> None:
        """Test parsing skill with both flat and nested metadata."""
        skill_file = temp_skill_dir / "test-skill.md"
        skill_file.write_text(
            """---
name: test-skill
description: Test skill with mixed format
category: testing
license: MIT
metadata:
  version: "2.0.0"
  extra_field: "extra value"
---

# Test Skill

Mixed format skill.
""",
            encoding="utf-8",
        )

        frontmatter = validator.parse_frontmatter(skill_file)
        assert frontmatter is not None

        normalized = validator.normalize_frontmatter(frontmatter)

        # Top-level fields preserved
        assert normalized["category"] == "testing"
        assert normalized["license"] == "MIT"

        # Nested metadata flattened
        assert normalized["version"] == "2.0.0"
        assert normalized["extra_field"] == "extra value"

        # metadata object removed after flattening
        assert "metadata" not in normalized


class TestMetadataNormalization:
    """Test metadata normalization logic."""

    def test_normalize_flat_structure_no_changes(
        self, validator: SkillValidator
    ) -> None:
        """Test that flat structure is not modified."""
        frontmatter = {
            "name": "test-skill",
            "description": "Test description",
            "version": "1.0.0",
            "tags": ["test"],
        }

        normalized = validator.normalize_frontmatter(frontmatter)

        assert normalized == frontmatter

    def test_normalize_nested_metadata_flattened(
        self, validator: SkillValidator
    ) -> None:
        """Test that nested metadata is flattened to top level."""
        frontmatter = {
            "name": "test-skill",
            "description": "Test description",
            "metadata": {"version": "1.0.0", "author": "Test Author", "tags": ["test"]},
        }

        normalized = validator.normalize_frontmatter(frontmatter)

        # Nested fields moved to top level
        assert normalized["version"] == "1.0.0"
        assert normalized["author"] == "Test Author"
        assert normalized["tags"] == ["test"]

        # metadata object removed
        assert "metadata" not in normalized

    def test_normalize_preserves_top_level_over_nested(
        self, validator: SkillValidator
    ) -> None:
        """Test that top-level fields take precedence over nested."""
        frontmatter = {
            "name": "test-skill",
            "description": "Test description",
            "version": "2.0.0",  # Top-level
            "metadata": {
                "version": "1.0.0",  # Nested (should be ignored)
                "author": "Test Author",
            },
        }

        normalized = validator.normalize_frontmatter(frontmatter)

        # Top-level version preserved
        assert normalized["version"] == "2.0.0"
        # Nested author added
        assert normalized["author"] == "Test Author"

    def test_normalize_string_to_list_conversion(
        self, validator: SkillValidator
    ) -> None:
        """Test that string tags/dependencies are converted to lists."""
        frontmatter = {
            "name": "test-skill",
            "description": "Test description",
            "tags": "single-tag",
            "dependencies": "single-dep",
        }

        normalized = validator.normalize_frontmatter(frontmatter)

        assert normalized["tags"] == ["single-tag"]
        assert normalized["dependencies"] == ["single-dep"]


class TestAgentSkillsIOValidation:
    """Test agentskills.io spec validation warnings."""

    def test_validate_name_format_warning(self, validator: SkillValidator) -> None:
        """Test warning for non-compliant name format."""
        skill = Skill(
            id="test/skill",
            name="Test Skill With Spaces",  # Non-compliant
            description="Valid description here",
            instructions="Long enough instructions " * 10,
            category="testing",
            tags=["test"],
            dependencies=[],
            examples=[],
            file_path=Path("/tmp/test.md"),
            repo_id="test",
        )

        result = validator.validate_skill(skill)

        # Should have warning about name format
        assert any(
            "agentskills.io spec format" in warning.lower()
            for warning in result["warnings"]
        )

    def test_validate_compliant_name_no_warning(
        self, validator: SkillValidator
    ) -> None:
        """Test that compliant name format produces no warning."""
        skill = Skill(
            id="test/skill",
            name="test-skill-with-hyphens",  # Compliant
            description="Valid description here",
            instructions="Long enough instructions " * 10,
            category="testing",
            tags=["test"],
            dependencies=[],
            examples=[],
            file_path=Path("/tmp/test.md"),
            repo_id="test",
        )

        result = validator.validate_skill(skill)

        # Should NOT have warning about name format
        assert not any(
            "agentskills.io spec format" in warning.lower()
            for warning in result["warnings"]
        )

    def test_validate_name_length_warning(self, validator: SkillValidator) -> None:
        """Test warning for name exceeding 64 chars."""
        long_name = "a" * 65  # Exceeds 64 char limit
        skill = Skill(
            id="test/skill",
            name=long_name,
            description="Valid description here",
            instructions="Long enough instructions " * 10,
            category="testing",
            tags=["test"],
            dependencies=[],
            examples=[],
            file_path=Path("/tmp/test.md"),
            repo_id="test",
        )

        result = validator.validate_skill(skill)

        # Should have warning about name length
        assert any("Name too long" in warning for warning in result["warnings"])

    def test_validate_description_length_warning(
        self, validator: SkillValidator
    ) -> None:
        """Test warning for description exceeding 1024 chars."""
        long_description = "a" * 1025  # Exceeds 1024 char limit
        skill = Skill(
            id="test/skill",
            name="test-skill",
            description=long_description,
            instructions="Long enough instructions " * 10,
            category="testing",
            tags=["test"],
            dependencies=[],
            examples=[],
            file_path=Path("/tmp/test.md"),
            repo_id="test",
        )

        result = validator.validate_skill(skill)

        # Should have warning about description length
        assert any("Description too long" in warning for warning in result["warnings"])

    def test_validate_compatibility_length_warning(
        self, validator: SkillValidator
    ) -> None:
        """Test warning for compatibility exceeding 500 chars."""
        long_compatibility = "a" * 501  # Exceeds 500 char limit
        skill = Skill(
            id="test/skill",
            name="test-skill",
            description="Valid description here",
            instructions="Long enough instructions " * 10,
            category="testing",
            tags=["test"],
            dependencies=[],
            examples=[],
            file_path=Path("/tmp/test.md"),
            repo_id="test",
            compatibility=long_compatibility,
        )

        result = validator.validate_skill(skill)

        # Should have warning about compatibility length
        assert any(
            "Compatibility field too long" in warning for warning in result["warnings"]
        )


class TestBackwardCompatibility:
    """Test backward compatibility with existing skills."""

    def test_existing_skills_still_parse(
        self, validator: SkillValidator, temp_skill_dir: Path
    ) -> None:
        """Test that existing mcp-skillset skills still parse correctly."""
        skill_file = temp_skill_dir / "existing-skill.md"
        skill_file.write_text(
            """---
name: existing-skill
description: Existing skill that should continue to work
category: testing
tags: [python, testing]
dependencies: []
version: 1.0.0
author: Original Author
---

# Existing Skill

This skill should continue to work after agentskills.io support is added.

## Examples

```python
def example():
    pass
```
""",
            encoding="utf-8",
        )

        frontmatter = validator.parse_frontmatter(skill_file)
        assert frontmatter is not None

        normalized = validator.normalize_frontmatter(frontmatter)

        # All existing fields preserved
        assert normalized["name"] == "existing-skill"
        assert normalized["category"] == "testing"
        assert normalized["tags"] == ["python", "testing"]
        assert normalized["dependencies"] == []
        assert normalized["version"] == "1.0.0"
        assert normalized["author"] == "Original Author"

    def test_optional_agentskills_io_fields_preserved(
        self, validator: SkillValidator
    ) -> None:
        """Test that optional agentskills.io fields are preserved when present."""
        frontmatter = {
            "name": "test-skill",
            "description": "Test description",
            "license": "MIT",
            "compatibility": "Requires Python 3.8+",
            "allowed-tools": "Bash Read Write",
        }

        normalized = validator.normalize_frontmatter(frontmatter)

        # agentskills.io fields preserved
        assert normalized["license"] == "MIT"
        assert normalized["compatibility"] == "Requires Python 3.8+"
        assert normalized["allowed-tools"] == "Bash Read Write"
