#!/usr/bin/env python3
"""Render a self-contained status page from a plain-text service list.

Input format, one service per line:

    <name>  <state>  [note]

`state` is one of ok / degraded / down. Anything else is a parse error and is
reported rather than guessed at — a status page that silently drops a service
is worse than one that fails to build, because the missing row looks like a
service that does not exist rather than one nobody measured.

    python3 statuspage.py --in services.txt --out status.html
"""

from __future__ import annotations

import argparse
import html
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

STATES = {"ok": "operational", "degraded": "degraded", "down": "outage"}


@dataclass(frozen=True)
class Service:
    name: str
    state: str
    note: str = ""


class ParseError(Exception):
    """A line that cannot be read. Never swallowed."""


def parse_line(line: str, lineno: int) -> Service | None:
    """One service, or None for a blank/comment line."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    parts = stripped.split(None, 2)
    if len(parts) < 2:
        raise ParseError(f"line {lineno}: expected `<name> <state> [note]`, got {stripped!r}")
    name, state = parts[0], parts[1].lower()
    if state not in STATES:
        raise ParseError(
            f"line {lineno}: unknown state {parts[1]!r} for {name!r} — "
            f"expected one of {', '.join(sorted(STATES))}")
    return Service(name, state, parts[2] if len(parts) > 2 else "")


def parse(text: str) -> tuple[list[Service], list[str]]:
    """Every service, and every error. Both — one bad line must not hide the rest."""
    services, errors = [], []
    for i, line in enumerate(text.splitlines(), start=1):
        try:
            svc = parse_line(line, i)
        except ParseError as exc:
            errors.append(str(exc))
            continue
        if svc is not None:
            services.append(svc)
    return services, errors


def render(services: list[Service], errors: list[str],
           generated_at: datetime | None = None) -> str:
    """`generated_at`, if given, must be a UTC-aware datetime — the caller's
    clock, not this function's. It is when the page was built, which is not
    the same moment as when any individual service was last checked."""
    e = html.escape
    rows = "\n".join(
        f'    <tr class="{s.state}"><td>{e(s.name)}</td>'
        f'<td>{e(STATES[s.state])}</td><td>{e(s.note)}</td></tr>'
        for s in services)
    problems = ""
    if errors:
        items = "\n".join(f"      <li>{e(err)}</li>" for err in errors)
        problems = (f'  <section class="errors"><h2>Could not read</h2>\n'
                    f'    <ul>\n{items}\n    </ul></section>\n')
    generated = ""
    if generated_at is not None:
        stamp = e(generated_at.strftime("%Y-%m-%d %H:%M:%S UTC"))
        generated = (f'  <p class="generated">Page generated {stamp} '
                     f'&mdash; this is when the page was built, not when '
                     f'any service was last checked.</p>\n')
    return f"""<!doctype html>
<html lang="en"><meta charset="utf-8">
<title>Service status</title>
<style>
  body {{ font: 16px/1.5 system-ui, sans-serif; margin: 3rem auto; max-width: 42rem; }}
  table {{ border-collapse: collapse; width: 100%; }}
  td {{ padding: .5rem .75rem; border-bottom: 1px solid #ddd; }}
  .ok td:nth-child(2) {{ color: #2e6b4f; }}
  .degraded td:nth-child(2) {{ color: #916620; }}
  .down td:nth-child(2) {{ color: #96382f; }}
  .errors {{ color: #96382f; }}
  .generated {{ color: #555; font-size: .9rem; }}
</style>
<h1>Service status</h1>
{generated}{problems}  <table>
{rows}
  </table>
</html>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--in", dest="src", type=Path, required=True)
    ap.add_argument("--out", dest="dest", type=Path, required=True)
    args = ap.parse_args()

    services, errors = parse(args.src.read_text())
    generated_at = datetime.now(timezone.utc)
    args.dest.write_text(render(services, errors, generated_at))
    print(f"status: {len(services)} service(s), {len(errors)} unreadable line(s) "
          f"-> {args.dest}")
    # Unreadable input is a failure, not a footnote. The page still renders so
    # the problem is visible, but the build does not pass.
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
