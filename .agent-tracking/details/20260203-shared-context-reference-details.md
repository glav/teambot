<!-- markdownlint-disable-file -->
# Task Details: Shared Context Reference Syntax (`$agent`)

## Research Reference

**Source Research**: .agent-tracking/research/20260203-shared-context-research.md
**Test Strategy**: .agent-tracking/test-strategies/20260203-shared-context-test-strategy.md

---

## Phase 1: Parser & Model Extensions

### Task 1.1: Add WAITING status to TaskStatus enum

Add a new `WAITING` status to the TaskStatus enum to represent agents waiting for referenced agents to complete.

* **Files**:
  * `src/teambot/tasks/models.py` - Add WAITING to TaskStatus enum
* **Success**:
  * `TaskStatus.WAITING` exists
  * `is_terminal()` returns False for WAITING
* **Research References**:
  * .agent-tracking/research/20260203-shared-context-research.md (Lines 161-178) - TaskStatus enum extension
* **Implementation**:
  ```python
  class TaskStatus(Enum):
      PENDING = auto()    # Waiting to run (may have unmet dependencies)
      WAITING = auto()    # Waiting for referenced agent to complete  # NEW
      RUNNING = auto()    # Currently executing
      COMPLETED = auto()  # Finished successfully
      FAILED = auto()     # Finished with error
      SKIPPED = auto()    # Skipped due to parent failure
      CANCELLED = auto()  # Cancelled by user
  ```

---

### Task 1.2: Add `references` field to Command dataclass

Extend the Command dataclass to store agent IDs from `$ref` syntax.

* **Files**:
  * `src/teambot/repl/parser.py` - Modify Command dataclass
* **Success**:
  * `Command.references` field exists
  * Default value is empty list
* **Research References**:
  * .agent-tracking/research/20260203-shared-context-research.md (Lines 141-159) - Command dataclass extension
* **Implementation**:
  ```python
  @dataclass
  class Command:
      type: CommandType
      agent_id: Optional[str] = None
      agent_ids: list[str] = field(default_factory=list)
      content: Optional[str] = None
      background: bool = False
      is_pipeline: bool = False
      pipeline: Optional[list[PipelineStage]] = None
      references: list[str] = field(default_factory=list)  # Agent IDs from $ref
  ```

---

### Task 1.3: Add REFERENCE_PATTERN regex constant

Add regex pattern to detect `$agent` references in content.

* **Files**:
  * `src/teambot/repl/parser.py` - Add pattern constant after line 80
* **Success**:
  * `REFERENCE_PATTERN` matches `$pm`, `$ba`, `$builder-1`
  * Does not match `$100` or other non-agent patterns
* **Research References**:
  * .agent-tracking/research/20260203-shared-context-research.md (Lines 376-382) - Reference pattern definition
* **Implementation**:
  ```python
  # Pattern for agent references in content: $pm, $ba, $builder-1
  REFERENCE_PATTERN = re.compile(r"\$([a-zA-Z][a-zA-Z0-9-]*)")
  ```

---

### Task 1.4: Implement reference detection in `_parse_agent_command()`

Detect `$agent` references in command content and populate the `references` field.

* **Files**:
  * `src/teambot/repl/parser.py` - Modify `_parse_agent_command()` function
* **Success**:
  * `parse_command("@pm task $ba")` returns `references=["ba"]`
  * Multiple references detected and deduplicated
* **Research References**:
  * .agent-tracking/research/20260203-shared-context-research.md (Lines 392-399) - Reference detection logic
* **Implementation**:
  ```python
  # In _parse_agent_command(), after extracting content:
  
  # Detect $agent references in content
  references = []
  if content:
      matches = REFERENCE_PATTERN.findall(content)
      # Deduplicate while preserving order
      seen = set()
      references = [r for r in matches if not (r in seen or seen.add(r))]
  
  return Command(
      type=CommandType.AGENT,
      agent_id=agent_id,
      agent_ids=agent_ids,
      content=content,
      background=background,
      references=references,  # NEW
  )
  ```

