# Objective File Format

Objective files define what TeamBot should accomplish. They are written in markdown and provide goals, success criteria, and context for the agent team.

## Basic Format

```markdown
# Objective: Build User Dashboard

## Goals
1. Create user profile page
2. Add settings management
3. Implement notification preferences

## Success Criteria
- [ ] Profile page displays user information
- [ ] Users can edit their profile
- [ ] Notification settings are persisted

## Constraints
- Must work with existing authentication
- Use existing UI component library

## Context
The application uses React for frontend and Express for backend.
```

## Schema

| Section | Required | Description |
|---------|----------|-------------|
| `# Objective:` | Yes | Title/goal of the work |
| `## Goals` | Yes | Numbered list of goals |
| `## Success Criteria` | Yes | Checklist with `- [ ]` items |
| `## Constraints` | No | Technical or business constraints |
| `## Context` | No | Additional context for agents |

## Section Details

### Objective Title

The main heading defines the overall goal:

```markdown
# Objective: Implement User Authentication
```

### Goals

Numbered list of specific goals to accomplish:

```markdown
## Goals
1. Create login endpoint
2. Implement JWT token generation
3. Add password hashing
4. Create logout functionality
```

### Success Criteria

Checkboxes that define when the objective is complete:

```markdown
## Success Criteria
- [ ] Users can log in with email and password
- [ ] JWT tokens are issued on successful login
- [ ] Passwords are securely hashed
- [ ] Sessions expire after 24 hours
```

### Constraints

Technical or business limitations:

```markdown
## Constraints
- Must use existing PostgreSQL database
- Cannot modify user table schema
- Must support OAuth2 integration later
```

### Context

Background information for agents:

```markdown
## Context
The application uses Express.js with TypeScript. Authentication 
should integrate with the existing middleware pattern. See 
`src/middleware/auth.ts` for the current implementation.
```

## SDD Template

For complex features, use the Spec-Driven Development (SDD) template:

```bash
cp docs/sdd-objective-template.md objectives/my-feature.md
```

The SDD template includes additional sections for:
- Detailed requirements
- Technical approach
- Testing strategy
- Rollout plan

## Best Practices

1. **Be specific** - Clear goals lead to better results
2. **Define success** - Measurable criteria help agents know when done
3. **Provide context** - Background helps agents make good decisions
4. **List constraints** - Prevents agents from going in wrong directions

## Example: API Feature

```markdown
# Objective: Add User Search API

## Goals
1. Create GET /api/users/search endpoint
2. Support filtering by name, email, role
3. Implement pagination
4. Add result caching

## Success Criteria
- [ ] Search returns matching users
- [ ] Filters work independently and combined
- [ ] Pagination with limit/offset works
- [ ] Results cached for 5 minutes
- [ ] API documentation updated

## Constraints
- Must use existing auth middleware
- Response time < 200ms for cached results
- Maximum 100 results per page

## Context
The API uses Express with the repository pattern. See 
`src/repositories/userRepository.ts` for database access patterns.
```

---

## Next Steps

- [File-Based Orchestration](file-based-orchestration.md) - Running objectives
- [Workflow Stages](workflow-stages.md) - How objectives are processed
- [Getting Started](getting-started.md) - First run tutorial
