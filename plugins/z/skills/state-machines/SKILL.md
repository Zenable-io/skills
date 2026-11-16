---
name: state-machines
description: Find the implicit state machines in a codebase — status fields, groups of booleans, nullable timestamps, retry counters, and effect chains that together mean a state — and write down the rules they must follow, so every future change by an agent or a person can be checked against them. Lists each machine's states, transitions, stuck states, races, and impossible combinations, replays each finding against the real code, draws the important flows, and proposes the rules as Zenable requirements. Use when the user asks to "find the state machines", map a lifecycle or status flow, asks why records or jobs get stuck, stale, or orphaned, worries about races between workers or retries, is about to add a new status or flag, or invokes `/z:state-machines`.
---

# Find the implicit state machines

Most state in an application is never written down as a state machine. It hides in a
`status` column, three booleans that must never all be true, a `cancelled_at` that is
only sometimes set, or a retry counter that a timer resets. Each of these is a state
machine that nobody drew, and its bugs are the states nobody meant to allow: a spinner
that never stops, a job that never finishes, an order that is both refunded and shipped.

These rules live in the heads of whoever built each part, and in a large codebase that
many teams change, nobody holds all of them. A coding agent holds none. Agents break them
in predictable ways: a new boolean beside an existing status, a second place that writes
the status without its guard, an effect that fires in a state nobody expected. The goal
of this skill is to write those rules down where every change can be checked against
them. The map and the findings are the evidence for the rules.

The user's request names the area, flow, or bug to start from. With no area named,
search the whole repository, rank the candidates by how much a bug in them would hurt
users (money, data, access, work that silently never finishes), and map the top few in
depth. Three machines mapped with every writer and a replayed finding are worth more
than twenty sketched from their field names, so say which candidates you left unmapped.

If a `state-machines.md` from an earlier run exists, start with "Refresh" below.

## Find the candidates

Search the code for these signs, and read each hit before you count it:

- **Status values.** Enum types, `status` / `state` / `phase` / `stage` fields, string
  literals compared in `switch` or `match`, database columns with a fixed set of values.
- **Flag groups.** Two or more booleans on one object that are set together, such as
  `isLoading`, `isError`, and `hasSubmitted`. Each combination is a state.
- **Phase timestamps.** Nullable fields like `started_at`, `completed_at`, `cancelled_at`
  whose being set or unset decides what the code does next.
- **Counters and timers.** Retry counts, attempt numbers, backoff timers, leases,
  timeouts, and heartbeats.
- **Effect and event chains.** UI effects that fire on a state change, message handlers
  that move a record along, webhooks, queue consumers, and scheduled jobs that pick up
  rows by status.
- **Locks and ownership.** Claimed-by fields, mutexes, advisory locks, and idempotency keys.

Group the hits into machines. One machine is one thing that moves between states: an
order, an upload, a session, a form, a deployment. Its state can be spread across
several files, tables, and services. Follow the writes, not the file layout.

## Map each machine

For each machine, write down:

- **States**, named by what a person can see or cares about ("Waiting for payment"),
  each with the fields and values that make it up and where in the code it is stored.
- **Transitions**: the event that causes each one (a user action, a response, a timer,
  a message), the guard that must hold, and the file and function that writes it.
- **Start and end states**: where a new instance begins, and which states are meant to
  be final.
- **Writers**: every place in the code that writes the machine's fields. A writer that
  bypasses the usual transition function is a common source of bugs, so list them all.

Name every file and function a reader can open. A transition you cannot point to in
the code is a guess, so mark it as one.

## Find what goes wrong

These are the findings. Look for each kind on every machine:

- **Stuck states**: a state that is not meant to be final but has no way out, or whose
  only way out depends on something that may never happen (a webhook that is never
  retried, a timer that dies with the process).
- **Impossible combinations that can happen**: field values that make no sense together
  ("loading" and "error" at once, `shipped` with a `refunded_at`), and the sequence of
  events that produces them.
- **Races**: two writers that can interleave, such as a user cancelling while a job
  completes, or two workers claiming one row.
- **Missing guards**: a transition that any state can take when only some states should
  take it.
- **Lost events**: an event that arrives in a state that ignores it, when it should be
  handled or kept for later.

For each finding, give the shortest sequence of steps that reaches it, numbered, in the
code's own words, with the file and function for each step. For example:

