"""Loader for the integration map — Buddy's topology source of truth.

`docs/system_model/integration_map.yaml` owns what connects to what; it must
never own a number that `design_params.yaml` or the requirements yaml already
owns. Instead it writes a reference (`param:power.protection.main_fuse_a`),
which `resolve()` turns back into the live value at draw time. That is why a
diagram can never quote a stale current limit: there is no copy to go stale.

    from buddy_calcs import integration as im
    im.MAP["blocks"]                     # raw
    im.block("drive_mcu")                # by id
    im.resolve("param:firmware.pwm_hz")  # -> 20000
    im.fmt("param:power.protection.main_fuse_a", "{:g} A")  # -> "60 A"
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from . import P, R, ROOT

MAP_FILE = ROOT / "docs" / "system_model" / "integration_map.yaml"

MAP: dict = yaml.safe_load(MAP_FILE.read_text(encoding="utf-8"))

_REF = re.compile(r"(param|req):([A-Za-z0-9_.]+)")


def _dig(tree: dict, dotted: str) -> Any:
    node: Any = tree
    for key in dotted.split("."):
        if not isinstance(node, dict) or key not in node:
            raise KeyError(dotted)
        node = node[key]
    return node


def resolve(value: Any) -> Any:
    """Resolve `param:`/`req:` references. Non-strings pass through unchanged.

    A string that is exactly one reference returns the typed value; a string
    that merely *contains* references has each one substituted inline, so
    "param:power.bus.v_cutoff–param:power.bus.v_full V" renders as "9.0–12.6 V".
    """
    if not isinstance(value, str):
        return value
    whole = _REF.fullmatch(value)
    if whole:
        return _dig(P if whole.group(1) == "param" else R, whole.group(2))
    return _REF.sub(lambda m: _fmt_scalar(
        _dig(P if m.group(1) == "param" else R, m.group(2))), value)


def _fmt_scalar(v: Any) -> str:
    return f"{v:g}" if isinstance(v, (int, float)) and not isinstance(v, bool) else str(v)


def fmt(value: Any, template: str = "{}") -> str:
    """Resolve then format — the usual call from a figure script."""
    r = resolve(value)
    return "" if r is None else template.format(r)


def refs() -> list[str]:
    """Every reference string in the map, for the drift checker."""
    found: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
        elif isinstance(node, str):
            found.extend(f"{a}:{b}" for a, b in _REF.findall(node))

    walk(MAP)
    return found


# ---------------------------------------------------------------- accessors --
def block(block_id: str) -> dict:
    for b in MAP["blocks"]:
        if b["id"] == block_id:
            return b
    raise KeyError(f"no block {block_id!r} in {MAP_FILE.name}")


def link(link_id: str) -> dict:
    for ln in MAP["links"]:
        if ln["id"] == link_id:
            return ln
    raise KeyError(f"no link {link_id!r} in {MAP_FILE.name}")


def node(node_id: str) -> dict:
    for n in MAP["ros"]["nodes"]:
        if n["id"] == node_id:
            return n
    raise KeyError(f"no ROS node {node_id!r} in {MAP_FILE.name}")


def topic(name: str) -> dict:
    for t in MAP["ros"]["topics"]:
        if t["name"] == name:
            return t
    raise KeyError(f"no topic {name!r} in {MAP_FILE.name}")


def rail(rail_id: str) -> dict:
    for r in MAP["power"]["rails"]:
        if r["id"] == rail_id:
            return r
    raise KeyError(f"no rail {rail_id!r} in {MAP_FILE.name}")


def validate() -> list[str]:
    """Structural checks — ids unique, cross-references land. Deep consistency
    against pin_map/protocol/bridge source lives in tools/check_integration_map.py."""
    problems: list[str] = []

    def dupes(items: list[dict], key: str, what: str) -> None:
        seen: set = set()
        for it in items:
            if it[key] in seen:
                problems.append(f"duplicate {what} id {it[key]!r}")
            seen.add(it[key])

    dupes(MAP["blocks"], "id", "block")
    dupes(MAP["links"], "id", "link")
    dupes(MAP["ros"]["nodes"], "id", "ROS node")
    dupes(MAP["ros"]["topics"], "name", "topic")
    dupes(MAP["power"]["rails"], "id", "rail")

    block_ids = {b["id"] for b in MAP["blocks"]}
    node_ids = {n["id"] for n in MAP["ros"]["nodes"]}
    allowed = set(MAP["meta"]["status_values"])

    for b in MAP["blocks"]:
        if b["status"] not in allowed:
            problems.append(f"block {b['id']}: unknown status {b['status']!r}")
    for ln in MAP["links"]:
        for end in ("from", "to"):
            if ln[end] not in block_ids:
                problems.append(f"link {ln['id']}: {end} {ln[end]!r} is not a block")
        if ln["status"] not in allowed:
            problems.append(f"link {ln['id']}: unknown status {ln['status']!r}")
    for r in MAP["power"]["rails"]:
        for fed in r.get("feeds", []) or []:
            if fed not in block_ids:
                problems.append(f"rail {r['id']}: feeds unknown block {fed!r}")
        if r["source"] not in block_ids:
            problems.append(f"rail {r['id']}: source {r['source']!r} is not a block")
    for t in MAP["ros"]["topics"]:
        for end in ("from", "to"):
            for n in t.get(end) or []:
                if n not in node_ids:
                    problems.append(f"topic {t['name']}: {end} {n!r} is not a ROS node")

    for ref in refs():
        try:
            resolve(ref)
        except KeyError:
            problems.append(f"dangling reference {ref!r} — no such key")

    return problems
