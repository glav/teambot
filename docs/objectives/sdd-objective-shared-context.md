## Objective

- Be able to share or pass context and results between agents with teambot smart enough to detect dependencies on other agents and queue/wait accordingly.

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

