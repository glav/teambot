## Objective

Enhancement of the agent message output pane for easy identification and understanding of multi-agent output as the system performs more work.

**Goal**:
- Currently the information/agent agent message output pane on the right has some simple prompt and specific phrase colouring, but for the most part, outputs the agent output without easily showing which agent caused the output, particularly where lots of output as generated from multiple agents
- With that in mind, This goal here is to do the following:
  - Ensure that output from multiple agents is easily identified
  - can be traced back to what agent produced it
  - Is visually pleasing and provides easy discernment between different agent output
  - Removes excessive horizontal scrolling, and prefers word/sentence wrap.

**Problem Statement**:
- When agents output results, particularly multiple agents, there is a heading identifying the agent producing it but all the text is white and when there is lots of output, it is hard to see what agent produced what output.
- When an agent hands off to another agent, the visual indicator/output should indicate this to ensure the flow is easier to identify
- Currently, the user needs to scroll horizontally to read long output, often long way to the right, then scroll back to left, then right again. This is not user friendly and hampers understanding and useability.

**Success Criteria**:
- [ ] Easy identification of agent output for each agent, especially where more than 1 agent performs output simultaneously in the information output pane.
- [ ] No need to horizontally scroll to read output in the information output window.
- [ ] Easy visual indicator in the agent message output pane where the agent hand off to another agent to continue processing and generating output.

---

## Technical Context

**Target Codebase**: Existing teambot

**Primary Language/Framework**: Existing - python

**Testing Preference**: Hybrid

**Key Constraints**:
- Ensure no degradation of terminal and text based experience, especially teambot output formatting.

---

## Additional Context

- How the information is presented for each agents output is currently open. This could be simple coloured grouping, collapsable panels, coloured border with agent heading and context information or other to be identified.
- Additional spacing between output for logical separation between agent output and blobs of logically grouped information would be deemed useful as well.

---
