---
agent: "agent"
description: "Generate pull request description using the defined template"
tools: ['execute/getTerminalOutput', 'execute/runInTerminal', 'read/terminalSelection', 'read/terminalLastCommand', 'read/readFile', 'search']
---

# Create Azure DevOps Pull Request description

Use the Azure DevOps PR template from #file:../../../.azuredevops/pull_request_template.md

## Instructions

1. Compare the changes from the current branch to main branch.
2. Identify key changes, including new features, bug fixes, and documentation updates.
3. Attempt to infer the work item it from the branch name or commit messages. eg. If the branch name is feat/1234-add-login, the work item ID is 1234. If you cannot infer the work item ID, ask the user what the work item is is.
  - When filling in the work item id, ensure it follows this exact format: '#<work item id>'.
  - There should be no space in between the '#' and the work item id.
  - There should be no extra text, only the work item id.
4. Fill out each section of the PR template with relevant information:
   - **Description**: Summarize the changes and their impact.
   - **Steps to Reproduce Bug and Validate Solution**: If applicable, provide steps to reproduce any fixed bugs.
   - **PR Checklist**: Ensure all checklist items are addressed.
   - **Does This Introduce a Breaking Change?**: Indicate if there are breaking changes.
   - **Testing**: Describe testing performed and environments used.
   - **Any Relevant Logs or Outputs**: Attach logs or screenshots if necessary.
   - **Other Information or Known Dependencies**: Include any additional relevant information.
5. Ensure the description is clear, concise, and follows the template structure.
6. Compliance:
   - Ensure description captures both what changed and why
   - Include work item linkage if applicable
   - Provide sufficient detail for reviewers
   - Ensure all checklist items from the template are present, and only verifiably completed items are checked.
   - There is a maximum description length of 4000 characters, including all letters, numbers, punctuation, spaces, tabs, newlines (`\n`), carriage returns (`\r`), emojis, and any other special. Ensure that the output does not exceed this limit.

If you do not have enough information to fill out a section, ask for input from the user.
If the user is enable to provide the information, leave the section blank for them to fill in later with a placeholder.