<!-- markdownlint-disable-file -->
# Task Details: TeamBot Implementation

## Research Reference

**Source Research**: .agent-tracking/research/20260122-teambot-research.md
**Test Strategy**: .agent-tracking/test-strategies/20260122-teambot-test-strategy.md
**Feature Spec**: docs/feature-specs/teambot.md

---

## Phase 1: Project Setup

### Task 1.1: Update pyproject.toml with dependencies

Update the project configuration to include all required dependencies for TeamBot.

* **Files**:
  * `pyproject.toml` - Add runtime and dev dependencies
* **Changes**:
  ```toml
  [project]
  name = "teambot"
  version = "0.1.0"
  description = "CLI wrapper for GitHub Copilot CLI enabling autonomous AI agent teams"
  readme = "README.md"
  requires-python = ">=3.10"
  dependencies = [
      "python-dotenv>=1.0.0",
      "python-frontmatter>=1.0.0",
      "rich>=13.0.0",
  ]

  [dependency-groups]
  dev = [
      "ruff>=0.8.0",
      "pytest>=7.4.0",
      "pytest-cov>=4.1.0",
      "pytest-mock>=3.12.0",
  ]

  [project.scripts]
  teambot = "teambot.cli:main"

  [tool.pytest.ini_options]
  testpaths = ["tests"]
  python_files = ["test_*.py"]
  python_classes = ["Test*"]
  python_functions = ["test_*"]
  addopts = "--cov=src/teambot --cov-report=term-missing"
  ```
* **Success**:
  * `uv sync` completes without errors
  * All dependencies installed
* **Research References**:
  * .agent-tracking/research/20260122-teambot-research.md (Lines 680-710) - Dependencies section
* **Dependencies**: None

---

### Task 1.2: Create TeamBot package structure

Create the complete package directory structure for TeamBot.

* **Files**:
  * `src/teambot/__init__.py` - Package init with version
  * `src/teambot/cli.py` - CLI entry point placeholder
  * `src/teambot/orchestrator.py` - Orchestrator placeholder
  * `src/teambot/agent_runner.py` - Agent runner placeholder
  * `src/teambot/window_manager.py` - Window manager placeholder
  * `src/teambot/messaging/__init__.py` - Messaging package init
  * `src/teambot/messaging/protocol.py` - Message protocol placeholder
  * `src/teambot/messaging/router.py` - Message router placeholder
  * `src/teambot/history/__init__.py` - History package init
  * `src/teambot/history/manager.py` - History manager placeholder
  * `src/teambot/history/frontmatter.py` - Frontmatter parsing placeholder
  * `src/teambot/history/compactor.py` - Context compactor placeholder
  * `src/teambot/visualization/__init__.py` - Visualization package init
  * `src/teambot/visualization/console.py` - Console visualization placeholder
  * `src/teambot/config/__init__.py` - Config package init
  * `src/teambot/config/loader.py` - Config loader placeholder
  * `src/teambot/config/schema.py` - Config schema placeholder
* **Directory Structure**:
  ```
  src/teambot/
  ├── __init__.py
  ├── cli.py
  ├── orchestrator.py
  ├── agent_runner.py
  ├── window_manager.py
  ├── messaging/
  │   ├── __init__.py
  │   ├── protocol.py
  │   └── router.py
  ├── history/
  │   ├── __init__.py
  │   ├── manager.py
  │   ├── frontmatter.py
  │   └── compactor.py
  ├── visualization/
  │   ├── __init__.py
  │   └── console.py
  └── config/
      ├── __init__.py
      ├── loader.py
      └── schema.py
  ```
* **Initial __init__.py Content**:
  ```python
  """TeamBot - Autonomous AI agent teams for software development."""
  __version__ = "0.1.0"
  ```
* **Success**:
  * All directories created
  * `from teambot import __version__` works
* **Research References**:
  * .agent-tracking/research/20260122-teambot-research.md (Lines 210-260) - Project structure
* **Dependencies**: Task 1.1

---

### Task 1.3: Setup test infrastructure

Create test directory structure and configuration.

* **Files**:
  * `tests/__init__.py` - Test package init
  * `tests/conftest.py` - Shared pytest fixtures
  * `tests/test_messaging/__init__.py` - Messaging tests package
  * `tests/test_history/__init__.py` - History tests package
  * `tests/test_config/__init__.py` - Config tests package
  * `tests/test_visualization/__init__.py` - Visualization tests package
