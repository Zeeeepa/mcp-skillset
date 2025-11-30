# CLI Command Refactoring Status - Ticket 1M-460

**Date:** 2025-11-30
**Ticket:** https://linear.app/1m-hyperdev/issue/1M-460
**Analyst:** Research Agent
**Status:** In Progress - Phase 1 Complete (Extraction), Phase 2 Pending (Integration)

---

## Executive Summary

**Current Progress: 8/18 commands extracted (44% complete)**

The CLI refactoring effort has successfully extracted 8 commands to modular files in `src/mcp_skills/cli/commands/`. However, **Phase 2 integration work is pending** - the extracted commands need to be:
1. Imported into main.py
2. Registered with the CLI group
3. Original implementations removed from main.py

**Key Finding:** Extraction is proceeding well, but commands remain duplicated in both locations. Main.py is still 2,568 lines and will shrink significantly once Phase 2 is completed for extracted commands.

---

## Detailed Status

### ✅ Extracted Commands (8/18 - 44%)

Commands successfully extracted to `src/mcp_skills/cli/commands/`:

| Command | Status | Lines Extracted | File Size | Complexity | Commit |
|---------|--------|----------------|-----------|------------|--------|
| **mcp** | ✅ Extracted | 53 | 1.7K | Simple | 5ffed42 |
| **list** | ✅ Extracted | 95 | 3.1K | Simple | 5ffed42 |
| **info** | ✅ Extracted | 129 | 4.1K | Medium | 5ffed42 |
| **show** | ✅ Extracted | (aliased to info) | - | Simple | 5ffed42 |
| **search** | ✅ Extracted | 111 | 4.0K | Medium | 67eba48 |
| **doctor** | ✅ Extracted | 149 | 5.2K | Medium | 67eba48 |
| **demo** | ✅ Extracted | 194 | 7.0K | Complex | 67eba48 |
| **index** | ✅ Extracted | 97 | 3.6K | Medium | (inferred) |
| **recommend** | ✅ Extracted | 127 | 4.6K | Medium | 69a951b |

**Total Extracted:** ~955 lines of command code

### ⏳ Remaining Commands (9/18 - 50%)

Commands still in main.py requiring extraction:

| Command | Lines (main.py) | Complexity | Priority | Dependencies | Effort Estimate |
|---------|----------------|------------|----------|--------------|-----------------|
| **stats** | 71 | Simple | HIGH | SkillManager, usage tracking | 1-2 hours |
| **enrich** | 155 | Medium | MEDIUM | PromptEnricher, SkillManager | 2-3 hours |
| **build-skill** | 187 | Medium | MEDIUM | Template system, validation | 2-3 hours |
| **config** | 237 | Complex | HIGH | Config management, interactive UI | 3-4 hours |
| **setup** | 271 | Complex | CRITICAL | ToolchainDetector, AgentInstaller | 4-5 hours |
| **repo** | 310 | Complex | MEDIUM | RepositoryManager, 3 subcommands | 4-5 hours |
| **discover** | 381 | Complex | LOW | GitHubDiscovery, API integration | 5-6 hours |
| **install** | 885 | Very Complex | CRITICAL | AgentInstaller, multi-agent support | 8-10 hours |

**Note:** `repo` is actually a command group with 3 subcommands:
- `repo add` (L1305-1351)
- `repo list` (L1352-1399)
- `repo update` (L1400-1449)

### ❌ Non-Existent Commands (1/18)

| Command | Status | Notes |
|---------|--------|-------|
| **hybrid** | ❌ Does not exist | Hybrid search is a config option, not a command |

**Finding:** The `hybrid` command was planned but never implemented. Hybrid search functionality exists as configuration parameters in the `config` command and as `--search-mode` options in `search` and `recommend` commands.

---

## Complexity Analysis

### Simple Commands (71-95 lines)
1. **stats** - 71 lines
   - Usage statistics display
   - Minimal dependencies
   - Straightforward extraction

### Medium Commands (111-237 lines)
2. **enrich** - 155 lines
   - Prompt enrichment with skills
   - PromptEnricher service integration
   - Moderate complexity

