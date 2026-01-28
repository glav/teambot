<!-- markdownlint-disable-file -->
# Task Details: Split-Pane Terminal Interface

## Research Reference

**Source Research**: .agent-tracking/research/20260128-split-pane-interface-research.md
**Test Strategy**: .agent-tracking/test-strategies/20260128-split-pane-interface-test-strategy.md
**Feature Spec**: docs/feature-specs/split-pane-interface.md

---

## Phase 1: Setup & Dependencies

### Task 1.1: Add Textual dependency to pyproject.toml

Add the Textual framework as a project dependency and textual[dev] as a dev dependency.

* **Files**:
  * `pyproject.toml` - Add textual to dependencies and textual[dev] to dev dependencies
* **Success**:
  * `uv sync` completes without error
  * `uv run python -c "import textual"` succeeds
* **Research References**:
  * .agent-tracking/research/20260128-split-pane-interface-research.md (Lines 329-338) - Configuration examples
* **Dependencies**:
  * None

**Implementation**:
```toml
# In pyproject.toml, update dependencies section:
dependencies = [
  "python-dotenv>=1.0.0",
  "python-frontmatter>=1.0.0",
  "rich>=13.0.0",
  "github-copilot-sdk==0.1.16",
  "textual>=0.47.0",  # NEW: Split-pane UI framework
]

# In dev dependency group:
[dependency-groups]
dev = [
  "ruff>=0.8.0",
  "pytest>=7.4.0",
  "pytest-cov>=4.1.0",
  "pytest-mock>=3.12.0",
  "pytest-asyncio>=0.23.0",
  "textual[dev]>=0.47.0",  # NEW: Includes pilot for testing
]
```

---

### Task 1.2: Create ui module directory structure

Create the new `ui` module under `src/teambot/` and corresponding test directory.

* **Files**:
  * `src/teambot/ui/__init__.py` - Module exports
  * `src/teambot/ui/app.py` - Placeholder for TeamBotApp
  * `src/teambot/ui/widgets/__init__.py` - Widget exports
  * `src/teambot/ui/widgets/input_pane.py` - Placeholder
  * `src/teambot/ui/widgets/output_pane.py` - Placeholder
  * `src/teambot/ui/styles.css` - Placeholder stylesheet
  * `tests/test_ui/__init__.py` - Test module
  * `tests/test_ui/conftest.py` - Textual test fixtures
* **Success**:
  * All directories and files created
  * Module can be imported: `from teambot.ui import TeamBotApp`
* **Research References**:
  * .agent-tracking/research/20260128-split-pane-interface-research.md (Lines 372-383) - Module structure
* **Dependencies**:
  * Task 1.1 completion

**Directory Structure**:
```
src/teambot/ui/
├── __init__.py           # Exports: TeamBotApp, InputPane, OutputPane
├── app.py                # TeamBotApp class (placeholder)
├── widgets/
│   ├── __init__.py       # Exports: InputPane, OutputPane
│   ├── input_pane.py     # InputPane widget
│   └── output_pane.py    # OutputPane widget
└── styles.css            # Textual CSS

tests/test_ui/
├── __init__.py
├── conftest.py           # Textual fixtures
├── test_app.py           # App tests
├── test_input_pane.py    # InputPane tests
├── test_output_pane.py   # OutputPane tests
└── test_integration.py   # Integration tests
```

---

## Phase 2: TDD Integration Tests (Write Tests First)

### Task 2.1: Write fallback mode tests

Write TDD tests for fallback mode logic before implementation.

* **Files**:
  * `tests/test_ui/test_integration.py` - Fallback mode tests
* **Success**:
  * Tests written and collected (will fail until implementation)
  * Tests cover: narrow terminal, legacy flag, non-TTY
* **Research References**:
  * .agent-tracking/research/20260128-split-pane-interface-research.md (Lines 486-498) - Fallback logic
  * .agent-tracking/test-strategies/20260128-split-pane-interface-test-strategy.md (Lines 141-165) - Fallback test strategy
