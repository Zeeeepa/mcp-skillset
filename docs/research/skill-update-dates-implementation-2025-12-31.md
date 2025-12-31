# Research: Adding Update Dates to Skills

**Date:** December 31, 2025
**Status:** Research Complete
**Scope:** Understanding current skill indexing architecture to implement update date tracking

---

## Executive Summary

This research analyzes the skill indexing infrastructure to determine the best approach for adding update date tracking. The codebase has a clear separation of concerns:

1. **Skill Model** (`src/mcp_skills/models/skill.py`) - Defines skill structure
2. **Skill Manager** (`src/mcp_skills/services/skill_manager.py`) - Loads and caches skills
3. **Indexing Engine** (`src/mcp_skills/services/indexing/engine.py`) - Orchestrates indexing
4. **Vector Store** (`src/mcp_skills/services/indexing/vector_store.py`) - ChromaDB integration

**Recommendation:** Add `updated_at` field to the `Skill` dataclass and store as ChromaDB metadata. Use file mtime as the source (simpler) with optional git commit date enhancement for future releases.

---

## Current Architecture

### 1. Skill Model Structure

**File:** `/Users/masa/Projects/mcp-skillset/src/mcp_skills/models/skill.py`

Current `Skill` dataclass fields:
- `id`: Unique skill identifier (format: `{repo_id}/{skill_path}`)
- `name`: Skill name
- `description`: Short description
- `instructions`: Full skill instructions (markdown)
- `category`: Skill category (testing, debugging, refactoring, etc.)
- `tags`: List of tags
- `dependencies`: List of skill IDs this depends on
- `examples`: List of example usage scenarios
- `file_path`: Path to SKILL.md file (Python `Path` object)
- `repo_id`: Repository identifier
- `version`: Optional version string
- `author`: Optional author information

**Status:** No date fields currently tracked.

### 2. Skill Manager (Discovery and Loading)

**File:** `/Users/masa/Projects/mcp-skillset/src/mcp_skills/services/skill_manager.py`

Key methods:
- `discover_skills()`: Walks directory tree to find all SKILL.md files
- `load_skill()`: Loads skill from disk with in-memory caching
- `get_skill_metadata()`: Fast metadata extraction from YAML frontmatter
- `_parse_skill_file()`: Creates Skill object from file content

**Important:** The `_parse_skill_file()` method (line 429):
1. Reads file content using `file_path.read_text(encoding="utf-8")`
2. Splits frontmatter and instructions
3. Validates with Pydantic models (`SkillModel`)
4. Creates Skill dataclass instance

**Access to file mtime:** Possible via `file_path.stat().st_mtime` when Skill object is created.

### 3. Indexing Engine (Orchestration)

**File:** `/Users/masa/Projects/mcp-skillset/src/mcp_skills/services/indexing/engine.py`

Key methods:
- `index_skill()`: Adds skill to vector store and knowledge graph
- `reindex_all()`: Rebuilds indices from scratch
- `build_embeddings()`: Delegates to VectorStore
- `extract_relationships()`: Delegates to GraphStore

Flow:
1. SkillManager discovers/loads skills
2. IndexingEngine receives Skill objects
3. Calls `vector_store.index_skill()` with Skill object
4. Calls `graph_store.add_skill()` with Skill object

### 4. Vector Store (ChromaDB Integration)

**File:** `/Users/masa/Projects/mcp-skillset/src/mcp_skills/services/indexing/vector_store.py`

The `index_skill()` method (line 141) currently:

```python
# Prepare metadata
metadata = {
    "skill_id": skill.id,
    "name": skill.name,
    "category": skill.category,
    "tags": ",".join(skill.tags),  # Comma-separated for ChromaDB
    "repo_id": skill.repo_id,
}

# Add to ChromaDB (embeddings generated automatically)
self.collection.add(
    ids=[skill.id],
    documents=[embeddable_text],
    metadatas=[metadata],
)
```

**Current metadata stored:**
- `skill_id`: Unique identifier
- `name`: Skill name
- `category`: Category (for filtering)
- `tags`: Comma-separated tags (for filtering)
- `repo_id`: Repository identifier

