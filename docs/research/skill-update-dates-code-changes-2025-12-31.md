# Detailed Code Changes: Adding Update Dates to Skills

## Change 1: Update Skill Model (skill.py)

**File:** `src/mcp_skills/models/skill.py`

### 1.1 Add datetime import at the top

**Current (line 3):**
```python
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
```

**Change to:**
```python
from dataclasses import asdict, dataclass
from datetime import datetime  # ADD THIS
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
```

### 1.2 Update SkillMetadataModel (Pydantic) - line 10

**Current:**
```python
class SkillMetadataModel(BaseModel):
    """Skill metadata from YAML frontmatter."""

    name: str = Field(..., min_length=1, description="Skill name")
    description: str = Field(..., min_length=10, description="Skill description")
    category: str = Field(..., description="Skill category")
    tags: list[str] = Field(default_factory=list, description="Skill tags")
    dependencies: list[str] = Field(
        default_factory=list, description="Required skill dependencies"
    )
    version: str | None = Field(None, description="Skill version")
    author: str | None = Field(None, description="Skill author")
```

**Change to:**
```python
class SkillMetadataModel(BaseModel):
    """Skill metadata from YAML frontmatter."""

    name: str = Field(..., min_length=1, description="Skill name")
    description: str = Field(..., min_length=10, description="Skill description")
    category: str = Field(..., description="Skill category")
    tags: list[str] = Field(default_factory=list, description="Skill tags")
    dependencies: list[str] = Field(
        default_factory=list, description="Required skill dependencies"
    )
    version: str | None = Field(None, description="Skill version")
    author: str | None = Field(None, description="Skill author")
    updated_at: datetime | None = Field(None, description="Skill last update timestamp")  # ADD THIS
```

### 1.3 Update SkillModel (Pydantic) - line 28

**Current:**
```python
class SkillModel(BaseModel):
    """Complete skill data model with validation."""

    id: str = Field(..., min_length=1, description="Unique skill identifier")
    name: str = Field(..., min_length=1, description="Skill name")
    description: str = Field(..., min_length=10, description="Skill description")
    instructions: str = Field(
        ..., min_length=50, description="Full skill instructions (markdown)"
    )
    category: str = Field(..., description="Skill category")
    tags: list[str] = Field(default_factory=list, description="Skill tags")
    dependencies: list[str] = Field(
        default_factory=list, description="Required skill dependencies"
    )
    examples: list[str] = Field(default_factory=list, description="Usage examples")
    file_path: str = Field(..., description="Path to SKILL.md file")
    repo_id: str = Field(..., description="Repository identifier")
    version: str | None = Field(None, description="Skill version")
    author: str | None = Field(None, description="Skill author")
```

**Change to:**
```python
class SkillModel(BaseModel):
    """Complete skill data model with validation."""

    id: str = Field(..., min_length=1, description="Unique skill identifier")
    name: str = Field(..., min_length=1, description="Skill name")
    description: str = Field(..., min_length=10, description="Skill description")
    instructions: str = Field(
        ..., min_length=50, description="Full skill instructions (markdown)"
    )
    category: str = Field(..., description="Skill category")
    tags: list[str] = Field(default_factory=list, description="Skill tags")
    dependencies: list[str] = Field(
        default_factory=list, description="Required skill dependencies"
    )
    examples: list[str] = Field(default_factory=list, description="Usage examples")
    file_path: str = Field(..., description="Path to SKILL.md file")
    repo_id: str = Field(..., description="Repository identifier")
    version: str | None = Field(None, description="Skill version")
    author: str | None = Field(None, description="Skill author")
    updated_at: datetime | None = Field(None, description="Skill last update timestamp")  # ADD THIS
```

### 1.4 Update SkillMetadata dataclass - line 73

**Current:**
```python
@dataclass
class SkillMetadata:
    """Skill metadata from YAML frontmatter."""

    name: str
    description: str
    category: str
    tags: list[str]
    dependencies: list[str]
    version: str | None = None
    author: str | None = None
```

**Change to:**
```python
@dataclass
class SkillMetadata:
    """Skill metadata from YAML frontmatter."""

    name: str
    description: str
    category: str
    tags: list[str]
    dependencies: list[str]
    version: str | None = None
    author: str | None = None
    updated_at: datetime | None = None  # ADD THIS
```

