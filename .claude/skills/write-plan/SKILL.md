---
name: write-plan
description: Use after brainstorming is approved, to generate a step-by-step implementation plan before writing any code
---

# Write Implementation Plan

## Purpose
Generate a precise, bite-sized implementation plan that enables executing a feature with minimal risk of getting lost or making wrong assumptions.

## Plan Structure

### Header (mandatory)
- Goal: one sentence
- Architecture: how this fits into the existing project
- Files affected: list with their responsibility

### Tasks
Each task must be:
- **2–5 minutes** to execute
- Have a clear success criterion
- Follow TDD cycle: failing test → minimal implementation → passing test → commit

### Each task contains
- Exact file paths
- What to write (code samples if helpful)
- Test command with expected output
- Commit message

## Quality Rules
- DRY, YAGNI, no over-engineering
- One clear responsibility per file
- Follow existing patterns (check main.py, settings.py before proposing new patterns)
- No speculative features

## Save the plan
Write to `docs/plans/YYYY-MM-DD-<feature-name>.md`

## After the plan is written
Invoke `/execute-plan` to start implementation.
