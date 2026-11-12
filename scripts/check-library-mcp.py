#!/usr/bin/env python3
"""Exercise the actual MCP stdio connection, design retrieval and image response."""
import base64
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
requests = [
    {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "library-check", "version": "1"}}},
    {"jsonrpc": "2.0", "method": "notifications/initialized"},
    {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
    {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "search_references", "arguments": {"query": "Lusion", "collection": "captures", "limit": 2}}},
    {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "get_reference", "arguments": {"id": "lusion-home", "include_image": True, "checkpoint": 0}}},
    {"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "read_design", "arguments": {"id": "design-md-linear-app"}}},
    {"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {"name": "get_reference", "arguments": {"id": "../../etc/passwd", "include_image": True}}},
    {"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": "search_references", "arguments": {"limit": 1000}}},
    {"jsonrpc": "2.0", "id": 8, "method": "nonexistent"},
    {"jsonrpc": "2.0", "id": {}, "method": "ping"},
    {"jsonrpc": "2.0", "id": [], "method": "ping"},
    {"jsonrpc": "2.0", "id": True, "method": "ping"},
]
result = subprocess.run([sys.executable, str(ROOT / "scripts/library-mcp.py")],
                        input="\n".join(json.dumps(item) for item in requests) + "\n", text=True, capture_output=True, check=True, timeout=30)
responses = [json.loads(line) for line in result.stdout.splitlines()]
assert len(responses) == 11, "Notifications must not produce protocol responses; stdout must contain only JSON-RPC"
for response in responses[-3:]:
    assert response["id"] is None and response["error"]["code"] == -32600, "Invalid ID types must be rejected"
by_id = {item["id"]: item for item in responses}
assert by_id[1]["result"]["protocolVersion"] == "2025-06-18"
assert len(by_id[2]["result"]["tools"]) == 4
search = json.loads(by_id[3]["result"]["content"][0]["text"])
assert search["total"] >= 1 and len(search["items"]) <= 2
image = by_id[4]["result"]["content"][1]
assert image["type"] == "image" and image["mimeType"] == "image/jpeg"
assert base64.b64decode(image["data"]).startswith(b"\xff\xd8"), "MCP must return an actual JPEG"
design = json.loads(by_id[5]["result"]["content"][0]["text"])
assert len(design["designMarkdown"]) > 500 and design["reference"]["upstreamCommit"]
assert by_id[6]["result"]["isError"], "Arbitrary filesystem paths must not be readable"
assert by_id[7]["error"]["code"] == -32602
assert by_id[8]["error"]["code"] == -32601
print("ok: MCP initialization, discovery, search, JPEG evidence, DESIGN.md and invalid-input behavior")
