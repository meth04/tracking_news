# Claude Code Rules (No-Git, Autopilot)

## Scope
- Work ONLY inside this repository directory.
- Do NOT use git commands at all.

## Secrets & Privacy (STRICT)
- NEVER print the contents of `.env` or any secrets.
- NEVER echo environment variables that look like keys/tokens.
- If you need a value from `.env`, use it only implicitly by running the app/tests, not by displaying it.
- If debugging requires configs, write a redacted summary (e.g., "PROXY_API_KEY is set / missing") without showing the value.

## Safety
- Do NOT run destructive commands: rm -rf, sudo, chmod -R, chown -R, mkfs, dd, git clean.
- Do NOT `curl | bash` or install unknown binaries.
- Minimize new dependencies; ask by writing to BLOCKERS.md.

## Autopilot workflow (loop)
For each iteration:
1) Read TASKS.md and pick the top unchecked task.
2) PLAN: write a short plan (files to edit + commands to run).
3) IMPLEMENT: make the minimal code changes.
4) VERIFY: run tests / lint / type-check (best available).
5) REPORT: write results to PROGRESS.md (what changed, commands run, outcomes, next task).
6) Repeat.

## Standard outputs
- All progress goes to `PROGRESS.md`.
- All uncertainties/questions go to `BLOCKERS.md`.