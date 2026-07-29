"""Minimal KiCAD 10 schematic emitter, shared by Buddy's wiring generators.

Buddy's schematics are generated, not drawn: `gen_drive_wiring.py` (the drive
harness) and `gen_system_wiring.py` (power distribution + compute/sensor
interconnect) both build sheets through this module, and both are verified
afterwards by exporting the netlist with `kicad-cli` and asserting the expected
topology pin-by-pin.

Two properties matter and are enforced here:

* **Deterministic.** Element UUIDs are derived with `uuid5` from a stable key
  instead of `uuid4`, so regenerating an unchanged schematic produces a
  byte-identical file. Generated artifacts are committed; random UUIDs would
  make every rebuild a spurious diff and hide the real change.
* **On-grid.** KiCAD only connects pins that land on its 1.27 mm grid. Instance
  origins are snapped, so off-grid endpoints (a bug that already cost a
  debugging session once) cannot come back.

    from kicad_sch import Sheet, PITCH
    sh = Sheet("system_wiring", "Buddy system wiring", "2026-07-28")
    sh.define("JETSON", JETSON_PINS, 30, 25)
    u1 = sh.place("JETSON", "A1", "Jetson Orin Nano Super", 100, 100)
    sh.net(u1, "USB0", "MCU_USB")
    sh.write(outdir)
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import uuid
from dataclasses import dataclass, field
from glob import glob
from pathlib import Path

PITCH = 2.54          # standard KiCAD pin pitch (mm)
GRID = 1.27           # connection grid — off-grid pins silently fail to net
FONT = "(effects (font (size 1.27 1.27)))"
FONT_S = "(effects (font (size 1.016 1.016)))"

_NS = uuid.UUID("6f0f3b52-9d5f-5c2e-9f4a-1f7d2b8c4e11")  # fixed Buddy namespace


def snap(v: float) -> float:
    """Snap to KiCAD's 1.27 mm connection grid."""
    return round(v / GRID) * GRID


def uid(key: str) -> str:
    """Stable UUID for `key` — same key, same UUID, every run."""
    return str(uuid.uuid5(_NS, key))