---

## Phase 2: Parser Tests (TDD)

### Task 2.1: Create tests for reference parsing

Create comprehensive tests for `$agent` reference detection in parser.

* **Files**:
  * `tests/test_repl/test_parser.py` - Add TestParseReferences class
* **Success**:
  * All reference parsing scenarios tested
  * Coverage for reference detection ≥95%
* **Research References**:
  * .agent-tracking/research/20260203-shared-context-research.md (Lines 694-737) - Parser test examples
  * .agent-tracking/test-strategies/20260203-shared-context-test-strategy.md (Lines 102-131) - TDD testing sequence
* **Test Cases**:
  ```python
  class TestParseReferences:
      """Tests for $agent reference parsing."""
  
      def test_parse_single_reference(self):
          """Test parsing single $agent reference."""
          result = parse_command("@pm Summarize $ba output")
          
          assert result.references == ["ba"]
          assert "$ba" in result.content
  
      def test_parse_multiple_references(self):
          """Test parsing multiple references."""
          result = parse_command("@reviewer Check $builder-1 against $pm")
          
          assert result.references == ["builder-1", "pm"]
  
      def test_parse_hyphenated_reference(self):
          """Test parsing reference with hyphenated agent ID."""
          result = parse_command("@pm Use $builder-1 work")
          
          assert result.references == ["builder-1"]
  
      def test_parse_no_reference(self):
          """Test command without references."""
          result = parse_command("@pm Create a plan")
          
          assert result.references == []
  
      def test_parse_duplicate_references_deduplicated(self):
          """Test duplicate references are deduplicated."""
          result = parse_command("@pm Check $ba then verify $ba again")
          
          assert result.references == ["ba"]
  
      def test_dollar_amount_not_reference(self):
          """Test that $100 is not treated as reference."""
          result = parse_command("@pm Budget is $100")
          
          assert result.references == []
  ```

---

### Task 2.2: Create tests for Command.references field

Test that Command dataclass properly handles references field.

* **Files**:
  * `tests/test_repl/test_parser.py` - Add to TestParseReferences
* **Success**:
  * Field exists with correct default
  * References populated from parsing
* **Research References**:
  * .agent-tracking/test-strategies/20260203-shared-context-test-strategy.md (Lines 134-155) - Command dataclass tests
* **Test Cases**:
  ```python
  def test_command_has_references_field(self):
      """Test Command dataclass has references field."""
      cmd = Command(type=CommandType.AGENT)
      
      assert hasattr(cmd, 'references')
      assert cmd.references == []

  def test_command_references_default_empty(self):
      """Test references defaults to empty list."""
      cmd = Command(type=CommandType.AGENT, agent_id="pm")
      
      assert cmd.references == []
  ```

---

## Phase 3: TaskManager Agent Result Storage

### Task 3.1: Add `_agent_results` dictionary

Add dictionary to store latest results by agent ID.

* **Files**:
  * `src/teambot/tasks/manager.py` - Add `_agent_results` in `__init__` and update `execute_task`
* **Success**:
  * Results stored by agent_id on task completion
  * Latest result overwrites previous
* **Research References**:
  * .agent-tracking/research/20260203-shared-context-research.md (Lines 401-411) - Agent result storage
* **Implementation**:
  ```python
  def __init__(self, ...):
      # ... existing init ...
      self._agent_results: dict[str, TaskResult] = {}  # agent_id -> latest result
  
  async def execute_task(self, task_id: str) -> TaskResult:
      # ... existing execution logic ...
      
      # After task completion, store result by agent_id
      if task.result:
          self._agent_results[task.agent_id] = task.result
      
      return task.result
  ```

---

### Task 3.2: Implement `get_agent_result()` method

Add method to retrieve latest result for an agent.

* **Files**:
  * `src/teambot/tasks/manager.py` - Add new method
