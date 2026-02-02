# TeamBot Objective Template: Spec-Driven Development (SDD)

## How to Use This Template

1. Copy this file to your objectives directory (e.g., `objectives/my-feature.md`)
2. Fill in the sections below with your specific objective details
3. Run: `uv run teambot run objectives/my-feature.md`
4. TeamBot will orchestrate the agents through the full SDD workflow

---

## Objective

<!-- Replace with your objective description -->
**Goal**: [Describe what you want to build or accomplish]

**Problem Statement**: [What problem does this solve? Why is it needed?]

**Success Criteria**:
- [ ] [Measurable outcome 1]
- [ ] [Measurable outcome 2]
- [ ] [Measurable outcome 3]

---

## Technical Context

**Target Codebase**: [Path or description of the codebase to work on]

**Primary Language/Framework**: [Python, JavaScript, Go, etc.]

**Testing Preference**: [TDD / Code-First / Hybrid]

**Key Constraints**:
- [Performance requirements]
- [Compatibility requirements]
- [Security requirements]

---

## TeamBot Workflow Stages

When you run `teambot run`, the orchestrator guides agents through a **13-stage prescriptive workflow**. Each stage has designated personas, required artifacts, and exit criteria.

### Stage 1: SETUP
- **Lead**: PM Agent
- **Description**: Initialize project, configure agents, and establish working directory
- **Exit Criteria**: Environment ready, configuration validated
- **Prompt / Instructions**: `.agent/commands/sdd/sdd.0-initialize.prompt.md`

### Stage 2: BUSINESS_PROBLEM (Optional)
- **Lead**: BA Agent, PM Agent
- **Description**: Define the business problem, goals, and success criteria
- **Artifact**: `problem_statement.md`
- **Exit Criteria**: Clear problem definition with measurable goals
- *Note: May be skipped for small changes*

### Stage 3: SPEC
- **Lead**: BA Agent, Writer Agent
- **Description**: Create detailed feature specification
- **Artifact**: `feature_spec.md`
- **Exit Criteria**: Complete specification with all required sections

### Stage 4: SPEC_REVIEW
- **Lead**: Reviewer Agent, PM Agent
- **Description**: Review and approve the feature specification
- **Artifact**: `spec_review.md`
- **Decision Gate**: APPROVED → Continue | NEEDS_REVISION → Return to SPEC
- **Iteration**: If NEEDS_REVISION, address feedback and re-review until APPROVED

### Stage 5: RESEARCH
- **Lead**: Builder Agents, Writer Agent
- **Description**: Research technical approaches, analyze project structure, and identify dependencies
- **Artifact**: `research.md`
- **Exit Criteria**: Research document with implementation recommendations

### Stage 6: TEST_STRATEGY
- **Lead**: Builder Agents, Reviewer Agent
- **Description**: Define testing approach (TDD vs Code-First), coverage targets, and test patterns
- **Artifact**: `test_strategy.md`
- **Exit Criteria**: Test strategy document with approach per component

### Stage 7: PLAN
- **Lead**: PM Agent, Builder Agents
- **Description**: Create implementation plan with task breakdown and dependencies
- **Artifact**: `implementation_plan.md`
- **Exit Criteria**: Actionable plan with atomic tasks and clear dependencies

### Stage 8: PLAN_REVIEW
- **Lead**: Reviewer Agent, PM Agent
- **Description**: Review and approve the implementation plan
- **Artifact**: `plan_review.md`
- **Decision Gate**: APPROVED → Continue | NEEDS_REVISION → Return to PLAN
- **Iteration**: If NEEDS_REVISION, address feedback and re-review until APPROVED

### Stage 9: IMPLEMENTATION
- **Lead**: Builder Agents (builder-1, builder-2)
- **Description**: Execute the implementation plan, write code, and implement tests
- **Exit Criteria**: All tasks complete, code implemented per plan

### Stage 10: IMPLEMENTATION_REVIEW
- **Lead**: Reviewer Agent
- **Description**: Review implemented changes for quality, correctness, and adherence to spec
- **Artifact**: `impl_review.md`
- **Decision Gate**: APPROVED → Continue | NEEDS_REVISION → Return to IMPLEMENTATION

