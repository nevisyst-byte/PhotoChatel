---
name: skill-creator
description: Use when you want to create a new Claude skill for this project. Guides you through defining, writing, and testing a new skill.
---

# Skill Creator

## Purpose
Interactively guide the creation of a new skill for this project, saved in `.claude/skills/<name>/SKILL.md`.

## Process

### 1. Capture intent
Ask the user:
- What should this skill do?
- When should it trigger? (what user phrase or situation)
- What should it output or accomplish?
- Are there edge cases to handle?

One question at a time.

### 2. Draft the skill
Create `.claude/skills/<name>/SKILL.md` with:

```markdown
---
name: <kebab-case-name>
description: <one line — written to encourage triggering in the right situations>
---

<clear instructions for Claude to follow>
```

### 3. Key writing rules
- **Description** should be "pushy" — describe the situations that should trigger it, not just what it does
- Keep body under 500 lines
- Explain *why* instructions matter — don't just use ALL-CAPS demands
- Include examples of good and bad outputs if helpful
- Reference other project skills with `/skill-name` if there's a logical flow

### 4. Review
Show the draft to the user. Ask:
- "Does this match what you had in mind?"
- "Is there anything missing or incorrect?"

Iterate until approved.

### 5. Save
Write the final file. Remind the user that skills are loaded on next Claude Code session restart.

## Skill locations
- Project-wide: `.claude/skills/<name>/SKILL.md` ← use this for photobooth skills
- Personal (all projects): `~/.claude/skills/<name>/SKILL.md`
