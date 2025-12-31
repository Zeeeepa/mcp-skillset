# Quick Reference: Update Date Implementation

## Key Code Locations

### 1. Skill Model - WHERE TO ADD THE FIELD
**File:** `/Users/masa/Projects/mcp-skillset/src/mcp_skills/models/skill.py`

Current Skill dataclass (line 124-153):
- Add field: `updated_at: datetime | None = None`
- Also update `to_dict()` method (line 155-163) to serialize datetime to ISO string
- Also update `from_dict()` method (line 165-189) to deserialize from ISO string
- Same changes for `SkillMetadata` dataclass and Pydantic models

### 2. Skill Manager - WHERE TO CAPTURE THE DATE
**File:** `/Users/masa/Projects/mcp-skillset/src/mcp_skills/services/skill_manager.py`

In `_parse_skill_file()` method (~line 429-521):
- Before line 485 (building skill_data), capture file mtime:
  ```python
  try:
      mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=UTC)
  except (OSError, AttributeError):
      mtime = None
  ```
- Add to skill_data dict: `"updated_at": mtime`
- Import `from datetime import UTC, datetime` at the top

### 3. Vector Store - WHERE TO STORE IN CHROMADB
**File:** `/Users/masa/Projects/mcp-skillset/src/mcp_skills/services/indexing/vector_store.py`

In `index_skill()` method (~line 141-184):
- Update metadata dict (line 164-170):
  ```python
  metadata = {
      "skill_id": skill.id,
      "name": skill.name,
      "category": skill.category,
      "tags": ",".join(skill.tags),
      "repo_id": skill.repo_id,
      "updated_at": skill.updated_at.isoformat() if skill.updated_at else None,
  }
  ```

## Date Source Decision

**✓ FILE MTIME (Recommended for Phase 1)**
- Captured via: `file_path.stat().st_mtime`
- Location: SkillManager._parse_skill_file()
- Format: Python datetime with UTC timezone
- Serialization: ISO format string for JSON/ChromaDB
- Why: Simple, no dependencies, works everywhere

**✗ GIT COMMIT DATE (Future Phase 2)**
- Would require: `git.Repo(skill_file.parent)` calls
- More accurate but requires git access
- Can be added later without breaking existing code

## Import Statements to Add

**In skill.py:**
```python
from datetime import datetime
```

**In skill_manager.py:**
```python
from datetime import UTC, datetime  # Add UTC to existing imports
```

## Backward Compatibility

- Field is optional: `updated_at: datetime | None = None`
- Existing skills without dates will have `None` value
- No API breaks
- Can migrate existing indices when needed

## Testing Locations

**File:** `/Users/masa/Projects/mcp-skillset/tests/test_indexing_engine.py`
- Line 25-71: sample_skills fixture (add updated_at to test skills)
- Add tests for datetime serialization

**File:** `/Users/masa/Projects/mcp-skillset/tests/test_skill_manager.py`
- Need new tests for mtime capture in _parse_skill_file()

## ChromaDB Query Examples (Phase 2)

```python
# Filter for recently updated skills
where={"updated_at": {"$gte": "2025-01-01T00:00:00+00:00"}}

# Filter for skills updated before date
where={"updated_at": {"$lte": "2025-01-01T00:00:00+00:00"}}

# Filter for skills with no date (older skills)
where={"updated_at": {"$eq": None}}
```

## Files to Modify

| File | Changes | Lines |
|------|---------|-------|
| `src/mcp_skills/models/skill.py` | Add datetime import + 4 dataclasses + 4 serialization methods | ~30 |
| `src/mcp_skills/services/skill_manager.py` | Add UTC import + capture mtime + pass to Skill | ~10 |
| `src/mcp_skills/services/indexing/vector_store.py` | Update metadata dict in index_skill() | ~1 |
| **Total** | **3 files** | **~41 lines** |

## Phase 1 Checklist

- [ ] Add datetime import to skill.py
- [ ] Add updated_at field to Skill dataclass
- [ ] Add updated_at field to SkillMetadata dataclass
- [ ] Update Pydantic models (SkillModel, SkillMetadataModel)
- [ ] Update to_dict() methods to serialize datetime
- [ ] Update from_dict() methods to deserialize datetime
- [ ] Add UTC import to skill_manager.py
- [ ] Capture mtime in _parse_skill_file()
- [ ] Add updated_at to skill_data dict
- [ ] Pass updated_at to Skill constructor
- [ ] Update metadata dict in vector_store.py
- [ ] Update test fixtures (add updated_at)
- [ ] Write tests for mtime capture
- [ ] Write tests for datetime serialization
- [ ] Test with actual skill files

## Expected Impact

- **Code complexity:** Minimal (optional field, no new logic)
- **Performance:** Negligible (<1% overhead)
- **Memory:** ~56 bytes per skill (datetime object)
- **Storage:** ~30 bytes per skill (ISO string in ChromaDB)
- **Breaking changes:** None (fully backward compatible)

## Related Code Patterns

The codebase already uses datetime in Repository model:
- `src/mcp_skills/models/repository.py`: `last_updated: datetime`
- `src/mcp_skills/services/repository_manager.py`: Uses `datetime.now(UTC)`

Follow the same pattern for consistency.
