# LocalAIPC — Open TODO (all 5 ADRs accepted 2026-09-06)

Order: IaC/base → SP/MCP → messaging trials. Check off as each lands.
Items tagged `Needs your input` are blocked on you — everything else buildable is done.

## Base (ADR-003)

- [x] 1. `bootstrap.sh` repo URL — filled with `https://github.com/Skeeee343/LocalAIPC.git`.
  > Needs your input: flip the repo to public (recommended — nothing sensitive is committed by design; secrets live in vault/`.env`, both gitignored). If you keep it private, HTTPS clone needs a token on the host — say so and I'll switch to SSH + deploy-key steps.
- [x] 2. Pin images — landed: `ghcr.io/openclaw/openclaw:2026.9.2@sha256:a860…` (official GHCR primary, immutable version+digest; latest stable 2026.9.2 per releases) + `python:3.12-slim@sha256:7838…` base in `mcp/Dockerfile`. Compose updated to official contract (host `8787` → container `18789`, healthcheck `/healthz`).
  > Leftover needing host: OpenClaw gateway onboarding (provider key) + state persistence volume — surfaces on first run (#6), not pinnable from here.
- [ ] 3. Super Productivity in playbook — native SP desktop install task in `ansible/site.yml` (biggest code-coverage gap).
  > Research done, decision needed (see below). Key finding: SP has no server database. The official `super-productivity/super-productivity` Docker image serves only the static web UI — task data lives in the browser (or WebDAV/SuperSync), and the web build has documented limitations vs desktop. The local REST API the adapter needs belongs to the desktop/Electron app. So "install DB + web on server, access externally" is not an SP topology — that mental model fits Vikunja/Donetick, not SP. Options:
  > A. SP desktop on the machine you work at daily + adapter beside it, OpenClaw/model on the Ubuntu server over Tailscale (keeps ADR-001/004, full features + agent). Recommended if you want SP's UI.
  > B. SP web container on server for UI-anywhere + WebDAV sync for cross-browser persistence — but the agent then has no server-side data to manage; breaks the MCP path, reopens ADR-001.
  > C. Server-native backend (Donetick/Vikunja) if server-hosted + agent-managed data is the real requirement — reopens ADR-001.
  > Needs your input: A, B, or C? No container needed for A (desktop app, snap/flatpak or download); B needs two containers (web + WebDAV) which I'll add on your go-ahead.
- [x] 4. Backup payload — script + restore procedure + 7d/4w/3m retention behind `localaipc-backup` timer. Landed: `ansible/templates/backup.sh.j2` + `ansible/backup.service`, timer enabled in `site.yml`, restore in runbook. Retention verified in container (daily/Sunday/1st-of-month tiers).
- [x] 5. Secrets file — `ansible/secrets.yml` via vault (or env file), wired into playbook, never committed. Landed: `ansible/secrets.yml.example` + `include_vars` loader in `site.yml` + `.gitignore` + `.env` render (`DISCORD_BOT_TOKEN`, `SP_TOKEN`) consumed by both compose services.
  > Needs your input: fill `ansible/secrets.yml` (or vault) with real tokens when ready — values only, wiring is done.
- [ ] 6. First run on real host — `make check` / `make apply` on Ubuntu; confirm nvidia driver (not just `nvidia-utils`). Includes `discord.patch.json5` + `.env` render check.
  > Needs your input: host access / go-ahead to run. Say the word when the box is ready.

## ADR-004 (read-only landed: `mcp/server.py` + matrix in `docs/sp-capability-matrix.md`)

- [ ] 7. Validate matrix on host — SP running, `curl $SP_BASE_URL/health` + bearer read; fill `?` in matrix.
  > Needs your input: blocked on host + SP running (#3, #6). Nothing to build until endpoints are confirmed — will not invent endpoints.
- [ ] 8. Phase 3 writes — `create/update/complete/create_recurring/maintenance_due` with idempotency, TZ validation, project lookup, dup prevention, retries.
  > Deferred: blocked on #7 (real endpoint paths). Ready to build once the matrix is filled.
- [ ] 9. Phase 4 domain — `create_chore/complete_chore/create_habit/log_habit`, completion-anchored recurrence.
  > Deferred: blocked on #8.
- [ ] 10. Acceptance — ADR-002 30–50 command suite passes.
  > Deferred: blocked on #8–#9.

## ADR-005 (accepted: Discord → Telegram → Signal; IaC fragment landed)

- [x] 11. Discord IaC — `ansible/templates/discord.patch.json5.j2` + `site.yml` vars + `compose.yml.j2` `env_file` (token via vault, 0600, never committed). Runbook section written. Fragment render verified (empty + full IDs).
- [ ] 12. Discord trial — private server (`Create My Own > For me and my friends`), bot (Message Content Intent), IDs to `secrets.yml`, `make apply` → `config patch` → `pairing approve` → 1-week phone→task→briefing loop (inbound "add chore every 10 days" + outbound briefing). Record notification discipline.
  > Needs your input: create the server + bot in the Discord portal (I can't do the clicks/token copy), then paste Server ID + User ID + token path. Steps are in `docs/ops-runbook.md`.
- [ ] 13. Telegram fallback — only if Discord chafes. BotFather `/newbot`, `channels add`, pair, same 1-week loop.
  > Needs your input: only on your go-ahead after the Discord trial.
- [ ] 14. Signal last — only if both chafe. Separate bot number, QR/SMS register + captcha, `pairing approve`, same loop; record number/captcha/rate-limit + signal-cli friction.
  > Needs your input: a spare number capable of receiving SMS, plus go-ahead.
- [ ] 15. Pick one primary — trial winner, least ops burden; WebChat stays fallback. No multi-channel fan-out until Phase 5.
  > Needs your input: your verdict after trials.
