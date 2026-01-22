# Spec-Driven Development (SDD) Workflow

This directory contains the enhanced Spec-Driven Development workflow with integrated review gates, testing strategy, and deterministic outputs.

## 📋 Workflow Overview

The SDD workflow consists of 9 sequential steps with built-in quality gates:

```
0. sdd.0-initialize.prompt.md                → Initialize environment
   ↓
1. sdd.1-create-feature-spec.prompt.md       → Create feature specification
   ↓
2. sdd.2-review-spec.prompt.md               → Review spec for completeness
   ↓
3. sdd.3-research-feature.prompt.md          → Research implementation approach
   ↓
4. sdd.4-determine-test-strategy.prompt.md   → Determine testing approach
   ↓
5. sdd.5-task-planner-for-feature.prompt.md  → Create implementation plan
   ↓
6. sdd.6-review-plan.prompt.md               → Review plan for readiness
   ↓
7. sdd.7-task-implementer-for-feature.prompt.md → Execute implementation
   ↓
8. sdd.8-post-implementation-review.prompt.md → Final validation
```

## 🎯 Key Features

### 1. **Determinism & Validation** (ENHANCED)
- **Output validation checklists** at every step with explicit PASS/FAIL status
- **Mandatory validation commands** before proceeding to next step
- **Placeholder verification** ensuring all `{{tokens}}` are replaced
- **Line number validation** for cross-file references
- **State preservation** with versioning before revisions

### 2. **Testing Integration** (CRITICAL)
- **Deterministic decision matrix** for TDD vs Code-First selection
- **Score-based approach selection** removes subjective decisions
- **Mandatory test phases** in implementation plans
- **Coverage targets** specified and validated
- **Test timing enforcement** (TDD before, Code-First after)

### 3. **Technical Stack Clarification**
- **Explicit stack questions** in spec creation (Step 1)
- **Framework detection** in initialization (Step 0)
- **Testing approach preference** documented early
- **Constraint identification** upfront

### 4. **Review Gates with Approval Protocol** (ENHANCED)
- **Explicit user sign-off** required before proceeding
- **State preservation** before any revisions
- **Revision tracking** with version history
- **Clear decision criteria** (APPROVED/NEEDS_REVISION/BLOCKED)

### 5. **Enhanced Plan Structure** (ENHANCED)
- **Dependency graphs** (mermaid) for plans with >5 tasks
- **Critical path identification** for project planning
- **Phase gate criteria** with explicit completion conditions
- **Effort estimation** tables for planning
- **Sub-phases** for complex task grouping

### 6. **Quick Reference Sections** (NEW)
- Every step has a **Quick Reference table** at the top
- Shows: Purpose, Input, Output, Key Deliverables, Next Step
- Enables quick navigation and understanding

## 📖 Detailed Step Descriptions

### Step 0: Initialize Environment
**File**: `sdd.0-initialize.prompt.md`  
**Role**: Initialization Specialist

**Purpose**: Prepare the environment for SDD workflow.

**Key Features**:
- Verifies prerequisites (Python, uv, Git)
- Creates tracking directories if missing
- Detects technical stack from project
- Checks for existing in-progress work

**Outputs**:
- Initialized `.agent-tracking/` directory structure
- Environment status report

**Next Step**: Run `sdd.1-create-feature-spec.prompt.md`

---

### Step 1: Create Feature Specification
**File**: `sdd.1-create-feature-spec.prompt.md`  
**Role**: Product Manager

**Purpose**: Create comprehensive feature specification through structured questioning.

**Key Features**:
- Guided Q&A process with state management
- Technical stack and testing approach questions
- Reference integration from docs/files
- Session continuity with state files
- Progressive refinement through iterations

**Outputs**:
- Feature spec: `docs/feature-specs/{{name}}.md`
- State file: `.agent-tracking/feature-spec-sessions/{{name}}.state.json`

**Next Step**: Run `sdd.2-review-spec.prompt.md`

---

### Step 2: Review Specification
**File**: `sdd.2-review-spec.prompt.md`  
**Role**: Quality Assurance Specialist

**Purpose**: Validate specification completeness and quality before proceeding to research.

