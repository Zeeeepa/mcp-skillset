# CLI Refactoring Plan: Phase 1 Implementation

**Ticket**: 1M-460
**Date**: 2025-11-30
**Objective**: Refactor cli/main.py (2,568 lines) into modular command structure

## Current State Analysis

### File Statistics
- **Total Lines**: 2,568
- **Total Functions**: 29
- **CLI Commands**: 18
- **Average Lines per Command**: ~143

### All 18 CLI Commands

| # | Command | Function | Estimated Lines | Category |
|---|---------|----------|-----------------|----------|
| 1 | `setup` | `setup()` | ~270 | Setup & Config |
| 2 | `install` | `install()` | ~160 | Setup & Config |
| 3 | `config` | `config()` | ~200 | Setup & Config |
| 4 | `mcp` | `mcp()` | ~45 | MCP Server |
| 5 | `search` | `search()` | ~90 | Skill Discovery |
| 6 | `list` | `list()` | ~75 | Skill Discovery |
| 7 | `info` | `info()` | ~95 | Skill Discovery |
| 8 | `show` | `show()` | ~10 | Skill Discovery (alias) |
| 9 | `recommend` | `recommend()` | ~180 | Skill Discovery |
| 10 | `demo` | `demo()` | ~180 | Skill Discovery |
| 11 | `discover` | `discover()` | ~70 | Repository Mgmt |
| 12 | `repo` | `repo()` | ~50 | Repository Mgmt |
| 13 | `index` | `index()` | ~70 | Indexing |
| 14 | `hybrid` | `hybrid()` | ~165 | Indexing |
| 15 | `enrich` | `enrich()` | ~170 | Skill Building |
| 16 | `build-skill` | `build_skill()` | ~500 | Skill Building |
| 17 | `doctor` | `doctor()` | ~120 | Diagnostics |
| 18 | `stats` | `stats()` | ~280 | Diagnostics |

### Additional Functions (Not Commands)
- `cli()` - Main CLI group (entry point)
- `health()` - Deprecated alias for doctor
- `repo_add()`, `repo_list()`, `repo_update()` - Repo subcommands

## Target Structure

```
src/mcp_skills/cli/
├── __init__.py              # Package init
├── main.py                  # Entry point ONLY (~50 lines)
│                            # - Create CLI group
│                            # - Import and register commands
│                            # - Run CLI
│
├── commands/                # Command modules
│   ├── __init__.py
│   ├── setup.py            # setup command
│   ├── install.py          # install command
│   ├── config.py           # config command
│   ├── mcp_server.py       # mcp command
│   ├── search.py           # search command
│   ├── list_skills.py      # list command
│   ├── info.py             # info + show commands
│   ├── recommend.py        # recommend command
│   ├── demo.py             # demo command
│   ├── discover.py         # discover command
│   ├── repository.py       # repo + subcommands
│   ├── index.py            # index command
│   ├── hybrid.py           # hybrid command
│   ├── enrich.py           # enrich command
│   ├── build_skill.py      # build-skill command
│   ├── doctor.py           # doctor + health commands
│   └── stats.py            # stats command
│
└── shared/                  # Shared utilities
    ├── __init__.py
    ├── formatters.py       # Output formatting utilities
    ├── console.py          # Rich console singleton
    └── validators.py       # Input validation helpers
```

## Implementation Strategy

### Phase 1.1: Infrastructure Setup (30 mins)
1. Create directory structure
2. Create `__init__.py` files
3. Set up `shared/console.py` with singleton

### Phase 1.2: Extract Simple Commands First (2 hours)
Start with smallest, simplest commands to establish pattern:

**Batch 1 - Simple Commands** (~10-50 lines each):
1. `mcp_server.py` - mcp command (~45 lines)
2. `list_skills.py` - list command (~75 lines)
3. `info.py` - info + show (~105 lines combined)
4. `discover.py` - discover command (~70 lines)
5. `index.py` - index command (~70 lines)

### Phase 1.3: Medium Complexity Commands (3 hours)
**Batch 2 - Medium Commands** (~90-180 lines each):
6. `search.py` - search command (~90 lines)
7. `doctor.py` - doctor + health (~120 lines)
8. `recommend.py` - recommend command (~180 lines)
9. `demo.py` - demo command (~180 lines)
10. `hybrid.py` - hybrid command (~165 lines)
11. `enrich.py` - enrich command (~170 lines)

### Phase 1.4: Complex Commands (4 hours)
**Batch 3 - Complex Commands** (~160-500 lines each):
12. `install.py` - install command (~160 lines)
13. `config.py` - config command (~200 lines)
14. `setup.py` - setup command (~270 lines)
15. `stats.py` - stats command (~280 lines)
16. `build_skill.py` - build-skill command (~500 lines)
17. `repository.py` - repo + subcommands (~100 lines)

### Phase 1.5: Main Entry Point Refactor (1 hour)
18. Refactor `main.py` to import all commands
19. Keep only CLI group definition
20. Reduce to <100 lines

### Phase 1.6: Testing & Validation (2 hours)
21. Run full test suite
22. Manual CLI testing for each command
23. Fix any import or circular dependency issues

## Command Module Template

Each command module should follow this structure:

