# SP capability matrix (ADR-004 Phase 1)

Source: Super Productivity local REST (bearer except `/health`) + plugin API.
Status: REST assumed, validate on host with SP running. Do not invent endpoints.

| Capability | REST | Plugin | File | Notes |
|---|---|---|---|---|
| Create task | ? validate | yes | no (never live-edit `MAIN.json`) | `POST /api/tasks`? confirm path on host |
| Update recurrence | ? validate | yes | no | interval vs weekly anchor TBD |
| Complete occurrence | ? validate | yes | no | must not corrupt series |
| Read counters+history | ? validate | yes | no | habit streaks need plugin if REST gaps |
| Task-complete hook | no | yes | no | plugin-only if needed |

Validate: `curl -s localhost:<sp-port>/health` + bearer `curl $SP_BASE_URL/api/...`.
If REST gaps: minimal SP plugin bridge, else Donetick sidecar for chores (ADR-001).
