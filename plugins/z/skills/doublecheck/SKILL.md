---
name: doublecheck
description: Double check work for quality, test coverage, elegance, hallucinations, and orphaned code left behind by changes on this branch. Use when the user asks you to review or verify your own work before shipping, or invokes `/z:doublecheck`.
---

# Double check the work

Double check your work make sure it is good, not over engineered, that your tests pass,
that it's elegant and not messy, that you use standard SOLID principles for things that
are repeated more than 2 times, and most importantly that you didn't hallucinate.

List each behavior this branch changed with the command or observation that proves it,
including the failure path, and run each one. A check you have never seen fail proves
nothing: break the behavior, confirm the check fails, then restore the exact same code and
confirm it passes. If a behavior can't be observed, add the test, log, or readable state
that shows it as part of this change.

Make sure that any code changes or improvements / additions made in this branch did not
leave any code orphaned; if it did, we prefer to clean it up so do some research and
confirm that any orphaned code or docs have been removed.

Do some research in the current code base and look for existing design patterns,
approaches, or libraries which solve the same problem that we did, and if it's a great
match then use it. Do not do excessive refactoring to use something that another part of
the code base does, but if it is clearly a good fit we should be using it to avoid logic
sprawl.