3. **build-skill** - 187 lines
   - Skill template generation
   - Validation and deployment
   - Interactive prompts

4. **config** - 237 lines
   - Configuration management
   - Interactive UI with rich library
   - Multiple config sections

### Complex Commands (271-381 lines)
5. **setup** - 271 lines
   - Project auto-configuration
   - Toolchain detection
   - Agent installation orchestration
   - Critical for user onboarding

6. **repo** - 310 lines (command group)
   - Repository management
   - 3 subcommands (add, list, update)
   - Requires preserving Click group structure

7. **discover** - 381 lines
   - GitHub API integration
   - Repository discovery
   - Complex error handling

### Very Complex Commands (885 lines)
8. **install** - 885 lines
   - Multi-agent installation
   - Complex agent detection
   - JSON/config file manipulation
   - Error recovery and validation
   - Most critical for user experience

---

## Recommended Extraction Order

### Phase 2A: Quick Wins (Priority 1) - 1-2 days
Extract simple commands to build momentum and reduce main.py size:

1. **stats** (71 lines) - 1-2 hours
   - Simplest remaining command
   - Minimal dependencies
   - Good test case for Phase 2 integration pattern

2. **enrich** (155 lines) - 2-3 hours
   - Moderate complexity
   - PromptEnricher already well-encapsulated

### Phase 2B: Medium Complexity (Priority 2) - 2-3 days
3. **build-skill** (187 lines) - 2-3 hours
   - Template system is self-contained
   - Interactive prompts are isolated

4. **config** (237 lines) - 3-4 hours
   - Critical for user configuration
   - Well-defined boundaries
   - Interactive UI can be extracted

### Phase 2C: Command Groups (Priority 3) - 3-4 days
5. **repo** (310 lines) - 4-5 hours
   - Extract as command group module
   - Preserve Click group structure
   - 3 subcommands stay together

### Phase 2D: Critical Complex Commands (Priority 4) - 1 week
6. **setup** (271 lines) - 4-5 hours
   - Critical for onboarding
   - Heavy testing required
   - Integration with install command

7. **install** (885 lines) - 8-10 hours
   - Most complex command
   - Highest risk for regression
   - Extensive testing required
   - Consider breaking into sub-modules

### Phase 2E: Low Priority (Priority 5) - 2-3 days
8. **discover** (381 lines) - 5-6 hours
   - Rarely used command
   - Extract last to minimize risk

---

## Phase 2 Integration Work Required

For each extracted command, complete these steps:

### Integration Checklist (per command)
- [ ] Import command from `commands` module
- [ ] Register with CLI group: `cli.add_command(command_name)`
- [ ] Remove original implementation from main.py
- [ ] Update imports (move service imports to command file)
- [ ] Add shared utilities import (console, logger)
- [ ] Run tests to verify functionality
- [ ] Update documentation

### Example Integration Pattern

```python
# In main.py (top of file)
from mcp_skills.cli.commands.stats import stats
from mcp_skills.cli.commands.enrich import enrich

# Register commands
cli.add_command(stats)
cli.add_command(enrich)

# Remove original implementations (delete entire command functions)
```

### Shared Utilities Module Needed

**Recommendation:** Create `src/mcp_skills/cli/shared/` module:
- `console.py` - Shared Rich console instance
- `logger.py` - Shared logger configuration
- `utils.py` - Common CLI utilities

This prevents circular imports and provides consistent styling.

---

## Testing Strategy

### Per-Command Testing
1. **Unit Tests:** Test command logic in isolation
2. **Integration Tests:** Test CLI invocation with Click testing
3. **Regression Tests:** Compare output before/after extraction

### Full CLI Testing
After all extractions:
- [ ] Run full test suite: `uv run pytest tests/cli/`
- [ ] Manual smoke tests for all 18 commands
- [ ] Verify help text: `mcp-skillset --help`
- [ ] Test command aliases and shortcuts

---

## Risk Assessment