* **conftest.py Content**:
  ```python
  """Shared pytest fixtures for TeamBot tests."""
  import pytest
  from pathlib import Path
  import tempfile
  import json

  @pytest.fixture
  def temp_teambot_dir(tmp_path):
      """Create a temporary .teambot directory structure."""
      teambot_dir = tmp_path / ".teambot"
      teambot_dir.mkdir()
      (teambot_dir / "history").mkdir()
      (teambot_dir / "state").mkdir()
      return teambot_dir

  @pytest.fixture
  def sample_agent_config():
      """Standard agent configuration for testing."""
      return {
          "id": "builder-1",
          "persona": "builder",
          "display_name": "Builder (Primary)",
          "parallel_capable": True,
          "workflow_stages": ["implementation", "testing"]
      }

  @pytest.fixture
  def sample_objective():
      """Sample objective markdown content."""
      return """# Objective: Test Feature

  ## Description
  Build a test feature for validation.

  ## Definition of Done
  - [ ] Feature implemented
  - [ ] Tests passing

  ## Success Criteria
  - API responds correctly
  """
  ```
* **Success**:
  * `uv run pytest` runs (0 tests initially)
  * Test discovery works
* **Research References**:
  * .agent-tracking/research/20260122-teambot-research.md (Lines 60-140) - Testing infrastructure
  * .agent-tracking/test-strategies/20260122-teambot-test-strategy.md (Lines 300-400) - Test patterns
* **Dependencies**: Task 1.2

---

## Phase 2: Core Messaging (TDD)

### Task 2.1: Write message protocol tests

Write comprehensive tests for the message protocol BEFORE implementation.

* **Files**:
  * `tests/test_messaging/test_protocol.py` - Protocol tests
* **Test Cases**:
  ```python
  """Tests for message protocol - TDD approach."""
  import pytest
  from datetime import datetime

  class TestMessageType:
      """Tests for MessageType enum."""
      
      def test_message_types_exist(self):
          """Verify all required message types are defined."""
          from teambot.messaging.protocol import MessageType
          
          assert hasattr(MessageType, 'TASK_ASSIGN')
          assert hasattr(MessageType, 'TASK_COMPLETE')
          assert hasattr(MessageType, 'STATUS_UPDATE')
          assert hasattr(MessageType, 'ERROR')
          assert hasattr(MessageType, 'SHUTDOWN')
      
      def test_message_type_values_are_strings(self):
          """Message type values should be descriptive strings."""
          from teambot.messaging.protocol import MessageType
          
          assert MessageType.TASK_ASSIGN.value == "task_assign"
          assert MessageType.SHUTDOWN.value == "shutdown"

  class TestAgentMessage:
      """Tests for AgentMessage dataclass."""
      
      def test_create_message_with_required_fields(self):
          """Create message with minimum required fields."""
          from teambot.messaging.protocol import AgentMessage, MessageType
          
          msg = AgentMessage(
              type=MessageType.TASK_ASSIGN,
              source_agent="orchestrator"
          )
          
          assert msg.type == MessageType.TASK_ASSIGN
          assert msg.source_agent == "orchestrator"
          assert msg.target_agent is None
          assert msg.payload is None
          assert msg.timestamp is not None
      
      def test_create_message_with_all_fields(self):
          """Create message with all optional fields."""
          from teambot.messaging.protocol import AgentMessage, MessageType
          
          msg = AgentMessage(
              type=MessageType.TASK_COMPLETE,
              source_agent="builder-1",
              target_agent="orchestrator",
              payload={"result": "success"},
              correlation_id="task-123"
          )
          
          assert msg.target_agent == "orchestrator"
          assert msg.payload["result"] == "success"
          assert msg.correlation_id == "task-123"
      
      def test_message_to_dict(self):
          """Message should be serializable to dict."""
          from teambot.messaging.protocol import AgentMessage, MessageType
          
          msg = AgentMessage(
              type=MessageType.STATUS_UPDATE,
              source_agent="pm",
              payload={"status": "working"}
          )
          
          data = msg.to_dict()
          
          assert data["type"] == "status_update"
          assert data["source_agent"] == "pm"
          assert data["payload"]["status"] == "working"
      
      def test_message_from_dict(self):
          """Message should be deserializable from dict."""
          from teambot.messaging.protocol import AgentMessage, MessageType
          
          data = {
              "type": "task_assign",
              "source_agent": "orchestrator",
              "target_agent": "builder-1",
              "payload": {"task": "implement feature"},
              "timestamp": 1706000000.0
          }
          
          msg = AgentMessage.from_dict(data)
          
          assert msg.type == MessageType.TASK_ASSIGN
          assert msg.target_agent == "builder-1"
  ```
