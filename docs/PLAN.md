# LocalAIPC — Plan

Source: `duck.ai_2026-09-06_14-10-27.txt` (7 prompts, GPT-5.6 Luna — provenance only; ADRs are authoritative where they conflict, e.g. ADR-002 supersedes its Gemma 4 sizing).
Goal: self-hosted TickTick replacement (tasks + recurring chores + habits) with local AI assistant. Single-machine scope.

## Locked stack

- Tasks: Super Productivity (ADR-001, accepted)
- Agent gateway: OpenClaw
- Model runtime: Ollama native, default `qwen3:4b` 4K thinking-off; fallbacks `qwen2.5:3b` / `llama3.2:3b` (ADR-002, approved — Gemma 4 E2B/E4B disqualified on size: 7.2/9.6GB tags)
- Bridge: small typed MCP adapter, REST first, no direct `MAIN.json` edits (ADR-004, approved)
- Deploy: single Ubuntu host, Ansible-local (`ansible/site.yml`), Compose-as-template, `bootstrap.sh` shim only (ADR-003, accepted)
- Chat: Discord → Telegram → Signal trial order, private Discord server, WebChat fallback (ADR-005, accepted)

## Hardware envelope (design to this, not best-case)

- Host: single Ubuntu box (familiar, not hard requirement), 4 cores assumed
- RAM: 16GB min, target 24–32GB if budget allows
- GPU: Quadro P2000 5GB VRAM, Pascal, no tensor cores — **no CPU offload assumed**
- Disk: 50GB free SSD min, 100GB preferred (OS 10–20GB, models 5–15GB, app+logs 5–15GB, backups rest)
- Consequence: model + KV cache + runtime must fit fully in ~5GB at 4K context. This rules out anything needing split offload as default.

## Phases (configs deferred)

1. Validate Super Productivity REST/plugin coverage read-only (capability matrix).
2. Read-only MCP (`get_today, search, overdue, projects, habit_history`).
3. Validated writes with idempotency + confirm on delete/bulk.
4. Habit/chore domain layer (completion-anchored recurrence).
5. Proactive briefings. Staged automation last.

## Long-term manageability (IaC)

All future configs are IaC by the ADR-003 contract:
declarative YAML, idempotent re-runnable, `healthcheck` + `config check` entrypoint,
pinned versions, secrets via env/vault file (never in git), so a future agent can
`check → diff → patch → verify` without shell archaeology.

## Open risks

- Model: ADR-002 approved; remaining risk is tool-accuracy on 3–4B class — run 30–50 command suite before lock.
- Super Productivity local API maturity — validate before building writes.
- Signal/Discord hosting friction — ADR-005 accepted (Discord first).
