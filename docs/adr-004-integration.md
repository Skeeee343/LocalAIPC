# ADR-004 — MCP integration + safety

Status: approved. Date: 2026-09-06.

## Decision

Thin MCP server over SP local REST. Tools: `get_today, search_tasks, overdue, list_projects, create_task, update_task, complete_task, create_recurring_task, habit_history, maintenance_due` + domain layer `create_chore/complete_chore/create_habit/log_habit` with completion-anchored recurrence.

## Rules

- Read-only first; writes add idempotency keys, TZ-aware date validation, project lookup, dup prevention, retries.
- Confirm: delete, bulk complete/reschedule/move, anything notifying others. Short model context (relevant tasks only).
- Never: edit `MAIN.json` live, expose SP API publicly, broad shell/FS for agent, bulk ops without preview count.