* **Dependencies**:
  * Phase 1 completion

**Test Implementation**:
```python
# tests/test_ui/test_integration.py
import pytest
from unittest.mock import patch, MagicMock
import os


class TestFallbackMode:
    """TDD tests for fallback mode - written BEFORE implementation."""

    def test_narrow_terminal_triggers_fallback(self):
        """Terminal < 80 columns should trigger legacy mode."""
        with patch("shutil.get_terminal_size") as mock_size:
            mock_size.return_value = os.terminal_size((79, 24))
            from teambot.ui.app import should_use_split_pane
            assert should_use_split_pane() is False

    def test_wide_terminal_uses_split_pane(self):
        """Terminal >= 80 columns should use split pane."""
        with patch("shutil.get_terminal_size") as mock_size:
            mock_size.return_value = os.terminal_size((80, 24))
            with patch("sys.stdout.isatty", return_value=True):
                from teambot.ui.app import should_use_split_pane
                assert should_use_split_pane() is True

    def test_legacy_mode_env_forces_fallback(self):
        """TEAMBOT_LEGACY_MODE=true should force legacy mode."""
        with patch.dict(os.environ, {"TEAMBOT_LEGACY_MODE": "true"}):
            from teambot.ui.app import should_use_split_pane
            assert should_use_split_pane() is False

    def test_non_tty_triggers_fallback(self):
        """Non-TTY terminal should trigger fallback."""
        with patch("sys.stdout.isatty", return_value=False):
            from teambot.ui.app import should_use_split_pane
            assert should_use_split_pane() is False
```

---

### Task 2.2: Write command routing integration tests

Write TDD tests for command routing from Input to Router.

* **Files**:
  * `tests/test_ui/test_integration.py` - Command routing tests
* **Success**:
  * Tests written for agent and system commands
  * Tests verify correct handler is called
* **Research References**:
  * .agent-tracking/research/20260128-split-pane-interface-research.md (Lines 500-523) - Router integration
  * .agent-tracking/test-strategies/20260128-split-pane-interface-test-strategy.md (Lines 115-135) - Integration TDD
* **Dependencies**:
  * Phase 1 completion

**Test Implementation**:
```python
class TestCommandRouting:
    """TDD tests for command routing - written BEFORE implementation."""

    @pytest.fixture
    def mock_executor(self):
        """Create mock executor."""
        executor = MagicMock()
        executor.execute = AsyncMock(return_value=MagicMock(
            success=True,
            output="Task completed",
            task_id="task-1"
        ))
        return executor

    @pytest.fixture
    def mock_router(self):
        """Create mock router."""
        router = MagicMock()
        router.route_system = AsyncMock(return_value="Status output")
        return router

    @pytest.mark.asyncio
    async def test_agent_command_routes_to_executor(self, mock_executor, mock_router):
        """@agent command should route to TaskExecutor."""
        from teambot.ui.app import TeamBotApp
        
        app = TeamBotApp(executor=mock_executor, router=mock_router)
        async with app.run_test() as pilot:
            await pilot.type("@pm create plan")
            await pilot.press("enter")
            await pilot.pause()
        
        mock_executor.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_system_command_routes_to_router(self, mock_executor, mock_router):
        """/command should route to system commands."""
        from teambot.ui.app import TeamBotApp
        
        app = TeamBotApp(executor=mock_executor, router=mock_router)
        async with app.run_test() as pilot:
            await pilot.type("/status")
            await pilot.press("enter")
            await pilot.pause()
        
        mock_router.route_system.assert_called_once()
```

---

### Task 2.3: Write task callback integration tests

Write TDD tests for TaskExecutor callback integration.

* **Files**:
  * `tests/test_ui/test_integration.py` - Callback tests
* **Success**:
  * Tests written for on_task_completed callback
  * Tests verify output appears in OutputPane