* **Success**:
  * Tests written and discoverable
  * Tests FAIL initially (no implementation)
* **Research References**:
  * .agent-tracking/research/20260122-teambot-research.md (Lines 270-340) - Message protocol pattern
* **Dependencies**: Phase 1

---

### Task 2.2: Implement message protocol

Implement the message protocol to pass all tests from Task 2.1.

* **Files**:
  * `src/teambot/messaging/protocol.py` - Message protocol implementation
* **Implementation**:
  ```python
  """Message protocol for inter-agent communication."""
  from dataclasses import dataclass, field
  from typing import Any, Optional, Dict
  from enum import Enum
  import time

  class MessageType(Enum):
      """Types of messages exchanged between agents."""
      TASK_ASSIGN = "task_assign"
      TASK_COMPLETE = "task_complete"
      STATUS_UPDATE = "status_update"
      ERROR = "error"
      SHUTDOWN = "shutdown"
      CONTEXT_REQUEST = "context_request"
      CONTEXT_RESPONSE = "context_response"

  @dataclass
  class AgentMessage:
      """Standard message format for inter-agent communication."""
      type: MessageType
      source_agent: str
      target_agent: Optional[str] = None
      payload: Any = None
      timestamp: float = field(default_factory=time.time)
      correlation_id: Optional[str] = None
      
      def to_dict(self) -> Dict[str, Any]:
          """Serialize message to dictionary."""
          return {
              "type": self.type.value,
              "source_agent": self.source_agent,
              "target_agent": self.target_agent,
              "payload": self.payload,
              "timestamp": self.timestamp,
              "correlation_id": self.correlation_id,
          }
      
      @classmethod
      def from_dict(cls, data: Dict[str, Any]) -> "AgentMessage":
          """Deserialize message from dictionary."""
          return cls(
              type=MessageType(data["type"]),
              source_agent=data["source_agent"],
              target_agent=data.get("target_agent"),
              payload=data.get("payload"),
              timestamp=data.get("timestamp", time.time()),
              correlation_id=data.get("correlation_id"),
          )
  ```
* **Success**:
  * All tests from Task 2.1 pass
  * `uv run pytest tests/test_messaging/test_protocol.py` succeeds
* **Research References**:
  * .agent-tracking/research/20260122-teambot-research.md (Lines 270-340) - Protocol pattern
* **Dependencies**: Task 2.1 (tests must exist first)

---

### Task 2.3: Write message router tests

Write tests for message routing logic BEFORE implementation.

* **Files**:
  * `tests/test_messaging/test_router.py` - Router tests
* **Test Cases**:
  ```python
  """Tests for message router - TDD approach."""
  import pytest
  from multiprocessing import Queue
  from unittest.mock import Mock, patch

  class TestMessageRouter:
      """Tests for MessageRouter class."""
      
      def test_register_agent_queue(self):
          """Router should track agent queues."""
          from teambot.messaging.router import MessageRouter
          
          router = MessageRouter()
          queue = Queue()
          
          router.register_agent("builder-1", queue)
          
          assert "builder-1" in router.agent_queues
          assert router.agent_queues["builder-1"] is queue
      
      def test_route_to_specific_agent(self):
          """Messages with target should go to that agent's queue."""
          from teambot.messaging.router import MessageRouter
          from teambot.messaging.protocol import AgentMessage, MessageType
          
          router = MessageRouter()
          queue = Queue()
          router.register_agent("builder-1", queue)
          
          msg = AgentMessage(
              type=MessageType.TASK_ASSIGN,
              source_agent="orchestrator",
              target_agent="builder-1",
              payload={"task": "test"}
          )
          
          router.route(msg)
          
          received = queue.get(timeout=1)
          assert received.payload["task"] == "test"
      
      def test_broadcast_to_all_agents(self):
          """Messages without target should broadcast to all."""
          from teambot.messaging.router import MessageRouter
          from teambot.messaging.protocol import AgentMessage, MessageType
          
          router = MessageRouter()
          q1, q2 = Queue(), Queue()
          router.register_agent("agent-1", q1)
          router.register_agent("agent-2", q2)
          
          msg = AgentMessage(
              type=MessageType.SHUTDOWN,
              source_agent="orchestrator",
              target_agent=None  # Broadcast
          )
          
          router.route(msg)
          
          assert q1.get(timeout=1).type == MessageType.SHUTDOWN
          assert q2.get(timeout=1).type == MessageType.SHUTDOWN
      
      def test_unregister_agent(self):
          """Should remove agent from routing."""
          from teambot.messaging.router import MessageRouter
          
          router = MessageRouter()
          queue = Queue()
          router.register_agent("builder-1", queue)
          router.unregister_agent("builder-1")
          
          assert "builder-1" not in router.agent_queues
  ```
