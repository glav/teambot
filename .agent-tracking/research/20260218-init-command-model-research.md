<!-- markdownlint-disable-file -->
# Research: Init Command Model Configuration and Prerequisites

**Date**: 2026-02-18  
**Feature**: Fix Init Command Model Configuration and Prerequisites  
**Status**: ✅ Research Complete

---

## 📋 Research Scope

### Objective
Research implementation approach for enhancing the `teambot init` command to:
1. Update default model from `claude-sonnet-4` to `claude-sonnet-4.5`
2. Add explicit `model` field to each agent in default config
3. Automatically refresh model cache during `teambot init`
4. Check Copilot CLI authentication status during init
5. Display configurable "Recommended Next Steps" guidance after init

### Success Criteria
- [x] Technical approach validated
- [x] Code patterns documented
- [x] Entry points analyzed
- [x] Test infrastructure researched
- [x] Implementation guidance ready

---

## 🎯 Entry Point Analysis

### User Input Entry Points

| Entry Point | Code Path | Reaches Feature? | Implementation Required? |
|-------------|-----------|------------------|-------------------------|
| `teambot init` | `cli.py:main()` → `cmd_init()` | ✅ YES | ✅ YES (primary) |
| `teambot init --force` | `cli.py:main()` → `cmd_init()` | ✅ YES | ✅ YES |

### Code Path Trace

#### Entry Point 1: `teambot init`
1. User enters: `teambot init`
2. Handled by: `cli.py:main()` (lines 629-656)
3. Routes to: `cli.py:cmd_init()` (lines 190-252)
4. Calls: `config/loader.py:create_default_config()` (lines 33-97)
5. **Coverage**: All implementation changes are in this path ✅

### Coverage Gaps
| Gap | Impact | Required Fix |
|-----|--------|--------------|
| None identified | N/A | N/A |

### Implementation Scope Verification
- [x] All entry points from acceptance test scenarios are traced
- [x] All code paths that should trigger feature are identified
- [x] Coverage gaps are documented with required fixes

---

## 🔬 Technical Findings

### Finding 1: Default Config Structure

**Source**: `src/teambot/config/loader.py` (Lines 33-97)

**Current Implementation**:
```python
def create_default_config() -> dict[str, Any]:
    """Create default configuration with MVP agents."""
    return {
        "teambot_dir": ".teambot",
        "default_model": "claude-sonnet-4",  # ❌ Needs update to claude-sonnet-4.5
        "default_agent": "pm",
        "agents": [
            {
                "id": "pm",
                "persona": "project_manager",
                "display_name": "Project Manager",
                "parallel_capable": False,
                "workflow_stages": ["setup", "planning", "coordination"],
                # ❌ Missing explicit "model" field
            },
            # ... more agents
        ],
        # ...
    }
```

**Required Changes**:
1. Change `"default_model": "claude-sonnet-4"` → `"default_model": "claude-sonnet-4.5"`
2. Add `"model": "claude-sonnet-4.5"` to each agent definition

**Evidence**: Model `claude-sonnet-4.5` is validated in existing tests:
- `tests/test_config/test_schema.py` (Line 33): `"claude-sonnet-4.5"` is in mock cache

---

### Finding 2: Model Cache Refresh Implementation

**Source**: `src/teambot/config/schema.py` (Lines 142-196)

**Existing `refresh_models()` Function**:
```python
async def refresh_models() -> bool:
    """Refresh model cache from SDK.
    
    Fetches models from SDK and updates cache. This is async
    because SDK operations are async.
    
    Returns:
        True if refresh succeeded, False otherwise.
    """
    # ... implementation
```

**Key Implementation Details**:
- Function is `async` - requires `asyncio.run()` wrapper for sync context
- Creates `CopilotSDKClient`, calls `start()`, `list_models()`, `stop()`
- Saves to cache via `model_cache.save_cache()`
- Returns `bool` success status
- Gracefully handles SDK unavailability (returns `False`)

**REPL Usage Pattern** (for reference):
- `src/teambot/repl/commands.py` (Lines 289-319) - `_handle_models_refresh()`

**Implementation for `cmd_init()`**:
```python
# In cmd_init(), after create_default_config():
async def _refresh_model_cache() -> bool:
    from teambot.config.schema import refresh_models
    return await refresh_models()

try:
    success = asyncio.run(_refresh_model_cache())
    if success:
        display.print_success("Model cache refreshed")
    else:
        display.print_warning("Could not refresh model cache - continue anyway")
except Exception:
    display.print_warning("Model cache refresh failed - continue anyway")
```

---

### Finding 3: Authentication Check Implementation