* **Research References**:
  * .agent-tracking/research/20260128-split-pane-interface-research.md (Lines 420-426) - Callback pattern
  * .agent-tracking/test-strategies/20260128-split-pane-interface-test-strategy.md (Lines 200-225) - Callback tests
* **Dependencies**:
  * Phase 1 completion

**Test Implementation**:
```python
class TestTaskCallbacks:
    """TDD tests for task callbacks - written BEFORE implementation."""

    @pytest.mark.asyncio
    async def test_task_completion_writes_to_output(self):
        """Task completion callback should write to output pane."""
        from teambot.ui.app import TeamBotApp
        from unittest.mock import MagicMock
        
        mock_executor = MagicMock()
        callback_holder = {}
        
        def capture_callback(cb):
            callback_holder['on_complete'] = cb
        
        mock_executor.set_on_task_completed = capture_callback
        
        app = TeamBotApp(executor=mock_executor)
        async with app.run_test() as pilot:
            # Simulate task completion
            mock_task = MagicMock(agent_id="pm", id="task-1")
            await callback_holder['on_complete'](mock_task, "Plan created")
            
            output = app.query_one("#output")
            # Verify output contains the result
            assert "Plan created" in str(output)

    @pytest.mark.asyncio
    async def test_task_failure_shows_error(self):
        """Task failure should show error in output pane."""
        from teambot.ui.app import TeamBotApp
        
        # Similar pattern for error handling
        pass
```

---

## Phase 3: Core Widget Implementation (Code-First)

### Task 3.1: Implement TeamBotApp main application class

Implement the main Textual application with split-pane layout.

* **Files**:
  * `src/teambot/ui/app.py` - TeamBotApp implementation
  * `src/teambot/ui/__init__.py` - Update exports
* **Success**:
  * App can be instantiated
  * Both panes render on startup
  * CSS layout applied correctly
* **Research References**:
  * .agent-tracking/research/20260128-split-pane-interface-research.md (Lines 260-310) - Textual app example
  * .agent-tracking/research/20260128-split-pane-interface-research.md (Lines 398-426) - App implementation
* **Dependencies**:
  * Phase 2 tests written

**Implementation**:
```python
# src/teambot/ui/app.py
from datetime import datetime
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static
from textual import on

from teambot.ui.widgets import InputPane, OutputPane
from teambot.repl.parser import parse_command, CommandType


def should_use_split_pane() -> bool:
    """Check if split-pane mode should be used."""
    import os
    import shutil
    import sys
    
    # Check legacy mode flag
    if os.environ.get("TEAMBOT_LEGACY_MODE", "").lower() == "true":
        return False
    
    # Check TTY
    if not sys.stdout.isatty():
        return False
    
    # Check terminal width
    size = shutil.get_terminal_size()
    if size.columns < 80:
        return False
    
    return True


class TeamBotApp(App):
    """Split-pane terminal interface for TeamBot."""
    
    CSS_PATH = Path(__file__).parent / "styles.css"
    
    def __init__(self, executor=None, router=None, **kwargs):
        super().__init__(**kwargs)
        self._executor = executor
        self._router = router
        
        # Register callbacks
        if self._executor:
            self._executor.set_on_task_completed(self._handle_task_complete)
    
    def compose(self) -> ComposeResult:
        """Create the split-pane layout."""
        with Horizontal():
            with Vertical(id="input-pane"):
                yield Static("[bold green]TeamBot[/bold green]", id="header")
                yield InputPane(placeholder="@agent task or /command", id="prompt")
            yield OutputPane(id="output", highlight=True, markup=True)
    
    @on(InputPane.Submitted)
    async def handle_input(self, event) -> None:
        """Handle submitted input from InputPane."""
        command_text = event.value.strip()
        if not command_text:
            event.input.clear()
            return
        
        output = self.query_one("#output", OutputPane)
        
        # Echo command
        output.write_command(command_text)
        
        # Parse and route
        command = parse_command(command_text)
        
        if command.type == CommandType.AGENT:
            await self._handle_agent_command(command)
        elif command.type == CommandType.SYSTEM:
            await self._handle_system_command(command)
        else:
            output.write_info("Tip: Use @agent for tasks or /help for commands")
        
        event.input.clear()
    
    async def _handle_agent_command(self, command):
        """Route agent command to executor."""
        if self._executor:
            await self._executor.execute(command)
    
    async def _handle_system_command(self, command):
        """Route system command to router."""
        output = self.query_one("#output", OutputPane)
        
        if command.name == "clear":
            output.clear()
            return
        
        if self._router:
            result = await self._router.route_system(command)
            output.write(result)
    
    async def _handle_task_complete(self, task, result):
        """Callback from TaskExecutor when task completes."""
        output = self.query_one("#output", OutputPane)
        output.write_task_complete(task.agent_id, result)
```