* **Success**:
  * Returns latest TaskResult for agent
  * Returns None when no result exists
* **Research References**:
  * .agent-tracking/research/20260203-shared-context-research.md (Lines 414-425) - get_agent_result method
* **Implementation**:
  ```python
  def get_agent_result(self, agent_id: str) -> Optional[TaskResult]:
      """Get latest result for an agent.
      
      Args:
          agent_id: Agent identifier.
          
      Returns:
          Latest TaskResult for agent, or None.
      """
      return self._agent_results.get(agent_id)
  ```

---

### Task 3.3: Implement `get_running_task_for_agent()` method

Add method to find currently running task for an agent.

* **Files**:
  * `src/teambot/tasks/manager.py` - Add new method
* **Success**:
  * Returns running Task if found
  * Returns None if no running task
* **Research References**:
  * .agent-tracking/research/20260203-shared-context-research.md (Lines 427-439) - get_running_task_for_agent method
* **Implementation**:
  ```python
  def get_running_task_for_agent(self, agent_id: str) -> Optional[Task]:
      """Get currently running task for an agent.
      
      Args:
          agent_id: Agent identifier.
          
      Returns:
          Running Task if found, else None.
      """
      for task in self._tasks.values():
          if task.agent_id == agent_id and task.status == TaskStatus.RUNNING:
              return task
      return None
  ```

---

## Phase 4: TaskManager Tests (TDD)

### Task 4.1: Create tests for agent result storage

Test that results are stored and retrieved correctly by agent ID.

* **Files**:
  * `tests/test_tasks/test_manager.py` - Add TestAgentResults class
* **Success**:
  * Result stored on task completion
  * Latest result overwrites previous
  * None returned when no result
* **Research References**:
  * .agent-tracking/test-strategies/20260203-shared-context-test-strategy.md (Lines 159-185) - Manager TDD sequence
* **Test Cases**:
  ```python
  class TestAgentResults:
      """Tests for agent result storage and retrieval."""
  
      @pytest.mark.asyncio
      async def test_agent_result_stored_on_completion(self, task_manager):
          """Test result is stored by agent_id after completion."""
          task = task_manager.create_task(agent_id="ba", prompt="Analyze")
          await task_manager.execute_task(task.id)
          
          result = task_manager.get_agent_result("ba")
          assert result is not None
          assert result.success
  
      @pytest.mark.asyncio
      async def test_get_agent_result_returns_latest(self, task_manager):
          """Test latest result overwrites previous."""
          # First task
          task1 = task_manager.create_task(agent_id="ba", prompt="First")
          await task_manager.execute_task(task1.id)
          
          # Second task for same agent
          task2 = task_manager.create_task(agent_id="ba", prompt="Second")
          await task_manager.execute_task(task2.id)
          
          result = task_manager.get_agent_result("ba")
          # Should be from second task
          assert "Second" in result.output or task2.result == result
  
      def test_get_agent_result_returns_none_when_missing(self, task_manager):
          """Test None returned when agent has no results."""
          result = task_manager.get_agent_result("never_ran")
          
          assert result is None
  ```

---

### Task 4.2: Create tests for running task lookup

Test finding currently running task for an agent.

* **Files**:
  * `tests/test_tasks/test_manager.py` - Add to TestAgentResults
* **Success**:
  * Running task found correctly
  * None returned when no running task
* **Test Cases**:
  ```python
  @pytest.mark.asyncio
  async def test_get_running_task_for_agent(self, task_manager):
      """Test finding running task for agent."""
      # Create and start a task (but don't await completion)
      task = task_manager.create_task(agent_id="ba", prompt="Slow task")
      # Mock running state
      task.status = TaskStatus.RUNNING
      
      running = task_manager.get_running_task_for_agent("ba")
      
      assert running is not None
      assert running.id == task.id
      assert running.status == TaskStatus.RUNNING

  def test_get_running_task_returns_none_when_idle(self, task_manager):
      """Test None returned when agent has no running task."""
      running = task_manager.get_running_task_for_agent("idle_agent")
      
      assert running is None
  ```

