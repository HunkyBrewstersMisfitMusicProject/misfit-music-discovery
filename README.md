# Misfit Music Project

A working space for the Misfit Music Project. This repository currently contains
**foundation infrastructure only** — the product definition, goals, and scope are
still to be set by Elias and Hermes together.

## What's here
- `src/mmp/` — a free, offline audio toolkit (the `mmp` CLI). Built on ffmpeg,
  no paid dependencies, no network required at runtime.
- `COLLABORATION.md` — the operating agreement between Elias and Hermes.
- `docs/` — notes, decisions, and working logs.

## Status
- [x] Local dev environment bootstrapped (uv, ffmpeg, git)
- [x] Repo skeleton + collaboration pact committed
- [x] `mmp` CLI: `inspect`, `tone` commands working
- [ ] Product definition (pending Elias)
- [ ] First real artifact (pending direction)

## Quick start
```bash
cd misfit-music
uv venv && . .venv/bin/activate   # or: uv run python -m mmp.cli
python -m mmp.cli tone demo.wav --seconds 2
python -m mmp.cli inspect demo.wav
```

No budget is spent by anything in this repo. All tooling is free and local.
