# Skill Download Progress Bar Enhancement Analysis

**Date:** 2025-11-30
**Objective:** Identify skill downloading code and integration points for per-repository progress bars
**Status:** Complete

---

## Executive Summary

This analysis identifies the skill downloading workflow and provides specific recommendations for adding Rich Progress bars with "one per repo" tracking. The codebase uses GitPython for repository cloning in `RepositoryManager`, with two main CLI entry points: `setup` command (downloads default repos) and `repo update` command (updates existing repos).

**Key Finding:** Repository downloading happens in `RepositoryManager.add_repository()` and `RepositoryManager.update_repository()`, currently with simple spinner progress indicators. Enhancement requires:
1. Add BarColumn and DownloadColumn to Rich Progress display
2. Track git clone/pull progress via GitPython callbacks
3. Display per-repository progress with bytes downloaded and transfer speed

---

## 1. Download Location

### Primary Download Service

**File:** `/Users/masa/Projects/mcp-skillset/src/mcp_skills/services/repository_manager.py`

**Class:** `RepositoryManager`

**Methods:**
- `add_repository(url, priority, license)` - Lines 94-171
  - Clones new repository using `git.Repo.clone_from()`
  - Line 149: `git.Repo.clone_from(url, local_path, depth=1)`
  - Currently no progress feedback during clone operation
  - Counts skills after clone completes

- `update_repository(repo_id)` - Lines 173-226
  - Updates existing repository using `git pull`
  - Lines 204-206: Gets repo and pulls from origin
  - Currently no progress feedback during pull operation
  - Rescans skills after pull completes

**GitHub Discovery Service:**
**File:** `/Users/masa/Projects/mcp-skillset/src/mcp_skills/services/github_discovery.py`
- **Does NOT download repositories** - only searches/verifies via API
- Used for discovering repos, not cloning them
- No progress bars needed for this service

---

## 2. Current Implementation

### Progress Feedback: **Spinner Only** (Inadequate)

**Current Pattern (Repeated 13+ times in codebase):**
```python
with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    console=console,
) as progress:
    task = progress.add_task("Cloning repository...", total=None)
    repo = repo_manager.add_repository(url, priority=priority)
    progress.update(task, completed=True)
```

**Problems:**
- `total=None` means indeterminate progress (spinner only)
- No file/byte counts shown
- No transfer speed information
- User can't estimate remaining time
- All repos in setup get same treatment (no per-repo visibility)

### Repository Iteration Pattern

**Setup Command (Lines 129-156 in main.py):**
```python
# Clone repositories
for repo_config in repos_to_add:
    repo_id = repo_manager._generate_repo_id(repo_config["url"])
    existing = repo_manager.get_repository(repo_id)

    if existing:
        console.print(f"  ⊙ Repository already exists: {repo_config['url']}")
    else:
        console.print(f"  + Cloning: {repo_config['url']}")
        new_repo = repo_manager.add_repository(
            url=repo_config["url"],
            priority=repo_config["priority"],
            license=repo_config["license"],
        )
        console.print(f"    ✓ Cloned {new_repo.skill_count} skills")
```

**Repo Update Command (Lines 1456-1487 in main.py):**
```python
with Progress(...) as progress:
    for repo in repos:
        task = progress.add_task(f"Updating {repo.id}...", total=None)
        updated_repo = repo_manager.update_repository(repo.id)
        progress.update(task, completed=True)
```

**Download Type:** **Sequential** (one repo at a time, synchronous)
- No parallelization currently
- GitPython operations are blocking
- Opportunity for async/parallel downloads in future

---

## 3. Integration Points for Rich Progress

### Recommended Location: CLI Command Level

**Why CLI level vs Service level:**
- CLI already imports Rich Progress components
- Service layer should remain UI-agnostic
- Progress display is presentation concern, not business logic
- Allows different UIs (TUI, web dashboard) to implement their own progress

### Specific Integration Points

#### A. Setup Command (main.py lines 129-156)

**Current:**
```python
for repo_config in repos_to_add:
    console.print(f"  + Cloning: {repo_config['url']}")
    new_repo = repo_manager.add_repository(...)
    console.print(f"    ✓ Cloned {new_repo.skill_count} skills")
```

