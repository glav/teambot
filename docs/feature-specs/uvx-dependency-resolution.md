# Feature Specification: UVX Dependency Resolution

## Problem Statement

~~TeamBot cannot be installed via `uvx --from git+https://github.com/teambot-ai/teambot teambot` because the `github-copilot-sdk==0.1.23` dependency cannot be resolved from standard PyPI.~~

**CORRECTED (2026-02-16):** The original root cause analysis was **incorrect**. The `github-copilot-sdk` IS available on PyPI and resolves correctly.

### Actual Root Cause

The repository URL `https://github.com/teambot-ai/teambot` **does not exist** (or is private/inaccessible):

```bash
$ git ls-remote https://github.com/teambot-ai/teambot
remote: Repository not found.
fatal: repository 'https://github.com/teambot-ai/teambot/' not found
```

The actual repository is at `https://github.com/glav/teambot` (per git remote configuration).

### Current Behavior

```bash
$ uvx --from git+https://github.com/teambot-ai/teambot teambot
× Failed to resolve `--with` requirement
╰─▶ Git operation failed
```

### Expected Behavior

Users should be able to install and run TeamBot directly from the correct git repository URL using `uvx`.

---

## Business Requirements

### BR-1: Correct Repository URL
**Priority:** High  
**Status:** Documentation/User Error

The user was using an incorrect repository URL. No code changes required.

**Resolution:**
- Use the correct URL: `uvx --from git+https://github.com/glav/teambot teambot`
- Or if `teambot-ai/teambot` is intended to be the canonical location, the repository needs to be created/made public

### BR-2: Dependency Transparency (NO LONGER APPLICABLE)
~~**Priority:** Medium~~

~~The source and installation method for `github-copilot-sdk` must be clearly documented.~~

**Status:** Not applicable - `github-copilot-sdk==0.1.23` is correctly published on PyPI and resolves without issues.

### BR-3: Consistent Installation Methods
**Priority:** Medium

All documented installation methods should reference the correct repository URL.

**Acceptance Criteria:**
- [ ] README uses correct git URL
- [ ] Docker/devcontainer configs use correct URL
- [ ] Any documentation referencing `teambot-ai/teambot` is updated

---

## Technical Constraints

| Constraint | Description |
|------------|-------------|
| ~~SDK Availability~~ | ~~`github-copilot-sdk` is not on public PyPI~~ **INCORRECT** - SDK is on PyPI |
| Repository Access | `teambot-ai/teambot` does not exist; actual repo is `glav/teambot` |

---

## Options Analysis

| Option | Approach | Pros | Cons |
|--------|----------|------|------|
| ~~A~~ | ~~Add git dependency URL in pyproject.toml~~ | ~~Works with uvx/pip~~ | **REJECTED - would break build** |
| B | Use correct repository URL | Works immediately | User must know correct URL |
| C | Create/publish `teambot-ai/teambot` | Canonical URL | Requires repo creation |
| D | Publish to PyPI | `uvx teambot` works directly | Requires PyPI publishing |

**Recommendation:** Option B (use correct URL) for immediate fix. Consider Option C or D for better UX long-term.

---

## Dependencies

- Requires knowledge of where `github-copilot-sdk` is hosted
- May require authentication setup for private repositories

---

## Out of Scope

- Changes to the SDK itself
- Alternative SDK implementations
- Offline installation support

---

## Open Questions (Resolved)

1. ~~Where is `github-copilot-sdk` hosted?~~ → **https://github.com/github/copilot-sdk**
2. ~~Is the SDK repository public or private?~~ → **Public**
3. ~~Are there authentication requirements?~~ → **None**

---

## Implementation Notes

*No code changes required for immediate fix.*

**Immediate Resolution:** Use the correct repository URL:
```bash
uvx --from git+https://github.com/glav/teambot teambot
```

**Future Consideration for @builder agents:**
- If `teambot-ai/teambot` should be the canonical URL, create that repository or set up a redirect
- Consider publishing to PyPI for simpler `uvx teambot` usage
- Update any documentation referencing incorrect URLs
