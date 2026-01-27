"""Tests for frontmatter parsing - TDD approach."""

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
            action_type="code_created",
        )

        assert meta.title == "Created auth module"
        assert meta.description == "Implemented JWT authentication"
        assert meta.agent_id == "builder-1"
        assert meta.action_type == "code_created"

    def test_metadata_to_dict(self):
        """Metadata should serialize to dict."""
        from teambot.history.frontmatter import HistoryMetadata

        meta = HistoryMetadata(
            title="Test",
            description="Test desc",
            timestamp=datetime(2026, 1, 22, 10, 30, 0),
            agent_id="builder-1",
            action_type="code_created",
            files_affected=["src/auth.py"],
        )

        data = meta.to_dict()

        assert data["title"] == "Test"
        assert "2026-01-22" in data["timestamp"]
        assert data["files_affected"] == ["src/auth.py"]

    def test_metadata_from_dict(self):
        """Metadata should deserialize from dict."""
        from teambot.history.frontmatter import HistoryMetadata

        data = {
            "title": "Test Title",
            "description": "Test desc",
            "timestamp": "2026-01-22T10:30:00",
            "agent_id": "builder-1",
            "action_type": "code_created",
            "files_affected": ["src/auth.py"],
        }

        meta = HistoryMetadata.from_dict(data)

        assert meta.title == "Test Title"
        assert meta.agent_id == "builder-1"
        assert isinstance(meta.timestamp, datetime)


class TestFrontmatterParser:
    """Tests for frontmatter parsing functions."""

    def test_parse_valid_frontmatter(self, tmp_path):
        """Parse file with valid YAML frontmatter."""
        from teambot.history.frontmatter import parse_frontmatter

        content = """---
title: Test Title
description: Test description
timestamp: 2026-01-22T10:30:00
agent_id: builder-1
action_type: code_created
---

# Content here
This is the body content.
"""
        file_path = tmp_path / "test.md"
        file_path.write_text(content)

        metadata, body = parse_frontmatter(file_path)

        assert metadata["title"] == "Test Title"
        assert metadata["agent_id"] == "builder-1"
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

    def test_parse_frontmatter_only_reads_metadata(self, tmp_path):
        """Quick scan should only read frontmatter, not full content."""
        from teambot.history.frontmatter import scan_frontmatter_only

        content = (
            """---
title: Quick Scan Test
description: Short desc
timestamp: 2026-01-22T10:30:00
agent_id: builder-1
action_type: code_created
---

# Very large content below
"""
            + "Large content " * 10000
        )

        file_path = tmp_path / "large.md"
        file_path.write_text(content)

        metadata = scan_frontmatter_only(file_path)

        assert metadata["title"] == "Quick Scan Test"
        assert metadata["agent_id"] == "builder-1"


class TestCreateFrontmatter:
    """Tests for creating frontmatter content."""

    def test_create_frontmatter_string(self):
        """Create YAML frontmatter string from metadata."""
        from teambot.history.frontmatter import HistoryMetadata, create_frontmatter

        meta = HistoryMetadata(
            title="Test Title",
            description="Test description",
            timestamp=datetime(2026, 1, 22, 10, 30, 0),
            agent_id="builder-1",
            action_type="code_created",
        )

        frontmatter_str = create_frontmatter(meta)

        assert "---" in frontmatter_str
        assert "title: Test Title" in frontmatter_str
        assert "agent_id: builder-1" in frontmatter_str

    def test_create_history_file_content(self):
        """Create complete history file with frontmatter and body."""
        from teambot.history.frontmatter import HistoryMetadata, create_history_content

        meta = HistoryMetadata(
            title="Created feature",
            description="Implemented new feature",
            timestamp=datetime(2026, 1, 22, 10, 30, 0),
            agent_id="builder-1",
            action_type="code_created",
        )
        body = "## Changes Made\n\nImplemented the feature."

        content = create_history_content(meta, body)

        assert content.startswith("---")
        assert "title: Created feature" in content
        assert "## Changes Made" in content
