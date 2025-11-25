# CLI Test Suite for mcp-skillset

Comprehensive test coverage for all CLI commands using Click's CliRunner and mocked services.

## Test Structure

```
tests/cli/
├── __init__.py                 # Package marker
├── conftest.py                 # Shared fixtures (159 lines)
├── test_config.py             # Config command tests (12 tests, 222 lines)
├── test_doctor.py             # Health check tests (15 tests, 275 lines)
├── test_enrich.py             # Prompt enrichment tests (15 tests, 273 lines)
├── test_help.py               # Help/info/list tests (15 tests, 215 lines)
├── test_index.py              # Indexing tests (10 tests, 220 lines)
├── test_install.py            # Agent installation tests (11 tests, 246 lines)
├── test_mcp.py                # MCP server tests (10 tests, 182 lines)
├── test_search.py             # Search/recommend tests (17 tests, 272 lines)
└── test_setup.py              # Setup command tests (7 tests, 195 lines)
```

**Total: 112 tests across 2,613 lines of code**

## Commands Covered

1. **setup** - Auto-configuration with toolchain detection
2. **config** - Interactive and command-line configuration
3. **index** - Skill indexing operations
4. **install** - Agent installation for Claude, Cursor, etc.
5. **mcp** - MCP server startup
6. **list/info/show** - Skill listing and information display
7. **doctor/health** - Health checks and diagnostics
8. **search/recommend** - Skill search and recommendations
9. **enrich** - Prompt enrichment

## Running Tests

```bash
# Run all CLI tests
uv run pytest tests/cli/ -v

# Run specific test file
uv run pytest tests/cli/test_setup.py -v

# Run specific test
uv run pytest tests/cli/test_setup.py::TestSetupCommand::test_setup_help -v

# Run with coverage
uv run pytest tests/cli/ --cov=src/mcp_skills/cli --cov-report=html
```

## Test Patterns

### Mocking Strategy

All tests use comprehensive mocking to isolate CLI logic:

- **SkillManager**: Mocked for skill operations
- **IndexingEngine**: Mocked for indexing operations
- **RepositoryManager**: Mocked for repository management
- **ToolchainDetector**: Mocked for project detection
- **AgentInstaller**: Mocked for agent installation
- **PromptEnricher**: Mocked for prompt enrichment
- **MCPSkillsConfig**: Mocked configuration

### Test Categories

1. **Help Tests**: Verify command help text and options
2. **Success Scenarios**: Test successful command execution
3. **Error Handling**: Test graceful failure and error messages
4. **Edge Cases**: Test boundary conditions and unusual inputs
5. **Integration Points**: Test interaction between components

## Fixtures (conftest.py)

### Core Fixtures

- `cli_runner`: Click's CliRunner for command invocation
- `mock_config`: Mocked MCPSkillsConfig instance
- `mock_skill`: Sample skill for testing
- `mock_repository`: Sample repository metadata
- `mock_toolchain_info`: Sample toolchain detection result

### Service Mocks

- `mock_skill_manager`: Mocked SkillManager
- `mock_indexing_engine`: Mocked IndexingEngine
- `mock_repository_manager`: Mocked RepositoryManager
- `mock_toolchain_detector`: Mocked ToolchainDetector
- `mock_agent_installer`: Mocked AgentInstaller
- `mock_prompt_enricher`: Mocked PromptEnricher

### Utilities

- `isolated_filesystem`: Temporary filesystem for file operations

## Test Coverage by Command

| Command | Tests | Key Areas |
|---------|-------|-----------|
| setup | 7 | Toolchain detection, repo cloning, indexing |
| config | 12 | Interactive menu, --show, --set, validation |
| index | 10 | Incremental, force, stats, error handling |
| install | 11 | Multiple agents, dry-run, force, validation |
| mcp | 10 | Server startup, dev mode, error handling |
| help | 15 | List, info, show, stats, version |
| doctor | 15 | Health checks, config validation, diagnostics |
| search | 17 | Query search, recommendations, modes |
| enrich | 15 | File/text input, output, modes, limits |

## Known Issues and TODOs

### Fixture Issues

Some tests have fixture compatibility issues that need resolution:

1. **SkillMetadata** - Field name mismatches (id vs name)
2. **Repository** - Initialization parameter mismatches
3. **HybridSearchConfig** - Field name changes (kg_weight -> graph_weight)

### Skipped Tests

- MCP server tests with I/O issues (marked with `@pytest.mark.skip`)
- Integration tests requiring full system setup
- Tests requiring actual network connections

### Improvements Needed

1. Fix remaining fixture initialization issues
2. Add more integration tests for command combinations
3. Improve mock assertions to verify call arguments
4. Add tests for concurrent command execution
5. Add tests for signal handling (SIGINT, SIGTERM)

## Design Decisions

### Click CliRunner

All tests use Click's `CliRunner` which provides:
- Isolated invocation context
- Captured stdout/stderr
- Exit code verification
- Input simulation
- Temporary filesystem support

### Comprehensive Mocking

External services are fully mocked because:
- Tests run quickly without I/O
- No external dependencies required
- Predictable test behavior
- Easy to test error conditions

### Test Organization

Tests are organized by command rather than by functionality:
- Easy to find tests for specific commands
- Clear test coverage per command
- Mirrors CLI command structure

## Contributing

When adding new CLI commands:

1. Create new test file: `test_<command>.py`
2. Add fixtures to `conftest.py` if needed
3. Include help, success, and error tests
4. Mock all external dependencies
5. Use descriptive test names
6. Document skipped tests

## Example Test

```python
@patch("mcp_skills.cli.main.SkillManager")
def test_search_basic(
    mock_manager_cls: Mock,
    cli_runner: CliRunner,
    mock_skill,
) -> None:
    """Test basic search command."""
    # Setup mock
    mock_manager = Mock()
    mock_manager.search_skills.return_value = [mock_skill]
    mock_manager_cls.return_value = mock_manager

    # Run command
    result = cli_runner.invoke(cli, ["search", "testing"])

    # Verify
    assert result.exit_code == 0
    assert "Searching for" in result.output
    mock_manager.search_skills.assert_called_once()
```

## License

Same as mcp-skillset project license.