---

### Task 3.2: Implement OutputPane widget

Implement the output pane widget with auto-scroll and timestamps.

* **Files**:
  * `src/teambot/ui/widgets/output_pane.py` - OutputPane implementation
  * `src/teambot/ui/widgets/__init__.py` - Update exports
* **Success**:
  * Messages display with timestamps
  * Auto-scroll to bottom on new content
  * Status indicators (✓, ✗, ℹ) render correctly
* **Research References**:
  * .agent-tracking/research/20260128-split-pane-interface-research.md (Lines 546-561) - OutputPane example
* **Dependencies**:
  * Task 3.1

**Implementation**:
```python
# src/teambot/ui/widgets/output_pane.py
from datetime import datetime
from textual.widgets import RichLog


class OutputPane(RichLog):
    """Output pane with timestamps and status indicators."""
    
    def write_command(self, command: str) -> None:
        """Write echoed command."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.write(f"[dim]{timestamp}[/dim] [bold]>[/bold] {command}")
        self.scroll_end()
    
    def write_task_complete(self, agent_id: str, result: str) -> None:
        """Write task completion message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.write(f"[dim]{timestamp}[/dim] [green]✓[/green] @{agent_id}: {result}")
        self.scroll_end()
    
    def write_task_error(self, agent_id: str, error: str) -> None:
        """Write task error message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.write(f"[dim]{timestamp}[/dim] [red]✗[/red] @{agent_id}: {error}")
        self.scroll_end()
    
    def write_info(self, message: str) -> None:
        """Write info message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.write(f"[dim]{timestamp}[/dim] [blue]ℹ[/blue] {message}")
        self.scroll_end()
    
    def write_system(self, output: str) -> None:
        """Write system command output."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.write(f"[dim]{timestamp}[/dim]\n{output}")
        self.scroll_end()
```

---

### Task 3.3: Implement InputPane widget with command history

Implement the input pane widget with command history navigation.

* **Files**:
  * `src/teambot/ui/widgets/input_pane.py` - InputPane implementation
  * `src/teambot/ui/widgets/__init__.py` - Update exports
* **Success**:
  * Up/down arrows navigate command history
  * Input cleared after submission
  * History persists across submissions
* **Research References**:
  * .agent-tracking/research/20260128-split-pane-interface-research.md (Lines 565-581) - InputPane example
* **Dependencies**:
  * Task 3.1

**Implementation**:
```python
# src/teambot/ui/widgets/input_pane.py
from textual.widgets import Input
from textual.events import Key


class InputPane(Input):
    """Input pane with command history navigation."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._history: list[str] = []
        self._history_index: int = -1
        self._current_input: str = ""
    
    def on_input_submitted(self, event) -> None:
        """Store submitted input in history."""
        if event.value.strip():
            self._history.append(event.value)
        self._history_index = -1
        self._current_input = ""
    
    def on_key(self, event: Key) -> None:
        """Handle up/down arrow for history navigation."""
        if event.key == "up":
            self._navigate_history(-1)
            event.prevent_default()
        elif event.key == "down":
            self._navigate_history(1)
            event.prevent_default()
    
    def _navigate_history(self, direction: int) -> None:
        """Navigate through command history."""
        if not self._history:
            return
        
        # Save current input when starting navigation
        if self._history_index == -1:
            self._current_input = self.value
        
        # Calculate new index
        new_index = self._history_index + direction
        
        if new_index < -1:
            new_index = -1
        elif new_index >= len(self._history):
            new_index = len(self._history) - 1
        
        self._history_index = new_index
        
        # Update input value
        if self._history_index == -1:
            self.value = self._current_input
        else:
            # Navigate from end of history
            self.value = self._history[-(self._history_index + 1)]
```