**Source**: `src/teambot/copilot/sdk_client.py` (Lines 194-215)

**Existing Authentication Check**:
```python
async def _check_auth(self) -> None:
    """Check and store authentication status."""
    if not self._client:
        return
    try:
        status = await self._client.get_auth_status()
        if isinstance(status, dict):
            self._authenticated = status.get("isAuthenticated", False)
        else:
            self._authenticated = getattr(status, "isAuthenticated", False)
    except Exception:
        self._authenticated = False

def is_authenticated(self) -> bool:
    """Check if Copilot is authenticated."""
    return self._authenticated
```

**REPL Authentication Check Pattern** (for reference):
- `src/teambot/repl/loop.py` (Lines 249-258)

**Recommended Implementation for `cmd_init()`**:
```python
async def _check_copilot_auth() -> tuple[bool, str | None]:
    """Check Copilot authentication status.
    
    Returns:
        Tuple of (is_authenticated, error_message_if_any)
    """
    from teambot.copilot.sdk_client import CopilotSDKClient, SDKClientError
    
    client = CopilotSDKClient()
    if not client.is_available():
        return False, "SDK not available"
    
    try:
        await client.start()
        is_auth = client.is_authenticated()
        await client.stop()
        return is_auth, None
    except SDKClientError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)
```

**Display Guidance** (from existing code pattern):
- `cli.py` (Line 48): `display.print_warning("After installing, authenticate with: copilot auth")`
- `repl/loop.py` (Lines 254-257): Multi-line guidance for unauthenticated state

---

### Finding 4: ConsoleDisplay Methods

**Source**: `src/teambot/visualization/console.py` (Lines 205-250+)

**Available Methods**:
```python
class ConsoleDisplay:
    def print_success(self, message: str) -> None  # Green ✓ prefix
    def print_error(self, message: str) -> None    # Red ✗ prefix
    def print_warning(self, message: str) -> None  # Yellow ⚠ prefix
    def print_info(self, message: str) -> None     # Cyan ℹ prefix
    def print_header(self, title: str) -> None     # Section header
```

**Usage Pattern for "Next Steps" Display**:
```python
display.print_info("")
display.print_info("=== Recommended Next Steps ===")
display.print_info("1. Configure per-agent models for better quality")
display.print_info("2. Run 'teambot run objectives/your-task.md'")
```

---

### Finding 5: Configurable Text from Package Files

**Source**: `src/teambot/scaffolds.py` (Lines 6-32)

**Pattern for Loading Bundled Files**:
```python
from importlib.resources import files

def get_scaffolds_dir() -> Path:
    """Get path to bundled scaffold files."""
    pkg = files("teambot")
    scaffolds = pkg.joinpath("scaffolds")
    if hasattr(scaffolds, "_path"):
        return Path(scaffolds._path)
    return Path(str(scaffolds))
```

**Recommended Implementation for "Next Steps" Text**:

1. **Create guidance file**: `src/teambot/scaffolds/init_guidance.md`
2. **Load at runtime**:
```python
def get_init_guidance() -> str:
    """Load post-init guidance text from package."""
    from importlib.resources import files
    
    pkg = files("teambot")
    guidance_file = pkg.joinpath("scaffolds", "init_guidance.md")
    
    if hasattr(guidance_file, "read_text"):
        return guidance_file.read_text(encoding="utf-8")
    return Path(str(guidance_file)).read_text(encoding="utf-8")
```

**Alternative**: Use `importlib.resources.read_text()` for simpler API:
```python
from importlib.resources import read_text
text = read_text("teambot.scaffolds", "init_guidance.md")
```

---

### Finding 6: Build System Configuration

**Source**: `pyproject.toml` (Lines 5-9)

**Current Include Rules**:
```toml
[tool.hatch.build.targets.wheel]
packages = ["src/teambot"]

[tool.hatch.build]
include = ["src/teambot/**/*.css", "src/teambot/scaffolds/**"]
```

**📌 Note**: The `src/teambot/scaffolds/**` pattern already includes all files in scaffolds directory. New `init_guidance.md` will be automatically included.

---

## 🏗️ Implementation Architecture

### Recommended Approach: Sequential Implementation

#### Phase 1: Update Default Configuration
- **File**: `src/teambot/config/loader.py`
- **Changes**:
  - Update `default_model` to `"claude-sonnet-4.5"`
  - Add `"model": "claude-sonnet-4.5"` to each agent in `agents` list

#### Phase 2: Add Model Cache Refresh
- **File**: `src/teambot/cli.py`
- **Location**: `cmd_init()` function, after `create_default_config()` call
- **Implementation**: Call `refresh_models()` via `asyncio.run()`, handle errors gracefully

