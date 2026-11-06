"""Tiny client for the local VoiceStudio MCP server (keeps base64 audio out of the agent's context).

The server URL and headers are read from the nearest project-local .mcp.json (walking up from the current
folder), entry "voicestudio". Nothing is hard-coded here, and nothing is ever written to a global config.
"""
import json, os, urllib.request

def _config():
    d = os.getcwd()
    while True:
        p = os.path.join(d, '.mcp.json')
        if os.path.exists(p):
            s = json.load(open(p)).get('mcpServers', {}).get('voicestudio')
            if s: return s['url'], s.get('headers', {})
        if os.path.dirname(d) == d: break
        d = os.path.dirname(d)
    raise SystemExit('No project-local .mcp.json with a "voicestudio" server found above ' + os.getcwd())

URL, _H = _config()
H = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream", **_H}

def rpc(p, sid=None):
    h = dict(H)
    if sid: h["mcp-session-id"] = sid
    with urllib.request.urlopen(urllib.request.Request(URL, json.dumps(p).encode(), h), timeout=900) as r:
        sid = r.headers.get("mcp-session-id") or sid; b = r.read().decode()
    l = [x[6:] for x in b.splitlines() if x.startswith("data: ")]
    return sid, (json.loads(l[0]) if l else (json.loads(b) if b.strip() else None))

def session():
    sid, _ = rpc({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "episode-reel", "version": "1"}}})
    rpc({"jsonrpc": "2.0", "method": "notifications/initialized"}, sid); return sid

def call(sid, name, arguments):
    _, r = rpc({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": name, "arguments": arguments}}, sid)
    return json.loads(r["result"]["content"][0]["text"])