**Enhanced:**
```python
from rich.progress import (
    Progress, SpinnerColumn, TextColumn,
    BarColumn, DownloadColumn, TransferSpeedColumn,
    TimeRemainingColumn
)

with Progress(
    SpinnerColumn(),
    TextColumn("[bold blue]{task.description}"),
    BarColumn(),
    DownloadColumn(),
    TransferSpeedColumn(),
    TimeRemainingColumn(),
    console=console,
) as progress:
    for repo_config in repos_to_add:
        # Check if exists
        repo_id = repo_manager._generate_repo_id(repo_config["url"])
        existing = repo_manager.get_repository(repo_id)

        if existing:
            console.print(f"  ⊙ Repository already exists: {repo_config['url']}")
            continue

        # Add task for this repo
        task_id = progress.add_task(
            f"Cloning {repo_config['url']}",
            total=100,  # Will update with actual bytes
            start=False
        )

        # Clone with progress callback
        new_repo = repo_manager.add_repository_with_progress(
            url=repo_config["url"],
            priority=repo_config["priority"],
            license=repo_config["license"],
            progress_callback=lambda current, total: progress.update(
                task_id, completed=current, total=total
            )
        )

        progress.update(task_id, completed=True)
        console.print(f"    ✓ Cloned {new_repo.skill_count} skills")
```

#### B. Repo Update Command (main.py lines 1451-1487)

**Current:**
```python
with Progress(...) as progress:
    for repo in repos:
        task = progress.add_task(f"Updating {repo.id}...", total=None)
        updated_repo = repo_manager.update_repository(repo.id)
```

**Enhanced:**
```python
with Progress(
    SpinnerColumn(),
    TextColumn("[bold blue]{task.description}"),
    BarColumn(),
    DownloadColumn(),
    TransferSpeedColumn(),
    console=console,
) as progress:
    for repo in repos:
        task_id = progress.add_task(
            f"Updating {repo.id}",
            total=100,
            start=False
        )

        updated_repo = repo_manager.update_repository_with_progress(
            repo_id=repo.id,
            progress_callback=lambda current, total: progress.update(
                task_id, completed=current, total=total
            )
        )

        progress.update(task_id, completed=True)
```

---

## 4. Metrics to Track Per Repository

### Primary Metrics (Must Have)

1. **Repository Name/ID** - Already displayed in task description
2. **Bytes Downloaded** - Via GitPython progress callback
3. **Total Bytes** - Via GitPython progress callback
4. **Transfer Speed** - Calculated by Rich Progress automatically
5. **Download Status** - downloading/complete/failed via task state

### Secondary Metrics (Nice to Have)

6. **Files/Objects Cloned** - Available via GitPython callbacks
7. **Time Remaining** - Estimated by Rich Progress
8. **Skill Count** - Already tracked, display after completion

### GitPython Progress Callback API

**GitPython provides `RemoteProgress` class for tracking:**

```python
from git import RemoteProgress

class CloneProgress(RemoteProgress):
    def __init__(self, progress_callback):
        super().__init__()
        self.progress_callback = progress_callback

    def update(self, op_code, cur_count, max_count=None, message=''):
        # op_code: Stage of clone (BEGIN, END, COUNTING, etc.)
        # cur_count: Current count (bytes or objects)
        # max_count: Total count
        # message: Git status message

        if max_count:
            self.progress_callback(cur_count, max_count)

# Usage in clone:
progress_handler = CloneProgress(callback_func)
git.Repo.clone_from(url, path, progress=progress_handler)
```

**Available op_codes from GitPython:**
- `RemoteProgress.BEGIN` - Start of operation
- `RemoteProgress.END` - End of operation
- `RemoteProgress.COUNTING` - Counting objects
- `RemoteProgress.COMPRESSING` - Compressing objects
- `RemoteProgress.WRITING` - Writing objects
- `RemoteProgress.RECEIVING` - Receiving objects (download phase)

---

## 5. Related Commands That Trigger Downloads

### Commands That Download Repositories

1. **`mcp-skillset setup`** (Lines 73-322)
   - **Downloads:** DEFAULT_REPOS (5 repositories)
   - **When:** First-time setup or re-setup
   - **Pattern:** Loops through repos_to_add, calls add_repository()
   - **Progress:** Currently simple print statements
   - **Priority:** **HIGH** - Most common user entry point

2. **`mcp-skillset repo add <url>`** (Lines 1308-1349)
   - **Downloads:** Single repository from URL
   - **When:** User manually adds custom repo
   - **Pattern:** Single add_repository() call with spinner
   - **Progress:** Spinner only (lines 1320-1328)
   - **Priority:** **MEDIUM** - Advanced users only

