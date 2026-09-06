# ADR-005 — Messaging channel (accepted)

Status: accepted. Date: 2026-09-06. Lean: evaluate Discord → Telegram → Signal.

## Eliminated

iMessage — no Linux host path (Apple-only, no stable server bridge). Dropped.

## Evaluation (trial order)

- Discord: user already installed, no new app, no per-message charge. Easiest familiar trial (bot token, DM + private server). Test: outbound daily briefing + inbound "add chore every 10 days". Watch: mixes AI into social app; notification discipline needed.
- Telegram: simplest OpenClaw path overall (BotFather token, bundled plugin), no per-message charge, but requires new phone app. Fallback if Discord chafes. Gives clean AI-only separation.
- Signal: best privacy, familiar, no new app, no per-message charge — but heaviest ops (separate bot number, captcha + SMS verify, signal-cli brittle). Try last.

## Decision rule

Pick the one that survives a 1-week trial of phone→task→briefing loop with least ops burden. Keep WebChat always as fallback. One primary only — no multi-channel fan-out until Phase 5.
