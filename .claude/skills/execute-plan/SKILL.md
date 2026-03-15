---
name: execute-plan
description: Use to execute an implementation plan task by task, with verification at each step
---

# Execute Plan

## Three Phases

### 1. Load and Review
- Read the plan file in `docs/plans/`
- Critically examine it — raise concerns BEFORE starting
- Confirm with user before proceeding

### 2. Execute Tasks
For each task:
- Mark `in_progress`
- Follow the steps exactly as written
- Run the verification / test specified
- Mark `completed` only when verified
- Commit after each passing task

### 3. Complete
When all tasks are done, run the full test suite and present a summary.

## Critical Stopping Points
Halt immediately and ask for clarification if:
- A dependency is missing
- A test fails unexpectedly
- Instructions are unclear or contradictory
- Repeated failures on the same step

**Never guess. Never skip. Ask.**

## Constraints
- Never start implementation on `main` branch without explicit user consent
- If a task says "write a test first" — write the test first, watch it fail, then implement
- Do not implement features not in the plan
