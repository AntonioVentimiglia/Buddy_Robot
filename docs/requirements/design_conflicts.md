2026-06-26 · **conflict #4 revised 2026-07-31** (budget raised to $2000 and split
into pots; see ADR-0008 and ADR-0009)

Known design conflicts:
1. 2.5 m/s top speed conflicts with 0.25 m stopping distance and operation near people.
2. 0.3 m x 0.3 m footprint conflicts with 20 kg base mass + 10 kg payload + future arm.
3. 20 degree ramp conflicts with small footprint, high center of gravity risk, and low budget.
4. **Budget — revised 2026-07-31, no longer a blocking conflict but a tight one.**
   The original $300–600 band was superseded: the programme budget is **$2000**,
   and it is now understood to cover the arms, LiDAR, and RGB-D as well as the
   base. Tracked as two pots plus a capital line, so that "v0.1 is funded" and
   "the whole roadmap is funded" stop being the same question:

   | Pot | Contents | Est. |
   |---|---|---|
   | *Spent to date* | Jetson, Nucleos, drivers, drivetrain, network, tools | **$1,173.85** |
   | **v0.1 remaining** | LiFePO4 pack + charger, 5 V buck (the 12 V one is deleted — see ADR-0005 amendment #2), fuses, bus wire/XT60, E-stop + DC contactor, crimper, misc; LD19 + BNO086 | ~$385 |
   | **Future-phase** | OAK-D Lite (deferred, ADR-0007); dual-arm servos + hardware (ADR-0009) | ~$380–560 |
   | | *Remaining of $2000* | **$826.15** |

   **Reading:** v0.1 closes comfortably (~$355 of $826). The future-phase pot
   fits only at the low end of the servo estimate — a high-end servo choice
   overruns by roughly $90. This is the live tension, and it is what makes the
   Feetech-vs-hobby-servo evaluation in ADR-0009 a budget decision as well as a
   technical one.

   **Excluded from the $2000 by decision:** the QIDI Plus 4 printer and initial
   filament (~$860) are tracked as a **capital tool**, not robot BOM (ADR-0008) —
   the project owner scoped it as a purchase serving future projects. Counting
   tooling, total programme outlay is ~$2,860.
5. Autonomous charging should be a future interface, not v0.1 hardware.
6. Remote operation without a nearby physical E-stop should not be allowed in v0.1.
7. OTA to MCUs should come after wired flashing and physical recovery are proven.