---

## Phase 5: TaskExecutor Reference Handling

### Task 5.1: Implement `_wait_for_references()` async method

Add method to wait for referenced agents to complete any running tasks.

* **Files**:
  * `src/teambot/tasks/executor.py` - Add new async method
* **Success**:
  * Waits for running task to complete
  * Handles multiple references
  * No hang when no running task
* **Research References**:
  * .agent-tracking/research/20260203-shared-context-research.md (Lines 470-481) - Wait implementation
* **Implementation**:
  ```python
  async def _wait_for_references(self, references: list[str]) -> None:
      """Wait for referenced agents to complete any running tasks.
      
      Args:
          references: List of agent IDs to wait for.
      """
      for agent_id in references:
          running_task = self._manager.get_running_task_for_agent(agent_id)
          if running_task:
              # Update status to WAITING
              # Wait for the task to complete
              while running_task.status == TaskStatus.RUNNING:
                  await asyncio.sleep(0.1)
  ```

---

### Task 5.2: Implement `_inject_references()` method

Add method to inject referenced agent outputs into prompt.

* **Files**:
  * `src/teambot/tasks/executor.py` - Add new method
* **Success**:
  * Outputs prepended with agent headers
  * Placeholder used when no output available
  * Original prompt preserved in "Your Task" section
* **Research References**:
  * .agent-tracking/research/20260203-shared-context-research.md (Lines 483-506) - Injection implementation
* **Implementation**:
  ```python
  def _inject_references(self, prompt: str, references: list[str]) -> str:
      """Inject referenced agent outputs into prompt.
      
      Args:
          prompt: Original prompt with $ref tokens.
          references: List of agent IDs referenced.
          
      Returns:
          Prompt with outputs prepended.
      """
      sections = []
      for agent_id in references:
          result = self._manager.get_agent_result(agent_id)
          if result and result.success:
              sections.append(
                  f"=== Output from @{agent_id} ===\n{result.output}\n"
              )
          else:
              sections.append(
                  f"=== Output from @{agent_id} ===\n[No output available]\n"
              )
      
      sections.append(f"=== Your Task ===\n{prompt}")
      return "\n".join(sections)
  ```

---

### Task 5.3: Update `_execute_simple()` to handle references

Modify simple execution to check for and handle `$ref` dependencies.

* **Files**:
  * `src/teambot/tasks/executor.py` - Modify `_execute_simple()` method
* **Success**:
  * References detected and waited for
  * Output injected before execution
  * Non-reference commands unchanged
* **Research References**:
  * .agent-tracking/research/20260203-shared-context-research.md (Lines 443-466) - Execute simple modification
* **Implementation**:
  ```python
  async def _execute_simple(self, command: Command) -> ExecutionResult:
      """Execute simple single-agent command, handling $ref dependencies."""
      agent_id = command.agent_ids[0] if command.agent_ids else command.agent_id
      
      # Check for $ref dependencies
      if command.references:
          # Wait for any referenced agents that are currently running
          await self._wait_for_references(command.references)
          
          # Build prompt with injected outputs
          prompt = self._inject_references(command.content, command.references)
      else:
          prompt = command.content
      
      # Continue with existing task creation and execution...
  ```

---

## Phase 6: TaskExecutor Tests (TDD)

### Task 6.1: Create tests for reference output injection

Test that referenced outputs are correctly injected into prompts.

* **Files**:
  * `tests/test_tasks/test_executor.py` - Add TestExecutorReferences class
* **Success**:
  * Output prepended with correct header
  * Multiple references handled
* **Research References**:
  * .agent-tracking/research/20260203-shared-context-research.md (Lines 742-765) - Executor test examples
  * .agent-tracking/test-strategies/20260203-shared-context-test-strategy.md (Lines 500-530) - TDD sequence
