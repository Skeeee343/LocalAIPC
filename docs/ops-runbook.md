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

## Remote management from Mac (Ansible over SSH)

One-time, when the box has an address:

```bash
# 1. Inventory: fill ansible/inventory.ini [server] (ansible_host + ansible_user)
# 2. Key: cp ansible/secrets.yml.example ansible/secrets.yml, paste
#    `cat ~/.ssh/id_ed25519.pub` into admin_ssh_key
# 3. First key deploy needs a password login (or run bootstrap.sh on the box,
#    which deploys the key locally): ansible-playbook -i ansible/inventory.ini \
#      --limit server ansible/site.yml --ask-pass
ssh <user>@<host>   # verify passwordless login
```

Daily: `make check` / `make apply` from this Mac (targets `--limit server`;
health probes run on the box via the `server` group). On-box fallback:
`make check-local` / `make apply-local`.

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
| MCP adapter (this Mac) | `curl -sf localhost:3000/health` | 200 |
| GPU | `nvidia-smi -L` | P2000 listed |

## Super Productivity (ADR-001 topology: desktop app + local adapter, server over Tailscale)

1. Install the regular desktop app on your daily-use machine ([downloads wiki](https://github.com/super-productivity/super-productivity/wiki/2.01-Downloads-and-Install)): snap (`snap install superproductivity`) or Flatpak on Linux, dmg/pkg on macOS, installer on Windows. Use it normally first (tasks, a repeating chore, a habit).
2. In SP settings, enable the local REST API and copy the bearer token → `sp_token` in `ansible/secrets.yml` (vault).
3. Run the MCP adapter beside SP (same machine, so `SP_BASE_URL=http://localhost:8080` holds): `SP_TOKEN=<token> python3 mcp/server.py`. It already binds `0.0.0.0:3000` for tailnet reachability — never expose it publicly.
4. Tailscale on both ends: server joins via playbook (`tailscale_authkey` = reusable pre-auth key from tailscale.com/admin → `make apply`); install app/login on the SP machine. Verify: from server, `tailscale status` shows the SP machine, and `curl http://<sp-tailnet-ip>:3000/health` returns ok.
5. OpenClaw MCP config points at the adapter over tailnet (wired at first host run, #6).

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
# no openclaw CLI on host — one-shot container (same path, mounted ro):
docker compose --profile cli run --rm openclaw-cli config patch --file /opt/localaipc/discord.patch.json5
docker restart localaipc-openclaw-1
docker logs localaipc-openclaw-1 --tail 8  # expect Discord probe, no trust warning
```
Notes: Public Bot OFF is fine (invite URL still works); toggling privileged
intents after inviting may need kick + re-invite. First DM triggers pairing.
"Typing..." with no reply = agent still inferring on P2000 (slow, not stuck);
true failure shows `embedded run timeout` in gateway logs.
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

Messaging secrets (`discord_bot_token`, plus `discord_guild_id`/`discord_user_id`) follow the same path — vault vars in `site.yml`, rendered to `/opt/localaipc/.env` (0600, includes auto-generated `OPENCLAW_GATEWAY_TOKEN`) and `discord.patch.json5` (0644: IDs only, readable by the non-root CLI container). Token never committed. Gateway token is generate-once (`openssl rand` → `/opt/localaipc/.gateway-token`, 0600), reused across applies.

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
- Secrets silently empty on remote runs: `stat` executes on the target, so the
  `playbook_dir` existence check must `delegate_to: localhost` (controller-side path)
- OpenClaw `Restarting (78) Missing config`: seed `openclaw.json` (`gateway.mode: local`) before first boot
- OpenClaw `EACCES mkdir .../state`: state dir must be owned by the image's runtime uid (resolved via `docker run --rm <image> id -u`), not root
- Gateway `Refusing to bind ... without auth`: token is generated once box-side, passed via `.env`
- `channel is configured, but external plugin "discord" is installed without explicit trust`: set `plugins.entries.discord.enabled=true` (in the patch fragment) and re-apply
- Discord "typing..." forever: `context-pressure-diagnostic` + `embedded run timeout` = context cap too small (see ADR-002 revision); raise, don't retry blindly
- Stale-output confusion: always run `make apply` from the Mac before re-running box commands; compare timestamps before concluding anything
