# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Fetch your organization's PR history and stage the local PR delivery report.

Every request goes through the signed-in `zenable` CLI, so this script holds no
credentials of its own. Responses are stored unchanged inside small envelopes
(`endpoint`, `params`, `fetched_at`, `response`); the report page does all of
the math, so a re-fetch never has to agree with a second copy of the formulas.

Usage:
    uv run --script fetch_pr_metrics.py
    uv run --script fetch_pr_metrics.py --start 2025-01-01 --out ./pr-report \\
        --automation-authors release-runner,deploy-user
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

PR_METRICS = "/api/data/pr-metrics"
BACKFILL_PROGRESS = "/api/data/pr-metrics/backfill-progress"
GITHUB_REPOS = "/api/data/github/repos"
PAGE_LIMIT = 1000
DEFAULT_TITLE = "PR delivery history"
DOCS_URL = "https://docs.zenable.io/?utm_source=skills&utm_medium=cli"
REPORT_TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "report.html"


class FetchError(RuntimeError):
    """A CLI call failed; the message is ready to show the user."""


def default_start(today: date) -> date:
    """First day of the month 13 months before `today`'s month."""
    months = today.year * 12 + today.month - 1 - 13
    return date(months // 12, months % 12 + 1, 1)


def call_api(path: str, params: dict[str, str] | None = None) -> Any:
    """GET `path` through `zenable api raw` and return the parsed JSON body."""
    argv = ["zenable", "api", "raw", "GET", path, "--json"]
    for key, value in (params or {}).items():
        argv += ["--param", f"{key}={value}"]
    try:
        completed = subprocess.run(argv, capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        raise FetchError("the `zenable` CLI is not on PATH; install it from https://cli.zenable.app") from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        message = f"`zenable api raw GET {path}` failed (exit {completed.returncode}): {detail}"
        if "403" in detail:
            message += (
                "\nYour account lacks findings access, or your plan does not include PR history reports."
                f" See {DOCS_URL}"
            )
        raise FetchError(message)
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise FetchError(f"`zenable api raw GET {path}` returned non-JSON output: {completed.stdout[:200]!r}") from exc


def envelope(endpoint: str, params: dict[str, str], response: Any) -> dict[str, Any]:
    return {
        "endpoint": endpoint,
        "params": params,
        "fetched_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "response": response,
    }


def fetch_pr_pages(start: date, end: date) -> list[dict[str, Any]]:
    """Page through PR metrics until a short page or the reported total."""
    pages: list[dict[str, Any]] = []
    offset = 0
    while True:
        params = {
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "limit": str(PAGE_LIMIT),
            "offset": str(offset),
            "sort_by": "opened_at",
            "sort_order": "asc",
        }
        response = call_api(PR_METRICS, params)
        rows = response.get("pr_metrics") or []
        pages.append(envelope(PR_METRICS, params, response))
        offset += len(rows)
        total = response.get("total")
        if len(rows) < PAGE_LIMIT or (total is not None and offset >= total):
            return pages


def write_atomic(path: Path, text: str) -> None:
    """Write via a temp file in the same directory so a reader never sees half a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def write_json(path: Path, value: Any) -> None:
    write_atomic(path, json.dumps(value, indent=2) + "\n")


def parse_args(argv: list[str], today: date) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--start", type=date.fromisoformat, default=default_start(today),
                        help="first day to include, YYYY-MM-DD (default: first of the month 13 months ago)")
    parser.add_argument("--end", type=date.fromisoformat, default=today, help="last day to include (default: today)")
    parser.add_argument("--out", type=Path, default=Path("pr-metrics-report"), help="report directory")
    parser.add_argument("--title", help=f"report title (default: kept from the last run, else {DEFAULT_TITLE!r})")
    parser.add_argument("--automation-authors",
                        help="comma-separated logins to count as automation, beyond names ending in [bot]"
                             " (default: kept from the last run)")
    args = parser.parse_args(argv)
    if args.start > args.end:
        parser.error(f"--start {args.start} is after --end {args.end}")
    return args


def main(argv: list[str] | None = None, today: date | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv, today or date.today())
    data = args.out / "data"
    try:
        pages = fetch_pr_pages(args.start, args.end)
        backfill = envelope(BACKFILL_PROGRESS, {}, call_api(BACKFILL_PROGRESS))
        repos = envelope(GITHUB_REPOS, {}, call_api(GITHUB_REPOS))
    except FetchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    # A re-fetch keeps what the user set last time, including hand-added `dimensions`.
    config_path = data / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    config.setdefault("title", DEFAULT_TITLE)
    config.setdefault("automation_authors", [])
    if args.title is not None:
        config["title"] = args.title
    if args.automation_authors is not None:
        config["automation_authors"] = [a.strip() for a in args.automation_authors.split(",") if a.strip()]
    config["start"], config["end"] = args.start.isoformat(), args.end.isoformat()
    write_json(data / "pr_metrics.json", pages)
    write_json(data / "backfill_progress.json", backfill)
    write_json(data / "github_repos.json", repos)
    write_json(config_path, config)
    write_atomic(args.out / "index.html", REPORT_TEMPLATE.read_text(encoding="utf-8"))
    rows = sum(len(p["response"].get("pr_metrics") or []) for p in pages)
    print(f"Fetched {rows} PRs from {args.start} to {args.end} into {args.out}")
    print(f"Serve it:  python3 -m http.server 8765 -d {args.out}")
    print("Then open: http://localhost:8765")
    return 0


if __name__ == "__main__":
    sys.exit(main())
