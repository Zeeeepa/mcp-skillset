# Setup Command Analysis: Claude Code Integration

**Research Date:** 2025-11-30
**Project:** mcp-skillset
**Linear Project:** [MCP-SkillSet](https://linear.app/1m-hyperdev/project/mcp-skillset-dynamic-rag-skills-for-code-assistants-0000af8da9b0)
**Purpose:** Analyze current setup command to enable Claude CLI integration

---

## Executive Summary

The current `mcp-skillset setup` command installs MCP servers by modifying JSON configuration files in agent directories (Claude Desktop, Claude Code/VS Code, Auggie). However, **Claude Code now provides a native CLI** (`claude mcp add`) for managing MCP servers, which is the recommended integration path.

### Key Finding: Claude CLI Exists and Should Be Used

**Critical Discovery:** The `claude` CLI binary is available with comprehensive MCP management commands:
- `claude mcp add` - Add MCP servers
- `claude mcp remove` - Remove MCP servers
- `claude mcp list` - List configured servers
- `claude mcp get` - Get server details

### Recommended Approach

**Replace JSON file manipulation with Claude CLI invocation** for Claude Code installations:

```python
# Instead of: AgentInstaller._write_config(settings.json)
# Use: subprocess.run(['claude', 'mcp', 'add', 'stdio', 'mcp-skillset', 'mcp-skillset', 'mcp'])
```

---

## Current Implementation Analysis

### 1. Setup Command Location

**Primary File:** `/Users/masa/Projects/mcp-skillset/src/mcp_skills/cli/main.py`

**Function:** `setup()` (lines 67-299)

**Current Flow:**
1. Detect project toolchain (ToolchainDetector)
2. Clone skill repositories (RepositoryManager)
3. Index skills (IndexingEngine)
4. Validate setup
5. **Install for AI agents** (AgentInstaller) ← Focus area
6. Display summary

### 2. Agent Installation Service

**File:** `/Users/masa/Projects/mcp-skillset/src/mcp_skills/services/agent_installer.py`

**Class:** `AgentInstaller`

**Current Installation Method:**
```python
def install(agent: DetectedAgent, force: bool, dry_run: bool) -> InstallResult:
    """Installs MCP SkillSet by modifying agent config JSON files."""

    # 1. Load existing config (JSON parse)
    # 2. Check if already installed
    # 3. Create backup (timestamped)
    # 4. Add MCP config to mcpServers key
    # 5. Validate modified config
    # 6. Write config file
    # 7. Update .gitignore
```

**MCP Server Configuration:**
```python
MCP_SERVER_CONFIG = {
    "command": "mcp-skillset",
    "args": ["mcp"],
    "env": {},
}
```

**Writes to:** `config["mcpServers"]["mcp-skillset"]`

### 3. Agent Detection

**File:** `/Users/masa/Projects/mcp-skillset/src/mcp_skills/services/agent_detector.py`

**Detected Agents:**

| Agent | ID | Config Path (macOS) | Config File |
|-------|----|--------------------|-------------|
| Claude Desktop | `claude-desktop` | `~/Library/Application Support/Claude` | `claude_desktop_config.json` |
| Claude Code | `claude-code` | `~/Library/Application Support/Code/User` | `settings.json` |
| Auggie | `auggie` | `~/Library/Application Support/Auggie` | `config.json` |

**Important Note:** Claude Desktop is **excluded by default** in setup command due to "config path conflicts with Claude Code" (line 224).

### 4. Claude Code Configuration Format

**Current Target:** `~/Library/Application Support/Code/User/settings.json`

**Example Config:**
```json
{
  "statusLine": {...},
  "alwaysThinkingEnabled": false,
  "activeOutputStyle": "claude-mpm",
  "mcpServers": {
    "mcp-skillset": {
      "command": "mcp-skillset",
      "args": ["mcp"],
      "env": {}
    }
  }
}
```

**Problem:** This file contains user-specific VS Code/Claude Code settings that are unrelated to MCP servers. Direct modification risks:
- Breaking user settings
- Merge conflicts
- Unclear separation of concerns

---

## Claude CLI Analysis

### Available Commands

**Base Command:** `claude mcp`

**Subcommands:**

```bash
claude mcp add <name> <commandOrUrl> [args...]      # Add MCP server
  --transport stdio|http|sse                        # Transport type
  --env KEY=VALUE                                   # Environment variables

claude mcp remove <name>                            # Remove server
claude mcp list                                     # List all servers
claude mcp get <name>                               # Get server details
claude mcp add-json <name> <json>                   # Add from JSON
claude mcp add-from-claude-desktop                  # Import from Desktop
```

### Example Usage for mcp-skillset

```bash
# Add mcp-skillset as stdio server
claude mcp add --transport stdio mcp-skillset mcp-skillset mcp

# Remove mcp-skillset
claude mcp remove mcp-skillset

# List all configured servers
claude mcp list

# Get mcp-skillset details
claude mcp get mcp-skillset
```

### Configuration Storage

**Actual Configuration Location:** Unknown from research (likely `~/.claude/` directory based on presence of `~/.claude/settings.json`)

**Benefits of CLI Approach:**
- ✅ Official API - stable, forward-compatible
- ✅ Handles config file format internally
- ✅ Built-in validation
- ✅ Automatic restart/reload handling
- ✅ Clear separation from user settings
- ✅ Cross-platform compatibility
- ✅ Future-proof (CLI changes handled by Anthropic)

---

## Integration Recommendations

### Option 1: Hybrid Approach (Recommended)

**Strategy:** Use Claude CLI for Claude Code, keep JSON manipulation for other agents.

```python
# In agent_installer.py

def install(agent: DetectedAgent, force: bool, dry_run: bool) -> InstallResult:
    """Install MCP SkillSet for detected agent."""

    if agent.id == "claude-code":
        # Use Claude CLI for Claude Code
        return self._install_via_claude_cli(agent, force, dry_run)
    else:
        # Use JSON manipulation for Claude Desktop and Auggie
        return self._install_via_json_config(agent, force, dry_run)

def _install_via_claude_cli(self, agent: DetectedAgent, force: bool, dry_run: bool) -> InstallResult:
    """Install using claude mcp add command."""

    import subprocess

    # Check if claude CLI is available
    if not shutil.which("claude"):
        return InstallResult(
            success=False,
            agent_name=agent.name,
            agent_id=agent.id,
            config_path=agent.config_path,
            error="Claude CLI not found. Please install Claude Code first.",
        )

    # Check if already installed
    if not force:
        result = subprocess.run(
            ["claude", "mcp", "get", "mcp-skillset"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return InstallResult(
                success=False,
                agent_name=agent.name,
                agent_id=agent.id,
                config_path=agent.config_path,
                error="mcp-skillset is already installed. Use --force to overwrite.",
            )

    # Dry run mode
    if dry_run:
        return InstallResult(
            success=True,
            agent_name=agent.name,
            agent_id=agent.id,
            config_path=agent.config_path,
            changes_made="[DRY RUN] Would run: claude mcp add --transport stdio mcp-skillset mcp-skillset mcp",
        )

    # Remove existing if force mode
    if force:
        subprocess.run(
            ["claude", "mcp", "remove", "mcp-skillset"],
            capture_output=True,
            text=True,
        )

    # Add MCP server
    result = subprocess.run(
        [
            "claude",
            "mcp",
            "add",
            "--transport",
            "stdio",
            "mcp-skillset",
            "mcp-skillset",
            "mcp",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return InstallResult(
            success=False,
            agent_name=agent.name,
            agent_id=agent.id,
            config_path=agent.config_path,
            error=f"Failed to add MCP server: {result.stderr}",
        )

    return InstallResult(
        success=True,
        agent_name=agent.name,
        agent_id=agent.id,
        config_path=agent.config_path,
        changes_made="Added mcp-skillset via Claude CLI",
    )
```

### Option 2: CLI-Only Approach (Future-Proof)

**Strategy:** Require all agents to provide CLI management tools, deprecate JSON manipulation.

**Pros:**
- Cleaner codebase
- More maintainable
- Official integration methods only

**Cons:**
- Breaking change for Claude Desktop and Auggie
- Requires those agents to provide CLI tools first

**Timeline:** Consider for v1.0 or v2.0

### Option 3: Keep Current Approach (Not Recommended)

**Strategy:** Continue JSON file manipulation for all agents.

**Cons:**
- ❌ Brittle - config format changes break installer
- ❌ Unofficial - not using documented API
- ❌ Risky - can corrupt user settings
- ❌ Unmaintainable - hard to debug issues

---

## Implementation Plan

### Phase 1: Add Claude CLI Support (v0.6.9)

**Files to Modify:**
1. `/Users/masa/Projects/mcp-skillset/src/mcp_skills/services/agent_installer.py`
   - Add `_install_via_claude_cli()` method
   - Modify `install()` to route Claude Code to CLI method
   - Add `_check_claude_cli_available()` helper

2. `/Users/masa/Projects/mcp-skillset/src/mcp_skills/cli/main.py`
   - Update `setup()` help text to mention CLI usage
   - Update `install()` help text to mention CLI usage

3. `/Users/masa/Projects/mcp-skillset/tests/cli/test_install.py`
   - Add tests for Claude CLI integration
   - Mock subprocess calls
   - Test error handling (CLI not found, add fails, etc.)

**Test Cases:**
- ✅ Claude CLI available, server not installed → Success
- ✅ Claude CLI available, server already installed → Error (use --force)
- ✅ Claude CLI available, --force flag → Remove then add
- ✅ Claude CLI available, --dry-run flag → Show command without running
- ✅ Claude CLI not available → Clear error message
- ✅ Claude CLI add command fails → Proper error handling

### Phase 2: Documentation Updates (v0.6.9)

**Files to Update:**
1. `/Users/masa/Projects/mcp-skillset/README.md`
   - Document Claude CLI requirement
   - Update installation instructions
   - Add troubleshooting section

2. `/Users/masa/Projects/mcp-skillset/docs/DEPLOY.md`
   - Update release checklist
   - Add Claude CLI version compatibility notes

3. Create `/Users/masa/Projects/mcp-skillset/docs/CLAUDE_CLI_INTEGRATION.md`
   - Document design decisions
   - Explain CLI vs JSON approaches
   - Provide migration guide for users

### Phase 3: Deprecation Warning (v0.7.0)

**Timeline:** After Claude CLI integration is stable

**Action:**
- Add deprecation warning for JSON manipulation of Claude Code
- Inform users to use `--agent claude-desktop` or `--agent auggie` explicitly
- Document timeline for removing JSON manipulation

### Phase 4: CLI-Only Requirement (v1.0.0)

**Timeline:** Major version bump

**Breaking Changes:**
- Remove JSON manipulation for Claude Code
- Require Claude CLI for Claude Code installation
- Consider requiring CLI for all agents (if available)

---

## Testing Strategy

### Unit Tests

**File:** `/Users/masa/Projects/mcp-skillset/tests/cli/test_install.py`

```python
@patch("subprocess.run")
def test_claude_cli_installation_success(mock_run):
    """Test successful Claude CLI installation."""
    mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

    installer = AgentInstaller()
    agent = DetectedAgent(
        name="Claude Code",
        id="claude-code",
        config_path=Path("~/.config/Code/User/settings.json"),
        exists=True,
    )

    result = installer.install(agent)

    assert result.success
    assert "claude mcp add" in result.changes_made
    mock_run.assert_called_once_with(
        ["claude", "mcp", "add", "--transport", "stdio", "mcp-skillset", "mcp-skillset", "mcp"],
        capture_output=True,
        text=True,
    )

@patch("shutil.which")
def test_claude_cli_not_found(mock_which):
    """Test error when Claude CLI not found."""
    mock_which.return_value = None

    installer = AgentInstaller()
    agent = DetectedAgent(
        name="Claude Code",
        id="claude-code",
        config_path=Path("~/.config/Code/User/settings.json"),
        exists=True,
    )

    result = installer.install(agent)

    assert not result.success
    assert "Claude CLI not found" in result.error
```

### Integration Tests

**Manual Testing:**
1. Clean Claude Code installation
2. Run `mcp-skillset setup`
3. Verify `claude mcp list` shows mcp-skillset
4. Test skill discovery in Claude Code
5. Run `mcp-skillset install --force`
6. Verify reinstallation works
7. Run `mcp-skillset install --dry-run`
8. Verify no changes made

---

## Risk Analysis

### Risks with CLI Approach

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Claude CLI API changes | Medium | High | Version pin, test on updates, provide fallback |
| CLI not available on all platforms | Low | High | Check availability, clear error messages |
| CLI performance issues | Low | Low | CLI is local, should be fast |
| CLI error messages unclear | Medium | Medium | Parse errors, provide helpful context |

### Risks with Current JSON Approach

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Config format changes | High | High | None - breaks silently |
| User settings corruption | Medium | Critical | Backups help, but recovery is manual |
| Merge conflicts | High | Medium | None - users must resolve manually |
| Unclear ownership | High | Low | Documentation helps, but still confusing |

**Conclusion:** CLI approach has **lower overall risk** despite being a new dependency.

---

## Dependencies

### Required Python Modules

```python
import subprocess  # For running claude CLI
import shutil      # For which() to check CLI availability
```

**Already available** - no new dependencies needed.

### External Dependencies

**Required:**
- `claude` CLI binary (installed with Claude Code)

**Version Compatibility:**
- Minimum Claude Code version: Unknown (needs research)
- Current tested version: Available in Claude Code as of 2025-11-30

---

## Configuration Examples

### Example 1: Default Setup (Auto Mode)

```bash
$ mcp-skillset setup --auto

🚀 Starting mcp-skillset setup...
📁 Project directory: /Users/masa/Projects/my-app

[Step 1/6] Detecting project toolchain...
  ✓ Primary language: Python
  ✓ Frameworks: FastAPI
  ✓ Test frameworks: pytest
  ✓ Confidence: 95%

[Step 2/6] Setting up skill repositories...
  + Cloning: https://github.com/AnthropicWorkshop/claude-skills
    ✓ Cloned 12 skills

[Step 3/6] Building skill indices...
  ✓ Indexed 12 skills

[Step 4/6] Configuring MCP server...
  ✓ Config updated

[Step 5/6] Validating setup...
  ✓ 12 skills available
  ✓ 12 skills indexed

[Step 6/6] Installing for AI agents...
  ✓ Detected 1 agent(s):
    • Claude Code

  Installing mcp-skillset for these agents:
    ✓ Claude Code configured (via Claude CLI)

  Installed for 1/1 agent(s)

✓ Setup complete!

Next steps:
  1. Restart Claude Code to load mcp-skillset
  2. Explore skills: mcp-skillset demo
  3. Search skills: mcp-skillset search 'python testing'
```

### Example 2: Manual Install (Claude Code Only)

```bash
$ mcp-skillset install --agent claude-code

🔍 MCP SkillSet Agent Installer

[Step 1/3] Detecting AI agents...

✓ Found 1 agent(s):
  • Claude Code: ~/.config/Code/User/settings.json

[Step 2/3] Installing...
  ✓ Claude Code configured (via Claude CLI)

✓ Installation complete!

Restart Claude Code to use mcp-skillset.
```

### Example 3: Force Reinstall

```bash
$ mcp-skillset install --agent claude-code --force

🔍 MCP SkillSet Agent Installer

[Step 1/3] Detecting AI agents...

✓ Found 1 agent(s):
  • Claude Code: ~/.config/Code/User/settings.json

[Step 2/3] Installing...
  Removing existing mcp-skillset configuration...
  ✓ Claude Code configured (via Claude CLI)

✓ Installation complete!

Restart Claude Code to use mcp-skillset.
```

---

## Linear Ticket Integration

**Recommended Ticket Structure:**

**Epic:** "Claude CLI Integration for Setup Command"

**Issues:**
1. **Add Claude CLI Support to AgentInstaller**
   - Implement `_install_via_claude_cli()` method
   - Add `_check_claude_cli_available()` helper
   - Route Claude Code installations to CLI method
   - State: Todo

2. **Add Unit Tests for Claude CLI Integration**
   - Test success path
   - Test CLI not found error
   - Test already installed error
   - Test force reinstall
   - Test dry run mode
   - State: Todo

3. **Update Documentation for Claude CLI**
   - Update README.md installation instructions
   - Create CLAUDE_CLI_INTEGRATION.md design doc
   - Update DEPLOY.md release checklist
   - State: Todo

4. **Integration Testing and Validation**
   - Manual testing on clean installation
   - Test force reinstall
   - Test dry run mode
   - Verify skill discovery works
   - State: Todo

5. **Add Deprecation Warning for JSON Manipulation**
   - Add warning message for Claude Code JSON installs
   - Update help text to recommend Claude CLI
   - Document migration path
   - State: Backlog (v0.7.0)

---

## Next Steps

### Immediate Actions (v0.6.9)

1. ✅ **Research Complete** - This document
2. 🔲 Create Linear epic and issues
3. 🔲 Implement `_install_via_claude_cli()` in `agent_installer.py`
4. 🔲 Add unit tests in `test_install.py`
5. 🔲 Manual integration testing
6. 🔲 Update documentation
7. 🔲 Release v0.6.9 with Claude CLI support

### Future Considerations (v0.7.0+)

1. Add deprecation warnings for JSON manipulation
2. Research Claude Desktop CLI (if available)
3. Research Auggie CLI (if available)
4. Consider CLI-only requirement for v1.0

---

## References

### Code Files

- `/Users/masa/Projects/mcp-skillset/src/mcp_skills/cli/main.py` - Setup command
- `/Users/masa/Projects/mcp-skillset/src/mcp_skills/services/agent_installer.py` - Installation logic
- `/Users/masa/Projects/mcp-skillset/src/mcp_skills/services/agent_detector.py` - Agent detection
- `/Users/masa/Projects/mcp-skillset/tests/cli/test_setup.py` - Setup tests
- `/Users/masa/Projects/mcp-skillset/tests/cli/test_install.py` - Install tests

### Configuration Locations

- Claude Code Settings: `~/Library/Application Support/Code/User/settings.json`
- Claude Code Skills: `~/.claude/skills/`
- Claude Code Config: `~/.claude/settings.json`
- Claude Desktop Config: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Auggie Config: `~/Library/Application Support/Auggie/config.json`

### External Documentation

- Claude CLI Help: `claude --help`
- Claude MCP Commands: `claude mcp --help`

---

## Appendix: Claude CLI Command Reference

### Full Command Syntax

```bash
# Add stdio MCP server
claude mcp add --transport stdio <name> <command> [args...]

# Add HTTP MCP server
claude mcp add --transport http <name> <url>

# Add SSE MCP server
claude mcp add --transport sse <name> <url>

# Add with environment variables
claude mcp add --transport stdio --env KEY=VALUE <name> <command> [args...]

# Remove MCP server
claude mcp remove <name>

# List all MCP servers
claude mcp list

# Get MCP server details
claude mcp get <name>

# Add from JSON string
claude mcp add-json <name> '<json-config>'

# Import from Claude Desktop
claude mcp add-from-claude-desktop
```

### Example: Adding mcp-skillset

```bash
# Basic installation
claude mcp add --transport stdio mcp-skillset mcp-skillset mcp

# With environment variables
claude mcp add --transport stdio \
  --env MCP_SKILLSET_DEBUG=true \
  mcp-skillset \
  mcp-skillset \
  mcp

# Using JSON
claude mcp add-json mcp-skillset '{
  "command": "mcp-skillset",
  "args": ["mcp"],
  "env": {}
}'
```

---

**End of Research Document**