3. **`mcp-skillset repo update [repo_id]`** (Lines 1402-1505)
   - **Downloads:** Updates existing repos (git pull)
   - **When:** User updates repos or automatic updates
   - **Pattern:**
     - Single repo: One update_repository() call
     - All repos: Loop through repos, update each
   - **Progress:** Spinner per repo (lines 1451-1487)
   - **Priority:** **HIGH** - Regular maintenance command

### Commands That Do NOT Download

- `discover search/trending/topic` - GitHub API search only
- `index` - Indexes local repos, no downloads
- `search/show/list` - Query operations only
- `config/doctor/stats` - Management commands

---

## 6. Recommended Implementation Approach

### Phase 1: Add GitPython Progress Callbacks (Service Layer)

**File:** `src/mcp_skills/services/repository_manager.py`

**New Method:**
```python
def add_repository_with_progress(
    self,
    url: str,
    priority: int = 0,
    license: str = "Unknown",
    progress_callback: Callable[[int, int], None] | None = None,
) -> Repository:
    """Clone new repository with progress tracking.

    Args:
        url: Git repository URL
        priority: Priority for skill selection (0-100)
        license: Repository license
        progress_callback: Callback function(current_bytes, total_bytes)

    Returns:
        Repository metadata object
    """
    # ... validation code (lines 126-145) ...

    # Clone with progress
    local_path = self.base_dir / repo_id
    logger.info(f"Cloning repository {url} to {local_path}")

    try:
        if progress_callback:
            from git import RemoteProgress

            class CloneProgress(RemoteProgress):
                def update(self, op_code, cur_count, max_count=None, message=''):
                    if max_count and progress_callback:
                        progress_callback(cur_count, max_count)

            progress_handler = CloneProgress()
            git.Repo.clone_from(url, local_path, depth=1, progress=progress_handler)
        else:
            # Fallback to no progress (existing behavior)
            git.Repo.clone_from(url, local_path, depth=1)
    except git.exc.GitCommandError as e:
        raise ValueError(f"Failed to clone repository {url}: {e}") from e

    # ... rest of method (lines 153-171) ...
```

**Similar for update_repository_with_progress():**
```python
def update_repository_with_progress(
    self,
    repo_id: str,
    progress_callback: Callable[[int, int], None] | None = None,
) -> Repository:
    """Pull latest changes with progress tracking."""
    # ... validation (lines 196-198) ...

    try:
        repo = git.Repo(repository.local_path)
        origin = repo.remotes.origin

        if progress_callback:
            from git import RemoteProgress

            class PullProgress(RemoteProgress):
                def update(self, op_code, cur_count, max_count=None, message=''):
                    if max_count and progress_callback:
                        progress_callback(cur_count, max_count)

            progress_handler = PullProgress()
            origin.pull(progress=progress_handler)
        else:
            origin.pull()
    except git.exc.GitCommandError as e:
        raise ValueError(f"Failed to update repository {repo_id}: {e}") from e

    # ... rest of method (lines 215-226) ...
```

### Phase 2: Enhance CLI Progress Display

**File:** `src/mcp_skills/cli/main.py`

**Update imports (line 19):**
```python
from rich.progress import (
    Progress, SpinnerColumn, TextColumn,
    BarColumn, DownloadColumn, TransferSpeedColumn,
    TimeRemainingColumn,
)
```

**Update setup command (replace lines 129-156):**
```python
# Clone repositories with progress bars
if repos_to_add:
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}", justify="left"),
        BarColumn(bar_width=40),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        for repo_config in repos_to_add:
            repo_id = repo_manager._generate_repo_id(repo_config["url"])
            existing = repo_manager.get_repository(repo_id)

            if existing:
                console.print(f"  ⊙ Repository already exists: {repo_config['url']}")
                added_repos.append(existing)
                continue

            # Add task for this repository
            task_id = progress.add_task(
                f"Cloning {repo_config['url']}",
                total=100,  # Will be updated by callback
                start=False
            )

            try:
                # Clone with progress tracking
                def update_progress(current: int, total: int) -> None:
                    progress.update(task_id, completed=current, total=total)
                    if not progress.tasks[task_id].started:
                        progress.start_task(task_id)

                new_repo = repo_manager.add_repository_with_progress(
                    url=repo_config["url"],
                    priority=repo_config["priority"],
                    license=repo_config["license"],
                    progress_callback=update_progress,
                )

                progress.update(task_id, completed=True)
                added_repos.append(new_repo)
                console.print(f"    ✓ Cloned {new_repo.skill_count} skills")

            except Exception as e:
                progress.stop()
                console.print(f"    [red]✗ Failed to clone {repo_config['url']}: {e}[/red]")
                logger.error(f"Repository clone failed: {e}")
```

