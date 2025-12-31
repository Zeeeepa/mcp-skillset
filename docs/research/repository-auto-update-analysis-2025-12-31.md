# Repository Auto-Update Analysis

**Date:** 2025-12-31
**Research Focus:** Current repository update mechanisms and auto-update implementation strategy
**Project:** mcp-skillset

## Executive Summary

The mcp-skillset codebase has a **well-designed manual update workflow** through `mcp-skillset repo update` but **no automatic update mechanism**. The infrastructure for auto-update is **partially in place** through the `RepositoryConfig.auto_update` field in configuration, but it's not currently used by any code. This research identifies the current update flow, key methods for auto-update implementation, and provides a roadmap for adding automatic repository updates.

**Key Findings:**
1. ✅ Manual update workflow is robust and production-ready
2. ✅ Configuration schema already includes `auto_update` field
3. ❌ No code currently checks or uses the `auto_update` flag
4. ❌ No scheduled/background task mechanism exists
5. ✅ All building blocks exist for auto-update implementation

## Current Manual Update Workflow

### CLI Command: `mcp-skillset repo update`

**File:** `src/mcp_skills/cli/commands/repo.py`

**Usage:**
```bash
# Update specific repository
mcp-skillset repo update <repo_id>

# Update all repositories
mcp-skillset repo update
```

**Implementation Flow:**

#### Single Repository Update (lines 156-180)
```python
def repo_update(repo_id: str | None) -> None:
    repo_manager = RepositoryManager()

    if repo_id:
        # Update single repository
        with Progress() as progress:
            task = progress.add_task("Pulling latest changes...", total=None)
            repo = repo_manager.update_repository(repo_id)

            # Display results
            console.print("✓ Repository updated successfully")
            console.print(f"  • ID: {repo.id}")
            console.print(f"  • Skills: {repo.skill_count}")
```

#### Bulk Repository Update (lines 183-265)
```python
def repo_update(repo_id: str | None) -> None:
    else:
        # Update all repositories
        repos = repo_manager.list_repositories()

        with Progress() as progress:
            for repo in repos:
                task = progress.add_task(f"Updating {repo.id}", total=100)

                old_skill_count = repo.skill_count
                updated_repo = repo_manager.update_repository_with_progress(
                    repo.id,
                    progress_callback=make_callback(task)
                )

                skill_diff = updated_repo.skill_count - old_skill_count
                # Report skill changes

        # Suggest reindexing
        console.print("Tip: Run 'mcp-skillset index' to reindex updated skills")
```

### Repository Manager Update Methods

**File:** `src/mcp_skills/services/repository_manager.py`

#### `update_repository(repo_id: str)` (lines 292-350)

**Purpose:** Pull latest changes from repository (no progress tracking)

**Implementation:**
```python
def update_repository(self, repo_id: str) -> Repository:
    # 1. Find repository by ID
    repository = self.get_repository(repo_id)
    if not repository:
        raise ValueError(f"Repository not found: {repo_id}")

    # 2. Git fetch and reset to origin (read-only repos)
    repo = git.Repo(repository.local_path)
    origin = repo.remotes.origin
    origin.fetch()
    default_branch = repo.active_branch.name
    repo.head.reset(f"origin/{default_branch}", index=True, working_tree=True)

    # 3. Rescan for new/updated skills
    skill_count = self._count_skills(repository.local_path)

    # 4. Update metadata
    repository.last_updated = datetime.now(UTC)
    repository.skill_count = skill_count

    # 5. Save updated metadata to SQLite
    self.metadata_store.update_repository(repository)

    return repository
```

**Error Handling:**
- `ValueError`: Repository not found
- `GitCommandError`: Pull operation failed (network, conflicts)
- `InvalidGitRepositoryError`: Local clone is corrupted

**Recovery Strategy:**
- Skill repos are read-only, so we **fetch and hard reset** to origin
- This handles local changes and divergent branches automatically
- If local repository is corrupted, re-clone is recommended

#### `update_repository_with_progress()` (lines 352-419)

**Purpose:** Same as `update_repository()` but with progress tracking for UI

**Additional Features:**
- Accepts `progress_callback: Callable[[int, int, str], None]`
- Uses `CloneProgress` handler to translate GitPython progress to callback
- Enables rich progress bars in CLI