---

### Task 3.4: Create CSS stylesheet for layout

Create the Textual CSS file for split-pane layout.

* **Files**:
  * `src/teambot/ui/styles.css` - Layout styles
* **Success**:
  * Left pane 30%, right pane 70%
  * Minimum widths respected
  * Borders and padding applied
* **Research References**:
  * .agent-tracking/research/20260128-split-pane-interface-research.md (Lines 428-449) - CSS styles
* **Dependencies**:
  * Task 3.1

**Implementation**:
```css
/* src/teambot/ui/styles.css */

Screen {
    layout: horizontal;
}

Horizontal {
    height: 100%;
}

#input-pane {
    width: 30%;
    min-width: 25;
    border: solid $primary;
    padding: 1;
}

#header {
    dock: top;
    height: 1;
    padding: 0 1;
}

#prompt {
    dock: bottom;
}

#output {
    width: 70%;
    border: solid $secondary;
    padding: 0 1;
}
```

---

## Phase 4: Integration with Existing REPL

### Task 4.1: Integrate with command parser and router

Connect TeamBotApp to existing `parse_command()` and `AgentRouter`.

* **Files**:
  * `src/teambot/ui/app.py` - Update handle_input method
* **Success**:
  * Commands parsed correctly
  * Agent commands route to executor
  * System commands route to router
* **Research References**:
  * .agent-tracking/research/20260128-split-pane-interface-research.md (Lines 500-523) - Router integration
* **Dependencies**:
  * Phase 3 completion

**Implementation Notes**:
- Import `parse_command` from `teambot.repl.parser`
- Import `CommandType` enum for routing decisions
- Use existing `AgentRouter` for system commands
- Handle `CommandType.RAW` with helpful tip message

---

### Task 4.2: Integrate TaskExecutor callbacks with OutputPane

Wire TaskExecutor's `on_task_completed` callback to OutputPane.

* **Files**:
  * `src/teambot/ui/app.py` - Update callback registration
  * `src/teambot/tasks/executor.py` - May need to expose callback setter
* **Success**:
  * Task completion appears in output pane
  * Error messages appear for failed tasks
  * Callback is async-safe
* **Research References**:
  * .agent-tracking/research/20260128-split-pane-interface-research.md (Lines 420-426) - Callback pattern
* **Dependencies**:
  * Task 4.1

**Implementation Notes**:
- TaskExecutor may need `set_on_task_completed(callback)` method
- Callback receives (task, result) parameters
- Use `call_from_thread` if callback is from non-Textual context

---

### Task 4.3: Add /clear command for output pane

Add the `/clear` command to clear the output pane.

* **Files**:
  * `src/teambot/ui/app.py` - Handle /clear in system commands
  * `src/teambot/repl/commands.py` - May need to register /clear
* **Success**:
  * `/clear` clears output pane content
  * Input pane unaffected
  * Command echoed before clear
* **Research References**:
  * .agent-tracking/test-strategies/20260128-split-pane-interface-test-strategy.md (Lines 170-180) - /clear tests
* **Dependencies**:
  * Task 4.1

**Implementation**:
```python
# In TeamBotApp._handle_system_command()
if command.name == "clear":
    output = self.query_one("#output", OutputPane)
    output.clear()
    return
```

---

### Task 4.4: Update loop.py entry point with fallback logic

