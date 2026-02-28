# Tracking News - Task List (Release / International-grade)

> Autopilot rules: NO GIT. Do NOT leak secrets (.env). Work only inside repo.  
> After each task: run verification (tests/lint) and append a short entry to PROGRESS.md.  
> If blocked: write details + suggested next action to BLOCKERS.md and continue with a non-blocked task.

---

## 0) Ground truth & project health
- [ ] **Inventory**: Identify how to run the project end-to-end (entrypoints, commands, env requirements).  
      Output: update RUNBOOK.md with the correct commands and notes (redacted).
- [ ] **Baseline checks**: run `pytest` and `ruff check .` and record current status in PROGRESS.md (no secrets).
- [ ] **Fix lint debt**: fix *all* `ruff check .` issues (including `dashboard.py`) until ruff is clean.
- [ ] **Format**: add a formatter command and make codebase consistently formatted (prefer `ruff format .` if configured).
- [ ] **Preflight**: add a “preflight” command that catches obvious runtime errors (imports, compileall, config validation).

---

## 1) Reliability & correctness (core pipeline)
- [ ] **Canonical URL & dedup hardening**: ensure canonicalization handles common trackers (utm_*, fbclid, gclid) and edge cases.  
      Add unit tests for canonical URL + title hash dedup.
- [ ] **Scheduler resilience**: confirm retry/backoff is correct and won’t spin CPU; add tests for retry policy if feasible.
- [ ] **Source ingestion MVP**: ensure at least 3–5 reliable sources (prefer RSS/APIs) are configured and ingestion is stable.  
      Add tests for parsing failures + graceful degradation.
- [ ] **Storage integrity**: confirm DB schema + migrations are safe; add indexes for query speed; add tests for migration path.
- [ ] **Timezone correctness**: normalize all timestamps to UTC internally; ensure parsing is correct across sources; add tests.

---

## 2) “Vietnam finance impact” quality (v1 → v2 path)
- [ ] **Classifier v1 review**: audit rules/keywords/entities; add unit tests for representative examples (VN macro, FX, rates, banks, inflation, policy).
- [ ] **Scoring calibration**: define score bands (low/med/high) with clear meaning; document in README.
- [ ] **Pluggable classifier interface**: refactor so classifier is swappable (rule-based v1 now, LLM-based later) without touching pipeline logic.
- [ ] **Language handling**: ensure Vietnamese/English text normalization is correct; add tests for diacritics and tokenization basics.

---

## 3) Productization: CLI, alerts, and demo UX
- [ ] **CLI polish**: add `--json` output, better help text, sensible defaults, and examples in README.
- [ ] **Telegram alert safety**: ensure alerts are optional, rate-limited, and never include secrets; add a “dry-run” mode.
- [ ] **Config validation**: validate required env vars with clear errors (but never print secret values).
- [ ] **Sample data**: provide a small sample dataset or a “seed” command to demo without live scraping.

---

## 4) Observability & operations (international-grade)
- [ ] **Structured logging**: consistent log format, levels, and context fields (source, url, article_id, run_id).
- [ ] **Health checks**: implement a lightweight health check (CLI `health` command or HTTP `/healthz` if you have a server).
- [ ] **Metrics** (optional): expose basic counters (ingested, deduped, failed, retried). If no server, write metrics to logs.
- [ ] **Error taxonomy**: centralize exception handling so failures are actionable and don’t crash the whole loop.

---

## 5) Documentation (English-first + VN quickstart)
- [ ] **README.md (English-first)**: problem statement, architecture, quickstart, configuration, demo, troubleshooting.
- [ ] **Vietnamese quickstart section**: minimal steps to run on server (conda, env, run demo).
- [ ] **RUNBOOK.md**: operational commands: run scheduler, run CLI queries, clean shutdown, log locations.
- [ ] **CONTRIBUTING.md** (optional): coding standards, how to add a new source, how to add classifier rules/tests.

---

## 6) “Run on a free port” demo (must-have)
> Goal: be able to run a demo service/UI on an unused port automatically, without guessing.

- [ ] **Port picker utility**: implement `get_free_port()` helper (Python) and/or a `scripts/get_free_port.sh`.
- [ ] **Demo runner script**: create `scripts/run_demo.sh` that:
      1) picks a free port,
      2) starts the demo service (or dashboard) on that port,
      3) prints the URL and how to stop it.
- [ ] **No-conflict guarantee**: the script must fail gracefully if dependencies are missing and write to BLOCKERS.md.

---

## 7) Tooling convenience (one-liners)
- [ ] Add `Makefile` (or `justfile`) with:
  - `make test`  -> run tests
  - `make lint`  -> ruff check .
  - `make fmt`   -> ruff format .
  - `make demo`  -> run demo on free port
  - `make run`   -> run scheduler/daemon
- [ ] Ensure commands work in the current conda env (`news`) and document in RUNBOOK.

---

## Definition of Done (for Release Mode)
- [ ] `python -m pytest -q` passes
- [ ] `ruff check .` has **0 issues**
- [ ] Formatting is consistent (`ruff format .` or equivalent)
- [ ] `make demo` (or `scripts/run_demo.sh`) runs a demo on a **free port** and prints the URL
- [ ] README + RUNBOOK allow a new dev to run within 10 minutes (no secrets exposed)
- [ ] PROGRESS.md is up to date; BLOCKERS.md empty or has clear actionable items