### Low Risk Commands (Extract First)
- stats, enrich, build-skill
- Well-isolated functionality
- Minimal service dependencies

### Medium Risk Commands
- config, repo, index, doctor, demo
- More complex but well-tested
- Careful integration required

### High Risk Commands (Extract Last)
- **setup** - Critical onboarding flow
- **install** - Multi-agent complexity
- **discover** - GitHub API integration

**Mitigation Strategy:**
1. Extract high-risk commands last
2. Create comprehensive test coverage before extraction
3. Test on multiple platforms (macOS, Linux, Windows)
4. Prepare rollback plan (git revert)

---

## File Size Reduction Estimate

### Current State
- **main.py:** 2,568 lines

### After Phase 2 Complete (All 9 remaining commands extracted)
- **Remaining in main.py:** ~1,071 lines (estimated)
  - Removed: stats (71), enrich (155), build-skill (187), config (237), setup (271), repo (310), discover (381), install (885) = **2,497 lines**
  - But: imports, shared code, CLI setup, etc. remain

### Projected main.py Contents (Post-Extraction)
- Imports and setup: ~50 lines
- CLI group definition: ~10 lines
- Command registrations: ~20 lines
- Shared utilities/helpers: ~100 lines (if not extracted)
- **Total:** ~180-200 lines

**Main.py Reduction:** 2,568 → ~200 lines (92% reduction)

---

## Dependencies to Watch

### Service Dependencies (Frequently Used)
- `SkillManager` - Used by most commands
- `IndexingEngine` - Used by index, search, recommend
- `RepositoryManager` - Used by repo, discover, setup
- `AgentInstaller` - Used by install, setup
- `ToolchainDetector` - Used by setup, recommend

### External Library Dependencies
- `click` - All commands
- `rich` (Console, Table, Panel, Progress) - All commands
- `pathlib.Path` - File operations
- `datetime` - Timestamps and stats

### Circular Import Risks
**CRITICAL:** Avoid circular imports between:
- `main.py` ↔ `commands/*`
- `commands/*` ↔ `services/*`

**Solution:** Use shared utilities module and lazy imports where necessary.

---

## Estimated Completion Timeline

### Phase 2A (Priority 1): 1-2 days
- Extract: stats, enrich
- Integrate: Remove from main.py, test
- **Deliverable:** 2 commands integrated, main.py reduced by ~226 lines

### Phase 2B (Priority 2): 2-3 days
- Extract: build-skill, config
- Integrate and test
- **Deliverable:** 4 commands integrated (total), main.py reduced by ~650 lines

### Phase 2C (Priority 3): 3-4 days
- Extract: repo (command group)
- Integrate and test subcommands
- **Deliverable:** 5 commands integrated (total), main.py reduced by ~960 lines

### Phase 2D (Priority 4): 1 week
- Extract: setup, install (most complex)
- Extensive testing required
- **Deliverable:** 7 commands integrated (total), main.py reduced by ~2,116 lines

### Phase 2E (Priority 5): 2-3 days
- Extract: discover
- Final integration and testing
- **Deliverable:** All 9 remaining commands integrated

### Final Testing & Cleanup: 2-3 days
- Full regression testing
- Documentation updates
- Code review and refinement

**Total Estimated Time:** 3-4 weeks (15-20 business days)

---

## Success Criteria

