# Electronics

## The schematics are generated — do not hand-edit them

Both KiCAD sheets are emitted by a script and their connectivity is asserted by
another one. Opening a `.kicad_sch` in KiCAD to move a symbol is fine for
looking; saving over it loses the change on the next `python3 tools/build.py`.

| Sheet | Covers | Generator | Verifier |
|---|---|---|---|
| `drive_mcu_wiring/` | NUCLEO-G474RE ↔ 4× VNH5019 ↔ 4× goBILDA 5203 motor/encoder, Vbat divider, E-stop reporting | `tools/kicad/gen_drive_wiring.py` | `tools/kicad/check_drive_wiring.py` — 43 nets |
| `system_wiring/` | 3S pack, protection chain, regulated rails, Jetson ↔ MCU ↔ sensors, future arm branch | `tools/kicad/gen_system_wiring.py` | `tools/kicad/check_system_wiring.py` — 16 nets |

The two sheets meet at shared net names — `+12V_BUS`, `GND_PWR`, `+5V_RAIL`,
`+3V3`, `GND`, `ESTOP_STATE` — so a rail can be followed across both.

Each sheet is also exported to PDF next to it (`tools/kicad/render_schematics.py`)
so the harness is readable and printable without KiCAD installed. PDF rather than
SVG deliberately: KiCAD's SVG export draws every glyph of its stroke font as a
path, about 1 MB per sheet, against ~70 kB for the PDF.

```bash
python3 tools/kicad/gen_system_wiring.py && python3 tools/kicad/check_system_wiring.py
```

The verifiers need `kicad-cli`. It is found automatically on Windows, macOS and
Linux; set `KICAD_CLI` to override.

## Why generated

Connectivity is a claim that should be mechanical, not visual. The verifiers
export the real netlist and assert the expected topology pin-by-pin against an
expectation written independently of the generator — if the generator is wrong,
the checker must not agree with it. Two real bugs were caught this way when the
drive sheet was first built: caption offsets landing on neighbouring blocks, and
off-grid pin endpoints (KiCAD only connects pins that sit on its 1.27 mm grid).

Element UUIDs are derived with `uuid5` from a stable key rather than `uuid4`, so
regenerating an unchanged schematic produces a byte-identical file. Without that,
every rebuild is a few hundred lines of meaningless diff on a committed artifact.

## The wider picture

`docs/system_model/system_integration.md` indexes these sheets alongside the six
generated integration figures; `firmware/drive_mcu/docs/pin_map.md` is the source
of truth for pin assignment, and `tools/check_integration_map.py` fails the build
if the schematic's net table stops agreeing with it.

## datasheets/

Vendor PDFs, kept because vendor pages change and product pages disagree with
their own datasheets — the 4× encoder-scaling bug (log, 2026-07-16) was caught by
reading the sheet rather than the web page.