#### Phase 3: Add Authentication Check
- **File**: `src/teambot/cli.py`  
- **Location**: `cmd_init()` function, after model cache refresh
- **Implementation**: Create helper function, display appropriate guidance

#### Phase 4: Create Guidance File
- **File**: `src/teambot/scaffolds/init_guidance.md`
- **Content**: Markdown-formatted next steps guidance

#### Phase 5: Display Post-Init Guidance
- **File**: `src/teambot/cli.py`
- **Location**: End of `cmd_init()` function, before `return 0`
- **Implementation**: Load guidance file, display via `ConsoleDisplay`

---

## 📝 Proposed Implementation Details

### 1. Updated `create_default_config()`

```python
def create_default_config() -> dict[str, Any]:
    """Create default configuration with MVP agents."""
    default_model = "claude-sonnet-4.5"  # Updated default
    
    return {
        "teambot_dir": ".teambot",
        "default_model": default_model,
        "default_agent": "pm",
        "agents": [
            {
                "id": "pm",
                "persona": "project_manager",
                "display_name": "Project Manager",
                "parallel_capable": False,
                "workflow_stages": ["setup", "planning", "coordination"],
                "model": default_model,  # ✅ Explicit model field
            },
            {
                "id": "ba",
                "persona": "business_analyst",
                "display_name": "Business Analyst",
                "parallel_capable": False,
                "workflow_stages": ["business_problem", "spec"],
                "model": default_model,
            },
            # ... repeat for all agents
        ],
        # ...
    }
```

### 2. Model Cache Refresh Helper

```python
async def _refresh_model_cache_async() -> bool:
    """Async helper to refresh model cache."""
    from teambot.config.schema import refresh_models
    return await refresh_models()


def _refresh_model_cache(display: ConsoleDisplay) -> bool:
    """Refresh model cache, displaying status.
    
    Args:
        display: Console display for output.
        
    Returns:
        True if refresh succeeded.
    """
    try:
        success = asyncio.run(_refresh_model_cache_async())
        if success:
            display.print_success("Model cache refreshed")
            return True
        else:
            display.print_warning(
                "Could not refresh model cache - models may not be available"
            )
            display.print_warning(
                "Run '/models --refresh' later to update model list"
            )
            return False
    except Exception as e:
        display.print_warning(f"Model cache refresh failed: {e}")
        display.print_warning(
            "Run '/models --refresh' later to update model list"
        )
        return False
```

### 3. Authentication Check Helper

```python
async def _check_auth_async() -> tuple[bool, str | None]:
    """Check Copilot authentication status.
    
    Returns:
        Tuple of (is_authenticated, error_message).
    """
    from teambot.copilot.sdk_client import CopilotSDKClient, SDKClientError
    
    client = CopilotSDKClient()
    if not client.is_available():
        return False, "Copilot SDK not available"
    
    try:
        await client.start()
        is_auth = client.is_authenticated()
        await client.stop()
        return is_auth, None
    except SDKClientError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)


def _check_copilot_authentication(display: ConsoleDisplay) -> bool:
    """Check and display Copilot authentication status.
    
    Args:
        display: Console display for output.
        
    Returns:
        True if authenticated.
    """
    try:
        is_auth, error = asyncio.run(_check_auth_async())
        
        if is_auth:
            display.print_success("Copilot authenticated")
            return True
        else:
            display.print_warning("Copilot not authenticated")
            if error:
                display.print_warning(f"  {error}")
            display.print_info("  Run 'copilot auth' to authenticate")
            display.print_info("  Or set GITHUB_TOKEN environment variable")
            return False
    except Exception as e:
        display.print_warning(f"Could not check authentication: {e}")
        display.print_info("Run 'copilot auth' to ensure you're authenticated")
        return False
```

### 4. Guidance File Content

**File**: `src/teambot/scaffolds/init_guidance.md`

```markdown
## Recommended Next Steps

### 1. Configure Per-Agent Models (Optional)

For better quality and cost optimization, customize models for each agent:

```json
{
  "agents": [
    {
      "id": "reviewer",
      "model": "claude-opus-4.5"  // Premium model for code review
    },
    {
      "id": "builder-1",
      "model": "gpt-5.1-codex"  // Fast model for implementation
    }
  ]
}
```

Edit `teambot.json` to set per-agent models.

### 2. Run Your First Objective

Create an objective file and run TeamBot:

```bash
teambot run objectives/your-feature.md
```

### 3. Explore Interactive Mode

Start interactive mode for ad-hoc tasks:

```bash
teambot run
```

Type `@pm help` to get started.
```