### 1.5 Update SkillMetadata.to_dict() - line 94

**Current:**
```python
def to_dict(self) -> dict[str, Any]:
    """Convert SkillMetadata to dictionary for JSON serialization."""
    return asdict(self)
```

**Change to:**
```python
def to_dict(self) -> dict[str, Any]:
    """Convert SkillMetadata to dictionary for JSON serialization."""
    data = asdict(self)
    data["updated_at"] = self.updated_at.isoformat() if self.updated_at else None  # ADD THIS
    return data
```

### 1.6 Update SkillMetadata.from_dict() - line 102

**Current:**
```python
@classmethod
def from_dict(cls, data: dict[str, Any]) -> "SkillMetadata":
    """Create SkillMetadata from dictionary loaded from JSON."""
    return cls(
        name=data["name"],
        description=data["description"],
        category=data["category"],
        tags=data.get("tags", []),
        dependencies=data.get("dependencies", []),
        version=data.get("version"),
        author=data.get("author"),
    )
```

**Change to:**
```python
@classmethod
def from_dict(cls, data: dict[str, Any]) -> "SkillMetadata":
    """Create SkillMetadata from dictionary loaded from JSON."""
    # ADD THESE 3 LINES
    updated_at_str = data.get("updated_at")
    updated_at = datetime.fromisoformat(updated_at_str) if updated_at_str else None

    return cls(
        name=data["name"],
        description=data["description"],
        category=data["category"],
        tags=data.get("tags", []),
        dependencies=data.get("dependencies", []),
        version=data.get("version"),
        author=data.get("author"),
        updated_at=updated_at,  # ADD THIS
    )
```

### 1.7 Update Skill dataclass - line 124

**Current:**
```python
@dataclass
class Skill:
    """Complete skill data model."""

    id: str
    name: str
    description: str
    instructions: str
    category: str
    tags: list[str]
    dependencies: list[str]
    examples: list[str]
    file_path: Path
    repo_id: str
    version: str | None = None
    author: str | None = None
```

**Change to:**
```python
@dataclass
class Skill:
    """Complete skill data model."""

    id: str
    name: str
    description: str
    instructions: str
    category: str
    tags: list[str]
    dependencies: list[str]
    examples: list[str]
    file_path: Path
    repo_id: str
    version: str | None = None
    author: str | None = None
    updated_at: datetime | None = None  # ADD THIS
```

### 1.8 Update Skill.to_dict() - line 155

**Current:**
```python
def to_dict(self) -> dict[str, Any]:
    """Convert Skill to dictionary for JSON serialization."""
    data = asdict(self)
    data["file_path"] = str(self.file_path)
    return data
```

**Change to:**
```python
def to_dict(self) -> dict[str, Any]:
    """Convert Skill to dictionary for JSON serialization."""
    data = asdict(self)
    data["file_path"] = str(self.file_path)
    data["updated_at"] = self.updated_at.isoformat() if self.updated_at else None  # ADD THIS
    return data
```

### 1.9 Update Skill.from_dict() - line 165

**Current:**
```python
@classmethod
def from_dict(cls, data: dict[str, Any]) -> "Skill":
    """Create Skill from dictionary loaded from JSON."""
    return cls(
        id=data["id"],
        name=data["name"],
        description=data["description"],
        instructions=data["instructions"],
        category=data["category"],
        tags=data.get("tags", []),
        dependencies=data.get("dependencies", []),
        examples=data.get("examples", []),
        file_path=Path(data["file_path"]),
        repo_id=data["repo_id"],
        version=data.get("version"),
        author=data.get("author"),
    )
```

**Change to:**
```python
@classmethod
def from_dict(cls, data: dict[str, Any]) -> "Skill":
    """Create Skill from dictionary loaded from JSON."""
    # ADD THESE 3 LINES
    updated_at_str = data.get("updated_at")
    updated_at = datetime.fromisoformat(updated_at_str) if updated_at_str else None

    return cls(
        id=data["id"],
        name=data["name"],
        description=data["description"],
        instructions=data["instructions"],
        category=data["category"],
        tags=data.get("tags", []),
        dependencies=data.get("dependencies", []),
        examples=data.get("examples", []),
        file_path=Path(data["file_path"]),
        repo_id=data["repo_id"],
        version=data.get("version"),
        author=data.get("author"),
        updated_at=updated_at,  # ADD THIS
    )
```

