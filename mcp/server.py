#!/usr/bin/env python3
"""LocalAIPC MCP adapter — read-only Phase 2 (ADR-004). Stdlib only."""
import json, os, sys, urllib.request, urllib.parse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from zoneinfo import ZoneInfo

SP_BASE = os.environ.get("SP_BASE_URL", "http://localhost:8080")
SP_TOKEN = os.environ.get("SP_TOKEN", "")
PORT = int(os.environ.get("PORT", "3000"))
LOCAL_TZ = ZoneInfo(os.environ.get("TZ", "America/Chicago"))

def sp_get(path, params=None, retries=2):
    url = SP_BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    for _ in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {SP_TOKEN}"} if SP_TOKEN else {})
            with urllib.request.urlopen(req, timeout=5) as r:
                return json.load(r)
        except Exception as e:
            last = e
    raise last

def slim(tasks, limit=50):
    return [{"id": t.get("id"), "title": t.get("title"), "due": t.get("due"),
             "project": t.get("project"), "status": t.get("status")}
            for t in (tasks if isinstance(tasks, list) else tasks.get("tasks", []))][:limit]

def parse_date(s):  # ponytail: strict TZ-aware, adapter owns date math
    d = datetime.fromisoformat(s)
    return d if d.tzinfo else d.replace(tzinfo=LOCAL_TZ)

def next_from_completion(days):
    return datetime.now(timezone.utc).astimezone(LOCAL_TZ).date().isoformat() + f" +{days}d"

class H(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *a): pass
    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(u.query)
        try:
            if u.path == "/health":
                return self._send(200, {"ok": True})
            if u.path == "/today":
                return self._send(200, {"tasks": slim(sp_get("/api/tasks", {"due": "today"}))})
            if u.path == "/overdue":
                return self._send(200, {"tasks": slim(sp_get("/api/tasks", {"due": "overdue"}))})
            if u.path == "/search":
                return self._send(200, {"tasks": slim(sp_get("/api/tasks", {"q": q.get("q", [""])[0]}))})
            if u.path == "/projects":
                return self._send(200, sp_get("/api/projects"))
            if u.path == "/habit_history":
                return self._send(200, sp_get("/api/habits/history", {"id": q.get("id", [""])[0]}))
            return self._send(404, {"error": "unknown"})
        except Exception as e:
            return self._send(502, {"error": f"sp unreachable: {e}"})
    def do_POST(self):  # writes disabled until Phase 3
        self._send(501, {"error": "writes disabled until Phase 3", "confirm_required": True})

def check():
    errs = []
    if not SP_BASE.startswith("http://localhost") and not SP_BASE.startswith("http://127."):
        errs.append("SP_BASE_URL must stay localhost (never expose SP publicly)")
    parse_date("2026-09-06T09:00:00-05:00")
    try:
        assert next_from_completion(90).endswith("+90d")
    except Exception as e:
        errs.append(str(e))
    try:
        sp_get("/health")
    except Exception as e:
        print(f"warn: SP not reachable ({e}) — matrix validation pending on host")
    if errs:
        print("FAIL: " + "; ".join(errs)); return 1
    print("ok: config valid"); return 0

def self_test():
    assert parse_date("2026-09-06T09:00:00-05:00").tzinfo is not None
    assert parse_date("2026-09-06T09:00:00").tzinfo is not None  # naive -> local TZ
    assert next_from_completion(10).endswith("+10d")
    assert slim([{"id": "1", "title": "t", "extra": "dropped"}])[0].get("extra") is None
    print("self-test ok")

if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(check())
    if "--self-test" in sys.argv:
        self_test()
    else:
        HTTPServer(("0.0.0.0", PORT), H).serve_forever()
