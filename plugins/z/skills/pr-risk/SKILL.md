---
name: pr-risk
description: Dispute a Zenable pull request (GitHub PR) or merge request (GitLab MR) risk assessment — read the recorded grading behind its risk level, replay what-if scenarios (rubric weights, disabled dimensions, risk floors, a fresh re-grade) to find the smallest risk-configuration change that would have produced the level you expected, and record your verdict as feedback. Use this skill whenever the user disagrees with a PR or MR risk level, says something like "this merged as low, it should have been high", asks why a PR got its risk level, which risk setting would have changed it, or wants to give feedback on a risk assessment, or invokes `/z:pr-risk`.
allowed-tools: Bash(which zenable:*), Bash(zenable version:*), Bash(zenable auth can-i:*), Bash(zenable auth whoami:*), Bash(zenable api pr-risk:*), Bash(gh pr view:*), Bash(glab mr view:*), Bash(echo:*)
---

# PR risk what-if

Help the user test a risk assessment they disagree with. Read what Zenable
recorded when it graded the PR/MR, replay scenarios against that record, find
the smallest configuration change that reaches the level the user expected,
and record their verdict. This skill never writes configuration: the user
applies any change in Settings themselves.

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

This skill needs the Zenable MCP tools `simulate_pr_risk` and
`submit_pr_risk_feedback`. In Claude Code they surface as `mcp__zenable__*`; in
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
existing feedback.

Then call `simulate_pr_risk` with `repository_url`, `change_ref`, optionally
`coverage_run_id` (default: the newest run), and **no scenarios**. This is the
baseline: read `recorded_grading` (grader path and model, rubric with weights,
PR facts, per-file scores, `floor_metric_values`).

Tell the user plainly which run the merge gate trusted (`merged_by_gate`) and
what level it recorded.

## 3. What-if

Each `simulate_pr_risk` call with scenarios costs 10 credits and takes up to 25
scenarios, so batch them into one call. Scenario shape:

```json
{
  "name": "string, at most 80 characters",
  "rubric_overrides": [
    {"name": "...", "description": "...", "weight": 2.0, "enabled": true}
  ],
  "floors": [
    {"expression": {...}, "minimum_level": "low|medium|high|critical"}
  ],
  "regrade": false
}
```

`rubric_overrides` and `floors` may be `null` to keep the recorded value.

How the tool treats a scenario:

- Changing only weights, `enabled` flags, or floors replays
  **deterministically** from the recorded grades.
- Changing a dimension's wording, adding a dimension, or `regrade: true`
  re-grades the recorded state with Zenable's judgment model. The result is
  marked `deterministic: false`.
- Level thresholds are fixed. Scenarios cannot change them.

A floor expression uses the same shape as a risk floor in Settings:

```json
{"type": "rule", "rule": {"condition": {
  "metric": "total_loc_changed",
  "category": null,
  "operator": "greater_than",
  "threshold": 400
}}}
```

- `metric`: `total_loc_changed`, `total_loc_added`, `total_loc_removed`,
  `finding_count`, or `requirements_with_findings_count`.
- `category`: `null`, or a finding category (only for the two finding metrics).
- `operator`: `greater_than`, `at_least`, `less_than`, or `at_most`.
- `threshold`: an integer.

To combine rules, use
`{"type": "operation", "operator": "and|or|not", "operands": [...]}`. If the
tool rejects that shape, use single-rule floors.

A good first batch:

1. **Weight sweeps**: ×2 and ×3 on the dimensions that scored highest in the
   worst file.
2. **Disable** the dimension that pulls the composite down.
3. **Floor candidates** from `floor_metric_values`, for example
   `total_loc_changed greater_than <recorded value − 1>` or
   `finding_count at_least <recorded value>`, each with the expected level as
   `minimum_level`.
4. **One re-grade**: the recorded rubric with `regrade: true`, to see today's
   judgment.
5. **One reworded rubric**, only if the user argues a dimension's wording misses
   the point.

For each result, read `level`, `changed`, `deterministic`, `floor_level`,
`worst_file`, and `files[]`.

## 4. Recommend

The smallest **deterministic** scenario that reaches the expected level is the
suggested change. Show it as the exact rubric weights or floor entry to apply
in **Settings > PR reviews > Risk**. Do not try to apply it: risk settings are
deliberately kept out of automated configuration changes, so the user makes
this change themselves.

If no configuration reaches the expected level, say the grader disagreed, and
show the re-grade result. A floor is then the honest lever: it sets a minimum
level from facts about the change rather than overriding the grader's
judgment.

## 5. Record the verdict

Ask the user for consent, then call `submit_pr_risk_feedback` with:

- `rating`: `thumbs_up` or `thumbs_down`
- `repository_url` and `change_ref`
- `coverage_run_id` (optional; default the newest run)
- `expected_level`
- `comment`: at most 1024 characters; include the scenario that worked

Feedback is free. Each person has one verdict per run; submitting again
replaces it.

If the MCP server is unavailable, use the CLI instead. Confirm the flags with
`zenable api pr-risk create-feedback -h`; if the command does not exist, ask the
user to run `zenable self update` first.

## Caveats

Say these plainly when they apply:

- Only runs graded since Zenable started recording grading inputs can be
  replayed. Older runs return a capture error.
- Re-grades are judgments and can differ from run to run.
- A floor-only scenario evaluates against the metric values recorded at review
  time, not the PR/MR as it is now.
