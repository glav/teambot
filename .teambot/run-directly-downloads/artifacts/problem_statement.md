# Problem Statement: TeamBot Distribution & Installation

## Business Problem

**TeamBot currently requires users to clone the source repository and run via `uv run teambot`**, creating a significant barrier to adoption. This friction-heavy onboarding prevents potential users from quickly evaluating the tool and discourages integration into existing projects.

### Current State Pain Points

| Pain Point | Impact | Affected Users |
|------------|--------|----------------|
| Must clone source repository | High friction, delays evaluation | All new users |
| Requires `uv` knowledge | Unfamiliar tooling for many developers | Non-Python developers |
| No standard `pip install` path | Breaks expected Python package workflow | Python developers |
| No devcontainer support | Cannot use in isolated environments | Enterprise/cloud users |
| No Windows-native guidance | Excludes significant developer population | Windows developers |
| No option for non-Python environments | Forces Python installation | Docker-first teams, Java/JS developers |

### Why This Matters

1. **Lost Adoption**: Users who hit friction during installation often abandon the tool before seeing its value
2. **Competitive Disadvantage**: Similar tools (e.g., `npx create-react-app`, `uvx ruff`) offer zero-install experiences
3. **Enterprise Blockers**: Organizations using devcontainers or standardized environments cannot easily adopt TeamBot
4. **Support Burden**: Lack of clear installation paths generates support requests and confusion

---

## Goals

### Primary Goals

1. **Reduce time-to-first-run to under 60 seconds** for users with Python 3.10+ installed
2. **Enable zero-local-install evaluation** via `uvx` or devcontainer
3. **Support standard Python distribution** via PyPI (`pip install`)
4. **Provide clear installation paths** for Windows, Linux, and macOS users

### Secondary Goals

1. **Support devcontainer-based workflows** without requiring TeamBot in the repository
2. **Enable non-Python environments** via Docker or pre-built binaries (future consideration)
3. **Maintain single source of truth** for version and configuration

---

## Target User Personas

### Persona 1: The Evaluator
> "I want to try TeamBot in 5 minutes without modifying my project"

- **Needs**: Zero-install trial, ephemeral usage
- **Solution**: `uvx copilot-teambot` or Docker image
- **Success Metric**: Can run `teambot --help` within 60 seconds

### Persona 2: The Python Developer
> "I want to install TeamBot like any other Python tool"

- **Needs**: Standard `pip install`, virtual environment support
- **Solution**: PyPI package `copilot-teambot`
- **Success Metric**: `pip install copilot-teambot && teambot init` works

### Persona 3: The Existing Codebase Adopter
> "I want to add TeamBot to my existing project"

- **Needs**: Add as dev dependency, integrate with existing workflow
- **Solution**: `uv add --dev teambot` or `pip install copilot-teambot`
- **Success Metric**: Integrates without disrupting existing tooling

### Persona 4: The Devcontainer User
> "I want TeamBot available in my containerized dev environment"

- **Needs**: Declarative installation, reproducible environments
- **Solution**: Devcontainer feature or base image
- **Success Metric**: Container builds with TeamBot ready in under 60 seconds

### Persona 5: The Windows Developer
> "I work primarily on Windows and need native support"

- **Needs**: Works in PowerShell/CMD, no WSL required
- **Solution**: pip/uvx with Windows-compatible paths
- **Success Metric**: All commands work in PowerShell on Windows 10/11

### Persona 6: The Non-Python Developer
> "I don't have Python installed and don't want to"

- **Needs**: Use TeamBot without Python setup
- **Solution**: Docker image or devcontainer feature
- **Success Metric**: Can use TeamBot with only Docker installed

---

## Success Criteria (Measurable)

| Criterion | Measurement | Target |
|-----------|-------------|--------|
| PyPI installation works | CI test on Python 3.10, 3.11, 3.12 | 100% pass rate |
| `uvx` execution works | Manual and CI verification | Zero prior installation needed |
| Devcontainer feature works | Feature installation time | < 60 seconds |
| Windows compatibility | CI test on Windows runner | All commands pass |
| Documentation coverage | All personas have documented path | 5/5 personas covered |

---

## Scope

### In Scope

- PyPI package publishing (package name: `copilot-teambot`)
- `uvx` support for ephemeral execution
- Devcontainer feature creation
- Windows compatibility verification
- Installation documentation for all personas
- CI/CD testing of installation methods

### Out of Scope (for initial release)

- Standalone binary distribution (requires significant build infrastructure)
- Homebrew formula (can follow later)
- Chocolatey package for Windows (can follow later)
- GUI installer
- Auto-update mechanism

---

## Constraints

| Constraint | Rationale |
|------------|-----------|
| Python 3.10+ required | github-copilot-sdk dependency |
| Copilot CLI not bundled | Licensing; user must install separately |
| Package name must be available | `teambot` likely taken on PyPI |
| Cross-platform compatibility | Windows, Linux, macOS all required |

---

## Dependencies

1. **PyPI account access** for publishing
2. **GitHub Actions** for CI/CD and release automation
3. **Devcontainer spec compliance** for feature creation
4. **Test environments** for Windows, Linux, macOS validation

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| PyPI name `copilot-teambot` unavailable | Low | High | Check availability early; have alternates ready |
| github-copilot-sdk installation issues on Windows | Medium | Medium | Test early; document workarounds |
| Devcontainer feature complexity | Medium | Low | Start with simple pip-based feature |
| User confusion with Copilot CLI prerequisite | High | Medium | Clear documentation and error messages |

---

## Assumptions

1. Users have internet access during installation
2. Users can install Python 3.10+ or Docker (for non-Python path)
3. PyPI upload permissions will be granted
4. GitHub Copilot SDK remains compatible with pip installation

---

## Next Steps

1. **Research Phase**: Document all viable distribution options with pros/cons
2. **Decision**: Select primary distribution method(s)
3. **Specification**: Define detailed acceptance criteria for each method
4. **Implementation Plan**: Create actionable plan for development

---

*Document created: 2026-02-13*  
*Stage: BUSINESS_PROBLEM*  
*Next artifact: distribution_options.md (SPEC stage)*