### Phase 2 Complete When:
- [ ] All 17 commands extracted to modular files (hybrid doesn't exist)
- [ ] All commands imported and registered in main.py
- [ ] Original implementations removed from main.py
- [ ] main.py reduced to ~200 lines (92% reduction)
- [ ] All tests passing
- [ ] No functional regressions
- [ ] Documentation updated
- [ ] Code review approved

### Quality Gates:
- [ ] Test coverage maintained above 85%
- [ ] No circular import issues
- [ ] Consistent error handling across commands
- [ ] Consistent Rich console styling
- [ ] All commands have docstrings and help text

---

## Next Steps

### Immediate Actions (Next Session)
1. **Create shared utilities module** (`src/mcp_skills/cli/shared/`)
   - Extract console, logger, common utilities
   - Prevent circular imports

2. **Integrate first extracted command** (e.g., `mcp`)
   - Import into main.py
   - Register with CLI group
   - Remove original implementation
   - Verify tests pass
   - **Document integration pattern** for remaining commands

3. **Extract stats command** (simplest remaining)
   - Follow established pattern
   - Immediate integration
   - Reduces main.py by 71 lines

### Documentation Needed
- [ ] Integration pattern guide (how to integrate extracted commands)
- [ ] Command extraction checklist
- [ ] Testing guide for extracted commands
- [ ] Shared utilities usage guide

---

## Commands Summary Table

| # | Command | Status | Lines | Complexity | Priority | Estimate |
|---|---------|--------|-------|------------|----------|----------|
| 1 | setup | ⏳ Remaining | 271 | Complex | CRITICAL | 4-5h |
| 2 | install | ⏳ Remaining | 885 | Very Complex | CRITICAL | 8-10h |
| 3 | config | ⏳ Remaining | 237 | Complex | HIGH | 3-4h |
| 4 | mcp | ✅ Extracted | 53 | Simple | - | - |
| 5 | search | ✅ Extracted | 111 | Medium | - | - |
| 6 | list | ✅ Extracted | 95 | Simple | - | - |
| 7 | info | ✅ Extracted | 129 | Medium | - | - |
| 8 | show | ✅ Extracted | (alias) | Simple | - | - |
| 9 | recommend | ✅ Extracted | 127 | Medium | - | - |
| 10 | demo | ✅ Extracted | 194 | Complex | - | - |
| 11 | discover | ⏳ Remaining | 381 | Complex | LOW | 5-6h |
| 12 | repo | ⏳ Remaining | 310 | Complex | MEDIUM | 4-5h |
| 13 | index | ✅ Extracted | 97 | Medium | - | - |
| 14 | hybrid | ❌ Non-existent | - | - | - | - |
| 15 | enrich | ⏳ Remaining | 155 | Medium | MEDIUM | 2-3h |
| 16 | build-skill | ⏳ Remaining | 187 | Medium | MEDIUM | 2-3h |
| 17 | doctor | ✅ Extracted | 149 | Medium | - | - |
| 18 | stats | ⏳ Remaining | 71 | Simple | HIGH | 1-2h |

**Totals:**
- Extracted: 8 commands (~955 lines)
- Remaining: 9 commands (~2,497 lines)
- Non-existent: 1 command (hybrid)

---

## Appendix: Command Groups

### Main CLI Group
- Primary entry point: `mcp-skillset`
- 17 top-level commands (18 planned - 1 non-existent)

### Repo Subgroup
- `repo add` - Add new repository
- `repo list` - List repositories
- `repo update` - Update repository

**Note:** When extracting `repo`, preserve Click group structure:

```python
# In commands/repo.py
@click.group(name="repo")
def repo():
    """Manage skill repositories."""
    pass

@repo.command("add")
def repo_add(...):
    ...

@repo.command("list")
def repo_list(...):
    ...

@repo.command("update")
def repo_update(...):
    ...
```

---

## Research Metadata

**Research Method:** Code analysis with grep, file inspection, git history review
**Tools Used:** Bash, Grep, Read, Git log analysis
**Files Analyzed:**
- `/Users/masa/Projects/mcp-skillset/src/mcp_skills/cli/main.py` (2,568 lines)
- `/Users/masa/Projects/mcp-skillset/src/mcp_skills/cli/commands/*.py` (8 files)
- Git commit history for ticket 1M-460

**Confidence Level:** High (based on direct code inspection and git history)

**Limitations:**
- Line count estimates are approximate (decorators, whitespace, comments vary)
- Integration time estimates assume no major blockers
- Test coverage time not included in per-command estimates
- Assumes existing test suite is comprehensive

**Recommendations Validated By:**
- Commit history showing successful extraction pattern
- File size analysis of extracted commands
- Complexity assessment based on dependencies and LOC
- Risk assessment based on user impact and critical path analysis
