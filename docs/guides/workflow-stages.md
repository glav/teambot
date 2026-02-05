# Workflow Stages

TeamBot enforces a 13-stage prescriptive workflow for autonomous development.

## Stage Flow

```
SETUP → BUSINESS_PROBLEM → SPEC → SPEC_REVIEW → RESEARCH →
TEST_STRATEGY → PLAN → PLAN_REVIEW → IMPLEMENTATION →
IMPLEMENTATION_REVIEW → TEST → POST_REVIEW → COMPLETE
```

## Stage Details

| Stage | Description | Allowed Personas |
|-------|-------------|------------------|
| `SETUP` | Initialize project and configuration | PM |
| `BUSINESS_PROBLEM` | Define business problem and goals (optional) | BA, PM |
| `SPEC` | Create feature specification | BA, Writer |
| `SPEC_REVIEW` | Review and approve spec | Reviewer, PM |
| `RESEARCH` | Research technical approaches | Builder, Writer |
| `TEST_STRATEGY` | Define testing approach | Builder, Reviewer |
| `PLAN` | Create implementation plan | PM, Builder |
| `PLAN_REVIEW` | Review and approve plan | Reviewer, PM |
| `IMPLEMENTATION` | Execute the plan | Builder (parallel) |
| `IMPLEMENTATION_REVIEW` | Review changes | Reviewer |
| `TEST` | Execute tests and validate | Builder, Reviewer |
| `POST_REVIEW` | Final review and retrospective | PM, Reviewer |
| `COMPLETE` | Workflow complete | - |

## Review Stages

Four stages require review approval:
- `SPEC_REVIEW`
- `PLAN_REVIEW`
- `IMPLEMENTATION_REVIEW`
- `POST_REVIEW`

### Review Process

Each review stage iterates up to 4 times:

1. Work agent produces output
2. Review agent evaluates
3. If rejected: feedback incorporated, repeat
4. If approved: advance to next stage
5. After 4 rejections: stop with failure report

### Review Failure

If a review fails after 4 iterations:
- Execution stops with error message
- Detailed failure report saved to `.teambot/failures/`
- Report contains all iteration feedback and suggestions

## Parallel Execution

During `IMPLEMENTATION` stage, both `builder-1` and `builder-2` execute concurrently. This enables:
- Faster development through parallelization
- Multiple components implemented simultaneously
- Coordinated work via shared workspace

## Optional Stages

The `BUSINESS_PROBLEM` stage is optional. If your objective already has clear requirements, this stage may be skipped.

Configure stage behavior in `stages.yaml`:

```yaml
BUSINESS_PROBLEM:
  optional: true
```

---

## Next Steps

- [Agent Personas](agent-personas.md) - The 6 specialized agents
- [Configuration](configuration.md) - Customizing stages
- [File-Based Orchestration](file-based-orchestration.md) - Running workflows
