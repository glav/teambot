## Objective

<!-- Replace with your objective description -->
**Goal**: I would like to enhance the teambot solution so that when a user enters a prompt, they can reference another agents results or output for further processing or actions. It needs to be intuitive and easy to use.

**Problem Statement**: Sometimes a user will enter a prompt without using any chaining syntax (ie. '->' ) and then realise that the output would be good to have another agent act on it. Rather than having to copy the output and paste in another prompt, it would be very beneficial to reference that easily as part of a new prompt. This also provides the flexibility of agent interaction ad hoc by the user.
Examples:
```
@reviewer Can you review the entire codebase and identify any areas that can be simplified or cleaned up?
@builder-1 Can you implement the high priority recommendations from $reviewer
```
The above example will cause the 'builder-1' agent to -wait- for 'reviewer' agent to complete the review, then act on the 'reviewer' agent output.
The status of @reviewer will be reflected as performing the task while the 'builder-1' agent will reflect as waiting until it begins to act on the output of the 'reviewer' agent, when it will be reflected as performing the task.

**Success Criteria**:
- [ ] Must provide an easy to use syntax to reference another agents results or output like '$pm' for the 'pm' agents results.
- [ ] If a prompt references another agents results, then the agent on which references the other agent will wait for that agent to complete its output then perform the action using those latest results.
- [ ] The readme.md clearly states how this syntax is used, along with the '->' syntax with a comparison of differences for both.
- [ ] The agent status should be accurately reflected in what agent is waiting, executing or idle.

---

## Technical Context

**Target Codebase**: src/teambot/

**Primary Language/Framework**: Python - existing language

**Testing Preference**: Hybrid - choose best approach for feature development

**Key Constraints**:
- None
---

## TeamBot Workflow Stages

When you run `teambot run`, the orchestrator guides agents through a **13-stage prescriptive workflow**. Each stage has designated personas, required artifacts, and exit criteria.

### Output directory
- feature specs: `docs/feature-specs/`
### Stage 1: SETUP
- **Lead**: PM Agent
- **Required**: NO - Already performed as part of previous step
- **Description**: Initialize project, configure agents, and establish working directory
- **Exit Criteria**: Environment ready, configuration validated
- Can skip this step

### Stage 2: BUSINESS_PROBLEM (Optional)
- **Lead**: BA Agent, PM Agent
- **Description**: Define the business problem, goals, and success criteria
- **Required**: NO
- **Artifact**: `problem_statement.md`
- **Exit Criteria**: Clear problem definition with measurable goals
- *Note: May be skipped for small changes*
- Can skip this step

### Stage 3: SPEC
- **Lead**: BA Agent, Writer Agent
- **Description**: Create detailed feature specification
- **Artifact**: `feature_spec.md`
- **Exit Criteria**: Complete specification with all required sections
- **Prompt / Instructions**: `.agent/commands/sdd/sdd.1-create-feature-spec.prompt.md`

### Stage 4: SPEC_REVIEW
- **Lead**: Reviewer Agent, PM Agent
- **Description**: Review and approve the feature specification
- **Artifact**: `spec_review.md`
- **Decision Gate**: APPROVED → Continue | NEEDS_REVISION → Return to SPEC
- **Iteration**: If NEEDS_REVISION, address feedback and re-review until APPROVED
- **Prompt / Instructions**: `.agent/commands/sdd/sdd.2-review-spec.prompt.md`

### Stage 5: RESEARCH
- **Lead**: Builder Agents, Writer Agent
- **Description**: Research technical approaches, analyze project structure, and identify dependencies
- **Artifact**: `research.md`
- **Exit Criteria**: Research document with implementation recommendations
- **Prompt / Instructions**: `.agent/commands/sdd/sdd.3-research-feature.prompt.md`

### Stage 6: TEST_STRATEGY
- **Lead**: Builder Agents, Reviewer Agent
- **Description**: Define testing approach (TDD vs Code-First), coverage targets, and test patterns
- **Artifact**: `test_strategy.md`
- **Exit Criteria**: Test strategy document with approach per component
- **Prompt / Instructions**: `.agent/commands/sdd/sdd.4-determine-test-strategy.prompt.md`

### Stage 7: PLAN
- **Lead**: PM Agent, Builder Agents
- **Description**: Create implementation plan with task breakdown and dependencies
- **Artifact**: `implementation_plan.md`
- **Exit Criteria**: Actionable plan with atomic tasks and clear dependencies
- **Prompt / Instructions**: `.agent/commands/sdd/sdd.5-task-planner-for-feature.prompt.md`

### Stage 8: PLAN_REVIEW
- **Lead**: Reviewer Agent, PM Agent
- **Description**: Review and approve the implementation plan
- **Artifact**: `plan_review.md`
- **Decision Gate**: APPROVED → Continue | NEEDS_REVISION → Return to PLAN
- **Iteration**: If NEEDS_REVISION, address feedback and re-review until APPROVED
- **Prompt / Instructions**: `.agent/commands/sdd/sdd.6-review-plan.prompt.md`

### Stage 9: IMPLEMENTATION
- **Lead**: Builder Agents (builder-1, builder-2)
- **Description**: Execute the implementation plan, write code, and implement tests
- **Exit Criteria**: All tasks complete, code implemented per plan
- **Prompt / Instructions**: `.agent/commands/sdd/sdd.7-task-implementer-for-feature.prompt.md`

### Stage 10: IMPLEMENTATION_REVIEW
- **Lead**: Reviewer Agent
- **Description**: Review implemented changes for quality, correctness, and adherence to spec
- **Artifact**: `impl_review.md`
- **Decision Gate**: APPROVED → Continue | NEEDS_REVISION → Return to IMPLEMENTATION
- **Prompt / Instructions**: `.agent/commands/sdd/sdd.8-post-implementation-review.prompt.md`

### Stage 11: TEST
- **Lead**: Builder Agents, Reviewer Agent
- **Description**: Execute tests and validate implementation meets requirements
- **Artifact**: `test_results.md`
- **Exit Criteria**: All tests passing, coverage targets met

### Stage 12: POST_REVIEW
- **Lead**: PM Agent, Reviewer Agent
- **Description**: Final review, retrospective, and validation of all success criteria
- **Artifact**: `post_review.md`
- **Decision Gate**: APPROVED → COMPLETE | NEEDS_REVISION → Address issues
- **Prompt / Instructions**: `.agent/commands/sdd/sdd.8-post-implementation-review.prompt.md`

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
- [ ] Success criteria is met

---

## Artifact Locations

After completion, artifacts will be located in `.teambot/`:

```
.teambot/
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