### 5. Display Guidance Function

```python
def _display_post_init_guidance(display: ConsoleDisplay) -> None:
    """Display post-init recommended next steps.
    
    Loads guidance from package file for maintainability.
    """
    try:
        from importlib.resources import files
        
        pkg = files("teambot")
        guidance_path = pkg.joinpath("scaffolds", "init_guidance.md")
        
        if hasattr(guidance_path, "read_text"):
            content = guidance_path.read_text(encoding="utf-8")
        else:
            content = Path(str(guidance_path)).read_text(encoding="utf-8")
        
        display.print_info("")
        display.print_header("Recommended Next Steps")
        
        # Parse and display content
        for line in content.strip().split("\n"):
            if line.startswith("## "):
                continue  # Skip header (already printed)
            elif line.startswith("### "):
                display.print_info("")
                display.print_info(line[4:])  # Remove ### prefix
            elif line.startswith("```"):
                continue  # Skip code fence markers
            elif line.strip():
                display.print_info(f"  {line}")
                
    except Exception:
        # Fallback to hardcoded guidance if file load fails
        display.print_info("")
        display.print_info("=== Recommended Next Steps ===")
        display.print_info("1. Edit teambot.json to configure per-agent models")
        display.print_info("2. Run 'teambot run objectives/your-task.md'")
        display.print_info("3. Use 'teambot run' for interactive mode")
```

---

## 🧪 Testing Strategy Research

### Existing Test Infrastructure

**Framework**: pytest 7.4.0+ with plugins
- **Location**: `tests/` directory
- **Naming**: `test_*.py` pattern
- **Runner**: `uv run pytest`
- **Coverage**: coverage.py with ~80% target

**Test Fixtures** (from `tests/conftest.py`):
- `temp_teambot_dir(tmp_path)` - Creates temporary `.teambot` structure
- `sample_agent_config` - Standard agent config dict
- `mock_sdk_client` - Mocked Copilot SDK client
- `mock_streaming_session` - Mock for streaming events

**Existing CLI Test Patterns** (from `tests/test_cli.py`):
```python
def test_init_creates_config(self, tmp_path, monkeypatch):
    """Init creates configuration file."""
    import argparse
    from teambot.cli import ConsoleDisplay, cmd_init
    
    monkeypatch.chdir(tmp_path)
    args = argparse.Namespace(force=False)
    display = ConsoleDisplay()
    
    result = cmd_init(args, display)
    
    assert result == 0
    assert (tmp_path / "teambot.json").exists()
```

**Model Cache Test Patterns** (from `tests/test_config/test_schema.py`):
```python
@pytest.fixture
def mock_model_cache(tmp_path, reset_model_state):
    """Create a valid model cache for testing."""
    cache_dir = tmp_path / ".teambot"
    cache_dir.mkdir()
    cache_file = cache_dir / "model_cache.json"
    cache_data = {
        "models": [
            {"id": "claude-sonnet-4.5", "name": "Claude Sonnet 4.5", "category": "standard"},
            # ...
        ],
        "timestamp": time.time(),
        "sdk_version": "1.0.0",
    }
    cache_file.write_text(json.dumps(cache_data))
    return tmp_path
```

### Required Test Cases

#### 1. Default Config Tests

```python
class TestDefaultConfigModel:
    """Tests for default model configuration."""
    
    def test_default_model_is_claude_sonnet_4_5(self):
        """Default model should be claude-sonnet-4.5."""
        from teambot.config.loader import create_default_config
        config = create_default_config()
        assert config["default_model"] == "claude-sonnet-4.5"
    
    def test_each_agent_has_explicit_model_field(self):
        """Each agent should have explicit model field."""
        from teambot.config.loader import create_default_config
        config = create_default_config()
        for agent in config["agents"]:
            assert "model" in agent, f"Agent {agent['id']} missing model field"
            assert agent["model"] == "claude-sonnet-4.5"
```

#### 2. Model Cache Refresh Tests

```python
class TestInitModelCacheRefresh:
    """Tests for model cache refresh during init."""
    
    def test_init_attempts_model_cache_refresh(self, tmp_path, monkeypatch):
        """Init should attempt to refresh model cache."""
        # Mock refresh_models to track call
        refresh_called = [False]
        async def mock_refresh():
            refresh_called[0] = True
            return True
        
        monkeypatch.setattr("teambot.config.schema.refresh_models", mock_refresh)
        monkeypatch.chdir(tmp_path)
        
        # Run init
        # ... assert refresh_called[0] is True
    
    def test_init_continues_if_refresh_fails(self, tmp_path, monkeypatch):
        """Init should continue even if model cache refresh fails."""
        async def mock_refresh_fail():
            return False
        
        monkeypatch.setattr("teambot.config.schema.refresh_models", mock_refresh_fail)
        monkeypatch.chdir(tmp_path)
        
        # Run init - should succeed with warning
        # ... assert result == 0
