# Problem Statement: Worktree Workflow Enhancement

## Business Problem

### Current State

TeamBot's `--worktree` option creates isolated Git worktrees for development tasks, allowing parallel work without branch switching. However, the current implementation has a critical gap in objective file handling:

1. **Objective file validation occurs before worktree creation** - The CLI validates that the objective file exists in the source repository
2. **No objective file migration** - After worktree creation, the working directory changes to the worktree, but the objective file is not copied over
3. **Relative paths break silently** - Objective files specified with relative paths become invalid after the `chdir` to the worktree
4. **No base branch specification** - Users cannot specify which branch to base the worktree on, limiting workflow flexibility

### Impact

| Stakeholder | Pain Point |
|-------------|------------|
| **Developers** | Worktree creation succeeds but execution fails due to missing objective file |
| **Teams** | Cannot leverage worktrees for objectives stored only in main repo |
| **CI/CD** | Automated workflows fail unpredictably when objective paths are relative |

### Root Cause

The worktree workflow assumes the objective file will exist in the worktree after creation. This assumption fails when:
- The objective file is newly created (staged but not committed)
- The objective file exists only on the current branch
- The worktree is branched from a point before the objective file existed

---

## Goals

### Primary Goal
Enable seamless worktree workflows where objective files are automatically available in the newly created worktree, regardless of their commit status in the source repository.

### Secondary Goal
Provide flexibility for users to specify the base branch for worktree creation.

---

## Success Criteria

| ID | Criterion | Measurable Outcome |
|----|-----------|-------------------|
| SC-1 | **Automatic objective file copy** | If objective file doesn't exist in worktree but exists in source repo (staged or committed), it is copied automatically |
| SC-2 | **Base branch specification** | New `--base-branch` option allows specifying which branch to base worktree on |
| SC-3 | **User feedback** | Clear logging indicates when an objective file is copied to the worktree |
| SC-4 | **Backward compatibility** | Existing `--worktree` workflows continue to work unchanged |
| SC-5 | **Test coverage** | Unit tests achieve 80%+ coverage on new functionality |
| SC-6 | **End-to-end validation** | Acceptance tests validate the complete workflow |

---

## Scope

### In Scope

- Detecting when objective file is missing in worktree
- Copying objective file from source repository to worktree
- Handling staged (uncommitted) objective files
- Handling committed objective files
- Adding `--base-branch` CLI option
- Logging/output for file copy operations
- Cross-platform compatibility (Linux, macOS, Windows)
- Respecting Windows 260-character path limit validation

### Out of Scope

- Syncing other files from source to worktree
- Automatic worktree cleanup
- Multiple objective file handling
- Remote branch support for `--base-branch`

---

## Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| Git CLI | External | Required for worktree operations |
| Click CLI | Internal | Framework for CLI argument parsing |
| Existing worktree manager | Internal | `src/teambot/worktree/manager.py` |

---

## Assumptions

1. **Git availability**: Git CLI is installed and available on PATH
2. **Repository context**: Commands are run from within a Git repository
3. **File system access**: User has read/write permissions in both source repo and worktree location
4. **Single objective**: Each `run` command operates on a single objective file

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Path handling differences across platforms | Medium | High | Use `pathlib` consistently; test on all platforms |
| File permission issues on copy | Low | Medium | Preserve original file permissions; log failures clearly |
| Race conditions with staged files | Low | Low | Copy file content directly, not reference |

---

## User Stories

### US-1: Automatic Objective File Copy
**As a** developer using worktrees  
**I want** the objective file to be automatically copied to my worktree  
**So that** I can start working immediately without manual file management

**Acceptance Criteria:**
- [ ] Given an objective file exists in the source repo but not in the worktree, when I run `teambot run --worktree objective.md`, then the objective file is copied to the worktree
- [ ] Given the copy succeeds, when I view the output, then I see a message indicating the file was copied
- [ ] Given the objective file already exists in the worktree, when I run the command, then no copy occurs

### US-2: Staged File Support
**As a** developer with a newly created objective file  
**I want** to use `--worktree` even if my objective file is only staged (not committed)  
**So that** I can start working on new tasks immediately

**Acceptance Criteria:**
- [ ] Given an objective file is staged but not committed, when I create a worktree, then the staged version is copied to the worktree
- [ ] Given the file is both modified and staged, when I create a worktree, then the working directory version is copied

### US-3: Base Branch Specification
**As a** developer managing multiple features  
**I want** to specify which branch my worktree should be based on  
**So that** I can control the starting point for my feature branch

**Acceptance Criteria:**
- [ ] Given I specify `--base-branch main`, when the worktree is created, then it branches from `main` instead of the current branch
- [ ] Given I don't specify `--base-branch`, when the worktree is created, then it uses current behavior (branches from current branch)
- [ ] Given I specify an invalid branch name, when I run the command, then I see a clear error message

---

## Glossary

| Term | Definition |
|------|------------|
| **Worktree** | A Git feature allowing multiple working directories attached to a single repository |
| **Source repository** | The original Git repository where the command is executed |
| **Objective file** | A markdown file defining the development task for TeamBot |
| **Staged file** | A file added to Git's staging area but not yet committed |

---

## Document Information

| Field | Value |
|-------|-------|
| **Author** | Business Analyst Agent |
| **Created** | 2026-02-24 |
| **Status** | Draft |
| **Stage** | BUSINESS_PROBLEM |
