# Architecture Review: DI/SOA Best Practices Analysis

**Date:** 2025-11-30
**Reviewer:** Claude (Architecture Analysis)
**Scope:** mcp-skillset codebase
**Focus:** Dependency Injection, Service-Oriented Architecture, God Files

## Executive Summary

### Critical Issues Found
1. **God File:** `cli/main.py` (2,568 lines, 18 commands)
2. **Large Services:** Multiple services >500 lines
3. **Tight Coupling:** Direct instantiation in CLI commands
4. **Missing DI Framework:** No dependency injection container
5. **Inconsistent Service Patterns:** Mixed responsibility patterns

### Recommendations Priority
- 🔴 **Critical:** Refactor `cli/main.py` into command modules
- 🟡 **High:** Implement DI container
- 🟡 **High:** Extract service interfaces
- 🟢 **Medium:** Standardize service patterns
- 🟢 **Medium:** Add service layer tests

## File Size Analysis

### God Files (>500 lines)

| File | Lines | Issue | Recommendation |
|------|-------|-------|----------------|
| `cli/main.py` | 2,568 | 🔴 God file with 18 commands | Split into command modules |
| `mcp/tools/skill_tools.py` | 753 | 🟡 All MCP tools in one file | Extract tool classes |
| `services/skill_manager.py` | 741 | 🟡 Too many responsibilities | Split search, indexing, management |
| `services/toolchain_detector.py` | 671 | 🟡 Detection logic for all languages | Extract language detectors |
| `services/agent_installer.py` | 656 | 🟡 Mixed JSON + CLI installation | Separate installer strategies |
| `cli/config_menu.py` | 638 | 🟡 All config UI in one file | Extract menu components |

### Well-Sized Files (< 400 lines) ✅
- `services/indexing/vector_store.py` (349 lines)
- `services/indexing/graph_store.py` (356 lines)
- `models/config.py` (372 lines)
- `services/agent_detector.py` (229 lines)

## DI/SOA Violations

### 1. God File: `cli/main.py` (2,568 lines)

**Problem:**
- 18 CLI commands in single file
- ~143 lines per command average
- Violates Single Responsibility Principle
- Difficult to test, maintain, modify

**Code Example:**
```python
# cli/main.py has ALL commands:
@cli.command()
def setup(...): pass  # 150+ lines

@cli.command()
def install(...): pass  # 100+ lines

@cli.command()
def search(...): pass  # 80+ lines

# ... 15 more commands
```

**Recommendation:**
```
cli/
├── main.py              # Entry point only (~50 lines)
├── commands/
│   ├── __init__.py
│   ├── setup.py         # setup command
│   ├── install.py       # install command
│   ├── search.py        # search command
│   ├── discover.py      # discover command
│   └── ...
└── shared/
    ├── formatters.py    # Output formatting
    └── validators.py    # Input validation
```

**Benefits:**
- Each command file <150 lines
- Easier to test in isolation
- Clearer command ownership
- Simpler code review
- Parallel development possible

### 2. No Dependency Injection Container

**Problem:**
Services are directly instantiated in commands:

```python
# cli/main.py
@cli.command()
def search(query: str):
    # Direct instantiation - hard to test, tightly coupled
    config = MCPSkillsConfig.load(config_path)
    skill_manager = SkillManager(config.skills_dir)
    engine = IndexingEngine(config.skills_dir)
    results = engine.search(query)
    # ...
```