### Git Operation Details

**File:** `src/mcp_skills/services/repository_manager.py` (lines 30-62)

**CloneProgress Handler:**
```python
class CloneProgress(RemoteProgress):
    """GitPython progress handler for repository cloning and updates.

    Translates GitPython's RemoteProgress callbacks into simpler callback
    interface suitable for CLI progress bars.
    """

    def __init__(self, callback: Callable[[int, int, str], None]) -> None:
        super().__init__()
        self.callback = callback

    def update(self, _op_code: int, cur_count: int | float,
               max_count: int | float | None = None, message: str = "") -> None:
        if max_count and self.callback:
            self.callback(int(cur_count), int(max_count), message or "")
```

**Update Strategy:**
- Uses GitPython library for git operations
- Fetches latest changes from origin
- Hard resets to `origin/<default_branch>` (discards local changes)
- Skill repositories are read-only, so hard reset is safe

## Indexing Trigger Mechanism

### CLI Command: `mcp-skillset index`

**File:** `src/mcp_skills/cli/commands/index.py`

**Usage:**
```bash
# Default: incremental indexing
mcp-skillset index

# Force full reindex
mcp-skillset index --force

# Explicit incremental
mcp-skillset index --incremental
```

**Implementation:**
```python
def index(incremental: bool, force: bool) -> None:
    skill_manager = SkillManager()
    indexing_engine = IndexingEngine(skill_manager=skill_manager)

    with Progress() as progress:
        task = progress.add_task("Building indices...", total=None)

        # Reindex (force=True clears existing indices first)
        stats = indexing_engine.reindex_all(force=force)

        # Display statistics
        console.print("✓ Indexing complete")
        console.print(f"Skills Indexed: {stats.total_skills}")
        console.print(f"Graph Nodes: {stats.graph_nodes}")
        console.print(f"Graph Edges: {stats.graph_edges}")
```

### IndexingEngine.reindex_all()

**File:** `src/mcp_skills/services/indexing/engine.py` (lines 262-332)

**Purpose:** Rebuild vector + knowledge graph indices from scratch

**Implementation Flow:**
```python
def reindex_all(self, force: bool = False) -> IndexStats:
    # 1. Clear existing indices if forced
    if force:
        self.vector_store.clear()
        self.graph_store.clear()

    # 2. Discover all skills
    skills = self.skill_manager.discover_skills()

    # 3. Index each skill (embeddings + graph)
    for skill in skills:
        try:
            self.index_skill(skill)
            indexed_count += 1
        except Exception as e:
            failed_count += 1

    # 4. Update last indexed timestamp
    self._last_indexed = datetime.now()

    # 5. Save graph to disk for persistence
    if self.graph_store.save(self._graph_path):
        logger.info(f"Knowledge graph saved to {self._graph_path}")

    # 6. Return statistics
    return self.get_stats()
```

**Performance:**
- Time Complexity: O(n × m) where n = skills, m = avg text length
- Expected: ~2-5 seconds for 100 skills on CPU
- Uses batch processing for efficiency

## Configuration Schema

### RepositoryConfig.auto_update Field

**File:** `src/mcp_skills/models/config.py` (lines 216-228)

**Current Definition:**
```python
class RepositoryConfig(BaseSettings):
    """Repository configuration.

    Attributes:
        url: Git repository URL
        priority: Repository priority (0-100)
        auto_update: Automatically update on startup  # ⚠️ Not used yet
    """

    url: str = Field(..., description="Git repository URL")
    priority: int = Field(50, description="Repository priority", ge=0, le=100)
    auto_update: bool = Field(True, description="Auto-update on startup")
```

**Status:**
- ✅ Field exists in schema
- ❌ **No code currently checks this field**
- ❌ **No startup hook uses this configuration**

### MCPSkillsConfig

**File:** `src/mcp_skills/models/config.py` (lines 256-404)

**Relevant Fields:**
```python
class MCPSkillsConfig(BaseSettings):
    # Repositories
    repositories: list[RepositoryConfig] = Field(
        default_factory=list,
        description="Configured repositories"
    )

    # Other relevant config
    toolchain_cache_duration: int = Field(
        3600,
        description="Toolchain cache duration (seconds)",
        ge=0
    )
```