* **Success**:
  * Tests written and discoverable
  * Tests FAIL initially (no implementation)
* **Research References**:
  * .agent-tracking/research/20260122-teambot-research.md (Lines 130-180) - Queue routing
* **Dependencies**: Task 2.2

---

### Task 2.4: Implement message router

Implement the message router to pass all tests from Task 2.3.

* **Files**:
  * `src/teambot/messaging/router.py` - Router implementation
* **Implementation**:
  ```python
  """Message routing between agents."""
  from multiprocessing import Queue
  from typing import Dict, Optional
  from .protocol import AgentMessage

  class MessageRouter:
      """Routes messages between agents via queues."""
      
      def __init__(self):
          self.agent_queues: Dict[str, Queue] = {}
          self._timeout = 5.0
      
      def register_agent(self, agent_id: str, queue: Queue) -> None:
          """Register an agent's queue for message delivery."""
          self.agent_queues[agent_id] = queue
      
      def unregister_agent(self, agent_id: str) -> None:
          """Remove an agent from routing."""
          self.agent_queues.pop(agent_id, None)
      
      def route(self, message: AgentMessage) -> None:
          """Route message to target agent or broadcast."""
          if message.target_agent:
              self._send_to_agent(message.target_agent, message)
          else:
              self._broadcast(message)
      
      def _send_to_agent(self, agent_id: str, message: AgentMessage) -> None:
          """Send message to specific agent."""
          if agent_id in self.agent_queues:
              self.agent_queues[agent_id].put(message, timeout=self._timeout)
      
      def _broadcast(self, message: AgentMessage) -> None:
          """Send message to all registered agents."""
          for queue in self.agent_queues.values():
              queue.put(message, timeout=self._timeout)
  ```
* **Success**:
  * All tests from Task 2.3 pass
  * `uv run pytest tests/test_messaging/` succeeds
* **Research References**:
  * .agent-tracking/research/20260122-teambot-research.md (Lines 130-180)
* **Dependencies**: Task 2.3

---

## Phase 3: Orchestrator (TDD)

### Task 3.1: Write orchestrator tests

Write comprehensive tests for the orchestrator BEFORE implementation.

* **Files**:
  * `tests/test_orchestrator.py` - Orchestrator tests
* **Test Cases**:
  ```python
  """Tests for orchestrator - TDD approach."""
  import pytest
  from multiprocessing import Queue
  from unittest.mock import Mock, patch, MagicMock
  import time

  class TestOrchestrator:
      """Tests for Orchestrator class."""
      
      def test_create_orchestrator_with_config(self, sample_agent_config):
          """Orchestrator initializes with configuration."""
          from teambot.orchestrator import Orchestrator
          
          config = {"agents": [sample_agent_config]}
          orch = Orchestrator(config)
          
          assert orch.config == config
          assert orch.agents == {}
          assert isinstance(orch.main_queue, Queue)
      
      def test_spawn_agent_creates_queue(self, sample_agent_config):
          """Spawning agent creates dedicated queue."""
          from teambot.orchestrator import Orchestrator
          
          config = {"agents": [sample_agent_config]}
          orch = Orchestrator(config)
          
          # Mock the actual process spawning
          with patch.object(orch, '_create_agent_process') as mock_create:
              mock_create.return_value = MagicMock()
              orch.spawn_agent(sample_agent_config)
          
          assert "builder-1" in orch.router.agent_queues
      
      def test_send_to_agent_uses_router(self, sample_agent_config):
          """send_to_agent delegates to router."""
          from teambot.orchestrator import Orchestrator
          from teambot.messaging.protocol import AgentMessage, MessageType
          
          config = {"agents": [sample_agent_config]}
          orch = Orchestrator(config)
          
          # Setup mock queue
          mock_queue = Queue()
          orch.router.register_agent("builder-1", mock_queue)
          
          msg = AgentMessage(
              type=MessageType.TASK_ASSIGN,
              source_agent="orchestrator",
              target_agent="builder-1"
          )
          
          orch.send_to_agent("builder-1", msg)
          
          received = mock_queue.get(timeout=1)
          assert received.type == MessageType.TASK_ASSIGN
      
      def test_shutdown_sends_sentinel_to_all(self, sample_agent_config):
          """Shutdown broadcasts SHUTDOWN message."""
          from teambot.orchestrator import Orchestrator
          from teambot.messaging.protocol import MessageType
          
          config = {"agents": [sample_agent_config]}
          orch = Orchestrator(config)
          
          # Setup mock queues for multiple agents
          queues = {}
          for agent_id in ["pm", "builder-1", "reviewer"]:
              q = Queue()
              orch.router.register_agent(agent_id, q)
              queues[agent_id] = q
          
          orch.shutdown()
          
          for agent_id, q in queues.items():
              msg = q.get(timeout=1)
              assert msg.type == MessageType.SHUTDOWN
      
      def test_handle_agent_message(self, sample_agent_config):
          """Orchestrator processes messages from main queue."""
          from teambot.orchestrator import Orchestrator
          from teambot.messaging.protocol import AgentMessage, MessageType
          
          config = {"agents": [sample_agent_config]}
          orch = Orchestrator(config)
          
          # Put a message on main queue
          msg = AgentMessage(
              type=MessageType.TASK_COMPLETE,
              source_agent="builder-1",
              payload={"result": "success"}
          )
          orch.main_queue.put(msg)
          
          # Process one message
          orch._process_one_message(timeout=1)
          
          # Verify message was handled (check internal state or logs)
          assert True  # Placeholder - specific assertion depends on handler logic
  ```