* **Test Cases**:
  ```python
  class TestExecutorReferences:
      """Tests for $ref execution."""
  
      @pytest.mark.asyncio
      async def test_reference_injects_output(self):
          """Test that referenced output is injected."""
          mock_sdk = AsyncMock()
          mock_sdk.execute = AsyncMock(return_value="Done")
          
          executor = TaskExecutor(sdk_client=mock_sdk)
          
          # First, run a task for ba
          cmd1 = parse_command("@ba Analyze requirements")
          await executor.execute(cmd1)
          
          # Now reference ba's output
          cmd2 = parse_command("@pm Summarize $ba")
          await executor.execute(cmd2)
          
          # Check that PM received BA's output
          call_args = mock_sdk.execute.call_args_list[-1]
          prompt = call_args[0][1]
          assert "=== Output from @ba ===" in prompt
  ```

---

### Task 6.2: Create tests for waiting on running tasks

Test that referencing agent waits for referenced agent to complete.

* **Files**:
  * `tests/test_tasks/test_executor.py` - Add to TestExecutorReferences
* **Success**:
  * Waits for running task
  * Execution order verified
* **Test Cases**:
  ```python
  @pytest.mark.asyncio
  async def test_reference_waits_for_running_task(self):
      """Test that reference waits for running task."""
      import asyncio
      
      call_order = []
      
      async def slow_execute(agent_id, prompt):
          call_order.append(f"{agent_id}_start")
          if agent_id == "ba":
              await asyncio.sleep(0.3)
          call_order.append(f"{agent_id}_end")
          return f"{agent_id} output"
      
      mock_sdk = AsyncMock()
      mock_sdk.execute = slow_execute
      
      executor = TaskExecutor(sdk_client=mock_sdk)
      
      # Start BA in background
      cmd1 = parse_command("@ba Analyze &")
      asyncio.create_task(executor.execute(cmd1))
      
      # Small delay to ensure BA starts
      await asyncio.sleep(0.05)
      
      # PM references BA (should wait)
      cmd2 = parse_command("@pm Summarize $ba")
      await executor.execute(cmd2)
      
      # BA should complete before PM accesses its output
      ba_end_idx = call_order.index("ba_end")
      pm_start_idx = call_order.index("pm_start")
      assert ba_end_idx < pm_start_idx
  ```

---

### Task 6.3: Create tests for no output available scenario

Test graceful handling when referenced agent has no output.

* **Files**:
  * `tests/test_tasks/test_executor.py` - Add to TestExecutorReferences
* **Success**:
  * Placeholder text injected
  * Execution continues without error
* **Test Cases**:
  ```python
  @pytest.mark.asyncio
  async def test_reference_no_output_available(self):
      """Test graceful handling when no output available."""
      mock_sdk = AsyncMock()
      mock_sdk.execute = AsyncMock(return_value="Done")
      
      executor = TaskExecutor(sdk_client=mock_sdk)
      
      # Reference agent that hasn't run
      cmd = parse_command("@pm Summarize $ba")
      result = await executor.execute(cmd)
      
      # Should still execute with placeholder
      call_args = mock_sdk.execute.call_args
      prompt = call_args[0][1]
      assert "[No output available]" in prompt
  ```

---

## Phase 7: REPL Routing & Overlay Updates

### Task 7.1: Update REPL routing condition for references

Modify routing to send commands with references through TaskExecutor.

* **Files**:
  * `src/teambot/repl/loop.py` - Update routing condition (lines 280-290)
* **Success**:
  * Commands with `$ref` route to TaskExecutor
  * Simple commands without refs use existing path
* **Research References**:
  * .agent-tracking/research/20260203-shared-context-research.md (Lines 509-522) - Routing change
