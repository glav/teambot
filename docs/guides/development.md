# Development

Guide for contributing to TeamBot development.

## Setup

```bash
# Install all dependencies including dev tools
uv sync --group dev

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/teambot --cov-report=term-missing

# Lint and format
uv run ruff check .
uv run ruff format .
```

## Project Structure

```
teambot/
├── src/teambot/
│   ├── cli.py                # CLI entry point
│   ├── orchestrator.py       # Agent lifecycle management
│   ├── agent_runner.py       # Individual agent process execution
│   ├── window_manager.py     # Cross-platform window spawning
│   ├── orchestration/        # File-based orchestration
│   │   ├── objective_parser.py
│   │   ├── execution_loop.py
│   │   ├── review_iterator.py
│   │   ├── parallel_executor.py
│   │   ├── acceptance_test_executor.py
│   │   ├── stage_config.py
│   │   └── time_manager.py
│   ├── config/               # Configuration loading
│   ├── copilot/              # Copilot SDK wrapper
│   ├── history/              # History file management
│   ├── messaging/            # Inter-agent messaging
│   ├── prompts/              # Persona templates
│   ├── repl/                 # Interactive REPL (parser, router, commands)
│   ├── tasks/                # Task graph, execution, and output injection
│   ├── ui/                   # Split-pane terminal interface (Textual)
│   ├── visualization/        # Console formatting and animations
│   └── workflow/             # Workflow state machine
├── tests/                    # Test suite (1050 tests)
└── docs/                     # Documentation
```

## Running Tests

```bash
# All tests
uv run pytest

# Specific module
uv run pytest tests/test_workflow/

# Single test file
uv run pytest tests/test_cli.py

# With verbose output
uv run pytest -v

# Stop on first failure
uv run pytest -x
```

## Test Coverage

Current: **80% coverage** with **1050 tests**

| Module | Coverage |
|--------|----------|
| `orchestration/objective_parser.py` | 100% |
| `orchestration/time_manager.py` | 100% |
| `orchestration/review_iterator.py` | 95% |
| `orchestration/execution_loop.py` | 94% |
| `orchestration/parallel_executor.py` | 92% |
| `workflow/stages.py` | 100% |
| `workflow/state_machine.py` | 96% |

## Linting

```bash
# Check for issues
uv run ruff check .

# Auto-fix issues
uv run ruff check . --fix

# Format code
uv run ruff format .
```

## Dependencies

### Runtime

| Package | Purpose |
|---------|---------|
| `github-copilot-sdk` | GitHub Copilot SDK for AI agent execution |
| `python-frontmatter` | YAML frontmatter parsing |
| `rich` | Console UI and formatting |
| `textual` | Split-pane terminal interface |

### External

| Tool | Purpose |
|------|---------|
| [uv](https://github.com/astral-sh/uv) | Package management |
| [GitHub CLI](https://cli.github.com/) | Authentication (optional) |

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run `uv run pytest` and `uv run ruff check .`
5. Open a Pull Request

### Guidelines

- Add tests for new functionality
- Follow existing code patterns
- Update documentation for user-facing changes
- Keep commits focused and well-described

---

## Next Steps

- [Getting Started](getting-started.md) - Using TeamBot
- [Architecture](architecture.md) - Internal architecture and design
- [Configuration](configuration.md) - Configuration details
- [Workflow Stages](workflow-stages.md) - Understanding the workflow