* **Success**:
  * Tests written and discoverable
  * Tests FAIL initially (no implementation)
* **Research References**:
  * .agent-tracking/research/20260122-teambot-research.md (Lines 270-400) - Orchestrator pattern
  * .agent-tracking/test-strategies/20260122-teambot-test-strategy.md (Lines 180-220) - Orchestrator testing
* **Dependencies**: Phase 2

---

### Task 3.2: Implement orchestrator

Implement the orchestrator to pass all tests from Task 3.1.

* **Files**:
  * `src/teambot/orchestrator.py` - Orchestrator implementation
* **Implementation**:
  ```python
  """Parent orchestrator for managing agent lifecycle and communication."""
  from multiprocessing import Process, Queue
  from queue import Empty
  from typing import Dict, Optional, Any
  import logging

  from .messaging.protocol import AgentMessage, MessageType
  from .messaging.router import MessageRouter

  logger = logging.getLogger(__name__)

  class Orchestrator:
      """Parent process managing agent lifecycle and communication."""
      
      def __init__(self, config: Dict[str, Any]):
          self.config = config
          self.agents: Dict[str, Process] = {}
          self.router = MessageRouter()
          self.main_queue: Queue = Queue()
          self.running = False
      
      def spawn_agent(self, agent_config: Dict[str, Any]) -> Process:
          """Spawn agent in new process with dedicated queue."""
          agent_id = agent_config["id"]
          agent_queue = Queue()
          
          self.router.register_agent(agent_id, agent_queue)
          
          process = self._create_agent_process(agent_config, agent_queue)
          process.start()
          self.agents[agent_id] = process
          
          logger.info(f"Spawned agent: {agent_id}")
          return process
      
      def _create_agent_process(
          self,
          agent_config: Dict[str, Any],
          agent_queue: Queue
      ) -> Process:
          """Create the agent process (can be overridden for testing)."""
          from .agent_runner import agent_main
          
          return Process(
              target=agent_main,
              args=(agent_config, agent_queue, self.main_queue),
              name=f"agent-{agent_config['id']}"
          )
      
      def send_to_agent(self, agent_id: str, message: AgentMessage) -> None:
          """Send message to specific agent."""
          message.target_agent = agent_id
          self.router.route(message)
      
      def broadcast(self, message: AgentMessage) -> None:
          """Broadcast message to all agents."""
          message.target_agent = None
          self.router.route(message)
      
      def shutdown(self) -> None:
          """Graceful shutdown of all agents."""
          logger.info("Initiating shutdown...")
          
          shutdown_msg = AgentMessage(
              type=MessageType.SHUTDOWN,
              source_agent="orchestrator"
          )
          self.broadcast(shutdown_msg)
          
          # Wait for agents to finish
          for agent_id, process in self.agents.items():
              process.join(timeout=10.0)
              if process.is_alive():
                  logger.warning(f"Force terminating agent: {agent_id}")
                  process.terminate()
          
          self.running = False
          logger.info("Shutdown complete")
      
      def _process_one_message(self, timeout: float = 1.0) -> bool:
          """Process a single message from main queue."""
          try:
              message = self.main_queue.get(timeout=timeout)
              self._handle_message(message)
              return True
          except Empty:
              return False
      
      def _handle_message(self, message: AgentMessage) -> None:
          """Handle incoming message from an agent."""
          logger.debug(f"Received from {message.source_agent}: {message.type}")
          
          if message.type == MessageType.TASK_COMPLETE:
              self._handle_task_complete(message)
          elif message.type == MessageType.ERROR:
              self._handle_error(message)
          elif message.type == MessageType.STATUS_UPDATE:
              self._handle_status_update(message)
      
      def _handle_task_complete(self, message: AgentMessage) -> None:
          """Handle task completion from agent."""
          logger.info(f"Task completed by {message.source_agent}")
      
      def _handle_error(self, message: AgentMessage) -> None:
          """Handle error from agent."""
          logger.error(f"Error from {message.source_agent}: {message.payload}")
      
      def _handle_status_update(self, message: AgentMessage) -> None:
          """Handle status update from agent."""
          logger.debug(f"Status from {message.source_agent}: {message.payload}")
      
      def run(self) -> None:
          """Main orchestrator loop."""
          self.running = True
          while self.running:
              self._process_one_message()
  ```