**Validation Checks**:
- ✅ All required sections complete and substantive
- ✅ Technical stack explicitly defined
- ✅ Testing approach documented
- ✅ All requirements are testable
- ✅ Success metrics are measurable
- ✅ Dependencies identified
- ✅ No unresolved critical questions

**Outputs**:
- Review report: `.agent-tracking/spec-reviews/{{date}}-{{name}}-review.md`
- Decision: APPROVED | NEEDS_REVISION | BLOCKED

**If Approved**: Proceed to `sdd.3-research-feature.prompt.md`  
**If Revisions Needed**: Return to `sdd.1-create-feature-spec.prompt.md` with feedback

---

### Step 3: Research Feature
**File**: `sdd.3-research-feature.prompt.md`  
**Role**: Research Specialist

**Purpose**: Conduct deep research on implementation approach with emphasis on testing infrastructure.

**Research Areas**:
- Project structure and patterns
- External documentation and examples
- Testing frameworks and patterns
- Code conventions and best practices
- Technical implementation approaches

**Enhanced Testing Research**:
- Identify existing test framework
- Document test patterns from codebase
- Analyze coverage requirements
- Review 2-3 representative test files
- Document test data management

**Outputs**:
- Research doc: `.agent-tracking/research/{{date}}-{{name}}-research.md`

**Next Step**: Run `sdd.4-determine-test-strategy.prompt.md`

---

### Step 4: Determine Test Strategy
**File**: `sdd.4-determine-test-strategy.prompt.md`  
**Role**: Test Architect

**Purpose**: Analyze feature and recommend optimal testing approach per component.

**Decision Framework**:
1. **Analyze Feature Characteristics**
   - Complexity (algorithm-heavy vs simple)
   - Risk profile (critical vs low-impact)
   - Requirements clarity (well-defined vs exploratory)
   
2. **Recommend Approach**
   - **TDD**: High complexity, clear requirements, critical logic
   - **Code-First**: Simple features, exploratory work, low risk
   - **Hybrid**: Mix of both based on component

3. **Specify Coverage & Patterns**
   - Coverage targets per component
   - Test framework from research
   - Example test patterns
   - Critical scenarios to test

**Outputs**:
- Test strategy: `.agent-tracking/test-strategies/{{date}}-{{name}}-test-strategy.md`

**Next Step**: Run `sdd.5-task-planner-for-feature.prompt.md`

---

### Step 5: Create Task Plan
**File**: `sdd.5-task-planner-for-feature.prompt.md`  
**Role**: Planning Specialist

**Purpose**: Create actionable implementation plan with integrated test phases.

**Enhanced Requirements**:
- Must validate research AND test strategy exist
- Must integrate test tasks per test strategy approach
- Test phases sequenced correctly (TDD before, Code-First after)
- Coverage targets from test strategy included
- Sub-phases for complex tasks

**Plan Structure**:
- Phases with measurable objectives
- Atomic tasks with dependencies
- Line number references to details
- Test implementation phases (MANDATORY for code)

**Outputs**:
- Plan: `.agent-tracking/plans/{{date}}-{{name}}-plan.instructions.md`
- Details: `.agent-tracking/details/{{date}}-{{name}}-details.md`

**Next Step**: Run `sdd.6-review-plan.prompt.md`

---

### Step 6: Review Implementation Plan
**File**: `sdd.6-review-plan.prompt.md`  
**Role**: Implementation Readiness Specialist

**Purpose**: Validate plan quality and implementation readiness.

**Validation Checks**:
- ✅ All plan tasks have corresponding details
- ✅ Test strategy properly integrated
- ✅ Line number references are accurate
- ✅ Dependencies are satisfiable
- ✅ Success criteria are measurable
- ✅ Tasks are actionable and atomic
- ✅ No circular dependencies

**Special Focus on Testing**:
- Test phases present for code features
- Test approach matches test strategy
- Coverage validation tasks included
- Test timing correct (TDD vs Code-First)

**Outputs**:
- Review report: `.agent-tracking/plan-reviews/{{date}}-{{name}}-plan-review.md`
- Decision: APPROVED | NEEDS_REVISION | BLOCKED

