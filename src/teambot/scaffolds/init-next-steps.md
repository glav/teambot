## Recommended Next Steps

### 1. Configure Per-Agent Models (Optional)

For better quality and cost optimization, customize models for each agent
in teambot.json:

```json
{
  "agents": [
    {
      "id": "reviewer",
      "model": "claude-opus-4.5"
    },
    {
      "id": "builder-1",
      "model": "gpt-5.1-codex"
    }
  ]
}
```

### 2. Run Your First Objective

Create an objective file and run TeamBot:

```bash
teambot run objectives/your-feature.md
```

See docs/sdd-objective-template.md for the objective file format.

### 3. Explore Interactive Mode

Start interactive mode for ad-hoc tasks:

```bash
teambot run
```

Type `@pm help` to get started with the Project Manager agent.

### 4. Learn More

- View available models: Run TeamBot then use `/models` command
- Configure notifications: Edit the `notifications` section in teambot.json
- Customize agents: Edit files in `.github/agents/` directory