* **Success**:
  * All tests from Task 3.1 pass
  * `uv run pytest tests/test_orchestrator.py` succeeds
* **Research References**:
  * .agent-tracking/research/20260122-teambot-research.md (Lines 270-400)
* **Dependencies**: Task 3.1

---

## Phase 4: History Management (TDD)

### Task 4.1: Write frontmatter parsing tests

Write tests for YAML frontmatter parsing BEFORE implementation.

* **Files**:
  * `tests/test_history/test_frontmatter.py` - Frontmatter tests
* **Test Cases**:
  ```python
  """Tests for frontmatter parsing - TDD approach."""
  import pytest
  from datetime import datetime

  class TestHistoryMetadata:
      """Tests for HistoryMetadata dataclass."""
      
      def test_create_metadata(self):
          """Create metadata with required fields."""
          from teambot.history.frontmatter import HistoryMetadata
          
          meta = HistoryMetadata(
              title="Created auth module",
              description="Implemented JWT authentication",
              timestamp=datetime(2026, 1, 22, 10, 30, 0),
              agent_id="builder-1",
              action_type="code_created"
          )
          
          assert meta.title == "Created auth module"
          assert meta.agent_id == "builder-1"
      
      def test_metadata_to_dict(self):
          """Metadata should serialize to dict."""
          from teambot.history.frontmatter import HistoryMetadata
          
          meta = HistoryMetadata(
              title="Test",
              description="Test desc",
              timestamp=datetime(2026, 1, 22, 10, 30, 0),
              agent_id="builder-1",
              action_type="code_created",
              files_affected=["src/auth.py"]
          )
          
          data = meta.to_dict()
          
          assert data["title"] == "Test"
          assert "2026-01-22" in data["timestamp"]
          assert data["files_affected"] == ["src/auth.py"]

  class TestFrontmatterParser:
      """Tests for frontmatter parsing functions."""
      
      def test_parse_valid_frontmatter(self, tmp_path):
          """Parse file with valid YAML frontmatter."""
          from teambot.history.frontmatter import parse_frontmatter
          
          content = '''---
  title: Test Title
  description: Test description
  timestamp: 2026-01-22T10:30:00
  agent_id: builder-1
  action_type: code_created
  ---

  # Content here
  '''
          file_path = tmp_path / "test.md"
          file_path.write_text(content)
          
          metadata, body = parse_frontmatter(file_path)
          
          assert metadata["title"] == "Test Title"
          assert "Content here" in body
      
      def test_parse_missing_frontmatter(self, tmp_path):
          """Handle file without frontmatter gracefully."""
          from teambot.history.frontmatter import parse_frontmatter
          
          content = "# Just content, no frontmatter"
          file_path = tmp_path / "test.md"
          file_path.write_text(content)
          
          metadata, body = parse_frontmatter(file_path)
          
          assert metadata == {}
          assert "Just content" in body
  ```
* **Success**:
  * Tests written and discoverable
  * Tests FAIL initially
* **Research References**:
  * .agent-tracking/research/20260122-teambot-research.md (Lines 480-560) - Frontmatter pattern
* **Dependencies**: Phase 1

---

### Task 4.2: Implement frontmatter parsing

Implement frontmatter parsing to pass tests from Task 4.1.

