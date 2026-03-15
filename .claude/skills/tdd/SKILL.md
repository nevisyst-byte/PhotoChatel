---
name: tdd
description: Use when implementing any feature or bugfix, before writing implementation code
---

# Test-Driven Development (TDD)

## Overview
Write the test first. Watch it fail. Write minimal code to pass.
Core principle: If you didn't watch the test fail, you don't know if it tests the right thing.
Violating the letter of the rules is violating the spirit of the rules.

## The Iron Law
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
Write code before the test? Delete it. Start over. No exceptions.

## Red-Green-Refactor
RED → Verify fails correctly → GREEN → Verify passes → REFACTOR → (repeat)

### RED: Write one minimal test showing what should happen.
- One behavior, clear name, real code (no mocks unless unavoidable).

### Verify RED (MANDATORY, never skip):
- Run the test
- Confirm: test fails (not errors), failure message is expected, fails because feature is missing.

### GREEN: Write simplest code to pass the test. No extra features.

### Verify GREEN (MANDATORY):
- Run the test
- Confirm: test passes, other tests still pass, output pristine.

### REFACTOR: After green only — remove duplication, improve names, extract helpers. Keep tests green.

## Good Tests
- Minimal: one thing; "and" in name → split it
- Clear: name describes behavior
- Shows intent: demonstrates desired API

## Red Flags — STOP and Start Over
- Code before test
- Test passes immediately
- Rationalizing "just this once"
- "Keep as reference" / "adapt existing code"
- "Already spent X hours, deleting is wasteful"
- "TDD is dogmatic, I'm being pragmatic"

## Verification Checklist
- [ ] Every new function/method has a test
- [ ] Watched each test fail before implementing
- [ ] Each test failed for expected reason
- [ ] Wrote minimal code to pass each test
- [ ] All tests pass, output pristine
- [ ] Tests use real code (mocks only if unavoidable)
- [ ] Edge cases and errors covered

## Final Rule
Production code → test exists and failed first. Otherwise → not TDD. No exceptions without human partner's permission.
