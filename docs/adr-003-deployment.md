# ADR-003 — Deployment: Ansible-local + Compose-as-template

Status: accepted. Date: 2026-09-06 (revised).

## Decision

Ansible runs locally on the single Ubuntu host (`ansible-playbook -i inventory.ini -c local site.yml`). No Tower/AWX/Semaphore, no agent. `compose.yml` is a template Ansible writes, not a separate system. `bootstrap.sh` is a ~10-line shim (install ansible + git, clone, run playbook) used once.

## Why

`compose.yml + bootstrap.sh` alone leaves native Ollama + Super Productivity desktop outside code and has no drift check. Ansible-local covers OS + natives + containers in one idempotent place, free (GPL), with `--check --diff` built in.

## IaC contract (so future agent can manage it)

- Declarative YAML only, pinned images/model tags, `ansible-vault` or env-file secrets (never committed)
- `make check` = `ansible-playbook --check --diff` + `curl :11434/api/tags + curl :8787/health + curl :3000/health + nvidia-smi`
- `make apply` = `ansible-playbook` (idempotent converge, never wipe; re-run repairs, never duplicates)
- Backups via systemd timer (7d/4w/3m), data + config only, not model blobs
- Layout: `ansible/inventory.ini` (localhost), `ansible/site.yml` (base, ollama native, compose template, backup timer)