* **Files**:
  * `src/teambot/history/frontmatter.py` - Frontmatter implementation
* **Implementation**:
  ```python
  """YAML frontmatter parsing for history files."""
  import frontmatter
  from pathlib import Path
  from datetime import datetime
  from typing import Dict, Any, List, Tuple, Optional
  from dataclasses import dataclass, field

  @dataclass
  class HistoryMetadata:
      """Structured frontmatter for history files."""
      title: str
      description: str
      timestamp: datetime
      agent_id: str
      action_type: str
      files_affected: List[str] = field(default_factory=list)
      
      def to_dict(self) -> Dict[str, Any]:
          """Serialize metadata to dictionary."""
          return {
              "title": self.title,
              "description": self.description,
              "timestamp": self.timestamp.isoformat(),
              "agent_id": self.agent_id,
              "action_type": self.action_type,
              "files_affected": self.files_affected,
          }

  def parse_frontmatter(file_path: Path) -> Tuple[Dict[str, Any], str]:
      """Parse YAML frontmatter from a markdown file."""
      try:
          post = frontmatter.load(file_path)
          return dict(post.metadata), post.content
      except Exception:
          # Return empty metadata if parsing fails
          return {}, file_path.read_text()

  def create_frontmatter_content(
      metadata: HistoryMetadata,
      content: str
  ) -> str:
      """Create markdown content with YAML frontmatter."""
      post = frontmatter.Post(content)
      post.metadata = metadata.to_dict()
      return frontmatter.dumps(post)
  ```
* **Success**:
  * All tests from Task 4.1 pass
* **Research References**:
  * .agent-tracking/research/20260122-teambot-research.md (Lines 480-560)
* **Dependencies**: Task 4.1

---

### Task 4.3: Write history manager tests

Write tests for history file manager BEFORE implementation.

* **Files**:
  * `tests/test_history/test_manager.py` - Manager tests
* **Test Cases**: (Similar structure to Tasks 4.1-4.2, tests for create_history_file, scan_frontmatter, load_relevant_history)
* **Success**: Tests written and FAIL initially
* **Dependencies**: Task 4.2

---

### Task 4.4: Implement history manager

Implement history manager to pass tests from Task 4.3.

* **Files**:
  * `src/teambot/history/manager.py` - Manager implementation
* **Success**: All tests pass
* **Dependencies**: Task 4.3

---

### Task 4.5: Write context compactor tests

Write tests for context compaction BEFORE implementation.

* **Files**:
  * `tests/test_history/test_compactor.py` - Compactor tests
* **Success**: Tests written and FAIL initially
* **Dependencies**: Task 4.4

---

### Task 4.6: Implement context compactor

Implement context compactor to pass tests from Task 4.5.

* **Files**:
  * `src/teambot/history/compactor.py` - Compactor implementation
* **Implementation**: (See research document Lines 590-660)
* **Success**: All tests pass
* **Dependencies**: Task 4.5

---

## Phase 5: Configuration System (TDD)

### Task 5.1: Write config loader tests

Write tests for configuration loading BEFORE implementation.

* **Files**:
  * `tests/test_config/test_loader.py` - Loader tests
* **Success**: Tests written and FAIL initially
* **Dependencies**: Phase 1

---

### Task 5.2: Implement config loader

Implement config loader to pass tests.

* **Files**:
  * `src/teambot/config/loader.py` - Loader implementation
* **Success**: All tests pass
* **Dependencies**: Task 5.1

---

### Task 5.3: Create JSON schema and default config

Create schema definition and default configuration file.

* **Files**:
  * `src/teambot/config/schema.py` - Schema definitions
  * `src/teambot/config/default.json` - Default configuration
* **Success**: Schema validates, default config loads
* **Dependencies**: Task 5.2
* **Research References**:
  * .agent-tracking/research/20260122-teambot-research.md (Lines 680-780) - JSON schema

---

## Phase 6: Window Manager (Code-First)

### Task 6.1: Implement window manager

Implement cross-platform window spawning (Code-First approach).

* **Files**:
  * `src/teambot/window_manager.py` - Window manager implementation
* **Implementation**: (See research document Lines 400-480)
* **Success**: Manual verification on current OS
* **Dependencies**: Phase 3

---

### Task 6.2: Add window manager tests

Add tests AFTER implementation (Code-First).

* **Files**:
  * `tests/test_window_manager.py` - Window manager tests
* **Success**: Tests pass, coverage ≥ 70%
* **Dependencies**: Task 6.1

---

