"""Tests for TaskGraph (DAG) with cycle detection."""

import pytest

from teambot.tasks.graph import TaskGraph, CycleDetectedError


class TestTaskGraphBasic:
    """Basic TaskGraph tests."""

    def test_empty_graph(self):
        """Test empty graph."""
        graph = TaskGraph()

        assert graph.task_count == 0
        assert graph.get_ready_tasks() == []

    def test_add_task_no_deps(self):
        """Test adding task without dependencies."""
        graph = TaskGraph()
        graph.add_task("t1", [])

        assert graph.task_count == 1
        assert "t1" in graph.get_ready_tasks()

    def test_add_task_with_deps(self):
        """Test adding task with dependencies."""
        graph = TaskGraph()
        graph.add_task("t1", [])
        graph.add_task("t2", ["t1"])

        assert graph.task_count == 2
        assert graph.get_dependencies("t2") == ["t1"]

    def test_get_ready_tasks(self):
        """Test getting ready tasks (no pending dependencies)."""
        graph = TaskGraph()
        graph.add_task("t1", [])
        graph.add_task("t2", [])
        graph.add_task("t3", ["t1"])

        ready = graph.get_ready_tasks()
        assert "t1" in ready
        assert "t2" in ready
        assert "t3" not in ready

    def test_mark_completed(self):
        """Test marking task as completed."""
        graph = TaskGraph()
        graph.add_task("t1", [])
        graph.add_task("t2", ["t1"])

        assert "t2" not in graph.get_ready_tasks()

        graph.mark_completed("t1")

        assert "t2" in graph.get_ready_tasks()

    def test_get_dependents(self):
        """Test getting tasks that depend on a given task."""
        graph = TaskGraph()
        graph.add_task("t1", [])
        graph.add_task("t2", ["t1"])
        graph.add_task("t3", ["t1"])
        graph.add_task("t4", ["t2"])

        dependents = graph.get_dependents("t1")
        assert "t2" in dependents
        assert "t3" in dependents
        assert "t4" not in dependents


class TestTaskGraphCycleDetection:
    """Tests for cycle detection."""

    def test_no_cycle_linear(self):
        """Test linear chain has no cycle."""
        graph = TaskGraph()
        graph.add_task("t1", [])
        graph.add_task("t2", ["t1"])
        graph.add_task("t3", ["t2"])

        # Should not raise
        assert graph.task_count == 3

    def test_no_cycle_diamond(self):
        """Test diamond pattern has no cycle."""
        graph = TaskGraph()
        graph.add_task("t1", [])
        graph.add_task("t2", ["t1"])
        graph.add_task("t3", ["t1"])
        graph.add_task("t4", ["t2", "t3"])

        # Should not raise
        assert graph.task_count == 4

    def test_simple_cycle_detected(self):
        """Test simple A->B->A cycle is detected."""
        graph = TaskGraph()
        graph.add_task("t1", [])
        graph.add_task("t2", ["t1"])

        with pytest.raises(CycleDetectedError) as exc_info:
            graph.add_task("t1", ["t2"])  # t1 depends on t2, but t2 depends on t1

        assert "cycle" in str(exc_info.value).lower()

    def test_self_cycle_detected(self):
        """Test self-referencing cycle is detected."""
        graph = TaskGraph()

        with pytest.raises(CycleDetectedError):
            graph.add_task("t1", ["t1"])  # t1 depends on itself

    def test_indirect_cycle_detected(self):
        """Test indirect A->B->C->A cycle is detected."""
        graph = TaskGraph()
        graph.add_task("t1", [])
        graph.add_task("t2", ["t1"])
        graph.add_task("t3", ["t2"])

        with pytest.raises(CycleDetectedError):
            graph.add_task("t1", ["t3"])  # Creates t1->t2->t3->t1 cycle


class TestTaskGraphTopologicalOrder:
    """Tests for topological ordering."""

    def test_topological_order_simple(self):
        """Test simple topological order."""
        graph = TaskGraph()
        graph.add_task("t1", [])
        graph.add_task("t2", ["t1"])
        graph.add_task("t3", ["t2"])

        order = graph.get_topological_order()

        assert order.index("t1") < order.index("t2")
        assert order.index("t2") < order.index("t3")

    def test_topological_order_parallel(self):
        """Test topological order with parallel tasks."""
        graph = TaskGraph()
        graph.add_task("t1", [])
        graph.add_task("t2", [])
        graph.add_task("t3", ["t1", "t2"])

        order = graph.get_topological_order()

        assert order.index("t1") < order.index("t3")
        assert order.index("t2") < order.index("t3")

    def test_topological_order_diamond(self):
        """Test topological order with diamond pattern."""
        graph = TaskGraph()
        graph.add_task("a", [])
        graph.add_task("b", ["a"])
        graph.add_task("c", ["a"])
        graph.add_task("d", ["b", "c"])

        order = graph.get_topological_order()

        assert order.index("a") < order.index("b")
        assert order.index("a") < order.index("c")
        assert order.index("b") < order.index("d")
        assert order.index("c") < order.index("d")


class TestTaskGraphFailureHandling:
    """Tests for failure handling in graph."""

    def test_mark_failed_skips_dependents(self):
        """Test that marking task failed returns dependents to skip."""
        graph = TaskGraph()
        graph.add_task("t1", [])
        graph.add_task("t2", ["t1"])
        graph.add_task("t3", ["t2"])

        to_skip = graph.mark_failed("t1")

        assert "t2" in to_skip
        assert "t3" in to_skip

    def test_mark_failed_partial_deps(self):
        """Test failure with partial dependencies (fan-out)."""
        graph = TaskGraph()
        graph.add_task("t1", [])
        graph.add_task("t2", [])
        graph.add_task("t3", ["t1", "t2"])  # Depends on both

        # Mark only t1 as failed - t3 should still wait for t2
        to_skip = graph.mark_failed("t1")

        # t3 has partial failure but should wait to see if t2 succeeds
        # (partial failure handling - continue with available)
        assert "t3" not in to_skip  # Don't skip yet, wait for t2

    def test_mark_failed_all_parents_failed(self):
        """Test when all parents fail, dependent is skipped."""
        graph = TaskGraph()
        graph.add_task("t1", [])
        graph.add_task("t2", [])
        graph.add_task("t3", ["t1", "t2"])

        graph.mark_failed("t1")
        to_skip = graph.mark_failed("t2")

        # Now both parents failed, t3 should be skipped
        assert "t3" in to_skip
