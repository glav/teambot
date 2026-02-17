# Research Summary: Map Repo Files to Package Location

**Full Research Document**: `.agent-tracking/research/20260217-map-repo-files-research.md`

## Executive Summary

Research complete for enhancing `teambot init` to automatically copy scaffolding files from the installed package to user repositories.

## Selected Approach

| Component | Solution |
|-----------|----------|
| **Package Bundling** | Hatchling `force-include` in pyproject.toml |
| **File Access** | `importlib.resources.files()` (Python 3.10+ standard) |
| **Copy Logic** | New `src/teambot/scaffolds.py` module |
| **Integration** | Extend `cmd_init()` in `src/teambot/cli.py` |

## Files to Bundle (~372K total)

- `stages.yaml` (16K) → `stages.yaml`
- `AGENTS.md` (8K) → `AGENTS.md`
- `docs/sdd-objective-template.md` (4K) → `docs/sdd-objective-template.md`
- `.github/agents/` (28K, 6 files) → `.github/agents/`
- `.agent/` (316K, ~28 files) → `.agent/`

## Key Implementation Tasks

1. **Update pyproject.toml** - Add `force-include` for scaffold bundling
2. **Create scaffolds.py** - New module for scaffold file management
3. **Update cli.py** - Integrate scaffold copying into `cmd_init()`
4. **Create tests** - TDD for scaffolds module, extend CLI tests

## Testing Approach

- **TDD** for `scaffolds.py` module (well-defined requirements)
- **Code-First** for CLI integration (simple extension)
- Use existing patterns: `tmp_path`, `monkeypatch.chdir()`

## Exit Criteria Met

✅ Research document with implementation recommendations
✅ Technical approach validated
✅ Entry point analysis complete
✅ Test infrastructure researched