**Status:** No timestamp or date metadata currently stored.

---

## Data Sources for Update Dates

### Option 1: File Modification Time (mtime) - RECOMMENDED

**Advantages:**
- Simple to implement: `file_path.stat().st_mtime`
- Works for all environments (no git required)
- Automatic on file changes (no manual tracking)
- Readily available at skill parsing time
- No external dependencies

**Disadvantages:**
- Can be misleading (file copy, extraction, etc. changes mtime)
- Not reliable for git-tracked files (rebase/merge can change mtime)
- Requires file system access

**Implementation location:** In `SkillManager._parse_skill_file()` method

### Option 2: Git Commit Date - FUTURE ENHANCEMENT

**Advantages:**
- Most accurate for version-controlled skills
- Reflects actual content changes
- Works across clones/copies
- Already used in `RepositoryManager` (line 404 in repository_manager.py)

**Disadvantages:**
- Requires git repository (not all skills may be git-tracked)
- Slower (requires git command execution)
- Only works for committed files
- Extra complexity for initial implementation

**Implementation location:** In a future service layer that queries git metadata

**Example from existing code** (`repository_manager.py`):
```python
from datetime import UTC, datetime
# ...
repository.last_updated = datetime.now(UTC)
```

---

## Implementation Approach

### Phase 1: Add to Skill Model and Indexing

**1. Update Skill Model** (`src/mcp_skills/models/skill.py`)

Add field to both dataclasses:

```python
from datetime import datetime

@dataclass
class SkillMetadata:
    # ... existing fields ...
    updated_at: datetime | None = None

@dataclass
class Skill:
    # ... existing fields ...
    updated_at: datetime | None = None
```

Also update Pydantic models:

```python
class SkillMetadataModel(BaseModel):
    # ... existing fields ...
    updated_at: datetime | None = Field(None, description="Skill last update timestamp")

class SkillModel(BaseModel):
    # ... existing fields ...
    updated_at: datetime | None = Field(None, description="Skill last update timestamp")
```

**2. Capture Date in SkillManager** (`src/mcp_skills/services/skill_manager.py`)

In `_parse_skill_file()` method (~line 429):

```python
def _parse_skill_file(self, file_path: Path, repo_id: str) -> Skill | None:
    try:
        # ... existing code ...

        # Get file modification time
        try:
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=UTC)
        except (OSError, AttributeError):
            mtime = None

        # Build skill data for validation
        skill_data = {
            # ... existing fields ...
            "updated_at": mtime,
        }
        # ... rest of method ...
```

**3. Store in ChromaDB Metadata** (`src/mcp_skills/services/indexing/vector_store.py`)

In `index_skill()` method (~line 163):

```python
# Prepare metadata
metadata = {
    "skill_id": skill.id,
    "name": skill.name,
    "category": skill.category,
    "tags": ",".join(skill.tags),
    "repo_id": skill.repo_id,
    "updated_at": skill.updated_at.isoformat() if skill.updated_at else None,
}
```

**4. Backward Compatibility**

- Make `updated_at` optional (default: `None`)
- Existing skills without dates will have `None`
- ChromaDB can filter by presence: `where={"updated_at": {"$ne": None}}`

---

## Query Implementation Options

### Option A: Separate Search Parameter (Recommended for Phase 2)

```python
def search(
    self,
    query: str,
    top_k: int = 20,
    filters: dict[str, Any] | None = None,
    updated_after: datetime | None = None,
    updated_before: datetime | None = None,
) -> list[ScoredSkill]:
    """Search with optional date filtering."""
    if not filters:
        filters = {}

    if updated_after:
        filters["updated_at"] = {"$gte": updated_after.isoformat()}
    if updated_before:
        filters["updated_at"] = {"$lte": updated_before.isoformat()}

    # ... existing search logic ...
```

### Option B: New Command

```bash
mcp-skillset search-recent --days 30 --query "testing"
```

Would query skills updated in last 30 days.

### Option C: Sort Results by Recency