> **An order can be charged after it is cancelled.** (race; `orders/service.py`)
> 1. The customer presses Cancel; `cancel_order` sets `status = "cancelled"`.
> 2. The payment worker, which read the order before step 1, calls `capture_payment`.
> 3. `capture_payment` checks `payment_intent_id`, not `status`, and captures.
>
> Replayed with a test that runs steps 1 and 2 against one order: the order ends
> `cancelled` with `captured_at` set.

### Rule out false positives before you report

A finding the team has to disprove costs them more than a missed one, so the bar is
evidence, not suspicion. Before you report a finding, look for what would make it a
non-issue:

- a guard you did not see: a database constraint, a unique index, a conditional
  `UPDATE ... WHERE status = ...`, a lock, an idempotency key, or a check in a caller;
- a recovery path that ends the stuck state: a reaper, a scheduled sweep, a timeout,
  a retry policy, or a dead-letter queue;
- a combination that is legitimate: a documented intermediate state, a migration in
  progress, or a feature flag that keeps the path off;
- a step that cannot happen: an event that only arrives in states that handle it.

Then replay the steps against the real code, one step for each event: write a test, or
reproduce it with the project's own tooling. If a step cannot happen, the map is wrong,
so fix the map and drop the finding. Put replay tests where the user can see and keep
them, and don't leave them in the user's working tree unless they ask; a scratch
directory or a separate branch is fine. Report only findings you have replayed. List the
ones you could not replay separately, each with why and with your confidence, so the
user can tell a confirmed bug from a lead.

Don't change product code to fix a finding unless the user asks. The user may need the
finding as evidence, may already have a fix in flight, or may decide the behaviour is
intended, and a silent fix takes those choices away.

## Draw the important flows

Use the `diagram` skill to draw each machine that has a finding, and the flows the user
cares about most. Pass it the states, transitions, guards, and findings from your map.
Mark each state where a finding occurs, and give the path to it.

## Propose the rules

Each machine has rules its states must follow, whether or not anyone wrote them down:
"a cancelled order is never charged", "an upload leaves Processing within ten minutes",
"only one worker holds a job". Write each one as a single plain sentence, with the
machine it belongs to and the code it constrains.

Write each rule so a change can be checked against it without your map: name the
fields, the allowed values, and the code allowed to change them. For each rule, say:

- whether the current code keeps it. A rule the code breaks is a finding, with its
  replayed steps;
- whether a deterministic check can enforce it, such as "only the transition function
  writes `status`" or "every `status` value is handled", or whether it needs judgment,
  such as "a retry never charges twice".

Offer the rules to the user as candidate Zenable requirements, so they are checked as
agents and people change the code, not only today. For the ones they accept, use the
`setup` skill to co-author, scope, and persist them through the Zenable MCP. Without the
Zenable MCP, list them in the report for the user to add later.

## Report

Write `state-machines.md` where the user chooses; offer the repository's docs folder
first. If you can't ask, use the docs folder (or the repository root when there is none)
and say where you put it. It holds:

- the rules first: each rule, its machine, whether the code keeps it, whether a
  deterministic check can enforce it, and which became requirements;
- the findings, ranked by harm to users, each with its replayed steps and the evidence
  from the replay;
- one section per machine: what it is, its states and transitions with code locations,
  its diagram, and its rules;
- a coverage record: for each machine, the files and functions its map describes, and
  the commit at which you last confirmed that the map matches them.

Then tell the user in a few sentences how many machines you found, the most serious
findings, and what the map does not cover (code you did not read, services outside the
repository, configuration that changes behaviour at run time).

## Refresh

Rules that became requirements are checked on every change already. Refresh keeps the
map, the diagrams, and the rules nobody adopted in step with the code, and finds
machines and rules that are new since the last run.

When `state-machines.md` exists, read its coverage record and diff each machine's
covered files from the recorded commit to the current one. Also look for new writers of
the machine's fields outside the recorded files. For each change, decide whether it
alters the machine: a new state or transition, a moved guard, a new writer, or nothing
the map describes. Update the map, the diagrams, and the rules from the code, then redo
"Find what goes wrong" for the machines that changed. Move a machine's recorded commit
forward only after you confirm its map matches the code at the new commit.

Close with the `doublecheck` skill on any tests you wrote.
