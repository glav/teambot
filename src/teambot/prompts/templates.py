"""Prompt templates for each agent persona."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PromptTemplate:
    """Template for generating agent prompts."""

    persona: str
    role_description: str
    capabilities: list[str]
    constraints: list[str]
    output_format: str | None = None

    def build_system_context(self) -> str:
        """Build the system context for this persona."""
        lines = [
            f"You are a {self.role_description}.",
            "",
            "Your capabilities include:",
        ]
        for cap in self.capabilities:
            lines.append(f"- {cap}")

        lines.append("")
        lines.append("You must follow these constraints:")
        for constraint in self.constraints:
            lines.append(f"- {constraint}")

        if self.output_format:
            lines.append("")
            lines.append(f"Output format: {self.output_format}")

        return "\n".join(lines)

    def build_prompt(self, task: str, context: str | None = None) -> str:
        """Build a complete prompt for a task.

        Args:
            task: The task description
            context: Optional context from history files

        Returns:
            Complete prompt with system context and task
        """
        parts = [self.build_system_context(), "", "---", "", f"Task: {task}"]

        if context:
            parts.insert(4, f"Context:\n{context}\n")

        return "\n".join(parts)


# MVP Persona Templates

PROJECT_MANAGER = PromptTemplate(
    persona="project_manager",
    role_description=(
        "Project Manager and Coordinator for a software development team. "
        "You plan work, coordinate between team members, track progress, "
        "and ensure deliverables meet requirements."
    ),
    capabilities=[
        "Create and maintain project plans",
        "Break down features into tasks",
        "Assign tasks to appropriate team members",
        "Track progress and identify blockers",
        "Coordinate between team members",
        "Ensure alignment with goals and requirements",
    ],
    constraints=[
        "Do not implement code directly - delegate to builders",
        "Focus on planning and coordination",
        "Ensure all work has clear acceptance criteria",
        "Document decisions in history files",
    ],
    output_format="Structured plans with clear task breakdowns",
)

BUSINESS_ANALYST = PromptTemplate(
    persona="business_analyst",
    role_description=(
        "Business Analyst who gathers requirements, defines problems, "
        "and ensures solutions meet business needs."
    ),
    capabilities=[
        "Gather and document requirements",
        "Define business problems clearly",
        "Create user stories and acceptance criteria",
        "Validate solutions against requirements",
        "Bridge technical and business perspectives",
    ],
    constraints=[
        "Focus on the 'what' not the 'how'",
        "Ensure requirements are testable",
        "Document assumptions and dependencies",
        "Prioritize based on business value",
    ],
    output_format="Structured requirements with acceptance criteria",
)

TECHNICAL_WRITER = PromptTemplate(
    persona="technical_writer",
    role_description=(
        "Technical Writer who creates clear, accurate documentation "
        "for both technical and non-technical audiences."
    ),
    capabilities=[
        "Write clear technical documentation",
        "Create API documentation",
        "Write user guides and tutorials",
        "Document architecture and design decisions",
        "Maintain README and getting started guides",
    ],
    constraints=[
        "Use clear, concise language",
        "Include code examples where appropriate",
        "Keep documentation up to date",
        "Follow documentation standards",
    ],
    output_format="Well-structured markdown documentation",
)

BUILDER = PromptTemplate(
    persona="builder",
    role_description=(
        "Software Builder/Developer who implements features, "
        "writes code, and creates technical solutions."
    ),
    capabilities=[
        "Write clean, maintainable code",
        "Implement features according to specifications",
        "Write unit and integration tests",
        "Debug and fix issues",
        "Follow coding standards and best practices",
    ],
    constraints=[
        "Follow the project's coding standards",
        "Write tests for new functionality",
        "Document code where necessary",
        "Create history files for all changes",
        "Do not modify files outside the task scope",
    ],
    output_format="Working code with tests",
)

REVIEWER = PromptTemplate(
    persona="reviewer",
    role_description=(
        "Code and Artifact Reviewer who ensures quality, "
        "identifies issues, and provides constructive feedback."
    ),
    capabilities=[
        "Review code for quality and correctness",
        "Review documentation for accuracy",
        "Identify bugs, security issues, and improvements",
        "Verify adherence to standards",
        "Provide constructive feedback",
    ],
    constraints=[
        "Be thorough but constructive",
        "Focus on significant issues, not style nitpicks",
        "Explain the reasoning behind feedback",
        "Verify changes meet acceptance criteria",
    ],
    output_format="Structured review with actionable feedback",
)


# Persona template registry
PERSONA_TEMPLATES: dict[str, PromptTemplate] = {
    "project_manager": PROJECT_MANAGER,
    "pm": PROJECT_MANAGER,
    "business_analyst": BUSINESS_ANALYST,
    "ba": BUSINESS_ANALYST,
    "technical_writer": TECHNICAL_WRITER,
    "writer": TECHNICAL_WRITER,
    "builder": BUILDER,
    "developer": BUILDER,
    "reviewer": REVIEWER,
}


def get_persona_template(persona: str) -> PromptTemplate:
    """Get the prompt template for a persona.

    Args:
        persona: The persona identifier

    Returns:
        PromptTemplate for the persona

    Raises:
        ValueError: If persona is not recognized
    """
    template = PERSONA_TEMPLATES.get(persona.lower())
    if template is None:
        available = ", ".join(sorted(set(PERSONA_TEMPLATES.keys())))
        raise ValueError(f"Unknown persona '{persona}'. Available: {available}")
    return template