**If Approved**: Proceed to `sdd.7-task-implementer-for-feature.prompt.md`  
**If Revisions Needed**: Return to `sdd.5-task-planner-for-feature.prompt.md` with feedback

---

### Step 7: Implement Tasks
**File**: `sdd.7-task-implementer-for-feature.prompt.md`  
**Role**: Implementation Specialist

**Purpose**: Execute implementation plan systematically with test implementation.

**Critical Features**:
- **Tests are REQUIRED** when specified in plan (following test strategy)
- Tests must pass before marking tasks complete
- Follow TDD or Code-First approach per component
- Use test patterns from research
- Meet coverage targets from test strategy

**Process**:
1. Select next unchecked task from plan
2. Load task details by line range
3. Verify dependencies satisfied
4. Load research references AND test strategy
5. Implement per task details (including tests)
6. Validate and run tests
7. Update changes log
8. Mark task complete

**Outputs**:
- Code changes in project files
- Test files (when applicable)
- Changes log: `.agent-tracking/changes/{{date}}-{{name}}-changes.md`

**Next Step**: Run `sdd.8-post-implementation-review.prompt.md`

---

### Step 8: Post-Implementation Review
**File**: `sdd.8-post-implementation-review.prompt.md`  
**Role**: Post-Implementation Review Specialist

**Purpose**: Final validation of implementation before marking workflow complete.

**Validation Checks**:
- ✅ All tasks marked complete
- ✅ All tests passing
- ✅ Coverage targets met
- ✅ Code quality verified (linting)
- ✅ Requirements traced and satisfied
- ✅ Changes log complete

**Cleanup Options**:
- Keep tracking files for reference
- Archive tracking files
- Delete tracking files (specification preserved)

**Outputs**:
- Final review report: `.agent-tracking/implementation-reviews/{{date}}-{{name}}-final-review.md`
- Deployment readiness assessment

---

## 🔍 Quality Standards

### Determinism Checklist
Every output file must:
- [ ] Have all `{{placeholders}}` replaced with actual values
- [ ] Have accurate line number references
- [ ] Have verified cross-references
- [ ] Have no TODO/TBD without resolution plans

### Testing Checklist (NEW)
For code-related features:
- [ ] Test strategy document exists
- [ ] Test framework identified from codebase
- [ ] Coverage targets specified with rationale
- [ ] Test phases in implementation plan
- [ ] Tests implemented following strategy approach
- [ ] Tests passing before task completion
- [ ] Coverage targets met and validated

### Review Gate Checklist
- [ ] Environment initialized (Step 0)
- [ ] Spec reviewed before research (Step 2)
- [ ] Test strategy determined before planning (Step 4)
- [ ] Plan reviewed before implementation (Step 6)
- [ ] Implementation reviewed before completion (Step 8)

### Validation Command Checklist (NEW)
Each step must output explicit validation status:
- [ ] `VALIDATION_STATUS: PASS | FAIL` with details
- [ ] All placeholders listed if any remain
- [ ] User confirmation obtained at review gates

## 📁 Artifact Locations

```
.agent-tracking/
├── feature-spec-sessions/     # Step 1 state files
├── spec-reviews/              # Step 2 review reports
├── research/                  # Step 3 research documents
├── test-strategies/           # Step 4 test strategies
├── plans/                     # Step 5 task plans
├── details/                   # Step 5 task details
├── plan-reviews/              # Step 6 review reports
├── changes/                   # Step 7 change logs
└── implementation-reviews/    # Step 8 final reviews

docs/
└── feature-specs/             # Step 1 specifications
```

## 🎓 Best Practices

### 1. Always Complete Previous Step
Don't skip steps. Each builds on the previous and provides essential input for the next.

### 2. Review Gates Are Critical
The even-numbered steps (2, 4, 6, 8) include review gates that catch issues early before expensive downstream work begins.

### 3. Testing Is Not Optional
For any code implementation, test strategy and test implementation are mandatory, not optional extras.

### 4. Document Decisions Early
Technical stack, testing approach, and key constraints should be documented in Step 1, not discovered later.

### 5. Validate Artifacts
Use the quality checklists to ensure outputs meet standards before proceeding.