**Update repo update command (replace lines 1451-1487):**
```python
with Progress(
    SpinnerColumn(),
    TextColumn("[bold blue]{task.description}", justify="left"),
    BarColumn(bar_width=40),
    DownloadColumn(),
    TransferSpeedColumn(),
    console=console,
) as progress:
    for repo in repos:
        task_id = progress.add_task(
            f"Updating {repo.id}",
            total=100,
            start=False
        )

        try:
            old_skill_count = repo.skill_count

            def update_progress(current: int, total: int) -> None:
                progress.update(task_id, completed=current, total=total)
                if not progress.tasks[task_id].started:
                    progress.start_task(task_id)

            updated_repo = repo_manager.update_repository_with_progress(
                repo_id=repo.id,
                progress_callback=update_progress
            )

            progress.update(task_id, completed=True)
            updated_count += 1
            skill_diff = updated_repo.skill_count - old_skill_count
            new_skills += skill_diff

            # ... print success messages (lines 1467-1476) ...

        except Exception as e:
            progress.stop()
            console.print(f"  [red]✗[/red] {repo.id}: {e}")
            failed_count += 1
            # Recreate progress for next repo
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(bar_width=40),
                DownloadColumn(),
                TransferSpeedColumn(),
                console=console,
            )
            progress.start()
```

### Phase 3: Handle Edge Cases

**Edge Cases to Handle:**

1. **Repository already exists** (setup command)
   - Skip progress bar, just print "already exists"
   - Don't add task to progress display

2. **Clone/pull fails mid-download**
   - Stop progress gracefully
   - Display error message
   - Continue with next repo (setup/update all)

3. **No bytes transferred** (cached/up-to-date repos)
   - GitPython may report 0/0 for cached operations
   - Display as "up to date" instead of 0 bytes

4. **Very small repos** (<1MB)
   - Progress may complete too fast to see
   - Still show completed state for user feedback

5. **Network interruption**
   - GitPython raises GitCommandError
   - Catch, stop progress, show error, continue

---

## 7. Example Output (Before vs After)

### Before (Current Spinner Only)

```
🚀 Starting mcp-skillset setup...
📁 Project directory: /path/to/project

Step 2/6: Setting up skill repositories...
  + Cloning: https://github.com/anthropics/skills.git
  ⠋ Cloning repository...
    ✓ Cloned 42 skills
  + Cloning: https://github.com/obra/superpowers.git
  ⠋ Cloning repository...
    ✓ Cloned 15 skills
```

**Problems:**
- No idea how long it will take
- Can't see download progress
- All repos look the same
- No bytes/speed information

### After (Enhanced Progress Bars)

```
🚀 Starting mcp-skillset setup...
📁 Project directory: /path/to/project

Step 2/6: Setting up skill repositories...
⠋ Cloning anthropics/skills      ━━━━━━━━━━━━━━━━━╸━━━━━━━━━  12.5/18.2 MB  2.1 MB/s  0:00:03
  ✓ Cloned 42 skills
⠋ Cloning obra/superpowers        ━━━━━━━━━━━━━━━━━━━━━━━━━━  5.8/5.8 MB    1.8 MB/s  0:00:00
  ✓ Cloned 15 skills
⠋ Cloning ComposioHQ/awesome...   ━━━━━━━━━━━╸━━━━━━━━━━━━━  8.3/15.1 MB   1.5 MB/s  0:00:04
```

**Improvements:**
- Clear visual progress per repo
- Bytes downloaded vs total
- Transfer speed visible
- Time remaining estimate
- One progress bar per repository (as requested)

---

## 8. Code Changes Summary

### Files to Modify

1. **`src/mcp_skills/services/repository_manager.py`** (~50 lines added)
   - Add `add_repository_with_progress()` method
   - Add `update_repository_with_progress()` method
   - Keep existing methods for backward compatibility
   - Add GitPython RemoteProgress handlers

2. **`src/mcp_skills/cli/main.py`** (~100 lines modified)
   - Update Rich Progress imports (line 19)
   - Replace setup command repo cloning (lines 129-156)
   - Replace repo update command progress (lines 1451-1487)
   - Replace repo add command progress (lines 1320-1328)

### Backward Compatibility

- Existing methods `add_repository()` and `update_repository()` remain unchanged
- New methods with `_with_progress` suffix are optional
- CLI can choose which method to call based on context
- Tests can continue using existing methods

