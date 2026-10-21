import json
import os
import sys
from datetime import date
from pathlib import Path

import pytest
from conftest import load_script

fetch = load_script("fetch_pr_metrics")

# Stands in for the `zenable` CLI: serves PR rows in pages from a fixture and logs argv.
STUB = """#!{python}
import json, os, sys
argv = sys.argv[1:]
fx = json.load(open(os.environ["ZENABLE_STUB_FIXTURE"]))
with open(os.environ["ZENABLE_STUB_LOG"], "a") as log:
    log.write(json.dumps(argv) + "\\n")
path = argv[3]
if path in fx.get("fail", {{}}):
    rc, err = fx["fail"][path]
    sys.stderr.write(err)
    sys.exit(rc)
params = dict(argv[i + 1].split("=", 1) for i, a in enumerate(argv) if a == "--param")
if path == "/api/data/pr-metrics":
    offset, limit = int(params["offset"]), int(params["limit"])
    n = fx["rows"]
    rows = [{{"pr_metrics_id": i}} for i in range(offset, min(n, offset + limit))]
    body = {{"pr_metrics": rows, "total": n, "limit": limit, "offset": offset}}
elif path == "/api/data/pr-metrics/backfill-progress":
    body = {{"progress": [{{"repo_id": "github:o/r", "status": "completed"}}], "total": 1}}
else:
    body = {{"repos": [{{"full_name": "o/r", "repo_metadata": {{"archived": False}}}}]}}
print(json.dumps(body))
"""


@pytest.fixture
def cli(tmp_path, monkeypatch):
    """Put a stub `zenable` on PATH; returns (set fixture, read call log)."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stub = bin_dir / "zenable"
    stub.write_text(STUB.format(python=sys.executable), encoding="utf-8")
    stub.chmod(0o755)
    fixture, log = tmp_path / "fixture.json", tmp_path / "calls.jsonl"
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("ZENABLE_STUB_FIXTURE", str(fixture))
    monkeypatch.setenv("ZENABLE_STUB_LOG", str(log))

    def configure(**fx):
        fixture.write_text(json.dumps(fx), encoding="utf-8")

    def calls():
        return [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []

    return configure, calls


def _params(argv):
    return dict(argv[i + 1].split("=", 1) for i, a in enumerate(argv) if a == "--param")


@pytest.mark.parametrize(
    ("today", "expected"),
    [(date(2026, 10, 21), date(2025, 9, 1)), (date(2026, 1, 31), date(2024, 12, 1)), (date(2026, 2, 1), date(2025, 1, 1))],
)
def test_default_start_is_first_of_month_13_months_back(today, expected):
    assert fetch.default_start(today) == expected


@pytest.mark.parametrize(("rows", "pages"), [(0, 1), (999, 1), (1000, 1), (1001, 2), (2500, 3)])
def test_pages_until_short_page_or_total(cli, tmp_path, rows, pages):
    configure, calls = cli
    configure(rows=rows)
    out = tmp_path / "report"
    assert fetch.main(["--start", "2026-01-01", "--end", "2026-03-31", "--out", str(out)]) == 0

    pr_calls = [c for c in calls() if c[3] == "/api/data/pr-metrics"]
    assert [int(_params(c)["offset"]) for c in pr_calls] == [1000 * i for i in range(pages)]
    assert all(c[:3] == ["api", "raw", "GET"] and "--json" in c for c in calls())
    first = _params(pr_calls[0])
    assert first == {"start_date": "2026-01-01", "end_date": "2026-03-31", "limit": "1000", "offset": "0",
                     "sort_by": "opened_at", "sort_order": "asc"}

    stored = json.loads((out / "data" / "pr_metrics.json").read_text())
    assert len(stored) == pages
    assert set(stored[0]) == {"endpoint", "params", "fetched_at", "response"}
    assert stored[0]["endpoint"] == "/api/data/pr-metrics" and stored[0]["params"] == first
    assert sum(len(p["response"]["pr_metrics"]) for p in stored) == rows


def test_writes_every_file_and_defaults(cli, tmp_path):
    configure, _ = cli
    configure(rows=3)
    out = tmp_path / "report"
    assert fetch.main(["--out", str(out), "--automation-authors", " a, b ,,"], today=date(2026, 10, 21)) == 0

    data = out / "data"
    assert json.loads((data / "config.json").read_text()) == {
        "title": "PR delivery history", "start": "2025-09-01", "end": "2026-10-21", "automation_authors": ["a", "b"]}
    assert json.loads((data / "backfill_progress.json").read_text())["response"]["progress"][0]["status"] == "completed"
    assert json.loads((data / "github_repos.json").read_text())["endpoint"] == "/api/data/github/repos"
    assert (out / "index.html").read_text() == fetch.REPORT_TEMPLATE.read_text()
    # Atomic writes leave no temp files behind.
    assert not [p for p in out.rglob("*") if p.name.endswith(".tmp")]


def test_refetch_keeps_user_config(cli, tmp_path):
    configure, _ = cli
    configure(rows=1)
    out = tmp_path / "report"
    assert fetch.main(["--out", str(out), "--title", "Acme", "--automation-authors", "deployer"]) == 0
    config_path = out / "data" / "config.json"
    config = json.loads(config_path.read_text())
    config["dimensions"] = [{"key": "branch", "label": "Branch", "field": "default_branch"}]
    config_path.write_text(json.dumps(config))

    assert fetch.main(["--out", str(out)]) == 0
    kept = json.loads(config_path.read_text())
    assert kept["title"] == "Acme" and kept["automation_authors"] == ["deployer"]
    assert kept["dimensions"] == config["dimensions"]


def test_forbidden_fails_loudly_and_writes_nothing(cli, tmp_path, capsys):
    configure, _ = cli
    configure(rows=5, fail={"/api/data/pr-metrics": [1, 'Error: HTTP 403: {"error": "forbidden"}']})
    out = tmp_path / "report"
    assert fetch.main(["--out", str(out)]) == 1
    err = capsys.readouterr().err
    assert "HTTP 403" in err and "report access" in err
    assert "https://docs.zenable.io/?utm_source=skills&utm_medium=cli" in err
    assert not out.exists()


def test_other_cli_errors_pass_through(cli, tmp_path, capsys):
    configure, _ = cli
    configure(rows=5, fail={"/api/data/github/repos": [2, "Error: not signed in"]})
    assert fetch.main(["--out", str(tmp_path / "r")]) == 1
    err = capsys.readouterr().err
    assert "Error: not signed in" in err and "report access" not in err


def test_failed_write_keeps_previous_file(tmp_path, monkeypatch):
    target = tmp_path / "data.json"
    target.write_text("old")

    def boom(*_):
        raise OSError("disk full")

    monkeypatch.setattr(fetch.os, "replace", boom)
    with pytest.raises(OSError):
        fetch.write_atomic(target, "new")
    assert target.read_text() == "old"
    assert [p.name for p in tmp_path.iterdir()] == ["data.json"]


def test_start_after_end_is_rejected():
    with pytest.raises(SystemExit):
        fetch.parse_args(["--start", "2026-05-01", "--end", "2026-04-01"], date(2026, 10, 21))


def test_template_is_shipped():
    assert Path(fetch.REPORT_TEMPLATE).is_file()