**Configuration Sources:**
1. Environment variables (MCP_SKILLS_*)
2. Config file (~/.mcp-skillset/config.yaml)
3. Defaults

## Metadata Storage

### MetadataStore (SQLite)

**File:** `src/mcp_skills/services/metadata_store.py`

**Purpose:** SQLite-based metadata storage for repositories and skills

**Key Tables:**
- `repositories` - Repository metadata (id, url, local_path, priority, last_updated, skill_count)
- Skills metadata (future enhancement)

**Performance:**
- O(1) indexed lookups via primary key
- Transaction safety with automatic backups
- Foreign keys with CASCADE deletes

**Migration:**
- Auto-migrates from JSON to SQLite on first use
- JSON backed up as `repos.json.backup` after migration

## Auto-Update Implementation Gaps

### Current State Analysis

#### ✅ What Exists
1. **Manual update command:** `mcp-skillset repo update`
2. **Update methods:** `RepositoryManager.update_repository()` and `update_repository_with_progress()`
3. **Configuration field:** `RepositoryConfig.auto_update`
4. **Progress tracking:** Rich progress bars for updates
5. **Error handling:** Robust error recovery with GitCommandError handling
6. **Metadata storage:** SQLite persistence for repository state

#### ❌ What's Missing
1. **Auto-update check logic:** No code checks `auto_update` field
2. **Startup hook:** No mechanism to trigger updates on startup
3. **Background scheduler:** No periodic update mechanism
4. **Update strategy:** No decision on when/how to auto-update
5. **Failure recovery:** No retry logic for failed auto-updates
6. **User notification:** No way to inform user of auto-updates

## Auto-Update Implementation Roadmap

### Option 1: Startup Update (Recommended for MCP Server)

**When:** On MCP server startup (first connection)

**Trigger Point:** `src/mcp_skills/mcp/server.py`

**Implementation:**
```python
async def main():
    """MCP server entry point with auto-update."""

    # 1. Load configuration
    config = MCPSkillsConfig()

    # 2. Check for auto-update enabled repositories
    if any(repo.auto_update for repo in config.repositories):
        logger.info("Auto-update enabled, checking for updates...")

        repo_manager = RepositoryManager()

        for repo_config in config.repositories:
            if not repo_config.auto_update:
                continue

            try:
                # Check if repository needs update (e.g., daily check)
                repo = repo_manager.get_repository(repo_config.url)
                if repo and should_update(repo):
                    logger.info(f"Auto-updating {repo.id}...")
                    repo_manager.update_repository(repo.id)
            except Exception as e:
                logger.warning(f"Auto-update failed for {repo.id}: {e}")
                # Continue with other repos

    # 3. Start MCP server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(...)
```

**Helper Function:**
```python
def should_update(repo: Repository, max_age_hours: int = 24) -> bool:
    """Check if repository should be auto-updated.

    Args:
        repo: Repository to check
        max_age_hours: Maximum age before update (default: 24 hours)

    Returns:
        True if update is needed
    """
    age = datetime.now(UTC) - repo.last_updated
    return age.total_seconds() > (max_age_hours * 3600)
```

**Pros:**
- Simple implementation (single function call)
- Updates happen when server starts (predictable timing)
- No additional dependencies required
- User doesn't need to remember to update

**Cons:**
- Updates only when server restarts
- Might delay server startup slightly
- No updates for long-running sessions

### Option 2: Background Scheduler (Advanced)

**When:** Periodic updates every N hours

**Library:** APScheduler or similar

**Implementation:**
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

async def auto_update_task():
    """Background task to auto-update repositories."""
    config = MCPSkillsConfig()
    repo_manager = RepositoryManager()

    for repo_config in config.repositories:
        if not repo_config.auto_update:
            continue

        try:
            repo = repo_manager.get_repository(repo_config.url)
            if repo:
                logger.info(f"Auto-updating {repo.id}...")
                repo_manager.update_repository(repo.id)
        except Exception as e:
            logger.error(f"Auto-update failed for {repo.id}: {e}")

async def main():
    """MCP server with background auto-update."""

    # Start background scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        auto_update_task,
        'interval',
        hours=24,
        id='repo_auto_update'
    )
    scheduler.start()

    # Start MCP server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(...)
