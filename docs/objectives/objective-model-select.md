## Objective

- Provide an easy way, like to copilot CLI to be able to use a specific model when asking teambot agents to perform a task.

**Goal**:

- Teambot currently does not support model selection or indicate what model is being used when performing tasks.
- Like the Copilot CLI I would like to be able to specify a model when requesting an agent to perform a task.
- Each agent should be able to use a default model or a specific model.
- Each agent should be able to have a default model specified.
  - For example, 'pm' agent may have Claude opus 4.5 model as the default, 'ba' agent may have GPT 5.2 Codex as the default
- Only models supported by the Copilot SDk are supported in teambot.
- The model currently being used should be evident in the terminal UI display so it is easy to see which agent has which model assigned to a task.
- We should be able to list all available models that we can choose from.
- When doing file based orchestration, we should be able to use different models per agent which will follow whatever the default model is for the agent currently running the file based orchestration task.

**Problem Statement**:

- Teambot currently does not support using different models.
- Each model has its strengths, speed and also related costs.
- To provide a cost effective but still good experience, we need to allow teambot to use a selection of models via configuration
- This allows the user to configure the most cost effective but suitable approach for agents.
- This also allows one model to either plan or implement, while another model performs review and feedback.

**Success Criteria**:
- [ ] Be able to easily see what model an agent is using in the terminal UI and /status command.
- [ ] Be able to easily see what agent and model is being used when issuing /tasks command.
- [ ] Be able to select a specific model when entering an agent directive via user input either inline or for the remainder of the session for that agent.
- [ ] Configuration should support a default model for each agent persona.
- [ ] Errors should be shown when an invalid model is selected.


---

## Technical Context

**Target Codebase**:

- Teambot

**Primary Language/Framework**:

- Current - python

**Testing Preference**:

- Follow current pattern

**Key Constraints**:
- Only models supported by Github Copilot CLI and the supporting SDK

---

## Additional Context

- The models assigned to each agent should be displayed in the initial display of agents and their activity but in a concise and visually pleasing way that does not interfere with the current display mechanics
- Any output documentation files like specifications, plans, etc should indicate what model was used to produce it.
  - The exception is files like the README.md which constitute user documentation and the model that produced it is not relevant.
  - Only plans, specs etc that are used by models/agents to produce an output require the model to be listed that produced it.

---
