"""Tests for REPL command parser."""

import pytest

from teambot.repl.parser import (
    Command,
    CommandType,
    parse_command,
    ParseError,
)


class TestParseAgentCommands:
    """Tests for @agent command parsing."""

    def test_parse_agent_command_basic(self):
        """Test parsing basic @agent command."""
        result = parse_command("@pm Create a project plan")

        assert result.type == CommandType.AGENT
        assert result.agent_id == "pm"
        assert result.content == "Create a project plan"

    def test_parse_agent_command_with_hyphen(self):
        """Test parsing agent with hyphenated ID."""
        result = parse_command("@builder-1 Implement the feature")

        assert result.type == CommandType.AGENT
        assert result.agent_id == "builder-1"
        assert result.content == "Implement the feature"

    def test_parse_agent_command_secondary_builder(self):
        """Test parsing secondary builder agent."""
        result = parse_command("@builder-2 Write unit tests")

        assert result.type == CommandType.AGENT
        assert result.agent_id == "builder-2"
        assert result.content == "Write unit tests"

    def test_parse_agent_command_ba(self):
        """Test parsing BA agent command."""
        result = parse_command("@ba Analyze the requirements")

        assert result.type == CommandType.AGENT
        assert result.agent_id == "ba"
        assert result.content == "Analyze the requirements"

    def test_parse_agent_command_writer(self):
        """Test parsing writer agent command."""
        result = parse_command("@writer Document the API")

        assert result.type == CommandType.AGENT
        assert result.agent_id == "writer"
        assert result.content == "Document the API"

    def test_parse_agent_command_reviewer(self):
        """Test parsing reviewer agent command."""
        result = parse_command("@reviewer Review the implementation")

        assert result.type == CommandType.AGENT
        assert result.agent_id == "reviewer"
        assert result.content == "Review the implementation"

    def test_parse_agent_command_with_extra_spaces(self):
        """Test parsing command with extra spaces."""
        result = parse_command("@pm   Create   a   plan")

        assert result.type == CommandType.AGENT
        assert result.agent_id == "pm"
        assert result.content == "Create   a   plan"

    def test_parse_agent_command_multiline(self):
        """Test parsing multiline content."""
        result = parse_command("@pm Create a plan\nwith multiple\nlines")

        assert result.type == CommandType.AGENT
        assert result.agent_id == "pm"
        assert result.content == "Create a plan\nwith multiple\nlines"

    def test_parse_agent_command_empty_task_raises(self):
        """Test that @agent without task raises error."""
        with pytest.raises(ParseError, match="task required"):
            parse_command("@pm")

    def test_parse_agent_command_only_spaces_raises(self):
        """Test that @agent with only spaces raises error."""
        with pytest.raises(ParseError, match="task required"):
            parse_command("@pm   ")


class TestParseSystemCommands:
    """Tests for /command system command parsing."""

    def test_parse_help_command(self):
        """Test parsing /help command."""
        result = parse_command("/help")

        assert result.type == CommandType.SYSTEM
        assert result.command == "help"
        assert result.args == []

    def test_parse_status_command(self):
        """Test parsing /status command."""
        result = parse_command("/status")

        assert result.type == CommandType.SYSTEM
        assert result.command == "status"
        assert result.args == []

    def test_parse_history_command(self):
        """Test parsing /history command."""
        result = parse_command("/history")

        assert result.type == CommandType.SYSTEM
        assert result.command == "history"
        assert result.args == []

    def test_parse_quit_command(self):
        """Test parsing /quit command."""
        result = parse_command("/quit")

        assert result.type == CommandType.SYSTEM
        assert result.command == "quit"

    def test_parse_exit_command(self):
        """Test parsing /exit as alias for quit."""
        result = parse_command("/exit")

        assert result.type == CommandType.SYSTEM
        assert result.command == "exit"

    def test_parse_command_with_args(self):
        """Test parsing system command with arguments."""
        result = parse_command("/history pm")

        assert result.type == CommandType.SYSTEM
        assert result.command == "history"
        assert result.args == ["pm"]

    def test_parse_command_with_multiple_args(self):
        """Test parsing system command with multiple args."""
        result = parse_command("/history pm 10")

        assert result.type == CommandType.SYSTEM
        assert result.command == "history"
        assert result.args == ["pm", "10"]

    def test_parse_unknown_system_command(self):
        """Test parsing unknown system command passes through."""
        result = parse_command("/unknown")

        assert result.type == CommandType.SYSTEM
        assert result.command == "unknown"