```python
def search(
    self,
    query: str,
    top_k: int = 20,
    sort_by: str = "relevance",  # or "recent" or "oldest"
) -> list[ScoredSkill]:
    """Search with optional date-based sorting."""
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    SKILL.md File                        │
│  Contains: YAML frontmatter + markdown instructions      │
│  File stat contains: mtime (last modification)           │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│           SkillManager._parse_skill_file()              │
│  1. Read file (mtime captured here)                     │
│  2. Parse frontmatter + instructions                     │
│  3. Create Skill object with updated_at                 │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              Skill Dataclass                            │
│  + Fields: id, name, description, instructions...       │
│  + NEW: updated_at (datetime | None)                    │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│            IndexingEngine.index_skill()                 │
│  Receives Skill object with updated_at                 │
└────────────────────┬──────────────────────┬─────────────┘
                     │                      │
        ┌────────────▼───────────┐  ┌─────▼──────────────┐
        │   VectorStore          │  │  GraphStore        │
        │ (ChromaDB)             │  │  (NetworkX)        │
        │                        │  │                    │
        │ metadata = {           │  │ Add skill node     │
        │   "updated_at": ...    │  │ Add relationships  │
        │ }                      │  │                    │
        └────────────────────────┘  └────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │  ChromaDB Persistence  │
        │  (can query by date)   │
        └────────────────────────┘
```

---

## Files to Modify

### Must Modify:
1. **`src/mcp_skills/models/skill.py`**
   - Add `updated_at` field to `Skill` dataclass
   - Add `updated_at` field to `SkillMetadata` dataclass
   - Add to Pydantic models (`SkillModel`, `SkillMetadataModel`)
   - Update `to_dict()` and `from_dict()` methods

2. **`src/mcp_skills/services/skill_manager.py`**
   - Modify `_parse_skill_file()` to capture mtime
   - Update skill_data dict building to include `updated_at`

3. **`src/mcp_skills/services/indexing/vector_store.py`**
   - Update `index_skill()` metadata dict to include `updated_at`

### Should Update (Phase 2):
4. **`src/mcp_skills/services/indexing/hybrid_search.py`**
   - Add date filtering support to `search()` method

5. **CLI Commands** (`src/mcp_skills/cli/commands/`)
   - Add `--updated-after`, `--updated-before` flags to search
   - Add `--sort-by` flag with "recent" option

### Test Files:
6. **`tests/test_indexing_engine.py`**
   - Add tests for date field serialization
   - Add tests for date-based filtering

7. **`tests/test_skill_manager.py`**
   - Add tests to verify mtime capture

---

## Serialization Considerations

### JSON Storage
The Skill model already handles serialization via `to_dict()` and `from_dict()`. Update these:

```python
def to_dict(self) -> dict[str, Any]:
    data = asdict(self)
    data["file_path"] = str(self.file_path)
    data["updated_at"] = self.updated_at.isoformat() if self.updated_at else None
    return data

@classmethod
def from_dict(cls, data: dict[str, Any]) -> "Skill":
    # ... existing code ...
    updated_at_str = data.get("updated_at")
    updated_at = datetime.fromisoformat(updated_at_str) if updated_at_str else None

    return cls(
        # ... existing fields ...
        updated_at=updated_at,
    )
```

### ChromaDB Metadata
ChromaDB metadata is a simple dict. Dates must be serialized:

```python
metadata = {
    "skill_id": skill.id,
    "updated_at": skill.updated_at.isoformat() if skill.updated_at else None,
}

# For querying:
# where={"updated_at": {"$gte": "2025-01-01T00:00:00+00:00"}}
```

---

## Performance Implications

### Speed Impact:
- **Negligible**: mtime is retrieved via `stat()` call, already needed for other purposes
- **Storage**: ~30 bytes per skill for ISO datetime string (minimal)
- **Search**: Optional filters add minimal overhead to ChromaDB queries

### Memory Impact:
- **Negligible**: One datetime object per skill in memory (~56 bytes)
- **Indexing**: No significant impact on embedding generation

### Scale Testing (estimated):
- 100 skills: No measurable difference
- 1000 skills: <1% overhead
- 10,000 skills: <2% overhead

