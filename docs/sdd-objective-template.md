# TeamBot Objective Template

Use this template to define objectives for TeamBot's file-based orchestration.

## How to Use

1. Copy this file to your objectives directory (e.g., `objectives/my-feature.md`)
2. Fill in the YAML frontmatter AND the sections below with your specific objective details
3. Run: `uv run teambot run objectives/my-feature.md`
4. TeamBot will orchestrate the agents through the workflow defined in `stages.yaml`

---

## Frontmatter

Every objective file MUST include YAML frontmatter at the top. This provides structured,
machine-parseable fields that agents and the orchestrator use for deterministic behavior.

```yaml
---
feature_name: my-feature          # kebab-case, used for artifact directory naming
language: python                  # Primary language: python, javascript, typescript, go, etc.
framework: fastapi                # Primary framework (optional, leave blank if N/A)
test_preference: tdd              # tdd | code-first | hybrid
scope: medium                    # small | medium | large — controls stage skipping
acceptance_scenarios:
  - name: "Descriptive scenario name"
    steps:
      - "Step 1: Do something specific"
      - "Step 2: Do something else"
    expected: "What should happen as the observable outcome"
  - name: "Another scenario"
    steps:
      - "Step 1: Another action"
    expected: "Another expected outcome"
---
```

### Frontmatter Field Reference

| Field | Required | Description |
|-------|----------|-------------|
| `feature_name` | Yes | Kebab-case identifier. Used for `.teambot/{feature_name}/` directory. |
| `language` | Yes | Primary programming language of the feature. |
| `framework` | No | Primary framework or library. Leave blank if not applicable. |
| `test_preference` | Yes | `tdd` (write tests first), `code-first` (write code then tests), or `hybrid`. |
| `scope` | Yes | `small` (< 5 files), `medium` (5-20 files), `large` (20+ files). |
| `acceptance_scenarios` | Yes | List of end-to-end test scenarios with steps and expected outcomes. |

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

## Additional Context

<!-- Optional: Add any additional context that will help the agents -->
<!-- Examples: related documentation, architectural decisions, dependencies -->

---

## Example: Filled Template

```markdown
---
feature_name: user-authentication
language: python
framework: fastapi
test_preference: tdd
scope: medium
acceptance_scenarios:
  - name: "Login via GitHub OAuth"
    steps:
      - "Navigate to /login endpoint"
      - "Click GitHub OAuth button"
      - "Complete GitHub authorization"
      - "Verify redirect back to application"
    expected: "User session created with valid JWT token, user profile stored"
  - name: "Token expiry and refresh"
    steps:
      - "Login and obtain JWT token"
      - "Wait for token expiry (or simulate with expired token)"
      - "Access protected route with expired token"
    expected: "401 Unauthorized returned, user redirected to login"
  - name: "Google OAuth login"
    steps:
      - "Navigate to /login endpoint"
      - "Click Google OAuth button"
      - "Complete Google authorization"
    expected: "User session created, same flow as GitHub OAuth"
---

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

## Additional Context

See docs/auth-requirements.md for detailed authentication requirements.
The existing user model is defined in src/models/user.py.
```

---

## Notes

- **Stage configuration**: The workflow stages (agents, artifacts, exit criteria) are defined in `stages.yaml`. See README.md for customization options.
- **Artifacts**: Generated artifacts will be saved to `.teambot/{feature-name}/` directory, where `{feature-name}` is derived from your objective title (1-3 words, dash-separated). For the example above, this would be `.teambot/user-authentication/`.
- **Parallel execution**: Multiple objectives can run in parallel since each gets its own feature directory.
- **Resume**: If interrupted, resume with `uv run teambot run --resume`.
