#!/usr/bin/env python3
"""Export both KiCAD schematics to PDF, next to the sheet they come from.

A `.kicad_sch` is only readable with KiCAD installed, and the harness has to be
readable at the bench. PDF rather than SVG on purpose: KiCAD's SVG export draws
every glyph of its stroke font as a path, which costs ~1 MB per sheet, while the
PDF of the same sheet is ~70 kB, prints correctly, and is what you actually hand
to someone building the harness.

kicad-cli stamps a wall-clock `/CreationDate` into the PDF, which would make
every rebuild a spurious diff on a committed artifact. It is rewritten here to
the sheet's own date — same byte length, so the xref table stays valid.

Skipped with a message (not an error) when kicad-cli is unavailable, so the
parametric build still runs on a machine without KiCAD.

    python3 tools/kicad/render_schematics.py

Output: electronics/KiCAD/<project>/<project>.pdf
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kicad_sch import find_kicad_cli  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PROJECTS = ["drive_mcu_wiring", "system_wiring"]
_DATE = re.compile(rb"/CreationDate\s*\(D:\d{4}:\d{2}:\d{2}:\d{2}:\d{2}:\d{2}\)")
_SHEET_DATE = re.compile(r'\(date "(\d{4})-(\d{2})-(\d{2})"\)')


def normalise(pdf: Path, sch: Path) -> None:
    """Replace the wall-clock creation date with the sheet's own date."""
    m = _SHEET_DATE.search(sch.read_text(encoding="utf-8"))
    y, mo, d = m.groups() if m else ("2026", "01", "01")
    stamp = f"/CreationDate (D:{y}:{mo}:{d}:00:00:00)".encode()
    data = pdf.read_bytes()
    fixed = _DATE.sub(stamp, data)
    if len(fixed) != len(data):  # same length keeps the xref offsets valid
        raise SystemExit("date normalisation changed the PDF length")
    pdf.write_bytes(fixed)


def main() -> int:
    cli = find_kicad_cli()
    if cli is None:
        print("kicad-cli not found — skipping schematic PDF export "
              "(set KICAD_CLI to override)")
        return 0

    for project in PROJECTS:
        folder = ROOT / "electronics" / "KiCAD" / project
        sch = folder / f"{project}.kicad_sch"
        if not sch.exists():
            print(f"missing {sch.relative_to(ROOT)} — run its generator first")
            return 1
        pdf = folder / f"{project}.pdf"
        subprocess.run([cli, "sch", "export", "pdf", "-o", str(pdf), str(sch)],
                       check=True, capture_output=True)
        normalise(pdf, sch)
        print(f"rendered  {pdf.relative_to(ROOT)} ({pdf.stat().st_size // 1024} kB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