### Stage 11: TEST
- **Lead**: Builder Agents, Reviewer Agent
- **Description**: Execute tests and validate implementation meets requirements. New tests should be introduced to ensure that any new functionality is exercised/covered, that the main functional goal is tested, and that the tests pass before continuing.
- **Artifact**: `test_results.md`
- **Exit Criteria**: All tests passing, coverage targets met

### Stage 12: POST_REVIEW
- **Lead**: PM Agent, Reviewer Agent
- **Description**: Final review, retrospective, and validation of all success criteria
- **Artifact**: `post_review.md`
- **Decision Gate**: APPROVED → COMPLETE | NEEDS_REVISION → Address issues

### Stage 13: COMPLETE
- **Description**: Workflow complete, all artifacts finalized
- **Exit Criteria**: All success criteria met, documentation complete

---

## Iteration Protocol

### Review Gate Behavior
At each review stage (SPEC_REVIEW, PLAN_REVIEW, IMPLEMENTATION_REVIEW, POST_REVIEW), the reviewer agent will:

1. **Evaluate** against the stage criteria and required artifacts
2. **Decide**: APPROVED, NEEDS_REVISION, or BLOCKED
3. **If NEEDS_REVISION**:
   - Document specific issues to address
   - Return to the previous stage with feedback
   - Re-execute and re-review
4. **If APPROVED**:
   - Proceed to the next stage
5. **If BLOCKED**:
   - Escalate to PM agent for resolution
   - Do not proceed until unblocked

### Completion Criteria
The workflow is complete when:
- [ ] POST_REVIEW stage returns APPROVED
- [ ] All tests are passing
- [ ] Coverage targets are met
- [ ] No unresolved NEEDS_REVISION items
- [ ] All required artifacts generated

---

## Artifact Locations

After completion, artifacts will be located in `.teambot/{feature-name}` where `{feature-name}` is a 1-3 word feature title with no spaces but dashes separating works (for example 'create-api'):

```
.teambot/{feature-name}
├── workflow_state.json          # Current workflow state
├── history/                     # Task history with frontmatter
├── problem_statement.md         # Business problem (if applicable)
├── feature_spec.md              # Feature specification
├── spec_review.md               # Spec review report
├── research.md                  # Research document
├── test_strategy.md             # Test strategy
├── implementation_plan.md       # Implementation plan
├── plan_review.md               # Plan review report
├── impl_review.md               # Implementation review
├── test_results.md              # Test execution results
└── post_review.md               # Final review and retrospective
```

---

## Agent Coordination Notes

TeamBot orchestrates 6 specialized agent personas:

| Agent | Persona IDs | Primary Stages |
|-------|-------------|----------------|
| **PM Agent** | `pm`, `project_manager` | SETUP, BUSINESS_PROBLEM, PLAN, PLAN_REVIEW, POST_REVIEW |
| **BA Agent** | `ba`, `business_analyst` | BUSINESS_PROBLEM, SPEC |
| **Writer Agent** | `writer`, `technical_writer` | SPEC, RESEARCH |
| **Builder-1** | `builder`, `developer` | RESEARCH, TEST_STRATEGY, PLAN, IMPLEMENTATION, TEST |
| **Builder-2** | `builder`, `developer` | RESEARCH, TEST_STRATEGY, PLAN, IMPLEMENTATION, TEST |
| **Reviewer Agent** | `reviewer` | SPEC_REVIEW, TEST_STRATEGY, PLAN_REVIEW, IMPLEMENTATION_REVIEW, TEST, POST_REVIEW |

---

## Example: Filled Template

```markdown
## Objective

**Goal**: Add user authentication with OAuth2 support

**Problem Statement**: Users currently have no way to securely log in. We need OAuth2
authentication to enable single sign-on with GitHub and Google.

**Success Criteria**:
- [ ] Users can log in via GitHub OAuth
- [ ] Users can log in via Google OAuth
- [ ] Sessions persist with secure JWT tokens
- [ ] 95% test coverage on auth module

## Technical Context

**Target Codebase**: /workspaces/myproject/src/auth/

**Primary Language/Framework**: Python / FastAPI

**Testing Preference**: TDD

**Key Constraints**:
- Must integrate with existing user model
- Tokens must expire after 24 hours
- Must pass OWASP security checklist
```