---

## Related Code Patterns

### Existing DateTime Usage in Codebase

**`src/mcp_skills/models/repository.py`:**
```python
from datetime import datetime

@dataclass
class Repository:
    last_updated: datetime  # Already tracks repository update time

    def to_dict(self) -> dict[str, Any]:
        data["last_updated"] = self.last_updated.isoformat()
        return data
```

**`src/mcp_skills/services/repository_manager.py`:**
```python
from datetime import UTC, datetime

# Already uses UTC timezone for consistency
repository.last_updated = datetime.now(UTC)
```

**Recommendation:** Follow same pattern for consistency:
- Use `datetime` from standard library
- Use UTC timezone when parsing system time
- Use `.isoformat()` for serialization

---

## Implementation Checklist

### Phase 1: Core Implementation
- [ ] Add `updated_at` field to `Skill` dataclass
- [ ] Add `updated_at` field to `SkillMetadata` dataclass
- [ ] Add `updated_at` to Pydantic models
- [ ] Update Skill `to_dict()` and `from_dict()` methods
- [ ] Update SkillManager `_parse_skill_file()` to capture mtime
- [ ] Update VectorStore metadata to include `updated_at`
- [ ] Update unit tests to handle datetime fields
- [ ] Verify serialization works (JSON round-trip)
- [ ] Test with sample skills

### Phase 2: Query Support
- [ ] Add date filter parameters to hybrid_search
- [ ] Implement date range filtering
- [ ] Add sorting by date
- [ ] Add CLI flags for date filtering
- [ ] Update documentation

### Phase 3: Future Enhancements
- [ ] Git commit date extraction (requires git integration)
- [ ] Skill update notifications
- [ ] "Recently updated" skill recommendations
- [ ] Migration script for adding dates to existing indices

---

## Risk Assessment

### Low Risk:
- Adding optional field (backward compatible)
- File mtime is always available
- No breaking changes to API

### Medium Risk:
- Serialization edge cases (None values)
- Timezone consistency (use UTC)
- ChromaDB query syntax for dates

### Mitigation:
- Comprehensive unit tests
- Handle None gracefully
- Clear documentation
- Gradual rollout (optional field)

---

## Summary Table

| Aspect | Recommendation | Rationale |
|--------|-----------------|-----------|
| **Date Source** | File mtime (Phase 1) | Simple, no dependencies, works everywhere |
| **Storage Location** | Skill model + ChromaDB metadata | Searchable, queryable, persistent |
| **Data Type** | Python datetime (UTC) | Matches existing Repository pattern |
| **Serialization** | ISO format string | Standard, timezone-aware |
| **Query Method** | ChromaDB where filters | Native support, efficient |
| **Backward Compatibility** | Optional field (None) | Safe for existing skills |
| **Phase 2 Enhancement** | Git commit dates | More accurate, optional complexity |

---

## Files Analyzed

1. `/Users/masa/Projects/mcp-skillset/src/mcp_skills/models/skill.py` - Skill data models
2. `/Users/masa/Projects/mcp-skillset/src/mcp_skills/services/skill_manager.py` - Skill lifecycle (discovery, loading, caching)
3. `/Users/masa/Projects/mcp-skillset/src/mcp_skills/services/indexing/engine.py` - Indexing orchestration
4. `/Users/masa/Projects/mcp-skillset/src/mcp_skills/services/indexing/vector_store.py` - ChromaDB vector store
5. `/Users/masa/Projects/mcp-skillset/src/mcp_skills/models/repository.py` - Repository model (datetime pattern reference)
6. `/Users/masa/Projects/mcp-skillset/src/mcp_skills/services/repository_manager.py` - Repository management (git integration example)
7. `/Users/masa/Projects/mcp-skillset/tests/test_indexing_engine.py` - Existing indexing tests

---

## Next Steps

1. **Review this analysis** - Verify approach aligns with project architecture
2. **Create Linear ticket** - Reference this research and implementation checklist
3. **Implement Phase 1** - Core date field addition
4. **Write unit tests** - Verify serialization and storage
5. **Plan Phase 2** - Query and filtering support
