---
agent: agent
description: Create an architecture decision record following organizational standards
tools: ['edit/createFile', 'edit/createDirectory', 'edit/editFiles', 'search', 'runCommands', 'think', 'fetch', 'todos']
---

# Create Architecture Decision Record

Create a decision record following the standards in `.agent/standards/decision-record-standards.md` and using the template in `.agent/standards/decision-record-template.md`.

## Workflow

1. **Review Standards**: Read `.agent/standards/decision-record-standards.md` to understand requirements
2. **Gather Information**: Ask the user for:
   - What decision needs to be documented?
   - What is the context/problem that led to this decision?
   - What was decided and why?
   - What alternatives were considered and why rejected?
   - Who are the deciders? (names or roles)
   - What are the consequences (benefits AND trade-offs)?
   - What are the follow-up actions?
   - Are there related work items or ADRs?
3. **Generate Record**: Use the template in `.agent/standards/decision-record-template.md`
4. **Create File**: Save to `docs/architecture/decisions/adr-yyyy-mm-dd-title.md` with today's date
5. **Validate**: Ensure all required sections are complete and meaningful

## Requirements

- Use status "Proposed" for new records (user can change after approval)
- Format date as "DD MMMM YYYY" (e.g., "28 October 2025")
- Ensure title is lowercase with hyphens (3-7 words)
- Link to Azure DevOps work items in "Related Docs"
- Include at least 1-2 alternatives with rejection reasons
- Document both positive and negative consequences

## Output

Create the file and confirm:
- File path and name
- Decision title and status
- Remind user to update status to "Accepted" after approval