* **Implementation**:
  ```python
  # Check if this is an advanced agent command
  if command.type == CommandType.AGENT and (
      command.is_pipeline or
      len(command.agent_ids) > 1 or
      command.background or
      command.references  # NEW: Has $ref dependencies
  ):
      # Use task executor for parallel/pipeline/background/references
      result = await self._handle_advanced_command(command)
  else:
      # Use existing router for simple commands
      result = await self._router.route(command)
  ```

---

### Task 7.2: Add waiting fields to OverlayState

Add fields to track waiting agents and their dependencies.

* **Files**:
  * `src/teambot/visualization/overlay.py` - Update OverlayState dataclass
* **Success**:
  * `waiting_count` field exists
  * `waiting_for` dict tracks relationships
* **Research References**:
  * .agent-tracking/research/20260203-shared-context-research.md (Lines 536-543) - Overlay state extension
* **Implementation**:
  ```python
  @dataclass
  class OverlayState:
      enabled: bool = True
      active_agents: list[str] = field(default_factory=list)
      running_count: int = 0
      pending_count: int = 0
      completed_count: int = 0
      failed_count: int = 0
      waiting_count: int = 0  # NEW
      waiting_for: dict[str, str] = field(default_factory=dict)  # NEW: agent -> waiting_for_agent
  ```

---

### Task 7.3: Update overlay display for waiting state

Update `_build_content()` to show waiting status and relationships.

* **Files**:
  * `src/teambot/visualization/overlay.py` - Update `_build_content()` method
* **Success**:
  * Waiting count displayed in status line
  * Waiting relationships shown (e.g., "@pm→@ba")
* **Research References**:
  * .agent-tracking/research/20260203-shared-context-research.md (Lines 546-573) - Display implementation
* **Implementation**:
  ```python
  def _build_content(self) -> list[str]:
      lines = []
      
      if self._state.is_idle():
          lines.append("✓ Idle")
      else:
          # Show waiting agents
          if self._state.waiting_count > 0:
              waiting = ", ".join(f"@{a}→@{w}" for a, w in self._state.waiting_for.items())
              lines.append(f"⏳ Waiting: {waiting}"[:OVERLAY_WIDTH - 4])
          
          # Show active agents with spinner
          spinner = SPINNER_FRAMES[self._state.spinner_frame % len(SPINNER_FRAMES)]
          agents = ", ".join(f"@{a}" for a in self._state.active_agents[:3])
          lines.append(f"{spinner} {agents}"[:OVERLAY_WIDTH - 4])
      
      # Task counts with waiting
      running = self._state.running_count
      waiting = self._state.waiting_count
      pending = self._state.pending_count
      completed = self._state.completed_count
      counts = f"{running}🔄 {waiting}⏳ {pending}⏸ {completed}✓"
      lines.append(f"Tasks: {counts}"[:OVERLAY_WIDTH - 4])
      
      return lines
  ```

---

## Phase 8: Documentation

### Task 8.1: Add "Shared Context References" section to README

Document the `$agent` syntax with examples.

* **Files**:
  * `README.md` - Add section after existing syntax documentation
* **Success**:
  * Syntax clearly explained
  * Usage examples provided
  * How it works described
* **Research References**:
  * .agent-tracking/research/20260203-shared-context-research.md (Lines 575-626) - README documentation
* **Content**:
  ```markdown
  ### Shared Context References (`$agent`)
  
  Reference another agent's most recent output using `$agent` syntax:
  
  ```bash
  # Reference PM's last output
  teambot: @builder-1 Implement based on $pm
  
  # Reference multiple agents
  teambot: @reviewer Check $builder-1 against $pm requirements
  
  # Wait for running task
  teambot: @pm Summarize $ba  # Waits if @ba is still running
  ```
  
  **How It Works**:
  1. Parser detects `$agent` references in your prompt
  2. If referenced agent has a running task, waits for completion
  3. Referenced agent's latest output is prepended to your prompt
  4. Your agent receives full context automatically
  ```

---

### Task 8.2: Add syntax comparison table

