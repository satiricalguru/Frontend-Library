# Give agents a reference library

Frontend Library supports three access paths: a portable skill, a dependency-free search CLI, and a local read-only MCP server. They read the same catalogs and evidence; no hosted service or account is required.

## Portable skill

The repository includes [`.agents/skills/frontend-library/SKILL.md`](../.agents/skills/frontend-library/SKILL.md) for agents that discover repository skills. For Codex across projects, run this from the checkout:

```bash
mkdir -p "$HOME/.codex/skills"
ln -s "$PWD/.agents/skills/frontend-library" "$HOME/.codex/skills/frontend-library"
```

The command intentionally does not overwrite an existing skill. Restart or refresh your agent's skill discovery if necessary. Other agents can read the same SKILL.md or copy its folder into their documented skills directory. If the skill is copied away from the checkout, set `FRONTEND_LIBRARY_ROOT` or pass `--library` when searching.

Example request:

> Use $frontend-library to study Lusion's homepage. Inspect the desktop and mobile evidence, write a section and motion brief, then implement that direction in this project's existing stack. Identify missing assets and verify matching viewport checkpoints.

## Offline search

From the repository root:

```bash
python3 scripts/query-library.py Lusion --type captures --has-video --json
python3 scripts/query-library.py scroll --type codrops --limit 6 --json
python3 scripts/query-library.py Linear --type design-md --json
python3 scripts/query-library.py --type media-resources --tag "Stock Videos" --limit 20 --json
python3 scripts/query-library.py --help
```

From another project, add `--library /absolute/path/to/Frontend-Library`. Results include stable IDs, original sources, coverage and absolute paths to available evidence. The query tool does not fetch live websites. Captures, design analyses and link indexes are distinct collection types.

## MCP connection

Configure an MCP client to launch Python with the **absolute** server path. A client using `mcpServers` configuration can use:

```json
{
  "mcpServers": {
    "frontend-library": {
      "command": "python3",
      "args": ["/absolute/path/to/Frontend-Library/scripts/library-mcp.py"]
    }
  }
}
```

Clients have different configuration files; use their documented configuration location. This example does not modify your client settings. The server uses newline-delimited JSON-RPC over stdio, implements MCP tools, performs no network requests, and exposes no writes or browser controls. It supports protocol negotiation for 2024-11-05, 2025-03-26 and 2025-06-18; clients requiring a different protocol need compatibility support.

| Tool | Purpose |
|:--|:--|
| `list_collections` | Discover catalog counts and evidence types |
| `search_references` | Find a small set by query and collection; up to 20 results |
| `get_reference` | Read a record and optionally return one local checkpoint as an actual image |
| `read_design` | Read a bundled, attributed DESIGN.md analysis; link-only entries explain their limits |

For visual context, call `get_reference` with `{"id":"lusion-home","include_image":true,"checkpoint":0}`. A multimodal MCP client can inspect the returned JPEG. Change `checkpoint` to compare later states. Video paths are returned for clients with local media access; the server does not pretend to send a full video as an image.

Validate the connection behavior locally:

```bash
python3 scripts/check-library-mcp.py
```

This lightweight server is intended for local stdio clients. It is not a public HTTP service or a replacement for a production multi-user reference platform. Its transport and tool message formats follow the [MCP transport specification](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports) and [tool specification](https://modelcontextprotocol.io/specification/2025-06-18/server/tools).

## A fidelity workflow

1. Pick the primary reference and inspect its actual visuals. Use one local DESIGN.md analysis for relevant tokens and component rules. Preserve an existing project DESIGN.md and merge verified constraints.
2. Write the section order, measured composition, camera/scene states, triggers, timing ranges, asset requirements and mobile alternatives. Label observed, inferred and proposed claims.
3. Build static framing first, then implement DOM/canvas motion with a shared timeline. Match the user's product and stack. Use original or appropriately licensed assets.
4. Compare the same viewport and interaction checkpoints. Check mobile, keyboard access, reduced motion and loading failures. Report specific remaining differences.

This workflow improves evidence and verification. It cannot guarantee mistake-free or pixel-identical reconstruction when models, source shaders, fonts, scene settings or interaction states are unavailable. A studio case study or a DESIGN.md analysis is not equivalent to capturing the live site.