```

**Pros:**
- Regular updates without restart
- Configurable update frequency
- Can run during idle periods

**Cons:**
- Adds dependency (APScheduler)
- More complex implementation
- Background tasks in stdio server need careful handling

### Option 3: CLI Command with Cron (User-Managed)

**When:** User sets up cron job

**Implementation:**
```bash
# User adds to crontab
0 */6 * * * mcp-skillset repo update --quiet
```

**Add `--quiet` flag to `repo update`:**
```python
@repo.command("update")
@click.argument("repo_id", required=False)
@click.option("--quiet", is_flag=True, help="Suppress output")
def repo_update(repo_id: str | None, quiet: bool) -> None:
    """Update repositories (pull latest changes)."""

    if quiet:
        # Disable console output
        console = Console(file=io.StringIO())

    # ... existing update logic ...
```

**Pros:**
- No code changes to auto-update logic
- User has full control over timing
- Works with existing update command

**Cons:**
- Requires user to set up cron
- Not automatic out-of-the-box
- Platform-dependent (cron vs Windows Task Scheduler)

## Recommended Implementation Strategy

### Phase 1: Add Auto-Update Check on Startup (Minimal Changes)

**Location:** `src/mcp_skills/mcp/server.py`

**Changes:**
1. Add `check_auto_updates()` function
2. Call it at server startup before creating server instance
3. Respect `auto_update` config field per repository

**Code:**
```python
def check_auto_updates(max_age_hours: int = 24) -> None:
    """Check and perform auto-updates for configured repositories.

    Args:
        max_age_hours: Maximum age before triggering update (default: 24 hours)
    """
    try:
        config = MCPSkillsConfig()
        repo_manager = RepositoryManager()

        auto_update_repos = [r for r in config.repositories if r.auto_update]

        if not auto_update_repos:
            return

        logger.info(f"Checking {len(auto_update_repos)} repositories for auto-update")

        for repo_config in auto_update_repos:
            try:
                # Extract repo ID from URL
                repo_id = repo_manager._generate_repo_id(repo_config.url)
                repo = repo_manager.get_repository(repo_id)

                if not repo:
                    logger.warning(f"Repository not found: {repo_id}")
                    continue

                # Check if update is needed
                age = datetime.now(UTC) - repo.last_updated
                age_hours = age.total_seconds() / 3600

                if age_hours < max_age_hours:
                    logger.debug(f"Skipping {repo.id} (last updated {age_hours:.1f}h ago)")
                    continue

                # Perform update
                logger.info(f"Auto-updating {repo.id} ({age_hours:.1f}h old)")
                updated_repo = repo_manager.update_repository(repo.id)

                skill_diff = updated_repo.skill_count - repo.skill_count
                if skill_diff != 0:
                    logger.info(f"Repository {repo.id}: {skill_diff:+d} skills")

            except Exception as e:
                # Log but don't fail startup
                logger.warning(f"Auto-update failed for {repo_config.url}: {e}")

    except Exception as e:
        # Don't fail server startup on auto-update errors
        logger.error(f"Auto-update check failed: {e}")

async def main():
    """MCP server entry point."""

    # Check for auto-updates before starting server
    check_auto_updates()

    # Create and run server
    server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(...)
```

### Phase 2: Add Auto-Reindex After Updates (Follow-up)

**Enhancement:** Automatically reindex if skills changed

**Implementation:**
```python
def check_auto_updates(max_age_hours: int = 24) -> None:
    """Check and perform auto-updates with reindexing."""

    # ... existing update logic ...

    total_skill_changes = 0

    for repo_config in auto_update_repos:
        # ... update repository ...

        skill_diff = updated_repo.skill_count - repo.skill_count
        total_skill_changes += abs(skill_diff)

    # Auto-reindex if skills changed
    if total_skill_changes > 0:
        logger.info(f"Skills changed ({total_skill_changes:+d}), triggering reindex")
        try:
            skill_manager = SkillManager()
            indexing_engine = IndexingEngine(skill_manager=skill_manager)
            stats = indexing_engine.reindex_all(force=False)  # Incremental
            logger.info(f"Reindexing complete: {stats.total_skills} skills")
        except Exception as e:
            logger.error(f"Auto-reindex failed: {e}")