```python
"""Command: <name> - <brief description>."""

from __future__ import annotations

import click
from rich.console import Console

from mcp_skills.cli.shared.console import console
from mcp_skills.services.<service> import <Service>

# Any command-specific imports


@click.command()
@click.option(...)
@click.argument(...)
def <command_name>(...) -> None:
    """<Command description>.

    <Detailed usage information>

    Examples:
        mcp-skillset <command> <example>
    """
    # Command implementation
    pass


# Register with CLI in main.py:
# from mcp_skills.cli.commands.<module> import <command_name>
# cli.add_command(<command_name>)
```

## Shared Utilities

### shared/console.py
```python
"""Shared Rich console instance."""

from rich.console import Console

# Single console instance used by all commands
console = Console()
```

### shared/formatters.py
```python
"""Output formatting utilities for CLI commands."""

from rich.table import Table
from rich.tree import Tree
from rich.panel import Panel

def format_skill_table(skills: list) -> Table:
    """Format skills as Rich table."""
    pass

def format_config_panel(config: dict) -> Panel:
    """Format configuration as Rich panel."""
    pass

# ... other formatting functions
```

### shared/validators.py
```python
"""Input validation helpers for CLI commands."""

from pathlib import Path
import click

def validate_project_dir(path: str) -> Path:
    """Validate and return project directory path."""
    pass

def validate_skill_id(skill_id: str) -> str:
    """Validate skill ID format."""
    pass

# ... other validation functions
```

## Migration Checklist

### For Each Command Module:
- [ ] Create command file in `commands/`
- [ ] Copy command function from main.py
- [ ] Copy command-specific imports
- [ ] Update imports to use shared console
- [ ] Extract any reusable formatting to shared/
- [ ] Add docstring with examples
- [ ] Test command in isolation
- [ ] Import and register in main.py
- [ ] Verify integration test

### For main.py Refactor:
- [ ] Import all command modules
- [ ] Register all commands with `cli.add_command()`
- [ ] Remove old command definitions
- [ ] Keep only CLI group and entry point
- [ ] Verify file is <100 lines
- [ ] Run full test suite

## Testing Strategy

### Unit Testing
Each command module should be testable in isolation:

```python
# tests/cli/commands/test_search.py
from click.testing import CliRunner
from mcp_skills.cli.commands.search import search

def test_search_command():
    runner = CliRunner()
    result = runner.invoke(search, ["python testing"])
    assert result.exit_code == 0
    assert "Results" in result.output
```

### Integration Testing
Ensure main.py correctly wires all commands:

```python
# tests/cli/test_main.py
from click.testing import CliRunner
from mcp_skills.cli.main import cli

def test_all_commands_registered():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert "setup" in result.output
    assert "search" in result.output
    # ... all 18 commands
```

## Risk Mitigation

### Potential Issues:
1. **Circular imports** - Services importing from CLI
   - Solution: Ensure one-way dependency (CLI → Services)

2. **Shared state** - Multiple commands using same console
   - Solution: Use singleton pattern in shared/console.py

3. **Test breakage** - Existing tests import from main.py
   - Solution: Update test imports to new command modules

4. **Click context** - Commands sharing Click context
   - Solution: Properly pass context via @click.pass_context where needed

### Rollback Plan:
- Keep original main.py as main.py.backup
- Each batch committed separately
- Can rollback per-batch if issues arise

## Success Metrics

### Code Quality:
- ✅ No file >500 lines
- ✅ Each command module <200 lines (except build-skill <500)
- ✅ main.py <100 lines
- ✅ All commands testable in isolation

### Functionality:
- ✅ All 18 commands working identically
- ✅ No breaking changes to CLI interface
- ✅ All existing tests pass
- ✅ No performance degradation

### Maintainability:
- ✅ Clear command ownership (one file = one command)
- ✅ Easy to add new commands (<100 lines each)
- ✅ Reusable utilities extracted
- ✅ Improved test coverage

## Timeline Estimate

| Phase | Duration | Cumulative |
|-------|----------|------------|
| 1.1: Infrastructure | 30 mins | 0.5h |
| 1.2: Simple Commands (5) | 2 hours | 2.5h |
| 1.3: Medium Commands (6) | 3 hours | 5.5h |
| 1.4: Complex Commands (6) | 4 hours | 9.5h |
| 1.5: Main Refactor | 1 hour | 10.5h |
| 1.6: Testing | 2 hours | 12.5h |
| **Total** | **12.5 hours** | **~2 days** |

## Dependencies

**Before Starting:**
- ✅ Architecture review completed
- ✅ Linear ticket created (1M-460)
- ✅ All tests currently passing

**During Implementation:**
- Frequent commits (per batch)
- Incremental testing
- Documentation updates

**After Completion:**
- Update 1M-460 ticket status
- Document new command module pattern
- Create PR for review

## Next Steps

1. ✅ Create this implementation plan
2. Create infrastructure (directories, shared utils)
3. Start with Batch 1 (simple commands)
4. Proceed through Batches 2-3
5. Refactor main.py
6. Test and validate
7. Update Linear ticket

---

**Status**: Ready to implement
**Estimated Completion**: 2 days (12.5 hours)
**Risk Level**: Medium (mitigated with incremental approach)