**Issues:**
- Hard to test (can't mock dependencies)
- Tight coupling (command knows service implementation)
- Duplicated initialization code across commands
- No lifecycle management
- Difficult to swap implementations

**Recommended Pattern:**

```python
# services/container.py
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    config = providers.Singleton(MCPSkillsConfig.load)

    skill_manager = providers.Singleton(
        SkillManager,
        skills_dir=config.provided.skills_dir
    )

    indexing_engine = providers.Singleton(
        IndexingEngine,
        skills_dir=config.provided.skills_dir
    )

# cli/commands/search.py
@cli.command()
@inject
def search(
    query: str,
    engine: IndexingEngine = Depends(Provide[Container.indexing_engine])
):
    results = engine.search(query)
    # ...
```

**Benefits:**
- Easy testing (inject mocks)
- Loose coupling (depend on interfaces)
- Centralized configuration
- Automatic lifecycle management
- Clear dependency graph

### 3. Missing Service Interfaces

**Problem:**
Services are concrete classes, not abstractions:

```python
# Clients depend directly on implementations
class IndexingEngine:
    def search(self, query): ...

# No interface/protocol defined
# Can't easily swap implementations
# Testing requires real dependencies
```

**Recommended Pattern:**

```python
# services/interfaces/search_engine.py
from typing import Protocol, List
from models.skill import Skill

class ISearchEngine(Protocol):
    """Search engine interface for skill discovery."""

    def search(self, query: str, limit: int = 10) -> List[Skill]:
        """Search for skills matching query."""
        ...

    def reindex(self) -> None:
        """Rebuild search index."""
        ...

# services/indexing/engine.py
class IndexingEngine:  # Implements ISearchEngine implicitly
    def search(self, query: str, limit: int = 10) -> List[Skill]:
        return self._hybrid_search.search(query, limit)

    def reindex(self) -> None:
        self._rebuild_indices()

# In DI container
class Container:
    search_engine: ISearchEngine = providers.Singleton(
        IndexingEngine,  # Can swap with different implementation
        skills_dir=config.provided.skills_dir
    )
```

**Benefits:**
- Easy to mock for testing
- Can swap implementations
- Clear contracts between layers
- Supports multiple implementations
- Better documentation

### 4. Skill Manager God Class (741 lines)

**Problem:**
`SkillManager` has too many responsibilities:

```python
class SkillManager:
    # Discovery responsibilities
    def discover_skills(self, repo_path): ...
    def scan_directory(self, path): ...

    # Loading responsibilities
    def load_skill(self, skill_path): ...
    def load_all_skills(self): ...

    # Search responsibilities
    def search_skills(self, query): ...
    def filter_by_tags(self, tags): ...

    # Metadata responsibilities
    def get_metadata(self, skill_id): ...
    def update_metadata(self, skill_id, data): ...
```

**Recommended Split:**

```python
# services/skill_discovery.py (~200 lines)
class SkillDiscoveryService:
    """Discovers skills from repositories."""
    def discover_skills(self, repo_path): ...
    def scan_directory(self, path): ...

# services/skill_loader.py (~150 lines)
class SkillLoaderService:
    """Loads and validates skill files."""
    def load_skill(self, skill_path): ...
    def load_all_skills(self): ...

# services/skill_search.py (~200 lines)
class SkillSearchService:
    """Searches and filters skills."""
    def search(self, query): ...
    def filter_by_tags(self, tags): ...

# services/skill_metadata.py (~150 lines)
class SkillMetadataService:
    """Manages skill metadata."""
    def get(self, skill_id): ...
    def update(self, skill_id, data): ...
```

**Benefits:**
- Single Responsibility Principle
- Easier testing (smaller surface area)
- Clearer purpose for each service
- Can evolve independently
- Simpler to understand

### 5. Toolchain Detector Anti-Pattern (671 lines)

**Problem:**
All language detection in one class:

```python
class ToolchainDetector:
    def _detect_python(self, path): ...      # 50 lines
    def _detect_javascript(self, path): ...  # 50 lines
    def _detect_rust(self, path): ...        # 50 lines
    def _detect_go(self, path): ...          # 50 lines
    # ... 8 more languages
```

**Recommended Pattern:**

```python
# services/detectors/base.py
class LanguageDetector(Protocol):
    """Interface for language detection."""

    @property
    def language_name(self) -> str: ...

    def can_detect(self, path: Path) -> bool: ...

    def detect(self, path: Path) -> Optional[LanguageInfo]: ...

# services/detectors/python_detector.py (~80 lines)
class PythonDetector:
    language_name = "Python"

    def can_detect(self, path: Path) -> bool:
        return (path / "requirements.txt").exists() or \
               (path / "pyproject.toml").exists()

    def detect(self, path: Path) -> Optional[LanguageInfo]:
        # Python-specific detection logic
        ...

# services/detectors/javascript_detector.py (~80 lines)
class JavaScriptDetector:
    # JavaScript-specific logic
    ...

# services/toolchain_detector.py (~100 lines)
class ToolchainDetector:
    """Orchestrates language detectors."""

    def __init__(self, detectors: List[LanguageDetector]):
        self.detectors = detectors

    def detect(self, path: Path) -> ToolchainInfo:
        for detector in self.detectors:
            if detector.can_detect(path):
                lang_info = detector.detect(path)
                if lang_info:
                    return self._build_toolchain_info(lang_info)
        return ToolchainInfo()
```

**Benefits:**
- Each detector <100 lines
- Easy to add new languages
- Can test detectors independently
- Plugin architecture for detectors
- Open/Closed Principle

### 6. Agent Installer Mixed Concerns (656 lines)

**Problem:**
Handles both JSON config files AND CLI-based installation:

```python
class AgentInstaller:
    def install(self, agent, force, dry_run):
        if agent.id == "claude-code":
            return self._install_via_claude_cli(agent, force, dry_run)
        else:
            return self._install_via_json_config(agent, force, dry_run)

    def _install_via_json_config(self, ...):  # 100 lines
        # JSON manipulation logic
        ...

    def _install_via_claude_cli(self, ...):   # 80 lines
        # Subprocess/CLI logic
        ...
```

**Recommended Pattern:**

```python
# services/installers/base.py
class IAgentInstaller(Protocol):
    """Interface for agent installation strategies."""

    def can_install(self, agent: DetectedAgent) -> bool: ...

    def install(
        self,
        agent: DetectedAgent,
        force: bool = False,
        dry_run: bool = False
    ) -> InstallResult: ...

# services/installers/json_installer.py (~200 lines)
class JsonConfigInstaller:
    """Installs via JSON config file manipulation."""

    def can_install(self, agent: DetectedAgent) -> bool:
        return agent.config_type == "json"

    def install(self, agent, force, dry_run) -> InstallResult:
        # JSON-only logic
        ...

# services/installers/cli_installer.py (~150 lines)
class CliInstaller:
    """Installs via agent CLI tools."""

    def can_install(self, agent: DetectedAgent) -> bool:
        return agent.has_cli and shutil.which(agent.cli_command)

    def install(self, agent, force, dry_run) -> InstallResult:
        # CLI-only logic
        ...

# services/agent_installer.py (~100 lines)
class AgentInstaller:
    """Orchestrates installation strategies."""

    def __init__(self, installers: List[IAgentInstaller]):
        self.installers = installers

    def install(self, agent, force=False, dry_run=False) -> InstallResult:
        for installer in self.installers:
            if installer.can_install(agent):
                return installer.install(agent, force, dry_run)
        return InstallResult(success=False, error="No installer available")
```

**Benefits:**
- Strategy Pattern (clean)
- Each installer <200 lines
- Easy to add new installation methods
- Testable in isolation
- Clearer separation of concerns

## Metrics Summary

### Current State

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Largest file | 2,568 lines | <500 lines | 🔴 Fail |
| Files >500 lines | 6 | 0 | 🔴 Fail |
| DI container | None | Yes | 🔴 Missing |
| Service interfaces | 0 | All public services | 🔴 Missing |
| God classes | 3 | 0 | 🔴 Fail |
| Avg service size | ~450 lines | <300 lines | 🟡 High |
| Test coverage | 20% | >85% | 🔴 Low |

### Target State

| Metric | Current | Target | Priority |
|--------|---------|--------|----------|
| Largest file | 2,568 | <500 | 🔴 Critical |
| Files >500 lines | 6 | 0 | 🔴 Critical |
| DI container | No | Yes | 🟡 High |
| Service interfaces | No | Yes | 🟡 High |
| Command modules | 1 | 18 | 🔴 Critical |
| Avg service size | 450 | <250 | 🟢 Medium |
| Test coverage | 20% | >85% | 🟡 High |

## Recommended Actions

### Phase 1: Critical Refactoring (v0.8.0)
1. **Split `cli/main.py` into command modules**
   - Effort: 2-3 days
   - Risk: Medium (extensive CLI changes)
   - Impact: High (better maintainability)
   - Tickets: See Linear issues below

2. **Extract CLI installers (Strategy Pattern)**
   - Effort: 1 day
   - Risk: Low (well-defined interface)
   - Impact: Medium (cleaner code)

3. **Split SkillManager into focused services**
   - Effort: 2 days
   - Risk: Medium (many dependencies)
   - Impact: High (better testability)

### Phase 2: DI Implementation (v0.9.0)
1. **Add dependency-injector framework**
   - Effort: 1 day
   - Risk: Low (additive change)
   - Impact: High (better testing)

2. **Create service interfaces (Protocols)**
   - Effort: 2 days
   - Risk: Low (gradual migration)
   - Impact: High (clearer contracts)

3. **Migrate commands to use DI**
   - Effort: 3 days
   - Risk: Medium (touches all commands)
   - Impact: High (much easier testing)

### Phase 3: Service Modernization (v1.0.0)
1. **Extract language detectors (Plugin Pattern)**
   - Effort: 2 days
   - Risk: Low (additive)
   - Impact: Medium (extensibility)

2. **Standardize service patterns**
   - Effort: 3 days
   - Risk: Low (internal refactoring)
   - Impact: Medium (consistency)

3. **Add comprehensive service tests**
   - Effort: 4 days
   - Risk: Low (pure testing)
   - Impact: High (coverage >85%)

## Linear Tickets to Create

### Critical (v0.8.0)
- [ ] **1M-XXX:** Refactor CLI main.py into command modules (god file)
- [ ] **1M-XXX:** Extract agent installer strategies (JsonConfigInstaller, CliInstaller)
- [ ] **1M-XXX:** Split SkillManager into focused services (Discovery, Loader, Search, Metadata)

### High Priority (v0.9.0)
- [ ] **1M-XXX:** Add dependency-injector framework for service management
- [ ] **1M-XXX:** Create service interface protocols (ISearchEngine, ISkillLoader, etc.)
- [ ] **1M-XXX:** Migrate CLI commands to use dependency injection

### Medium Priority (v1.0.0)
- [ ] **1M-XXX:** Extract toolchain language detectors into plugins
- [ ] **1M-XXX:** Refactor skill_tools.py into individual tool classes
- [ ] **1M-XXX:** Standardize service layer patterns and naming conventions
- [ ] **1M-XXX:** Add comprehensive service layer tests (target 85% coverage)

## Success Criteria

### Code Quality Metrics
- ✅ No files >500 lines
- ✅ All services <300 lines average
- ✅ DI container in use
- ✅ Service interfaces defined
- ✅ Test coverage >85%

### Architectural Metrics
- ✅ CLI commands separated into modules
- ✅ Strategy pattern for installers
- ✅ Plugin pattern for language detectors
- ✅ Single Responsibility Principle followed
- ✅ Dependency Inversion Principle applied

### Maintainability Metrics
- ✅ New commands added in <100 lines
- ✅ New language detection in <80 lines
- ✅ Services testable in isolation
- ✅ Clear separation of concerns
- ✅ Documented dependency graph

## Conclusion

The codebase has solid foundations but suffers from several architectural anti-patterns:

**Strengths:**
- ✅ Good service layer separation
- ✅ Clear models and data structures
- ✅ Comprehensive functionality
- ✅ Well-documented code

**Weaknesses:**
- 🔴 God file (cli/main.py at 2,568 lines)
- 🔴 No dependency injection
- 🔴 Missing service interfaces
- 🔴 Several oversized services (>500 lines)
- 🔴 Low test coverage (20%)

**Priority:**
Focus on Phase 1 (Critical Refactoring) first:
1. Split cli/main.py
2. Extract installer strategies
3. Decompose SkillManager

This will provide immediate maintainability benefits and set the stage for DI implementation in Phase 2.