```

#### 3. Authentication Check Tests

```python
class TestInitAuthenticationCheck:
    """Tests for Copilot authentication check during init."""
    
    def test_init_checks_authentication(self, tmp_path, monkeypatch):
        """Init should check Copilot authentication status."""
        # ... mock SDK client
    
    def test_init_shows_auth_warning_if_not_authenticated(self, tmp_path, monkeypatch):
        """Init should show warning if not authenticated."""
        # ... verify warning message displayed
    
    def test_init_continues_if_auth_check_fails(self, tmp_path, monkeypatch):
        """Init should continue even if auth check fails."""
        # ... assert init succeeds with warning
```

#### 4. Guidance Display Tests

```python
class TestInitGuidanceDisplay:
    """Tests for post-init guidance display."""
    
    def test_init_displays_next_steps(self, tmp_path, monkeypatch, capsys):
        """Init should display recommended next steps."""
        # ... verify guidance is printed
    
    def test_guidance_loaded_from_file(self):
        """Guidance should be loaded from scaffolds file."""
        from teambot.scaffolds import get_scaffolds_dir
        guidance_file = get_scaffolds_dir() / "init_guidance.md"
        assert guidance_file.exists()
```

### Testing Approach Recommendation

| Component | Approach | Rationale |
|-----------|----------|-----------|
| Default config changes | Code-First | Simple, low risk |
| Model cache refresh | TDD | Complex async, multiple failure modes |
| Authentication check | TDD | Complex async, error handling critical |
| Guidance loading | Code-First | Simple file loading |
| Integration (full init) | Code-First | Test existing behavior preserved |

---

## ⚠️ Potential Pitfalls

### 1. Async in Sync Context
**Issue**: `refresh_models()` and SDK auth checks are async
**Mitigation**: Use `asyncio.run()` wrapper, handle exceptions

### 2. SDK Not Available
**Issue**: SDK may not be installed/available
**Mitigation**: Check `client.is_available()` before operations, fail gracefully

### 3. Network Failures
**Issue**: Model refresh requires network connectivity
**Mitigation**: Wrap in try/except, display warning, continue init

### 4. Test Isolation
**Issue**: Model cache uses global state
**Mitigation**: Use `reset_model_cache()` fixture, mock `Path.cwd()`

### 5. Package File Access
**Issue**: `importlib.resources` API differs between Python versions
**Mitigation**: Use pattern from `scaffolds.py` with `hasattr()` checks

---

## 📋 Task Implementation Requests

### Implementation Tasks

1. **Update `create_default_config()` in `loader.py`**
   - Change `default_model` to `"claude-sonnet-4.5"`
   - Add `"model"` field to each agent

2. **Create `_refresh_model_cache()` helper in `cli.py`**
   - Async wrapper for `refresh_models()`
   - Display success/warning messages
   - Handle exceptions gracefully

3. **Create `_check_copilot_authentication()` helper in `cli.py`**
   - Use `CopilotSDKClient` to check auth status
   - Display appropriate guidance for unauthenticated users

4. **Create `init_guidance.md` in `scaffolds/`**
   - Markdown-formatted next steps content
   - Maintainable/editable outside code

5. **Create `_display_post_init_guidance()` in `cli.py`**
   - Load guidance from package file
   - Fallback to hardcoded if load fails

6. **Update `cmd_init()` to call new functions**
   - Add model cache refresh after config creation
   - Add auth check after model refresh
   - Add guidance display before return

7. **Add tests for new functionality**
   - Test default config changes
   - Test model cache refresh behavior
   - Test authentication check behavior
   - Test guidance display

---

## 🔄 Potential Next Research

| Topic | Priority | Notes |
|-------|----------|-------|
| SDK auth flow details | Low | Current implementation sufficient |
| Model cache TTL optimization | Low | Out of scope for this feature |

---

## ✅ Research Validation

```
RESEARCH_VALIDATION: PASS
- Document: CREATED ✅
- Placeholders: 0 remaining ✅
- Technical Approach: DOCUMENTED ✅
- Entry Points: 1 traced, 1 covered ✅
- Test Infrastructure: RESEARCHED ✅
- Implementation Ready: YES ✅
```
