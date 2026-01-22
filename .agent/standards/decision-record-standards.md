# Decision Record Standards

Decision records (ADRs) capture major project decisions with context, rationale, alternatives, and consequences. This standard defines when and how to create them across MLOps repositories.

## When to Create

**Create decision records for**:
- Architectural, process, or policy decisions
- Technology or framework selection
- Agent framework additions (commands, standards)
- Integration patterns or error handling strategies

**Do NOT create for**:
- Minor implementation details
- Routine bug fixes following established patterns
- Temporary workarounds

## Status Lifecycle

| Status | Meaning |
|--------|---------|
| **Proposed** | Under discussion, seeking feedback |
| **Accepted** | Approved and ready for implementation |
| **Deprecated** | No longer recommended, migration in progress |
| **Superseded** | Replaced by a newer decision (link to it) |

## Naming and Storage

**Location**: `decision-records/` at repository root

**Format**: `yyyy-mm-dd-title.md`
- Date: When decision was accepted
- Title: Short, lowercase, hyphen-separated (3-7 words)

**Examples**:
- ✅ `2025-10-13-adopt-decision-record-template.md`
- ✅ `2025-10-20-agent-command-organization.md`
- ❌ `decision_about_git_hooks.md` (no date, underscores)
- ❌ `ADR-001-git-hooks.md` (no date format)

## Template

Use the template in [`decision-record-template.md`](./decision-record-template.md).

**All sections required**. Write clearly:
- **Context**: Enough background for newcomers to understand the problem
- **Decision**: State what was decided, not just what was discussed
- **Consequences**: Include both benefits AND trade-offs
- **Alternatives**: Document at least 1-2 options and rejection reasons
- **Related Docs**: Always link to the triggering work item

## AI Agent Support

Use `/docs.create-adr` command (if available) or have agents:
1. Ask questions to gather context, decision, alternatives, deciders
2. Generate draft using template
3. Apply correct naming convention
4. Link to work items and related ADRs

## Cross-Referencing

Link related decisions in "Related Docs":
```markdown
- **Related Docs**: 
  - [2025-10-13-adopt-decision-record-template.md](./2025-10-13-adopt-decision-record-template.md)
  - [Azure DevOps Work Item #9057](https://dev.azure.com/NSWPATH-IS-RAD/Ext-HIT/_workitems/edit/9057)
```

Update superseded records: Change Status to "Superseded" and link to new record.

## Examples

**Good examples in Ext-HIT**:
- `2025-10-13-adopt-decision-record-template.md` - Clear, practical
- `2025-10-20-agent-command-organization.md` - Comprehensive with examples
- `2025-10-13-repository-policies.md` - Well-linked

**Anti-patterns**:
- ❌ Vague context: "We need better error handling"
- ❌ No alternatives: "Alternatives: None"
- ❌ Missing consequences: "This will be good"

## Maintenance

- Review "Accepted" decisions annually
- Update status to "Deprecated" when better approaches emerge
- Create superseding records, update both
- Never delete old records - preserve history

---

**References**: [ADR GitHub](https://adr.github.io/) | [Template](./decision-record-template.md)

**Last Updated**: 28 October 2025
