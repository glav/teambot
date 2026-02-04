"""Tests for extended parser syntax (parallel execution)."""

from teambot.repl.parser import (
    CommandType,
    parse_command,
)


class TestBackgroundOperator:
    """Tests for & background operator."""

    def test_parse_background_task(self):
        """Test parsing @agent task &."""
        result = parse_command("@pm Create a plan &")

        assert result.type == CommandType.AGENT
        assert result.agent_id == "pm"
        assert result.content == "Create a plan"
        assert result.background is True

    def test_parse_background_with_extra_spaces(self):
        """Test background with spaces before &."""
        result = parse_command("@pm Create a plan  &")

        assert result.background is True
        assert result.content == "Create a plan"

    def test_parse_non_background_task(self):
        """Test normal task without &."""
        result = parse_command("@pm Create a plan")

        assert result.background is False

    def test_parse_ampersand_in_content(self):
        """Test & in middle of content is not background."""
        result = parse_command("@pm Create plan & execute it")

        # & in middle is part of content, not background operator
        assert result.background is False
        assert "& execute" in result.content

    def test_parse_background_multiagent(self):
        """Test background with multi-agent."""
        result = parse_command("@pm,ba Analyze &")

        assert result.background is True
        assert result.agent_ids == ["pm", "ba"]


class TestMultiAgentOperator:
    """Tests for , multi-agent operator."""

    def test_parse_two_agents(self):
        """Test parsing @agent1,agent2 task."""
        result = parse_command("@pm,ba Analyze requirements")

        assert result.type == CommandType.AGENT
        assert result.agent_ids == ["pm", "ba"]
        assert result.content == "Analyze requirements"

    def test_parse_three_agents(self):
        """Test parsing three agents."""
        result = parse_command("@pm,ba,writer Document the feature")

        assert result.agent_ids == ["pm", "ba", "writer"]

    def test_parse_agents_with_hyphens(self):
        """Test agents with hyphens in IDs."""
        result = parse_command("@builder-1,builder-2 Implement feature")

        assert result.agent_ids == ["builder-1", "builder-2"]

    def test_parse_single_agent_still_works(self):
        """Test single agent returns list with one element."""
        result = parse_command("@pm Create plan")

        assert result.agent_ids == ["pm"]
        assert result.agent_id == "pm"  # Backward compatible

    def test_parse_agents_no_spaces(self):
        """Test agents without spaces around comma."""
        result = parse_command("@pm,ba,writer Task")

        assert result.agent_ids == ["pm", "ba", "writer"]

    def test_parse_agents_with_spaces_invalid(self):
        """Test that spaces in agent list is invalid."""
        # @pm, ba would be parsed as @pm with content ", ba Task"
        # But since we split by comma, "pm, ba" becomes ["pm", " ba"]
        # and " ba" is stripped to "ba", but since it follows comma directly
        # the pattern @pm, matches as single agent "pm" with content starting with ", ba"
        # Actually with our pattern, @pm, ba Task parses as @pm with ", ba Task"
        # The comma is included in agent pattern so it gets "pm,"
        result = parse_command("@pm, ba Task")

        # The regex allows comma in agent pattern, so "pm," is the agent string
        # which splits to ["pm", ""] -> ["pm"]
        assert result.agent_ids == ["pm"]
        # Content starts after the agent match
        assert "ba Task" in result.content


class TestDependencyOperator:
    """Tests for -> dependency operator."""

    def test_parse_simple_dependency(self):
        """Test parsing @a task -> @b task."""
        result = parse_command("@pm Create plan -> @builder-1 Implement it")

        assert result.type == CommandType.AGENT
        assert result.is_pipeline is True
        assert len(result.pipeline) == 2

        assert result.pipeline[0].agent_ids == ["pm"]
        assert result.pipeline[0].content == "Create plan"

        assert result.pipeline[1].agent_ids == ["builder-1"]
        assert result.pipeline[1].content == "Implement it"

    def test_parse_three_stage_pipeline(self):
        """Test parsing three-stage pipeline."""
        result = parse_command("@ba Write specs -> @builder-1 Build -> @reviewer Review")

        assert len(result.pipeline) == 3
        assert result.pipeline[0].agent_ids == ["ba"]
        assert result.pipeline[1].agent_ids == ["builder-1"]
        assert result.pipeline[2].agent_ids == ["reviewer"]

    def test_parse_pipeline_with_multiagent(self):
        """Test pipeline with multi-agent stages."""
        result = parse_command("@pm,ba Plan -> @builder-1,builder-2 Build")

        assert len(result.pipeline) == 2
        assert result.pipeline[0].agent_ids == ["pm", "ba"]
        assert result.pipeline[1].agent_ids == ["builder-1", "builder-2"]

    def test_parse_pipeline_with_background(self):
        """Test pipeline with background operator."""
        result = parse_command("@pm Plan -> @builder-1 Build &")

        assert result.is_pipeline is True
        assert result.background is True

    def test_parse_non_pipeline(self):
        """Test normal command is not pipeline."""
        result = parse_command("@pm Create a plan")

        assert result.is_pipeline is False
        assert result.pipeline is None

    def test_parse_arrow_in_content(self):
        """Test -> in content without second @ is not pipeline."""
        result = parse_command("@pm Create plan -> execute")

        # No @agent after ->, so it's content
        assert result.is_pipeline is False
        assert "-> execute" in result.content


class TestCombinedOperators:
    """Tests for combined operators."""

    def test_multiagent_background(self):
        """Test multi-agent with background."""
        result = parse_command("@pm,ba,writer Analyze feature &")

        assert result.agent_ids == ["pm", "ba", "writer"]
        assert result.background is True

    def test_pipeline_multiagent_background(self):
        """Test full combo: pipeline + multi-agent + background."""
        result = parse_command("@pm,ba Plan -> @builder-1,builder-2 Build &")

        assert result.is_pipeline is True
        assert result.background is True
        assert len(result.pipeline) == 2
        assert result.pipeline[0].agent_ids == ["pm", "ba"]
        assert result.pipeline[1].agent_ids == ["builder-1", "builder-2"]


class TestBackwardCompatibility:
    """Tests ensuring old syntax still works."""

    def test_simple_agent_command(self):
        """Test simple @agent task still works."""
        result = parse_command("@pm Create a plan")

        assert result.type == CommandType.AGENT
        assert result.agent_id == "pm"
        assert result.content == "Create a plan"

    def test_system_command(self):
        """Test /command still works."""
        result = parse_command("/help")

        assert result.type == CommandType.SYSTEM
        assert result.command == "help"

    def test_raw_input(self):
        """Test raw input still works."""
        result = parse_command("hello world")

        assert result.type == CommandType.RAW
        assert result.content == "hello world"