Update `run_interactive_mode()` to choose between Textual and legacy mode.

* **Files**:
  * `src/teambot/repl/loop.py` - Update entry point
* **Success**:
  * `should_use_split_pane()` determines mode
  * Textual app launched when appropriate
  * Legacy REPL used as fallback
  * Feature flag support via `TEAMBOT_SPLIT_PANE`
* **Research References**:
  * .agent-tracking/research/20260128-split-pane-interface-research.md (Lines 486-498) - Entry point
* **Dependencies**:
  * Tasks 4.1, 4.2, 4.3

**Implementation**:
```python
# src/teambot/repl/loop.py

def run_interactive_mode(console=None, enable_overlay=True):
    """Entry point - chooses Textual or legacy mode."""
    import os
    
    # Check if split-pane is explicitly enabled
    split_pane_flag = os.environ.get("TEAMBOT_SPLIT_PANE", "").lower() == "true"
    
    # Import here to avoid circular imports
    from teambot.ui.app import TeamBotApp, should_use_split_pane
    
    if split_pane_flag or should_use_split_pane():
        # Use new Textual interface
        from teambot.repl.router import create_router
        from teambot.tasks.executor import TaskExecutor
        from teambot.copilot.sdk_client import CopilotSDKClient
        
        sdk_client = CopilotSDKClient()
        executor = TaskExecutor(sdk_client=sdk_client)
        router = create_router()
        
        app = TeamBotApp(executor=executor, router=router)
        app.run()
    else:
        # Legacy mode with overlay
        loop = REPLLoop(console=console, enable_overlay=enable_overlay)
        asyncio.run(loop.run())
```

---

## Phase 5: Widget Tests (Code-First Test Phase)

### Task 5.1: Add TeamBotApp pilot tests

Add tests for TeamBotApp using Textual's pilot test driver.

* **Files**:
  * `tests/test_ui/test_app.py` - App tests
* **Success**:
  * App launches and displays both panes
  * Input submission handled correctly
  * 85% coverage achieved
* **Research References**:
  * .agent-tracking/test-strategies/20260128-split-pane-interface-test-strategy.md (Lines 380-420) - App test patterns
* **Dependencies**:
  * Phase 4 completion

**Test Implementation**:
```python
# tests/test_ui/test_app.py
import pytest
from teambot.ui.app import TeamBotApp


class TestTeamBotApp:
    """Tests for TeamBotApp main application."""

    @pytest.mark.asyncio
    async def test_app_displays_both_panes(self):
        """App shows input and output panes."""
        app = TeamBotApp()
        async with app.run_test() as pilot:
            assert app.query_one("#input-pane") is not None
            assert app.query_one("#output") is not None

    @pytest.mark.asyncio
    async def test_input_echoed_to_output(self):
        """Submitted input appears in output pane."""
        app = TeamBotApp()
        async with app.run_test() as pilot:
            await pilot.type("@pm test")
            await pilot.press("enter")
            await pilot.pause()
            
            output = app.query_one("#output")
            # Check output contains the command
            assert "@pm test" in str(output)

    @pytest.mark.asyncio
    async def test_input_cleared_after_submit(self):
        """Input field cleared after submission."""
        app = TeamBotApp()
        async with app.run_test() as pilot:
            await pilot.type("@pm test")
            await pilot.press("enter")
            await pilot.pause()
            
            input_pane = app.query_one("#prompt")
            assert input_pane.value == ""
```

---

### Task 5.2: Add InputPane pilot tests

Add tests for InputPane command history navigation.

* **Files**:
  * `tests/test_ui/test_input_pane.py` - InputPane tests
* **Success**:
  * History navigation works correctly
  * Edge cases handled (empty history, boundaries)
  * 80% coverage achieved
* **Research References**:
  * .agent-tracking/test-strategies/20260128-split-pane-interface-test-strategy.md (Lines 105-120) - InputPane tests
* **Dependencies**:
  * Task 5.1

