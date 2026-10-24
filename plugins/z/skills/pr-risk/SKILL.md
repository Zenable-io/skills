---
name: pr-risk
description: Dispute a Zenable pull request (GitHub PR) or merge request (GitLab MR) risk assessment — read the recorded grading behind its risk level and the profile's PR risk eval suite, explain which risk setting (rubric weights, disabled dimensions, risk floors) drove the level, and record the dispute as an eval case so Zenable scores it and proposes a setting change for approval. Use this skill whenever the user disagrees with a PR or MR risk level, says something like "this merged as low, it should have been high", asks why a PR got its risk level, which risk setting would have changed it, or wants to give feedback on or dispute a risk assessment, or invokes `/z:pr-risk`.
allowed-tools: Bash(which zenable:*), Bash(zenable version:*), Bash(zenable auth can-i:*), Bash(zenable auth whoami:*), Bash(zenable api pr-risk:*), Bash(gh pr view:*), Bash(glab mr view:*), Bash(echo:*)
---

# PR risk dispute

Help the user dispute a risk assessment they disagree with. Read what Zenable
recorded when it graded the PR/MR, explain what drove the level, and record
their dispute so Zenable searches for the configuration change.

The loop after a dispute runs in Zenable, not in this skill:

1. **Dispute.** `add_pr_risk_eval_case` stores the dispute as a labelled case
   on the config profile the repository used, and queues a scoring run.
2. **Scored.** Zenable generates variants of the same PR/MR (files, findings
   or rubric dimensions in reverse order; description removed), each labelled
   with the recorded level, then scores the current settings against every
   case on the profile.
3. **Proposal.** When one weight or floor change fixes the disputed cases
   without breaking any other case, a configuration proposal appears in
   **Settings > Configuration** on that profile.
4. **Approve.** A person accepts it there. If an approval flow covers
   configuration changes, it waits for that approval too.

This skill never writes configuration: the user accepts the proposal, or
applies any change, in Settings themselves.

## Pre-flight

zenable CLI location: !`which zenable 2>/dev/null || echo "NOT INSTALLED"`

zenable CLI version: !`zenable version 2>/dev/null || echo "unavailable"`

If the CLI is not installed, ask the user for permission before installing
anything. If they approve, get the current install command for their operating
system from https://cli.zenable.app and run it, then re-run `zenable version`.

Findings access: !`zenable auth can-i findings:read 2>/dev/null; echo "exit code $?"`

Continue only on exit code 0. Exit code 1 means the account cannot read
findings: the user's role lacks access, or their plan does not include it.
Tell the user that and point them to the
[Zenable docs](https://docs.zenable.io/?utm_source=skill&utm_medium=pr-risk). For
any other code, the user is probably not signed in: ask them to run
`zenable login`.

Authenticated account: !`zenable auth whoami 2>&1 || echo "NOT AUTHENTICATED"`

### Zenable MCP

This skill needs the Zenable MCP tools `get_pr_risk_eval_suite` and
`add_pr_risk_eval_case`. In Claude Code they surface as `mcp__zenable__*`; in
other IDEs they appear under whatever prefix that IDE uses. If they are absent,
ask the user for permission, then connect the server with
`zenable install mcp claude-code` (run `zenable install mcp -h` for other IDEs),
or point them to the
[MCP setup docs](https://docs.zenable.io/integrations/mcp/getting-started?utm_source=skill&utm_medium=pr-risk).

## 1. Identify the PR/MR

Take the PR/MR from the user's words. To resolve a number or URL:

```bash
gh pr view <number|url> --json url,number,baseRepository,headRefOid,mergedAt
# GitLab
glab mr view <number|url>
```

- `repository_url` is the **base** repository web URL, for example
  `https://github.com/org/repo`, not a fork.
- `change_ref` is the PR/MR number as a string, for example `"42"`.

If the user has not said which level they expected and why, ask before going
further.

## 2. Read the record

List every assessed run for the PR/MR:

```bash
zenable api pr-risk list --view run --repository-url <url> --change-ref <n> --json
```

The list defaults to the trailing 30 days. For an older PR/MR, add
`--start-date YYYY-MM-DD` (windows are at most 366 days). Confirm flag names
with `zenable api pr-risk list -h` if a call fails.

For each run, read the level, `risk_detail` (dimension scores, composite,
`floor_level`, `worst_file`), the merge-gate decision (`gate_merge`), and any
existing disputes.

Then call `get_pr_risk_eval_suite` with `repository_url`, `change_ref`,
and optionally `coverage_run_id` (default: the newest run). It costs 10
credits. It returns:

- `recorded_grading`: grader path and model, rubric with weights, PR facts,
  per-file scores, `floor_metric_values`.
- The profile's eval suite: the bundle (cases and their labels), the latest
  scoring run with its exact agreement, the latest comparison (fixed,
  regressed, unchanged), and any pending proposal with its status.

If the bundle already holds a dispute on this run, or a pending proposal
fixes it, tell the user and skip to step 3.

Tell the user plainly which run the merge gate trusted (`merged_by_gate`) and
what level it recorded.

## 3. Explain

From `recorded_grading`, show the user which file was worst, which dimensions
scored highest in it, and which weights and floors set the level. Level
thresholds are fixed; only weights, enabled dimensions and floors can move a
level. Do not try to apply a change. Recording the dispute (step 4) lets
Zenable score weight, enabled-dimension and floor changes against every case
on the profile and propose one in **Settings > Configuration** when it breaks
nothing; the user accepts it there, or makes the change by hand.

A floor is often the honest lever: it sets a minimum level from facts about
the change (`floor_metric_values`) rather than overriding the grader's
judgment.

## 4. Record the dispute

Ask the user for consent, then call `add_pr_risk_eval_case` with:

- `repository_url` and `change_ref`
- `coverage_run_id` (optional; default the newest run)
- `expected_level`: must differ from the recorded level; the tool refuses a
  dispute that agrees with it
- `rationale`: at most 1024 characters; the user's one-sentence reason, plus
  the setting they think should change

Disputing is free. Each person has one dispute per run; disputing again
updates it. The result says a scoring run was queued: quote that to the user,
and tell them the proposal, if one comes, appears in **Settings >
Configuration** on the profile, with the bundle and scores under
**Evaluations > PR risk**.

If the MCP server is unavailable, use the CLI instead. Find the command with
`zenable api pr-risk -h`; if no eval-case command exists, ask the user to run
`zenable self update` first.

## Caveats

Say these plainly when they apply:

- Only runs graded since Zenable started recording grading inputs can be
  read. Older runs return a capture error.
- Floors evaluate against the metric values recorded at review time, not the
  PR/MR as it is now.
