# agentskills.io Specification Compatibility Analysis

**Research Date:** 2026-01-17
**Project:** mcp-skillset
**Purpose:** Determine compatibility level between mcp-skillset's SKILL.md format and agentskills.io specification

---

## Executive Summary

**Compatibility Level: PARTIAL** ✓

mcp-skillset uses SKILL.md files with YAML frontmatter and markdown body, which aligns with the core agentskills.io specification. However, there are differences in required fields, field naming conventions, and optional features that prevent full compliance.

**Key Findings:**
- ✅ Uses YAML frontmatter with `---` delimiters (matches spec)
- ✅ Uses markdown body for instructions (matches spec)
- ✅ Supports progressive disclosure architecture (matches spec)
- ⚠️ Different required field names (`name` vs spec's lowercase-hyphen naming)
- ⚠️ Additional fields not in spec (`category`, `tags`, `dependencies`)
- ⚠️ No explicit support for spec's `license`, `compatibility`, `allowed-tools` fields
- ⚠️ No support for optional `scripts/`, `references/`, `assets/` directories

---

## Current mcp-skillset Format

### 1. File Structure

**Location:** `.claude/skills/{skill-name}/SKILL.md`

**Format:**
```markdown
---
name: skill-name
description: Brief description
category: testing
tags: [python, pytest, tdd]
dependencies: []
version: 1.0.0
author: mcp-skillset
---

# Skill Title

## Summary
Brief summary section...

## Instructions
Detailed markdown instructions...
```

### 2. Required Fields (Validated by Pydantic)

Based on `src/mcp_skills/models/skill.py` and `src/mcp_skills/services/validators/skill_validator.py`:

**CRITICAL (errors if missing):**
- `name` (string, min_length=1)
- `description` (string, min_length=10)
- `instructions` (markdown body, min_length=50)

**OPTIONAL:**
- `category` (string, validated against predefined list)
- `tags` (list[str], default=[])
- `dependencies` (list[str], default=[])
- `version` (string | None)
- `author` (string | None)

### 3. Parsing Logic

**File:** `src/mcp_skills/services/validators/skill_validator.py`

```python
def split_frontmatter(self, content: str) -> tuple[str, str]:
    """Split SKILL.md content into frontmatter and instructions."""
    frontmatter_pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(frontmatter_pattern, content, re.DOTALL)

    if match:
        return match.group(1), match.group(2)  # (yaml, markdown)
```

**YAML parsing:** Uses `yaml.safe_load()` for frontmatter

**Validation:** Pydantic models enforce schema at parse time

### 4. Example Skills Analyzed

**Sample 1:** `.claude/skills/universal-testing-test-driven-development/SKILL.md`
```yaml
---
name: test-driven-development
description: Comprehensive TDD patterns and practices...
updated_at: 2025-10-30T17:00:00Z
tags: [testing, tdd, best-practices, quality-assurance]
---
```

**Sample 2:** `docs/skill-templates/fastapi-web-development/SKILL.md`
```yaml
---
name: FastAPI Modern Web Development
skill_id: fastapi-web-development
version: 1.0.0
description: Production-grade FastAPI development...
category: Python Web Development
tags: [fastapi, python, async, pydantic]
author: mcp-skillset
license: MIT
created: 2025-11-25
last_updated: 2025-11-25
toolchain: [Python 3.11+, FastAPI 0.100+]
frameworks: [FastAPI, Pydantic]
related_skills: [test-driven-development, systematic-debugging]
---
```

**Sample 3:** `.claude/skills/toolchains-python-validation-pydantic/SKILL.md`
```yaml
---
name: pydantic
description: Python data validation using type hints...
progressive_disclosure:
  entry_point: [summary, when_to_use, quick_start]
  full_content: all
token_estimates:
  entry_point: 70
  full: 5500
---
```

**Observations:**
- Inconsistent field usage across skills (some use `skill_id`, others don't)
- Some skills include `progressive_disclosure` metadata (aligns with agentskills.io philosophy)
- Additional fields like `toolchain`, `frameworks`, `related_skills` (not in spec)
- Token estimates included in some skills (good progressive disclosure practice)

---

## agentskills.io Specification

### 1. Required Fields

**Source:** https://agentskills.io

```yaml
---
name: skill-name  # Max 64 chars, lowercase-hyphen format
description: Brief description  # Max 1024 chars
---
```

**Naming Convention:**
- `name` must be lowercase with hyphens (e.g., `test-driven-development`)
- Max 64 characters
- Used as unique identifier

**Description Constraint:**
- Max 1024 characters
- Brief summary of skill purpose

### 2. Optional Fields

```yaml
---
name: skill-name
description: Brief description
license: MIT  # SPDX identifier
compatibility: [claude-3.5, gpt-4]  # Compatible models
metadata:
  author: Author Name
  version: 1.0.0
  tags: [python, testing]
allowed-tools: [bash, python, file-operations]  # Restricted tool access
---
```

### 3. Progressive Disclosure Architecture

**Metadata Section (~100 tokens):**
- YAML frontmatter with essential fields
- Minimal context for skill discovery

**Activation Section (<5000 tokens):**
- Markdown body with full instructions
- Loaded when skill is invoked

**Optional Directories:**
- `scripts/` - Executable scripts for skill automation
- `references/` - Additional documentation and examples
- `assets/` - Images, diagrams, supporting files

### 4. Philosophy

- **Minimal footprint:** ~100 tokens in metadata, <5k tokens when activated
- **Progressive disclosure:** Load only what's needed
- **Tool restriction:** `allowed-tools` limits AI agent tool access for security
- **Model compatibility:** Declare which AI models skill supports

---

## Compatibility Analysis

### Field-by-Field Comparison

| Field | mcp-skillset | agentskills.io | Status |
|-------|--------------|----------------|--------|
| `name` | ✅ Required (string) | ✅ Required (lowercase-hyphen, max 64 chars) | ⚠️ No format validation |
| `description` | ✅ Required (min 10 chars) | ✅ Required (max 1024 chars) | ⚠️ No max length check |
| `license` | ❌ Not supported | ✅ Optional (SPDX) | ❌ Missing |
| `compatibility` | ❌ Not supported | ✅ Optional (model list) | ❌ Missing |
| `allowed-tools` | ❌ Not supported | ✅ Optional (tool restrictions) | ❌ Missing |
| `metadata` | ❌ Not supported | ✅ Optional (nested object) | ⚠️ Flat structure instead |
| `category` | ✅ Optional (validated list) | ❌ Not in spec | ➕ Extra field |
| `tags` | ✅ Optional (list[str]) | ✅ In metadata | ⚠️ Top-level vs nested |
| `dependencies` | ✅ Optional (list[str]) | ❌ Not in spec | ➕ Extra field |
| `version` | ✅ Optional (string) | ✅ In metadata | ⚠️ Top-level vs nested |
| `author` | ✅ Optional (string) | ✅ In metadata | ⚠️ Top-level vs nested |

### Architecture Comparison

| Feature | mcp-skillset | agentskills.io | Status |
|---------|--------------|----------------|--------|
| YAML frontmatter | ✅ Uses `---` delimiters | ✅ Uses `---` delimiters | ✅ Compatible |
| Markdown body | ✅ Full instructions | ✅ Full instructions | ✅ Compatible |
| Progressive disclosure | ⚠️ Some skills implement | ✅ Core philosophy | ⚠️ Partial |
| Token limits | ⚠️ No enforcement | ✅ ~100 metadata, <5k body | ⚠️ Not enforced |
| Optional directories | ❌ Not supported | ✅ scripts/, references/, assets/ | ❌ Missing |
| Security restrictions | ⚠️ Via SkillSecurityValidator | ✅ Via allowed-tools | ⚠️ Different approach |

---

## Differences and Gaps

### 1. Naming Convention

**Current:**
```yaml
name: test-driven-development  # ✅ Already compliant
name: FastAPI Modern Web Development  # ❌ Contains uppercase and spaces
```

**Issue:** No validation for lowercase-hyphen format or 64-char limit

**Impact:** Some skills use human-readable names instead of identifier format

### 2. Field Structure

**Current (flat):**
```yaml
name: skill-name
description: Brief description
version: 1.0.0
author: mcp-skillset
tags: [python, testing]
```

**Spec (nested metadata):**
```yaml
name: skill-name
description: Brief description
metadata:
  version: 1.0.0
  author: mcp-skillset
  tags: [python, testing]
```

**Impact:** Incompatible field locations for optional metadata

### 3. Missing Security Features

**agentskills.io `allowed-tools`:**
```yaml
allowed-tools: [bash, python, file-operations]
```

**mcp-skillset approach:**
- Uses `SkillSecurityValidator` for content scanning
- No declarative tool restrictions in YAML
- Security enforced at runtime, not metadata level

**Impact:** Different security model - validation vs. restriction

### 4. No Support for Optional Directories

**Spec supports:**
- `skills/skill-name/scripts/` - Executable automation
- `skills/skill-name/references/` - Extended docs
- `skills/skill-name/assets/` - Media files

**mcp-skillset:**
- All content in single `SKILL.md` file
- No multi-file skill structure

**Impact:** Cannot distribute skills with supporting files

### 5. Progressive Disclosure Not Enforced

**Current:**
```yaml
# Only some skills include token estimates
progressive_disclosure:
  entry_point: [summary, when_to_use]
  full_content: all
token_estimates:
  entry_point: 70
  full: 5500
```

**Spec philosophy:**
- Frontmatter MUST be ~100 tokens
- Body MUST be <5000 tokens

**Impact:** No size constraints enforced during validation

---

## Recommendations for Full Compliance

### Priority 1: Critical Changes (Breaking)

#### 1.1 Add Spec-Required Fields Support

**File:** `src/mcp_skills/models/skill.py`

```python
class SkillMetadataModel(BaseModel):
    """Skill metadata with agentskills.io compliance."""

    # Required (spec)
    name: str = Field(
        ...,
        min_length=1,
        max_length=64,
        pattern=r'^[a-z0-9-]+$',  # Lowercase-hyphen only
        description="Skill identifier (lowercase-hyphen format)"
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=1024,  # Spec limit
        description="Brief skill description"
    )

    # Optional (spec)
    license: str | None = Field(None, description="SPDX license identifier")
    compatibility: list[str] = Field(
        default_factory=list,
        description="Compatible AI models"
    )
    allowed_tools: list[str] = Field(
        default_factory=list,
        description="Restricted tool access list"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (nested)"
    )

    # mcp-skillset extensions (optional)
    category: str | None = Field(None, description="Skill category")
    tags: list[str] = Field(default_factory=list, description="Tags")
    dependencies: list[str] = Field(default_factory=list, description="Dependencies")
    version: str | None = Field(None, description="Version")
    author: str | None = Field(None, description="Author")
```

#### 1.2 Enforce Progressive Disclosure Limits

**File:** `src/mcp_skills/services/validators/skill_validator.py`

```python
class SkillValidator:
    # Token estimation (rough: 1 token ≈ 4 chars)
    MAX_FRONTMATTER_TOKENS = 100
    MAX_FRONTMATTER_CHARS = 400
    MAX_BODY_TOKENS = 5000
    MAX_BODY_CHARS = 20000

    def validate_skill(self, skill: Skill) -> dict[str, list[str]]:
        errors = []
        warnings = []

        # Validate frontmatter size (agentskills.io requirement)
        frontmatter_yaml = yaml.dump(skill.metadata.to_dict())
        if len(frontmatter_yaml) > self.MAX_FRONTMATTER_CHARS:
            errors.append(
                f"Frontmatter too large ({len(frontmatter_yaml)} chars, "
                f"max {self.MAX_FRONTMATTER_CHARS} for ~100 tokens)"
            )

        # Validate body size (agentskills.io requirement)
        if len(skill.instructions) > self.MAX_BODY_CHARS:
            warnings.append(
                f"Instructions too large ({len(skill.instructions)} chars, "
                f"recommended max {self.MAX_BODY_CHARS} for ~5000 tokens)"
            )

        # Validate name format (lowercase-hyphen)
        if not re.match(r'^[a-z0-9-]+$', skill.name):
            errors.append(
                f"Invalid name format: '{skill.name}'. "
                "Use lowercase-hyphen format (e.g., 'test-driven-development')"
            )

        return {"errors": errors, "warnings": warnings}
```

### Priority 2: Non-Breaking Enhancements

#### 2.1 Support Optional Directories

**Structure:**
```
.claude/skills/fastapi-web-development/
├── SKILL.md                    # Main skill file
├── scripts/                    # Optional automation
│   ├── setup.sh
│   └── validate.py
├── references/                 # Optional extended docs
│   ├── api-design-patterns.md
│   └── examples/
└── assets/                     # Optional media
    └── architecture-diagram.png
```

**Implementation:**
```python
class SkillManager:
    def load_skill(self, skill_id: str) -> Skill | None:
        """Load skill with optional directories."""
        skill_dir = self.repos_dir / skill_id
        skill_file = skill_dir / "SKILL.md"

        if not skill_file.exists():
            return None

        skill = self._parse_skill_file(skill_file, repo_id)

        # Check for optional directories (agentskills.io spec)
        skill.has_scripts = (skill_dir / "scripts").is_dir()
        skill.has_references = (skill_dir / "references").is_dir()
        skill.has_assets = (skill_dir / "assets").is_dir()

        return skill
```

#### 2.2 Add Migration Tool for Legacy Skills

**Command:** `mcp-skillset migrate-to-spec`

```python
def migrate_skill_to_spec(skill_path: Path) -> dict:
    """Migrate mcp-skillset skill to agentskills.io format.

    Changes:
    - Validate name format (lowercase-hyphen)
    - Move optional fields to metadata object
    - Add license field prompt
    - Add compatibility field prompt
    - Validate size constraints
    """
    content = skill_path.read_text()
    frontmatter, body = split_frontmatter(content)
    metadata = yaml.safe_load(frontmatter)

    # Convert name to lowercase-hyphen
    name = metadata.get("name", "").lower().replace(" ", "-")
    name = re.sub(r'[^a-z0-9-]', '', name)[:64]

    # Restructure metadata
    new_metadata = {
        "name": name,
        "description": metadata.get("description", "")[:1024],
        "license": input("License (SPDX identifier): ") or None,
        "compatibility": ["claude-3.5-sonnet"],  # Default
        "metadata": {
            "version": metadata.get("version"),
            "author": metadata.get("author"),
            "tags": metadata.get("tags", []),
        }
    }

    # Write migrated skill
    new_content = f"---\n{yaml.dump(new_metadata)}---\n\n{body}"
    skill_path.write_text(new_content)

    return {"status": "success", "name": name}
```

### Priority 3: Documentation Updates

#### 3.1 Document Compatibility Mode

**File:** `docs/AGENTSKILLS_IO_COMPATIBILITY.md`

```markdown
# agentskills.io Compatibility

mcp-skillset supports both native format and agentskills.io specification.

## Native Format (default)
Uses category, tags, dependencies at top level.

## Spec-Compliant Format
Uses nested metadata, license, compatibility fields.

## Migration
Run: mcp-skillset migrate-to-spec [skill-path]
```

#### 3.2 Update Skill Templates

**File:** `docs/skill-templates/TEMPLATE.md`

```yaml
---
# Required (agentskills.io spec)
name: skill-name
description: Brief description (max 1024 chars)

# Optional (agentskills.io spec)
license: MIT
compatibility: [claude-3.5-sonnet, gpt-4]
metadata:
  version: 1.0.0
  author: Your Name
  tags: [tag1, tag2]
allowed-tools: [bash, python, file-operations]

# Optional (mcp-skillset extensions)
category: testing
dependencies: [other-skill-id]
---
```

---

## Migration Strategy

### Phase 1: Backward-Compatible Support (Recommended)

**Goal:** Support both formats without breaking existing skills

**Approach:**
1. Extend validator to accept BOTH formats:
   - Legacy: `tags` at top level
   - Spec: `tags` in `metadata` object
2. Normalize internally to spec format
3. No changes required to existing skills

**Implementation:**
```python
def _normalize_metadata(self, metadata: dict) -> dict:
    """Normalize metadata to agentskills.io format."""

    # If already spec-compliant, return as-is
    if "metadata" in metadata:
        return metadata

    # Migrate legacy format to spec format
    spec_metadata = {
        "name": metadata.get("name", ""),
        "description": metadata.get("description", ""),
        "metadata": {
            "version": metadata.get("version"),
            "author": metadata.get("author"),
            "tags": metadata.get("tags", []),
        }
    }

    # Preserve mcp-skillset extensions
    if "category" in metadata:
        spec_metadata["category"] = metadata["category"]
    if "dependencies" in metadata:
        spec_metadata["dependencies"] = metadata["dependencies"]

    return spec_metadata
```

### Phase 2: Gradual Migration

**Timeline:** 3-6 months

1. **Month 1:** Release backward-compatible parser
2. **Month 2:** Add migration tool and documentation
3. **Month 3:** Migrate core skills to spec format
4. **Month 4:** Add deprecation warnings for legacy format
5. **Month 6:** Make spec format default for new skills

### Phase 3: Full Compliance (Optional)

**Goal:** 100% agentskills.io specification compliance

**Changes:**
1. Remove legacy format support
2. Enforce all spec validations
3. Require spec-compliant names and structure
4. Support optional directories (scripts/, references/, assets/)

**Breaking Changes:**
- Skills with non-compliant names will fail validation
- Top-level metadata fields will be rejected
- Size limits will be enforced strictly

---

## Conclusion

### Current Status

**mcp-skillset is PARTIALLY compatible** with agentskills.io specification:

**✅ Compatible:**
- Uses YAML frontmatter with `---` delimiters
- Uses markdown body for instructions
- Supports progressive disclosure philosophy
- Name and description fields present

**⚠️ Partially Compatible:**
- Field structure differs (flat vs nested)
- No format validation for skill names
- No size enforcement for progressive disclosure
- Security model differs (validation vs restrictions)

**❌ Not Compatible:**
- Missing `license`, `compatibility`, `allowed-tools` fields
- No support for optional directories (scripts/, references/, assets/)
- Uses top-level metadata instead of nested `metadata` object

### Recommended Action

**Implement Phase 1: Backward-Compatible Support**

This provides immediate agentskills.io compatibility while preserving all existing skills and functionality. Users can choose to adopt spec format gradually without breaking changes.

**Next Steps:**
1. Update Pydantic models to support both formats
2. Add metadata normalization in parser
3. Update documentation with compatibility guide
4. Create migration tool for users who want full compliance
5. Consider Phase 2 migration for long-term alignment

**Estimated Effort:**
- Phase 1 (backward-compatible): 2-3 days
- Migration tool: 1-2 days
- Documentation: 1 day
- Testing: 1-2 days

**Total:** ~1 week for full backward-compatible agentskills.io support

---

## References

**agentskills.io Specification:**
- Website: https://agentskills.io
- Format: YAML frontmatter + Markdown body
- Philosophy: Progressive disclosure (~100 tokens metadata, <5k body)

**mcp-skillset Implementation:**
- Models: `src/mcp_skills/models/skill.py`
- Validator: `src/mcp_skills/services/validators/skill_validator.py`
- Parser: `src/mcp_skills/services/skill_manager.py`
- Templates: `docs/skill-templates/`

**Analyzed Skills:**
- `.claude/skills/universal-testing-test-driven-development/SKILL.md`
- `.claude/skills/toolchains-python-validation-pydantic/SKILL.md`
- `docs/skill-templates/fastapi-web-development/SKILL.md`

---

**Research Conducted By:** Research Agent
**Date:** 2026-01-17
**Version:** 1.0
