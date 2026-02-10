# Agent Personas

TeamBot includes 6 specialized agent personas that work together autonomously.

## Overview

| Agent | Persona | Role |
|-------|---------|------|
| `pm` | Project Manager | Planning, coordination, task assignment |
| `ba` | Business Analyst | Requirements, problem definition, specs |
| `writer` | Technical Writer | Documentation, guides, API docs |
| `builder-1` | Builder (Primary) | Implementation, coding, testing |
| `builder-2` | Builder (Secondary) | Implementation, coding, testing |
| `reviewer` | Reviewer | Code review, quality assurance |

## Agent IDs and Aliases

Each agent has a short ID and optional aliases:

| Agent ID | Aliases | Persona |
|----------|---------|---------|
| `pm` | `project_manager` | Project Manager |
| `ba` | `business_analyst` | Business Analyst |
| `writer` | `technical_writer` | Technical Writer |
| `builder-1` | — | Builder (Primary) |
| `builder-2` | — | Builder (Secondary) |
| `reviewer` | — | Reviewer |

Use the short ID (e.g., `@pm`) or the full alias (e.g., `@project_manager`) when addressing agents. If you reference an unknown agent, TeamBot displays an error listing all valid agents.

## Persona Details

### Project Manager (`pm`)

**Role**: Planning, coordination, task assignment

**Capabilities**:
- Creates project plans and task breakdowns
- Breaks down features into manageable tasks
- Coordinates team members
- Tracks progress across stages
- Leads SETUP and PLAN stages

**When to use**: Project planning, task coordination, high-level decisions

### Business Analyst (`ba`)

**Role**: Requirements, problem definition, specifications

**Capabilities**:
- Gathers and analyzes requirements
- Defines business problems and goals
- Creates user stories and acceptance criteria
- Leads BUSINESS_PROBLEM and SPEC stages

**When to use**: Requirements gathering, user stories, acceptance criteria

### Technical Writer (`writer`)

**Role**: Documentation, guides, API docs

**Capabilities**:
- Writes user documentation
- Creates API documentation
- Produces architecture decision records
- Leads documentation tasks in SPEC and RESEARCH stages

**When to use**: Documentation, guides, explanations

### Builder (`builder-1`, `builder-2`)

**Role**: Implementation, coding, testing

**Capabilities**:
- Implements features according to specifications
- Writes unit and integration tests
- Debugs and fixes issues
- Both builders execute concurrently during IMPLEMENTATION

**When to use**: Code implementation, debugging, testing

**Note**: Two builder agents enable parallel development. During IMPLEMENTATION stage, both work concurrently on different parts of the plan.

### Reviewer (`reviewer`)

**Role**: Code review, quality assurance

**Capabilities**:
- Reviews code for quality and correctness
- Identifies bugs and potential improvements
- Verifies compliance with standards
- Leads all review stages (SPEC_REVIEW, PLAN_REVIEW, etc.)

**When to use**: Code reviews, quality checks, validation

## Stage Assignments

Each stage has designated agents:

| Stage | Primary Agent | Review Agent |
|-------|---------------|--------------|
| SETUP | pm | - |
| BUSINESS_PROBLEM | ba, pm | - |
| SPEC | ba, writer | reviewer |
| RESEARCH | builder, writer | - |
| TEST_STRATEGY | builder, reviewer | - |
| PLAN | pm, builder | reviewer |
| IMPLEMENTATION | builder-1, builder-2 | reviewer |
| TEST | builder, reviewer | - |
| POST_REVIEW | pm, reviewer | - |

---

## Next Steps

- [Workflow Stages](workflow-stages.md) - The 14-stage process
- [Interactive Mode](interactive-mode.md) - Using agents interactively
- [Configuration](configuration.md) - Configuring agents