# --------------------------------------------------------------- kicad-cli --
def find_kicad_cli() -> str | None:
    """Locate `kicad-cli` on any of the three dev platforms.

    Buddy is developed from Windows and macOS, so a hard-coded path is a
    portability bug waiting to happen (it was one). Order: explicit override,
    PATH, then the platform's usual install locations.
    """
    override = os.environ.get("KICAD_CLI")
    if override and Path(override).exists():
        return override
    found = shutil.which("kicad-cli")
    if found:
        return found
    candidates: list[str] = []
    system = platform.system()
    if system == "Windows":
        for base in (os.environ.get("ProgramFiles", r"C:\Program Files"),
                     os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")):
            candidates += sorted(glob(str(Path(base) / "KiCad" / "*" / "bin" / "kicad-cli.exe")),
                                 reverse=True)
    elif system == "Darwin":
        candidates.append("/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli")
    else:
        candidates += ["/usr/bin/kicad-cli", "/usr/local/bin/kicad-cli",
                       "/snap/bin/kicad.kicad-cli"]
    for c in candidates:
        if Path(c).exists():
            return c
    return None


def require_kicad_cli() -> str:
    cli = find_kicad_cli()
    if cli is None:
        raise SystemExit(
            "kicad-cli not found. Install KiCAD 10, or set KICAD_CLI to its path.\n"
            "  Windows: C:\\Program Files\\KiCad\\10.0\\bin\\kicad-cli.exe\n"
            "  macOS:   /Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli\n"
            "  Linux:   apt/flatpak kicad, then `which kicad-cli`")
    return cli


# ----------------------------------------------------------------- symbols --
# A pin is (name, side, slot): side in L/R/T/B, slot = index down/along that side.
Pin = tuple[str, str, int]


def pin_offset(pins: list[Pin], half_w: float, half_h: float,
               name: str) -> tuple[float, float, str]:
    """Symbol-space offset of a pin's connection end, plus the side it is on."""
    for pname, side, slot in pins:
        if pname != name:
            continue
        if side == "L":
            return -half_w - PITCH, -half_h + PITCH * (slot + 1), side
        if side == "R":
            return half_w + PITCH, -half_h + PITCH * (slot + 1), side
        if side == "T":
            return -half_w + PITCH * (slot + 2), -half_h - PITCH, side
        return -half_w + PITCH * (slot + 2), half_h + PITCH, side
    raise KeyError(name)


def symbol_def(name: str, pins: list[Pin], half_w: float, half_h: float) -> str:
    """Library entry: a rectangle body with line pins on the 2.54 mm pitch."""
    body = []
    for i, (pname, _side, _slot) in enumerate(pins, start=1):
        x, y, side = pin_offset(pins, half_w, half_h, pname)
        ang = {"L": 0, "R": 180, "T": 270, "B": 90}[side]
        body.append(
            f'(pin passive line (at {x:g} {y:g} {ang}) (length {PITCH:g}) '
            f'(name "{pname}" {FONT_S}) (number "{i}" {FONT_S}))')
    return f'''    (symbol "Buddy:{name}" (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 {-half_h - 2 * PITCH:g} 0) {FONT})
      (property "Value" "{name}" (at 0 {half_h + 2 * PITCH:g} 0) {FONT})
      (symbol "{name}_0_1"
        (rectangle (start {-half_w:g} {-half_h:g}) (end {half_w:g} {half_h:g})
          (stroke (width 0.254) (type default)) (fill (type background))))
      (symbol "{name}_1_1"
        {chr(10).join("        " + p for p in body)}
      )
    )'''


@dataclass
class Instance:
    lib: str
    ref: str
    value: str
    x: float
    y: float
    pins: list[Pin]
    half_w: float
    half_h: float

    def pin_xy(self, name: str) -> tuple[float, float, str]:
        """Sheet coordinates of a pin end (schematic y grows downward)."""
        sx, sy, side = pin_offset(self.pins, self.half_w, self.half_h, name)
        return self.x + sx, self.y - sy, side


# ------------------------------------------------------------------- sheet --
@dataclass
class Sheet:
    project: str
    title: str
    date: str
    rev: str = "A"
    company: str = "Buddy robot project"
    paper: str = "A3"
    _defs: dict[str, str] = field(default_factory=dict)
    _shapes: dict[str, tuple[list[Pin], float, float]] = field(default_factory=dict)
    _parts: list[str] = field(default_factory=list)
    _labels: list[str] = field(default_factory=list)
    _texts: list[str] = field(default_factory=list)
    _nets: int = 0

    @property
    def root_uuid(self) -> str:
        return uid(f"{self.project}:root")

    def define(self, name: str, pins: list[Pin], half_w: float, half_h: float) -> None:
        self._defs[name] = symbol_def(name, pins, half_w, half_h)
        self._shapes[name] = (pins, half_w, half_h)

    def place(self, lib: str, ref: str, value: str, x: float, y: float) -> Instance:
        pins, half_w, half_h = self._shapes[lib]
        x, y = snap(x), snap(y)
        inst = Instance(lib, ref, value, x, y, pins, half_w, half_h)
        pin_lines = "\n".join(
            f'    (pin "{i}" (uuid "{uid(f"{self.project}:{ref}:pin{i}")}"))'
            for i in range(1, len(pins) + 1))
        self._parts.append(
            f'''  (symbol (lib_id "Buddy:{lib}") (at {x:g} {y:g} 0) (unit 1)
    (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{uid(f"{self.project}:{ref}")}")
    (property "Reference" "{ref}" (at {x:g} {y - half_h - 5.08:g} 0) {FONT})
    (property "Value" "{value}" (at {x:g} {y + half_h + 5.08:g} 0) {FONT})
{pin_lines}
    (instances (project "{self.project}" (path "/{self.root_uuid}" (reference "{ref}") (unit 1))))
  )''')
        return inst

    def net(self, inst: Instance, pin: str, net_name: str) -> None:
        """Attach a global label to a pin — connectivity is by net name."""
        x, y, side = inst.pin_xy(pin)
        ang, justify = (0, "left") if side in ("R", "T") else (180, "right")
        if side == "T":
            ang, justify = 90, "left"
        elif side == "B":
            ang, justify = 270, "right"
        self._nets += 1
        self._labels.append(
            f'  (global_label "{net_name}" (shape input) (at {x:g} {y:g} {ang}) '
            f'(fields_autoplaced yes) (effects (font (size 1.27 1.27)) '
            f'(justify {justify})) '
            f'(uuid "{uid(f"{self.project}:label:{inst.ref}:{pin}:{net_name}")}"))')

    def nets(self, inst: Instance, mapping: dict[str, str]) -> None:
        for pin, net_name in mapping.items():
            self.net(inst, pin, net_name)

    def text(self, s: str, x: float, y: float, size: float = 1.5) -> None:
        self._texts.append(
            f'  (text "{s}" (exclude_from_sim no) (at {x:g} {y:g} 0) '
            f'(effects (font (size {size:g} {size:g})) (justify left)) '
            f'(uuid "{uid(f"{self.project}:text:{len(self._texts)}")}"))')

    @property
    def net_count(self) -> int:
        return self._nets

    def render(self) -> str:
        libs = "\n".join(self._defs[k] for k in self._defs)
        return f'''(kicad_sch
  (version 20260306)
  (generator "buddy_gen")
  (generator_version "10.0")
  (uuid "{self.root_uuid}")
  (paper "{self.paper}")
  (title_block
    (title "{self.title}")
    (date "{self.date}")
    (rev "{self.rev}")
    (company "{self.company}")
  )
  (lib_symbols
{libs}
  )
{chr(10).join(self._parts)}
{chr(10).join(self._labels)}
{chr(10).join(self._texts)}
  (sheet_instances (path "/" (page "1")))
  (embedded_fonts no)
)
'''

    def write(self, outdir: Path) -> Path:
        outdir.mkdir(parents=True, exist_ok=True)
        sch = outdir / f"{self.project}.kicad_sch"
        sch.write_text(self.render(), encoding="utf-8", newline="\n")
        (outdir / f"{self.project}.kicad_pro").write_text(json.dumps({
            "meta": {"filename": f"{self.project}.kicad_pro", "version": 3},
            "sheets": [[self.root_uuid, "Root"]],
        }, indent=2), encoding="utf-8", newline="\n")
        return sch