### Testing Requirements

1. **Unit Tests** (RepositoryManager)
   - Test progress callback is invoked
   - Test progress callback receives correct values
   - Test fallback when callback is None

2. **Integration Tests** (CLI)
   - Test setup command with multiple repos
   - Test repo update with progress
   - Test error handling mid-download

3. **Manual Testing** (Visual)
   - Clone large repo (>50MB) to see full progress
   - Clone small repo (<1MB) to test fast completion
   - Test network interruption handling

---

## 9. Performance Considerations

### Memory Impact

- **Minimal**: Progress callbacks use ~100 bytes per repo
- Rich Progress display: ~5KB total
- No additional data structures needed

### CPU Impact

- **Negligible**: Progress update is O(1) operation
- GitPython calls progress callback ~10-100 times per repo
- Rich rendering happens in separate thread

### Network Impact

- **None**: Progress tracking is passive monitoring
- No additional network requests
- Git clone/pull behavior unchanged

### Disk Impact

- **None**: Same files downloaded as before
- No additional caching or temporary files

---

## 10. Alternative Approaches Considered

### Alternative 1: Service-Level Progress Bars

**Approach:** Add Rich Progress inside RepositoryManager methods

**Pros:**
- Less CLI code duplication
- Progress "just works" everywhere

**Cons:**
- Violates separation of concerns
- Service layer should be UI-agnostic
- Hard to customize for different UIs (web, TUI)
- Difficult to test (mocking Rich Progress)

**Decision:** REJECTED - Keep UI logic in CLI layer

### Alternative 2: Event-Based Progress

**Approach:** Use event emitters/observers pattern

**Pros:**
- Decoupled service and UI
- Multiple listeners possible
- Clean architecture

**Cons:**
- Over-engineering for simple use case
- Adds complexity (event system)
- Harder to debug than direct callbacks

**Decision:** REJECTED - Callbacks are simpler

### Alternative 3: Parallel Downloads

**Approach:** Download multiple repos simultaneously

**Pros:**
- Faster overall setup time
- Better network utilization
- Modern UX expectation

**Cons:**
- Requires async/threading architecture
- Complex error handling
- May overwhelm GitHub rate limits
- GitPython is synchronous (need wrappers)

**Decision:** DEFERRED - Future enhancement (post-v0.7.0)
- Current sequential approach is simpler
- Can add parallelization later without breaking changes
- Focus on progress visibility first

---

## 11. Dependencies and Risks

### Dependencies

- **GitPython** (already installed): Provides RemoteProgress API
- **Rich** (already installed): Progress display components
- **No new dependencies required**

### Risks

#### Risk 1: GitPython Progress API Changes
- **Likelihood:** Low
- **Impact:** Medium
- **Mitigation:** GitPython is stable, API unchanged since 2.x
- **Fallback:** Detect missing progress support, use spinner

#### Risk 2: Progress Not Reported for Cached Clones
- **Likelihood:** High
- **Impact:** Low
- **Mitigation:** Check for 0/0 progress, show "cached" status
- **User Impact:** Visual only, download still succeeds

#### Risk 3: Progress Callback Performance
- **Likelihood:** Low
- **Impact:** Low
- **Mitigation:** Progress updates are async in Rich
- **Monitoring:** Test with 100+ repos to verify

---

## 12. Success Metrics

### User Experience Metrics

1. **Visibility:** Users can see download progress for each repo ✓
2. **Transparency:** Transfer speed and ETA visible ✓
3. **Per-Repo Tracking:** One progress bar per repository ✓
4. **Error Handling:** Failed downloads clearly indicated ✓

### Technical Metrics

1. **Performance:** <5% overhead for progress tracking
2. **Memory:** <1MB additional memory usage
3. **Compatibility:** All existing tests pass
4. **Coverage:** Progress paths covered by tests (>80%)

---

## 13. Next Steps

### Implementation Order

1. **Phase 1:** Add progress callbacks to RepositoryManager (2-3 hours)
   - Add `_with_progress` methods
   - Add RemoteProgress handlers
   - Test with unit tests

2. **Phase 2:** Update CLI commands (3-4 hours)
   - Update Rich Progress imports
   - Replace setup command progress
   - Replace repo update command progress
   - Replace repo add command progress

3. **Phase 3:** Testing and refinement (2-3 hours)
   - Test with large repos (>50MB)
   - Test with small repos (<1MB)
   - Test error handling
   - Manual QA

