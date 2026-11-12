#!/usr/bin/env python3
"""Validate capture provenance, index consistency and local media hashes offline."""
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent


def validate():
    errors = []

    def check(condition, message):
        if not condition:
            errors.append(message)

    def local(value, label):
        path = (ROOT / value).resolve()
        check(ROOT in path.parents, f"{label}: path escapes checkout")
        check(path.is_file(), f"{label}: missing {value}")
        return path

    catalog = json.loads((ROOT / "data/landing-pages.json").read_text())
    check(catalog["count"] == len(catalog["items"]), "Capture count is stale")
    seen = set()
    expected_records = {path.relative_to(ROOT).as_posix() for path in (ROOT / "captures").glob("*/*/page.json")}
    check(expected_records == {item["record"] for item in catalog["items"]}, "Capture index omits records or includes stale paths; rebuild it")
    for item in catalog["items"]:
        ident = item["id"]
        check(ident not in seen and bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", ident)), f"Invalid/duplicate capture ID: {ident}")
        seen.add(ident)
        for field in ("url", "source"):
            check(urlparse(item[field]).scheme == "https", f"{ident}: {field} must be an HTTPS provenance URL")
        path = local(item["record"], ident)
        if not path.exists():
            continue
        record = json.loads(path.read_text())
        for field in ("id", "url", "source", "status", "kind", "viewport", "capturedAt"):
            check(record[field] == item[field], f"{ident}: index field {field} is stale")
        check(bool(record.get("rights")) and bool(record.get("limitations")), f"{ident}: missing rights/limitations")
        check(record["status"] in ("captured", "needs-review", "failed"), f"{ident}: invalid status")
        local(item["guide"], ident)
        if record["status"] == "captured":
            check(len(record.get("checkpoints", [])) >= 6, f"{ident}: fewer than six checkpoints")
            check(bool(item.get("video")), f"{ident}: missing video")
        for field in ("preview", "video"):
            if item.get(field):
                local(item[field], ident)
        for media in record.get("files", []):
            media_path = local((path.parent.relative_to(ROOT) / media["file"]).as_posix(), ident)
            if media_path.exists():
                content = media_path.read_bytes()
                check(len(content) == media["bytes"] and len(content) > 0, f"{ident}: media byte count mismatch: {media['file']}")
                check(hashlib.sha256(content).hexdigest() == media["sha256"], f"{ident}: media hash mismatch: {media['file']}")
        for resource in record.get("resources", []):
            url = urlparse(resource["url"])
            site = ".".join(urlparse(record["url"]).hostname.removeprefix("www.").split(".")[-2:])
            allowed = url.hostname in ("lusion.co", "lusion.dev") or bool(url.hostname and url.hostname.endswith(".lusion.co")) if site == "lusion.co" \
                else bool(url.hostname and (url.hostname == site or url.hostname.endswith("." + site)))
            check(allowed, f"{ident}: unexpected resource host")
            check(not url.query and not url.fragment, f"{ident}: query/fragment leaked into resource inventory")
        if item.get("video"):
            check(item["video"].endswith("/" + record["video"]["file"]), f"{ident}: mismatched video path")
    for collection in json.loads((ROOT / "data/library-manifest.json").read_text())["collections"]:
        data = json.loads(local(collection["path"], collection["name"]).read_text())
        check(collection["count"] == len(data["items"]), f"Manifest count stale: {collection['name']}")
    analyses = json.loads((ROOT / "data/design-md.json").read_text())["items"]
    analysis_ids = set()
    for item in analyses:
        check(item["id"] not in analysis_ids, f"Duplicate design-analysis ID: {item['id']}")
        analysis_ids.add(item["id"])
        path = local(item["localDesignPath"], item["id"])
        local(item["licensePath"], item["id"])
        check(bool(re.fullmatch(r"[a-f0-9]{40}", item["upstreamCommit"])), f"{item['id']}: invalid upstream commit")
        if path.exists():
            content = path.read_bytes()
            check(len(content) == item["bytes"] and hashlib.sha256(content).hexdigest() == item["sha256"], f"{item['id']}: imported document changed without provenance update")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"ok: {len(seen)} capture packages, {len(analyses)} licensed analyses, indexes, provenance and SHA-256 hashes")
    return 0


if __name__ == "__main__":
    raise SystemExit(validate())
