# LocalAIPC — Install & Upkeep Runbook

Intent: single Ubuntu host, everything in code (`ansible/site.yml`),
drift-checked with `make check`, converged with `make apply`. No wipe,
no Tower, all free. See ADR-003.

## First install (once, on the host)

```bash
git clone <repo> /opt/localaipc
cd /opt/localaipc
./bootstrap.sh   # installs ansible+git, runs site.yml
```

What `bootstrap.sh` does: nothing clever — installs Ansible, clones the
repo, runs the playbook. All real config lives in `ansible/site.yml`.

## Daily upkeep (drift without wipe)

```bash
make check   # --check --diff + Ollama/OpenClaw/MCP health + nvidia-smi
make apply   # converge: re-run repairs, never duplicates, never wipes
```

`check` is read-only. If it reports changes, `apply` converges them.
Re-running `apply` with no drift changes nothing.

## Health verification (what `make check` hits)

| Target | Command | Expect |
|---|---|---|
| Ollama (native) | `curl -s localhost:11434/api/tags` | model list incl. `qwen3:4b` |
| OpenClaw | `curl -sf localhost:8787/healthz` | 200 (deep: `/readyz`) |
| MCP adapter | `curl -sf localhost:3000/health` | 200 |
| GPU | `nvidia-smi -L` | P2000 listed |

## Messaging (ADR-005, accepted: Discord → Telegram → Signal)

Trial order is least-ops-first. One primary only. WebChat always available as fallback.

### Discord (first trial, private server)

1. Discord app → create server: `Create My Own > For me and my friends` (you + bot only).
2. [Developer Portal](https://discord.com/developers/applications) → New Application → Bot → enable **Message Content Intent** (+ Server Members Intent for allowlists) → Reset Token → copy.
3. OAuth2 URL Generator: scopes `bot` + `applications.commands`; perms View Channels, Send Messages, Read History, Embed Links, Attach Files, Add Reactions (+ Send Messages in Threads if needed). Open URL → add to private server.
4. Discord settings → Advanced → Developer Mode ON. Right-click server → Copy Server ID; right-click own avatar → Copy User ID. Server Privacy Settings → Direct Messages ON (for pairing).
5. On host, set vault vars (`discord_guild_id`, `discord_user_id`, `discord_bot_token`), then:
```bash
make apply  # templates /opt/localaipc/discord.patch.json5 + /opt/localaipc/.env
openclaw config patch --file /opt/localaipc/discord.patch.json5
openclaw gateway restart
openclaw channels status --probe
```
6. DM the bot in Discord → `openclaw pairing approve discord <CODE>` (expires 1h). Test loop: inbound "add chore every 10 days" + outbound daily briefing.
7. Notification discipline: mute private server except DMs/mentions; keep AI chatter out of social servers.

### Telegram (fallback if Discord chafes)

BotFather → `/newbot` → token to vault → `openclaw channels add --channel telegram` → pair. Requires new phone app; gives clean AI-only separation. Simplest OpenClaw path (bundled plugin, long polling).

### Signal (last)

Needs **separate bot number** (personal number gets de-authed/ignored). `openclaw channels add --channel signal` → QR link or SMS register (captcha via `signalcaptchas.org`) → `pairing approve signal <CODE>`. Heaviest ops; best privacy.

## Backups

Systemd timer `localaipc-backup` (daily, persistent) runs `/opt/localaipc/backup.sh`
as root: tars `/opt/localaipc` (excl. `__pycache__`) to `/var/backups/localaipc`
(0700, files 0600) — never model blobs. Retention: daily 7d, Sundays 28d, 1st-of-month 93d.
Check: `systemctl list-timers localaipc-backup`; manual run: `sudo systemctl start localaipc-backup.service`.

Restore (models are never backed up — re-pull after restore):

```bash
ls -t /var/backups/localaipc            # pick a backup
sudo tar -xzf /var/backups/localaipc/localaipc-<date>.tar.gz -C /
ollama pull qwen3:4b                    # model blobs, then pin in site.yml
make apply                              # converge from restored config
```

Note: backups contain `/opt/localaipc/.env` (secrets). Protect the backup dir; do not copy archives off-host unencrypted.

## Secrets

Pinned images/model tags are in `ansible/site.yml` vars. Secrets go in
`ansible-vault` or an env file — never committed:

```bash
ansible-vault create ansible/secrets.yml
ansible-playbook -i ansible/inventory.ini -c local ansible/site.yml --ask-vault-pass
```

Messaging secrets (`discord_bot_token`, plus `discord_guild_id`/`discord_user_id`) follow the same path — vault vars in `site.yml`, rendered to `/opt/localaipc/.env` (0600) and `discord.patch.json5` (0600). Token never committed.

## Changing the system (add a package, service, setting)

1. Edit `ansible/site.yml` (or `ansible/templates/compose.yml.j2` for containers).
2. `make check` — confirm the diff shows only your change.
3. `make apply` — converge.
4. Commit. The playbook is the source of truth, not the live host.

## Troubleshooting

- `site.yml` syntax: `ansible-playbook --syntax-check -i ansible/inventory.ini -c local ansible/site.yml`
- Stack won't start: `docker compose -f /opt/localaipc/compose.yml ps`, then `docker compose -f /opt/localaipc/compose.yml up -d`
- Ollama missing model: `ollama pull qwen3:4b` (then pin the tag in `site.yml` vars)
- Timer not firing: `systemctl status localaipc-backup.timer`
- Discord DMs ignored: `openclaw pairing list discord` → approve; check DM Privacy Settings ON
- Discord guild silent: check `groupPolicy`/`guilds` allowlist + `requireMention`; `openclaw channels status --probe`
- Discord fragment drift: `make check` shows `discord.patch.json5` diff → `make apply` → re-run `config patch` + `gateway restart`