---

## Change 2: Update Skill Manager (skill_manager.py)

**File:** `src/mcp_skills/services/skill_manager.py`

### 2.1 Update imports at the top

**Current (line 3):**
```python
import logging
from pathlib import Path

import yaml
from pydantic import ValidationError
```

**Change to:**
```python
import logging
from datetime import UTC, datetime  # ADD UTC to imports
from pathlib import Path

import yaml
from pydantic import ValidationError
```

### 2.2 Capture mtime in _parse_skill_file()

**Location:** Inside `_parse_skill_file()` method, around line 482 (after extracting examples)

**Current:**
```python
# Extract examples from instructions (look for ## Examples section)
examples = self._extract_examples(instructions)

# Build skill data for validation
skill_data = {
    "id": skill_id,
    "name": metadata.get("name", ""),
    # ... rest of fields ...
}
```

**Change to:**
```python
# Extract examples from instructions (look for ## Examples section)
examples = self._extract_examples(instructions)

# Capture file modification time
try:
    mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=UTC)
except (OSError, AttributeError):
    mtime = None

# Build skill data for validation
skill_data = {
    "id": skill_id,
    "name": metadata.get("name", ""),
    # ... rest of fields ...
    "updated_at": mtime,  # ADD THIS
}
```

### 2.3 Pass updated_at to Skill constructor

**Location:** Inside `_parse_skill_file()` method, around line 504 (Skill creation)

**Current:**
```python
# Create Skill dataclass instance
return Skill(
    id=skill_model.id,
    name=skill_model.name,
    description=skill_model.description,
    instructions=skill_model.instructions,
    category=skill_model.category,
    tags=skill_model.tags,
    dependencies=skill_model.dependencies,
    examples=skill_model.examples,
    file_path=file_path,
    repo_id=skill_model.repo_id,
    version=skill_model.version,
    author=skill_model.author,
)
```

**Change to:**
```python
# Create Skill dataclass instance
return Skill(
    id=skill_model.id,
    name=skill_model.name,
    description=skill_model.description,
    instructions=skill_model.instructions,
    category=skill_model.category,
    tags=skill_model.tags,
    dependencies=skill_model.dependencies,
    examples=skill_model.examples,
    file_path=file_path,
    repo_id=skill_model.repo_id,
    version=skill_model.version,
    author=skill_model.author,
    updated_at=skill_model.updated_at,  # ADD THIS
)
```

---

## Change 3: Update Vector Store (vector_store.py)

**File:** `src/mcp_skills/services/indexing/vector_store.py`

### 3.1 Update metadata dict in index_skill()

**Location:** Inside `index_skill()` method, around line 164

**Current:**
```python
# Prepare metadata
metadata = {
    "skill_id": skill.id,
    "name": skill.name,
    "category": skill.category,
    "tags": ",".join(skill.tags),  # Comma-separated for ChromaDB
    "repo_id": skill.repo_id,
}
```

**Change to:**
```python
# Prepare metadata
metadata = {
    "skill_id": skill.id,
    "name": skill.name,
    "category": skill.category,
    "tags": ",".join(skill.tags),  # Comma-separated for ChromaDB
    "repo_id": skill.repo_id,
    "updated_at": skill.updated_at.isoformat() if skill.updated_at else None,  # ADD THIS
}
```

---

## Summary

### Files Modified: 3
1. `src/mcp_skills/models/skill.py`
2. `src/mcp_skills/services/skill_manager.py`
3. `src/mcp_skills/services/indexing/vector_store.py`

### Total Changes:
- **Lines added:** ~20
- **Lines modified:** ~15
- **Breaking changes:** None
- **New dependencies:** None (datetime is stdlib)

### Testing Required:
1. Update test fixtures (add updated_at to sample skills)
2. Test mtime capture in _parse_skill_file()
3. Test datetime serialization/deserialization
4. Test ChromaDB metadata storage
5. Integration tests with actual SKILL.md files

### Backward Compatibility:
- Field is optional (None default)
- Existing skills without dates gracefully handled
- No API changes
- Safe to deploy without migration