4. **Phase 4:** Documentation (1 hour)
   - Update CLI help text
   - Add progress screenshots to README
   - Document progress callback API

### Estimated Total Effort: **8-11 hours**

### Recommended Ticket

**Title:** Add per-repository progress bars for skill downloads

**Labels:** enhancement, UX, CLI

**Priority:** Medium

**Description:**
> Enhance skill download UX by adding Rich Progress bars that show:
> - Bytes downloaded per repository
> - Transfer speed
> - Time remaining
> - Clear status (downloading/complete/failed)
>
> Affects: `setup`, `repo add`, `repo update` commands
>
> Technical approach: Add GitPython RemoteProgress callbacks to RepositoryManager,
> display with Rich Progress BarColumn + DownloadColumn in CLI layer.

---

## Appendix A: Code References

### RepositoryManager Implementation

**File:** `src/mcp_skills/services/repository_manager.py`

**Key Methods:**
- Lines 94-171: `add_repository()` - Clone new repo
- Lines 173-226: `update_repository()` - Pull latest changes
- Lines 307-342: `_is_valid_git_url()` - URL validation
- Lines 344-388: `_generate_repo_id()` - Create repo ID from URL
- Lines 390-408: `_count_skills()` - Count SKILL.md files

### CLI Commands

**File:** `src/mcp_skills/cli/main.py`

**Key Commands:**
- Lines 73-322: `setup()` - Full setup including repo cloning
- Lines 1308-1349: `repo add()` - Add single repository
- Lines 1402-1505: `repo update()` - Update one or all repos

### Rich Progress Patterns

**Current Usage (13 instances):**
- All use SpinnerColumn + TextColumn only
- All use `total=None` (indeterminate)
- No download/transfer speed tracking

---

## Appendix B: GitPython RemoteProgress API

### RemoteProgress Class

```python
from git import RemoteProgress

class MyProgress(RemoteProgress):
    def update(self, op_code, cur_count, max_count=None, message=''):
        """Called by git operations to report progress.

        Args:
            op_code: Integer representing operation stage
            cur_count: Current count (bytes or objects)
            max_count: Total count (None if unknown)
            message: Status message from git
        """
        pass

# Usage:
progress = MyProgress()
git.Repo.clone_from(url, path, progress=progress)
```

### Operation Codes

```python
RemoteProgress.BEGIN = 1        # Start of operation
RemoteProgress.END = 2          # End of operation
RemoteProgress.COUNTING = 4     # Counting objects
RemoteProgress.COMPRESSING = 8  # Compressing objects
RemoteProgress.WRITING = 16     # Writing objects
RemoteProgress.RECEIVING = 32   # Receiving objects (download)
RemoteProgress.RESOLVING = 64   # Resolving deltas
RemoteProgress.FINDING = 128    # Finding sources
RemoteProgress.CHECKING = 256   # Checking out files
```

### Example Progress Handler

```python
class CloneProgress(RemoteProgress):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.last_update = 0

    def update(self, op_code, cur_count, max_count=None, message=''):
        # Only report RECEIVING stage (actual download)
        if op_code & RemoteProgress.RECEIVING:
            if max_count:
                # Throttle updates to every 100KB
                if cur_count - self.last_update > 100000:
                    self.callback(cur_count, max_count)
                    self.last_update = cur_count
```

---

## Appendix C: Rich Progress Components

### Recommended Columns

```python
from rich.progress import (
    Progress,
    SpinnerColumn,      # Spinning indicator
    TextColumn,         # Task description
    BarColumn,          # Progress bar
    DownloadColumn,     # Shows downloaded/total (e.g., "12.5/18.2 MB")
    TransferSpeedColumn,# Shows speed (e.g., "2.1 MB/s")
    TimeRemainingColumn,# Shows ETA (e.g., "0:00:03")
)

progress = Progress(
    SpinnerColumn(),
    TextColumn("[bold blue]{task.description}", justify="left"),
    BarColumn(bar_width=40),
    DownloadColumn(),
    TransferSpeedColumn(),
    TimeRemainingColumn(),
    console=console,
)
```

### Column Descriptions

- **SpinnerColumn:** Rotating indicator (⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏)
- **TextColumn:** Custom text with Rich markup
- **BarColumn:** Visual progress bar (━━━━╸━━━)
- **DownloadColumn:** Bytes downloaded vs total
- **TransferSpeedColumn:** Current download speed
- **TimeRemainingColumn:** Estimated time to completion

---

**End of Analysis**
