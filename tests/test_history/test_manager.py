"""Tests for history manager - TDD approach."""

from datetime import datetime


class TestHistoryFileManager:
    """Tests for HistoryFileManager class."""

    def test_create_manager(self, temp_teambot_dir):
        """Manager initializes with teambot directory."""
        from teambot.history.manager import HistoryFileManager

        manager = HistoryFileManager(temp_teambot_dir)

        assert manager.teambot_dir == temp_teambot_dir
        assert manager.history_dir == temp_teambot_dir / "history"

    def test_create_history_file(self, temp_teambot_dir):
        """Create a history file with frontmatter."""
        from teambot.history.frontmatter import HistoryMetadata
        from teambot.history.manager import HistoryFileManager

        manager = HistoryFileManager(temp_teambot_dir)
        metadata = HistoryMetadata(
            title="Created auth module",
            description="Implemented JWT authentication",
            timestamp=datetime(2026, 1, 22, 10, 30, 0),
            agent_id="builder-1",
            action_type="code-created",
        )
        content = "## Changes Made\n\nImplemented JWT auth in src/auth/jwt.py"

        filepath = manager.create_history_file(metadata, content)

        assert filepath.exists()
        assert "2026-01-22-103000" in filepath.name
        assert "code-created" in filepath.name

    def test_history_filename_format(self, temp_teambot_dir):
        """Filename follows YYYY-MM-DD-HHMMSS-<action-type>.md format."""
        from teambot.history.frontmatter import HistoryMetadata
        from teambot.history.manager import HistoryFileManager

        manager = HistoryFileManager(temp_teambot_dir)
        metadata = HistoryMetadata(
            title="Test",
            description="Test",
            timestamp=datetime(2026, 1, 22, 14, 45, 30),
            agent_id="builder-1",
            action_type="spec-reviewed",
        )

        filepath = manager.create_history_file(metadata, "Body content")

        assert filepath.name == "2026-01-22-144530-spec-reviewed.md"

    def test_scan_history_files(self, temp_teambot_dir):
        """Scan directory for all history files."""
        from teambot.history.frontmatter import HistoryMetadata
        from teambot.history.manager import HistoryFileManager

        manager = HistoryFileManager(temp_teambot_dir)

        # Create multiple history files
        for i in range(3):
            metadata = HistoryMetadata(
                title=f"Action {i}",
                description=f"Description {i}",
                timestamp=datetime(2026, 1, 22, 10, i, 0),
                agent_id="builder-1",
                action_type="code-created",
            )
            manager.create_history_file(metadata, f"Content {i}")

        files = manager.scan_history_files()

        assert len(files) == 3

    def test_scan_frontmatter_returns_metadata(self, temp_teambot_dir):
        """Scanning returns metadata without loading full content."""
        from teambot.history.frontmatter import HistoryMetadata
        from teambot.history.manager import HistoryFileManager

        manager = HistoryFileManager(temp_teambot_dir)

        # Create history files
        for i in range(2):
            metadata = HistoryMetadata(
                title=f"Action {i}",
                description=f"Description {i}",
                timestamp=datetime(2026, 1, 22, 10, i, 0),
                agent_id=f"builder-{i}",
                action_type="code-created",
            )
            manager.create_history_file(metadata, f"Content {i}" * 1000)

        results = manager.scan_all_frontmatter()

        assert len(results) == 2
        for result in results:
            assert "metadata" in result
            assert "path" in result
            assert "title" in result["metadata"]

    def test_load_history_file(self, temp_teambot_dir):
        """Load a complete history file with metadata and content."""
        from teambot.history.frontmatter import HistoryMetadata
        from teambot.history.manager import HistoryFileManager

        manager = HistoryFileManager(temp_teambot_dir)
        metadata = HistoryMetadata(
            title="Test Title",
            description="Test description",
            timestamp=datetime(2026, 1, 22, 10, 30, 0),
            agent_id="builder-1",
            action_type="code-created",
        )
        original_content = "## Original Content\n\nThis is the body."

        filepath = manager.create_history_file(metadata, original_content)
        loaded_meta, loaded_content = manager.load_history_file(filepath)

        assert loaded_meta["title"] == "Test Title"
        assert "Original Content" in loaded_content

    def test_get_recent_files(self, temp_teambot_dir):
        """Get most recent N history files."""
        from teambot.history.frontmatter import HistoryMetadata
        from teambot.history.manager import HistoryFileManager

        manager = HistoryFileManager(temp_teambot_dir)

        # Create files with different timestamps
        for minute in [5, 10, 15, 20, 25]:
            metadata = HistoryMetadata(
                title=f"Action at {minute}",
                description="Desc",
                timestamp=datetime(2026, 1, 22, 10, minute, 0),
                agent_id="builder-1",
                action_type="code-created",
            )
            manager.create_history_file(metadata, "Content")

        recent = manager.get_recent_files(limit=3)

        assert len(recent) == 3
        # Should be in reverse chronological order
        assert "102500" in recent[0].name  # Most recent first
        assert "102000" in recent[1].name
        assert "101500" in recent[2].name

    def test_filter_by_agent(self, temp_teambot_dir):
        """Filter history files by agent ID."""
        from teambot.history.frontmatter import HistoryMetadata
        from teambot.history.manager import HistoryFileManager

        manager = HistoryFileManager(temp_teambot_dir)

        # Create files from different agents with different timestamps
        for i, agent in enumerate(["builder-1", "builder-2", "reviewer"]):
            metadata = HistoryMetadata(
                title=f"Action by {agent}",
                description="Desc",
                timestamp=datetime(2026, 1, 22, 10, i, 0),  # Different minutes
                agent_id=agent,
                action_type="code-created",
            )
            manager.create_history_file(metadata, "Content")

        results = manager.filter_by_agent("builder-1")

        assert len(results) == 1
        assert results[0]["metadata"]["agent_id"] == "builder-1"


class TestHistoryFilenameGeneration:
    """Tests for history filename generation."""

    def test_generate_filename(self):
        """Generate filename from metadata."""
        from teambot.history.frontmatter import HistoryMetadata
        from teambot.history.manager import generate_history_filename

        metadata = HistoryMetadata(
            title="Test",
            description="Test",
            timestamp=datetime(2026, 1, 22, 14, 30, 45),
            agent_id="builder-1",
            action_type="code-created",
        )

        filename = generate_history_filename(metadata)

        assert filename == "2026-01-22-143045-code-created.md"

    def test_generate_filename_sanitizes_action_type(self):
        """Action type with spaces is sanitized."""
        from teambot.history.frontmatter import HistoryMetadata
        from teambot.history.manager import generate_history_filename

        metadata = HistoryMetadata(
            title="Test",
            description="Test",
            timestamp=datetime(2026, 1, 22, 14, 30, 45),
            agent_id="builder-1",
            action_type="code created with spaces",
        )

        filename = generate_history_filename(metadata)

        assert " " not in filename
        assert "code-created-with-spaces" in filename
