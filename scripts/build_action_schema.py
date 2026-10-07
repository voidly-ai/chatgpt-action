#!/usr/bin/env python3
"""Project a pinned agent OpenAPI snapshot into two anonymous, read-only Actions."""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]
API_HOST = "https://api.voidly.ai"
GATEWAY_HOST = "https://x402.voidly.ai"

API_PATHS = (
    "/v1/agent/discover",
    "/v1/agent/capabilities/search",
    "/v2/marketplace/directory",
    "/v2/marketplace/services",
    "/v1/home/public/handles/{handle}",
    "/v1/home/public/profiles/{profileId}",
)
GATEWAY_PATHS = (
    "/v1/services",
    "/v1/services/match",
    "/v1/services/{serviceId}",
)


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, _data: object) -> bool:
        return True


def _visit_refs(value: object, pending: list[str]) -> None:
    if isinstance(value, dict):
        ref = value.get("$ref")
        if isinstance(ref, str):
            pending.append(ref)
        for child in value.values():
            _visit_refs(child, pending)
    elif isinstance(value, list):
        for child in value:
            _visit_refs(child, pending)


def _components_for(source: dict, paths: dict) -> dict:
    pending: list[str] = []
    _visit_refs(paths, pending)
    selected: dict[str, dict] = {}
    seen: set[str] = set()
    while pending:
        ref = pending.pop()
        if ref in seen:
            continue
        seen.add(ref)
        parts = ref.split("/")
        if len(parts) != 4 or parts[:2] != ["#", "components"]:
            raise ValueError(f"unsupported external or nested reference: {ref}")
        section = parts[2].replace("~1", "/").replace("~0", "~")
        name = parts[3].replace("~1", "/").replace("~0", "~")
        value = deepcopy(source["components"][section][name])
        selected.setdefault(section, {})[name] = value
        _visit_refs(value, pending)
    return {section: dict(sorted(entries.items())) for section, entries in sorted(selected.items())}


def _project(source: dict, selected_paths: tuple[str, ...], host: str, title: str) -> dict:
    paths: dict[str, dict] = {}
    for path in selected_paths:
        original = source["paths"][path]
        servers = original.get("servers")
        if host == GATEWAY_HOST:
            if not isinstance(servers, list) or [item.get("url") for item in servers] != [host]:
                raise ValueError(f"gateway host drift: {path}")
        elif servers:
            raise ValueError(f"unexpected alternate API host: {path}")

        operation = {
            key: deepcopy(value)
            for key, value in original["get"].items()
            if not key.startswith("x-") or key == "x-voidly-availability"
        }
        if operation.get("security", []) != [] or "requestBody" in operation:
            raise ValueError(f"route is not an anonymous GET: {path}")
        operation["security"] = []
        if path.startswith("/v1/home/public/"):
            operation["x-voidly-availability"] = "feature_gated_unverified"
            operation["description"] = (
                "Anonymous read of a current public Agent Home profile, subject to feature availability, "
                "profile consent, and search indexing. Private, revoked, stale, unknown, or unavailable "
                "profiles return 404. Bio and board posts appear only when separately consented; posts "
                "are limited to visible, unexpired entries. Listings and verified reputation are "
                "currently unavailable. This source contract does not prove the endpoint is live."
            )
        for parameter in operation.get("parameters", []):
            if parameter.get("name") == "limit" and parameter.get("in") == "query":
                parameter["schema"]["default"] = 10
                parameter["schema"]["maximum"] = 10
        item = {key: deepcopy(original[key]) for key in ("summary", "description", "parameters") if key in original}
        item["get"] = operation
        paths[path] = item

    document = {
        "openapi": "3.1.0",
        "info": {
            "title": title,
            "version": source["info"]["version"],
            "description": (
                "Public, read-only Voidly discovery projected from a pinned agent OpenAPI snapshot. "
                "Source wiring is not proof of a served release. Catalog entries do not authorize "
                "payment, execution, publication, or private Agent Home access."
            ),
            "contact": {"name": "Voidly", "url": "https://voidly.ai"},
        },
        "servers": [{"url": host}],
        "security": [],
        "paths": paths,
        "x-voidly-coverage": {
            "servedVerified": False,
        },
    }
    components = _components_for(source, paths)
    if components:
        document["components"] = components
    return document


def build_documents(source_bytes: bytes) -> dict[str, dict]:
    source = json.loads(source_bytes)
    if source.get("openapi") != "3.1.0" or source.get("info", {}).get("version") != "2026-10-07.2":
        raise ValueError("source OpenAPI version drift")
    if source.get("x-voidly-coverage", {}).get("servedVerified") is not False:
        raise ValueError("source/served boundary changed")
    return {
        "openapi.yaml": _project(source, API_PATHS, API_HOST, "Voidly public discovery Action"),
        "openapi-x402.yaml": _project(source, GATEWAY_PATHS, GATEWAY_HOST, "Voidly x402 catalog Action"),
    }


def render(document: dict) -> str:
    return (
        "# Generated by scripts/build_action_schema.py from the pinned agent OpenAPI snapshot.\n"
        "# These source contracts do not prove served availability.\n"
        + yaml.dump(document, Dumper=NoAliasDumper, sort_keys=False, allow_unicode=True, width=100)
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="local agent OpenAPI snapshot")
    parser.add_argument("--check", action="store_true", help="compare with committed outputs")
    args = parser.parse_args()
    documents = build_documents(args.source.read_bytes())
    changed = []
    for filename, document in documents.items():
        output = ROOT / filename
        expected = render(document)
        if args.check:
            if not output.exists() or output.read_text() != expected:
                changed.append(filename)
        else:
            output.write_text(expected)
    if changed:
        print("Action schema drift: " + ", ".join(changed), file=sys.stderr)
        return 1
    print("Action schemas match pinned source" if args.check else "Wrote public Action schemas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