```

### Phase 3: Add User Configuration (Future)

**Configuration Options:**
```yaml
# ~/.mcp-skillset/config.yaml
repositories:
  - url: https://github.com/anthropics/skills.git
    priority: 100
    auto_update: true  # Enable auto-update

  - url: https://github.com/obra/superpowers.git
    priority: 90
    auto_update: false  # Disable auto-update

# Auto-update settings
auto_update:
  enabled: true
  max_age_hours: 24
  reindex_on_change: true
```

## Key Methods and Classes Summary

### Repository Update Methods

| Method | File | Purpose | Progress Tracking |
|--------|------|---------|-------------------|
| `update_repository()` | `repository_manager.py:292` | Pull latest changes | No |
| `update_repository_with_progress()` | `repository_manager.py:352` | Pull with progress | Yes |
| `list_repositories()` | `repository_manager.py:421` | Get all repos | N/A |
| `get_repository()` | `repository_manager.py:483` | Get single repo | N/A |

### Configuration Classes

| Class | File | Purpose |
|-------|------|---------|
| `RepositoryConfig` | `models/config.py:216` | Repository settings (includes `auto_update`) |
| `MCPSkillsConfig` | `models/config.py:256` | Main configuration |

### Indexing Methods

| Method | File | Purpose |
|--------|------|---------|
| `reindex_all()` | `indexing/engine.py:262` | Rebuild all indices |
| `index_skill()` | `indexing/engine.py:197` | Index single skill |
| `get_stats()` | `indexing/engine.py:409` | Get index statistics |

## Testing Considerations

### Test Cases for Auto-Update

1. **First-time update:** Repository never updated → should update
2. **Recent update:** Last updated 1 hour ago → should skip
3. **Stale update:** Last updated 25 hours ago → should update
4. **Network failure:** Git fetch fails → should log and continue
5. **Corrupted repo:** Local repo invalid → should log error
6. **No auto-update:** `auto_update=false` → should skip
7. **Multiple repos:** Mixed auto_update settings → should respect individual settings
8. **Skill changes:** Update adds/removes skills → should report changes
9. **Auto-reindex:** Skills changed → should trigger reindex
10. **Startup delay:** Measure auto-update impact on startup time

### Test Files to Create/Modify

- `tests/services/test_repository_manager_auto_update.py` - Unit tests
- `tests/e2e/test_auto_update_flow.py` - Integration tests
- Mock git operations for fast tests
- Mock datetime for age-based update logic

## Related Research Documents

- **py-mcp-installer-auto-update-flow-2025-12-17.md** - Auto-update pattern for py-mcp-installer (force flag implementation)
- **architecture-review-2025-11-30.md** - Overall architecture review

## Conclusion

The mcp-skillset codebase has **excellent infrastructure for auto-updates** but it's not currently activated. The recommended approach is:

1. **Minimal Phase 1:** Add startup auto-update check in `server.py` (20-30 lines)
2. **Enhanced Phase 2:** Add auto-reindex after skill changes (10-15 lines)
3. **Future Phase 3:** Add user-configurable auto-update settings

**Estimated Implementation Time:**
- Phase 1: 1-2 hours (including tests)
- Phase 2: 30 minutes
- Phase 3: 1 hour

**Risk Level:** Low
- All building blocks exist and are tested
- Auto-update is optional (respects config)
- Failure is non-fatal (logs warning, server starts anyway)
- No external dependencies required

## Files Referenced

### Core Implementation
- `src/mcp_skills/cli/commands/repo.py` - Manual update CLI
- `src/mcp_skills/services/repository_manager.py` - Update logic
- `src/mcp_skills/services/indexing/engine.py` - Reindexing
- `src/mcp_skills/models/config.py` - Configuration schema
- `src/mcp_skills/mcp/server.py` - MCP server entry point

### Supporting Files
- `src/mcp_skills/services/metadata_store.py` - SQLite storage
- `src/mcp_skills/cli/commands/index.py` - Manual reindex CLI
- `src/mcp_skills/services/skill_manager.py` - Skill discovery

**Total Files Analyzed:** 8 core files, 3 supporting files
