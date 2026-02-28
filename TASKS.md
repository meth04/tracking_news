# RELEASE MODE TASKS

## P0 - Quality Gate
- [x] Fix all `ruff check .` issues (including `dashboard.py`) or document any truly non-fixable items.

## P1 - Developer Experience
- [x] Add command interface for `lint`, `format`, `test`, `run` (Makefile or scripts).

## P2 - Configuration Hardening
- [x] Harden `.env.example` with safe defaults and no real secrets.
- [x] Add stricter settings validation and safer defaults in `config/settings.py`.

## P3 - Observability
- [x] Improve structured logging and user-facing error clarity.
- [x] Add a metrics endpoint/service if applicable.

## P4 - Demo Experience
- [x] Add a demo run command that starts on an auto-selected free port and prints URL.

## P5 - Documentation
- [x] Rewrite `README.md` with English-first docs and Vietnamese quickstart.

## P6 - Final Verification
- [x] Run full verification (`ruff check .`, tests, smoke commands) and record final status.