### 6. State Management
State files enable session continuity. Keep them updated and validate them when resuming work.

## 🚀 Quick Start

1. **Initialize the environment**: Run `sdd.0-initialize.prompt.md` (recommended first time)
2. **Start a new feature**: Run `sdd.1-create-feature-spec.prompt.md`
3. **Follow the handoff messages**: Each step tells you which step to run next
4. **Don't skip review gates**: Steps 2, 4, 6, 8 save time by catching issues early
5. **Trust the process**: The workflow is designed for quality and completeness

## 📊 Success Metrics

A successfully completed SDD workflow results in:

- ✅ **Complete specification** with all sections filled, technical stack defined, testable requirements
- ✅ **Comprehensive research** with code examples, patterns, and test infrastructure documented
- ✅ **Clear test strategy** with specific approach, coverage targets, and patterns (via decision matrix)
- ✅ **Actionable plan** with phases, atomic tasks, dependency graphs, and integrated tests
- ✅ **Working implementation** with passing tests meeting coverage targets
- ✅ **Full traceability** from requirements through research to implementation
- ✅ **Final validation** confirming all quality gates passed

## 🆘 Troubleshooting

### "Environment not initialized"
- Run `sdd.0-initialize.prompt.md` first
- Verify Python and uv are installed
- Check `.agent-tracking/` directories exist

### "Specification rejected by review"
- Review the review report for specific gaps
- Address critical issues first
- Re-run spec creation with feedback
- Don't proceed to research until approved

### "Test strategy unclear"
- Ensure Step 3 (research) included test infrastructure research
- Use the decision matrix scoring system in Step 4
- Review test strategy output for missing sections
- Consult with team if framework choice is unclear

### "Plan rejected by review"
- Check line number references are accurate
- Verify test strategy is properly integrated
- Ensure all tasks are actionable with clear success criteria
- Fix critical issues before implementation

### "Tests not specified in plan"
- Go back to Step 4 (test strategy) - may be missing
- Update Step 5 (planning) to integrate test tasks
- Re-run Step 6 (plan review) to validate
- Don't proceed to implementation without test tasks

### "Validation command shows FAIL"
- Review the specific items listed as failing
- Address each item before proceeding
- Re-run the step if needed
- Don't ignore validation failures

## 📝 Version History

### Version 3.1 (Current - 2026-01-21)
- **CHANGED**: Renumbered all steps to use whole integers (0-8) instead of half-integers
- **CHANGED**: All internal references updated to new step numbers

### Version 3.0 (2026-01-21)
- **NEW**: Added Step 0: Environment Initialization
- **NEW**: Added Step 8: Post-Implementation Review
- **NEW**: Added Quick Reference tables to all steps
- **NEW**: Added Output Validation Checklists with explicit PASS/FAIL status
- **NEW**: Added Deterministic Decision Matrix for test strategy (scoring system)
- **NEW**: Added Explicit Approval Protocol with user sign-off
- **NEW**: Added Dependency Graph requirement for complex plans (>5 tasks)
- **NEW**: Added Phase Gate Criteria with completion conditions
- **NEW**: Added State Preservation before revisions
- **ENHANCED**: All steps now have validation commands before handoff
- **ENHANCED**: Review gates require explicit user confirmation
- **ENHANCED**: Plan structure includes effort estimation and critical path

### Version 2.0 (2026-01-21)
- Added Step 1.5: Specification Review
- Added Step 2.5: Test Strategy Determination
- Added Step 3.5: Implementation Plan Review
- Enhanced Step 1 with technical stack questions
- Enhanced Step 2 with testing infrastructure research
- Enhanced Step 3 with test phase requirements and sub-phases
- Enhanced Step 4 to require test implementation
- Updated templates with testing sections and sub-phases
- Added determinism improvements across all steps

### Version 1.0 (Original)
- Step 1: Create Feature Specification
- Step 2: Research Feature
- Step 3: Create Task Plan
- Step 4: Implement Tasks

---

**Last Updated**: 2026-01-21  
**Version**: 3.0  
**Maintained By**: SDD Workflow Enhancement Project