## Phase 7: Console Visualization (Code-First)

### Task 7.1: Implement console visualization

Implement Rich-based console output (Code-First).

* **Files**:
  * `src/teambot/visualization/console.py` - Console implementation
* **Implementation**: (See research document Lines 520-590)
* **Success**: Visual verification works
* **Dependencies**: Phase 1

---

### Task 7.2: Add visualization tests

Add tests AFTER implementation (Code-First).

* **Files**:
  * `tests/test_visualization/test_console.py` - Console tests
* **Success**: Tests pass, coverage ≥ 60%
* **Dependencies**: Task 7.1

---

## Phase 8: Agent Runner (Code-First)

### Task 8.1: Implement agent runner

Implement agent process entry point (Code-First).

* **Files**:
  * `src/teambot/agent_runner.py` - Agent runner implementation
* **Success**: Agent receives and processes messages
* **Dependencies**: Phase 3, Phase 4

---

### Task 8.2: Add agent runner tests

Add tests AFTER implementation (Code-First).

* **Files**:
  * `tests/test_agent_runner.py` - Agent runner tests
* **Success**: Tests pass, coverage ≥ 70%
* **Dependencies**: Task 8.1

---

## Phase 9: CLI Entry Point

### Task 9.1: Implement CLI entry point

Create main CLI interface using argparse.

* **Files**:
  * `src/teambot/cli.py` - CLI implementation
* **Implementation**:
  ```python
  """TeamBot CLI entry point."""
  import argparse
  import sys
  from pathlib import Path
  
  from . import __version__
  from .config.loader import load_config
  from .orchestrator import Orchestrator
  
  def main():
      """Main CLI entry point."""
      parser = argparse.ArgumentParser(
          description="TeamBot - Autonomous AI agent teams"
      )
      parser.add_argument(
          "--version",
          action="version",
          version=f"TeamBot {__version__}"
      )
      parser.add_argument(
          "--config",
          type=Path,
          default=Path("teambot.config.json"),
          help="Configuration file path"
      )
      parser.add_argument(
          "objective",
          nargs="?",
          type=Path,
          help="Objective markdown file"
      )
      
      args = parser.parse_args()
      
      if args.objective:
          run_objective(args.config, args.objective)
      else:
          parser.print_help()
  
  def run_objective(config_path: Path, objective_path: Path):
      """Run TeamBot with given objective."""
      config = load_config(config_path)
      orchestrator = Orchestrator(config)
      
      # Load and parse objective
      objective_content = objective_path.read_text()
      
      # Start agents and process objective
      # (Implementation details)
      
      print(f"Running objective: {objective_path}")

  if __name__ == "__main__":
      main()
  ```
* **Success**: `uv run teambot --help` works
* **Dependencies**: All previous phases

---

### Task 9.2: Add end-to-end tests

Add end-to-end tests for CLI workflow.

* **Files**:
  * `tests/test_cli.py` - CLI tests
* **Success**: E2E tests pass
* **Dependencies**: Task 9.1

---

## Phase 10: Integration & Coverage Validation

### Task 10.1: Integration tests

Create integration tests for full workflow.

* **Files**:
  * `tests/test_integration.py` - Integration tests
* **Success**: Integration tests pass
* **Dependencies**: Phase 9

---

### Task 10.2: Coverage validation and gap filling

Validate coverage and fill gaps.

* **Steps**:
  1. Run `uv run pytest --cov=src/teambot --cov-report=html`
  2. Review coverage report
  3. Add tests for any gaps below 80%
  4. Verify all components meet targets
* **Success**: 
  * Overall coverage ≥ 80%
  * All tests pass
  * No ruff errors
* **Dependencies**: Task 10.1

---

## Dependencies Summary

| Dependency | Version | Purpose |
|------------|---------|---------|
| python-dotenv | ≥1.0.0 | Environment variable loading |
| python-frontmatter | ≥1.0.0 | YAML frontmatter parsing |
| rich | ≥13.0.0 | Console visualization |
| pytest | ≥7.4.0 | Testing framework |
| pytest-cov | ≥4.1.0 | Coverage reporting |
| pytest-mock | ≥3.12.0 | Mocking utilities |

## Success Criteria Summary

| Metric | Target | Validation |
|--------|--------|------------|
| All tasks complete | 28/28 | Checklist |
| Tests passing | 100% | `uv run pytest` |
| Coverage | ≥80% | `--cov-report` |
| Linting | 0 errors | `uv run ruff check .` |
| CLI works | Yes | `uv run teambot --help` |
