# PR delivery report data contract

The report page (`index.html`, copied from `assets/report.html`) reads four
files from `<out>/data/`. `scripts/fetch_pr_metrics.py` writes them. API
responses are stored unchanged inside an envelope; the page does all of the
math.

## Envelope

```json
{"endpoint": "/api/data/...", "params": {"key": "value"}, "fetched_at": "2026-10-21T14:00:00+00:00", "response": {}}
```

## `pr_metrics.json`

A JSON **array** of envelopes, one per page of `GET /api/data/pr-metrics`
(`start_date`, `end_date`, `limit=1000`, `offset`, `sort_by=opened_at`,
`sort_order=asc`). Each `response` is
`{"pr_metrics": [row, ...], "total": n, "limit": 1000, "offset": n}`.

Row fields the page uses:

| Field | Meaning |
| --- | --- |
| `pr_metrics_id` | Row id |
| `repo_id` | Repository key, for example `github:owner/name` |
| `pr_number`, `pr_url`, `pr_title` | The PR |
| `pr_author` | Author login |
| `opened_at`, `merged_at`, `closed_at` | ISO 8601 timestamps |
| `merge_result` | `merged`, `closed_unmerged`, or `open` |
| `additions`, `deletions` | Lines changed; size buckets use their sum |
| `is_zenable_authored` | PRs Zenable opened; the page leaves them out |
| `zenable_reviewed`, `zenable_first_review_at` | The earliest `zenable_first_review_at` splits "Before" from "After Zenable" |

If the rows across pages do not add up to `total`, the page shows a banner.

## `backfill_progress.json`

One envelope for `GET /api/data/pr-metrics/backfill-progress`. `response` is
`{"progress": [{"repo_id", "status", "progress_pct", "failed_pr_count", "backfill_start_date", ...}], "total": n}`.
The page reads `status` (`completed` or `in_progress`), `failed_pr_count`, and
`backfill_start_date` (the first covered day; a month that starts mid-month is
marked partial).

## `github_repos.json`

One envelope for `GET /api/data/github/repos`. `response` is
`{"repos": [row, ...]}`. The page accepts two row shapes and normalizes them:

| Normalized | Read from |
| --- | --- |
| key | `repo_id`, else `github:` + `full_name` |
| archived | `archived`, else `repo_metadata.archived` |
| removed | `removed`, else `repo_metadata.removed` |
| custom properties | `custom_properties`, else `repo_metadata.custom_properties`, else `{}` |
| review override | `review_enabled_override` (`true`, `false`, or `null` to inherit) |

PRs whose repository has no row show as "Not connected".

## `config.json`

```json
{
  "title": "PR delivery history",
  "start": "2025-09-01",
  "end": "2026-10-21",
  "automation_authors": ["release-user"],
  "dimensions": [{"key": "team", "label": "Team", "field": "pr_author", "labels": {"alice": "Platform"}}]
}
```

`dimensions` is optional and hand-edited: each entry adds a filter dimension over
PR row field `field`, shown as `labels[value]` when present, else the raw value.
The fetch script keeps `title`, `automation_authors`, and `dimensions` across
re-runs unless new values are passed.
