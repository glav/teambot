"""Configuration schema definitions for TeamBot."""

# JSON schema for configuration validation will be defined here
CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "agents": {"type": "array"},
        "workflow": {"type": "object"},
    },
    "required": ["agents"],
}
