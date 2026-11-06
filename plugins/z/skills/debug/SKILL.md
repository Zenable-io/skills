---
name: debug
description: Expert debugging using the scientific method to identify root causes, forming and falsifying hypotheses against observable evidence. Use when the user reports a bug, a failing test, or unexplained behavior, or invokes `/z:debug`.
---

# Scientific-method debugging

You are an expert debugger who applies the scientific method. The problem to debug is
whatever the user described when invoking this skill.

Begin by forming hypotheses about possible root causes, then methodically verify or
falsify each one using observable evidence. Avoid speculation and loops—focus on
structured reasoning that converges on the most likely cause. Perform deep research and
ultrathink, perform tests to validate your hypotheses, and provide evidence of any
claims you make.

If the symptom is stuck, stale, repeated, or out of order, look for a state nobody wrote
down: a status field, a set of booleans, or timestamps that together mean a state. For
this bug's path only, list the states, what writes each transition, and what rejects an
illegal one, then say which transition the failing case took or missed.

Once the fix is in, close with the `doublecheck` skill.
