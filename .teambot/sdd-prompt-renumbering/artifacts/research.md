# SDD Prompt Renumbering - Research Summary

This is a symbolic link to the main research document.

**Full Research Document:**
`.agent-tracking/research/20260308-sdd-prompt-renumbering-research.md`

**Quick Summary:**
- Task: Remove obsolete sdd.4 and renumber prompts 5-8 → 4-7
- File operations: 1 deletion + 5 renames in 2 locations each
- Configuration updates: 5 stages in stages.yaml
- Documentation updates: AGENTS.md, README.md, prompt cross-references
- Test updates: 4 test files with hardcoded references
- Critical discovery: sdd.7c does NOT exist as a file (docs only)
- Approach: Use git mv for history preservation
- Testing: Code-First with existing pytest framework