Document differences between `$ref` and `->` syntax.

* **Files**:
  * `README.md` - Add comparison table
* **Success**:
  * Clear comparison table
  * When-to-use guidance
* **Research References**:
  * .agent-tracking/research/20260203-shared-context-research.md (Lines 613-626) - Comparison table
* **Content**:
  ```markdown
  ### Comparing `$ref` vs `->` Syntax
  
  | Feature | `$ref` Syntax | `->` Pipeline |
  |---------|---------------|---------------|
  | **Use Case** | Reference existing output | Chain new tasks |
  | **Example** | `@pm Summarize $ba` | `@ba Analyze -> @pm Summarize` |
  | **Producer Task** | Uses last completed output | Runs new task |
  | **Direction** | Consumer pulls | Producer pushes |
  | **Multiple Sources** | `@pm Use $ba and $writer` | `@ba,writer Analyze -> @pm` |
  | **Best For** | Building on previous work | Designing new workflows |
  
  **When to Use Which**:
  - **`$ref`**: When you want to reference work an agent already completed
  - **`->`**: When you want to define a complete workflow from scratch
  ```

---

## Phase 9: Integration & Validation

### Task 9.1: Create integration tests

Test complete workflow with reference chaining.

* **Files**:
  * `tests/test_integration/test_shared_context.py` - Create new test file
* **Success**:
  * Full workflow passes (BA → PM refs BA → Builder refs PM)
  * Multiple references work together
* **Research References**:
  * .agent-tracking/research/20260203-shared-context-research.md (Lines 815-851) - Integration test examples
* **Test Cases**:
  ```python
  class TestSharedContextIntegration:
      """Integration tests for shared context feature."""
  
      @pytest.mark.asyncio
      async def test_full_workflow_with_references(self):
          """Test complete workflow: BA → PM references BA → Builder references PM."""
          mock_sdk = AsyncMock()
          
          outputs = {
              "ba": "Requirements: login, dashboard",
              "pm": "Plan: 1. Build login 2. Build dashboard",
              "builder-1": "Implementation complete",
          }
          
          async def mock_execute(agent_id, prompt):
              return outputs.get(agent_id, "default")
          
          mock_sdk.execute = mock_execute
          executor = TaskExecutor(sdk_client=mock_sdk)
          
          # BA analyzes
          await executor.execute(parse_command("@ba Analyze requirements"))
          
          # PM references BA
          await executor.execute(parse_command("@pm Create plan based on $ba"))
          
          # Builder references PM
          result = await executor.execute(
              parse_command("@builder-1 Implement $pm")
          )
          
          # Verify chain worked
          assert result.success
  ```

---

### Task 9.2: Validate coverage targets

Run full test suite and verify coverage meets targets.

* **Files**:
  * N/A - Validation task
* **Success**:
  * Parser reference logic: ≥95%
  * TaskManager agent results: ≥90%
  * TaskExecutor reference handling: ≥85%
  * Overall: ≥85%
* **Validation Command**:
  ```bash
  uv run pytest --cov=src/teambot --cov-report=term-missing
  ```
* **Coverage Targets** (from test strategy):
  | Component | Target |
  |-----------|--------|
  | Parser (references) | 95% |
  | TaskManager (agent results) | 90% |
  | TaskExecutor (ref handling) | 85% |
  | REPL Loop (routing) | 70% |
  | Overlay (waiting display) | 70% |

---

## Dependencies

* pytest (existing in pyproject.toml)
* pytest-asyncio (existing - asyncio_mode = "auto")
* pytest-cov (existing for coverage)
* unittest.mock (AsyncMock, MagicMock)

## Success Criteria

* `$agent` syntax parses correctly with references field populated
* References are injected into prompts with proper headers
* Agents wait for running referenced tasks before executing
* Status overlay shows waiting state accurately
* README documents both syntaxes with clear comparison
* All existing tests continue to pass
* Coverage targets met per test strategy