**Test Implementation**:
```python
# tests/test_ui/test_input_pane.py
import pytest
from teambot.ui.widgets.input_pane import InputPane


class TestInputPane:
    """Tests for InputPane widget."""

    @pytest.mark.asyncio
    async def test_history_navigation_up(self):
        """Up arrow shows previous command."""
        # Test implementation using pilot
        pass

    @pytest.mark.asyncio
    async def test_history_navigation_down(self):
        """Down arrow shows next command."""
        pass

    @pytest.mark.asyncio
    async def test_empty_history_no_crash(self):
        """Up arrow with empty history doesn't crash."""
        pass
```

---

### Task 5.3: Add OutputPane pilot tests

Add tests for OutputPane message display and scrolling.

* **Files**:
  * `tests/test_ui/test_output_pane.py` - OutputPane tests
* **Success**:
  * Messages display with correct format
  * Timestamps present
  * Status indicators correct
  * 80% coverage achieved
* **Research References**:
  * .agent-tracking/test-strategies/20260128-split-pane-interface-test-strategy.md (Lines 125-140) - OutputPane tests
* **Dependencies**:
  * Task 5.1

**Test Implementation**:
```python
# tests/test_ui/test_output_pane.py
import pytest
from teambot.ui.widgets.output_pane import OutputPane


class TestOutputPane:
    """Tests for OutputPane widget."""

    def test_write_task_complete_format(self):
        """Task completion has correct format."""
        # Test message formatting
        pass

    def test_write_task_error_format(self):
        """Task error has correct format."""
        pass

    def test_timestamp_present(self):
        """All messages have timestamps."""
        pass
```

---

## Phase 6: Validation & Cleanup

### Task 6.1: Validate test coverage meets targets

Run coverage report and verify targets are met.

* **Files**:
  * None (validation only)
* **Success**:
  * Unit coverage >= 85% for ui module
  * Integration coverage >= 90%
  * All tests pass
* **Research References**:
  * .agent-tracking/test-strategies/20260128-split-pane-interface-test-strategy.md (Lines 230-250) - Coverage targets
* **Dependencies**:
  * Phase 5 completion

**Validation Command**:
```bash
uv run pytest tests/test_ui/ --cov=src/teambot/ui --cov-report=term-missing --cov-report=html
```

**Expected Output**:
- `src/teambot/ui/app.py` >= 85%
- `src/teambot/ui/widgets/input_pane.py` >= 80%
- `src/teambot/ui/widgets/output_pane.py` >= 80%
- `tests/test_ui/test_integration.py` >= 90%

---

### Task 6.2: Manual terminal testing

Perform manual testing in target terminals.

* **Files**:
  * None (manual testing)
* **Success**:
  * VS Code terminal: split pane displays correctly
  * Narrow terminal: fallback mode activates
  * Commands route correctly
  * Output appears asynchronously
* **Research References**:
  * docs/feature-specs/split-pane-interface.md - NFR-SPI-004 terminal compatibility
* **Dependencies**:
  * Task 6.1

**Test Checklist**:
- [ ] VS Code integrated terminal (80+ columns)
- [ ] VS Code terminal (narrow < 80 columns for fallback)
- [ ] Submit `@pm create plan` - verify output appears
- [ ] Submit `/status` - verify status displays in output
- [ ] Submit `/clear` - verify output clears
- [ ] Press up arrow - verify history navigation
- [ ] Resize terminal - verify layout adjusts

---

## Dependencies

* Python >= 3.10
* Textual >= 0.47.0
* Rich >= 13.0.0
* pytest >= 7.4.0
* pytest-asyncio >= 0.23.0
* textual[dev] >= 0.47.0

## Success Criteria

* All Phase 2 TDD tests pass after implementation
* All Phase 5 widget tests pass
* Coverage meets targets (85% unit, 90% integration)
* Manual testing passes on VS Code terminal
* Fallback mode works for narrow terminals
* Existing tests continue to pass
