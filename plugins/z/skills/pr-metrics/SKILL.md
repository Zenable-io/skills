---
name: pr-metrics
description: Show your organization's pull request delivery history before and after Zenable — fetch your PR history and open a local HTML report of merged PRs per month, active authors, open-to-merge lead time (median/P75/P90), lead time by PR size, abandon rate, people vs automation, and per-repository and per-author tables, with filters. Use this skill whenever the user asks about PR delivery history, PR lead time or cycle time, merge or abandon rate, PR throughput, DORA-style monthly engineering metrics, or how delivery changed before and after adopting Zenable, or invokes `/z:pr-metrics`. Also trigger for phrases like "how fast do our PRs merge", "show our PR trends", or "did Zenable change our lead time".
allowed-tools: Bash(which zenable:*), Bash(zenable version:*), Bash(zenable auth can-i:*), Bash(zenable auth whoami:*), Bash(zenable api raw GET:*), Bash(uv run --script:*), Bash(python3:*), Bash(echo:*)
---

# PR delivery history

Fetch your organization's pull request history from Zenable and render it as a
local HTML report: month by month, before and after Zenable started reviewing
your PRs. Nothing is published or hosted. The data and the page stay in a folder
on this machine, and the page computes every number in the browser.

This skill was used privately first and is now public after private testing.

## Pre-flight

zenable CLI location: !`which zenable 2>/dev/null || echo "NOT INSTALLED"`

zenable CLI version: !`zenable version 2>/dev/null || echo "unavailable"`

If the CLI is not installed, ask the user for permission before installing
anything. If they approve, get the current install command for their operating
system from https://cli.zenable.app and run it, then re-run `zenable version`.

Report access: !`zenable auth can-i reports:read 2>/dev/null; echo "exit code $?"`

Continue only on exit code 0. Exit code 1 means the account cannot read
reports: the user's role lacks report access, or their plan does not include
it. Tell the user that and point them to the
[Zenable docs](https://docs.zenable.io/?utm_source=skills&utm_medium=cli). For any
other code, the user is probably not signed in: ask them to run `zenable login`.

Authenticated account: !`zenable auth whoami 2>&1 || echo "NOT AUTHENTICATED"`

## 1. Fetch

Ask the user two short questions, and accept "skip" for either:

- **Automation logins.** Logins whose PRs are machine-made (release or deploy
  users, service accounts). Logins that end in `[bot]` already count as
  automation. The report also suggests candidates, so this can wait.
- **Time window.** Default: from the first of the month 13 months ago to today.

Then run the fetch script from this skill's directory:

```bash
uv run --script scripts/fetch_pr_metrics.py --out ./pr-metrics-report \
  --automation-authors "release-user,deploy-user"
```

Options: `--start YYYY-MM-DD`, `--end YYYY-MM-DD`, `--out DIR`, `--title TEXT`,
`--automation-authors CSV`. If `uv` is not available, `python3
scripts/fetch_pr_metrics.py` works too (Python 3.11+, standard library only).

The script calls `zenable api raw` for PR history, history import progress, and
your connected GitHub repositories, then writes `data/*.json` and `index.html`
into the output folder. A re-run replaces the data and keeps the title,
automation logins, and any `dimensions` from the last run unless the user
passes new ones. If it fails, show the user the error text it prints; do not
retry with different endpoints.

## 2. Serve

Browsers block a `file://` page from loading its data, so serve the folder:

```bash
python3 -m http.server 8765 -d ./pr-metrics-report
```

Run it in the background and tell the user to open http://localhost:8765.

## 3. Review with the user

Walk the user through the page, starting from the defaults (period "Before
Zenable", authors "People"), then switch to "After Zenable". The period split is
the date of the first PR Zenable reviewed. Read the numbers with these limits in
mind, and say them plainly:

- **Lead time is open to merge**, not commit to deploy. It leaves out the time
  before the PR opened and the time after merge.
- **Merged PRs per month stands in for deployment frequency.** It counts
  changes that landed, not releases.
- **Abandon rate is not change failure rate.** A PR closed without merge is
  often a superseded or exploratory change, not a failure in production.
- **Recent months are still settling.** Months with more than 5% of PRs still
  open show hollow points; their lead times read low until those PRs close.
  Partial months carry a `*`.
- **No time to restore.** PR data has no incident signal, so this report does
  not estimate it.
- **Automation skews the median.** Automation PRs often merge in minutes. Use
  the Authors toggle and the "Suggested" tags to separate them.

If history import is still in progress for some repositories, the status line
says so; older months can be incomplete until it finishes.

## Filters

- **Period** and **Authors** toggles.
- **Filters**: type to search repositories, authors, PR size, repository
  status, review override, and each GitHub custom property. Press Enter for a
  "contains" match. Click a chip's `=` to switch it to exclude (`≠`).
- **Automation**: add logins, or a "contains" pattern, to count as automation.
- The filter state lives in the URL hash, so a link reopens the same view.
- Clicking a repository or author in the tables filters to it.

### Extra filter dimensions

`data/config.json` accepts an optional `dimensions` array of extra filter
dimensions over any PR field. Each entry is
`{"key", "label", "field", "labels"?}`: `field` names a PR row field, and
`labels` maps raw values to display names; values that share a label filter as one. For example, to group authors into teams (or use `"field": "default_branch"` with no labels):

```json
{"dimensions": [{"key": "team", "label": "Team", "field": "pr_author",
  "labels": {"alice": "Platform", "bob": "Platform", "carol": "Payments"}}]}
```

Edit the file and reload the page; re-fetching keeps it. The data contract is in
`references/data-contract.md`.
