# ADR-001 — Task backend: Super Productivity (locked)

Status: accepted. Date: 2026-09-06.

## Decision

Super Productivity primary. Fallbacks in order: Donetick (chores), dayGLANCE (TickTick-like, immature), Vikunja (stable API, weak habits).

## Why

Only mature FOSS option covering one-off tasks + every-X-days chores + habit-like repeats + Pomodoro/timebox in one UI (MIT, local-first). Vikunja is a cleaner server API but feels like "simplest possible todo" — no native habit/routine model.

## Consequence

Local-first = adapter must run beside the SP client (localhost REST). No remote-API assumption. Validate capability matrix before writes:

`create task / update recurrence / complete occurrence / read counters+history / task-complete hook` × (REST / plugin / file).
If REST gaps: add minimal SP plugin, else fallback to Donetick sidecar for chores.

Note: official `super-productivity/super-productivity` Docker image serves the static web UI only — task data lives in the browser (or sync backend), there is no server DB. It is not an agent backend; the MCP path needs the desktop app's localhost REST.

## Topology (accepted)

SP runs as a regular desktop install on the daily-use machine (snap/flatpak/releases per OS — apps exist for all major platforms). The MCP adapter runs beside it (same host, localhost REST + bearer token). OpenClaw + Ollama run on the Ubuntu server; Tailscale bridges the two (playbook installs + joins via vault pre-auth key). No SP container, no Xvfb, no scraped sync files.
