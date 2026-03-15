---
name: brainstorming
description: Use when planning a new feature, exploring options, or solving a complex problem before writing any code
---

# Brainstorming

## Hard Rule
Do NOT write code, scaffold files, or take any implementation action until a design has been presented AND explicitly approved by the user. This applies even for simple changes.

## Process

### 1. Explore context
Read relevant existing files, recent commits, and docs before asking anything.

### 2. Ask clarifying questions
One question at a time. Use multiple-choice when possible. Never overwhelm with a list.

### 3. Propose 2–3 approaches
For each approach, clearly state:
- What it does
- Trade-offs (pros/cons)
- Complexity estimate

### 4. Present design incrementally
Get approval after each section before continuing.

### 5. Write the design doc
Save to `docs/specs/YYYY-MM-DD-<topic>.md`

### 6. Spec review loop (max 5 iterations)
Ask user to review. Iterate on feedback.

### 7. Only then → invoke `/write-plan`
The only valid next step after brainstorming is approved.

## Key Principles
- YAGNI: eliminate unnecessary features ruthlessly
- Break systems into small isolated units with clear purpose
- Follow existing patterns in the codebase
- One question per message — never a list of questions

## Terminal State
This skill ends only by invoking `/write-plan` with an approved spec.
