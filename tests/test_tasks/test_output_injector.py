"""Tests for OutputInjector."""

from teambot.tasks.models import TaskResult
from teambot.tasks.output_injector import OutputInjector


class TestOutputInjectorSingleParent:
    """Tests for single parent output injection."""

    def test_inject_single_parent(self):
        """Test injecting output from single parent."""
        injector = OutputInjector()
        parent_results = {"t1": TaskResult(task_id="t1", output="Parent output here", success=True)}

        result = injector.inject("Do something with this", parent_results, ["t1"])

        assert "=== Output from @" in result
        assert "Parent output here" in result
        assert "=== Your Task ===" in result
        assert "Do something with this" in result

    def test_inject_preserves_order(self):
        """Test that task section comes after parent output."""
        injector = OutputInjector()
        parent_results = {"t1": TaskResult(task_id="t1", output="First", success=True)}

        result = injector.inject("My task", parent_results, ["t1"])

        # Parent output should come before task
        parent_pos = result.find("First")
        task_pos = result.find("My task")
        assert parent_pos < task_pos


class TestOutputInjectorMultipleParents:
    """Tests for multiple parent output injection (fan-out)."""

    def test_inject_multiple_parents(self):
        """Test injecting outputs from multiple parents."""
        injector = OutputInjector()
        parent_results = {
            "t1": TaskResult(task_id="t1", output="Output from builder-1", success=True),
            "t2": TaskResult(task_id="t2", output="Output from builder-2", success=True),
        }

        result = injector.inject("Review all", parent_results, ["t1", "t2"])

        assert "Output from builder-1" in result
        assert "Output from builder-2" in result
        assert "=== Your Task ===" in result
        assert "Review all" in result

    def test_inject_multiple_parents_order(self):
        """Test that parent outputs appear in dependency order."""
        injector = OutputInjector()
        parent_results = {
            "t1": TaskResult(task_id="t1", output="First parent", success=True),
            "t2": TaskResult(task_id="t2", output="Second parent", success=True),
        }

        result = injector.inject("Task", parent_results, ["t1", "t2"])

        first_pos = result.find("First parent")
        second_pos = result.find("Second parent")
        assert first_pos < second_pos

    def test_inject_with_agent_id_in_header(self):
        """Test that agent ID appears in section header."""
        injector = OutputInjector()
        parent_results = {
            "task-pm": TaskResult(task_id="task-pm", output="PM output", success=True),
        }

        # Injector should extract agent from task ID or be told agent
        result = injector.inject("Task", parent_results, ["task-pm"], agent_map={"task-pm": "pm"})

        assert "@pm" in result or "pm" in result


class TestOutputInjectorFailureHandling:
    """Tests for handling failed parent outputs."""

    def test_inject_with_failed_parent(self):
        """Test injection notes when parent failed."""
        injector = OutputInjector()
        parent_results = {
            "t1": TaskResult(task_id="t1", output="", success=False, error="Timeout"),
        }

        result = injector.inject("Do task", parent_results, ["t1"])

        assert "failed" in result.lower() or "error" in result.lower()
        assert "Do task" in result

    def test_inject_partial_failure(self):
        """Test injection with some parents failed."""
        injector = OutputInjector()
        parent_results = {
            "t1": TaskResult(task_id="t1", output="Good output", success=True),
            "t2": TaskResult(task_id="t2", output="", success=False, error="Failed"),
        }

        result = injector.inject("Review", parent_results, ["t1", "t2"])

        assert "Good output" in result
        assert "failed" in result.lower()
        assert "Review" in result

    def test_inject_missing_parent(self):
        """Test injection when parent result missing."""
        injector = OutputInjector()
        parent_results = {
            "t1": TaskResult(task_id="t1", output="Output", success=True),
            # t2 is missing
        }

        result = injector.inject("Task", parent_results, ["t1", "t2"])

        assert "Output" in result
        assert "missing" in result.lower() or "not available" in result.lower()


class TestOutputInjectorNoParents:
    """Tests for tasks without parents."""

    def test_inject_no_parents(self):
        """Test injection with no parent dependencies."""
        injector = OutputInjector()

        result = injector.inject("Standalone task", {}, [])

        # Should just return the original prompt
        assert result == "Standalone task"

    def test_inject_empty_deps_list(self):
        """Test injection with empty dependency list."""
        injector = OutputInjector()
        parent_results = {
            "t1": TaskResult(task_id="t1", output="Ignored", success=True),
        }

        result = injector.inject("My task", parent_results, [])

        # Should ignore the results since no deps specified
        assert result == "My task"
        assert "Ignored" not in result