class TestParseRawInput:
    """Tests for raw input (non-command) parsing."""

    def test_parse_plain_text_as_raw(self):
        """Test plain text is parsed as raw input."""
        result = parse_command("Hello, how are you?")

        assert result.type == CommandType.RAW
        assert result.content == "Hello, how are you?"

    def test_parse_empty_string_as_raw(self):
        """Test empty string is raw."""
        result = parse_command("")

        assert result.type == CommandType.RAW
        assert result.content == ""

    def test_parse_whitespace_as_raw(self):
        """Test whitespace-only is raw."""
        result = parse_command("   ")

        assert result.type == CommandType.RAW
        assert result.content == "   "

    def test_at_in_middle_is_raw(self):
        """Test @ in middle of text is raw input."""
        result = parse_command("Email me at user@example.com")

        assert result.type == CommandType.RAW
        assert result.content == "Email me at user@example.com"

    def test_slash_in_middle_is_raw(self):
        """Test / in middle of text is raw input."""
        result = parse_command("Check the path /home/user")

        assert result.type == CommandType.RAW
        assert result.content == "Check the path /home/user"


class TestCommandObject:
    """Tests for Command dataclass."""

    def test_command_agent_has_correct_fields(self):
        """Test agent command has all fields."""
        cmd = Command(type=CommandType.AGENT, agent_id="pm", content="Do task")

        assert cmd.type == CommandType.AGENT
        assert cmd.agent_id == "pm"
        assert cmd.content == "Do task"
        assert cmd.command is None
        assert cmd.args is None

    def test_command_system_has_correct_fields(self):
        """Test system command has all fields."""
        cmd = Command(type=CommandType.SYSTEM, command="help", args=["topic"])

        assert cmd.type == CommandType.SYSTEM
        assert cmd.command == "help"
        assert cmd.args == ["topic"]
        assert cmd.agent_id is None
        assert cmd.content is None

    def test_command_raw_has_correct_fields(self):
        """Test raw command has all fields."""
        cmd = Command(type=CommandType.RAW, content="Hello")

        assert cmd.type == CommandType.RAW
        assert cmd.content == "Hello"
        assert cmd.agent_id is None
        assert cmd.command is None


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_parse_leading_whitespace_preserved(self):
        """Test leading whitespace before command."""
        result = parse_command("  @pm Do something")

        # Leading space means it's raw input, not a command
        assert result.type == CommandType.RAW

    def test_parse_agent_with_numbers(self):
        """Test agent ID with numbers."""
        result = parse_command("@builder-2 Test task")

        assert result.agent_id == "builder-2"

    def test_parse_very_long_content(self):
        """Test parsing very long content."""
        long_content = "a" * 10000
        result = parse_command(f"@pm {long_content}")

        assert result.type == CommandType.AGENT
        assert len(result.content) == 10000

    def test_parse_special_characters_in_content(self):
        """Test special characters in content."""
        result = parse_command("@pm Create <html> & 'quotes' \"double\"")

        assert result.content == "Create <html> & 'quotes' \"double\""

    def test_parse_unicode_in_content(self):
        """Test unicode characters in content."""
        result = parse_command("@pm Create émoji 🚀 and symbols")

        assert result.type == CommandType.AGENT
        assert "🚀" in result.content


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

    def test_reference_at_end_of_content(self):
        """Test reference at end of content."""
        result = parse_command("@pm Summarize output from $ba")

        assert result.references == ["ba"]

    def test_reference_in_multiline_content(self):
        """Test reference detection in multiline content."""
        result = parse_command("@pm Check this\nbased on $ba\nwork")

        assert result.references == ["ba"]

    def test_command_has_references_field(self):
        """Test Command dataclass has references field."""
        cmd = Command(type=CommandType.AGENT)

        assert hasattr(cmd, "references")
        assert cmd.references == []

    def test_command_references_default_empty(self):
        """Test references defaults to empty list."""
        cmd = Command(type=CommandType.AGENT, agent_id="pm")

        assert cmd.references == []

    def test_reference_with_background(self):
        """Test reference parsing with background operator."""
        result = parse_command("@pm Summarize $ba output &")

        assert result.references == ["ba"]
        assert result.background is True

    def test_multiple_same_agent_refs_deduplicated(self):
        """Test same agent referenced multiple times is deduplicated."""
        result = parse_command("@pm Use $writer intro and $writer conclusion")

        assert result.references == ["writer"]

    def test_references_preserve_order(self):
        """Test references maintain discovery order."""
        result = parse_command("@pm Combine $writer with $ba and $reviewer")

        assert result.references == ["writer", "ba", "reviewer"]
